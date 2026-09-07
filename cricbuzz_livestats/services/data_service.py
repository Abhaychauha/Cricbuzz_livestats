"""
services/data_service.py
-------------------------
Bridges the Cricbuzz API and the Streamlit UI: calls the client,
handles/logs errors gracefully, and reshapes raw JSON into flat
pandas DataFrames the UI can render directly in st.dataframe().
"""

from __future__ import annotations

import logging
import pandas as pd

from api.cricbuzz_client import client, CricbuzzAPIError

logger = logging.getLogger(__name__)


def fetch_live_matches() -> tuple[pd.DataFrame, str | None]:
    """
    Returns (dataframe, error_message). If error_message is not None,
    the dataframe will be empty — the UI should show the error instead.
    """
    try:
        raw = client.get_live_matches()
    except CricbuzzAPIError as e:
        logger.warning("Live matches fetch failed: %s", e)
        return pd.DataFrame(), str(e)

    rows = []
    for type_match in raw.get("typeMatches", []):
        match_type = type_match.get("matchType", "")
        for series_match in type_match.get("seriesMatches", []):
            wrapper = series_match.get("seriesAdWrapper", {})
            for m in wrapper.get("matches", []):
                info = m.get("matchInfo", {})
                score = m.get("matchScore", {})
                rows.append({
                    "match_type": match_type,
                    "series": info.get("seriesName"),
                    "match_desc": info.get("matchDesc"),
                    "team1": info.get("team1", {}).get("teamName"),
                    "team2": info.get("team2", {}).get("teamName"),
                    "status": info.get("status"),
                    "venue": info.get("venueInfo", {}).get("ground"),
                    "team1_score": _format_innings_score(score.get("team1Score")),
                    "team2_score": _format_innings_score(score.get("team2Score")),
                })

    if not rows:
        return pd.DataFrame(), "No live matches right now."
    return pd.DataFrame(rows), None


def _format_innings_score(score_obj: dict | None) -> str:
    if not score_obj:
        return "-"
    parts = []
    for inng in score_obj.values():
        if isinstance(inng, dict):
            runs = inng.get("runs", "")
            wkts = inng.get("wickets", "")
            overs = inng.get("overs", "")
            parts.append(f"{runs}/{wkts} ({overs} ov)")
    return " & ".join(parts) if parts else "-"


def fetch_top_batting_stats(stat_type: str = "mostRuns") -> tuple[pd.DataFrame, str | None]:
    try:
        raw = client.get_top_batting_stats(stat_type)
    except CricbuzzAPIError as e:
        logger.warning("Top batting stats fetch failed: %s", e)
        return pd.DataFrame(), str(e)

    rows = raw.get("headers", []), raw.get("values", [])
    headers, values = rows
    if not values:
        return pd.DataFrame(), "No stats available right now."

    data = [v.get("values", []) for v in values]
    return pd.DataFrame(data, columns=headers if headers else None), None
