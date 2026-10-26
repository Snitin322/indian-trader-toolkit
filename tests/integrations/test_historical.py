from datetime import date

import pytest

from integrations.kite.historical import estimate_from_date, fetch_historical_bars


def test_estimate_from_date_day_interval_is_before_to_date():
    to_date = date(2026, 3, 1)
    from_date = estimate_from_date("day", needed_bars=20, to_date=to_date)
    assert from_date < to_date
    # 20 trading days padded generously should be comfortably under ~90 calendar days
    assert (to_date - from_date).days < 90


def test_estimate_from_date_scales_with_needed_bars():
    to_date = date(2026, 3, 1)
    short = estimate_from_date("day", needed_bars=20, to_date=to_date)
    long = estimate_from_date("day", needed_bars=200, to_date=to_date)
    assert long < short  # more bars needed -> further back


def test_estimate_from_date_intraday_interval():
    to_date = date(2026, 3, 1)
    from_date = estimate_from_date("5minute", needed_bars=30, to_date=to_date)
    assert from_date < to_date


def test_estimate_from_date_week_interval():
    to_date = date(2026, 3, 1)
    from_date = estimate_from_date("week", needed_bars=15, to_date=to_date)
    assert from_date < to_date


def test_estimate_from_date_unknown_interval_raises():
    with pytest.raises(ValueError):
        estimate_from_date("bogus", needed_bars=10, to_date=date(2026, 3, 1))


def test_fetch_historical_bars_parses_rows(monkeypatch):
    class FakeKite:
        def historical_data(self, instrument_token, from_date, to_date, interval):
            assert interval == "day"
            return [
                {"date": "2026-01-01T00:00:00+0530", "open": 100, "high": 105, "low": 99, "close": 102, "volume": 1000},
                {"date": "2026-01-02T00:00:00+0530", "open": 102, "high": 106, "low": 101, "close": 104, "volume": 1200},
            ]

    bars = fetch_historical_bars(FakeKite(), 123, date(2026, 1, 1), date(2026, 1, 2), "day")
    assert len(bars) == 2
    assert bars[0].close == 102.0
    assert bars[1].volume == 1200


def test_fetch_historical_bars_maps_week_to_day_interval():
    seen = {}

    class FakeKite:
        def historical_data(self, instrument_token, from_date, to_date, interval):
            seen["interval"] = interval
            return []

    fetch_historical_bars(FakeKite(), 123, date(2026, 1, 1), date(2026, 1, 2), "week")
    assert seen["interval"] == "day"


def test_fetch_historical_bars_retries_then_raises(monkeypatch):
    calls = {"count": 0}

    class FailingKite:
        def historical_data(self, *a, **k):
            calls["count"] += 1
            raise RuntimeError("rate limited")

    monkeypatch.setattr("time.sleep", lambda s: None)
    with pytest.raises(RuntimeError):
        fetch_historical_bars(FailingKite(), 123, date(2026, 1, 1), date(2026, 1, 2), "day")
    assert calls["count"] == 3
