import streamlit as st
from datetime import date

from models.entities import Player
from services import crud_service
from services.crud_service import CRUDError

st.set_page_config(page_title="CRUD Operations", page_icon="🛠️", layout="wide")
st.title("🛠️ CRUD Operations — Players")

tab_create, tab_read, tab_update, tab_delete = st.tabs(
    ["➕ Create", "📖 Read", "✏️ Update", "🗑️ Delete"]
)

ROLES = ["Batsman", "Bowler", "All-rounder", "Wicket-keeper"]

# ---------------------------------------------------------------- CREATE
with tab_create:
    st.subheader("Add a new player")
    with st.form("add_player_form", clear_on_submit=True):
        name = st.text_input("Full name")
        country = st.text_input("Country")
        role = st.selectbox("Playing role", ROLES)
        bat_style = st.text_input("Batting style (e.g. Right-hand bat)")
        bowl_style = st.text_input("Bowling style (optional)")
        dob = st.date_input("Date of birth", value=date(1995, 1, 1),
                             min_value=date(1950, 1, 1), max_value=date.today())
        submitted = st.form_submit_button("Add player")

    if submitted:
        try:
            crud_service.add_player(Player(
                full_name=name, country=country, playing_role=role,
                batting_style=bat_style or None, bowling_style=bowl_style or None,
                date_of_birth=dob,
            ))
            st.success(f"Player '{name}' added successfully.")
        except CRUDError as e:
            st.error(str(e))

# ------------------------------------------------------------------ READ
with tab_read:
    st.subheader("All players")
    search = st.text_input("Search by name (optional)")
    df = crud_service.search_players(search) if search else crud_service.get_all_players()
    st.dataframe(df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------- UPDATE
with tab_update:
    st.subheader("Update a player")
    all_players = crud_service.get_all_players()
    if all_players.empty:
        st.info("No players yet — add one in the Create tab first.")
    else:
        options = dict(zip(all_players["full_name"], all_players["player_id"]))
        chosen_name = st.selectbox("Select player", list(options.keys()))
        pid = options[chosen_name]
        row = all_players[all_players["player_id"] == pid].iloc[0]

        with st.form("update_player_form"):
            u_name = st.text_input("Full name", value=row["full_name"])
            u_country = st.text_input("Country", value=row["country"])
            u_role = st.selectbox("Playing role", ROLES, index=ROLES.index(row["playing_role"]))
            u_bat = st.text_input("Batting style", value=row["batting_style"] or "")
            u_bowl = st.text_input("Bowling style", value=row["bowling_style"] or "")
            update_submitted = st.form_submit_button("Save changes")

        if update_submitted:
            try:
                crud_service.update_player(Player(
                    player_id=int(pid), full_name=u_name, country=u_country,
                    playing_role=u_role, batting_style=u_bat or None,
                    bowling_style=u_bowl or None,
                ))
                st.success("Player updated.")
            except CRUDError as e:
                st.error(str(e))

# ---------------------------------------------------------------- DELETE
with tab_delete:
    st.subheader("Delete a player")
    all_players = crud_service.get_all_players()
    if all_players.empty:
        st.info("No players to delete.")
    else:
        options = dict(zip(all_players["full_name"], all_players["player_id"]))
        chosen_name = st.selectbox("Select player to delete", list(options.keys()), key="del_select")
        if st.button("Delete player", type="primary"):
            try:
                crud_service.delete_player(int(options[chosen_name]))
                st.success(f"Deleted '{chosen_name}'.")
                st.rerun()
            except CRUDError as e:
                st.error(str(e))
