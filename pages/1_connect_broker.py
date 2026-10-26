import streamlit as st

from auth import session

st.title("Connect Broker")
user_id = session.require_login()

st.info(
    "Zerodha Kite Connect login flow lands in Phase 2 of the build. "
    "Until then, every other page stays locked for this account."
)
