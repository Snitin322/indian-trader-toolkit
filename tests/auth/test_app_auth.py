import pytest

from auth import app_auth
from storage.repositories import users_repo


def test_register_creates_user_and_session():
    user_id, token = app_auth.register("new.user@example.com", "correcthorse")
    assert user_id > 0
    assert users_repo.resolve_session(token) == user_id


def test_register_rejects_invalid_email():
    with pytest.raises(app_auth.InvalidEmailError):
        app_auth.register("not-an-email", "correcthorse")


def test_register_rejects_short_password():
    with pytest.raises(app_auth.WeakPasswordError):
        app_auth.register("user@example.com", "short")


def test_register_rejects_duplicate_email():
    app_auth.register("dupe@example.com", "correcthorse")
    with pytest.raises(users_repo.EmailAlreadyRegisteredError):
        app_auth.register("dupe@example.com", "correcthorse")


def test_login_succeeds_with_correct_password():
    app_auth.register("login@example.com", "correcthorse")
    user_id, token = app_auth.login("login@example.com", "correcthorse")
    assert users_repo.resolve_session(token) == user_id


def test_login_fails_with_wrong_password():
    app_auth.register("login2@example.com", "correcthorse")
    with pytest.raises(app_auth.InvalidCredentialsError):
        app_auth.login("login2@example.com", "wrongpassword")


def test_login_fails_for_unknown_email():
    with pytest.raises(app_auth.InvalidCredentialsError):
        app_auth.login("ghost@example.com", "correcthorse")


def test_logout_invalidates_session():
    _, token = app_auth.register("logout@example.com", "correcthorse")
    app_auth.logout(token)
    assert users_repo.resolve_session(token) is None


def test_session_isolated_per_user():
    user_a, token_a = app_auth.register("a@example.com", "correcthorse")
    user_b, token_b = app_auth.register("b@example.com", "correcthorse")
    assert users_repo.resolve_session(token_a) == user_a
    assert users_repo.resolve_session(token_b) == user_b
    assert token_a != token_b
