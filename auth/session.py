"""st.session_state <-> DB-backed session glue, backed by a browser cookie
so the session survives a full page navigation — not just a Streamlit
rerun. This matters specifically because the Kite Connect login redirect
(pages/1_connect_broker.py) is a real top-level browser navigation away to
kite.zerodha.com and back, which wipes st.session_state entirely; without
a cookie, the user would always land back on the login page with their
request_token stranded in the URL and nowhere to be processed. (Confirmed
live: this was a real bug, not a hypothetical — see PROGRESS.md.)

Every page calls require_login() at the top; it re-resolves
session_token -> user_id on every Streamlit rerun (a cheap primary-key
lookup, not re-authentication). The cookie only ever carries the opaque
session_token — the DB `sessions` table remains the source of truth, so a
stolen/expired cookie is worthless without a matching unexpired DB row.
"""

import streamlit as st
from streamlit_cookies_controller import CookieController

from storage.repositories import users_repo

SESSION_STATE_KEY = "session_token"
COOKIE_KEY = "trader_app_cookies"
COOKIE_NAME = "trader_session_token"
COOKIE_MAX_AGE_SECONDS = 12 * 3600


def _cookies() -> CookieController:
    """One controller per script run, shared across every call site within
    it (app.py's gate check and each page's require_login()) via the same
    session_state key — avoids instantiating the underlying component
    more than once per rerun."""
    return CookieController(key=COOKIE_KEY)


def get_current_user_id() -> int | None:
    token = st.session_state.get(SESSION_STATE_KEY)
    if not token:
        token = _cookies().get(COOKIE_NAME)
        if token:
            st.session_state[SESSION_STATE_KEY] = token
    if not token:
        return None
    return users_repo.resolve_session(token)


def set_session(session_token: str) -> None:
    st.session_state[SESSION_STATE_KEY] = session_token
    _cookies().set(COOKIE_NAME, session_token, max_age=COOKIE_MAX_AGE_SECONDS)


def clear_session() -> None:
    token = st.session_state.get(SESSION_STATE_KEY)
    if token:
        users_repo.delete_session(token)
    st.session_state.pop(SESSION_STATE_KEY, None)
    _cookies().remove(COOKIE_NAME)


def require_login() -> int:
    """Returns the logged-in user_id, or halts page rendering with st.stop()."""
    user_id = get_current_user_id()
    if user_id is None:
        st.warning("Please log in from the Home page to continue.")
        st.stop()
    return user_id
