"""Bar-by-bar entry status for a setup that needs to be watched live.
Currently covers opening-range breakout — the one setup type where "has it
triggered yet" genuinely changes bar to bar during the session, which is
exactly what the original repo's `entry.py check` / `watch` commands do.

Mirrors core.scanner_rules.orb_breakout()'s trigger definition exactly
(same opening_range() helper), but reports an incremental status instead
of scanning a whole completed session in one shot — this module answers
"where are we right now," the scanner answers "what already happened."
"""

from dataclasses import dataclass
from datetime import datetime

from core.indicators import opening_range, orb_range_bar_count
from core.types import Bar, ScanParams

# waiting_for_range: not enough bars yet to even know the range
# waiting:           range is set, no close-through yet
# triggered:         a bar closed at/above the range high
# expired:           no_entries_after has passed with no trigger
STATUSES = ("waiting_for_range", "waiting", "triggered", "expired")


@dataclass
class EntryStatus:
    status: str
    as_of: datetime | None
    range_high: float | None = None
    range_low: float | None = None
    trigger_close: float | None = None


def check_orb_entry(
    bars: list[Bar],
    watch_interval: str,
    params: ScanParams,
    no_entries_after: str | None = None,
) -> EntryStatus:
    """`no_entries_after` is an "HH:MM" cutoff (local session time); once
    the latest bar's time is at/after it with no trigger, the setup is
    reported expired rather than left "waiting" forever."""
    range_bar_count = orb_range_bar_count(watch_interval, params.orb_range_minutes)

    if not bars:
        return EntryStatus(status="waiting_for_range", as_of=None)

    rng = opening_range(bars, range_bar_count)
    if rng is None:
        return EntryStatus(status="waiting_for_range", as_of=bars[-1].timestamp)
    range_high, range_low = rng

    for bar in bars[range_bar_count:]:
        if bar.close >= range_high:
            return EntryStatus(
                status="triggered",
                as_of=bar.timestamp,
                range_high=range_high,
                range_low=range_low,
                trigger_close=bar.close,
            )

    as_of = bars[-1].timestamp
    if no_entries_after and as_of.strftime("%H:%M") >= no_entries_after:
        return EntryStatus(status="expired", as_of=as_of, range_high=range_high, range_low=range_low)

    return EntryStatus(status="waiting", as_of=as_of, range_high=range_high, range_low=range_low)
