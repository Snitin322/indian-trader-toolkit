import streamlit as st

from auth import session

st.title("Watchlist / Entry / Exit")
session.require_login()

st.info("Entry timer + exit planner land in Phase 4 of the build.")
