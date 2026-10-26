-- Shared, app-wide cache (not user-scoped — same for every user) of NSE
-- index/sector/F&O constituent lists, so repeated scans within the same
-- day don't re-hit NSE's archive every time.

CREATE TABLE IF NOT EXISTS index_constituents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    universe_name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_index_constituents_universe ON index_constituents(universe_name, fetched_at);
