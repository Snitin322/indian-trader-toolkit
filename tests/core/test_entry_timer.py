from datetime import datetime, timedelta

from core.entry_timer import check_orb_entry
from core.types import Bar, ScanParams


def _bars(values, start=datetime(2026, 1, 5, 9, 15), minutes=5):
    return [
        Bar(timestamp=start + timedelta(minutes=minutes * i), open=o, high=h, low=l, close=c, volume=1000)
        for i, (o, h, l, c) in enumerate(values)
    ]


def test_waiting_for_range_with_no_bars():
    status = check_orb_entry([], "5minute", ScanParams(orb_range_minutes=15))
    assert status.status == "waiting_for_range"
    assert status.as_of is None


def test_waiting_for_range_with_partial_range():
    bars = _bars([(100, 101, 99, 100.5), (100.5, 102, 100, 101.5)])  # only 2 of 3 range bars
    status = check_orb_entry(bars, "5minute", ScanParams(orb_range_minutes=15))
    assert status.status == "waiting_for_range"


def test_waiting_once_range_is_set_but_no_trigger():
    bars = _bars(
        [
            (100, 101, 99, 100.5), (100.5, 102, 100, 101.5), (101.5, 100.8, 100.2, 100.8),
            (100.8, 101.9, 100.5, 101.0),  # under the range high (102)
        ]
    )
    status = check_orb_entry(bars, "5minute", ScanParams(orb_range_minutes=15))
    assert status.status == "waiting"
    assert status.range_high == 102
    assert status.range_low == 99


def test_triggered_on_first_close_through():
    bars = _bars(
        [
            (100, 101, 99, 100.5), (100.5, 102, 100, 101.5), (101.5, 100.8, 100.2, 100.8),
            (100.8, 103, 100.5, 101.5),  # wicks over but closes under
            (101.5, 104, 101.0, 103.5),  # closes through -> triggered
        ]
    )
    status = check_orb_entry(bars, "5minute", ScanParams(orb_range_minutes=15))
    assert status.status == "triggered"
    assert status.trigger_close == 103.5
    assert status.range_high == 102


def test_expired_after_cutoff_with_no_trigger():
    bars = _bars(
        [
            (100, 101, 99, 100.5), (100.5, 102, 100, 101.5), (101.5, 100.8, 100.2, 100.8),
            (100.8, 101.9, 100.5, 101.0),
        ],
        start=datetime(2026, 1, 5, 15, 25),  # late in the NSE session
    )
    status = check_orb_entry(
        bars, "5minute", ScanParams(orb_range_minutes=15), no_entries_after="15:30"
    )
    assert status.status == "expired"


def test_not_expired_before_cutoff():
    bars = _bars(
        [
            (100, 101, 99, 100.5), (100.5, 102, 100, 101.5), (101.5, 100.8, 100.2, 100.8),
            (100.8, 101.9, 100.5, 101.0),
        ],
        start=datetime(2026, 1, 5, 9, 15),
    )
    status = check_orb_entry(
        bars, "5minute", ScanParams(orb_range_minutes=15), no_entries_after="15:30"
    )
    assert status.status == "waiting"
