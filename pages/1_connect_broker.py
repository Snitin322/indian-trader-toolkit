from datetime import timedelta, timezone

import streamlit as st

import config
from auth import session
from integrations.kite import oauth
from storage.repositories import kite_credentials_repo

IST = timezone(timedelta(hours=5, minutes=30))

st.title("Connect Broker")
user_id = session.require_login()

# Kite redirects back here with ?request_token=... after a successful login.
# user_id above comes ONLY from our own session (auth.session), never from
# this URL — that's what stops one user's browser redirect from ever being
# able to write into another user's kite_credentials row.
request_token = st.query_params.get("request_token")

if request_token:
    try:
        session_data = oauth.complete_login(user_id, request_token)
        st.query_params.clear()
        st.success(f"Connected to Zerodha as {session_data.get('user_name') or session_data.get('user_id')}.")
        st.rerun()
    except oauth.KiteConfigError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"Could not complete Kite login: {exc}")

connected = kite_credentials_repo.is_connected(user_id)

if connected:
    expires_at = kite_credentials_repo.get_token_expiry(user_id)
    expires_ist = expires_at.astimezone(IST).strftime("%I:%M %p IST on %d %b") if expires_at else "later today"
    st.success(f"Zerodha account connected — good until **{expires_ist}**.")
    st.caption(
        "You do NOT need to do anything else right now. This stays connected across logging out "
        "of this app, restarting the server, or closing your browser — it only needs reconnecting "
        "once that time above passes (Kite's tokens expire daily; there's no way around that part)."
    )
    with st.expander("Reconnect anyway (switch Zerodha accounts, or something seems broken)"):
        st.caption(
            "Clicking below takes you to Zerodha's own login page. If your browser doesn't already "
            "have an active Zerodha web session, Zerodha will ask for your username/password/2FA "
            "again — that's normal Zerodha behavior, not this app, and isn't something to worry about."
        )
        try:
            st.link_button("Reconnect with Zerodha", oauth.get_login_url())
        except oauth.KiteConfigError as exc:
            st.error(str(exc))
else:
    st.info(
        "Connect your Zerodha account to unlock the Scanner, Time Machine, "
        "Risk & Budget, Order Ticket, Alerts, Screener and MF Copycat pages."
    )
    try:
        st.link_button("Log in with Zerodha", oauth.get_login_url())
    except oauth.KiteConfigError as exc:
        st.error(str(exc))
        st.caption(
            f"Set {config.KITE_API_KEY_ENV} and {config.KITE_API_SECRET_ENV} in your environment "
            "(from your Kite Connect developer app at developers.kite.trade) and restart the app."
        )
