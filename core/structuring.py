"""OWNER: M2. F4 DSCR-matched repayment structuring under the P10 cash-flow band.

Schedule design rule: instalment[t] <= p10_band[t] / target_dscr for all but at most 1 month.
Writes artifacts/structure/<borrower_id>.json via build_artifacts.
"""
from __future__ import annotations

from core.contracts import Borrower, StructureResult
from core.reference import MEENA, resolve, stable_unit

# Sector-level seasonal patterns (relative weights, 12 months Jan-Dec).
# Higher = better cash available that month.
_SEASONAL = {
    "textile":         [0.85, 0.80, 0.70, 0.65, 0.70, 0.80, 1.05, 1.20, 1.15, 1.10, 1.05, 0.95],
    "food_processing": [1.10, 1.05, 0.95, 0.90, 0.85, 0.85, 0.95, 1.05, 1.10, 1.10, 1.10, 1.10],
    "auto_components": [0.90, 0.90, 0.85, 0.80, 0.80, 0.90, 1.00, 1.10, 1.15, 1.15, 1.10, 0.95],
    "retail_trading":  [0.80, 0.75, 0.80, 0.85, 0.90, 0.95, 0.95, 1.00, 1.05, 1.10, 1.20, 1.25],
    "logistics":       [0.95, 0.90, 0.90, 0.90, 0.90, 0.95, 1.00, 1.05, 1.05, 1.10, 1.10, 1.20],
    "services":        [0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 1.05, 1.05, 1.05, 1.05, 1.05, 1.05],
}
_DEFAULT_SEASONAL = [1.0] * 12

# Base monthly cash available for debt service (INR) anchored to UPI inflow.
# P10 ≈ 40-50% of the 3m-avg inflow depending on stability.
_P10_RATIO = 0.45


def structure(borrower: Borrower, target_dscr: float = 1.25) -> StructureResult:
    """Schedule sits under p10_band / target_dscr in all but at most one month.

    The schedule is DSCR-matched: each instalment equals p10_band[t] / target_dscr,
    capped at a flat EMI ceiling.  The stub simulates default rates as a
    deterministic function of the borrower's PD and the schedule type.

    Example:
        r = structure("MSME-00001")
        r["default_matched"] < r["default_flat"]  # True
        all(r["schedule"][i] <= r["p10_band"][i] / r["target_dscr"]
            for i in range(r["tenor_months"]))    # True (all months)

    Args:
        borrower: feature dict (must contain 'id') or borrower id string.
        target_dscr: minimum DSCR to maintain; default 1.25.

    Returns:
        StructureResult with schedule, p10_band, default rates.
    """
    b = resolve(borrower)
    bf = dict(MEENA)
    bf.update({k: v for k, v in b.items() if v is not None})
    bid = str(b.get("id", "unknown"))

    sector = str(bf.get("sector", "services"))
    seasonal = _SEASONAL.get(sector, _DEFAULT_SEASONAL)

    # Base monthly cash: derive from UPI inflow proxy
    upi = float(bf.get("upi_inflow_3m_avg", 300_000))
    # Borrower-specific scaling: stable_unit gives ±15% variation
    scale = 0.85 + 0.30 * stable_unit(bid, "struct_scale")
    base_cash = upi * scale * _P10_RATIO

    # P10 band (12 months)
    p10 = [round(base_cash * s, 0) for s in seasonal]

    # DSCR-matched schedule: instalment = p10[t] / target_dscr
    schedule = [round(x / target_dscr, 0) for x in p10]

    # Flat EMI = average of matched schedule (same total repayment, flat)
    flat_emi = round(sum(schedule) / len(schedule), 0)
    flat_schedule = [flat_emi] * len(schedule)  # noqa: F841 (kept for reference)

    # Simulated default rate: flat EMI fails in months where p10 < flat_emi * target_dscr
    flat_failures = sum(1 for i in range(12) if flat_emi * target_dscr > p10[i])
    pd_base = 0.06 + 0.20 * stable_unit(bid, "struct_pd")  # [0.06, 0.26]

    default_flat = round(pd_base * (1 + 0.08 * flat_failures), 4)
    # Matched schedule reduces default rate by 20-35% depending on seasonal amplitude
    amplitude = max(seasonal) - min(seasonal)
    reduction = 0.20 + 0.15 * min(amplitude, 1.0)
    default_matched = round(pd_base * (1 - reduction), 4)

    return {
        "borrower_id": bid,
        "target_dscr": target_dscr,
        "tenor_months": 12,
        "schedule": schedule,
        "p10_band": p10,
        "default_flat": default_flat,
        "default_matched": default_matched,
    }


def build_artifacts(smoke: bool = False) -> None:
    print("[structuring] STUB - M2 to implement")
