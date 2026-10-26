# Build Progress

Repo: https://github.com/Snitin322/indian-trader-toolkit

Full design/rationale: `C:\Users\ashis\.claude\plans\luminous-tinkering-cat.md` (also readable from
within this repo's history of decisions — see `git log`).

Read this file first in any new session before touching code. It's the source of truth for
"what's actually been built" — trust it (and `git log`) over anything a conversation summary claims.

## Status

| Phase | What | Status |
|---|---|---|
| 0/1 | Foundation — SQLite schema, bcrypt auth, DB-backed sessions, Streamlit page router + gating | **Done** — 14 pytest tests passing, verified live in browser |
| 2 | Kite Connect per-user OAuth (login flow, encrypted token storage, daily expiry handling) | **Done, verified live against the user's real Zerodha account** (2026-10-26). Real `login_url()` generation, real browser login, real `generate_session()` token exchange all confirmed working. See "Live verification" note below. |
| 3 | Timeframe-first Scanner (interval-generalized breakout/flag/RSI setups, ORB) | **Done, verified live against real Kite data.** Fetched the real ~9,400-symbol NSE equity universe, pulled real daily bars for TCS/INFY/RELIANCE/HDFCBANK/ICICIBANK, ran the actual UI end-to-end ("Scanned 5 symbols at day; 5 setup hit(s)"). ORB (intraday) mode confirmed live by the user themselves (real ORB hits across several Bank Nifty stocks throughout the trading day). **Extended**: scan an entire NSE index/sector universe (23 universes) instead of typing symbols by hand — live-verified (real NSE fetch, real scan, real hits). **Extended again**: every result row (both a fresh scan and scan history) has a clickable "Open chart" link straight to that stock's real Kite Web TradingView chart (`kite.zerodha.com/chart/ext/tvc/{exchange}/{symbol}/{instrument_token}`) — live-verified real URLs for TCS/INFY/RELIANCE/ICICIBANK. |
| 4 | Entry timer + Exit planner | **Done, verified live.** `check_orb_entry` mirrors the scanner's ORB trigger logic incrementally (waiting_for_range/waiting/triggered/expired); `plan_exit` computes stop/target before entry (or-mid/or-low/custom). Live-verified: real TCS LTP fetch (₹2534.6) through Watchlist/Entry/Exit, built a real exit plan (stop ₹2458.56, target ₹2610.64), saved it, confirmed the row in the DB. |
| 5 | Time Machine (Monte Carlo + historical backtest) | Not started |
| 6 | Risk manager + Budget/position sizer | Not started |
| 7 | Broker order ticket + the hard confirmation gate | Not started |
| 8 | Alerts | Not started |
| 9 | Fundamental Screener | Not started |
| 10 | Bulk/Block Deal & Promoter Activity tracker | Not started |
| 11 | MF Copycat (AMFI monthly portfolio diff) | Not started |
| 12 | Earnings Surprise (trend-deviation approximation) | Not started |

## What exists on disk right now

- `app.py` — entrypoint, login gate, page router (gated by logged_in / kite_connected / has_interval)
- `pages/0_login.py`, `1_connect_broker.py`, `8_account_settings.py` — real functionality
- `pages/2_scanner.py` through `12_mf_copycat.py` (minus 8) — still stubs ("lands in Phase N")
- `auth/` — `app_auth.py` (register/login/logout), `session.py` (st.session_state <-> DB session glue)
- `storage/` — `db.py`, `crypto.py` (Fernet), `migrations/001_init.sql` (full schema),
  `repositories/users_repo.py`, `user_config_repo.py`, `kite_credentials_repo.py`
- `integrations/kite/` — `env.py` (reads KITE_API_KEY/SECRET from env), `oauth.py` (login-url +
  request_token->access_token exchange, daily-expiry computation), `client.py` (the one place every
  other module gets an authenticated KiteConnect instance; raises AuthRequiredError if missing/expired),
  `instruments.py` (NSE/BSE equity universe filtering), `historical.py` (historical_data wrapper +
  retry/backoff + from_date estimation), `quotes.py` (batch LTP/quote wrapper)
- `core/` — `types.py` (Bar/ScanParams/Setup dataclasses, INTERVAL_MINUTES), `indicators.py` (SMA,
  Wilder RSI, bar resampling for synthetic "weekly"), `scanner_rules.py` (all 5 daily-style setups +
  ORB, generalized over interval per the plan)
- `pages/2_scanner.py` — real: timeframe picker gate, daily-style/ORB mode, symbol input, results table,
  scan history
- `pages/3_watchlist_entry_exit.py` — real: pick a candidate (from a scan hit or manual symbol), check
  ORB entry status or use current LTP, build and save an exit plan
- `core/entry_timer.py` — incremental ORB entry status (waiting_for_range/waiting/triggered/expired),
  shares `core/indicators.py::opening_range()` + `orb_range_bar_count()` with the scanner so they can't
  disagree about what "the opening range" means
- `core/exit_planner.py` — stop/target computation (or-mid/or-low/custom stop styles)
- `storage/repositories/scan_results_repo.py`, `plans_repo.py` — per-user scan result and trade plan
  persistence
- `.env` / `.env.example` — config.py now auto-loads `.env` via python-dotenv, so secrets work the same
  regardless of how the server is launched (was previously relying on inherited process env only)
- `tests/` — 66 tests total, all passing, Kite SDK mocked throughout — no real network/credentials
  needed to run the suite
- `integrations/nse/index_universes.py` — fetches NSE's real index/sector constituent CSVs (Nifty 50,
  Nifty Bank, Private/PSU Bank, 15+ sector indices, Nifty 500/Smallcap 250/Midcap 150, etc.) and the
  F&O-eligible stock list; `storage/repositories/index_constituents_repo.py` caches them (24h) so
  repeated scans don't re-hit NSE every time. Flagged fragile/best-effort like the other NSE-scraped
  integrations — URLs/format confirmed working live but NSE gives no stability guarantee.
- `integrations/kite/links.py` — builds Kite Web chart deep links (`chart_url()`); scan results (both
  a fresh run and scan history) render a clickable "Open chart" column via it. **Known limitation,
  confirmed live**: the chart always opens at the viewer's own default/last-used timeframe, not the
  interval the scan was run at — tried several likely query-string/path variants against a real
  logged-in Kite Web session (user tested), none worked. Looks like a Kite Web UI preference, not
  something exposed on this URL. No workaround currently.
- `core/fundamentals/`, `integrations/fundamentals/` — still empty package skeletons (phase 9+)

## Live verification notes (2026-10-26)

- Real Kite Connect app ("Screener," the user's own, confirmed) credentials are in the local
  `.env` (gitignored, never committed). The full OAuth round trip, instrument universe fetch, and
  scanner pipeline were run against real data and real results, not just mocks.
- **Fixed, found live**: the redirect URL was initially `localhost:3000`, not `:8501` — user
  corrected it in the Kite Connect app settings. That then exposed a SECOND, more fundamental bug:
  the Kite login redirect is a full top-level browser navigation (not a Streamlit rerun), which
  wiped `st.session_state`-based login every time, stranding the `request_token` on a login page
  that never looks for it. Fixed by adding `streamlit-cookies-controller`-backed persistent
  sessions (`auth/session.py`) plus `app.py` now force-routing to Connect Broker whenever a
  `request_token` is pending in the URL, regardless of current connection status. Also had to add
  a short `time.sleep(0.3)` after every cookie write/remove before `st.rerun()` — without it,
  Streamlit's forced rerun cuts off the cookie component's browser-side write before it flushes
  (confirmed by inspecting `document.cookie` directly: the cookie was silently never being set
  until this was added). **Re-verified end-to-end after the fix**: reconnect → real Zerodha login →
  automatic redirect-triggered token exchange with NO manual intervention, confirmed via a fresh
  `token_obtained_at` timestamp in the DB.
- Real-world data quirk, not a bug: TATAMOTORS no longer exists as a plain NSE symbol — Tata Motors
  demerged into `TMPV` (passenger vehicles) and `TMCV` (commercial vehicles). The scanner correctly
  reports it as "not found" rather than silently guessing, per the honesty-over-silent-failure norm.

## Resolved limitation (fixed twice — see below)

~~Login sessions live only in `st.session_state`~~ — sessions now persist across full page reloads
via a browser cookie, with the DB `sessions` table remaining the actual source of truth (the cookie
only carries an opaque token).

**Round 1** used `streamlit-cookies-controller` (a bidirectional custom component). Worked in
automated/scripted browser testing, but the user reported it live: "every time I restart the app, I
have to log in and reconnect to the broker again." Root cause: the component's write only confirms
after an iframe postMessage round-trip completes on the *next* rerun — fine when a script-driven
click leaves time for that round trip, but a real interactive click immediately followed by
`st.rerun()` can fire before it settles, silently dropping the cookie write.

**Round 2**: reading uses `st.context.cookies` — a native, synchronous Streamlit API, no
component, no round-trip. Writing uses a one-way injected `<script>document.cookie=...</script>` via
`components.v1.html` — fire-and-forget, no return value to race against. Removed the now-unneeded
`time.sleep()` workarounds in `pages/0_login.py` and `app.py`'s logout along with the
`streamlit-cookies-controller` dependency. Live-verified: logged in, did a full server stop/start
(not just a page reload), and the fresh page load showed "Logged in" + "Broker: connected" with zero
manual steps.

**Follow-up UX fix**: user then reported Zerodha asking for credentials "every time" on both the
shared Browser pane and their own Chrome. Checked the DB directly — the stored connection was valid
the whole time. Actual cause: `pages/1_connect_broker.py` always showed a "Reconnect with Zerodha"
button even while already connected, so clicking it (reasonably, to check) sent them to Zerodha's own
login page, which asks for full credentials whenever that specific browser has no cached Zerodha web
session — normal Zerodha-side behavior, not a bug in this app, but confusing UX. Fixed by showing the
actual expiry time ("good until 07:30 AM IST on 27 Oct"), explicit "you do NOT need to do anything
else" messaging, and tucking the reconnect button into a collapsed expander. Live-verified the new
copy renders correctly.

## To resume in a new chat

Say something like "continue the AITradingFreeTool project" — a session with memory access will find
the pointer to this file. Otherwise just point a session at this file and the plan file directly.
