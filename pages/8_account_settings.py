import streamlit as st

from auth import session
from storage.repositories import user_config_repo

st.title("Account Settings")
user_id = session.require_login()

cfg = user_config_repo.get_config(user_id)

st.subheader("Risk limits")
col1, col2 = st.columns(2)
with col1:
    max_loss = st.number_input(
        "Max loss per trade (₹)", value=float(cfg.get("risk_max_loss_per_trade_inr", 1000)), step=100.0
    )
    daily_cap = st.number_input(
        "Max daily loss (₹)", value=float(cfg.get("risk_daily_loss_cap_inr", 3000)), step=100.0
    )
    max_trades = st.number_input(
        "Max trades per day", value=int(cfg.get("risk_max_trades_per_day", 3)), step=1
    )
with col2:
    min_rr = st.number_input(
        "Min reward:risk ratio", value=float(cfg.get("risk_min_reward_risk_ratio", 1.5)), step=0.1
    )
    capital = st.number_input(
        "Total trading capital (₹)", value=float(cfg.get("budget_total_capital_inr", 100000)), step=1000.0
    )
    paper = st.checkbox(
        "Paper trading (strongly recommended — disable only when you're ready for real orders)",
        value=bool(cfg.get("paper_trading_enabled", True)),
    )

if st.button("Save settings"):
    user_config_repo.update_config(
        user_id,
        risk_max_loss_per_trade_inr=max_loss,
        risk_daily_loss_cap_inr=daily_cap,
        risk_max_trades_per_day=max_trades,
        risk_min_reward_risk_ratio=min_rr,
        budget_total_capital_inr=capital,
        paper_trading_enabled=int(paper),
    )
    st.success("Saved.")

if not paper:
    st.warning(
        "Paper trading is OFF. Real orders are still only possible through the "
        "Order Ticket page's explicit confirmation gate — this setting alone "
        "does not place any trade."
    )
