"""Per-user trade plans: the output of entry_timer + exit_planner, the
input to the Time Machine (phase 5) and Risk & Budget (phase 6)."""

import json

from storage.db import get_connection


def create_plan(
    user_id: int,
    symbol: str,
    exchange: str,
    interval: str,
    entry_trigger_payload: dict,
    stop_loss: float,
    profit_target: float,
    scan_result_id: int | None = None,
) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO trade_plans
                (user_id, scan_result_id, symbol, exchange, interval,
                 entry_trigger_payload, stop_loss, profit_target, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """,
            (
                user_id, scan_result_id, symbol, exchange, interval,
                json.dumps(entry_trigger_payload), stop_loss, profit_target,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def _row_to_dict(row) -> dict:
    d = dict(row)
    if d.get("entry_trigger_payload"):
        d["entry_trigger_payload"] = json.loads(d["entry_trigger_payload"])
    if d.get("time_machine_payload"):
        d["time_machine_payload"] = json.loads(d["time_machine_payload"])
    return d


def get_plan(user_id: int, plan_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM trade_plans WHERE id = ? AND user_id = ?", (plan_id, user_id)
        ).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def get_active_plans(user_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM trade_plans WHERE user_id = ? AND status = 'active' ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def update_status(user_id: int, plan_id: int, status: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE trade_plans SET status = ?, updated_at = datetime('now') WHERE id = ? AND user_id = ?",
            (status, plan_id, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def update_time_machine_payload(user_id: int, plan_id: int, payload: dict) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE trade_plans SET time_machine_payload = ?, updated_at = datetime('now') WHERE id = ? AND user_id = ?",
            (json.dumps(payload), plan_id, user_id),
        )
        conn.commit()
    finally:
        conn.close()
