"""st.session_state <-> DB-backed session glue. Every page calls
require_login() at the top; it re-resolves session_token -> user_id on every
Streamlit rerun (a cheap primary-key lookup, not re-authentication).

NOTE: the session_token currently lives only in st.session_state, so a full
browser refresh (not just a Streamlit rerun) logs the user out. The `sessions`
table it resolves against is otherwise complete; swapping in a persistent
browser cookie (e.g. via streamlit-cookies-controller) later is a change to
this file only, not to the DB layer or any page.
"""

import streamlit as st

from storage.repositories import users_repo

SESSION_STATE_KEY = "session_token"


def get_current_user_id() -> int | None:
    token = st.session_state.get(SESSION_STATE_KEY)
    return users_repo.resolve_session(token) if token else None


def set_session(session_token: str) -> None:
    st.session_state[SESSION_STATE_KEY] = session_token


def clear_session() -> None:
    token = st.session_state.get(SESSION_STATE_KEY)
    if token:
        users_repo.delete_session(token)
    st.session_state.pop(SESSION_STATE_KEY, None)


def require_login() -> int:
    """Returns the logged-in user_id, or halts page rendering with st.stop()."""
    user_id = get_current_user_id()
    if user_id is None:
        st.warning("Please log in from the Home page to continue.")
        st.stop()
    return user_id
