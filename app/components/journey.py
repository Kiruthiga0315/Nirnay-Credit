"""OWNER: M4. Recourse Journey Simulator (F10).

Algorithm: apply recommended levers gradually over `months` months (default 6)
using a normalised S-curve so early months show slower progress and later months
accelerate – matching real-world behaviour where compliance and habit changes lag
initially before compounding.

S-curve used: sigmoid shifted and normalised so progress(0)=0, progress(1)=1.
    raw(t) = 1 / (1 + exp(-12*(t-0.5)))
    progress(t) = (raw(t) - raw(0)) / (raw(1) - raw(0))

Only verifiable levers from core.recourse are applied; gameable and immutable
features are never touched (AGENTS.md rule 10).
Requires exactly 6 calls to core.score per simulate_journey call (months=6).
"""
from __future__ import annotations

import copy
import json
import math
import pathlib
from typing import Any

import core

# Approval threshold – mirrors ui.pd_gauge default
APPROVAL_THRESHOLD: float = 0.5

_ARTIFACTS = pathlib.Path(__file__).resolve().parents[2] / "artifacts"


# ---------------------------------------------------------------------------
# S-curve helpers
# ---------------------------------------------------------------------------

def _s_raw(t: float) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-12.0 * (t - 0.5)))
    except OverflowError:
        return 0.0 if t < 0.5 else 1.0


_S0 = _s_raw(0.0)
_S1 = _s_raw(1.0)


def _s_progress(t: float) -> float:
    """Normalised S-curve: progress(0)=0, progress(1)=1."""
    return (_s_raw(t) - _S0) / (_S1 - _S0)


# ---------------------------------------------------------------------------
# Journey simulation
# ---------------------------------------------------------------------------

def simulate_journey(
    borrower: dict[str, Any],
    recourse_result: dict[str, Any] | None,
    months: int = 6,
) -> dict[str, Any]:
    """Apply recommended levers over `months` months; re-score each month.

    Args:
        borrower:       feature dict (must contain 'id').
        recourse_result: RecourseResult from core.recourse, or None.
        months:         number of forward months to simulate (default 6).

    Returns:
        {
            "months":         [0, 1, ..., months]  list[int]
            "pd_curve":       PD at each month     list[float]
            "approval_month": first month where PD < threshold, or None
            "threshold":      float
            "model_version":  str
            "interpolation":  "s-curve"  (documented)
        }
    """
    base_score = core.score(borrower)
    base_pd = base_score["pd"]
    model_version = base_score["model_version"]

    actions: list[dict[str, Any]] = []
    if recourse_result and recourse_result.get("actions"):
        actions = recourse_result["actions"]

    month_list = list(range(months + 1))
    pd_curve: list[float] = [round(base_pd, 4)]
    approval_month: int | None = None

    if base_pd < APPROVAL_THRESHOLD:
        approval_month = 0

    for m in range(1, months + 1):
        t = m / months
        progress = _s_progress(t)
        modified = copy.deepcopy(borrower)
        for action in actions:
            lever = action.get("lever")
            current = action.get("current", modified.get(lever, 0.0))
            target = action.get("target", current)
            if lever is not None:
                modified[lever] = current + progress * (target - current)
        result = core.score(modified)
        pd_m = round(result["pd"], 4)
        pd_curve.append(pd_m)
        if approval_month is None and pd_m < APPROVAL_THRESHOLD:
            approval_month = m

    return {
        "months": month_list,
        "pd_curve": pd_curve,
        "approval_month": approval_month,
        "threshold": APPROVAL_THRESHOLD,
        "model_version": model_version,
        "interpolation": "s-curve",
    }


# ---------------------------------------------------------------------------
# Group comparison (only if M2's fairness_groups artifact exists)
# ---------------------------------------------------------------------------

def group_journey_comparison() -> dict[str, Any] | None:
    """Read approval rates by group from M2's fairness_groups.json artifact.

    Returns a summary dict if the artifact exists, else None.
    Fields: women_led_approval_rate, not_women_led_approval_rate, tpr_gap.
    """
    fg_path = _ARTIFACTS / "fairness_groups.json"
    if not fg_path.exists():
        return None
    try:
        data = json.loads(fg_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None

    by_group = data.get("by_group", {})
    women = by_group.get("women_led")
    others = by_group.get("not_women_led")
    if not women or not others:
        return None

    return {
        "women_led_approval_rate": women.get("approval_rate", 0.0),
        "not_women_led_approval_rate": others.get("approval_rate", 0.0),
        "tpr_gap": data.get("tpr_gap", {}).get("women_led", 0.0),
        "ai_ratio": data.get("adverse_impact_ratio", {}).get("women_led"),
    }


# ---------------------------------------------------------------------------
# Pre-defined "safe" borrower presets (T4)
# ---------------------------------------------------------------------------

SAFE_BORROWERS: list[dict[str, Any]] = [
    {
        "id": "MSME-00001",
        "label": "Meena – Women-led textile unit (reference persona)",
        "note": "Thin-file borrower; recourse lever is receivable_days.",
    },
    {
        "id": "MSME-00005",
        "label": "MSME-00005 – Fast recourse scenario",
        "note": "Deterministic stub; reaches threshold by month 4.",
    },
    {
        "id": "MSME-00010",
        "label": "MSME-00010 – Alternative preset",
        "note": "Deterministic stub; moderate PD profile.",
    },
]
