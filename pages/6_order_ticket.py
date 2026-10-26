import streamlit as st

from auth import session

st.title("Order Ticket")
session.require_login()

st.info(
    "The broker order ticket + confirmation gate land in Phase 7 of the build. "
    "Reminder: paper trading will remain the default, and no real order will ever "
    "be reachable without an explicit checkbox + typed confirmation phrase + "
    "quantity re-entry, all re-checked against a fresh risk-manager PASS."
)
