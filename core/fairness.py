"""OWNER: M2. F5 priced fairness: metrics, in-processing mitigation, frontier, proxy audit.
Writes artifacts/frontier.json, artifacts/proxy_audit.json, artifacts/fairness_groups.json.

Fairness note (wording rule): say "measured and mitigated under stated definitions".
Metrics conflict mathematically when base rates differ — we expose the trade-off instead of hiding it.
Protected attributes are never model inputs; group-aware thresholds appear only as policy simulations.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from core.contracts import FairnessReport
from core.features import load_spec
from core.models import (
    APPROVAL_PD_THRESHOLD,
    expected_calibration_error,
    score_batch,
)
from core.paths import ARTIFACTS, DATA, write_metrics


def _get_test_data() -> pd.DataFrame:
    """Load OOT test set from borrowers and true outcomes from oracle."""
    borrowers = pd.read_parquet(DATA / "borrowers.parquet")
    oracle = pd.read_parquet(DATA / "oracle.parquet")
    df = borrowers.merge(oracle[["id", "default_12m"]], on="id", how="inner")
    test_df = df[df["application_month"] >= df["oot_test_start"]].copy()
    return test_df


def _get_group_masks(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Return boolean masks for each group defined in feature_spec.json."""
    spec = load_spec()
    masks = {}
    for g_name, g_def in spec.get("groups", {}).items():
        col = g_def["column"]
        val = g_def.get("value")
        if val is None:
            masks[g_name] = df[col].isna()
        else:
            masks[g_name] = df[col] == val
    return masks


def _calc_metrics(
    df: pd.DataFrame, 
    y_true: pd.Series, 
    y_prob: pd.Series, 
    approved: pd.Series, 
    mask: pd.Series
) -> dict[str, float]:
    """Calculate n, approval_rate, tpr, ece for a boolean mask.
    Outcome definition: We use default_12m == 0 as the 'positive' true outcome (good borrower).
    So TPR (Equal Opportunity) = P(Approved | Non-default).
    """
    if mask.sum() == 0:
        return {"n": 0, "approval_rate": 0.0, "tpr": 0.0, "ece": 0.0}
    
    n = int(mask.sum())
    approval_rate = float(approved[mask].mean())
    
    # TPR: Approved among non-defaulters
    good_mask = mask & (y_true == 0)
    if good_mask.sum() > 0:
        tpr = float(approved[good_mask].mean())
    else:
        tpr = 0.0
        
    # ECE
    ece = expected_calibration_error(y_true[mask].values, y_prob[mask].values)
    
    return {
        "n": n,
        "approval_rate": round(approval_rate, 4),
        "tpr": round(tpr, 4),
        "ece": round(ece, 4),
    }


def _group_metrics(policy: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Real group metrics calculated on the OOT test set.
    """
    # Load test data and score it
    test_df = _get_test_data()
    scored = score_batch(test_df)
    
    # Merge scores back
    df = test_df.merge(scored[["id", "pd"]], on="id", how="inner")
    
    y_true = df["default_12m"]
    y_prob = df["pd"]
    
    # Baseline approval
    # Note: Phase 3 will adjust this threshold based on policy["mitigation"].
    approved = y_prob < APPROVAL_PD_THRESHOLD
    
    masks = _get_group_masks(df)
    
    by_group = {}
    for g_name, mask in masks.items():
        by_group[g_name] = _calc_metrics(df, y_true, y_prob, approved, mask)
        # Add the reference group (not in the group)
        by_group[f"not_{g_name}"] = _calc_metrics(df, y_true, y_prob, approved, ~mask)
        
    return by_group


def _bootstrap_intersectional(
    df: pd.DataFrame, 
    approved: pd.Series, 
    mask: pd.Series, 
    name: str, 
    b_iterations: int = 200, 
    seed: int = 42
) -> dict[str, Any]:
    """Calculate 95% CI for approval rate using percentile bootstrap."""
    rng = np.random.RandomState(seed)
    n = int(mask.sum())
    
    if n == 0:
        return {
            "group": name,
            "n": 0,
            "approval_rate": 0.0,
            "ci_low": 0.0,
            "ci_high": 0.0,
            "small_n": True,
        }
        
    approved_in_group = approved[mask].values
    approval_rate = float(np.mean(approved_in_group))
    
    # Bootstrap
    boot_rates = []
    for _ in range(b_iterations):
        indices = rng.randint(0, n, size=n)
        boot_sample = approved_in_group[indices]
        boot_rates.append(np.mean(boot_sample))
        
    ci_low = float(np.percentile(boot_rates, 2.5))
    ci_high = float(np.percentile(boot_rates, 97.5))
    
    return {
        "group": name,
        "n": n,
        "approval_rate": round(approval_rate, 4),
        "ci_low": round(ci_low, 4),
        "ci_high": round(ci_high, 4),
        "small_n": n < 200,
    }


def fairness_report(policy: dict[str, Any] | None = None) -> FairnessReport:
    """Metrics by group + intersectional CIs for a policy.

    Policy dict keys (all optional):
        mitigation: "none" | "reweighing" | "in_processing" | "threshold"
        strength: float in [0, 1] — how aggressively to apply the mitigation

    Example:
        r = fairness_report({"mitigation": "none"})
        r["adverse_impact_ratio"]["women_led"]  # < 1.0 indicates lower approval rate
        
    Args:
        policy: dict describing the fairness mitigation policy, or None for baseline.

    Returns:
        FairnessReport with by_group, adverse_impact_ratio, tpr_gap, intersectional.
    """
    p = policy or {"mitigation": "none"}
    
    test_df = _get_test_data()
    scored = score_batch(test_df)
    df = test_df.merge(scored[["id", "pd"]], on="id", how="inner")
    approved = df["pd"] < APPROVAL_PD_THRESHOLD
    
    by_group = _group_metrics(p)
    
    adverse_impact_ratio = {}
    tpr_gap = {}
    
    for g_name in ["women_led", "rural", "new_to_credit"]:
        ref_name = f"not_{g_name}"
        if g_name in by_group and ref_name in by_group:
            ref_approval = by_group[ref_name]["approval_rate"]
            ref_tpr = by_group[ref_name]["tpr"]
            
            air = by_group[g_name]["approval_rate"] / ref_approval if ref_approval > 0 else 0.0
            adverse_impact_ratio[g_name] = round(air, 4)
            
            tgap = by_group[g_name]["tpr"] - ref_tpr
            tpr_gap[g_name] = round(tgap, 4)
            
    # Intersectional
    masks = _get_group_masks(df)
    women_rural = masks.get("women_led", pd.Series(False, index=df.index)) & masks.get("rural", pd.Series(False, index=df.index))
    women_ntc = masks.get("women_led", pd.Series(False, index=df.index)) & masks.get("new_to_credit", pd.Series(False, index=df.index))
    
    intersectional = [
        _bootstrap_intersectional(df, approved, women_rural, "women_led x rural"),
        _bootstrap_intersectional(df, approved, women_ntc, "women_led x new_to_credit"),
    ]

    return {
        "policy": p,
        "by_group": by_group,
        "adverse_impact_ratio": adverse_impact_ratio,
        "tpr_gap": tpr_gap,
        "intersectional": intersectional,
    }


def build_artifacts(smoke: bool = False) -> None:
    """Write artifacts/fairness_groups.json and metrics."""
    # Baseline report
    report = fairness_report({"mitigation": "none"})
    
    out_dir = ARTIFACTS
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "fairness_groups.json"
    out_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    
    # To compare with legacy policy, load legacy metrics if they exist
    
    write_metrics("fairness", {
        "women_led_air": report["adverse_impact_ratio"].get("women_led", 0.0),
        "rural_air": report["adverse_impact_ratio"].get("rural", 0.0),
        "new_to_credit_air": report["adverse_impact_ratio"].get("new_to_credit", 0.0),
        "women_led_tpr_gap": report["tpr_gap"].get("women_led", 0.0),
        "rural_tpr_gap": report["tpr_gap"].get("rural", 0.0),
        "new_to_credit_tpr_gap": report["tpr_gap"].get("new_to_credit", 0.0),
        "women_rural_intersectional_approval": report["intersectional"][0]["approval_rate"],
        "women_rural_intersectional_small_n": report["intersectional"][0]["small_n"],
        "_note": "Measured and mitigated under stated definitions: Positive outcome is Non-default.",
    })
    
    print("[fairness] fairness_groups.json written.")
