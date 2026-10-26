from auth import app_auth
from storage.repositories import plans_repo


def test_create_and_get_plan():
    user_id, _ = app_auth.register("plans@example.com", "correcthorse")
    plan_id = plans_repo.create_plan(
        user_id, "TCS", "NSE", "5minute",
        entry_trigger_payload={"trigger_close": 364.18}, stop_loss=358.32, profit_target=370.04,
    )
    plan = plans_repo.get_plan(user_id, plan_id)
    assert plan["symbol"] == "TCS"
    assert plan["status"] == "active"
    assert plan["entry_trigger_payload"]["trigger_close"] == 364.18


def test_get_plan_isolated_per_user():
    user_a, _ = app_auth.register("plansa@example.com", "correcthorse")
    user_b, _ = app_auth.register("plansb@example.com", "correcthorse")
    plan_id = plans_repo.create_plan(
        user_a, "TCS", "NSE", "day", entry_trigger_payload={}, stop_loss=90.0, profit_target=110.0,
    )
    assert plans_repo.get_plan(user_a, plan_id) is not None
    assert plans_repo.get_plan(user_b, plan_id) is None


def test_get_active_plans_excludes_closed():
    user_id, _ = app_auth.register("active@example.com", "correcthorse")
    p1 = plans_repo.create_plan(
        user_id, "TCS", "NSE", "day", entry_trigger_payload={}, stop_loss=90.0, profit_target=110.0,
    )
    p2 = plans_repo.create_plan(
        user_id, "INFY", "NSE", "day", entry_trigger_payload={}, stop_loss=90.0, profit_target=110.0,
    )
    plans_repo.update_status(user_id, p2, "expired")

    active = plans_repo.get_active_plans(user_id)
    assert len(active) == 1
    assert active[0]["id"] == p1


def test_update_time_machine_payload():
    user_id, _ = app_auth.register("tm@example.com", "correcthorse")
    plan_id = plans_repo.create_plan(
        user_id, "TCS", "NSE", "day", entry_trigger_payload={}, stop_loss=90.0, profit_target=110.0,
    )
    plans_repo.update_time_machine_payload(user_id, plan_id, {"target_first_pct": 29.4})
    plan = plans_repo.get_plan(user_id, plan_id)
    assert plan["time_machine_payload"]["target_first_pct"] == 29.4
