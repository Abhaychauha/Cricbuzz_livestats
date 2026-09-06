"""
sql/queries.py
---------------
All 25 SQL practice questions, each stored with:
  - level: Beginner / Intermediate / Advanced
  - question: the business question (as given in the project brief)
  - sql: the actual query, written against schema.sql

The Streamlit "SQL Queries & Analytics" page imports QUERIES and lets
the user pick one question at a time, see the SQL, and run it.

A handful of queries (Q2, Q8, Q16, Q22, Q25) use relative-date or
year-extraction functions that differ between SQLite and PostgreSQL.
IS_POSTGRES picks the right dialect for those five automatically based
on your .env DB_TYPE — everything else is standard SQL and needs no
changes either way.
"""

from config import config

IS_POSTGRES = config.DB_TYPE == "postgresql"

QUERIES = {

    # ============================= BEGINNER =============================
    "Q1: Players who represent India": {
        "level": "Beginner",
        "question": "Find all players who represent India. Display their full name, "
                     "playing role, batting style, and bowling style.",
        "sql": """
            SELECT full_name, playing_role, batting_style, bowling_style
            FROM players
            WHERE country = 'India'
            ORDER BY full_name;
        """,
    },

    "Q2: Matches in the last 30 days": {
        "level": "Beginner",
        "question": "Show all cricket matches played in the last 30 days, with "
                     "description, both team names, venue + city, and match date, "
                     "sorted most recent first.",
        "sql": f"""
            SELECT m.match_description,
                   t1.team_name AS team1,
                   t2.team_name AS team2,
                   v.venue_name,
                   v.city,
                   m.match_date
            FROM matches m
            JOIN teams t1 ON m.team1_id = t1.team_id
            JOIN teams t2 ON m.team2_id = t2.team_id
            LEFT JOIN venues v ON m.venue_id = v.venue_id
            WHERE m.match_date >= {"CURRENT_DATE - INTERVAL '30 days'" if IS_POSTGRES else "date('now', '-30 day')"}
            ORDER BY m.match_date DESC;
        """,
    },

    "Q3: Top 10 ODI run scorers": {
        "level": "Beginner",
        "question": "List the top 10 highest run scorers in ODI cricket, with name, "
                     "total runs, batting average, and centuries — highest first.",
        "sql": """
            SELECT p.full_name,
                   pc.total_runs,
                   pc.batting_average,
                   pc.centuries
            FROM player_career_stats pc
            JOIN players p ON pc.player_id = p.player_id
            WHERE pc.format = 'ODI'
            ORDER BY pc.total_runs DESC
            LIMIT 10;
        """,
    },

    "Q4: Venues with capacity > 50,000": {
        "level": "Beginner",
        "question": "Display all venues with seating capacity over 50,000. Show name, "
                     "city, country, capacity — largest first.",
        "sql": """
            SELECT venue_name, city, country, capacity
            FROM venues
            WHERE capacity > 50000
            ORDER BY capacity DESC;
        """,
    },

    "Q5: Total wins per team": {
        "level": "Beginner",
        "question": "Calculate how many matches each team has won, most wins first.",
        "sql": """
            SELECT t.team_name, COUNT(*) AS total_wins
            FROM matches m
            JOIN teams t ON m.winning_team_id = t.team_id
            GROUP BY t.team_name
            ORDER BY total_wins DESC;
        """,
    },

    "Q6: Player count by playing role": {
        "level": "Beginner",
        "question": "Count how many players belong to each playing role.",
        "sql": """
            SELECT playing_role, COUNT(*) AS player_count
            FROM players
            GROUP BY playing_role
            ORDER BY player_count DESC;
        """,
    },

    "Q7: Highest individual score per format": {
        "level": "Beginner",
        "question": "Find the highest individual batting score achieved in each "
                     "format (Test, ODI, T20I).",
        "sql": """
            SELECT m.match_type AS format, MAX(b.runs_scored) AS highest_score
            FROM batting_stats b
            JOIN matches m ON b.match_id = m.match_id
            GROUP BY m.match_type;
        """,
    },

    "Q8: Series started in 2024": {
        "level": "Beginner",
        "question": "Show all series that started in 2024 — name, host country, "
                     "match type, start date, total matches planned.",
        "sql": f"""
            SELECT series_name, host_country, match_type, start_date, total_matches
            FROM series
            WHERE {"EXTRACT(YEAR FROM start_date) = 2024" if IS_POSTGRES else "strftime('%Y', start_date) = '2024'"}
            ORDER BY start_date;
        """,
    },

    # ========================== INTERMEDIATE ==========================
    "Q9: All-rounders with 1000+ runs and 50+ wickets": {
        "level": "Intermediate",
        "question": "Find all-rounders with more than 1000 runs AND more than 50 "
                     "wickets in their career, with format.",
        "sql": """
            SELECT p.full_name, pc.total_runs, pc.total_wickets, pc.format
            FROM player_career_stats pc
            JOIN players p ON pc.player_id = p.player_id
            WHERE p.playing_role = 'All-rounder'
              AND pc.total_runs > 1000
              AND pc.total_wickets > 50;
        """,
    },

    "Q10: Last 20 completed matches with results": {
        "level": "Intermediate",
        "question": "Get details of the last 20 completed matches: description, "
                     "teams, winner, victory margin/type, venue — most recent first.",
        "sql": """
            SELECT match_description, team1, team2, winning_team,
                   victory_margin, victory_type, venue_name, match_date
            FROM v_recent_matches
            LIMIT 20;
        """,
    },

    "Q11: Player performance across formats": {
        "level": "Intermediate",
        "question": "Compare players' performance across formats (min. 2 formats "
                     "played): total runs in Test/ODI/T20I and overall batting average.",
        "sql": """
            SELECT p.full_name,
                   SUM(CASE WHEN pc.format = 'Test' THEN pc.total_runs ELSE 0 END) AS test_runs,
                   SUM(CASE WHEN pc.format = 'ODI'  THEN pc.total_runs ELSE 0 END) AS odi_runs,
                   SUM(CASE WHEN pc.format = 'T20I' THEN pc.total_runs ELSE 0 END) AS t20i_runs,
                   ROUND(AVG(pc.batting_average), 2) AS overall_batting_avg,
                   COUNT(DISTINCT pc.format) AS formats_played
            FROM player_career_stats pc
            JOIN players p ON pc.player_id = p.player_id
            GROUP BY p.player_id
            HAVING COUNT(DISTINCT pc.format) >= 2;
        """,
    },

    "Q12: Home vs away performance": {
        "level": "Intermediate",
        "question": "Analyze each team's performance at home vs away, comparing "
                     "venue country to team's country.",
        "sql": """
            SELECT t.team_name,
                   SUM(CASE WHEN v.country = t.country AND m.winning_team_id = t.team_id
                            THEN 1 ELSE 0 END) AS home_wins,
                   SUM(CASE WHEN v.country <> t.country AND m.winning_team_id = t.team_id
                            THEN 1 ELSE 0 END) AS away_wins
            FROM matches m
            JOIN teams t ON t.team_id IN (m.team1_id, m.team2_id)
            LEFT JOIN venues v ON m.venue_id = v.venue_id
            GROUP BY t.team_name
            ORDER BY home_wins DESC;
        """,
    },

    "Q13: Batting partnerships >= 100 runs": {
        "level": "Intermediate",
        "question": "Identify consecutive-position batting partnerships with a "
                     "combined 100+ runs in the same innings.",
        "sql": """
            SELECT p1.full_name AS batsman_1,
                   p2.full_name AS batsman_2,
                   pt.partnership_runs,
                   pt.innings_no,
                   pt.match_id
            FROM partnerships pt
            JOIN players p1 ON pt.player1_id = p1.player_id
            JOIN players p2 ON pt.player2_id = p2.player_id
            WHERE pt.partnership_runs >= 100
            ORDER BY pt.partnership_runs DESC;
        """,
    },

    "Q14: Bowling performance by venue": {
        "level": "Intermediate",
        "question": "For bowlers with 3+ matches at the same venue (>=4 overs each "
                     "match), find avg economy, total wickets, matches played there.",
        "sql": """
            SELECT p.full_name, v.venue_name,
                   ROUND(AVG(bw.economy_rate), 2) AS avg_economy,
                   SUM(bw.wickets_taken) AS total_wickets,
                   COUNT(DISTINCT bw.match_id) AS matches_at_venue
            FROM bowling_stats bw
            JOIN players p ON bw.player_id = p.player_id
            JOIN matches m ON bw.match_id = m.match_id
            JOIN venues v ON m.venue_id = v.venue_id
            WHERE bw.overs_bowled >= 4
            GROUP BY p.player_id, v.venue_id
            HAVING COUNT(DISTINCT bw.match_id) >= 3;
        """,
    },

    "Q15: Performance in close matches": {
        "level": "Intermediate",
        "question": "A close match = decided by <50 runs OR <5 wickets. Find each "
                     "player's avg runs, total close matches, and wins in those.",
        "sql": """
            WITH close_matches AS (
                SELECT match_id, winning_team_id
                FROM matches
                WHERE (victory_type = 'runs' AND victory_margin < 50)
                   OR (victory_type = 'wickets' AND victory_margin < 5)
            )
            SELECT p.full_name,
                   ROUND(AVG(b.runs_scored), 2) AS avg_runs_close_matches,
                   COUNT(DISTINCT b.match_id) AS close_matches_played,
                   SUM(CASE WHEN cm.winning_team_id IS NOT NULL THEN 1 ELSE 0 END) AS close_matches_won
            FROM batting_stats b
            JOIN close_matches cm ON b.match_id = cm.match_id
            JOIN players p ON b.player_id = p.player_id
            GROUP BY p.player_id
            ORDER BY avg_runs_close_matches DESC;
        """,
    },

    "Q16: Yearly batting trend since 2020": {
        "level": "Intermediate",
        "question": "For matches since 2020, show each player's avg runs and avg "
                     "strike rate per year (min. 5 matches that year).",
        "sql": f"""
            SELECT p.full_name,
                   {"EXTRACT(YEAR FROM m.match_date)::text" if IS_POSTGRES else "strftime('%Y', m.match_date)"} AS year,
                   ROUND(AVG(b.runs_scored), 2) AS avg_runs,
                   ROUND(AVG(b.strike_rate), 2) AS avg_strike_rate,
                   COUNT(*) AS matches_played
            FROM batting_stats b
            JOIN matches m ON b.match_id = m.match_id
            JOIN players p ON b.player_id = p.player_id
            WHERE m.match_date >= '2020-01-01'
            GROUP BY p.player_id, p.full_name, year
            HAVING COUNT(*) >= 5
            ORDER BY p.full_name, year;
        """,
    },

    # ============================= ADVANCED =============================
    "Q17: Toss impact on match outcome": {
        "level": "Advanced",
        "question": "What % of matches are won by the toss-winning team, broken "
                     "down by toss decision (bat/bowl)?",
        "sql": """
            SELECT toss_decision,
                   COUNT(*) AS total_matches,
                   SUM(CASE WHEN toss_winner_id = winning_team_id THEN 1 ELSE 0 END) AS won_after_toss,
                   ROUND(100.0 * SUM(CASE WHEN toss_winner_id = winning_team_id THEN 1 ELSE 0 END)
                         / COUNT(*), 2) AS win_pct
            FROM matches
            WHERE toss_decision IS NOT NULL
            GROUP BY toss_decision;
        """,
    },

    "Q18: Most economical limited-overs bowlers": {
        "level": "Advanced",
        "question": "Bowlers in ODI/T20 with >=10 matches, >=2 overs/match avg: "
                     "overall economy rate and total wickets.",
        "sql": """
            SELECT p.full_name,
                   ROUND(AVG(bw.economy_rate), 2) AS overall_economy,
                   SUM(bw.wickets_taken) AS total_wickets,
                   COUNT(DISTINCT bw.match_id) AS matches_played
            FROM bowling_stats bw
            JOIN players p ON bw.player_id = p.player_id
            JOIN matches m ON bw.match_id = m.match_id
            WHERE m.match_type IN ('ODI', 'T20I')
            GROUP BY p.player_id
            HAVING COUNT(DISTINCT bw.match_id) >= 10
               AND AVG(bw.overs_bowled) >= 2
            ORDER BY overall_economy ASC;
        """,
    },

    "Q19: Most consistent batsmen": {
        "level": "Advanced",
        "question": "Since 2022, players facing >=10 balls/innings: avg runs and "
                     "std-dev of runs (lower = more consistent).",
        "sql": """
            SELECT p.full_name,
                   ROUND(AVG(b.runs_scored), 2) AS avg_runs,
                   ROUND(
                       SQRT(AVG(b.runs_scored * b.runs_scored) - AVG(b.runs_scored) * AVG(b.runs_scored)),
                   2) AS stddev_runs,
                   COUNT(*) AS innings_played
            FROM batting_stats b
            JOIN matches m ON b.match_id = m.match_id
            JOIN players p ON b.player_id = p.player_id
            WHERE m.match_date >= '2022-01-01'
              AND b.balls_faced >= 10
            GROUP BY p.player_id
            ORDER BY stddev_runs ASC;
        """,
    },

    "Q20: Format-wise matches and batting average": {
        "level": "Advanced",
        "question": "Players with 20+ total matches across formats: count of Test/"
                     "ODI/T20 matches and batting average per format.",
        "sql": """
            SELECT p.full_name,
                   SUM(CASE WHEN pc.format = 'Test' THEN pc.matches_played ELSE 0 END) AS test_matches,
                   SUM(CASE WHEN pc.format = 'ODI'  THEN pc.matches_played ELSE 0 END) AS odi_matches,
                   SUM(CASE WHEN pc.format = 'T20I' THEN pc.matches_played ELSE 0 END) AS t20_matches,
                   ROUND(AVG(CASE WHEN pc.format = 'Test' THEN pc.batting_average END), 2) AS test_avg,
                   ROUND(AVG(CASE WHEN pc.format = 'ODI'  THEN pc.batting_average END), 2) AS odi_avg,
                   ROUND(AVG(CASE WHEN pc.format = 'T20I' THEN pc.batting_average END), 2) AS t20_avg
            FROM player_career_stats pc
            JOIN players p ON pc.player_id = p.player_id
            GROUP BY p.player_id
            HAVING SUM(pc.matches_played) >= 20;
        """,
    },

    "Q21: Weighted performance ranking (bat + bowl + field)": {
        "level": "Advanced",
        "question": "Combine batting, bowling, and fielding into one weighted score "
                     "per the given formula, ranked by format.",
        "sql": """
            SELECT p.full_name,
                   pc.format,
                   ROUND(
                       (pc.total_runs * 0.01) + (pc.batting_average * 0.5)
                       + (COALESCE(sr.avg_strike_rate, 0) * 0.3)
                       + (pc.total_wickets * 2) + ((50 - COALESCE(pc.bowling_average, 50)) * 0.5)
                       + ((6 - COALESCE(pc.economy_rate, 6)) * 2)
                       + (pc.catches * 3) + (pc.stumpings * 5)
                   , 2) AS weighted_score,
                   RANK() OVER (PARTITION BY pc.format ORDER BY
                       (pc.total_runs * 0.01) + (pc.batting_average * 0.5) DESC
                   ) AS format_rank
            FROM player_career_stats pc
            JOIN players p ON pc.player_id = p.player_id
            LEFT JOIN (
                SELECT player_id, AVG(strike_rate) AS avg_strike_rate
                FROM batting_stats GROUP BY player_id
            ) sr ON sr.player_id = pc.player_id
            ORDER BY pc.format, weighted_score DESC;
        """,
    },

    "Q22: Head-to-head team analysis": {
        "level": "Advanced",
        "question": "For team pairs with >=5 matches in the last 3 years: total "
                     "matches, wins each, avg victory margin, win % overall.",
        "sql": f"""
            SELECT t1.team_name AS team_a,
                   t2.team_name AS team_b,
                   COUNT(*) AS total_matches,
                   SUM(CASE WHEN m.winning_team_id = m.team1_id THEN 1 ELSE 0 END) AS team_a_wins,
                   SUM(CASE WHEN m.winning_team_id = m.team2_id THEN 1 ELSE 0 END) AS team_b_wins,
                   ROUND(AVG(m.victory_margin), 2) AS avg_victory_margin
            FROM matches m
            JOIN teams t1 ON m.team1_id = t1.team_id
            JOIN teams t2 ON m.team2_id = t2.team_id
            WHERE m.match_date >= {"CURRENT_DATE - INTERVAL '3 years'" if IS_POSTGRES else "date('now', '-3 years')"}
            GROUP BY t1.team_id, t2.team_id
            HAVING COUNT(*) >= 5;
        """,
    },

    "Q23: Recent player form (last 10 innings)": {
        "level": "Advanced",
        "question": "Last 10 innings per player: avg last-5 vs last-10 runs, recent "
                     "strike rate, scores >50, consistency, and Form category.",
        "sql": """
            WITH ranked_innings AS (
                SELECT b.*, m.match_date,
                       ROW_NUMBER() OVER (PARTITION BY b.player_id ORDER BY m.match_date DESC) AS rn
                FROM batting_stats b
                JOIN matches m ON b.match_id = m.match_id
            )
            SELECT p.full_name,
                   ROUND(AVG(CASE WHEN rn <= 5  THEN runs_scored END), 2) AS avg_last_5,
                   ROUND(AVG(CASE WHEN rn <= 10 THEN runs_scored END), 2) AS avg_last_10,
                   ROUND(AVG(CASE WHEN rn <= 10 THEN strike_rate END), 2) AS recent_strike_rate,
                   SUM(CASE WHEN rn <= 10 AND runs_scored > 50 THEN 1 ELSE 0 END) AS scores_above_50,
                   CASE
                       WHEN AVG(CASE WHEN rn <= 5 THEN runs_scored END) >= 50 THEN 'Excellent Form'
                       WHEN AVG(CASE WHEN rn <= 5 THEN runs_scored END) >= 35 THEN 'Good Form'
                       WHEN AVG(CASE WHEN rn <= 5 THEN runs_scored END) >= 20 THEN 'Average Form'
                       ELSE 'Poor Form'
                   END AS form_category
            FROM ranked_innings ri
            JOIN players p ON ri.player_id = p.player_id
            WHERE rn <= 10
            GROUP BY p.player_id;
        """,
    },

    "Q24: Best batting partnership combinations": {
        "level": "Advanced",
        "question": "Pairs with >=5 partnerships: avg partnership runs, count >50, "
                     "highest partnership, success rate — ranked.",
        "sql": """
            SELECT p1.full_name AS player_1,
                   p2.full_name AS player_2,
                   COUNT(*) AS partnerships_played,
                   ROUND(AVG(pt.partnership_runs), 2) AS avg_partnership_runs,
                   SUM(CASE WHEN pt.partnership_runs > 50 THEN 1 ELSE 0 END) AS partnerships_above_50,
                   MAX(pt.partnership_runs) AS highest_partnership,
                   ROUND(100.0 * SUM(CASE WHEN pt.partnership_runs > 50 THEN 1 ELSE 0 END)
                         / COUNT(*), 2) AS success_rate_pct
            FROM partnerships pt
            JOIN players p1 ON pt.player1_id = p1.player_id
            JOIN players p2 ON pt.player2_id = p2.player_id
            GROUP BY pt.player1_id, pt.player2_id
            HAVING COUNT(*) >= 5
            ORDER BY success_rate_pct DESC;
        """,
    },

    "Q25: Career trajectory (time-series by quarter)": {
        "level": "Advanced",
        "question": "Quarterly avg runs & strike rate per player (>=6 quarters, "
                     ">=3 matches/quarter); trend vs prior quarter; career phase label.",
        "sql": f"""
            WITH quarterly AS (
                SELECT b.player_id,
                       {"EXTRACT(YEAR FROM m.match_date)::text || '-Q' || CEIL(EXTRACT(MONTH FROM m.match_date) / 3.0)::text" if IS_POSTGRES else "strftime('%Y', m.match_date) || '-Q' || ((CAST(strftime('%m', m.match_date) AS INTEGER) - 1) / 3 + 1)"} AS quarter,
                       AVG(b.runs_scored) AS avg_runs,
                       AVG(b.strike_rate) AS avg_strike_rate,
                       COUNT(*) AS matches_in_quarter
                FROM batting_stats b
                JOIN matches m ON b.match_id = m.match_id
                GROUP BY b.player_id, quarter
                HAVING COUNT(*) >= 3
            ),
            trended AS (
                SELECT q.*, p.full_name,
                       LAG(avg_runs) OVER (PARTITION BY q.player_id ORDER BY quarter) AS prev_quarter_runs,
                       COUNT(*) OVER (PARTITION BY q.player_id) AS total_quarters
                FROM quarterly q
                JOIN players p ON q.player_id = p.player_id
            )
            SELECT full_name, quarter, ROUND(avg_runs, 2) AS avg_runs,
                   ROUND(avg_strike_rate, 2) AS avg_strike_rate,
                   CASE
                       WHEN prev_quarter_runs IS NULL THEN 'N/A'
                       WHEN avg_runs > prev_quarter_runs THEN 'Improving'
                       WHEN avg_runs < prev_quarter_runs THEN 'Declining'
                       ELSE 'Stable'
                   END AS trend_vs_prev_quarter
            FROM trended
            WHERE total_quarters >= 6
            ORDER BY full_name, quarter;
        """,
    },
}
