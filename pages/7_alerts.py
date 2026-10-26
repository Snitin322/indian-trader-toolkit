import streamlit as st

from auth import session

st.title("Alerts")
session.require_login()

st.info("Price/stop/target alerts land in Phase 8 of the build.")
