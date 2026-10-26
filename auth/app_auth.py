"""App-level email+password auth. Distinct from each user's separate Kite
broker login (see integrations/kite/oauth.py) — this just answers "which
app user is this browser session," not "which Zerodha account."""

import re

import bcrypt

from storage.repositories import users_repo

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class InvalidEmailError(ValueError):
    pass


class WeakPasswordError(ValueError):
    pass


class InvalidCredentialsError(ValueError):
    pass


def _validate_email(email: str) -> None:
    if not _EMAIL_RE.match(email or ""):
        raise InvalidEmailError(email)


def _validate_password(password: str) -> None:
    if not password or len(password) < 8:
        raise WeakPasswordError("Password must be at least 8 characters.")


def register(email: str, password: str) -> tuple[int, str]:
    """Creates the user and an active session. Returns (user_id, session_token)."""
    _validate_email(email)
    _validate_password(password)
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user_id = users_repo.create_user(email, password_hash)
    session_token = users_repo.create_session(user_id)
    return user_id, session_token


def login(email: str, password: str) -> tuple[int, str]:
    """Verifies credentials and creates a new session. Returns (user_id, session_token)."""
    user = users_repo.get_user_by_email(email)
    if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        raise InvalidCredentialsError("Incorrect email or password.")
    session_token = users_repo.create_session(user["id"])
    return user["id"], session_token


def logout(session_token: str) -> None:
    users_repo.delete_session(session_token)
