-- Per-user tables (every row scoped by user_id)

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS sessions (
    session_token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kite_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
    kite_api_key TEXT,
    encrypted_access_token BLOB,
    encrypted_public_token BLOB,
    kite_user_id TEXT,
    token_obtained_at TEXT,
    token_expires_at TEXT,
    last_login_attempt_at TEXT
);

CREATE TABLE IF NOT EXISTS user_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
    selected_interval TEXT,
    risk_max_loss_per_trade_inr REAL NOT NULL DEFAULT 1000,
    risk_daily_loss_cap_inr REAL NOT NULL DEFAULT 3000,
    risk_max_trades_per_day INTEGER NOT NULL DEFAULT 3,
    risk_max_orders_per_day INTEGER NOT NULL DEFAULT 6,
    risk_min_reward_risk_ratio REAL NOT NULL DEFAULT 1.5,
    risk_trading_window_start TEXT NOT NULL DEFAULT '09:20',
    risk_trading_window_end TEXT NOT NULL DEFAULT '15:00',
    risk_flat_by TEXT NOT NULL DEFAULT '15:15',
    budget_total_capital_inr REAL NOT NULL DEFAULT 100000,
    budget_cash_buffer_pct REAL NOT NULL DEFAULT 0.10,
    budget_max_position_pct REAL NOT NULL DEFAULT 0.25,
    paper_trading_enabled INTEGER NOT NULL DEFAULT 1,
    allow_options INTEGER NOT NULL DEFAULT 0,
    allow_margin INTEGER NOT NULL DEFAULT 0,
    allow_short INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS watchlist_scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    interval TEXT NOT NULL,
    setup_type TEXT NOT NULL,
    scan_run_at TEXT NOT NULL DEFAULT (datetime('now')),
    setup_payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scan_results_user ON watchlist_scan_results(user_id, scan_run_at);

CREATE TABLE IF NOT EXISTS trade_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    scan_result_id INTEGER REFERENCES watchlist_scan_results(id),
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    interval TEXT NOT NULL,
    entry_trigger_payload TEXT,
    stop_loss REAL,
    profit_target REAL,
    time_machine_payload TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_trade_plans_user ON trade_plans(user_id, status);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    plan_id INTEGER REFERENCES trade_plans(id),
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    order_type TEXT NOT NULL DEFAULT 'MARKET',
    price REAL,
    is_paper INTEGER NOT NULL DEFAULT 1,
    risk_check_result TEXT,
    confirmation_phrase_matched INTEGER NOT NULL DEFAULT 0,
    kite_order_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id, status);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    threshold REAL NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    triggered_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id, is_active);

CREATE TABLE IF NOT EXISTS screener_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    rule_name TEXT NOT NULL,
    rules_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_screener_rules_user ON screener_rules(user_id);

CREATE TABLE IF NOT EXISTS screener_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    rule_name TEXT NOT NULL,
    run_at TEXT NOT NULL DEFAULT (datetime('now')),
    shortlist TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_screener_results_user ON screener_results(user_id, run_at);

-- Shared, app-wide market-data caches (NOT user-scoped — same data for everyone)

CREATE TABLE IF NOT EXISTS fundamental_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    period_end TEXT NOT NULL,
    revenue REAL,
    net_income REAL,
    diluted_eps REAL,
    operating_margin REAL,
    revenue_growth_yoy REAL,
    source TEXT NOT NULL,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(symbol, exchange, period_end)
);

CREATE TABLE IF NOT EXISTS bulk_block_deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    deal_type TEXT NOT NULL,
    client_name TEXT NOT NULL,
    buy_sell TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    source TEXT NOT NULL,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_bulk_deals_symbol ON bulk_block_deals(symbol, trade_date);

CREATE TABLE IF NOT EXISTS insider_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    disclosing_person TEXT NOT NULL,
    category TEXT NOT NULL,
    buy_sell TEXT NOT NULL,
    quantity INTEGER,
    value REAL,
    disclosure_date TEXT NOT NULL,
    source TEXT NOT NULL,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_insider_trades_symbol ON insider_trades(symbol, disclosure_date);

CREATE TABLE IF NOT EXISTS mf_schemes (
    scheme_code TEXT PRIMARY KEY,
    scheme_name TEXT NOT NULL,
    amc_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mf_portfolio_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheme_code TEXT NOT NULL REFERENCES mf_schemes(scheme_code),
    month TEXT NOT NULL,
    holdings TEXT NOT NULL,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(scheme_code, month)
);
