"""The scanner's setup rules, generalized over interval (see plan:
"Generalizing scanner rules to any interval"). Every rule takes a list of
Bar at whatever interval the caller fetched (day/60minute/15minute/.../the
synthetic "week"), plus a ScanParams, and returns a Setup or None. No I/O.

Lookback windows are expressed in BAR COUNTS, not calendar time — "20" on
daily bars behaves exactly like the original repo's 20-day rules; the same
"20" on 60-minute bars is a faster, intraday-scale version of the same
rule. That's intentional, not a bug: see the plan for the rationale.
"""

from core.indicators import opening_range, orb_range_bar_count, rsi_wilder, sma
from core.types import Bar, ScanParams, Setup


def breakout_20d(symbol: str, exchange: str, interval: str, bars: list[Bar], params: ScanParams) -> Setup | None:
    """Last bar's close is above every close in the `lookback_bars` bars
    before it (a closing-high breakout, not an intraday-high one — same
    distinction the original repo makes)."""
    n = params.lookback_bars
    if len(bars) < n + 1:
        return None
    prior_closes = [b.close for b in bars[-(n + 1) : -1]]
    last = bars[-1]
    if last.close > max(prior_closes):
        return Setup(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            setup_type="breakout_20d",
            as_of=last.timestamp,
            details={"close": last.close, "prior_high": max(prior_closes), "lookback_bars": n},
        )
    return None


def reclaim_ma20(symbol: str, exchange: str, interval: str, bars: list[Bar], params: ScanParams) -> Setup | None:
    """The bar before was under its trailing SMA, the last bar is above its
    trailing SMA — a reclaim of the moving average."""
    n = params.lookback_bars
    if len(bars) < n + 2:
        return None
    closes = [b.close for b in bars]
    sma_series = sma(closes, n)
    prev_close, last_close = closes[-2], closes[-1]
    prev_sma, last_sma = sma_series[-2], sma_series[-1]
    if prev_sma is None or last_sma is None:
        return None
    if prev_close < prev_sma and last_close > last_sma:
        return Setup(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            setup_type="reclaim_ma20",
            as_of=bars[-1].timestamp,
            details={"close": last_close, "sma": last_sma, "lookback_bars": n},
        )
    return None


def oversold(symbol: str, exchange: str, interval: str, bars: list[Bar], params: ScanParams) -> Setup | None:
    """RSI(period) of the last bar is under the oversold threshold."""
    closes = [b.close for b in bars]
    rsi_series = rsi_wilder(closes, params.rsi_period)
    last_rsi = rsi_series[-1] if rsi_series else None
    if last_rsi is None:
        return None
    if last_rsi < params.rsi_oversold_threshold:
        return Setup(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            setup_type="oversold",
            as_of=bars[-1].timestamp,
            details={"rsi": last_rsi, "threshold": params.rsi_oversold_threshold},
        )
    return None


def oversold_bounce(symbol: str, exchange: str, interval: str, bars: list[Bar], params: ScanParams) -> Setup | None:
    """RSI was under the threshold as of the PREVIOUS bar, and the last bar
    closed up from the previous one — an initial bounce out of oversold."""
    if len(bars) < 2:
        return None
    closes = [b.close for b in bars]
    rsi_series = rsi_wilder(closes, params.rsi_period)
    prev_rsi = rsi_series[-2] if len(rsi_series) >= 2 else None
    if prev_rsi is None:
        return None
    closed_up = bars[-1].close > bars[-2].close
    if prev_rsi < params.rsi_oversold_threshold and closed_up:
        return Setup(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            setup_type="oversold_bounce",
            as_of=bars[-1].timestamp,
            details={"prior_rsi": prev_rsi, "threshold": params.rsi_oversold_threshold},
        )
    return None


def bull_flag(symbol: str, exchange: str, interval: str, bars: list[Bar], params: ScanParams) -> Setup | None:
    """A runup of at least `bull_flag_min_runup_pct` over the
    `bull_flag_runup_bars` bars immediately before the last
    `bull_flag_consolidation_bars` bars, which then stay inside a
    `bull_flag_max_range_pct` range (the "flag")."""
    runup_n, consol_n = params.bull_flag_runup_bars, params.bull_flag_consolidation_bars
    total_n = runup_n + consol_n
    if len(bars) < total_n:
        return None

    consolidation = bars[-consol_n:]
    runup_window = bars[-total_n:-consol_n]

    runup_start, runup_end = runup_window[0].close, runup_window[-1].close
    if runup_start <= 0:
        return None
    runup_pct = (runup_end - runup_start) / runup_start * 100.0

    consol_closes = [b.close for b in consolidation]
    consol_low = min(consol_closes)
    if consol_low <= 0:
        return None
    consol_range_pct = (max(consol_closes) - consol_low) / consol_low * 100.0

    if runup_pct >= params.bull_flag_min_runup_pct and consol_range_pct <= params.bull_flag_max_range_pct:
        return Setup(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            setup_type="bull_flag",
            as_of=bars[-1].timestamp,
            details={"runup_pct": runup_pct, "consolidation_range_pct": consol_range_pct},
        )
    return None


DAILY_STYLE_RULES = (breakout_20d, bull_flag, reclaim_ma20, oversold, oversold_bounce)


def run_daily_style_rules(
    symbol: str, exchange: str, interval: str, bars: list[Bar], params: ScanParams
) -> list[Setup]:
    hits = []
    for rule in DAILY_STYLE_RULES:
        setup = rule(symbol, exchange, interval, bars, params)
        if setup is not None:
            hits.append(setup)
    return hits


def orb_breakout(
    symbol: str, exchange: str, watch_interval: str, session_bars: list[Bar], params: ScanParams
) -> Setup | None:
    """Opening-range breakout over a single session's bars (chronological,
    watch_interval granularity, e.g. 5-minute bars for today only).

    The opening range is the first `orb_range_minutes` of the session.
    A hit is the first bar AFTER the range whose CLOSE is at or above the
    range high (the original repo's exact definition: a close-through, not
    an intraday wick-through)."""
    range_bar_count = orb_range_bar_count(watch_interval, params.orb_range_minutes)
    if len(session_bars) <= range_bar_count:
        return None

    rng = opening_range(session_bars, range_bar_count)
    if rng is None:
        return None
    range_high, range_low = rng

    for bar in session_bars[range_bar_count:]:
        if bar.close >= range_high:
            return Setup(
                symbol=symbol,
                exchange=exchange,
                interval=watch_interval,
                setup_type="orb",
                as_of=bar.timestamp,
                details={
                    "trigger_close": bar.close,
                    "range_high": range_high,
                    "range_low": range_low,
                    "range_bar_count": range_bar_count,
                    "pct_over": (bar.close - range_high) / range_high * 100.0 if range_high else None,
                },
            )
    return None
