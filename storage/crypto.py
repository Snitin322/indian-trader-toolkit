"""Encrypt-at-rest helpers for sensitive columns (Kite access tokens)."""

import os

from cryptography.fernet import Fernet

import config


class EncryptionKeyMissingError(RuntimeError):
    pass


def _get_fernet() -> Fernet:
    key = os.environ.get(config.DB_ENCRYPTION_KEY_ENV)
    if not key:
        raise EncryptionKeyMissingError(
            f"Set the {config.DB_ENCRYPTION_KEY_ENV} environment variable to a "
            "Fernet key (python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\")."
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt(plaintext: str) -> bytes:
    return _get_fernet().encrypt(plaintext.encode("utf-8"))


def decrypt(ciphertext: bytes) -> str:
    return _get_fernet().decrypt(ciphertext).decode("utf-8")
