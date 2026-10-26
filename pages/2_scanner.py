import time
from datetime import date, datetime, timedelta

import streamlit as st

from auth import session
from core.scanner_rules import orb_breakout, run_daily_style_rules
from core.types import ScanParams
from integrations.kite import client as kite_client
from integrations.kite import historical, instruments
from integrations.kite.env import KiteConfigError
from integrations.kite.links import chart_url
from integrations.nse import index_universes
from storage.repositories import index_constituents_repo, scan_results_repo, user_config_repo

# Kite's documented rate limit is ~3 requests/sec; this keeps us safely
# under that during a multi-symbol scan (manual lists are short enough
# that this adds negligible time; it matters for the 50-500 symbol
# index/sector universes).
_PACING_SECONDS_BETWEEN_FETCHES = 0.34


_CHART_COLUMN_CONFIG = {"Chart": st.column_config.LinkColumn(display_text="Open chart")}

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

_INDIVIDUAL_STOCKS_OPTION = "Pick individual stocks"
universe_names = [_INDIVIDUAL_STOCKS_OPTION] + list(index_universes.INDEX_UNIVERSES.keys()) + [
    index_universes.FO_UNIVERSE_NAME
]
universe_choice = st.selectbox("Universe", universe_names)

symbols: list[str] = []

if universe_choice == _INDIVIDUAL_STOCKS_OPTION:
    symbols_text = st.text_input(
        "Symbols (comma-separated)", value="TCS,INFY,RELIANCE,HDFCBANK,ICICIBANK"
    )
    symbols = [s.strip().upper() for s in symbols_text.split(",") if s.strip()]
else:
    if exchange != "NSE":
        st.info("NSE index/sector universes aren't defined for BSE. Switch Exchange to NSE, or use individual stocks.")
    force_refresh = st.checkbox("Refresh from NSE now (ignore cache)", value=False)

    cached = None if force_refresh else index_constituents_repo.get_cached_constituents(universe_choice)
    if cached:
        symbols = cached
        st.caption(f"{len(symbols)} symbols (cached, refreshed within the last 24h).")
    else:
        with st.spinner(f"Fetching {universe_choice} constituents from NSE..."):
            try:
                if universe_choice == index_universes.FO_UNIVERSE_NAME:
                    symbols = index_universes.fetch_fo_stock_list()
                else:
                    symbols = index_universes.fetch_index_constituents(universe_choice)
                index_constituents_repo.save_constituents(universe_choice, symbols)
                st.caption(f"{len(symbols)} symbols (fetched just now from NSE).")
            except index_universes.NseFetchError as exc:
                st.error(f"Could not fetch {universe_choice} from NSE: {exc}")
            except Exception as exc:
                st.error(f"Unexpected error fetching {universe_choice}: {exc}")

    if len(symbols) > 100:
        st.warning(
            f"{len(symbols)} symbols will take roughly "
            f"{int(len(symbols) * _PACING_SECONDS_BETWEEN_FETCHES / 60) + 1} minute(s) to scan "
            "(Kite's API rate limit, not a bug)."
        )

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
            for h in hits:
                h.details["instrument_token"] = token
            all_hits.extend(hits)
        except Exception as exc:
            failed.append((symbol, str(exc)))
        progress.progress((i + 1) / len(valid_symbols) if valid_symbols else 1.0)
        if i < len(valid_symbols) - 1:
            time.sleep(_PACING_SECONDS_BETWEEN_FETCHES)

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
                    "Chart": chart_url(h.exchange, h.symbol, h.details.get("instrument_token")),
                    **{k: v for k, v in h.details.items() if k != "instrument_token"},
                }
                for h in all_hits
            ],
            column_config=_CHART_COLUMN_CONFIG,
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
            {
                "Symbol": r["symbol"], "Exchange": r["exchange"], "Interval": r["interval"],
                "Setup": r["setup_type"], "As of": r["scan_run_at"],
                "Chart": chart_url(r["exchange"], r["symbol"], r["setup_payload"].get("instrument_token")),
            }
            for r in recent
        ],
        column_config=_CHART_COLUMN_CONFIG,
        use_container_width=True,
    )
else:
    st.caption("No scans run yet.")

st.caption(
    "A scan is a list of charts that matched a rule, not a list of stocks to buy. "
    "Most people who day trade lose money; this tool does not change that."
)
