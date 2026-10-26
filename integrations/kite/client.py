"""The one place every page/module gets an authenticated Kite client for a
given user. Nothing outside integrations/kite/ should import
kiteconnect.KiteConnect directly."""

from kiteconnect import KiteConnect

from integrations.kite.env import get_api_key
from storage.repositories import kite_credentials_repo


class AuthRequiredError(RuntimeError):
    """Raised when a user has no valid (unexpired) Kite session. Kite has
    no refresh-token flow, so callers must route the user back to the
    Connect Broker page for a fresh login — never retry silently."""

    def __init__(self, user_id: int):
        super().__init__(f"No valid Kite session for user {user_id}; re-login required.")
        self.user_id = user_id


def get_authenticated_client(user_id: int) -> KiteConnect:
    access_token = kite_credentials_repo.get_valid_access_token(user_id)
    if access_token is None:
        raise AuthRequiredError(user_id)
    kite = KiteConnect(api_key=get_api_key())
    kite.set_access_token(access_token)
    return kite
