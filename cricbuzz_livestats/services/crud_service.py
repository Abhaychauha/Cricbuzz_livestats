"""
services/crud_service.py
-------------------------
All Create / Read / Update / Delete logic for players lives here, kept
separate from the Streamlit UI (pages/4_CRUD_Operations.py just calls
these functions). This separation is what makes the app testable and
"clean architecture" — UI code never talks to SQL directly.
"""

from __future__ import annotations

import logging
import pandas as pd
from sqlalchemy.exc import IntegrityError

from models.entities import Player
from utils.db_connection import run_query, execute

logger = logging.getLogger(__name__)


class CRUDError(Exception):
    """Raised for validation or database errors surfaced to the UI."""


# ----------------------------------------------------------------------
# CREATE
# ----------------------------------------------------------------------
def add_player(player: Player) -> int:
    errors = player.validate()
    if errors:
        raise CRUDError("; ".join(errors))

    sql = """
        INSERT INTO players (full_name, country, playing_role,
                              batting_style, bowling_style, date_of_birth)
        VALUES (:full_name, :country, :playing_role,
                :batting_style, :bowling_style, :date_of_birth)
    """
    try:
        execute(sql, {
            "full_name": player.full_name,
            "country": player.country,
            "playing_role": player.playing_role,
            "batting_style": player.batting_style,
            "bowling_style": player.bowling_style,
            "date_of_birth": player.date_of_birth,
        })
        logger.info("Player added: %s", player.full_name)
        return 1
    except IntegrityError as e:
        raise CRUDError(f"Could not save player — {e.orig}")


# ----------------------------------------------------------------------
# READ
# ----------------------------------------------------------------------
def get_all_players() -> pd.DataFrame:
    return run_query("""
        SELECT player_id, full_name, country, playing_role,
               batting_style, bowling_style, date_of_birth
        FROM players
        ORDER BY full_name
    """)


def get_player_by_id(player_id: int) -> pd.DataFrame:
    return run_query(
        "SELECT * FROM players WHERE player_id = :pid",
        {"pid": player_id},
    )


def search_players(name_query: str) -> pd.DataFrame:
    return run_query(
        "SELECT * FROM players WHERE full_name LIKE :q ORDER BY full_name",
        {"q": f"%{name_query}%"},
    )


# ----------------------------------------------------------------------
# UPDATE
# ----------------------------------------------------------------------
def update_player(player: Player) -> int:
    if player.player_id is None:
        raise CRUDError("Cannot update a player without a player_id.")

    errors = player.validate()
    if errors:
        raise CRUDError("; ".join(errors))

    sql = """
        UPDATE players
        SET full_name = :full_name,
            country = :country,
            playing_role = :playing_role,
            batting_style = :batting_style,
            bowling_style = :bowling_style,
            date_of_birth = :date_of_birth
        WHERE player_id = :player_id
    """
    rows = execute(sql, {
        "full_name": player.full_name,
        "country": player.country,
        "playing_role": player.playing_role,
        "batting_style": player.batting_style,
        "bowling_style": player.bowling_style,
        "date_of_birth": player.date_of_birth,
        "player_id": player.player_id,
    })
    if rows == 0:
        raise CRUDError(f"No player found with id {player.player_id}.")
    logger.info("Player updated: id=%s", player.player_id)
    return rows


# ----------------------------------------------------------------------
# DELETE
# ----------------------------------------------------------------------
def delete_player(player_id: int) -> int:
    try:
        rows = execute(
            "DELETE FROM players WHERE player_id = :pid",
            {"pid": player_id},
        )
        if rows == 0:
            raise CRUDError(f"No player found with id {player_id}.")
        logger.info("Player deleted: id=%s", player_id)
        return rows
    except IntegrityError:
        raise CRUDError(
            "Cannot delete this player — they have related match stats. "
            "Delete those first, or archive instead of deleting."
        )
