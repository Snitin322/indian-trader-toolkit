from datetime import datetime, timezone

import pytest

from integrations.kite import client as kite_client
from integrations.kite import oauth
from integrations.kite.env import KiteConfigError
from storage.repositories import kite_credentials_repo
from auth import app_auth


@pytest.fixture(autouse=True)
def kite_env(monkeypatch):
    monkeypatch.setenv("KITE_API_KEY", "test-api-key")
    monkeypatch.setenv("KITE_API_SECRET", "test-api-secret")


def test_get_login_url_requires_api_key(monkeypatch):
    monkeypatch.delenv("KITE_API_KEY", raising=False)
    with pytest.raises(KiteConfigError):
        oauth.get_login_url()


def test_get_login_url_builds_a_kite_url():
    url = oauth.get_login_url()
    assert "kite.trade" in url or "kite.zerodha.com" in url
    assert "test-api-key" in url


@pytest.mark.parametrize(
    "obtained_at_str,expected_expiry_str",
    [
        # Logged in early morning IST -> expires 7:30am IST the NEXT day.
        ("2026-01-10T03:00:00+00:00", "2026-01-11T02:00:00+00:00"),  # 08:30 IST -> next day 07:30 IST
        # Logged in late at night IST -> still next-day 7:30am IST, not two days out.
        ("2026-01-10T18:00:00+00:00", "2026-01-11T02:00:00+00:00"),  # 23:30 IST -> next day 07:30 IST
    ],
)
def test_next_token_expiry_is_always_next_day_730am_ist(obtained_at_str, expected_expiry_str):
    obtained_at = datetime.fromisoformat(obtained_at_str)
    expiry = oauth.next_token_expiry(obtained_at)
    assert expiry == datetime.fromisoformat(expected_expiry_str)


def test_complete_login_persists_encrypted_token_scoped_to_caller_user(monkeypatch):
    """The security property from the plan: complete_login() must write to
    whatever user_id it's given, resolved by the CALLER from the app's own
    session, never from anything in the request_token/redirect itself."""

    user_id, _ = app_auth.register("broker@example.com", "correcthorse")

    class FakeKiteConnect:
        def __init__(self, api_key):
            self.api_key = api_key

        def generate_session(self, request_token, api_secret):
            assert request_token == "fake-request-token"
            assert api_secret == "test-api-secret"
            return {
                "access_token": "fake-access-token",
                "public_token": "fake-public-token",
                "user_id": "AB1234",
                "user_name": "Test User",
            }

    monkeypatch.setattr(oauth, "KiteConnect", FakeKiteConnect)

    session_data = oauth.complete_login(user_id, "fake-request-token")

    assert session_data["user_name"] == "Test User"
    assert kite_credentials_repo.is_connected(user_id)
    assert kite_credentials_repo.get_valid_access_token(user_id) == "fake-access-token"


def test_get_authenticated_client_raises_when_not_connected():
    user_id, _ = app_auth.register("noauth@example.com", "correcthorse")
    with pytest.raises(kite_client.AuthRequiredError):
        kite_client.get_authenticated_client(user_id)


def test_get_authenticated_client_raises_when_expired():
    from datetime import timedelta

    user_id, _ = app_auth.register("expired2@example.com", "correcthorse")
    now = datetime.now(timezone.utc)
    kite_credentials_repo.save_token(
        user_id, "key", "stale-token", None, "AB1", now - timedelta(days=2), now - timedelta(hours=1)
    )
    with pytest.raises(kite_client.AuthRequiredError):
        kite_client.get_authenticated_client(user_id)


def test_get_authenticated_client_returns_client_for_valid_token(monkeypatch):
    from datetime import timedelta

    user_id, _ = app_auth.register("valid@example.com", "correcthorse")
    now = datetime.now(timezone.utc)
    kite_credentials_repo.save_token(
        user_id, "key", "good-token", None, "AB1", now, now + timedelta(hours=5)
    )

    calls = {}

    class FakeKiteConnect:
        def __init__(self, api_key):
            calls["api_key"] = api_key

        def set_access_token(self, token):
            calls["access_token"] = token

    monkeypatch.setattr(kite_client, "KiteConnect", FakeKiteConnect)

    kite = kite_client.get_authenticated_client(user_id)
    assert calls["access_token"] == "good-token"
    assert isinstance(kite, FakeKiteConnect)
