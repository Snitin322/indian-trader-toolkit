from datetime import datetime, timedelta

import streamlit as st

from auth import session
from core.entry_timer import check_orb_entry
from core.exit_planner import InvalidExitPlanError, plan_exit
from core.types import ScanParams
from integrations.kite import client as kite_client
from integrations.kite import historical, instruments, quotes
from integrations.kite.env import KiteConfigError
from storage.repositories import plans_repo, scan_results_repo, user_config_repo

st.title("Watchlist / Entry / Exit")
user_id = session.require_login()

params = ScanParams()

st.subheader("1. Pick a candidate")
recent = scan_results_repo.get_latest_results(user_id, limit=50)
options = ["(enter a symbol manually)"] + [
    f"{r['symbol']} ({r['exchange']}) — {r['setup_type']} @ {r['scan_run_at']}" for r in recent
]
choice = st.selectbox("From a recent scan hit, or enter manually", options)

if choice == "(enter a symbol manually)":
    symbol = st.text_input("Symbol").strip().upper()
    exchange = st.selectbox("Exchange", ["NSE", "BSE"])
    setup_type = None
else:
    idx = options.index(choice) - 1
    chosen = recent[idx]
    symbol, exchange, setup_type = chosen["symbol"], chosen["exchange"], chosen["setup_type"]
    st.caption(f"Setup: {setup_type}")

if not symbol:
    st.info("Pick or enter a symbol to continue.")
    st.stop()

st.divider()
st.subheader("2. Check entry")

entry_price = None
range_high = range_low = None

col1, col2 = st.columns(2)
with col1:
    check_orb = st.button("Check Opening-Range entry status (intraday)")
with col2:
    use_ltp = st.button("Use current market price as entry")

if check_orb:
    try:
        kite = kite_client.get_authenticated_client(user_id)
        universe = instruments.fetch_equity_universe(kite, exchange)
        token_map = instruments.build_symbol_token_map(universe)
        token = token_map.get(symbol)
        if not token:
            st.error(f"{symbol} not found in the {exchange} equity universe.")
        else:
            today = datetime.now().date()
            bars = historical.fetch_historical_bars(
                kite, token, today, today + timedelta(days=1), params.orb_watch_interval
            )
            cfg = user_config_repo.get_config(user_id)
            status = check_orb_entry(
                bars, params.orb_watch_interval, params,
                no_entries_after=cfg.get("risk_trading_window_end"),
            )
            st.session_state["entry_status"] = status
    except kite_client.AuthRequiredError:
        st.error("Your Zerodha session has expired. Go to Connect Broker to log in again.")
    except KiteConfigError as exc:
        st.error(str(exc))

if use_ltp:
    try:
        kite = kite_client.get_authenticated_client(user_id)
        ltp_map = quotes.fetch_ltp(kite, [f"{exchange}:{symbol}"])
        price = ltp_map.get(f"{exchange}:{symbol}")
        if price is None:
            st.error(f"Could not get a quote for {symbol}.")
        else:
            st.session_state["entry_status"] = None
            st.session_state["manual_entry_price"] = price
    except kite_client.AuthRequiredError:
        st.error("Your Zerodha session has expired. Go to Connect Broker to log in again.")
    except KiteConfigError as exc:
        st.error(str(exc))

status = st.session_state.get("entry_status")
manual_price = st.session_state.get("manual_entry_price")

if status is not None:
    st.write(f"**Status: {status.status}** as of {status.as_of}")
    if status.range_high is not None:
        st.write(f"Opening range: {status.range_low} – {status.range_high}")
    if status.status == "triggered":
        entry_price = status.trigger_close
        range_high, range_low = status.range_high, status.range_low
        st.success(f"Triggered at {entry_price}")
    elif status.status in ("waiting", "waiting_for_range"):
        st.info("Not triggered yet — matching a rule is not a recommendation, and this is not triggered yet.")
    elif status.status == "expired":
        st.warning("This setup's entry window has expired.")
elif manual_price is not None:
    entry_price = manual_price
    st.write(f"Using current price as entry: {entry_price}")

if entry_price is None:
    st.info("Check an entry above to continue to exit planning.")
    st.stop()

st.divider()
st.subheader("3. Plan the exit (before you enter)")

stop_options = ["custom"] + (["or-mid", "or-low"] if range_high is not None else [])
stop_style = st.selectbox("Stop style", stop_options, format_func=lambda s: {
    "or-mid": "Opening range midpoint", "or-low": "Opening range low", "custom": "Custom price",
}[s])
custom_stop = None
if stop_style == "custom":
    custom_stop = st.number_input("Stop price", value=round(entry_price * 0.97, 2), step=0.05)
target_r = st.number_input("Target (multiple of risk, e.g. 1.0 = 1R)", value=1.0, min_value=0.1, step=0.1)

if st.button("Build Exit Plan", type="primary"):
    try:
        exit_plan = plan_exit(
            entry_price=entry_price, stop_style=stop_style, target_r_multiple=target_r,
            range_high=range_high, range_low=range_low, custom_stop=custom_stop,
        )
        st.session_state["exit_plan"] = exit_plan
    except InvalidExitPlanError as exc:
        st.error(str(exc))

exit_plan = st.session_state.get("exit_plan")
if exit_plan:
    c1, c2, c3 = st.columns(3)
    c1.metric("Stop loss", f"₹{exit_plan.stop_loss:.2f}")
    c2.metric("Profit target", f"₹{exit_plan.profit_target:.2f}")
    c3.metric("Risk/share", f"₹{exit_plan.risk_per_share:.2f}")

    if st.button("Save Plan"):
        plan_id = plans_repo.create_plan(
            user_id, symbol, exchange, params.orb_watch_interval,
            entry_trigger_payload={
                "entry_price": exit_plan.entry_price,
                "setup_type": setup_type,
                "range_high": range_high,
                "range_low": range_low,
            },
            stop_loss=exit_plan.stop_loss,
            profit_target=exit_plan.profit_target,
        )
        st.success(f"Plan #{plan_id} saved. Continue to Time Machine or Risk & Budget.")
        st.session_state.pop("exit_plan", None)
        st.session_state.pop("entry_status", None)
        st.session_state.pop("manual_entry_price", None)

st.divider()
st.subheader("Active plans")
active = plans_repo.get_active_plans(user_id)
if active:
    st.dataframe(
        [
            {"Symbol": p["symbol"], "Exchange": p["exchange"], "Stop": p["stop_loss"],
             "Target": p["profit_target"], "Created": p["created_at"]}
            for p in active
        ],
        use_container_width=True,
    )
else:
    st.caption("No active plans yet.")
