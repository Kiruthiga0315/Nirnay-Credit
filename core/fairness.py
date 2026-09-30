"""OWNER: M2. F5 priced fairness: metrics, in-processing mitigation, frontier, proxy audit.
Writes artifacts/frontier.json, artifacts/proxy_audit.json, artifacts/fairness_groups.json.

Fairness note (wording rule): say "measured and mitigated under stated definitions".
Metrics conflict mathematically when base rates differ — we expose the trade-off instead of hiding it.
Protected attributes are never model inputs; group-aware thresholds appear only as policy simulations.
"""
from __future__ import annotations

from typing import Any

from core.contracts import FairnessReport
from core.reference import stable_unit

# Reference portfolio sizes (match the generator target)
_N_TOTAL = 20_000
_N_WOMEN_LED = 3_200      # ~16%
_N_RURAL = 5_200          # ~26%
_N_WOMEN_RURAL = 900      # intersectional


def _group_metrics(policy: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Deterministic group metrics that respond sensibly to mitigation policies.

    The 'mitigation' key and 'strength' (0-1) adjust approval rates and TPR gaps.
    Base disparity reflects thin-file bias in the legacy policy (Blueprint §5.2).
    """
    strength = float(policy.get("strength", 0.0))
    mitigation = policy.get("mitigation", "none")

    # Reweighing and in-processing narrow the gap; group-threshold widens approvals
    if mitigation in ("reweighing", "in_processing", "exponentiated_gradient"):
        gap_reduction = 0.60 * strength   # up to 60% of gap closed
    elif mitigation == "threshold":
        gap_reduction = 0.80 * strength
    else:
        gap_reduction = 0.0

    # Seed slight variation so different policy param combos produce different numbers
    u = stable_unit(str(sorted(policy.items())), "fairness")

    base_approval_other = round(0.52 + 0.03 * u, 3)
    base_tpr_other = round(0.70 + 0.02 * u, 3)

    women_gap = round((0.11 - 0.05 * gap_reduction) * (1 + 0.05 * u), 3)
    rural_gap = round((0.13 - 0.06 * gap_reduction) * (1 + 0.04 * u), 3)
    tpr_gap_women = round(-(0.08 - 0.04 * gap_reduction) * (1 + 0.03 * u), 3)
    tpr_gap_rural = round(-(0.10 - 0.05 * gap_reduction) * (1 + 0.03 * u), 3)

    approval_women = round(base_approval_other - women_gap, 3)
    approval_rural = round(base_approval_other - rural_gap, 3)
    tpr_women = round(base_tpr_other + tpr_gap_women, 3)
    tpr_rural = round(base_tpr_other + tpr_gap_rural, 3)

    # ECE: calibration error stays small regardless of mitigation
    ece_other = round(0.018 + 0.004 * stable_unit("ece_other", str(policy)), 4)
    ece_women = round(0.022 + 0.006 * stable_unit("ece_women", str(policy)), 4)
    ece_rural = round(0.025 + 0.005 * stable_unit("ece_rural", str(policy)), 4)

    return {
        "women_led": {
            "n": _N_WOMEN_LED,
            "approval_rate": approval_women,
            "tpr": tpr_women,
            "ece": ece_women,
        },
        "other": {
            "n": _N_TOTAL - _N_WOMEN_LED,
            "approval_rate": base_approval_other,
            "tpr": base_tpr_other,
            "ece": ece_other,
        },
        "rural": {
            "n": _N_RURAL,
            "approval_rate": approval_rural,
            "tpr": tpr_rural,
            "ece": ece_rural,
        },
        "urban_metro": {
            "n": _N_TOTAL - _N_RURAL,
            "approval_rate": base_approval_other,
            "tpr": base_tpr_other,
            "ece": ece_other,
        },
    }


def fairness_report(policy: dict[str, Any] | None = None) -> FairnessReport:
    """Metrics by group + intersectional CIs for a policy.

    Policy dict keys (all optional):
        mitigation: "none" | "reweighing" | "in_processing" | "threshold"
        strength: float in [0, 1] — how aggressively to apply the mitigation

    All numbers are from the stub under documented assumptions; model_version='stub-...'.

    Example:
        r = fairness_report({"mitigation": "reweighing", "strength": 0.5})
        r["adverse_impact_ratio"]["women_led"]  # > 0.79 (gap narrowed)
        r["tpr_gap"]["women_led"]               # closer to 0 than without mitigation

    Args:
        policy: dict describing the fairness mitigation policy, or None for baseline.

    Returns:
        FairnessReport with by_group, adverse_impact_ratio, tpr_gap, intersectional.
    """
    p = policy or {"mitigation": "none"}
    by_group = _group_metrics(p)

    ref_approval = by_group["other"]["approval_rate"]
    ref_tpr = by_group["other"]["tpr"]

    adverse_impact_ratio = {
        g: round(v["approval_rate"] / ref_approval, 3)
        for g, v in by_group.items()
        if g != "other"
    }
    tpr_gap = {
        g: round(v["tpr"] - ref_tpr, 3)
        for g, v in by_group.items()
        if g != "other"
    }

    # Intersectional: women-led × rural
    women_rural_approval = round(
        (by_group["women_led"]["approval_rate"] + by_group["rural"]["approval_rate"]) / 2
        - 0.04,   # intersectional penalty (from generator bias mechanism)
        3,
    )
    # Clamp to plausible range
    women_rural_approval = max(0.25, min(0.60, women_rural_approval))
    ci_half = round(1.96 * (women_rural_approval * (1 - women_rural_approval) / _N_WOMEN_RURAL) ** 0.5, 3)

    intersectional = [
        {
            "group": "women_led x rural",
            "n": _N_WOMEN_RURAL,
            "approval_rate": women_rural_approval,
            "ci_low": round(women_rural_approval - ci_half, 3),
            "ci_high": round(women_rural_approval + ci_half, 3),
            "small_n": _N_WOMEN_RURAL < 500,
        }
    ]

    return {
        "policy": p,
        "by_group": by_group,
        "adverse_impact_ratio": adverse_impact_ratio,
        "tpr_gap": tpr_gap,
        "intersectional": intersectional,
    }


def build_artifacts(smoke: bool = False) -> None:
    print("[fairness] STUB - M2 to implement")
