"""Non-secret app configuration. Secrets (API keys, encryption key) come from
environment variables only — never hardcoded here, never committed."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Loads BASE_DIR/.env if present (gitignored — see .env.example for the
# template). Read directly from the file rather than relying on the
# process's inherited environment, so this works the same way no matter
# how the server was launched.
load_dotenv(BASE_DIR / ".env")

DB_PATH = os.environ.get("TRADERAPP_DB_PATH", str(DATA_DIR / "app.db"))

SESSION_TTL_HOURS = int(os.environ.get("TRADERAPP_SESSION_TTL_HOURS", "12"))

KITE_API_KEY_ENV = "KITE_API_KEY"
KITE_API_SECRET_ENV = "KITE_API_SECRET"

# Fernet key for encrypting Kite access tokens at rest. Must be set in the
# environment for any real (non-test) use; generate with:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
DB_ENCRYPTION_KEY_ENV = "TRADERAPP_DB_ENCRYPTION_KEY"

NSE_SESSION_START = "09:15"
NSE_SESSION_END = "15:30"
IST_TOKEN_EXPIRY_HOUR = 7  # Kite access tokens invalidate ~7:30am IST daily
IST_TOKEN_EXPIRY_MINUTE = 30
