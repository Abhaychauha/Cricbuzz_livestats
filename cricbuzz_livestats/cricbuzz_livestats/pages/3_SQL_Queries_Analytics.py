import streamlit as st
import plotly.express as px

from sql.queries import QUERIES
from utils.db_connection import run_query

st.set_page_config(page_title="SQL Queries & Analytics", page_icon="🧮", layout="wide")
st.title("🧮 SQL Queries & Analytics")
st.caption("25 practice questions — Beginner → Advanced — run against the seeded database.")

level_filter = st.sidebar.multiselect(
    "Filter by difficulty",
    ["Beginner", "Intermediate", "Advanced"],
    default=["Beginner", "Intermediate", "Advanced"],
)

filtered_titles = [
    title for title, q in QUERIES.items() if q["level"] in level_filter
]

selected_title = st.selectbox("Choose a question", filtered_titles)
selected = QUERIES[selected_title]

st.markdown(f"**Difficulty:** {selected['level']}")
st.markdown(f"**Business question:** {selected['question']}")

with st.expander("View SQL"):
    st.code(selected["sql"], language="sql")

if st.button("▶️ Run query", type="primary"):
    try:
        result_df = run_query(selected["sql"])
        st.success(f"Returned {len(result_df)} rows.")
        st.dataframe(result_df, use_container_width=True, hide_index=True)

        # Offer a quick chart when there's an obvious numeric column to plot
        numeric_cols = result_df.select_dtypes("number").columns.tolist()
        text_cols = result_df.select_dtypes("object").columns.tolist()
        if numeric_cols and text_cols and len(result_df) <= 30:
            fig = px.bar(
                result_df.head(20),
                x=text_cols[0],
                y=numeric_cols[0],
                title=f"{numeric_cols[0]} by {text_cols[0]}",
            )
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Query failed: {e}")
        st.info(
            "If the database hasn't been seeded yet, run:\n\n"
            "`python -m database.seed_data`"
        )
