from datetime import datetime

from auth import app_auth
from core.types import Setup
from storage.repositories import scan_results_repo


def test_save_and_get_latest_results():
    user_id, _ = app_auth.register("scanner@example.com", "correcthorse")
    setups = [
        Setup(symbol="TCS", exchange="NSE", interval="day", setup_type="breakout_20d",
              as_of=datetime(2026, 1, 1), details={"close": 101.0}),
        Setup(symbol="INFY", exchange="NSE", interval="day", setup_type="oversold",
              as_of=datetime(2026, 1, 1), details={"rsi": 25.0}),
    ]
    scan_results_repo.save_results(user_id, setups)

    results = scan_results_repo.get_latest_results(user_id)
    assert len(results) == 2
    symbols = {r["symbol"] for r in results}
    assert symbols == {"TCS", "INFY"}
    tcs_row = next(r for r in results if r["symbol"] == "TCS")
    assert tcs_row["setup_payload"]["close"] == 101.0


def test_results_isolated_per_user():
    user_a, _ = app_auth.register("scana@example.com", "correcthorse")
    user_b, _ = app_auth.register("scanb@example.com", "correcthorse")
    scan_results_repo.save_results(user_a, [
        Setup(symbol="TCS", exchange="NSE", interval="day", setup_type="breakout_20d",
              as_of=datetime(2026, 1, 1), details={}),
    ])
    assert len(scan_results_repo.get_latest_results(user_a)) == 1
    assert len(scan_results_repo.get_latest_results(user_b)) == 0


def test_save_empty_list_is_a_noop():
    user_id, _ = app_auth.register("scanempty@example.com", "correcthorse")
    scan_results_repo.save_results(user_id, [])
    assert scan_results_repo.get_latest_results(user_id) == []
