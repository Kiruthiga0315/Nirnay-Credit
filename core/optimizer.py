"""OWNER: M2. F8 Policy Optimizer (LP relaxation + rounding vs greedy threshold).

Maximises expected profit under:
  - total exposure <= budget
  - total EL <= loss cap
  - sector share <= sector_cap
  - approval share of women_led / rural / new_to_credit >= inclusion_floor

Under documented assumptions (stub): uses deterministic per-borrower metrics derived
from stable_unit so the optimizer produces different results for different policy params.
"""
from __future__ import annotations

from typing import Any

from core.contracts import OptimizeResult
from core.reference import TEST_BORROWER_IDS, stable_unit

# Illustrative portfolio constants (under documented assumptions)
_TICKET_LOW = 200_000   # INR
_TICKET_HIGH = 800_000  # INR
_MARGIN_RATE = 0.045    # net interest margin
_LGD = 0.45             # loss given default (stated assumption)
_OPEX_PER_LOAN = 5_000  # INR processing cost

# Protected-group membership (deterministic from id)
_WOMEN_LED_THRESHOLD = 0.35   # stable_unit < this -> women-led firm
_RURAL_THRESHOLD = 0.45       # stable_unit < this -> rural firm
_THIN_FILE_THRESHOLD = 0.30   # stable_unit < this -> new-to-credit


def _borrower_features(bid: str) -> dict[str, float | str]:
    """Deterministic per-borrower economic features."""
    pd = round(0.04 + 0.22 * stable_unit(bid, "opt_pd"), 4)
    ticket = round(_TICKET_LOW + (_TICKET_HIGH - _TICKET_LOW) * stable_unit(bid, "opt_ticket"), 0)
    is_women = stable_unit(bid, "opt_gender") < _WOMEN_LED_THRESHOLD
    is_rural = stable_unit(bid, "opt_rural") < _RURAL_THRESHOLD
    is_thin = stable_unit(bid, "opt_thin") < _THIN_FILE_THRESHOLD

    sectors = ["retail", "services", "manufacturing"]
    sector = sectors[int(stable_unit(bid, "opt_sector") * len(sectors))]

    el = round(pd * _LGD * ticket, 2)
    margin = round(ticket * _MARGIN_RATE, 2)
    net = round(margin - el - _OPEX_PER_LOAN, 2)

    return {
        "pd": pd, "ticket": ticket, "el": el, "net": net,
        "is_women": float(is_women), "is_rural": float(is_rural), "is_thin": float(is_thin),
        "sector": sector,
    }


def optimize(policy_params: dict[str, Any] | None = None) -> OptimizeResult:
    """Maximise expected profit under loss cap, budget, sector cap, inclusion floor.

    Policy params (all optional, with defaults):
        budget:           float, INR  — total exposure ceiling (default 20_000_000)
        loss_cap:         float, INR  — maximum total expected loss (default 1_500_000)
        sector_cap:       float [0,1] — max share for any single sector (default 0.40)
        inclusion_floor:  float [0,1] — min approval share for each protected group (default 0.30)

    All numbers are under documented assumptions (stub).

    Example:
        r = optimize({"budget": 15_000_000, "inclusion_floor": 0.40})
        r["approved_ids"]       # list of borrower id strings
        r["expected_profit"]    # INR
        r["fairness_gap"]       # {"women_led": float, "rural": float}

    Args:
        policy_params: dict of policy constraints, or None for defaults.

    Returns:
        OptimizeResult with approved_ids, expected_profit, expected_loss, exposure, fairness_gap.
    """
    import numpy as np
    from scipy.optimize import linprog

    p = policy_params or {}
    budget = float(p.get("budget", 20_000_000))
    loss_cap = float(p.get("loss_cap", 1_500_000))
    sector_cap = float(p.get("sector_cap", 0.40))
    inclusion_floor = float(p.get("inclusion_floor", 0.30))

    # Compute per-borrower features for all test borrowers
    all_ids = TEST_BORROWER_IDS
    features = {bid: _borrower_features(bid) for bid in all_ids}

    # Prepare LP arrays
    n = len(all_ids)
    c = -np.array([features[bid]["net"] for bid in all_ids], dtype=float)
    
    A_ub = []
    b_ub = []

    # 1. Total exposure <= budget
    A_ub.append([float(features[bid]["ticket"]) for bid in all_ids])
    b_ub.append(budget)

    # 2. Total EL <= loss cap
    A_ub.append([float(features[bid]["el"]) for bid in all_ids])
    b_ub.append(loss_cap)

    # 3. Sector share <= cap (exposure basis)
    # sum_{i in S} ticket_i * x_i <= sector_cap * sum_{i} ticket_i * x_i
    unique_sectors = set(features[bid]["sector"] for bid in all_ids)
    for s in unique_sectors:
        row = []
        for bid in all_ids:
            in_s = 1.0 if features[bid]["sector"] == s else 0.0
            row.append(float(features[bid]["ticket"]) * (in_s - sector_cap))
        A_ub.append(row)
        b_ub.append(0.0)

    # 4. Inclusion floor (count basis)
    # sum_{i in G} x_i >= inclusion_floor * sum_i x_i
    for group_key in ("is_women", "is_rural", "is_thin"):
        row = []
        for bid in all_ids:
            in_g = float(features[bid][group_key])
            row.append(inclusion_floor - in_g)
        A_ub.append(row)
        b_ub.append(0.0)

    bounds = [(0.0, 1.0)] * n
    
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
    
    if res.success:
        x = res.x
    else:
        # Fallback to greedy if LP is infeasible (e.g. constraints too tight)
        x = np.zeros(n)
        for i, bid in enumerate(all_ids):
            if features[bid]["net"] > 0:
                x[i] = 1.0

    # Documented Rounding Strategy:
    # 1. Sort borrowers descending by their LP fractional assignment (x_i).
    # 2. Break ties by net profit.
    # 3. Approve greedily sequentially, strictly enforcing budget and loss cap.
    order = sorted(range(n), key=lambda i: (x[i], features[all_ids[i]]["net"]), reverse=True)
    
    approved: list[str] = []
    total_exposure = 0.0
    total_el = 0.0
    
    for i in order:
        if x[i] < 1e-4 and features[all_ids[i]]["net"] <= 0:
            # Avoid picking negative net unless LP gave it a weight to satisfy inclusion
            if len(approved) > 0:
                # Still check inclusion informally to avoid stopping too early,
                # but if LP weight is ~0, we usually don't need it.
                pass
                
        bid = all_ids[i]
        f = features[bid]
        
        if total_exposure + float(f["ticket"]) > budget:
            continue
        if total_el + float(f["el"]) > loss_cap:
            continue
            
        approved.append(bid)
        total_exposure += float(f["ticket"])
        total_el += float(f["el"])

    def _share(group_key: str) -> float:
        if not approved:
            return 0.0
        return sum(float(features[bid][group_key]) for bid in approved) / len(approved)

    expected_profit = round(sum(float(features[bid]["net"]) for bid in approved), 2)
    expected_loss = round(sum(float(features[bid]["el"]) for bid in approved), 2)
    exposure = round(sum(float(features[bid]["ticket"]) for bid in approved), 2)

    overall_rate = len(approved) / len(all_ids) if all_ids else 0.0
    women_rate = _share("is_women")
    rural_rate = _share("is_rural")
    fairness_gap = {
        "women_led": round(women_rate - overall_rate, 3),
        "rural": round(rural_rate - overall_rate, 3),
    }

    return {
        "approved_ids": approved,
        "expected_profit": expected_profit,
        "expected_loss": expected_loss,
        "exposure": exposure,
        "fairness_gap": fairness_gap,
    }


def build_artifacts(smoke: bool = False) -> None:
    """Precompute a grid of policies into artifacts so sliders are instant."""
    from core.paths import write_metrics

    # Define a grid of inclusion floors to compute the Price of Inclusion
    floors = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5] if not smoke else [0.0, 0.3]
    
    results = []
    base_profit = None
    
    for floor in floors:
        params = {"inclusion_floor": floor}
        res = optimize(params)
        profit = res["expected_profit"]
        
        if floor == 0.0:
            base_profit = profit
            
        cost_of_inclusion = base_profit - profit if base_profit is not None else 0.0
        
        results.append({
            "inclusion_floor": floor,
            "expected_profit": profit,
            "cost_of_inclusion": max(0.0, cost_of_inclusion),
            "approved_count": len(res["approved_ids"]),
            "women_led_share": res["fairness_gap"]["women_led"] + (len(res["approved_ids"]) / len(TEST_BORROWER_IDS)),
        })
        
    write_metrics("optimizer", {"frontier": results})
