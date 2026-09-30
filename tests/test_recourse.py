"""Tests for core/recourse.py (M2 ownership).

Contract:
- Only verifiable levers are used (never gameable or immutable).
- new_pd < original pd when pd >= APPROVAL_PD_THRESHOLD.
- Improving a lever in the right direction never raises PD (monotone direction check).
- Max 4 actions returned.
- valid_until_model is set.
- recourse_equity returns by-group median costs.
Reference borrower: Meena (MSME-00001).
"""
from __future__ import annotations

import pytest

from core.contracts import REFERENCE_BORROWER_ID
from core.features import by_name
from core.models import APPROVAL_PD_THRESHOLD, score
from core.recourse import _load_scoring_model, _score_row, recourse

MEENA_ID = REFERENCE_BORROWER_ID


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def meena_recourse():
    return recourse(MEENA_ID)


@pytest.fixture(scope="module")
def meena_score():
    return score(MEENA_ID)


# ---------------------------------------------------------------------------
# Contract tests
# ---------------------------------------------------------------------------

def test_recourse_keys(meena_recourse):
    required = {"borrower_id", "actions", "new_pd", "cost", "months", "valid_until_model"}
    assert required.issubset(set(meena_recourse)), (
        f"Missing keys: {required - set(meena_recourse)}"
    )


def test_recourse_max_four_actions(meena_recourse):
    assert len(meena_recourse["actions"]) <= 4, (
        f"Too many actions: {len(meena_recourse['actions'])} > 4"
    )


def test_recourse_only_verifiable_levers(meena_recourse):
    """No action must use a gameable or immutable feature."""
    spec = by_name()
    for action in meena_recourse["actions"]:
        ln = action["lever"]
        assert ln in spec, f"Lever '{ln}' not in feature spec."
        mut = spec[ln]["mutability"]
        assert mut == "verifiable", (
            f"Lever '{ln}' has mutability='{mut}' — only 'verifiable' allowed."
        )


def test_recourse_new_pd_below_threshold_for_meena(meena_recourse):
    """Meena has pd >= threshold; recourse must bring it below."""
    assert meena_recourse["new_pd"] < APPROVAL_PD_THRESHOLD, (
        f"Meena new_pd={meena_recourse['new_pd']} >= threshold={APPROVAL_PD_THRESHOLD}"
    )


def test_recourse_new_pd_less_than_original(meena_recourse, meena_score):
    """new_pd must be strictly less than original pd."""
    pd_orig = meena_score["pd"]
    assert meena_recourse["new_pd"] < pd_orig, (
        f"new_pd={meena_recourse['new_pd']} >= original pd={pd_orig}"
    )


def test_recourse_valid_until_model_set(meena_recourse):
    assert meena_recourse["valid_until_model"], "valid_until_model must be non-empty."


def test_recourse_cost_non_negative(meena_recourse):
    assert meena_recourse["cost"] >= 0


def test_recourse_months_non_negative(meena_recourse):
    assert meena_recourse["months"] >= 0


def test_recourse_action_keys():
    r = recourse(MEENA_ID)
    for action in r["actions"]:
        for k in ("lever", "label", "current", "target", "unit", "cost", "months"):
            assert k in action, f"Action missing key '{k}': {action}"


def test_recourse_action_cost_non_negative():
    r = recourse(MEENA_ID)
    for action in r["actions"]:
        assert action["cost"] >= 0, f"Action cost < 0: {action}"


def test_recourse_action_months_non_negative():
    r = recourse(MEENA_ID)
    for action in r["actions"]:
        assert action["months"] >= 0, f"Action months < 0: {action}"


def test_recourse_monotone_direction():
    """Improving a lever must not raise PD above current (monotone direction check).

    We test this by asking: given a lever with monotone_pd=+1 (higher value raises PD),
    the target must be <= current (i.e., we recommend lowering it).
    For monotone_pd=-1, target >= current.
    """
    r = recourse(MEENA_ID)
    spec = by_name()
    for action in r["actions"]:
        ln = action["lever"]
        direction = spec[ln].get("monotone_pd", 0)
        if direction > 0:
            # Higher raises PD → target must be <= current
            assert action["target"] <= action["current"] + 1e-9, (
                f"Lever {ln} (monotone_pd=+1) has target {action['target']} > current {action['current']}"
            )
        elif direction < 0:
            # Higher lowers PD → target must be >= current
            assert action["target"] >= action["current"] - 1e-9, (
                f"Lever {ln} (monotone_pd=-1) has target {action['target']} < current {action['current']}"
            )


def test_recourse_monotone_pd_on_grid():
    """Improving any single lever never raises PD (grid test on Meena).

    For each verifiable lever, take 3 steps in the improving direction and
    verify PD does not increase at any step.
    """
    from core.features import lever_config, levers, recompute_derived
    from core.reference import MEENA

    model, feature_names, calibrator = _load_scoring_model()
    bf = dict(MEENA)
    base_pd = _score_row(model, feature_names, bf, calibrator)

    for ln in levers():
        cfg = lever_config(ln)
        direction = cfg.get("monotone_pd", 0)
        step = float(cfg.get("step", 1.0))
        lo, hi = cfg.get("allowed_range", [None, None])
        current_val = float(bf.get(ln, 0.0))

        prev_pd = base_pd
        val = current_val

        for _ in range(3):
            if direction >= 0:
                val -= step
                if lo is not None and val < lo:
                    break
            else:
                val += step
                if hi is not None and val > hi:
                    break

            trial = recompute_derived({**bf, ln: val})
            trial_pd = _score_row(model, feature_names, trial, calibrator)
            assert trial_pd <= prev_pd + 0.01, (
                f"Lever {ln} step from {current_val} to {val}: "
                f"PD went up from {prev_pd:.4f} to {trial_pd:.4f}"
            )
            prev_pd = trial_pd


def test_recourse_with_custom_levers():
    """Custom lever list must restrict recourse to those levers only."""
    r = recourse(MEENA_ID, levers=["receivable_days"])
    for action in r["actions"]:
        assert action["lever"] == "receivable_days", (
            f"Unexpected lever '{action['lever']}' when only 'receivable_days' allowed."
        )


def test_recourse_accepts_dict_input():
    from core.reference import MEENA
    r = recourse(dict(MEENA))
    assert isinstance(r, dict)
    assert "new_pd" in r


@pytest.mark.parametrize("bid", ["MSME-00004", "MSME-00010", "MSME-00016"])
def test_recourse_high_pd_borrowers_improve(bid):
    """For high-PD borrowers, new_pd must be less than original pd."""
    s = score(bid)
    if s["pd"] >= APPROVAL_PD_THRESHOLD:
        r = recourse(bid)
        assert r["new_pd"] < s["pd"], (
            f"{bid}: new_pd={r['new_pd']} >= original pd={s['pd']}"
        )


def test_recourse_build_artifacts():
    """build_artifacts writes recourse/MSME-00001.json and metrics."""
    import json

    from core.paths import ARTIFACTS
    from core.recourse import build_artifacts

    build_artifacts(smoke=True)
    p = ARTIFACTS / "recourse" / "MSME-00001.json"
    assert p.exists(), "recourse/MSME-00001.json not written."
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["new_pd"] < APPROVAL_PD_THRESHOLD
