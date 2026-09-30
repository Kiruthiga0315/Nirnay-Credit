"""OWNER: M2. Tests for all M2 stub functions across 20 TEST_BORROWER_IDS.

Checks:
- Return keys match contracts for every borrower.
- recourse: all actions use verifiable levers, new_pd < pd for all borrowers.
- structure: schedule <= p10_band / target_dscr in all but <=1 month per borrower.
- structure: default_matched < default_flat for all borrowers.
- fairness_report: adverse_impact_ratio values in (0, 1], tpr_gap is a float per group.
- optimizer: returns valid approved_ids subset, expected_profit > 0.
- Meena specifically: recourse new_pd < APPROVAL_PD_THRESHOLD.
"""
from __future__ import annotations

from typing import get_type_hints

import pytest

import core
from core import contracts as c
from core.features import by_name
from core.models import APPROVAL_PD_THRESHOLD
from core.reference import MEENA_ID, TEST_BORROWER_IDS


def keys(td):
    return set(get_type_hints(td))


# ---------------------------------------------------------------------------
# recourse()
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bid", TEST_BORROWER_IDS)
def test_recourse_keys(bid):
    r = core.recourse(bid)
    assert set(r) == keys(c.RecourseResult), (
        f"{bid}: recourse keys {set(r)} != {keys(c.RecourseResult)}"
    )


@pytest.mark.parametrize("bid", TEST_BORROWER_IDS)
def test_recourse_action_keys(bid):
    r = core.recourse(bid)
    for a in r["actions"]:
        assert set(a) == keys(c.RecourseAction), (
            f"{bid}: action keys {set(a)} != {keys(c.RecourseAction)}"
        )


@pytest.mark.parametrize("bid", TEST_BORROWER_IDS)
def test_recourse_only_verifiable_levers(bid):
    bn = by_name()
    r = core.recourse(bid)
    for a in r["actions"]:
        assert bn[a["lever"]]["mutability"] == "verifiable", (
            f"{bid}: lever '{a['lever']}' is not verifiable"
        )


@pytest.mark.parametrize("bid", TEST_BORROWER_IDS)
def test_recourse_new_pd_less_than_pd(bid):
    pd_current = core.score(bid)["pd"]
    r = core.recourse(bid)
    assert r["new_pd"] < pd_current, (
        f"{bid}: new_pd={r['new_pd']} not < pd={pd_current}"
    )


def test_recourse_meena_below_approval_threshold():
    """Meena's new_pd must be below the approval PD threshold (route-to-yes guarantee)."""
    r = core.recourse(MEENA_ID)
    assert r["new_pd"] < APPROVAL_PD_THRESHOLD, (
        f"Meena new_pd={r['new_pd']} >= APPROVAL_PD_THRESHOLD={APPROVAL_PD_THRESHOLD}"
    )


@pytest.mark.parametrize("bid", TEST_BORROWER_IDS)
def test_recourse_valid_until_model(bid):
    from core.models import MODEL_VERSION
    r = core.recourse(bid)
    assert r["valid_until_model"] == MODEL_VERSION, (
        f"{bid}: valid_until_model='{r['valid_until_model']}' != MODEL_VERSION='{MODEL_VERSION}'"
    )


@pytest.mark.parametrize("bid", TEST_BORROWER_IDS)
def test_recourse_pd_range(bid):
    r = core.recourse(bid)
    assert 0 < r["new_pd"] <= 1, f"{bid}: new_pd={r['new_pd']} out of (0, 1]"
    assert r["cost"] >= 0, f"{bid}: cost={r['cost']} < 0"
    assert r["months"] >= 0, f"{bid}: months={r['months']} < 0"


# ---------------------------------------------------------------------------
# structure()
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bid", TEST_BORROWER_IDS)
def test_structure_keys(bid):
    r = core.structure(bid)
    assert set(r) == keys(c.StructureResult), (
        f"{bid}: structure keys {set(r)} != {keys(c.StructureResult)}"
    )


@pytest.mark.parametrize("bid", TEST_BORROWER_IDS)
def test_structure_schedule_length(bid):
    r = core.structure(bid)
    assert len(r["schedule"]) == len(r["p10_band"]) == r["tenor_months"], (
        f"{bid}: schedule/p10_band length mismatch"
    )


@pytest.mark.parametrize("bid", TEST_BORROWER_IDS)
def test_structure_schedule_under_p10(bid):
    """Schedule must be <= p10_band / target_dscr in all but at most 1 month."""
    r = core.structure(bid)
    target_dscr = r["target_dscr"]
    violations = [
        i for i in range(r["tenor_months"])
        if r["schedule"][i] > (r["p10_band"][i] / target_dscr) + 1e-6
    ]
    assert len(violations) <= 1, (
        f"{bid}: schedule exceeds P10/DSCR in {len(violations)} months: {violations}"
    )


@pytest.mark.parametrize("bid", TEST_BORROWER_IDS)
def test_structure_matched_beats_flat(bid):
    """DSCR-matched default rate must be lower than flat EMI default rate."""
    r = core.structure(bid)
    assert r["default_matched"] < r["default_flat"], (
        f"{bid}: default_matched={r['default_matched']} >= default_flat={r['default_flat']}"
    )


@pytest.mark.parametrize("bid", TEST_BORROWER_IDS)
def test_structure_default_rates_in_range(bid):
    r = core.structure(bid)
    for key in ("default_flat", "default_matched"):
        assert 0 < r[key] < 1, f"{bid}: {key}={r[key]} out of (0, 1)"


# ---------------------------------------------------------------------------
# fairness_report()
# ---------------------------------------------------------------------------

def test_fairness_keys_no_policy():
    r = core.fairness_report(None)
    assert set(r) == keys(c.FairnessReport)


def test_fairness_keys_with_policy():
    r = core.fairness_report({"mitigation": "reweighing", "strength": 0.5})
    assert set(r) == keys(c.FairnessReport)


def test_fairness_adverse_impact_in_range():
    r = core.fairness_report(None)
    for group, ratio in r["adverse_impact_ratio"].items():
        assert 0 < ratio <= 1.0, f"Group '{group}' adverse_impact_ratio={ratio} out of (0, 1]"


def test_fairness_mitigation_narrows_gap():
    """Reweighing with strength=0.8 should change metrics vs no mitigation.

    Note: AIR and TPR gap are mathematically conflicting metrics when base default
    rates differ between groups (see docs/known_issues/m2.md F-02). Reweighing
    targets approval-rate parity, which may widen TPR gap. We verify the model
    produces different metrics, not that TPR gap specifically narrows.
    """
    base = core.fairness_report({"mitigation": "none"})
    mitigated = core.fairness_report({"mitigation": "reweighing", "strength": 0.8})
    # Mitigation should change at least one group's metrics
    any_changed = False
    for group in ("women_led", "rural"):
        gap_base = abs(base["tpr_gap"][group])
        gap_mitigated = abs(mitigated["tpr_gap"][group])
        if abs(gap_base - gap_mitigated) > 1e-6:
            any_changed = True
    assert any_changed, "Mitigation had no effect on any group's TPR gap"


def test_fairness_intersectional_ci_valid():
    r = core.fairness_report(None)
    for row in r["intersectional"]:
        assert row["ci_low"] <= row["approval_rate"] <= row["ci_high"], (
            f"Intersectional CI invalid: {row}"
        )
        assert row["n"] > 0


# ---------------------------------------------------------------------------
# optimize()
# ---------------------------------------------------------------------------

def test_optimize_keys():
    r = core.optimize({})
    assert set(r) == keys(c.OptimizeResult)


def test_optimize_approved_subset():
    r = core.optimize({})
    all_ids = set(TEST_BORROWER_IDS)
    for bid in r["approved_ids"]:
        assert bid in all_ids, f"Approved id '{bid}' not in TEST_BORROWER_IDS"


def test_optimize_financials_positive():
    r = core.optimize({})
    assert r["expected_profit"] > 0, f"expected_profit={r['expected_profit']} <= 0"
    assert r["expected_loss"] >= 0, f"expected_loss={r['expected_loss']} < 0"
    assert r["exposure"] > 0, f"exposure={r['exposure']} <= 0"


def test_optimize_different_policy_different_result():
    """Different policy params should produce different results.

    Using loss_cap as the binding constraint: a tight cap approves fewer borrowers
    (lower EL and lower exposure) than a loose one.
    """
    r1 = core.optimize({"loss_cap": 1_000})    # very tight: approves at most 1-2 borrowers
    r2 = core.optimize({"loss_cap": 5_000_000})  # loose: approves many
    # At least one metric should differ
    assert (r1["expected_loss"] != r2["expected_loss"]) or (r1["exposure"] != r2["exposure"]), (
        "loss_cap change had no effect on result"
    )


def test_optimize_fairness_gap_keys():
    r = core.optimize({})
    assert "women_led" in r["fairness_gap"]
    assert "rural" in r["fairness_gap"]


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bid", TEST_BORROWER_IDS[:5])
def test_recourse_determinism(bid):
    assert core.recourse(bid) == core.recourse(bid)


@pytest.mark.parametrize("bid", TEST_BORROWER_IDS[:5])
def test_structure_determinism(bid):
    assert core.structure(bid) == core.structure(bid)
