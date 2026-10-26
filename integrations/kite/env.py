"""Reads the Kite Connect app credentials from the environment. Never
hardcoded, never stored in the DB or config.json — only the per-user
*access token* that these credentials produce gets persisted (encrypted)."""

import os

import config


class KiteConfigError(RuntimeError):
    pass


def get_api_key() -> str:
    key = os.environ.get(config.KITE_API_KEY_ENV)
    if not key:
        raise KiteConfigError(
            f"Set the {config.KITE_API_KEY_ENV} environment variable to your "
            "Kite Connect app's API key (from developers.kite.trade)."
        )
    return key


def get_api_secret() -> str:
    secret = os.environ.get(config.KITE_API_SECRET_ENV)
    if not secret:
        raise KiteConfigError(
            f"Set the {config.KITE_API_SECRET_ENV} environment variable to your "
            "Kite Connect app's API secret."
        )
    return secret
