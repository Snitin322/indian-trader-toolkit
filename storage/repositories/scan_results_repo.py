"""Per-user technical scan results. Every function takes user_id."""

import json

from core.types import Setup
from storage.db import get_connection


def save_results(user_id: int, setups: list[Setup]) -> None:
    if not setups:
        return
    conn = get_connection()
    try:
        conn.executemany(
            """
            INSERT INTO watchlist_scan_results
                (user_id, symbol, exchange, interval, setup_type, scan_run_at, setup_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    user_id,
                    s.symbol,
                    s.exchange,
                    s.interval,
                    s.setup_type,
                    s.as_of.isoformat(),
                    json.dumps(s.details),
                )
                for s in setups
            ],
        )
        conn.commit()
    finally:
        conn.close()


def get_latest_results(user_id: int, limit: int = 200) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM watchlist_scan_results
            WHERE user_id = ?
            ORDER BY scan_run_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        results = []
        for row in rows:
            d = dict(row)
            d["setup_payload"] = json.loads(d["setup_payload"])
            results.append(d)
        return results
    finally:
        conn.close()
