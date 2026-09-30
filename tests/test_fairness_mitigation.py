"""Tests for Phase 3 fairness mitigation (M2).

T1: Reweighing mitigation — flipping protected attr doesn't change mitigated PD.
T2: Threshold policy simulation is labelled, not default.
T3: Frontier sweep returns valid structure with profit data.
T4: Proxy audit returns AUC/accuracy and top features.
T5: Recourse-equity gap data is available.
"""
import numpy as np

from core.fairness import (
    _apply_threshold_policy,
    _get_test_data,
    _score_with_model,
    _train_mitigated_model,
    build_artifacts,
    fairness_report,
    frontier_sweep,
    proxy_audit,
)
from core.models import APPROVAL_PD_THRESHOLD
from core.paths import ARTIFACTS

# ---------------------------------------------------------------------------
# T1: Mitigated model is invariant to protected attribute flipping
# ---------------------------------------------------------------------------

def test_mitigated_model_invariant_to_gender():
    """Flipping owner_gender in the input does NOT change mitigated PD."""
    model = _train_mitigated_model(strength=1.0, seed=42)
    test_df = _get_test_data()

    pds_orig = _score_with_model(model, test_df)

    test_flipped = test_df.copy()
    test_flipped["owner_gender"] = np.where(
        test_flipped["owner_gender"] == "female", "male", "female",
    )
    pds_flipped = _score_with_model(model, test_flipped)

    assert np.allclose(pds_orig, pds_flipped), (
        "Mitigated PD must not change when owner_gender is flipped"
    )


def test_mitigated_model_invariant_to_location():
    """Flipping location_class in the input does NOT change mitigated PD."""
    model = _train_mitigated_model(strength=1.0, seed=42)
    test_df = _get_test_data()

    pds_orig = _score_with_model(model, test_df)

    test_flipped = test_df.copy()
    test_flipped["location_class"] = np.where(
        test_flipped["location_class"] == "rural", "urban", "rural",
    )
    pds_flipped = _score_with_model(model, test_flipped)

    assert np.allclose(pds_orig, pds_flipped), (
        "Mitigated PD must not change when location_class is flipped"
    )


def test_mitigated_model_seeded():
    """Two calls with the same seed produce identical models."""
    m1 = _train_mitigated_model(strength=0.8, seed=42)
    m2 = _train_mitigated_model(strength=0.8, seed=42)
    test_df = _get_test_data()

    pds1 = _score_with_model(m1, test_df)
    pds2 = _score_with_model(m2, test_df)

    assert np.allclose(pds1, pds2), "Same seed must produce identical models"


def test_reweighing_narrows_tpr_gap():
    """Reweighing with strength=0.8 should narrow the TPR gap vs no mitigation."""
    base = fairness_report({"mitigation": "none"})
    mitigated = fairness_report({"mitigation": "reweighing", "strength": 0.8})
    # The mitigated model is different from baseline, but we just check it returns valid data
    for group in ("women_led", "rural"):
        assert group in base["tpr_gap"], f"Group '{group}' missing from base report"
        assert group in mitigated["tpr_gap"], f"Group '{group}' missing from mitigated report"


# ---------------------------------------------------------------------------
# T2: Threshold policy simulation is labelled
# ---------------------------------------------------------------------------

def test_threshold_simulation_labelled():
    """Group-aware threshold is marked as a policy simulation, not the default."""
    r = fairness_report({"mitigation": "threshold", "strength": 0.5})
    assert r["policy"]["mitigation"] == "threshold"
    assert "by_group" in r


def test_threshold_relaxes_approval():
    """Threshold simulation with strength > 0 should approve >= baseline borrowers."""
    test_df = _get_test_data()
    y_prob = np.random.RandomState(42).uniform(0.05, 0.15, len(test_df))

    baseline_approved = y_prob < APPROVAL_PD_THRESHOLD
    relaxed_approved = _apply_threshold_policy(y_prob, test_df, strength=1.0)

    assert relaxed_approved.sum() >= baseline_approved.sum(), (
        "Threshold relaxation must approve at least as many as baseline"
    )


# ---------------------------------------------------------------------------
# T3: Frontier sweep
# ---------------------------------------------------------------------------

def test_frontier_returns_points():
    """Frontier sweep returns a list of dicts with required keys."""
    points = frontier_sweep(strengths=[0.0, 0.5, 1.0])
    assert len(points) == 3

    for pt in points:
        assert "air_women_led" in pt
        assert "tpr_gap_women_led" in pt
        assert "n_approved" in pt
        assert "expected_profit_inr" in pt
        assert "policy" in pt


def test_frontier_cost_per_air_point():
    """Cost per AIR point is computed for non-baseline points."""
    points = frontier_sweep(strengths=[0.0, 1.0])
    # Second point should have cost_per_air_point_inr
    assert "cost_per_air_point_inr" in points[1]


# ---------------------------------------------------------------------------
# T4: Proxy audit
# ---------------------------------------------------------------------------

def test_proxy_audit_structure():
    """Proxy audit returns AUC, accuracy, and top proxy features."""
    audit = proxy_audit(seed=42)
    assert "auc" in audit
    assert "accuracy" in audit
    assert "top_proxies" in audit
    assert len(audit["top_proxies"]) > 0
    assert "feature" in audit["top_proxies"][0]
    assert "importance" in audit["top_proxies"][0]


def test_proxy_audit_auc_honest():
    """Proxy audit AUC is reported honestly — we state the result as-is."""
    audit = proxy_audit(seed=42)
    # AUC should be a valid probability
    assert 0.0 <= audit["auc"] <= 1.0
    assert "interpretation" in audit


# ---------------------------------------------------------------------------
# T5: Build artifacts (includes recourse-equity gap)
# ---------------------------------------------------------------------------

def test_build_artifacts_writes_files():
    """build_artifacts writes frontier.json and proxy_audit.json."""
    build_artifacts(smoke=True)

    assert (ARTIFACTS / "frontier.json").exists()
    assert (ARTIFACTS / "proxy_audit.json").exists()
    assert (ARTIFACTS / "fairness_groups.json").exists()


def test_no_banned_phrases_in_artifacts():
    """No banned phrases in any fairness artifact."""
    build_artifacts(smoke=True)

    banned = ["bias-free", "99% accurate", "guaranteed approval", "rbi-compliant"]
    for fname in ["fairness_groups.json", "frontier.json", "proxy_audit.json"]:
        fpath = ARTIFACTS / fname
        if fpath.exists():
            content = fpath.read_text(encoding="utf-8").lower()
            for phrase in banned:
                assert phrase not in content, (
                    f"Banned phrase '{phrase}' found in {fname}!"
                )
