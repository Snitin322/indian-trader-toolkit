import pytest

from core.exit_planner import InvalidExitPlanError, plan_exit


def test_or_mid_stop_matches_reel_example():
    # From the original repo's own worked example: range 354.47-362.18,
    # entry 364.18, stop at the midpoint 358.32, 1R target.
    plan = plan_exit(
        entry_price=364.18, stop_style="or-mid", target_r_multiple=1.0,
        range_high=362.18, range_low=354.47,
    )
    assert plan.stop_loss == pytest.approx(358.325)
    assert plan.risk_per_share == pytest.approx(364.18 - 358.325)
    assert plan.profit_target == pytest.approx(364.18 + (364.18 - 358.325))


def test_or_low_stop():
    plan = plan_exit(entry_price=100.0, stop_style="or-low", range_low=95.0)
    assert plan.stop_loss == 95.0
    assert plan.risk_per_share == 5.0
    assert plan.profit_target == 105.0  # default target_r_multiple=1.0


def test_custom_stop():
    plan = plan_exit(entry_price=100.0, stop_style="custom", custom_stop=90.0, target_r_multiple=2.0)
    assert plan.stop_loss == 90.0
    assert plan.risk_per_share == 10.0
    assert plan.profit_target == 120.0


def test_or_mid_requires_range():
    with pytest.raises(InvalidExitPlanError):
        plan_exit(entry_price=100.0, stop_style="or-mid")


def test_custom_requires_custom_stop():
    with pytest.raises(InvalidExitPlanError):
        plan_exit(entry_price=100.0, stop_style="custom")


def test_unknown_stop_style_rejected():
    with pytest.raises(InvalidExitPlanError):
        plan_exit(entry_price=100.0, stop_style="bogus")


def test_stop_above_entry_rejected():
    with pytest.raises(InvalidExitPlanError):
        plan_exit(entry_price=100.0, stop_style="custom", custom_stop=105.0)


def test_stop_equal_to_entry_rejected():
    with pytest.raises(InvalidExitPlanError):
        plan_exit(entry_price=100.0, stop_style="custom", custom_stop=100.0)


def test_nonpositive_target_multiple_rejected():
    with pytest.raises(InvalidExitPlanError):
        plan_exit(entry_price=100.0, stop_style="custom", custom_stop=90.0, target_r_multiple=0)
