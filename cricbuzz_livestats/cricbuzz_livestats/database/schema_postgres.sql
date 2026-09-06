-- =====================================================================
-- Cricbuzz LiveStats — Database Schema (PostgreSQL version)
-- Same structure as database/schema.sql, adapted for PostgreSQL syntax:
--   - SERIAL instead of INTEGER ... AUTOINCREMENT
--   - No PRAGMA (SQLite-only)
--   - CREATE OR REPLACE VIEW instead of CREATE VIEW IF NOT EXISTS
-- =====================================================================

CREATE TABLE IF NOT EXISTS teams (
    team_id     SERIAL PRIMARY KEY,
    team_name   TEXT NOT NULL UNIQUE,
    country     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS venues (
    venue_id    SERIAL PRIMARY KEY,
    venue_name  TEXT NOT NULL,
    city        TEXT NOT NULL,
    country     TEXT NOT NULL,
    capacity    INTEGER,
    UNIQUE (venue_name, city)
);

CREATE TABLE IF NOT EXISTS players (
    player_id       SERIAL PRIMARY KEY,
    full_name       TEXT NOT NULL,
    country         TEXT NOT NULL,
    playing_role    TEXT CHECK (playing_role IN
                        ('Batsman','Bowler','All-rounder','Wicket-keeper')),
    batting_style    TEXT,
    bowling_style    TEXT,
    date_of_birth    DATE
);

CREATE TABLE IF NOT EXISTS series (
    series_id       SERIAL PRIMARY KEY,
    series_name     TEXT NOT NULL,
    host_country    TEXT,
    match_type      TEXT CHECK (match_type IN ('Test','ODI','T20I')),
    start_date      DATE,
    total_matches   INTEGER
);

CREATE TABLE IF NOT EXISTS matches (
    match_id            SERIAL PRIMARY KEY,
    series_id           INTEGER REFERENCES series(series_id),
    match_description   TEXT,
    match_type          TEXT CHECK (match_type IN ('Test','ODI','T20I')),
    team1_id             INTEGER NOT NULL REFERENCES teams(team_id),
    team2_id             INTEGER NOT NULL REFERENCES teams(team_id),
    venue_id             INTEGER REFERENCES venues(venue_id),
    match_date           DATE,
    toss_winner_id       INTEGER REFERENCES teams(team_id),
    toss_decision        TEXT CHECK (toss_decision IN ('bat','bowl')),
    winning_team_id      INTEGER REFERENCES teams(team_id),
    victory_margin       INTEGER,
    victory_type         TEXT CHECK (victory_type IN ('runs','wickets','N/A')),
    CHECK (team1_id <> team2_id)
);

CREATE TABLE IF NOT EXISTS batting_stats (
    bat_stat_id         SERIAL PRIMARY KEY,
    match_id            INTEGER NOT NULL REFERENCES matches(match_id),
    player_id           INTEGER NOT NULL REFERENCES players(player_id),
    innings_no          INTEGER NOT NULL,
    batting_position    INTEGER,
    runs_scored         INTEGER DEFAULT 0,
    balls_faced         INTEGER DEFAULT 0,
    fours               INTEGER DEFAULT 0,
    sixes               INTEGER DEFAULT 0,
    strike_rate         NUMERIC,   -- NUMERIC (not REAL): lets ROUND(AVG(strike_rate), 2) work in Postgres
    out_type            TEXT,
    UNIQUE (match_id, player_id, innings_no)
);

CREATE TABLE IF NOT EXISTS bowling_stats (
    bowl_stat_id        SERIAL PRIMARY KEY,
    match_id            INTEGER NOT NULL REFERENCES matches(match_id),
    player_id           INTEGER NOT NULL REFERENCES players(player_id),
    innings_no          INTEGER NOT NULL,
    overs_bowled        REAL DEFAULT 0,
    runs_conceded       INTEGER DEFAULT 0,
    wickets_taken       INTEGER DEFAULT 0,
    economy_rate        NUMERIC,
    UNIQUE (match_id, player_id, innings_no)
);

CREATE TABLE IF NOT EXISTS fielding_stats (
    field_stat_id       SERIAL PRIMARY KEY,
    match_id            INTEGER NOT NULL REFERENCES matches(match_id),
    player_id           INTEGER NOT NULL REFERENCES players(player_id),
    catches             INTEGER DEFAULT 0,
    stumpings           INTEGER DEFAULT 0,
    UNIQUE (match_id, player_id)
);

CREATE TABLE IF NOT EXISTS partnerships (
    partnership_id      SERIAL PRIMARY KEY,
    match_id            INTEGER NOT NULL REFERENCES matches(match_id),
    innings_no          INTEGER NOT NULL,
    player1_id          INTEGER NOT NULL REFERENCES players(player_id),
    player2_id          INTEGER NOT NULL REFERENCES players(player_id),
    wicket_number       INTEGER,
    partnership_runs    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS player_career_stats (
    career_stat_id      SERIAL PRIMARY KEY,
    player_id           INTEGER NOT NULL REFERENCES players(player_id),
    format              TEXT CHECK (format IN ('Test','ODI','T20I')),
    total_runs          INTEGER DEFAULT 0,
    batting_average     NUMERIC,
    centuries           INTEGER DEFAULT 0,
    half_centuries      INTEGER DEFAULT 0,
    total_wickets       INTEGER DEFAULT 0,
    bowling_average     NUMERIC,
    economy_rate        NUMERIC,
    catches             INTEGER DEFAULT 0,
    stumpings           INTEGER DEFAULT 0,
    matches_played       INTEGER DEFAULT 0,
    UNIQUE (player_id, format)
);

CREATE INDEX IF NOT EXISTS idx_matches_date        ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_type         ON matches(match_type);
CREATE INDEX IF NOT EXISTS idx_batting_player       ON batting_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_bowling_player       ON bowling_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_career_player_format ON player_career_stats(player_id, format);
CREATE INDEX IF NOT EXISTS idx_partnerships_match   ON partnerships(match_id, innings_no);

CREATE OR REPLACE VIEW v_recent_matches AS
SELECT
    m.match_id,
    m.match_description,
    t1.team_name AS team1,
    t2.team_name AS team2,
    v.venue_name,
    v.city,
    m.match_date,
    wt.team_name AS winning_team,
    m.victory_margin,
    m.victory_type
FROM matches m
JOIN teams t1 ON m.team1_id = t1.team_id
JOIN teams t2 ON m.team2_id = t2.team_id
LEFT JOIN venues v ON m.venue_id = v.venue_id
LEFT JOIN teams wt ON m.winning_team_id = wt.team_id
ORDER BY m.match_date DESC;
