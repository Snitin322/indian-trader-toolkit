"""App-wide cache of NSE index/sector/F&O constituent lists. Not user-scoped
— the same data for every user, like fundamental_metrics/bulk_block_deals."""

from datetime import datetime, timedelta, timezone

from storage.db import get_connection


def save_constituents(universe_name: str, symbols: list[str]) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM index_constituents WHERE universe_name = ?", (universe_name,))
        conn.executemany(
            "INSERT INTO index_constituents (universe_name, symbol) VALUES (?, ?)",
            [(universe_name, s) for s in symbols],
        )
        conn.commit()
    finally:
        conn.close()


def get_cached_constituents(universe_name: str, max_age_hours: int = 24) -> list[str] | None:
    """Returns the cached list if it's fresh enough, else None (caller
    should re-fetch and call save_constituents)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT symbol, fetched_at FROM index_constituents WHERE universe_name = ? ORDER BY symbol",
            (universe_name,),
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        return None
    fetched_at = datetime.fromisoformat(rows[0]["fetched_at"]).replace(tzinfo=timezone.utc)
    if fetched_at < datetime.now(timezone.utc) - timedelta(hours=max_age_hours):
        return None
    return [r["symbol"] for r in rows]
