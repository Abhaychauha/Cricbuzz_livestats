"""
models/entities.py
-------------------
Lightweight dataclasses representing the core domain entities.
These are used mainly by the CRUD service and forms — they give us
type-checked, IDE-friendly objects instead of passing raw dicts around.
"""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Player:
    full_name: str
    country: str
    playing_role: str            # Batsman | Bowler | All-rounder | Wicket-keeper
    batting_style: str | None = None
    bowling_style: str | None = None
    date_of_birth: date | None = None
    player_id: int | None = None  # None until saved to DB

    def validate(self) -> list[str]:
        errors = []
        if not self.full_name.strip():
            errors.append("Full name is required.")
        if not self.country.strip():
            errors.append("Country is required.")
        if self.playing_role not in {"Batsman", "Bowler", "All-rounder", "Wicket-keeper"}:
            errors.append("Playing role must be one of: Batsman, Bowler, All-rounder, Wicket-keeper.")
        return errors


@dataclass
class Team:
    team_name: str
    country: str
    team_id: int | None = None


@dataclass
class Venue:
    venue_name: str
    city: str
    country: str
    capacity: int | None = None
    venue_id: int | None = None


@dataclass
class Match:
    match_description: str
    match_type: str               # Test | ODI | T20I
    team1_id: int
    team2_id: int
    venue_id: int | None
    match_date: date
    series_id: int | None = None
    toss_winner_id: int | None = None
    toss_decision: str | None = None      # bat | bowl
    winning_team_id: int | None = None
    victory_margin: int | None = None
    victory_type: str | None = None       # runs | wickets | N/A
    match_id: int | None = None

    def validate(self) -> list[str]:
        errors = []
        if self.team1_id == self.team2_id:
            errors.append("A team cannot play against itself.")
        if self.match_type not in {"Test", "ODI", "T20I"}:
            errors.append("Match type must be Test, ODI, or T20I.")
        return errors
