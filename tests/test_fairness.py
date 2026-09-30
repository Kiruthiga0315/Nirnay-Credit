"""Tests for core/fairness.py (M2).

Contract:
- Metrics on toy example match hand-computed values.
- Bootstrap is seeded.
- small_n flag correctly set for n < 200.
- Wording test (no banned phrases).
"""
import pandas as pd

from core.fairness import _bootstrap_intersectional, _calc_metrics, build_artifacts, fairness_report
from core.paths import ARTIFACTS


def test_calc_metrics_toy_example():
    """Metrics on a hand-built toy example match hand-computed values."""
    # Toy example: 10 borrowers
    # True outcomes (default_12m): 0=Good, 1=Bad
    # Good: 6, Bad: 4
    y_true = pd.Series([0, 0, 0, 0, 0, 0, 1, 1, 1, 1])
    
    # Probabilities
    y_prob = pd.Series([0.05, 0.08, 0.12, 0.09, 0.04, 0.15, 0.20, 0.08, 0.11, 0.02])
    
    # Approved (pd < 0.10)
    # y_prob < 0.10: [True, True, False, True, True, False, False, True, False, True]
    approved = pd.Series([True, True, False, True, True, False, False, True, False, True])
    
    # Mask for our group (let's say all 10 are in the group)
    mask = pd.Series([True] * 10)
    
    metrics = _calc_metrics(
        df=pd.DataFrame({"id": range(10)}),
        y_true=y_true,
        y_prob=y_prob,
        approved=approved,
        mask=mask
    )
    
    # Hand computation:
    # N = 10
    assert metrics["n"] == 10
    
    # Approval rate = 6 / 10 = 0.6
    assert metrics["approval_rate"] == 0.6
    
    # TPR = Approved among non-defaulters (y_true == 0).
    # Good mask (y_true == 0) is first 6.
    # Among first 6, approved are [True, True, False, True, True, False] -> 4 approved out of 6.
    # TPR = 4 / 6 = 0.6667
    assert abs(metrics["tpr"] - 0.6667) < 1e-3


def test_bootstrap_seeded():
    """Bootstrap CI must be reproducible with the same seed."""
    mask = pd.Series([True] * 500)
    approved = pd.Series([True] * 250 + [False] * 250)
    df = pd.DataFrame({"id": range(500)})
    
    res1 = _bootstrap_intersectional(df, approved, mask, "test", b_iterations=100, seed=42)
    res2 = _bootstrap_intersectional(df, approved, mask, "test", b_iterations=100, seed=42)
    
    assert res1["ci_low"] == res2["ci_low"]
    assert res1["ci_high"] == res2["ci_high"]
    assert not res1["small_n"]


def test_bootstrap_small_n_flag():
    """small_n flag is set when n < 200."""
    mask = pd.Series([True] * 150)
    approved = pd.Series([True] * 75 + [False] * 75)
    df = pd.DataFrame({"id": range(150)})
    
    res = _bootstrap_intersectional(df, approved, mask, "test", b_iterations=10, seed=42)
    assert res["small_n"] is True


def test_fairness_report_keys():
    """Check fairness report structure."""
    r = fairness_report({"mitigation": "none"})
    required_keys = {"policy", "by_group", "adverse_impact_ratio", "tpr_gap", "intersectional"}
    assert required_keys.issubset(set(r.keys()))
    
    assert "women_led" in r["adverse_impact_ratio"]
    assert "rural" in r["adverse_impact_ratio"]


def test_no_banned_phrases():
    """Wording test (no banned phrases)."""
    # Build artifacts to generate the metrics file
    build_artifacts(smoke=True)
    
    metrics_path = ARTIFACTS / "metrics" / "fairness.json"
    if metrics_path.exists():
        with open(metrics_path, encoding="utf-8") as f:
            content = f.read().lower()
        
        banned = ["bias-free", "99% accurate", "guaranteed approval", "rbi-compliant"]
        for phrase in banned:
            assert phrase not in content, f"Banned phrase '{phrase}' found in fairness metrics!"

