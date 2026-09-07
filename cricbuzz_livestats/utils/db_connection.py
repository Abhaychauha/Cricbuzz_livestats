"""
utils/db_connection.py
-----------------------
Single source of truth for database connections. Every other module
(services, pages) imports `get_engine()` or `run_query()` from here
instead of opening its own connection — this is what makes the app
"database-agnostic": switch DB_TYPE in .env and nothing else changes.
"""

from __future__ import annotations

import os
import time
import logging
from pathlib import Path
from contextlib import contextmanager

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from config import config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

_engine: Engine | None = None

# Cloud Postgres providers (Neon, Supabase, RDS, etc.) can drop a connection
# mid-statement over a flaky network — not something pool_pre_ping alone can
# catch, since that only checks connections *before* they're used. Retrying
# the whole operation from scratch is safe here because every call below is
# wrapped in its own single transaction (get_connection): a failed attempt
# commits nothing, so retrying never double-inserts.
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


def _run_with_retries(fn):
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return fn()
        except SQLAlchemyError as e:
            last_exc = e
            logger.warning(
                "Database operation failed (attempt %s/%s): %s",
                attempt, MAX_RETRIES, e,
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
    raise last_exc


def _build_connection_url() -> str:
    """Build the SQLAlchemy connection URL based on DB_TYPE."""
    if config.DB_TYPE == "sqlite":
        # Ensure the folder for the sqlite file exists.
        db_path = Path(config.SQLITE_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"

    if config.DB_TYPE == "postgresql":
        return (
            f"postgresql+psycopg2://{config.DB_USER}:{config.DB_PASSWORD}"
            f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
            f"?sslmode={config.DB_SSLMODE}"
        )

    if config.DB_TYPE == "mysql":
        return (
            f"mysql+mysqlconnector://{config.DB_USER}:{config.DB_PASSWORD}"
            f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
        )

    raise ValueError(f"Unsupported DB_TYPE: {config.DB_TYPE!r}")


def get_engine() -> Engine:
    """Return a cached SQLAlchemy engine (created once per process)."""
    global _engine
    if _engine is None:
        url = _build_connection_url()
        # check_same_thread=False is needed for SQLite + Streamlit's
        # multi-threaded execution model.
        connect_args = {"check_same_thread": False} if config.DB_TYPE == "sqlite" else {}
        _engine = create_engine(
            url,
            connect_args=connect_args,
            future=True,
            # Cloud Postgres providers (Neon, Supabase, RDS, etc.) can silently
            # drop idle/pooled connections. pool_pre_ping tests each connection
            # before use and transparently reconnects instead of raising
            # "server closed the connection unexpectedly" mid-script.
            pool_pre_ping=True,
            pool_recycle=280,
        )
        logger.info("Database engine created for DB_TYPE=%s", config.DB_TYPE)
    return _engine


@contextmanager
def get_connection():
    """Context manager yielding a raw SQLAlchemy connection with a transaction."""
    engine = get_engine()
    conn = engine.connect()
    trans = conn.begin()
    try:
        yield conn
        trans.commit()
    except SQLAlchemyError:
        trans.rollback()
        logger.exception("Transaction rolled back due to an error.")
        raise
    finally:
        conn.close()


def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Run a SELECT query and return the result as a pandas DataFrame."""
    def _do():
        engine = get_engine()
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn, params=params or {})
    return _run_with_retries(_do)


def execute(sql: str, params: dict | None = None) -> int:
    """
    Run a single INSERT / UPDATE / DELETE statement inside its own
    transaction. Returns number of rows affected.
    """
    def _do():
        with get_connection() as conn:
            result = conn.execute(text(sql), params or {})
            return result.rowcount
    return _run_with_retries(_do)


def execute_many(sql: str, list_of_params: list[dict]) -> int:
    """
    Insert/update many rows in ONE transaction / round-trip instead of one
    per row. Used by database/seed_data.py so seeding thousands of rows over
    a network connection (e.g. to a hosted Postgres like Neon) means a few
    hundred round-trips instead of several thousand — both much faster and
    far less exposed to a single network blip killing the whole run.
    """
    if not list_of_params:
        return 0

    def _do():
        with get_connection() as conn:
            result = conn.execute(text(sql), list_of_params)
            return result.rowcount
    return _run_with_retries(_do)


def init_schema(schema_path: str | None = None) -> None:
    """
    Execute the schema file to (re)create all tables/views/indexes.
    Picks database/schema.sql for SQLite, or database/schema_postgres.sql
    for PostgreSQL, unless an explicit path is given.
    """
    if schema_path is None:
        schema_path = (
            "database/schema_postgres.sql"
            if config.DB_TYPE == "postgresql"
            else "database/schema.sql"
        )

    schema_file = Path(schema_path)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    statements = [s.strip() for s in schema_file.read_text().split(";") if s.strip()]

    def _do():
        with get_connection() as conn:
            for stmt in statements:
                conn.execute(text(stmt))
    _run_with_retries(_do)
    logger.info("Schema initialized successfully (DB_TYPE=%s).", config.DB_TYPE)


def _build_insert_ignore_sql(table: str, columns: list[str], conflict_columns: list[str]) -> str:
    col_list = ", ".join(columns)
    val_list = ", ".join(f":{c}" for c in columns)

    if config.DB_TYPE == "postgresql":
        conflict = ", ".join(conflict_columns)
        return (
            f"INSERT INTO {table} ({col_list}) VALUES ({val_list}) "
            f"ON CONFLICT ({conflict}) DO NOTHING"
        )
    return f"INSERT OR IGNORE INTO {table} ({col_list}) VALUES ({val_list})"


def insert_ignore(table: str, params: dict, conflict_columns: list[str]) -> None:
    """
    Insert a row, silently skipping it if it violates a uniqueness
    constraint on `conflict_columns`. Written once here because SQLite
    and PostgreSQL use different syntax for "insert or do nothing":

        SQLite:     INSERT OR IGNORE INTO table (...) VALUES (...)
        PostgreSQL: INSERT INTO table (...) VALUES (...)
                    ON CONFLICT (col1, col2) DO NOTHING

    `params` keys become both the column list and the bound-parameter
    names, e.g. {"team_name": "India", "country": "India"}.
    """
    sql = _build_insert_ignore_sql(table, list(params.keys()), conflict_columns)
    execute(sql, params)


def insert_ignore_many(table: str, list_of_params: list[dict], conflict_columns: list[str]) -> int:
    """
    Batched version of insert_ignore(): inserts many rows for the same
    table in a single round-trip / transaction. `list_of_params` must be a
    non-empty list of dicts that all share the same keys.
    """
    if not list_of_params:
        return 0
    sql = _build_insert_ignore_sql(table, list(list_of_params[0].keys()), conflict_columns)
    return execute_many(sql, list_of_params)
