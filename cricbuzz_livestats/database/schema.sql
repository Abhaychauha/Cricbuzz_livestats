-- =====================================================================
-- Cricbuzz LiveStats — Database Schema
-- Works on SQLite, PostgreSQL, and MySQL with only minor type tweaks
-- (AUTOINCREMENT vs SERIAL vs AUTO_INCREMENT). This file targets SQLite,
-- the default for this project.
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- TEAMS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS teams (
    team_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    team_name   TEXT NOT NULL UNIQUE,
    country     TEXT NOT NULL
);

-- ---------------------------------------------------------------------
-- VENUES
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS venues (
    venue_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    venue_name  TEXT NOT NULL,
    city        TEXT NOT NULL,
    country     TEXT NOT NULL,
    capacity    INTEGER,
    UNIQUE (venue_name, city)
);

-- ---------------------------------------------------------------------
-- PLAYERS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS players (
    player_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name       TEXT NOT NULL,
    country         TEXT NOT NULL,
    playing_role    TEXT CHECK (playing_role IN
                        ('Batsman','Bowler','All-rounder','Wicket-keeper')),
    batting_style    TEXT,
    bowling_style    TEXT,
    date_of_birth    DATE
);

-- ---------------------------------------------------------------------
-- SERIES
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS series (
    series_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    series_name     TEXT NOT NULL,
    host_country    TEXT,
    match_type      TEXT CHECK (match_type IN ('Test','ODI','T20I')),
    start_date      DATE,
    total_matches   INTEGER
);

-- ---------------------------------------------------------------------
-- MATCHES
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS matches (
    match_id            INTEGER PRIMARY KEY AUTOINCREMENT,
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

-- ---------------------------------------------------------------------
-- BATTING STATS  (one row per player, per innings, per match)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS batting_stats (
    bat_stat_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id            INTEGER NOT NULL REFERENCES matches(match_id),
    player_id           INTEGER NOT NULL REFERENCES players(player_id),
    innings_no          INTEGER NOT NULL,
    batting_position    INTEGER,
    runs_scored         INTEGER DEFAULT 0,
    balls_faced         INTEGER DEFAULT 0,
    fours               INTEGER DEFAULT 0,
    sixes               INTEGER DEFAULT 0,
    strike_rate         REAL,
    out_type            TEXT,
    UNIQUE (match_id, player_id, innings_no)
);

-- ---------------------------------------------------------------------
-- BOWLING STATS (one row per player, per innings, per match)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bowling_stats (
    bowl_stat_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id            INTEGER NOT NULL REFERENCES matches(match_id),
    player_id           INTEGER NOT NULL REFERENCES players(player_id),
    innings_no          INTEGER NOT NULL,
    overs_bowled        REAL DEFAULT 0,
    runs_conceded       INTEGER DEFAULT 0,
    wickets_taken       INTEGER DEFAULT 0,
    economy_rate        REAL,
    UNIQUE (match_id, player_id, innings_no)
);

-- ---------------------------------------------------------------------
-- FIELDING STATS (catches / stumpings per match — used in Q21 ranking)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fielding_stats (
    field_stat_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id            INTEGER NOT NULL REFERENCES matches(match_id),
    player_id           INTEGER NOT NULL REFERENCES players(player_id),
    catches             INTEGER DEFAULT 0,
    stumpings           INTEGER DEFAULT 0,
    UNIQUE (match_id, player_id)
);

-- ---------------------------------------------------------------------
-- PARTNERSHIPS (consecutive-batting-position pairs, per innings)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS partnerships (
    partnership_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id            INTEGER NOT NULL REFERENCES matches(match_id),
    innings_no          INTEGER NOT NULL,
    player1_id          INTEGER NOT NULL REFERENCES players(player_id),
    player2_id          INTEGER NOT NULL REFERENCES players(player_id),
    wicket_number       INTEGER,       -- e.g. 1st wicket, 2nd wicket...
    partnership_runs    INTEGER DEFAULT 0
);

-- ---------------------------------------------------------------------
-- PLAYER CAREER STATS (pre-aggregated, one row per player per format —
-- powers the simple "top run scorer" style beginner queries fast,
-- without recomputing aggregates from raw innings every time)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS player_career_stats (
    career_stat_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id           INTEGER NOT NULL REFERENCES players(player_id),
    format              TEXT CHECK (format IN ('Test','ODI','T20I')),
    total_runs          INTEGER DEFAULT 0,
    batting_average     REAL,
    centuries           INTEGER DEFAULT 0,
    half_centuries      INTEGER DEFAULT 0,
    total_wickets       INTEGER DEFAULT 0,
    bowling_average     REAL,
    economy_rate        REAL,
    catches             INTEGER DEFAULT 0,
    stumpings           INTEGER DEFAULT 0,
    matches_played       INTEGER DEFAULT 0,
    UNIQUE (player_id, format)
);

-- ---------------------------------------------------------------------
-- INDEXES (frequently filtered/joined columns)
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_matches_date        ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_type         ON matches(match_type);
CREATE INDEX IF NOT EXISTS idx_batting_player       ON batting_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_bowling_player       ON bowling_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_career_player_format ON player_career_stats(player_id, format);
CREATE INDEX IF NOT EXISTS idx_partnerships_match   ON partnerships(match_id, innings_no);

-- ---------------------------------------------------------------------
-- A couple of convenience VIEWS
-- ---------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_recent_matches AS
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
