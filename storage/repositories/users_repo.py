"""User account + session persistence. The only repo module that is not
scoped by an existing user_id (it's what creates/resolves one)."""

import secrets
from datetime import datetime, timedelta, timezone

import config
from storage.db import get_connection


class EmailAlreadyRegisteredError(ValueError):
    pass


def create_user(email: str, password_hash: str) -> int:
    conn = get_connection()
    try:
        try:
            cur = conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email.strip().lower(), password_hash),
            )
        except Exception as exc:
            if "UNIQUE" in str(exc):
                raise EmailAlreadyRegisteredError(email) from exc
            raise
        user_id = cur.lastrowid
        conn.execute(
            "INSERT INTO user_config (user_id) VALUES (?)",
            (user_id,),
        )
        conn.commit()
        return user_id
    finally:
        conn.close()


def get_user_by_email(email: str):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ? AND is_active = 1",
            (email.strip().lower(),),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id: int):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = (
        datetime.now(timezone.utc) + timedelta(hours=config.SESSION_TTL_HOURS)
    ).isoformat()
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO sessions (session_token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires_at),
        )
        conn.commit()
        return token
    finally:
        conn.close()


def resolve_session(session_token: str):
    """Returns the user_id for a valid, unexpired session token, else None."""
    if not session_token:
        return None
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT user_id, expires_at FROM sessions WHERE session_token = ?",
            (session_token,),
        ).fetchone()
        if not row:
            return None
        if datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
            conn.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
            conn.commit()
            return None
        return row["user_id"]
    finally:
        conn.close()


def delete_session(session_token: str) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
        conn.commit()
    finally:
        conn.close()
