from datetime import datetime, timedelta, timezone

from auth import app_auth
from storage.db import get_connection
from storage.repositories import kite_credentials_repo, user_config_repo


def test_migrations_create_expected_tables():
    conn = get_connection()
    try:
        tables = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        conn.close()
    expected = {
        "users", "sessions", "kite_credentials", "user_config",
        "watchlist_scan_results", "trade_plans", "orders", "alerts",
        "screener_rules", "screener_results", "fundamental_metrics",
        "bulk_block_deals", "insider_trades", "mf_schemes", "mf_portfolio_snapshots",
    }
    assert expected.issubset(tables)


def test_new_user_gets_default_config_with_paper_trading_on():
    user_id, _ = app_auth.register("defaults@example.com", "correcthorse")
    cfg = user_config_repo.get_config(user_id)
    assert cfg["paper_trading_enabled"] == 1


def test_kite_token_round_trips_encrypted_and_is_retrievable():
    user_id, _ = app_auth.register("kite@example.com", "correcthorse")
    now = datetime.now(timezone.utc)
    kite_credentials_repo.save_token(
        user_id,
        kite_api_key="abc123",
        access_token="super-secret-token",
        public_token="pub-token",
        kite_user_id="AB1234",
        token_obtained_at=now,
        token_expires_at=now + timedelta(hours=10),
    )
    assert kite_credentials_repo.is_connected(user_id)
    assert kite_credentials_repo.get_valid_access_token(user_id) == "super-secret-token"

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT encrypted_access_token FROM kite_credentials WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()
    assert b"super-secret-token" not in row["encrypted_access_token"]


def test_expired_kite_token_is_not_returned_as_valid():
    user_id, _ = app_auth.register("expired@example.com", "correcthorse")
    now = datetime.now(timezone.utc)
    kite_credentials_repo.save_token(
        user_id,
        kite_api_key="abc123",
        access_token="stale-token",
        public_token=None,
        kite_user_id="AB1234",
        token_obtained_at=now - timedelta(days=1),
        token_expires_at=now - timedelta(hours=1),
    )
    assert not kite_credentials_repo.is_connected(user_id)
    assert kite_credentials_repo.get_valid_access_token(user_id) is None


def test_tokens_are_isolated_per_user():
    user_a, _ = app_auth.register("isoa@example.com", "correcthorse")
    user_b, _ = app_auth.register("isob@example.com", "correcthorse")
    now = datetime.now(timezone.utc)
    kite_credentials_repo.save_token(
        user_a, "key", "token-a", None, "AB1", now, now + timedelta(hours=5)
    )
    assert kite_credentials_repo.get_valid_access_token(user_a) == "token-a"
    assert kite_credentials_repo.get_valid_access_token(user_b) is None
