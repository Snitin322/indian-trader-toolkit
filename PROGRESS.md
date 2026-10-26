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
| 3 | Timeframe-first Scanner (interval-generalized breakout/flag/RSI setups, ORB) | **Done, verified live against real Kite data.** Fetched the real ~9,400-symbol NSE equity universe, pulled real daily bars for TCS/INFY/RELIANCE/HDFCBANK/ICICIBANK, ran the actual UI end-to-end ("Scanned 5 symbols at day; 5 setup hit(s)"). ORB (intraday) mode is coded but not yet live-tested — needs a run during market hours. |
| 4 | Entry timer + Exit planner | Not started |
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
- `storage/repositories/scan_results_repo.py` — per-user scan result persistence
- `.env` / `.env.example` — config.py now auto-loads `.env` via python-dotenv, so secrets work the same
  regardless of how the server is launched (was previously relying on inherited process env only)
- `tests/` — 66 tests total, all passing, Kite SDK mocked throughout — no real network/credentials
  needed to run the suite
- `core/fundamentals/`, `integrations/fundamentals/` — still empty package skeletons (phase 9+)

## Live verification notes (2026-10-26)

- Real Kite Connect app ("Screener," the user's own, confirmed) credentials are in the local
  `.env` (gitignored, never committed). The full OAuth round trip, instrument universe fetch, and
  scanner pipeline were run against real data and real results, not just mocks.
- **Action item for the user**: the actual redirect after a real Zerodha login landed on
  `http://localhost:3000/callback`, not `http://localhost:8501` as expected — the registered
  redirect URL on the Kite Connect app (developers.kite.trade) doesn't match this app's port.
  The token exchange was completed manually this time by lifting the `request_token` out of the
  dead-end redirect URL; `pages/1_connect_broker.py`'s automatic `st.query_params` handling will
  NOT work until the redirect URL is updated to `http://localhost:8501` in the Kite Connect app
  settings. Until fixed, completing a real login requires the same manual workaround.
- Real-world data quirk, not a bug: TATAMOTORS no longer exists as a plain NSE symbol — Tata Motors
  demerged into `TMPV` (passenger vehicles) and `TMCV` (commercial vehicles). The scanner correctly
  reports it as "not found" rather than silently guessing, per the honesty-over-silent-failure norm.

## Known limitation, not a bug

Login sessions live only in `st.session_state`, not a browser cookie — a full page refresh (not a
Streamlit rerun, an actual F5) logs you out. Documented in `auth/session.py`. Fix later via
`streamlit-cookies-controller` if it becomes annoying; doesn't block anything else.

## To resume in a new chat

Say something like "continue the AITradingFreeTool project" — a session with memory access will find
the pointer to this file. Otherwise just point a session at this file and the plan file directly.
