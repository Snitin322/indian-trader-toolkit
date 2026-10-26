import streamlit as st

from auth import session

st.title("Mutual Fund Copycat")
session.require_login()

st.info(
    "Lands in Phase 11 of the build: pick a scheme, see its AMFI-published monthly "
    "portfolio, and the month-over-month bought/added/trimmed/sold diff, with a "
    "'size to my budget' hand-off into the same Risk & Budget -> Order Ticket pipeline "
    "used by the technical track."
)
