"""Streamlit entrypoint: login/register gate, then the page router.

Gating flags (resolved fresh from the DB on every rerun, never cached in
st.session_state as the source of truth):
  is_logged_in      -> auth.session.get_current_user_id()
  kite_connected    -> storage.repositories.kite_credentials_repo.is_connected()
  has_selected_interval -> storage.repositories.user_config_repo.has_selected_interval()

IMPORTANT: st.navigation() must be called on EVERY run, including the
logged-out one. If it's skipped on some runs, Streamlit falls back to its
legacy automatic pages/-directory sidebar, which lists every page file
unconditionally and defeats the gating below (each page still enforces
session.require_login() internally, but the kite-connected/interval gates
would otherwise be silently bypassed in the sidebar UI).
"""

import streamlit as st

import config
from auth import session
from storage.db import init_db
from storage.repositories import kite_credentials_repo, user_config_repo

st.set_page_config(page_title="AI Trading Free Tool", page_icon="📈", layout="wide")

init_db(config.DB_PATH)

user_id = session.get_current_user_id()

if user_id is None:
    pages = [st.Page("pages/0_login.py", title="Log in / Register", icon="🔑", default=True)]
else:
    kite_connected = kite_credentials_repo.is_connected(user_id)
    has_interval = user_config_repo.has_selected_interval(user_id)

    with st.sidebar:
        st.success(f"Logged in (user #{user_id})")
        if st.button("Log out"):
            session.clear_session()
            st.rerun()
        st.divider()
        st.caption("Broker: " + ("connected" if kite_connected else "not connected"))
        st.caption("Scan timeframe: " + ("set" if has_interval else "not set"))

    # A pending Kite redirect (?request_token=...) must always land on
    # Connect Broker to be processed, even if kite_connected is already
    # True from an earlier session today — otherwise a reconnect's
    # request_token gets stranded in the URL with nowhere to be read.
    has_pending_kite_callback = bool(st.query_params.get("request_token"))

    pages = [
        st.Page(
            "pages/1_connect_broker.py",
            title="Connect Broker",
            icon="🔌",
            default=has_pending_kite_callback or not kite_connected,
        ),
        st.Page("pages/8_account_settings.py", title="Account Settings", icon="⚙️"),
        st.Page("pages/10_bulk_deals_promoters.py", title="Bulk Deals & Promoter Activity", icon="🏦"),
        st.Page("pages/11_earnings_surprise.py", title="Earnings Surprise", icon="📊"),
    ]
    if kite_connected:
        pages += [
            st.Page(
                "pages/2_scanner.py", title="Scanner", icon="📈",
                default=not has_interval and not has_pending_kite_callback,
            ),
            st.Page("pages/3_watchlist_entry_exit.py", title="Watchlist / Entry / Exit", icon="🎯"),
            st.Page("pages/4_time_machine.py", title="Time Machine", icon="🔮"),
            st.Page("pages/5_risk_budget.py", title="Risk & Budget", icon="🛡️"),
            st.Page("pages/6_order_ticket.py", title="Order Ticket", icon="🧾"),
            st.Page("pages/7_alerts.py", title="Alerts", icon="🔔"),
            st.Page("pages/9_screener.py", title="Screener", icon="🔎"),
            st.Page("pages/12_mf_copycat.py", title="MF Copycat", icon="📋"),
        ]

pg = st.navigation(pages)
pg.run()
