# Build Progress

Full design/rationale: `C:\Users\ashis\.claude\plans\luminous-tinkering-cat.md` (also readable from
within this repo's history of decisions — see git log once commits start).

Read this file first in any new session before touching code. It's the source of truth for
"what's actually been built" — trust it (and `git log`) over anything a conversation summary claims.

## Status

| Phase | What | Status |
|---|---|---|
| 0/1 | Foundation — SQLite schema, bcrypt auth, DB-backed sessions, Streamlit page router + gating | **Done** — 14 pytest tests passing, verified live in browser |
| 2 | Kite Connect per-user OAuth (login flow, encrypted token storage, daily expiry handling) | **Blocked** — needs a real Kite Connect developer app (API key/secret + redirect URL) from the user. Can build against mocks without it, but not test the real redirect flow. |
| 3 | Timeframe-first Scanner (interval-generalized breakout/flag/RSI setups, ORB) | Not started |
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
- `pages/0_login.py` through `pages/12_mf_copycat.py` — pages 2–7, 9, 12 are stubs ("lands in Phase N");
  0, 1, 8, 10, 11 have real (if minimal) functionality
- `auth/` — `app_auth.py` (register/login/logout), `session.py` (st.session_state <-> DB session glue)
- `storage/` — `db.py`, `crypto.py` (Fernet), `migrations/001_init.sql` (full schema),
  `repositories/users_repo.py`, `user_config_repo.py`, `kite_credentials_repo.py`
- `tests/` — `auth/test_app_auth.py`, `storage/test_db_and_repos.py` (14 tests, all passing)
- `core/`, `core/fundamentals/`, `integrations/kite/`, `integrations/fundamentals/` — empty package
  skeletons only, no logic yet (that's phases 2+)

## Known limitation, not a bug

Login sessions live only in `st.session_state`, not a browser cookie — a full page refresh (not a
Streamlit rerun, an actual F5) logs you out. Documented in `auth/session.py`. Fix later via
`streamlit-cookies-controller` if it becomes annoying; doesn't block anything else.

## To resume in a new chat

Say something like "continue the AITradingFreeTool project" — a session with memory access will find
the pointer to this file. Otherwise just point a session at this file and the plan file directly.
