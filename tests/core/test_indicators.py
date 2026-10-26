from datetime import datetime, timedelta

from core.indicators import iso_week_key, resample_bars, rsi_wilder, sma
from core.types import Bar


def _bars(closes, start=datetime(2026, 1, 1)):
    return [
        Bar(timestamp=start + timedelta(days=i), open=c, high=c, low=c, close=c, volume=1000)
        for i, c in enumerate(closes)
    ]


def test_sma_basic():
    values = [1, 2, 3, 4, 5]
    result = sma(values, 3)
    assert result == [None, None, 2.0, 3.0, 4.0]


def test_sma_rejects_nonpositive_period():
    import pytest

    with pytest.raises(ValueError):
        sma([1, 2, 3], 0)


def test_rsi_all_gains_is_100():
    closes = [float(i) for i in range(1, 20)]  # strictly increasing
    result = rsi_wilder(closes, period=14)
    assert result[14] == 100.0


def test_rsi_all_losses_is_0():
    closes = [float(20 - i) for i in range(20)]  # strictly decreasing
    result = rsi_wilder(closes, period=14)
    assert result[14] == 0.0


def test_rsi_flat_prices_is_50():
    closes = [100.0] * 20
    result = rsi_wilder(closes, period=14)
    assert result[14] == 50.0


def test_rsi_first_period_entries_are_none():
    closes = [float(i) for i in range(1, 20)]
    result = rsi_wilder(closes, period=14)
    assert all(v is None for v in result[:14])
    assert result[14] is not None


def test_rsi_too_short_series_is_all_none():
    closes = [1.0, 2.0, 3.0]
    result = rsi_wilder(closes, period=14)
    assert all(v is None for v in result)
    assert len(result) == 3


def test_resample_bars_weekly_groups_correctly():
    # Real market data has no weekend bars, so use actual trading-day dates:
    # Mon 2026-01-05 .. Fri 2026-01-09 (week 1), then Mon 2026-01-12 .. Wed
    # 2026-01-14 (week 2) — skipping the Jan 10-11 weekend entirely, same as
    # Kite would (no bars on non-trading days).
    trading_dates = [
        datetime(2026, 1, 5), datetime(2026, 1, 6), datetime(2026, 1, 7),
        datetime(2026, 1, 8), datetime(2026, 1, 9),
        datetime(2026, 1, 12), datetime(2026, 1, 13), datetime(2026, 1, 14),
    ]
    closes = [10, 11, 9, 12, 13, 14, 8, 15]
    daily = [
        Bar(timestamp=d, open=c, high=c, low=c, close=c, volume=1000)
        for d, c in zip(trading_dates, closes)
    ]
    weekly = resample_bars(daily, iso_week_key)
    assert len(weekly) == 2
    week1 = weekly[0]
    assert week1.open == 10
    assert week1.close == 13
    assert week1.high == 13
    assert week1.low == 9
    assert week1.volume == 5000

    week2 = weekly[1]
    assert week2.open == 14
    assert week2.close == 15
    assert week2.volume == 3000


def test_resample_bars_empty_input():
    assert resample_bars([], iso_week_key) == []
