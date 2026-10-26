"""NSE index/sector constituent lists and the F&O-eligible stock list.

This is scraped NSE data (CSV archive files), not an official documented
API — URLs and formats can change without notice, same caveat already
carried for the bulk-deal/news integrations (see PROGRESS.md). Every
fetch function is network I/O; the parsing is split into pure functions
(parse_index_csv, parse_fo_csv) so the actual CSV-handling logic is
unit-testable without hitting NSE.

Lets a user scan "Nifty Bank" or "F&O stocks" instead of either typing
symbols by hand or trying to scan all ~9,400 NSE equities (which would
take close to an hour at Kite's historical_data rate limit) — a curated
universe of 10-500 symbols scans in seconds to a few minutes.
"""

import requests

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
_HEADERS = {"User-Agent": _USER_AGENT, "Referer": "https://www.nseindia.com/"}
_TIMEOUT_SECONDS = 15

_INDICES_BASE_URL = "https://nsearchives.nseindia.com/content/indices/"
_FO_LOT_SIZE_URL = "https://nsearchives.nseindia.com/content/fo/fo_mktlots.csv"

# (display name, CSV filename) — every filename here was confirmed live
# against nsearchives.nseindia.com; NSE's naming isn't consistent (some
# have underscores, some don't), so these are deliberately hardcoded
# rather than derived from the display name.
INDEX_UNIVERSES: dict[str, str] = {
    "Nifty 50": "ind_nifty50list.csv",
    "Nifty Next 50": "ind_niftynext50list.csv",
    "Nifty Bank": "ind_niftybanklist.csv",
    "Nifty Private Bank": "ind_nifty_privatebanklist.csv",
    "Nifty PSU Bank": "ind_niftypsubanklist.csv",
    "Nifty Financial Services": "ind_niftyfinancelist.csv",
    "Nifty Midcap 150": "ind_niftymidcap150list.csv",
    "Nifty Smallcap 250": "ind_niftysmallcap250list.csv",
    "Nifty Midsmallcap 400": "ind_niftymidsmallcap400list.csv",
    "Nifty 500": "ind_nifty500list.csv",
    "Nifty Total Market": "ind_niftytotalmarket_list.csv",
    "Nifty Auto": "ind_niftyautolist.csv",
    "Nifty IT": "ind_niftyitlist.csv",
    "Nifty Pharma": "ind_niftypharmalist.csv",
    "Nifty FMCG": "ind_niftyfmcglist.csv",
    "Nifty Metal": "ind_niftymetallist.csv",
    "Nifty Realty": "ind_niftyrealtylist.csv",
    "Nifty Energy": "ind_niftyenergylist.csv",
    "Nifty Media": "ind_niftymedialist.csv",
    "Nifty Healthcare": "ind_niftyhealthcarelist.csv",
    "Nifty Infrastructure": "ind_niftyinfralist.csv",
    "Nifty PSE": "ind_niftypselist.csv",
    "Nifty CPSE": "ind_niftycpselist.csv",
}

FO_UNIVERSE_NAME = "F&O Stocks"

# Index/benchmark underlyings that appear in the F&O lot-size file
# alongside individual stocks — excluded so FO_UNIVERSE_NAME is stocks only.
_FO_INDEX_UNDERLYINGS = {
    "BANKNIFTY", "NIFTY", "FINNIFTY", "NIFTYFPI", "MIDCPNIFTY", "NIFTYNXT50",
}


class NseFetchError(RuntimeError):
    """Raised on a non-200 response or unparseable CSV — never silently
    returns an empty/partial list as if it were a real (if small) universe."""


def parse_index_csv(csv_text: str) -> list[str]:
    """Pure: NSE's index CSVs are `Company Name,Industry,Symbol,Series,ISIN`."""
    lines = [l for l in csv_text.splitlines() if l.strip()]
    if not lines:
        return []
    header = [h.strip() for h in lines[0].split(",")]
    try:
        symbol_idx = header.index("Symbol")
    except ValueError:
        raise NseFetchError(f"Unexpected CSV header, no 'Symbol' column: {header}")
    symbols = []
    for line in lines[1:]:
        fields = line.split(",")
        if len(fields) > symbol_idx:
            symbol = fields[symbol_idx].strip()
            if symbol:
                symbols.append(symbol)
    return symbols


def parse_fo_csv(csv_text: str) -> list[str]:
    """Pure: the F&O lot-size CSV lists index underlyings (BANKNIFTY, NIFTY,
    ...) first, then a `Derivatives on Individual Securities` section
    header, then one row per F&O-eligible stock. Returns stocks only."""
    lines = [l for l in csv_text.splitlines() if l.strip()]
    if len(lines) < 2:
        return []
    symbols = []
    for line in lines[1:]:
        fields = line.split(",")
        if len(fields) < 2:
            continue
        symbol = fields[1].strip()
        if not symbol or symbol == "Symbol" or symbol in _FO_INDEX_UNDERLYINGS:
            continue
        symbols.append(symbol)
    return symbols


def fetch_index_constituents(universe_name: str) -> list[str]:
    filename = INDEX_UNIVERSES.get(universe_name)
    if not filename:
        raise ValueError(f"Unknown universe: {universe_name}")
    resp = requests.get(
        _INDICES_BASE_URL + filename, headers=_HEADERS, timeout=_TIMEOUT_SECONDS
    )
    if resp.status_code != 200:
        raise NseFetchError(f"NSE returned HTTP {resp.status_code} for {universe_name}")
    symbols = parse_index_csv(resp.text)
    if not symbols:
        raise NseFetchError(f"No symbols parsed for {universe_name} — NSE's CSV format may have changed.")
    return symbols


def fetch_fo_stock_list() -> list[str]:
    resp = requests.get(_FO_LOT_SIZE_URL, headers=_HEADERS, timeout=_TIMEOUT_SECONDS)
    if resp.status_code != 200:
        raise NseFetchError(f"NSE returned HTTP {resp.status_code} for the F&O list")
    symbols = parse_fo_csv(resp.text)
    if not symbols:
        raise NseFetchError("No F&O stock symbols parsed — NSE's CSV format may have changed.")
    return symbols
