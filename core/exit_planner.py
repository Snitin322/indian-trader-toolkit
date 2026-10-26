"""Computes a stop-loss and profit target BEFORE entry — the original
repo's `exit.py plan --stop or-mid --target 1R` behavior. Pure math, no I/O.

Only long entries are supported for now (matches the rest of the pipeline:
no shorting, allow_short defaults False in config). Stop styles here are
deliberately the same ones the original ORB example used; "custom" covers
every other setup type, where there's no opening range to derive a stop
from and the user supplies their own stop price directly.
"""

from dataclasses import dataclass

STOP_STYLES = ("or-mid", "or-low", "custom")


class InvalidExitPlanError(ValueError):
    pass


@dataclass
class ExitPlan:
    entry_price: float
    stop_loss: float
    profit_target: float
    risk_per_share: float
    reward_risk_multiple: float


def plan_exit(
    entry_price: float,
    stop_style: str,
    target_r_multiple: float = 1.0,
    range_high: float | None = None,
    range_low: float | None = None,
    custom_stop: float | None = None,
) -> ExitPlan:
    if stop_style not in STOP_STYLES:
        raise InvalidExitPlanError(f"Unknown stop_style: {stop_style}")

    if stop_style == "or-mid":
        if range_high is None or range_low is None:
            raise InvalidExitPlanError("or-mid requires range_high and range_low")
        stop_loss = (range_high + range_low) / 2
    elif stop_style == "or-low":
        if range_low is None:
            raise InvalidExitPlanError("or-low requires range_low")
        stop_loss = range_low
    else:  # custom
        if custom_stop is None:
            raise InvalidExitPlanError("custom stop_style requires custom_stop")
        stop_loss = custom_stop

    risk_per_share = entry_price - stop_loss
    if risk_per_share <= 0:
        raise InvalidExitPlanError(
            f"Stop ({stop_loss}) must be below entry ({entry_price}) for a long position."
        )
    if target_r_multiple <= 0:
        raise InvalidExitPlanError("target_r_multiple must be positive")

    profit_target = entry_price + risk_per_share * target_r_multiple

    return ExitPlan(
        entry_price=entry_price,
        stop_loss=stop_loss,
        profit_target=profit_target,
        risk_per_share=risk_per_share,
        reward_risk_multiple=target_r_multiple,
    )
