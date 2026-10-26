"""Shared dataclasses used across core/ (pure logic) and the pages/
integrations that feed it. No streamlit, no DB, no network imports here."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Kite Connect's native historical_data intervals, minutes per bar. "week" is
# NOT a Kite interval — it's synthesized by indicators.resample_bars() from
# "day" bars, and included here only so downstream code has one place to
# look up "how many sessions roughly fit in N bars of this interval."
INTERVAL_MINUTES: dict[str, int] = {
    "minute": 1,
    "3minute": 3,
    "5minute": 5,
    "10minute": 10,
    "15minute": 15,
    "30minute": 30,
    "60minute": 60,
    "day": 375,  # one full NSE session, 09:15-15:30
    "week": 375 * 5,
}


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class ScanParams:
    # breakout_20d / reclaim_ma20 lookback, in BARS not calendar days —
    # 20 bars on "day" ~= 20 sessions (upstream's original behavior);
    # 20 bars on "60minute" ~= ~3.3 sessions. Deliberate: see plan.
    lookback_bars: int = 20

    # bull_flag: runup window immediately before the consolidation window
    bull_flag_runup_bars: int = 10
    bull_flag_consolidation_bars: int = 5
    bull_flag_min_runup_pct: float = 10.0
    bull_flag_max_range_pct: float = 5.0

    # oversold / oversold_bounce
    rsi_period: int = 14
    rsi_oversold_threshold: float = 30.0

    # opening-range breakout: range definition and watch cadence are
    # decoupled on purpose (plan section "Generalizing scanner rules")
    orb_range_minutes: int = 15
    orb_watch_interval: str = "5minute"


@dataclass
class Setup:
    symbol: str
    exchange: str
    interval: str
    setup_type: str
    as_of: datetime
    details: dict[str, Any] = field(default_factory=dict)
