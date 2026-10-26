from integrations.kite.instruments import build_symbol_token_map, filter_equity_universe


def _row(**overrides):
    base = {
        "instrument_token": 1,
        "exchange_token": 1,
        "tradingsymbol": "TCS",
        "name": "TATA CONSULTANCY SERVICES",
        "last_price": 3500.0,
        "expiry": "",
        "strike": 0.0,
        "tick_size": 0.05,
        "lot_size": 1,
        "instrument_type": "EQ",
        "segment": "NSE",
        "exchange": "NSE",
    }
    base.update(overrides)
    return base


def test_filter_keeps_plain_nse_equity():
    rows = [_row()]
    result = filter_equity_universe(rows, "NSE")
    assert len(result) == 1
    assert result[0].tradingsymbol == "TCS"


def test_filter_excludes_other_exchange():
    rows = [_row(exchange="BSE", segment="BSE")]
    result = filter_equity_universe(rows, "NSE")
    assert result == []


def test_filter_excludes_non_equity_instrument_type():
    rows = [_row(instrument_type="FUT")]
    assert filter_equity_universe(rows, "NSE") == []


def test_filter_excludes_trade_to_trade_series():
    rows = [_row(tradingsymbol="SOMECO-BE")]
    assert filter_equity_universe(rows, "NSE") == []


def test_filter_excludes_sme_series():
    rows = [_row(tradingsymbol="SMECO-SM")]
    assert filter_equity_universe(rows, "NSE") == []


def test_filter_keeps_multiple_valid_rows():
    rows = [_row(instrument_token=1, tradingsymbol="TCS"), _row(instrument_token=2, tradingsymbol="INFY")]
    result = filter_equity_universe(rows, "NSE")
    assert {r.tradingsymbol for r in result} == {"TCS", "INFY"}


def test_build_symbol_token_map():
    rows = [_row(instrument_token=11536, tradingsymbol="TCS")]
    instruments = filter_equity_universe(rows, "NSE")
    mapping = build_symbol_token_map(instruments)
    assert mapping == {"TCS": 11536}
