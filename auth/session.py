"""st.session_state <-> DB-backed session glue, backed by a browser cookie
so the session survives a full page navigation — not just a Streamlit
rerun. This matters specifically because the Kite Connect login redirect
(pages/1_connect_broker.py) is a real top-level browser navigation away to
kite.zerodha.com and back, which wipes st.session_state entirely; without
a cookie, the user would always land back on the login page with their
request_token stranded in the URL and nowhere to be processed.

Reading the cookie uses st.context.cookies — a native, synchronous
Streamlit API (no custom component, no round-trip, no race condition).
Writing a cookie has no native Streamlit API, so it's done with a one-way
injected <script>document.cookie=...</script> via components.v1.html;
this was chosen over the bidirectional streamlit-cookies-controller
component used in an earlier version of this file, which read back its
own writes through an iframe postMessage round-trip that only resolves
*after* the next rerun — reliable in automated/scripted browser testing
(confirmed working there) but NOT reliable in normal interactive use: a
real click-triggered st.rerun() can fire before that round-trip settles,
silently dropping the cookie write. Confirmed as the actual cause of a
user-reported bug: "every time I restart the app, I have to log in and
reconnect to the broker again" — see PROGRESS.md.

Every page calls require_login() at the top; it re-resolves
session_token -> user_id on every Streamlit rerun (a cheap primary-key
lookup, not re-authentication). The cookie only ever carries the opaque
session_token — the DB `sessions` table remains the source of truth, so a
stolen/expired cookie is worthless without a matching unexpired DB row.
"""

import streamlit as st
import streamlit.components.v1 as components

from storage.repositories import users_repo

SESSION_STATE_KEY = "session_token"
COOKIE_NAME = "trader_session_token"
COOKIE_MAX_AGE_SECONDS = 12 * 3600


def _write_cookie(value: str, max_age_seconds: int) -> None:
    """One-way: inject a script that sets document.cookie and renders
    nothing. No return value is read back, so there's no race with a
    subsequent st.rerun() — the script executes as part of rendering this
    run's output, strictly before any later run can begin."""
    components.html(
        f"""
        <script>
        document.cookie = "{COOKIE_NAME}={value}; path=/; max-age={max_age_seconds}; SameSite=Lax";
        </script>
        """,
        height=0,
    )


def get_current_user_id() -> int | None:
    token = st.session_state.get(SESSION_STATE_KEY)
    if not token:
        token = st.context.cookies.get(COOKIE_NAME)
        if token:
            st.session_state[SESSION_STATE_KEY] = token
    if not token:
        return None
    return users_repo.resolve_session(token)


def set_session(session_token: str) -> None:
    st.session_state[SESSION_STATE_KEY] = session_token
    _write_cookie(session_token, COOKIE_MAX_AGE_SECONDS)


def clear_session() -> None:
    token = st.session_state.get(SESSION_STATE_KEY)
    if token:
        users_repo.delete_session(token)
    st.session_state.pop(SESSION_STATE_KEY, None)
    _write_cookie("", 0)


def require_login() -> int:
    """Returns the logged-in user_id, or halts page rendering with st.stop()."""
    user_id = get_current_user_id()
    if user_id is None:
        st.warning("Please log in from the Home page to continue.")
        st.stop()
    return user_id
