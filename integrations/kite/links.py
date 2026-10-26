"""Deep links into Kite Web. Pure string-building, no I/O — opening the
link itself happens in the browser, not here."""


def chart_url(exchange: str, symbol: str, instrument_token) -> str | None:
    """Kite Web's TradingView chart deep link
    (https://kite.zerodha.com/chart/ext/tvc/{exchange}/{symbol}/{token}).
    Opens fine even without an active Kite Web session in that browser —
    it just redirects to login first in that case, same as any other
    kite.zerodha.com page. Returns None (no link) when the token is
    missing, e.g. for scan history rows saved before this field existed.

    KNOWN LIMITATION, confirmed live and not worth re-investigating without
    a new lead: this URL always opens at the viewer's own last-used/default
    chart timeframe, not the interval the scan was run at. Several likely
    query-string and path variants (?interval=5minute, ?interval=5,
    /5minute) were tried against a real logged-in Kite Web session and none
    of them changed it — the interval looks like a Kite Web UI preference
    (probably local to that browser/account), not something exposed on
    this URL. No workaround currently; the user just switches timeframe
    once after the chart opens."""
    if not instrument_token:
        return None
    return f"https://kite.zerodha.com/chart/ext/tvc/{exchange}/{symbol}/{instrument_token}"
