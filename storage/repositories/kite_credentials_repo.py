"""Per-user Kite Connect credentials. Access tokens are Fernet-encrypted at
rest (storage/crypto.py) and never returned/logged in plaintext except to
integrations.kite.client, which is the one place that needs them."""

from datetime import datetime, timezone

from storage import crypto
from storage.db import get_connection


def save_token(
    user_id: int,
    kite_api_key: str,
    access_token: str,
    public_token: str | None,
    kite_user_id: str,
    token_obtained_at: datetime,
    token_expires_at: datetime,
) -> None:
    encrypted_access = crypto.encrypt(access_token)
    encrypted_public = crypto.encrypt(public_token) if public_token else None
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO kite_credentials
                (user_id, kite_api_key, encrypted_access_token, encrypted_public_token,
                 kite_user_id, token_obtained_at, token_expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                kite_api_key=excluded.kite_api_key,
                encrypted_access_token=excluded.encrypted_access_token,
                encrypted_public_token=excluded.encrypted_public_token,
                kite_user_id=excluded.kite_user_id,
                token_obtained_at=excluded.token_obtained_at,
                token_expires_at=excluded.token_expires_at
            """,
            (
                user_id,
                kite_api_key,
                encrypted_access,
                encrypted_public,
                kite_user_id,
                token_obtained_at.isoformat(),
                token_expires_at.isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_valid_access_token(user_id: int) -> str | None:
    """Returns the decrypted access token only if it hasn't expired yet, else None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT encrypted_access_token, token_expires_at FROM kite_credentials WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row or not row["encrypted_access_token"]:
        return None
    expires_at = datetime.fromisoformat(row["token_expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    return crypto.decrypt(row["encrypted_access_token"])


def is_connected(user_id: int) -> bool:
    return get_valid_access_token(user_id) is not None


def record_login_attempt(user_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO kite_credentials (user_id, last_login_attempt_at)
            VALUES (?, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET last_login_attempt_at = datetime('now')
            """,
            (user_id,),
        )
        conn.commit()
    finally:
        conn.close()
