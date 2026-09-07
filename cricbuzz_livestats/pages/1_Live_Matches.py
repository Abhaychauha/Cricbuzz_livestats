import streamlit as st
from services.data_service import fetch_live_matches

st.set_page_config(page_title="Live Matches", page_icon="🔴", layout="wide")
st.title("🔴 Live Matches")

st.caption("Pulled directly from the Cricbuzz API in real time.")

if st.button("🔄 Refresh"):
    st.cache_data.clear()


@st.cache_data(ttl=30)
def _load():
    return fetch_live_matches()


df, error = _load()

if error:
    st.warning(error)
else:
    for _, row in df.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 3, 2])
            c1.markdown(f"**{row['team1']}** vs **{row['team2']}**")
            c1.caption(row["series"])
            c2.markdown(f"{row['team1_score']}  \n{row['team2_score']}")
            c3.markdown(f"📍 {row['venue']}")
            st.caption(row["status"])
