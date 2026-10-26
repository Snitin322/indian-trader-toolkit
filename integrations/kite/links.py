"""Deep links into Kite Web. Pure string-building, no I/O — opening the
link itself happens in the browser, not here."""


def chart_url(exchange: str, symbol: str, instrument_token) -> str | None:
    """Kite Web's TradingView chart deep link
    (https://kite.zerodha.com/chart/ext/tvc/{exchange}/{symbol}/{token}).
    Opens fine even without an active Kite Web session in that browser —
    it just redirects to login first in that case, same as any other
    kite.zerodha.com page. Returns None (no link) when the token is
    missing, e.g. for scan history rows saved before this field existed."""
    if not instrument_token:
        return None
    return f"https://kite.zerodha.com/chart/ext/tvc/{exchange}/{symbol}/{instrument_token}"
