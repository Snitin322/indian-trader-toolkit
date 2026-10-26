import streamlit as st

import config
from auth import session
from integrations.kite import oauth
from storage.repositories import kite_credentials_repo

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
    st.success("Zerodha account connected for today's trading session.")
    st.caption("Kite access tokens expire daily (~7:30am IST) — you'll need to reconnect tomorrow.")
else:
    st.info(
        "Connect your Zerodha account to unlock the Scanner, Time Machine, "
        "Risk & Budget, Order Ticket, Alerts, Screener and MF Copycat pages."
    )

try:
    login_url = oauth.get_login_url()
    st.link_button(
        "Reconnect with Zerodha" if connected else "Log in with Zerodha",
        login_url,
    )
except oauth.KiteConfigError as exc:
    st.error(str(exc))
    st.caption(
        f"Set {config.KITE_API_KEY_ENV} and {config.KITE_API_SECRET_ENV} in your environment "
        "(from your Kite Connect developer app at developers.kite.trade) and restart the app."
    )
