import streamlit as st

from auth import session

st.title("Scanner")
user_id = session.require_login()

st.info("The timeframe-first technical scanner lands in Phase 3 of the build.")
