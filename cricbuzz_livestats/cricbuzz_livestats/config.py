"""
config.py
---------
Central configuration for the whole app.
Reads secrets from environment variables (.env file locally, or platform
secrets when deployed). Nothing sensitive is ever hardcoded here.
"""

import os
from dotenv import load_dotenv

# Load variables from a local .env file (no-op if the file doesn't exist,
# e.g. in production where env vars are set by the hosting platform).
load_dotenv()


class Config:
    # ---- Cricbuzz / RapidAPI ----
    RAPIDAPI_KEY: str = os.getenv("RAPIDAPI_KEY", "")
    RAPIDAPI_HOST: str = os.getenv("RAPIDAPI_HOST", "cricbuzz-cricket.p.rapidapi.com")
    BASE_URL: str = f"https://{RAPIDAPI_HOST}"

    # ---- Database ----
    DB_TYPE: str = os.getenv("DB_TYPE", "sqlite").lower()
    SQLITE_PATH: str = os.getenv("SQLITE_PATH", "data/cricbuzz.db")

    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "cricbuzz_livestats")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    # Hosted Postgres providers (Neon, Supabase, RDS, etc.) require SSL.
    # Local Postgres usually doesn't need it — set DB_SSLMODE=disable if so.
    DB_SSLMODE: str = os.getenv("DB_SSLMODE", "require")

    @classmethod
    def validate(cls) -> list[str]:
        """Return a list of human-readable warnings about missing config."""
        warnings = []
        if not cls.RAPIDAPI_KEY:
            warnings.append(
                "RAPIDAPI_KEY is not set. Live API pages will not work until "
                "you add it to your .env file."
            )
        return warnings


config = Config()
