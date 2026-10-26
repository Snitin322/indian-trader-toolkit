import os
import sys
import tempfile
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
    """Every test gets its own throwaway SQLite file and encryption key —
    never touches the real app.db."""
    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, "test.db")
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setenv(config.DB_ENCRYPTION_KEY_ENV, Fernet.generate_key().decode())

    from storage.db import init_db

    init_db(db_path)
    yield db_path
