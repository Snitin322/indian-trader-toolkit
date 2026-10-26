from datetime import date, datetime, timedelta

import streamlit as st

from auth import session
from core.scanner_rules import orb_breakout, run_daily_style_rules
from core.types import ScanParams
from integrations.kite import client as kite_client
from integrations.kite import historical, instruments
from integrations.kite.env import KiteConfigError
from storage.repositories import scan_results_repo, user_config_repo

st.title("Scanner")
user_id = session.require_login()

NATIVE_INTERVALS = [
    "minute", "3minute", "5minute", "10minute", "15minute", "30minute", "60minute", "day",
]
ALL_INTERVALS = NATIVE_INTERVALS + ["week"]  # "week" is synthesized from "day", see core/indicators.py

cfg = user_config_repo.get_config(user_id)
current_interval = cfg.get("selected_interval")

st.subheader("1. Pick your timeframe")
st.caption(
    "This is locked in before anything else runs — the same scanner, entry, exit, and "
    "time-machine logic works for day trading (pick an intraday interval) or swing "
    "trading (pick day/week), just with a different timeframe."
)
chosen_interval = st.selectbox(
    "Scan interval",
    ALL_INTERVALS,
    index=ALL_INTERVALS.index(current_interval) if current_interval in ALL_INTERVALS else ALL_INTERVALS.index("day"),
)
if st.button("Save timeframe"):
    user_config_repo.set_selected_interval(user_id, chosen_interval)
    st.success(f"Timeframe set to {chosen_interval}.")
    st.rerun()

if not current_interval:
    st.info("Save a timeframe above to unlock scanning.")
    st.stop()

st.divider()
st.subheader("2. Run a scan")

mode = st.radio("Mode", ["Daily-style setups", "Opening Range Breakout (intraday)"])
exchange = st.selectbox("Exchange", ["NSE", "BSE"])
symbols_text = st.text_input(
    "Symbols (comma-separated)", value="TCS,INFY,RELIANCE,HDFCBANK,ICICIBANK"
)
symbols = [s.strip().upper() for s in symbols_text.split(",") if s.strip()]

run_clicked = st.button("Run Scan", type="primary")

if run_clicked:
    try:
        kite = kite_client.get_authenticated_client(user_id)
    except kite_client.AuthRequiredError:
        st.error("Your Zerodha session has expired. Go to Connect Broker to log in again.")
        st.stop()
    except KiteConfigError as exc:
        st.error(str(exc))
        st.stop()

    with st.spinner(f"Fetching {exchange} instrument list..."):
        try:
            universe = instruments.fetch_equity_universe(kite, exchange)
        except Exception as exc:
            st.error(f"Could not fetch the instrument list: {exc}")
            st.stop()
    token_map = instruments.build_symbol_token_map(universe)

    missing = [s for s in symbols if s not in token_map]
    if missing:
        st.warning(f"Not found in {exchange} equity universe, skipped: {', '.join(missing)}")
    valid_symbols = [s for s in symbols if s in token_map]

    params = ScanParams()
    all_hits = []
    progress = st.progress(0.0)
    failed = []

    for i, symbol in enumerate(valid_symbols):
        token = token_map[symbol]
        try:
            if mode == "Daily-style setups":
                needed = max(
                    params.lookback_bars + 2,
                    params.bull_flag_runup_bars + params.bull_flag_consolidation_bars,
                    params.rsi_period + 2,
                )
                to_date = date.today()
                from_date = historical.estimate_from_date(chosen_interval, needed, to_date)
                bars = historical.fetch_historical_bars(kite, token, from_date, to_date, chosen_interval)
                if chosen_interval == "week":
                    from core.indicators import iso_week_key, resample_bars
                    bars = resample_bars(bars, iso_week_key)
                hits = run_daily_style_rules(symbol, exchange, chosen_interval, bars, params)
            else:
                today = datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)
                bars = historical.fetch_historical_bars(
                    kite, token, today.date(), today.date() + timedelta(days=1), params.orb_watch_interval
                )
                setup = orb_breakout(symbol, exchange, params.orb_watch_interval, bars, params)
                hits = [setup] if setup else []
            all_hits.extend(hits)
        except Exception as exc:
            failed.append((symbol, str(exc)))
        progress.progress((i + 1) / len(valid_symbols) if valid_symbols else 1.0)

    if failed:
        st.warning(f"Failed to fetch/scan {len(failed)} of {len(valid_symbols)}: " +
                   ", ".join(f"{s} ({e})" for s, e in failed))

    st.write(
        f"Scanned {len(valid_symbols)} symbols at `{chosen_interval}`; "
        f"{len(all_hits)} setup hit(s)."
    )

    if all_hits:
        scan_results_repo.save_results(user_id, all_hits)
        st.dataframe(
            [
                {
                    "Symbol": h.symbol,
                    "Setup": h.setup_type,
                    "As of": h.as_of,
                    **h.details,
                }
                for h in all_hits
            ],
            use_container_width=True,
        )
    else:
        st.info("No setups matched. Matching a rule is not a recommendation — see the fine print.")

st.divider()
st.subheader("Recent scan history")
recent = scan_results_repo.get_latest_results(user_id, limit=50)
if recent:
    st.dataframe(
        [
            {"Symbol": r["symbol"], "Exchange": r["exchange"], "Interval": r["interval"],
             "Setup": r["setup_type"], "As of": r["scan_run_at"]}
            for r in recent
        ],
        use_container_width=True,
    )
else:
    st.caption("No scans run yet.")

st.caption(
    "A scan is a list of charts that matched a rule, not a list of stocks to buy. "
    "Most people who day trade lose money; this tool does not change that."
)
