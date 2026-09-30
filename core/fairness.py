"""OWNER: M2. F5 priced fairness: metrics, in-processing mitigation, frontier, proxy audit.
Writes artifacts/frontier.json, artifacts/proxy_audit.json, artifacts/fairness_groups.json."""
from __future__ import annotations

from typing import Any

from core.contracts import FairnessReport


def fairness_report(policy: dict[str, Any] | None = None) -> FairnessReport:
    """Metrics by group + intersectional CIs for a policy. STUB values."""
    return {
        "policy": policy or {"mitigation": "none"},
        "by_group": {
            "women_led": {"n": 3200, "approval_rate": 0.41, "tpr": 0.62, "ece": 0.02},
            "other": {"n": 16800, "approval_rate": 0.52, "tpr": 0.70, "ece": 0.02},
            "rural": {"n": 5200, "approval_rate": 0.40, "tpr": 0.61, "ece": 0.03},
            "urban_metro": {"n": 14800, "approval_rate": 0.53, "tpr": 0.71, "ece": 0.02},
        },
        "adverse_impact_ratio": {"women_led": 0.79, "rural": 0.75},
        "tpr_gap": {"women_led": -0.08, "rural": -0.10},
        "intersectional": [
            {"group": "women_led x rural", "n": 900, "approval_rate": 0.36,
             "ci_low": 0.33, "ci_high": 0.39, "small_n": False},
        ],
    }


def build_artifacts(smoke: bool = False) -> None:
    print("[fairness] STUB - M2 to implement")
