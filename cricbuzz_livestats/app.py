"""
app.py
------
Main entry point for the Streamlit app. This is the Home page.
Other pages live in pages/ and Streamlit auto-discovers them for the
sidebar navigation.
"""

import streamlit as st
from config import config

st.set_page_config(
    page_title="Cricbuzz LiveStats",
    page_icon="🏏",
    layout="wide",
)

st.title("🏏 Cricbuzz LiveStats: Real-Time Cricket Insights & SQL-Based Analytics")

st.markdown("""
Welcome! This dashboard combines **live cricket data** (via the Cricbuzz API)
with a **SQL-driven analytics engine** built on a normalized relational database.
""")

warnings = config.validate()
for w in warnings:
    st.warning(f"⚠️ {w}")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 What's inside")
    st.markdown("""
    - **Live Matches** — real-time scores pulled from the Cricbuzz API
    - **Top Player Stats** — most runs, wickets, hundreds, etc. from the API
    - **SQL Queries & Analytics** — 25 practice queries (beginner → advanced)
      run against a seeded relational database
    - **CRUD Operations** — add / update / delete player records
    """)

with col2:
    st.subheader("🛠️ Tech stack")
    st.markdown("""
    - **Frontend**: Streamlit
    - **Backend / API layer**: Python `requests` + Cricbuzz API (RapidAPI)
    - **Database**: SQLite by default (swap to PostgreSQL/MySQL via `.env`)
    - **Data layer**: SQLAlchemy + pandas
    """)

st.divider()
st.subheader("🚀 Getting started")
st.code(
    "pip install -r requirements.txt\n"
    "cp .env.example .env        # then fill in your RapidAPI key\n"
    "python -m database.seed_data   # creates & seeds the SQLite DB\n"
    "streamlit run app.py",
    language="bash",
)

st.info("Use the sidebar to navigate between pages.")
