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
| 2 | Kite Connect per-user OAuth (login flow, encrypted token storage, daily expiry handling) | **Code done, 22/22 tests passing** (mocked Kite SDK). **Not yet verified against a real Zerodha account** — needs `KITE_API_KEY`/`KITE_API_SECRET` env vars from a real Kite Connect developer app (developers.kite.trade, ~₹2000/mo) plus a redirect URL registered pointing back at this app, to test the actual browser login-redirect round trip. |
| 3 | Timeframe-first Scanner (interval-generalized breakout/flag/RSI setups, ORB) | **Code done, 66/66 tests passing total.** Live-verified the UI flow (timeframe gate, mode/exchange/symbol inputs, graceful error handling) against a FAKE Kite session — the actual data-fetching path (`instruments.fetch_equity_universe`, `historical.fetch_historical_bars`) is unverified against real Kite data, same gap as Phase 2. |
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

## Known limitation, not a bug

Login sessions live only in `st.session_state`, not a browser cookie — a full page refresh (not a
Streamlit rerun, an actual F5) logs you out. Documented in `auth/session.py`. Fix later via
`streamlit-cookies-controller` if it becomes annoying; doesn't block anything else.

## To resume in a new chat

Say something like "continue the AITradingFreeTool project" — a session with memory access will find
the pointer to this file. Otherwise just point a session at this file and the plan file directly.
