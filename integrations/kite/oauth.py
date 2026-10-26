"""Per-user Kite Connect OAuth: login-url generation and the
request_token -> access_token exchange. The only module that calls
kite.generate_session() — every other module gets an already-authenticated
client from integrations.kite.client.get_authenticated_client().

Security note: the caller MUST resolve `user_id` from the app's own
session (auth.session), never from anything in the Kite redirect itself —
the shared redirect URL means the incoming request_token carries no
trustworthy identity of its own. complete_login() just writes to whatever
user_id it's given, so binding that correctly is the caller's job
(see pages/1_connect_broker.py)."""

from datetime import datetime, time, timedelta, timezone

from kiteconnect import KiteConnect

import config
from integrations.kite.env import KiteConfigError, get_api_key, get_api_secret
from storage.repositories import kite_credentials_repo

IST = timezone(timedelta(hours=5, minutes=30))

__all__ = ["KiteConfigError", "get_login_url", "complete_login", "next_token_expiry"]


def get_login_url() -> str:
    kite = KiteConnect(api_key=get_api_key())
    return kite.login_url()


def next_token_expiry(obtained_at: datetime) -> datetime:
    """Kite access tokens invalidate at a fixed IST time (~7:30am) the
    calendar day AFTER they were obtained — a fixed daily cutoff, not a
    rolling TTL from the moment of login."""
    ist_obtained = obtained_at.astimezone(IST)
    expiry_date = ist_obtained.date() + timedelta(days=1)
    expiry_ist = datetime.combine(
        expiry_date,
        time(config.IST_TOKEN_EXPIRY_HOUR, config.IST_TOKEN_EXPIRY_MINUTE),
        tzinfo=IST,
    )
    return expiry_ist.astimezone(timezone.utc)


def complete_login(user_id: int, request_token: str) -> dict:
    """Exchanges request_token for an access_token and persists it
    encrypted, scoped to user_id. Returns the raw Kite session dict
    (contains the plaintext access_token — callers must not log it)."""
    kite = KiteConnect(api_key=get_api_key())
    session_data = kite.generate_session(request_token, api_secret=get_api_secret())

    now = datetime.now(timezone.utc)
    kite_credentials_repo.save_token(
        user_id=user_id,
        kite_api_key=get_api_key(),
        access_token=session_data["access_token"],
        public_token=session_data.get("public_token"),
        kite_user_id=str(session_data.get("user_id", "")),
        token_obtained_at=now,
        token_expires_at=next_token_expiry(now),
    )
    return session_data
