from datetime import datetime, timedelta

from core.scanner_rules import (
    breakout_20d,
    bull_flag,
    oversold,
    oversold_bounce,
    orb_breakout,
    reclaim_ma20,
    run_daily_style_rules,
)
from core.types import Bar, ScanParams


def _daily_bars(closes, start=datetime(2026, 1, 1)):
    return [
        Bar(timestamp=start + timedelta(days=i), open=c, high=c, low=c, close=c, volume=1_000_000)
        for i, c in enumerate(closes)
    ]


def _intraday_bars(values, start=datetime(2026, 1, 5, 9, 15), minutes=5):
    """values: list of (open, high, low, close) tuples."""
    return [
        Bar(
            timestamp=start + timedelta(minutes=minutes * i),
            open=o, high=h, low=l, close=c,
            volume=10_000,
        )
        for i, (o, h, l, c) in enumerate(values)
    ]


# ---- breakout_20d ----

def test_breakout_20d_fires_on_new_closing_high():
    closes = [100.0] * 20 + [101.0]  # flat 20, then a new high
    bars = _daily_bars(closes)
    setup = breakout_20d("TCS", "NSE", "day", bars, ScanParams())
    assert setup is not None
    assert setup.setup_type == "breakout_20d"
    assert setup.details["close"] == 101.0


def test_breakout_20d_does_not_fire_without_new_high():
    closes = [100.0] * 21
    bars = _daily_bars(closes)
    assert breakout_20d("TCS", "NSE", "day", bars, ScanParams()) is None


def test_breakout_20d_insufficient_bars():
    bars = _daily_bars([100.0] * 10)
    assert breakout_20d("TCS", "NSE", "day", bars, ScanParams()) is None


# ---- reclaim_ma20 ----

def test_reclaim_ma20_fires_on_crossing_back_above():
    # 22 bars at 100, then a dip bar under what will be the SMA, then a
    # strong close back above it.
    closes = [100.0] * 20 + [90.0, 110.0]
    bars = _daily_bars(closes)
    setup = reclaim_ma20("TCS", "NSE", "day", bars, ScanParams())
    assert setup is not None
    assert setup.setup_type == "reclaim_ma20"


def test_reclaim_ma20_does_not_fire_when_staying_above():
    closes = [100.0] * 20 + [101.0, 102.0]
    bars = _daily_bars(closes)
    assert reclaim_ma20("TCS", "NSE", "day", bars, ScanParams()) is None


# ---- oversold / oversold_bounce ----

def test_oversold_fires_on_low_rsi():
    closes = [float(100 - i) for i in range(20)]  # steady decline
    bars = _daily_bars(closes)
    setup = oversold("TCS", "NSE", "day", bars, ScanParams())
    assert setup is not None
    assert setup.details["rsi"] < 30.0


def test_oversold_does_not_fire_on_uptrend():
    closes = [float(i) for i in range(1, 21)]
    bars = _daily_bars(closes)
    assert oversold("TCS", "NSE", "day", bars, ScanParams()) is None


def test_oversold_bounce_fires_after_decline_then_uptick():
    # Decline enough to be oversold, then one bar closing up.
    decline = [float(100 - i) for i in range(20)]  # 100.0 down to 81.0
    closes = decline + [decline[-1] + 5]  # 86.0 — a bounce off the low
    bars = _daily_bars(closes)
    setup = oversold_bounce("TCS", "NSE", "day", bars, ScanParams())
    assert setup is not None
    assert setup.setup_type == "oversold_bounce"


def test_oversold_bounce_does_not_fire_without_prior_oversold():
    closes = [float(i) for i in range(1, 22)]  # uptrend the whole way
    bars = _daily_bars(closes)
    assert oversold_bounce("TCS", "NSE", "day", bars, ScanParams()) is None


# ---- bull_flag ----

def test_bull_flag_fires_on_runup_then_tight_consolidation():
    runup = [100.0 + i * 1.5 for i in range(10)]  # ~13.5% run
    consolidation = [runup[-1] + d for d in (0.2, -0.1, 0.3, -0.2, 0.1)]  # tight range
    bars = _daily_bars(runup + consolidation)
    setup = bull_flag("TCS", "NSE", "day", bars, ScanParams())
    assert setup is not None
    assert setup.details["runup_pct"] >= 10.0
    assert setup.details["consolidation_range_pct"] <= 5.0


def test_bull_flag_does_not_fire_on_weak_runup():
    runup = [100.0 + i * 0.1 for i in range(10)]  # ~0.9% run, too weak
    consolidation = [runup[-1]] * 5
    bars = _daily_bars(runup + consolidation)
    assert bull_flag("TCS", "NSE", "day", bars, ScanParams()) is None


def test_bull_flag_does_not_fire_on_wide_consolidation():
    runup = [100.0 + i * 1.5 for i in range(10)]
    consolidation = [runup[-1] + d for d in (0, 10, -10, 8, -8)]  # wide swings
    bars = _daily_bars(runup + consolidation)
    assert bull_flag("TCS", "NSE", "day", bars, ScanParams()) is None


# ---- run_daily_style_rules ----

def test_run_daily_style_rules_collects_all_hits():
    closes = [100.0] * 20 + [101.0]
    bars = _daily_bars(closes)
    hits = run_daily_style_rules("TCS", "NSE", "day", bars, ScanParams())
    setup_types = {h.setup_type for h in hits}
    assert "breakout_20d" in setup_types


# ---- orb_breakout ----

def test_orb_breakout_triggers_on_first_close_above_range_high():
    # 3 range bars (15 min @ 5-minute bars), then a breakout bar.
    bars = _intraday_bars(
        [
            (100, 101, 99, 100.5),   # range bar 1
            (100.5, 102, 100, 101.5),  # range bar 2 -> range high so far 102
            (101.5, 100.8, 100.2, 100.8),  # range bar 3
            (100.8, 103, 100.5, 101.5),  # wicks above range high (102) but CLOSES under it -> no trigger
            (101.5, 104, 101.0, 103.5),  # closes above range high (102) -> trigger
        ]
    )
    setup = orb_breakout("TCS", "NSE", "5minute", bars, ScanParams(orb_range_minutes=15))
    assert setup is not None
    assert setup.setup_type == "orb"
    assert setup.details["trigger_close"] == 103.5
    assert setup.details["range_high"] == 102


def test_orb_breakout_returns_none_when_no_breakout_yet():
    bars = _intraday_bars(
        [
            (100, 101, 99, 100.5),
            (100.5, 102, 100, 101.5),
            (101.5, 100.8, 100.2, 100.8),
            (100.8, 101.9, 100.5, 101.0),  # stays under range high (102)
        ]
    )
    assert orb_breakout("TCS", "NSE", "5minute", bars, ScanParams(orb_range_minutes=15)) is None


def test_orb_breakout_insufficient_bars_returns_none():
    bars = _intraday_bars([(100, 101, 99, 100.5), (100.5, 102, 100, 101.5)])
    assert orb_breakout("TCS", "NSE", "5minute", bars, ScanParams(orb_range_minutes=15)) is None


def test_orb_breakout_unknown_interval_raises():
    import pytest

    bars = _intraday_bars([(100, 101, 99, 100.5)] * 5)
    with pytest.raises(ValueError):
        orb_breakout("TCS", "NSE", "bogus", bars, ScanParams())
