"""Pure indicator math: SMA, Wilder RSI, and resampling bars to a coarser
interval (used to synthesize "weekly" from Kite's native "day" bars, since
Kite has no native weekly interval). No I/O, no streamlit, no Kite SDK.

Every function here is interval-agnostic by construction — callers decide
what interval the input `bars` came from; nothing here assumes "daily."
"""

from core.types import Bar


def sma(values: list[float], period: int) -> list[float | None]:
    """Simple moving average, aligned 1:1 with `values`. The first
    `period - 1` entries are None (not enough history yet)."""
    if period <= 0:
        raise ValueError("period must be positive")
    out: list[float | None] = [None] * len(values)
    running_sum = 0.0
    for i, v in enumerate(values):
        running_sum += v
        if i >= period:
            running_sum -= values[i - period]
        if i >= period - 1:
            out[i] = running_sum / period
    return out


def rsi_wilder(closes: list[float], period: int = 14) -> list[float | None]:
    """Wilder's RSI, aligned 1:1 with `closes`. The first `period` entries
    are None. Matches the original repo's "RSI 14 (Wilder)" definition:
    the first average gain/loss is a simple mean of the first `period`
    deltas, then Wilder-smoothed (prev * (period-1) + new) / period after
    that."""
    if period <= 0:
        raise ValueError("period must be positive")
    n = len(closes)
    out: list[float | None] = [None] * n
    if n <= period:
        return out

    deltas = [closes[i] - closes[i - 1] for i in range(1, n)]
    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    out[period] = _rsi_from_avgs(avg_gain, avg_loss)

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        out[i + 1] = _rsi_from_avgs(avg_gain, avg_loss)

    return out


def _rsi_from_avgs(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0 and avg_gain == 0:
        return 50.0
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def resample_bars(bars: list[Bar], bucket_key) -> list[Bar]:
    """Groups `bars` (assumed chronologically sorted) into coarser bars
    using `bucket_key(timestamp) -> hashable`, e.g. an ISO (year, week)
    tuple for weekly resampling. Within each bucket: open = first bar's
    open, high = max high, low = min low, close = last bar's close,
    volume = sum, timestamp = last bar's timestamp (the bucket is
    "complete" as of its last session)."""
    if not bars:
        return []

    buckets: dict = {}
    order: list = []
    for b in bars:
        key = bucket_key(b.timestamp)
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(b)

    out = []
    for key in order:
        group = buckets[key]
        out.append(
            Bar(
                timestamp=group[-1].timestamp,
                open=group[0].open,
                high=max(g.high for g in group),
                low=min(g.low for g in group),
                close=group[-1].close,
                volume=sum(g.volume for g in group),
            )
        )
    return out


def iso_week_key(timestamp):
    year, week, _ = timestamp.isocalendar()
    return (year, week)
