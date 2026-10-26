import streamlit as st

from auth import session

st.title("Time Machine")
session.require_login()

st.info("Monte Carlo simulation + historical backtest land in Phase 5 of the build.")
