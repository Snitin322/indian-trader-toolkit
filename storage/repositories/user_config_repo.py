"""Per-user config: selected scan interval, risk limits, budget, paper-trading
flag. Every function takes user_id — this is the multi-user isolation
boundary enforced in code (see plan: "every repository function filters by
user_id")."""

from storage.db import get_connection

_COLUMNS = (
    "selected_interval",
    "risk_max_loss_per_trade_inr",
    "risk_daily_loss_cap_inr",
    "risk_max_trades_per_day",
    "risk_max_orders_per_day",
    "risk_min_reward_risk_ratio",
    "risk_trading_window_start",
    "risk_trading_window_end",
    "risk_flat_by",
    "budget_total_capital_inr",
    "budget_cash_buffer_pct",
    "budget_max_position_pct",
    "paper_trading_enabled",
    "allow_options",
    "allow_margin",
    "allow_short",
)


def get_config(user_id: int) -> dict:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM user_config WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def update_config(user_id: int, **fields) -> None:
    unknown = set(fields) - set(_COLUMNS)
    if unknown:
        raise ValueError(f"Unknown user_config field(s): {unknown}")
    if not fields:
        return
    set_clause = ", ".join(f"{col} = ?" for col in fields)
    conn = get_connection()
    try:
        conn.execute(
            f"UPDATE user_config SET {set_clause}, updated_at = datetime('now') WHERE user_id = ?",
            (*fields.values(), user_id),
        )
        conn.commit()
    finally:
        conn.close()


def set_selected_interval(user_id: int, interval: str) -> None:
    update_config(user_id, selected_interval=interval)


def has_selected_interval(user_id: int) -> bool:
    return bool(get_config(user_id).get("selected_interval"))
