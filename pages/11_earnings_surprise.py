import streamlit as st

from auth import session

st.title("Earnings Surprise")
session.require_login()

st.info(
    "Lands in Phase 12 of the build. Caveat that will always be shown here: no free "
    "Indian data source provides analyst consensus estimates, so this flags results "
    "that deviate sharply from the company's OWN trailing growth trend — not a true "
    "beat/miss versus Street expectations."
)
