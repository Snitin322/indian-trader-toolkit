import streamlit as st

from auth import session

st.title("Screener")
session.require_login()

st.info("The fundamental rule-based stock screener lands in Phase 9 of the build.")
