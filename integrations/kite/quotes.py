"""Batch quote/LTP wrapper — replaces the original repo's cheap Yahoo
'spark' screen as a necessary-condition first pass before fetching full
OHLC history for every candidate."""


def fetch_ltp(kite, instrument_keys: list[str]) -> dict[str, float]:
    """instrument_keys look like 'NSE:INFY'."""
    if not instrument_keys:
        return {}
    raw = kite.ltp(*instrument_keys)
    return {key: data["last_price"] for key, data in raw.items()}


def fetch_quotes(kite, instrument_keys: list[str]) -> dict[str, dict]:
    if not instrument_keys:
        return {}
    return kite.quote(*instrument_keys)
