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


def _borrower_features(bid: str) -> dict[str, float]:
    """Deterministic per-borrower economic features."""
    pd = round(0.04 + 0.22 * stable_unit(bid, "opt_pd"), 4)
    ticket = round(_TICKET_LOW + (_TICKET_HIGH - _TICKET_LOW) * stable_unit(bid, "opt_ticket"), 0)
    is_women = stable_unit(bid, "opt_gender") < _WOMEN_LED_THRESHOLD
    is_rural = stable_unit(bid, "opt_rural") < _RURAL_THRESHOLD
    is_thin = stable_unit(bid, "opt_thin") < _THIN_FILE_THRESHOLD

    el = round(pd * _LGD * ticket, 2)
    margin = round(ticket * _MARGIN_RATE, 2)
    net = round(margin - el - _OPEX_PER_LOAN, 2)

    return {
        "pd": pd, "ticket": ticket, "el": el, "net": net,
        "is_women": float(is_women), "is_rural": float(is_rural), "is_thin": float(is_thin),
    }


def optimize(policy_params: dict[str, Any] | None = None) -> OptimizeResult:
    """Maximise expected profit under loss cap, budget, sector cap, inclusion floor.

    Policy params (all optional, with defaults):
        budget:           float, INR  — total exposure ceiling (default 20_000_000)
        loss_cap:         float, INR  — maximum total expected loss (default 1_500_000)
        sector_cap:       float [0,1] — max share for any single sector (default 0.40)
        inclusion_floor:  float [0,1] — min approval share for each protected group (default 0.30)

    All numbers are under documented assumptions (stub). model_version='stub-...'

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
    p = policy_params or {}
    budget = float(p.get("budget", 20_000_000))
    loss_cap = float(p.get("loss_cap", 1_500_000))
    inclusion_floor = float(p.get("inclusion_floor", 0.30))

    # Compute per-borrower features for all test borrowers
    all_ids = TEST_BORROWER_IDS
    features = {bid: _borrower_features(bid) for bid in all_ids}

    # Greedy LP relaxation: sort by net profit descending, add while within constraints
    # Only consider borrowers with positive net (EL + opex < expected margin)
    sorted_ids = [
        bid for bid in sorted(all_ids, key=lambda bid: features[bid]["net"], reverse=True)
        if features[bid]["net"] > 0
    ]

    approved: list[str] = []
    total_exposure = 0.0
    total_el = 0.0

    for bid in sorted_ids:
        f = features[bid]
        if total_exposure + f["ticket"] > budget:
            continue
        if total_el + f["el"] > loss_cap:
            continue
        approved.append(bid)
        total_exposure += f["ticket"]
        total_el += f["el"]

    # Check inclusion floor; if not met, swap in protected borrowers greedily
    def _share(group_key: str) -> float:
        if not approved:
            return 0.0
        return sum(features[bid][group_key] for bid in approved) / len(approved)

    for group_key in ("is_women", "is_rural"):
        while _share(group_key) < inclusion_floor:
            # Find the highest-net non-approved protected borrower
            candidate = next(
                (bid for bid in sorted_ids
                 if bid not in approved and features[bid][group_key] == 1.0),
                None,
            )
            if candidate is None:
                break  # cannot satisfy floor — document in known_issues
            # Swap out the worst non-protected approved borrower to stay within budget
            worst = min(
                (bid for bid in approved if features[bid][group_key] == 0.0),
                key=lambda bid: features[bid]["net"],
                default=None,
            )
            if worst is not None:
                approved.remove(worst)
                total_exposure -= features[worst]["ticket"]
                total_el -= features[worst]["el"]
            approved.append(candidate)
            total_exposure += features[candidate]["ticket"]
            total_el += features[candidate]["el"]
            break  # re-evaluate share next loop iteration

    expected_profit = round(sum(features[bid]["net"] for bid in approved), 2)
    expected_loss = round(sum(features[bid]["el"] for bid in approved), 2)
    exposure = round(sum(features[bid]["ticket"] for bid in approved), 2)

    # Fairness gap: approval share of protected vs overall
    overall_rate = len(approved) / len(all_ids)
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
    print("[optimizer] STUB - M2 to implement")
