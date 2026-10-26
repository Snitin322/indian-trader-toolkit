"""SQLite connection + migration runner. One connection per call (SQLite is
file-based; short-lived connections avoid Streamlit-rerun threading issues)."""

import sqlite3
from pathlib import Path

import config

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def run_migrations(db_path: str | None = None) -> None:
    conn = get_connection(db_path)
    try:
        for migration_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            conn.executescript(migration_file.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str | None = None) -> None:
    """Ensure the DB file and schema exist. Safe to call on every app startup."""
    run_migrations(db_path)
