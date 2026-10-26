import streamlit as st

from auth import session

st.title("Risk & Budget")
session.require_login()

st.info("Risk manager (PASS/BLOCK) + position sizer land in Phase 6 of the build.")
