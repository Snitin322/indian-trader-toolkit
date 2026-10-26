"""NSE/BSE equity universe: fetch Kite's instrument master and filter down
to plain, tradeable common-stock equities — the Indian equivalent of the
original repo's Nasdaq Trader symbol-directory filtering.

filter_equity_universe() is pure (takes raw dicts in, Instruments out) so
it's unit-testable without a live Kite session; fetch_equity_universe() is
the one-line I/O wrapper around it."""

from dataclasses import dataclass

# Trading-symbol suffixes marking a non-standard series (trade-to-trade /
# no same-day settlement, SME board, etc.) — not exhaustive. Flagged as
# best-effort in PROGRESS.md, same honesty norm as the rest of the scanner:
# never silently claim a "clean" universe that isn't actually fully vetted.
EXCLUDED_SYMBOL_SUFFIXES = ("-BE", "-SM", "-ST", "-BZ", "-BL", "-IL")


@dataclass(frozen=True)
class Instrument:
    instrument_token: int
    tradingsymbol: str
    name: str
    exchange: str
    segment: str
    instrument_type: str
    lot_size: int
    tick_size: float


def filter_equity_universe(raw_instruments: list[dict], exchange: str) -> list[Instrument]:
    out = []
    for row in raw_instruments:
        if row.get("exchange") != exchange or row.get("segment") != exchange:
            continue
        if row.get("instrument_type") != "EQ":
            continue
        symbol = row.get("tradingsymbol", "")
        if any(symbol.endswith(suffix) for suffix in EXCLUDED_SYMBOL_SUFFIXES):
            continue
        out.append(
            Instrument(
                instrument_token=int(row["instrument_token"]),
                tradingsymbol=symbol,
                name=row.get("name", ""),
                exchange=row["exchange"],
                segment=row["segment"],
                instrument_type=row["instrument_type"],
                lot_size=int(row.get("lot_size", 1) or 1),
                tick_size=float(row.get("tick_size", 0.05) or 0.05),
            )
        )
    return out


def fetch_equity_universe(kite, exchange: str) -> list[Instrument]:
    raw = kite.instruments(exchange)
    return filter_equity_universe(raw, exchange)


def build_symbol_token_map(instruments: list[Instrument]) -> dict[str, int]:
    return {inst.tradingsymbol: inst.instrument_token for inst in instruments}
