"""
api/cricbuzz_client.py
-----------------------
Thin, well-behaved wrapper around the Cricbuzz Cricket API (via RapidAPI).

Design goals:
- One place that knows about HTTP / headers / retries.
- Every public method returns already-parsed JSON (dict) or raises a
  clear CricbuzzAPIError — callers never touch `requests` directly.
"""

from __future__ import annotations

import time
import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter, Retry

from config import config

logger = logging.getLogger(__name__)


class CricbuzzAPIError(Exception):
    """Raised whenever the Cricbuzz API can't be reached or returns an error."""


class CricbuzzClient:
    def __init__(self, api_key: str | None = None, host: str | None = None):
        self.api_key = api_key or config.RAPIDAPI_KEY
        self.host = host or config.RAPIDAPI_HOST
        self.base_url = f"https://{self.host}"

        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1.5,          # 1.5s, 3s, 4.5s between retries
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------
    def _get(self, endpoint: str, params: dict | None = None) -> dict[str, Any]:
        if not self.api_key:
            raise CricbuzzAPIError(
                "RAPIDAPI_KEY is missing. Add it to your .env file before "
                "calling the live API."
            )

        url = f"{self.base_url}{endpoint}"
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host,
        }

        try:
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            logger.error("Cricbuzz API timed out: %s", url)
            raise CricbuzzAPIError("The Cricbuzz API took too long to respond.")

        except requests.exceptions.HTTPError as e:
            logger.error("Cricbuzz API HTTP error: %s", e)
            if response.status_code == 429:
                raise CricbuzzAPIError("Rate limit exceeded. Try again shortly.")
            raise CricbuzzAPIError(f"Cricbuzz API returned an error: {response.status_code}")

        except requests.exceptions.ConnectionError:
            logger.error("Could not connect to Cricbuzz API: %s", url)
            raise CricbuzzAPIError("Could not connect to the Cricbuzz API. Check your network.")

        except ValueError:  # JSON decode error
            logger.error("Cricbuzz API returned non-JSON response for %s", url)
            raise CricbuzzAPIError("Received an unreadable response from the Cricbuzz API.")

    # ------------------------------------------------------------------
    # Public endpoints (mapped to what the Streamlit pages need)
    # ------------------------------------------------------------------
    def get_live_matches(self) -> dict[str, Any]:
        """Currently live matches across all formats."""
        return self._get("/matches/v1/live")

    def get_recent_matches(self) -> dict[str, Any]:
        """Recently completed matches."""
        return self._get("/matches/v1/recent")

    def get_upcoming_matches(self) -> dict[str, Any]:
        """Upcoming scheduled matches."""
        return self._get("/matches/v1/upcoming")

    def get_match_scorecard(self, match_id: int) -> dict[str, Any]:
        """Full scorecard for a specific match id."""
        return self._get(f"/mcenter/v1/{match_id}/scard")

    def get_top_batting_stats(self, stat_type: str = "mostRuns") -> dict[str, Any]:
        """
        stat_type examples: mostRuns, highestScore, mostHundreds, mostFifties
        """
        return self._get(f"/stats/v1/topstats/0", params={"statsType": stat_type})

    def get_top_bowling_stats(self, stat_type: str = "mostWickets") -> dict[str, Any]:
        return self._get(f"/stats/v1/topstats/0", params={"statsType": stat_type})

    def get_series_list(self) -> dict[str, Any]:
        return self._get("/series/v1/international")


# A module-level singleton so pages can just `from api.cricbuzz_client import client`
client = CricbuzzClient()
