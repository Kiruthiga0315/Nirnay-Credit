"""Tests for core/explain.py (M2 ownership).

Contract: reasons_for() returns Reason objects sorted by impact desc; no protected
attributes appear in reasons; all features referenced are model_input=True.
Reference borrower: Meena (MSME-00001).
"""
from __future__ import annotations

import re

import pytest

from core.contracts import REFERENCE_BORROWER_ID
from core.explain import reasons_for
from core.features import by_name

MEENA_ID = REFERENCE_BORROWER_ID
_PROTECTED = {"owner_gender", "location_class"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def meena_reasons():
    return reasons_for(MEENA_ID, k=3)


# ---------------------------------------------------------------------------
# Contract tests
# ---------------------------------------------------------------------------

def test_reasons_returns_list(meena_reasons):
    assert isinstance(meena_reasons, list)


def test_reasons_length_le_k(meena_reasons):
    assert len(meena_reasons) <= 3


def test_reasons_each_has_required_keys(meena_reasons):
    for r in meena_reasons:
        assert "feature" in r, f"Missing 'feature' key in {r}"
        assert "text" in r, f"Missing 'text' key in {r}"
        assert "impact" in r, f"Missing 'impact' key in {r}"


def test_reasons_no_protected_attributes(meena_reasons):
    """Protected attributes (owner_gender, location_class) must never appear as reasons."""
    for r in meena_reasons:
        assert r["feature"] not in _PROTECTED, (
            f"Protected attribute '{r['feature']}' appeared in reasons — this violates rule 10."
        )


def test_reasons_only_model_input_features(meena_reasons):
    """Only features with model_input=True should appear in reasons."""
    spec = by_name()
    for r in meena_reasons:
        fname = r["feature"]
        if fname in spec:
            assert spec[fname].get("model_input", True), (
                f"Feature '{fname}' has model_input=False but appears in reasons."
            )


def test_reasons_sorted_by_impact_descending(meena_reasons):
    impacts = [r["impact"] for r in meena_reasons]
    assert impacts == sorted(impacts, reverse=True), (
        f"Reasons not sorted by impact desc: {impacts}"
    )


def test_reasons_text_is_non_empty(meena_reasons):
    for r in meena_reasons:
        assert isinstance(r["text"], str) and len(r["text"]) > 0, (
            f"Reason text is empty for feature '{r['feature']}'."
        )


def test_reasons_for_different_borrowers_valid():
    """Both Meena and another borrower must return valid non-empty reason lists."""
    r1 = reasons_for(MEENA_ID, k=3)
    r2 = reasons_for("MSME-00005", k=3)
    assert len(r1) > 0
    assert len(r2) > 0


def test_reasons_for_dict_input():
    """reasons_for() must accept a plain dict with borrower fields."""
    row = {"id": MEENA_ID, "receivable_days": 90.0, "cheque_bounces_6m": 2}
    reasons = reasons_for(row, k=2)
    assert isinstance(reasons, list)
    assert len(reasons) <= 2


def test_reasons_impact_is_float(meena_reasons):
    for r in meena_reasons:
        assert isinstance(r["impact"], float), (
            f"Impact must be float, got {type(r['impact'])} for {r['feature']}."
        )


def test_no_banned_wording_in_reasons(meena_reasons):
    """Reason text must not contain banned phrases."""
    banned = re.compile(r"bias-free|99% accurate|guaranteed approval|RBI-compliant", re.I)
    for r in meena_reasons:
        assert not banned.search(r["text"]), (
            f"Banned wording in reason text for '{r['feature']}': {r['text']}"
        )
