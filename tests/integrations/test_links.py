from integrations.kite.links import chart_url


def test_chart_url_builds_expected_format():
    assert chart_url("NSE", "TCS", 2953217) == "https://kite.zerodha.com/chart/ext/tvc/NSE/TCS/2953217"


def test_chart_url_none_when_token_missing():
    assert chart_url("NSE", "TCS", None) is None


def test_chart_url_none_when_token_falsy():
    assert chart_url("NSE", "TCS", 0) is None
