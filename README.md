# 🏏 Cricbuzz LiveStats: Real-Time Cricket Insights & SQL-Based Analytics

**🔗 Live demo:** [cricbuzzlivestats-hpkpjq8hjpbqffacvbjvjn.streamlit.app](https://cricbuzzlivestats-hpkpjq8hjpbqffacvbjvjn.streamlit.app/)

A cricket analytics dashboard combining **live data from the Cricbuzz API**
with a **SQL-driven analytics engine**, built with Python, Streamlit, and
SQLAlchemy. Includes full CRUD, 25 SQL practice queries (beginner →
advanced), and a database-agnostic design (SQLite / PostgreSQL / MySQL).

---

## 📁 Project structure

```
cricbuzz_livestats/
├── app.py                      # Streamlit entry point (Home page)
├── config.py                   # Central env-driven configuration
├── requirements.txt
├── .env.example                 # Copy to .env and fill in secrets
├── .gitignore
│
├── api/
│   └── cricbuzz_client.py       # Cricbuzz API wrapper (retries, error handling)
│
├── database/
│   ├── schema.sql                # CREATE TABLE / VIEW / INDEX statements
│   └── seed_data.py               # Populates realistic sample data
│
├── services/
│   ├── data_service.py           # Shapes API JSON into DataFrames for the UI
│   └── crud_service.py           # Create/Read/Update/Delete for players
│
├── models/
│   └── entities.py                # Player / Team / Venue / Match dataclasses
│
├── sql/
│   └── queries.py                 # All 25 practice SQL questions + queries
│
├── pages/                         # Streamlit auto-discovers these
│   ├── 1_Live_Matches.py
│   ├── 2_Top_Player_Stats.py
│   ├── 3_SQL_Queries_Analytics.py
│   └── 4_CRUD_Operations.py
│
├── utils/
│   └── db_connection.py           # Single source of truth for DB connections
│
└── data/                          # SQLite file lives here (gitignored)
```

---

## 🚀 Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get a Cricbuzz API key
1. Sign up at [RapidAPI](https://rapidapi.com).
2. Subscribe to the **Cricbuzz Cricket API** (free tier is fine for this project).
3. Copy your `X-RapidAPI-Key`.

### 3. Configure environment variables
```bash
cp .env.example .env
```
Edit `.env`:
```
RAPIDAPI_KEY=your_key_here
RAPIDAPI_HOST=cricbuzz-cricket.p.rapidapi.com
DB_TYPE=sqlite
SQLITE_PATH=data/cricbuzz.db
```
**Never commit `.env`** — it's already in `.gitignore`.

### 4. Create & seed the database
```bash
python -m database.seed_data
```
This creates all tables (via `database/schema.sql`) and fills them with
realistic sample data spanning ~6 years, so all 25 SQL queries return
meaningful results.

### 5. Run the app
```bash
streamlit run app.py
```

---

## 🗄️ Using PostgreSQL

The project ships with a dedicated `database/schema_postgres.sql` and
automatically picks it based on `DB_TYPE` — you don't need to edit any
Python code.

1. Create the database (e.g. in pgAdmin4, or via `psql`):
   ```sql
   CREATE DATABASE cricbuzz_livestats;
   ```
2. Install the driver (already in `requirements.txt`):
   ```bash
   pip install -r requirements.txt
   ```
3. Edit `.env`:
   ```
   DB_TYPE=postgresql
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=cricbuzz_livestats
   DB_USER=postgres
   DB_PASSWORD=your_actual_password
   ```
4. Seed it:
   ```bash
   python -m database.seed_data
   ```
   This runs `database/schema_postgres.sql` (not the SQLite one) and
   populates it the same way.

**Note on dialect differences:** `utils/db_connection.insert_ignore()`
switches between SQLite's `INSERT OR IGNORE` and Postgres's
`INSERT ... ON CONFLICT DO NOTHING` automatically. `sql/queries.py`
similarly switches date-arithmetic syntax (`date('now', '-30 day')` vs
`CURRENT_DATE - INTERVAL '30 days'`, `strftime()` vs `EXTRACT()`) for
the 5 queries that need it (Q2, Q8, Q16, Q22, Q25). This conversion was
checked carefully by hand but **not run against a live PostgreSQL
server** in the environment this was built in — if you hit a syntax
error on `python -m database.seed_data` or a specific query, paste the
exact error back and it can be fixed in one pass.

### Switching to MySQL instead
Same idea: set `DB_TYPE=mysql`, install `mysql-connector-python`, and
you'd want a `schema_mysql.sql` (not included yet — ask if you need it,
since MySQL's date functions and `AUTO_INCREMENT` differ from both
SQLite and Postgres).

---

## 📄 Pages

| Page | Purpose | Data source |
|---|---|---|
| Home | Project overview & setup instructions | — |
| Live Matches | Real-time scores & status | Cricbuzz API |
| Top Player Stats | Most runs / hundreds / etc. | Cricbuzz API |
| SQL Queries & Analytics | 25 practice queries, run on demand | Seeded SQL DB |
| CRUD Operations | Add / update / delete player records | Seeded SQL DB |

---

## 🧮 SQL Practice Questions

25 questions across 3 difficulty levels live in `sql/queries.py`:
- **Beginner (1–8):** SELECT, WHERE, GROUP BY, ORDER BY
- **Intermediate (9–16):** JOINs, subqueries, aggregates
- **Advanced (17–25):** window functions, CTEs, multi-metric ranking

Each entry includes the business question, the SQL, and its difficulty —
the Analytics page lets you pick one, inspect the SQL, and run it.

---

## 🔐 Security notes

- API keys and DB credentials are read from environment variables only —
  never hardcoded.
- `.env` and the SQLite file are gitignored.
- All SQL is parameterized (SQLAlchemy `text()` with bound params) to
  prevent SQL injection in the CRUD layer.

---

## 🧪 Testing

Quick manual checks:
```bash
# Confirm all 25 queries run cleanly
python3 -c "
from sql.queries import QUERIES
from utils.db_connection import run_query
for title, q in QUERIES.items():
    df = run_query(q['sql'])
    print(title, len(df), 'rows')
"
```

---

## 📌 Notes on data

The live Cricbuzz API only exposes *current* scores/standings, not years
of historical relational data. So this project keeps two data paths:
- **Live pages** (Live Matches, Top Player Stats) call the Cricbuzz API directly.
- **Analytics + CRUD** run against the seeded local SQL database, which
  simulates realistic historical data so the 25 SQL questions (partnerships,
  quarterly trends, head-to-head records, etc.) have something to analyze.

To go further: extend `services/data_service.py` to persist live API pulls
into the same tables over time, and the analytics will reflect real history.
