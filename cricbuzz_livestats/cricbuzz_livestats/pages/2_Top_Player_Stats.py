import streamlit as st
from services.data_service import fetch_top_batting_stats

st.set_page_config(page_title="Top Player Stats", page_icon="📊", layout="wide")
st.title("📊 Top Player Stats")

stat_options = {
    "Most Runs": "mostRuns",
    "Highest Score": "highestScore",
    "Most Hundreds": "mostHundreds",
    "Most Fifties": "mostFifties",
}

choice = st.selectbox("Choose a stat category", list(stat_options.keys()))

df, error = fetch_top_batting_stats(stat_options[choice])

if error:
    st.warning(error)
else:
    st.dataframe(df, use_container_width=True, hide_index=True)
