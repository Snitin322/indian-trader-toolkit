from datetime import datetime, timedelta, timezone

from storage.db import get_connection
from storage.repositories import index_constituents_repo


def test_save_and_get_cached_constituents():
    index_constituents_repo.save_constituents("Nifty Bank", ["HDFCBANK", "ICICIBANK", "SBIN"])
    result = index_constituents_repo.get_cached_constituents("Nifty Bank")
    assert result == ["HDFCBANK", "ICICIBANK", "SBIN"]


def test_get_cached_constituents_returns_none_when_missing():
    assert index_constituents_repo.get_cached_constituents("Nifty Nonexistent") is None


def test_save_constituents_replaces_old_list():
    index_constituents_repo.save_constituents("Nifty IT", ["TCS", "INFY"])
    index_constituents_repo.save_constituents("Nifty IT", ["TCS", "WIPRO"])
    result = index_constituents_repo.get_cached_constituents("Nifty IT")
    assert sorted(result) == ["TCS", "WIPRO"]


def test_get_cached_constituents_returns_none_when_stale():
    index_constituents_repo.save_constituents("Nifty Auto", ["TATAMOTORS"])
    conn = get_connection()
    try:
        stale_time = (datetime.now(timezone.utc) - timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE index_constituents SET fetched_at = ? WHERE universe_name = ?",
            (stale_time, "Nifty Auto"),
        )
        conn.commit()
    finally:
        conn.close()
    assert index_constituents_repo.get_cached_constituents("Nifty Auto", max_age_hours=24) is None
