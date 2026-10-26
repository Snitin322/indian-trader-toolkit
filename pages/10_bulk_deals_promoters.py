import streamlit as st

from auth import session

st.title("Bulk Deals & Promoter Activity")
session.require_login()

st.info(
    "The NSE/BSE bulk/block-deal and promoter-disclosure tracker lands in Phase 10. "
    "This data will be scraped from exchange pages (no official JSON API) and will "
    "always be labeled best-effort in this UI, same honesty policy as the rest of the app."
)
