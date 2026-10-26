import time

import streamlit as st

from auth import app_auth, session
from storage.repositories import users_repo

# The cookie-set component call needs a moment to actually run in the
# browser before we force a rerun — otherwise st.rerun() can cut it off
# mid-flight and the session cookie never gets written. Confirmed live:
# without this, login appears to work but doesn't survive a page reload.
_COOKIE_WRITE_DELAY_SECONDS = 0.3

st.title("AI Trading Free Tool")
st.caption("NSE/BSE technical scanning + fundamental screening, with Zerodha Kite Connect.")

login_tab, register_tab = st.tabs(["Log in", "Register"])

with login_tab:
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")
    if submitted:
        try:
            user_id, token = app_auth.login(email, password)
            session.set_session(token)
            time.sleep(_COOKIE_WRITE_DELAY_SECONDS)
            st.rerun()
        except app_auth.InvalidCredentialsError:
            st.error("Incorrect email or password.")

with register_tab:
    with st.form("register_form"):
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input(
            "Password (min 8 characters)", type="password", key="reg_password"
        )
        reg_submitted = st.form_submit_button("Create account")
    if reg_submitted:
        try:
            user_id, token = app_auth.register(reg_email, reg_password)
            session.set_session(token)
            time.sleep(_COOKIE_WRITE_DELAY_SECONDS)
            st.rerun()
        except app_auth.InvalidEmailError:
            st.error("Please enter a valid email address.")
        except app_auth.WeakPasswordError as exc:
            st.error(str(exc))
        except users_repo.EmailAlreadyRegisteredError:
            st.error("That email is already registered. Try logging in instead.")
