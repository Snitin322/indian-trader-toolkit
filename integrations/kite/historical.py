"""Wrapper around kite.historical_data(): converts Kite's raw rows into
core.types.Bar, retries with backoff on transient errors (Kite's documented
rate limit is ~3 req/sec — this replaces the original repo's Yahoo
429/5xx host-fallback retry logic), and estimates a safe `from_date` for a
desired number of bars at a given interval."""

import time
from datetime import date, datetime, timedelta

from core.types import INTERVAL_MINUTES, Bar

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2.0

# Rough trading-day padding factor to cover weekends/holidays when we only
# know "I want N bars," not the exact NSE calendar (core/calendars.py, not
# built yet — this is a deliberately generous overestimate, trimmed by the
# caller after fetching whatever Kite actually returns).
CALENDAR_PADDING_FACTOR = 1.8
MINUTES_PER_SESSION = INTERVAL_MINUTES["day"]  # 375


def _parse_bar(row: dict) -> Bar:
    ts = row["date"]
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)
    return Bar(
        timestamp=ts,
        open=float(row["open"]),
        high=float(row["high"]),
        low=float(row["low"]),
        close=float(row["close"]),
        volume=int(row.get("volume", 0) or 0),
    )


def estimate_from_date(interval: str, needed_bars: int, to_date: date) -> date:
    """A deliberately generous from_date so a fetch is likely to return at
    least `needed_bars` real trading bars, even accounting for weekends
    and holidays we aren't precisely modeling yet."""
    if interval == "day":
        calendar_days = needed_bars * 7 / 5  # trading week -> calendar week
    elif interval == "week":
        calendar_days = needed_bars * 7
    else:
        bar_minutes = INTERVAL_MINUTES.get(interval)
        if not bar_minutes:
            raise ValueError(f"Unknown interval: {interval}")
        bars_per_session = max(1, MINUTES_PER_SESSION // bar_minutes)
        sessions_needed = -(-needed_bars // bars_per_session)  # ceil
        calendar_days = sessions_needed * 7 / 5
    calendar_days *= CALENDAR_PADDING_FACTOR
    return to_date - timedelta(days=int(calendar_days) + 5)


def fetch_historical_bars(
    kite, instrument_token: int, from_date, to_date, interval: str
) -> list[Bar]:
    kite_interval = "day" if interval == "week" else interval
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            raw = kite.historical_data(instrument_token, from_date, to_date, kite_interval)
            return [_parse_bar(row) for row in raw]
        except Exception as exc:  # kiteconnect raises several *Exception subclasses
            last_exc = exc
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))
    raise last_exc
