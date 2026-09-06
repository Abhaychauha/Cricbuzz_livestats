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
        _engine = create_engine(url, connect_args=connect_args, future=True)
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
    engine = get_engine()
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn, params=params or {})
    except SQLAlchemyError as e:
        logger.error("Query failed: %s", e)
        raise


def execute(sql: str, params: dict | None = None) -> int:
    """
    Run an INSERT / UPDATE / DELETE statement inside a transaction.
    Returns number of rows affected.
    """
    with get_connection() as conn:
        result = conn.execute(text(sql), params or {})
        return result.rowcount


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

    statements = schema_file.read_text().split(";")
    with get_connection() as conn:
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))
    logger.info("Schema initialized successfully (DB_TYPE=%s).", config.DB_TYPE)


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
    columns = list(params.keys())
    col_list = ", ".join(columns)
    val_list = ", ".join(f":{c}" for c in columns)

    if config.DB_TYPE == "postgresql":
        conflict = ", ".join(conflict_columns)
        sql = (
            f"INSERT INTO {table} ({col_list}) VALUES ({val_list}) "
            f"ON CONFLICT ({conflict}) DO NOTHING"
        )
    else:
        sql = f"INSERT OR IGNORE INTO {table} ({col_list}) VALUES ({val_list})"

    execute(sql, params)
