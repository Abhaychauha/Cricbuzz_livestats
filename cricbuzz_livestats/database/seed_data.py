"""
database/seed_data.py
----------------------
Populates the database with realistic sample data so that the 25 SQL
practice queries have something meaningful to run against.

Why this exists: the live Cricbuzz API gives you *current* scores and
stats, not the years of relational match/innings history the advanced
SQL questions (partnerships, quarterly trends, head-to-head, etc.)
need. So this project keeps its own historical dataset in SQL, and
uses the live API separately for the "Live Matches" / "Top Stats" pages.

Run with:  python -m database.seed_data
"""

import random
from datetime import date, timedelta

from utils.db_connection import init_schema, execute, execute_many, run_query, insert_ignore, insert_ignore_many

random.seed(42)

TEAMS = [
    ("India", "India"), ("Australia", "Australia"), ("England", "England"),
    ("New Zealand", "New Zealand"), ("Pakistan", "Pakistan"),
    ("South Africa", "South Africa"), ("Sri Lanka", "Sri Lanka"),
    ("West Indies", "West Indies"), ("Bangladesh", "Bangladesh"), ("Afghanistan", "Afghanistan"),
]

VENUES = [
    ("Narendra Modi Stadium", "Ahmedabad", "India", 132000),
    ("Melbourne Cricket Ground", "Melbourne", "Australia", 100024),
    ("Eden Gardens", "Kolkata", "India", 66000),
    ("Lord's", "London", "England", 31100),
    ("The Oval", "London", "England", 25500),
    ("Wankhede Stadium", "Mumbai", "India", 33000),
    ("SCG", "Sydney", "Australia", 48000),
    ("Newlands", "Cape Town", "South Africa", 25000),
    ("R Premadasa Stadium", "Colombo", "Sri Lanka", 35000),
    ("National Stadium", "Karachi", "Pakistan", 34000),
]

PLAYERS = [
    # (name, country, role, batting_style, bowling_style)
    ("Virat Kohli", "India", "Batsman", "Right-hand bat", None),
    ("Rohit Sharma", "India", "Batsman", "Right-hand bat", None),
    ("Ravindra Jadeja", "India", "All-rounder", "Left-hand bat", "Left-arm orthodox"),
    ("Jasprit Bumrah", "India", "Bowler", "Right-hand bat", "Right-arm fast"),
    ("KL Rahul", "India", "Wicket-keeper", "Right-hand bat", None),
    ("Steve Smith", "Australia", "Batsman", "Right-hand bat", None),
    ("Pat Cummins", "Australia", "Bowler", "Right-hand bat", "Right-arm fast"),
    ("Glenn Maxwell", "Australia", "All-rounder", "Right-hand bat", "Right-arm off break"),
    ("David Warner", "Australia", "Batsman", "Left-hand bat", None),
    ("Joe Root", "England", "Batsman", "Right-hand bat", None),
    ("Ben Stokes", "England", "All-rounder", "Left-hand bat", "Right-arm fast-medium"),
    ("Jofra Archer", "England", "Bowler", "Right-hand bat", "Right-arm fast"),
    ("Kane Williamson", "New Zealand", "Batsman", "Right-hand bat", None),
    ("Trent Boult", "New Zealand", "Bowler", "Left-hand bat", "Left-arm fast-medium"),
    ("Babar Azam", "Pakistan", "Batsman", "Right-hand bat", None),
    ("Shaheen Afridi", "Pakistan", "Bowler", "Left-hand bat", "Left-arm fast"),
    ("Quinton de Kock", "South Africa", "Wicket-keeper", "Left-hand bat", None),
    ("Kagiso Rabada", "South Africa", "Bowler", "Right-hand bat", "Right-arm fast"),
    ("Wanindu Hasaranga", "Sri Lanka", "All-rounder", "Right-hand bat", "Right-arm leg break"),
    ("Shakib Al Hasan", "Bangladesh", "All-rounder", "Left-hand bat", "Left-arm orthodox"),
]

FORMATS = ["Test", "ODI", "T20I"]


def seed_teams(conn_free=True):
    for name, country in TEAMS:
        insert_ignore(
            "teams",
            {"team_name": name, "country": country},
            conflict_columns=["team_name"],
        )


def seed_venues():
    for name, city, country, cap in VENUES:
        insert_ignore(
            "venues",
            {"venue_name": name, "city": city, "country": country, "capacity": cap},
            conflict_columns=["venue_name", "city"],
        )


def seed_players():
    for name, country, role, bat, bowl in PLAYERS:
        # players has no natural unique key in the schema, so we guard
        # against re-seeding duplicates manually instead.
        existing = run_query(
            "SELECT player_id FROM players WHERE full_name = :n", {"n": name}
        )
        if existing.empty:
            execute(
                """INSERT INTO players
                   (full_name, country, playing_role, batting_style, bowling_style)
                   VALUES (:n, :c, :r, :b, :bo)""",
                {"n": name, "c": country, "r": role, "b": bat, "bo": bowl},
            )


def seed_series_and_matches(num_matches: int = 120):
    team_ids = run_query("SELECT team_id FROM teams")["team_id"].tolist()
    venue_ids = run_query("SELECT venue_id, country FROM venues")
    venue_rows = list(venue_ids.itertuples(index=False))

    existing_series = run_query("SELECT series_id FROM series")
    if existing_series.empty:
        execute("""INSERT INTO series (series_id, series_name, host_country,
                  match_type, start_date, total_matches)
                  VALUES (1, 'World Test Championship 2024-26', 'Multiple', 'Test', '2024-06-01', 60)""")
        execute("""INSERT INTO series (series_id, series_name, host_country,
                  match_type, start_date, total_matches)
                  VALUES (2, 'ODI World Cup Qualifiers', 'India', 'ODI', '2024-09-01', 30)""")
        execute("""INSERT INTO series (series_id, series_name, host_country,
                  match_type, start_date, total_matches)
                  VALUES (3, 'T20I Tri-Series 2024', 'Australia', 'T20I', '2024-11-01', 15)""")

    start_date = date.today() - timedelta(days=6 * 365)  # spread across ~6 years for quarterly analysis

    for i in range(num_matches):
        t1, t2 = random.sample(team_ids, 2)
        venue = random.choice(venue_rows)
        match_type = random.choice(FORMATS)
        match_date = start_date + timedelta(days=random.randint(0, 6 * 365))
        toss_winner = random.choice([t1, t2])
        toss_decision = random.choice(["bat", "bowl"])
        winner = random.choice([t1, t2, None])  # None -> draw/no result occasionally
        victory_type = random.choice(["runs", "wickets"]) if winner else "N/A"
        victory_margin = random.randint(5, 200) if victory_type == "runs" else random.randint(1, 9)
        series_id = {"Test": 1, "ODI": 2, "T20I": 3}[match_type]

        execute(
            """INSERT INTO matches
               (series_id, match_description, match_type, team1_id, team2_id, venue_id,
                match_date, toss_winner_id, toss_decision, winning_team_id,
                victory_margin, victory_type)
               VALUES (:sid, :desc, :mt, :t1, :t2, :vid, :md, :tw, :td, :wt, :vm, :vt)""",
            {
                "sid": series_id, "desc": f"Match {i+1}", "mt": match_type,
                "t1": t1, "t2": t2, "vid": venue.venue_id, "md": match_date.isoformat(),
                "tw": toss_winner, "td": toss_decision, "wt": winner,
                "vm": victory_margin if winner else None,
                "vt": victory_type if winner else "N/A",
            },
        )


def seed_innings_stats():
    """
    Generate batting/bowling/fielding rows + partnerships for every match.

    Batched per match (one round-trip per table per match) rather than one
    round-trip per individual row — thousands of tiny sequential inserts
    over a network connection to a hosted DB (e.g. Neon) is slow and far
    more likely to hit a transient connection drop than a few hundred
    batched ones.
    """
    matches = run_query("SELECT match_id, match_type FROM matches")
    players = run_query("SELECT player_id, playing_role FROM players")
    player_ids = players["player_id"].tolist()

    total = len(matches)
    for i, (_, match) in enumerate(matches.iterrows(), start=1):
        batting_rows, partnership_rows, bowling_rows, fielding_rows = [], [], [], []

        for innings_no in (1, 2):
            batting_order = random.sample(player_ids, min(6, len(player_ids)))
            prev_player = None
            for pos, pid in enumerate(batting_order, start=1):
                runs = max(0, int(random.gauss(35, 30)))
                balls = max(1, runs + random.randint(0, 40))
                sr = round((runs / balls) * 100, 2) if balls else 0
                batting_rows.append({
                    "match_id": int(match.match_id), "player_id": pid, "innings_no": innings_no,
                    "batting_position": pos, "runs_scored": runs, "balls_faced": balls,
                    "fours": random.randint(0, runs // 10 + 1),
                    "sixes": random.randint(0, runs // 20 + 1),
                    "strike_rate": sr,
                    "out_type": random.choice(["bowled", "caught", "lbw", "run out", "not out"]),
                })
                if prev_player is not None:
                    partnership_rows.append({
                        "mid": int(match.match_id), "inn": innings_no,
                        "p1": prev_player, "p2": pid, "wn": pos - 1,
                        "runs": max(0, int(random.gauss(45, 35))),
                    })
                prev_player = pid

            bowlers = random.sample(player_ids, min(4, len(player_ids)))
            for pid in bowlers:
                overs = round(random.uniform(2, 10), 1)
                runs_conceded = int(overs * random.uniform(3, 9))
                economy = round(runs_conceded / overs, 2) if overs else 0
                bowling_rows.append({
                    "match_id": int(match.match_id), "player_id": pid, "innings_no": innings_no,
                    "overs_bowled": overs, "runs_conceded": runs_conceded,
                    "wickets_taken": random.randint(0, 5), "economy_rate": economy,
                })

            fielders = random.sample(player_ids, min(3, len(player_ids)))
            for pid in fielders:
                fielding_rows.append({
                    "match_id": int(match.match_id), "player_id": pid,
                    "catches": random.randint(0, 2), "stumpings": random.randint(0, 1),
                })

        insert_ignore_many("batting_stats", batting_rows,
                            conflict_columns=["match_id", "player_id", "innings_no"])
        if partnership_rows:
            execute_many(
                """INSERT INTO partnerships
                   (match_id, innings_no, player1_id, player2_id, wicket_number, partnership_runs)
                   VALUES (:mid, :inn, :p1, :p2, :wn, :runs)""",
                partnership_rows,
            )
        insert_ignore_many("bowling_stats", bowling_rows,
                            conflict_columns=["match_id", "player_id", "innings_no"])
        insert_ignore_many("fielding_stats", fielding_rows,
                            conflict_columns=["match_id", "player_id"])

        if i % 20 == 0 or i == total:
            print(f"  ...seeded innings stats for {i}/{total} matches")


def seed_career_stats():
    """Aggregate career stats per player/format from the innings-level data."""
    players = run_query("SELECT player_id FROM players")
    for pid in players["player_id"]:
        for fmt in FORMATS:
            bat = run_query(
                """SELECT COUNT(*) AS innings, SUM(runs_scored) AS runs,
                          AVG(runs_scored) AS avg_runs
                   FROM batting_stats b JOIN matches m ON b.match_id = m.match_id
                   WHERE b.player_id = :pid AND m.match_type = :fmt""",
                {"pid": int(pid), "fmt": fmt},
            ).iloc[0]
            bowl = run_query(
                """SELECT SUM(wickets_taken) AS wickets, AVG(economy_rate) AS econ
                   FROM bowling_stats b JOIN matches m ON b.match_id = m.match_id
                   WHERE b.player_id = :pid AND m.match_type = :fmt""",
                {"pid": int(pid), "fmt": fmt},
            ).iloc[0]
            field = run_query(
                """SELECT SUM(catches) AS catches, SUM(stumpings) AS stumpings
                   FROM fielding_stats f JOIN matches m ON f.match_id = m.match_id
                   WHERE f.player_id = :pid AND m.match_type = :fmt""",
                {"pid": int(pid), "fmt": fmt},
            ).iloc[0]

            matches_played = int(bat["innings"] or 0)
            if matches_played == 0:
                continue

            insert_ignore(
                "player_career_stats",
                {
                    "player_id": int(pid), "format": fmt,
                    "total_runs": int(bat["runs"] or 0),
                    "batting_average": round(float(bat["avg_runs"] or 0), 2),
                    "centuries": random.randint(0, 5),
                    "half_centuries": random.randint(0, 10),
                    "total_wickets": int(bowl["wickets"] or 0),
                    "bowling_average": round(random.uniform(20, 40), 2),
                    "economy_rate": round(float(bowl["econ"] or random.uniform(3, 6)), 2),
                    "catches": int(field["catches"] or 0),
                    "stumpings": int(field["stumpings"] or 0),
                    "matches_played": matches_played,
                },
                conflict_columns=["player_id", "format"],
            )


def run_all():
    print("Initializing schema...")
    init_schema()
    print("Seeding teams...")
    seed_teams()
    print("Seeding venues...")
    seed_venues()
    print("Seeding players...")
    seed_players()
    print("Seeding series & matches...")
    seed_series_and_matches()
    print("Seeding innings-level stats (this takes a moment)...")
    seed_innings_stats()
    print("Aggregating career stats...")
    seed_career_stats()
    print("Done! Database is ready at the configured SQLITE_PATH.")


if __name__ == "__main__":
    run_all()
