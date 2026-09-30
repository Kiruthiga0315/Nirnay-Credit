"""Tests for core.legacy_policy — T4/T6 test suite."""
import pandas as pd
import pytest

from core.generator import build_artifacts as gen_build
from core.legacy_policy import build_artifacts as legacy_build
from core.paths import DATA


@pytest.fixture(scope="module", autouse=True)
def _generate_and_apply_policy():
    """Run generator then legacy policy once for all tests."""
    gen_build(smoke=True, kappa="medium", bias_strength="medium")
    legacy_build(smoke=True)


def test_observed_outcomes_exist():
    """observed_outcomes.parquet is written."""
    assert (DATA / "observed_outcomes.parquet").exists()


def test_legacy_decisions_exist():
    """legacy_decisions.parquet is written."""
    assert (DATA / "legacy_decisions.parquet").exists()


def test_observed_only_for_approved():
    """Outcomes are observed ONLY for approved firms."""
    decisions = pd.read_parquet(DATA / "legacy_decisions.parquet")
    observed = pd.read_parquet(DATA / "observed_outcomes.parquet")

    approved_ids = set(decisions[decisions["legacy_approved"] == 1]["id"])
    observed_ids = set(observed["id"])

    # Every observed id must be approved
    assert observed_ids.issubset(approved_ids), (
        f"Observed outcomes for non-approved firms: {observed_ids - approved_ids}"
    )
    # All approved ids should have observed outcomes
    assert approved_ids == observed_ids, (
        "Missing observed outcomes for approved firms"
    )


def test_override_share_in_range():
    """Override share is 0.05-0.10."""
    decisions = pd.read_parquet(DATA / "legacy_decisions.parquet")
    override_share = decisions["override"].mean()
    assert 0.05 <= override_share <= 0.10, (
        f"Override share {override_share:.3f} outside [0.05, 0.10]"
    )


def test_approvals_below_cutoff_exist():
    """Some firms below the cutoff are approved (manual overrides/exceptions)."""
    decisions = pd.read_parquet(DATA / "legacy_decisions.parquet")
    cutoff = decisions["legacy_cutoff"].iloc[0]

    below_cutoff_approved = decisions[
        (decisions["legacy_score"] <= cutoff) & (decisions["legacy_approved"] == 1)
    ]
    assert len(below_cutoff_approved) > 0, (
        "No approvals below cutoff — reject inference is not identifiable"
    )


def test_rejections_above_cutoff_exist():
    """Some firms above the cutoff are rejected (manual holds)."""
    decisions = pd.read_parquet(DATA / "legacy_decisions.parquet")
    cutoff = decisions["legacy_cutoff"].iloc[0]

    above_cutoff_rejected = decisions[
        (decisions["legacy_score"] > cutoff) & (decisions["legacy_approved"] == 0)
    ]
    assert len(above_cutoff_rejected) > 0, (
        "No rejections above cutoff"
    )


def test_stochastic_scores_have_variance():
    """Legacy scores are not deterministic — they include noise."""
    decisions = pd.read_parquet(DATA / "legacy_decisions.parquet")
    score_std = decisions["legacy_score"].std()
    assert score_std > 0.05, f"Score std {score_std:.4f} too low — likely missing noise"


def test_approval_rate_sensible():
    """Overall approval rate is in a sensible range (50-80%)."""
    decisions = pd.read_parquet(DATA / "legacy_decisions.parquet")
    approval_rate = decisions["legacy_approved"].mean()
    assert 0.50 <= approval_rate <= 0.80, (
        f"Approval rate {approval_rate:.3f} outside [0.50, 0.80]"
    )


def test_thin_file_lower_approval():
    """Firms without bureau scores should have lower approval rates."""
    borrowers = pd.read_parquet(DATA / "borrowers.parquet")
    decisions = pd.read_parquet(DATA / "legacy_decisions.parquet")

    merged = borrowers[["id", "bureau_score"]].merge(decisions[["id", "legacy_approved"]], on="id")
    has_bureau = merged["bureau_score"].notna()

    approval_with_bureau = merged.loc[has_bureau, "legacy_approved"].mean()
    approval_without_bureau = merged.loc[~has_bureau, "legacy_approved"].mean()

    assert approval_with_bureau > approval_without_bureau, (
        f"Approval with bureau ({approval_with_bureau:.3f}) "
        f"not > without ({approval_without_bureau:.3f})"
    )


def test_meena_in_decisions():
    """Meena (MSME-00001) appears in legacy decisions."""
    decisions = pd.read_parquet(DATA / "legacy_decisions.parquet")
    assert "MSME-00001" in decisions["id"].values
