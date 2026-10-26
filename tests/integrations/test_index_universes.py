import pytest

from integrations.nse.index_universes import (
    INDEX_UNIVERSES,
    NseFetchError,
    parse_fo_csv,
    parse_index_csv,
)


def test_parse_index_csv_extracts_symbols():
    csv_text = (
        "Company Name,Industry,Symbol,Series,ISIN Code\n"
        "Adani Enterprises Ltd.,Metals & Mining,ADANIENT,EQ,INE423A01024\n"
        "Adani Ports and Special Economic Zone Ltd.,Services,ADANIPORTS,EQ,INE742F01042\n"
    )
    assert parse_index_csv(csv_text) == ["ADANIENT", "ADANIPORTS"]


def test_parse_index_csv_empty_input():
    assert parse_index_csv("") == []


def test_parse_index_csv_missing_symbol_column_raises():
    with pytest.raises(NseFetchError):
        parse_index_csv("Company Name,Industry\nFoo,Bar\n")


def test_parse_index_csv_skips_blank_rows():
    csv_text = "Company Name,Industry,Symbol,Series,ISIN Code\n\nFoo Ltd.,X,FOO,EQ,INE000\n\n"
    assert parse_index_csv(csv_text) == ["FOO"]


def test_parse_fo_csv_excludes_index_underlyings_and_section_header():
    csv_text = (
        "UNDERLYING,SYMBOL,OCT-26\n"
        "NIFTY BANK,BANKNIFTY,30\n"
        "NIFTY 50,NIFTY,65\n"
        "Derivatives on Individual Securities,Symbol,\n"
        "ADANI ENERGY SOLUTION LTD,ADANIENSOL,1800\n"
        "ALKEM LABORATORIES LTD.,ALKEM,350\n"
    )
    assert parse_fo_csv(csv_text) == ["ADANIENSOL", "ALKEM"]


def test_parse_fo_csv_strips_padding_whitespace():
    csv_text = "UNDERLYING ,SYMBOL    ,OCT-26\nABB INDIA LIMITED           ,ABB       ,500\n"
    assert parse_fo_csv(csv_text) == ["ABB"]


def test_parse_fo_csv_empty_input():
    assert parse_fo_csv("") == []
    assert parse_fo_csv("header only\n") == []


def test_all_declared_universes_have_nonempty_filenames():
    assert len(INDEX_UNIVERSES) > 15
    for name, filename in INDEX_UNIVERSES.items():
        assert filename.endswith(".csv")
        assert name
