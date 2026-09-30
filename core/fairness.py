"""OWNER: M2. F5 priced fairness: metrics, in-processing mitigation, frontier, proxy audit.
Writes artifacts/frontier.json, artifacts/proxy_audit.json, artifacts/fairness_groups.json.

Fairness note (wording rule): say "measured and mitigated under stated definitions".
Metrics conflict mathematically when base rates differ — we expose the trade-off instead of hiding it.
Protected attributes are never model inputs; group-aware thresholds appear only as policy simulations.
"""
from __future__ import annotations

import json
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from core.contracts import FairnessReport
from core.features import by_name, load_spec, model_features
from core.models import (
    APPROVAL_PD_THRESHOLD,
    compute_expected_profit,
    expected_calibration_error,
    score_batch,
)
from core.paths import ARTIFACTS, DATA, write_metrics

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _get_all_data() -> pd.DataFrame:
    """Load all borrowers with true outcomes from oracle."""
    borrowers = pd.read_parquet(DATA / "borrowers.parquet")
    oracle = pd.read_parquet(DATA / "oracle.parquet")
    return borrowers.merge(oracle[["id", "default_12m"]], on="id", how="inner")


def _get_test_data() -> pd.DataFrame:
    """Load OOT test set from borrowers and true outcomes from oracle."""
    df = _get_all_data()
    return df[df["application_month"] >= df["oot_test_start"]].copy()


def _get_train_data() -> pd.DataFrame:
    """Load training set (application_month < oot_test_start) with outcomes."""
    df = _get_all_data()
    return df[df["application_month"] < df["oot_test_start"]].copy()


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


def _prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare feature matrix for LightGBM using model_features() from feature_spec.
    Same pipeline as core.models.score_batch — no protected attributes.
    """
    features = model_features()
    spec = by_name()
    X = df[features].copy()
    for f in features:
        if spec[f].get("type") == "cat":
            cats = spec[f].get("categories", [])
            X[f] = pd.Categorical(X[f], categories=cats)
        else:
            X[f] = pd.to_numeric(X[f], errors="coerce")
    return X


# ---------------------------------------------------------------------------
# T1: Mitigation via sample-reweighing (no protected attr at inference)
# ---------------------------------------------------------------------------

def _compute_reweighing_weights(
    y: np.ndarray,
    sensitive: np.ndarray,
    seed: int = 42,
) -> np.ndarray:
    """Compute sample weights to equalise P(Y|A) across groups.

    Standard reweighing (Kamiran & Calders 2012): for each (y, a) cell,
    weight = P(Y=y) * P(A=a) / P(Y=y, A=a).

    The protected attribute is used HERE (training only), never at predict time.
    """
    n = len(y)
    groups = np.unique(sensitive)
    labels = np.unique(y)
    weights = np.ones(n, dtype=float)

    for g in groups:
        g_mask = sensitive == g
        p_a = g_mask.sum() / n
        for lab in labels:
            l_mask = y == lab
            p_y = l_mask.sum() / n
            cell_mask = g_mask & l_mask
            p_ya = cell_mask.sum() / n
            if p_ya > 0:
                w = (p_y * p_a) / p_ya
                weights[cell_mask] = w

    # Normalise so mean weight == 1
    weights /= weights.mean()
    return weights


def _train_mitigated_model(
    strength: float = 1.0,
    group_col: str = "owner_gender",
    seed: int = 42,
) -> lgb.LGBMClassifier:
    """Train a LightGBM with reweighing-based mitigation.

    The protected attribute (group_col) is used ONLY to compute sample weights.
    The model itself is trained on the SAME model_features() as the production model.
    Flipping the protected attribute does NOT change predictions.

    Args:
        strength: 0.0 = no mitigation (uniform weights), 1.0 = full reweighing.
        group_col: protected attribute column for reweighing.
        seed: random seed.

    Returns:
        Trained LGBMClassifier.
    """
    train_df = _get_train_data()
    X_train = _prepare_features(train_df)
    y_train = train_df["default_12m"].values
    sensitive = train_df[group_col].fillna("unknown").values

    # Compute reweighing weights
    rw_weights = _compute_reweighing_weights(y_train, sensitive, seed=seed)

    # Blend: (1 - strength) * uniform + strength * reweighing
    uniform = np.ones_like(rw_weights)
    final_weights = (1.0 - strength) * uniform + strength * rw_weights

    # Monotone constraints from feature_spec
    features = model_features()
    spec = by_name()
    constraints = []
    for f in features:
        mono = spec[f].get("monotone_pd", 0)
        constraints.append(int(mono))

    model = lgb.LGBMClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        monotone_constraints=constraints,
        random_state=seed,
        verbose=-1,
    )
    model.fit(X_train, y_train, sample_weight=final_weights)
    return model


def _score_with_model(
    model: lgb.LGBMClassifier,
    df: pd.DataFrame,
) -> np.ndarray:
    """Score borrowers with a given model. Same feature pipeline, no protected attrs."""
    X = _prepare_features(df)
    return model.predict_proba(X)[:, 1]


# ---------------------------------------------------------------------------
# T2: Group-aware threshold simulation (labelled policy simulation ONLY)
# ---------------------------------------------------------------------------

def _apply_threshold_policy(
    y_prob: np.ndarray,
    df: pd.DataFrame,
    strength: float = 0.5,
) -> np.ndarray:
    """Regulator-mandated inclusion policy simulation (NEVER the default path).

    Lowers approval threshold for disadvantaged groups proportional to strength.
    This is a labelled policy simulation, not a recommendation.
    """
    masks = _get_group_masks(df)
    base_threshold = APPROVAL_PD_THRESHOLD
    approved = y_prob < base_threshold

    # Relaxed threshold for protected groups (simulation only)
    relaxation = 0.03 * strength  # up to 3pp relaxation
    for g_name in ["women_led", "rural", "new_to_credit"]:
        if g_name in masks:
            group_threshold = base_threshold + relaxation
            mask_arr = np.asarray(masks[g_name])
            group_approved = y_prob[mask_arr] < group_threshold
            approved_arr = approved.copy()
            approved_arr[mask_arr] = group_approved
            approved = approved_arr

    return approved


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def _calc_metrics(
    df: pd.DataFrame,
    y_true: pd.Series,
    y_prob: pd.Series,
    approved: pd.Series,
    mask: pd.Series,
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
    """Group metrics on the OOT test set, optionally with mitigation."""
    test_df = _get_test_data()

    mitigation = policy.get("mitigation", "none")
    strength = float(policy.get("strength", 0.0))

    if mitigation in ("reweighing",) and strength > 0:
        # Train a mitigated model and score with it
        model = _train_mitigated_model(strength=strength, seed=42)
        y_prob_arr = _score_with_model(model, test_df)
        y_prob = pd.Series(y_prob_arr, index=test_df.index)
        approved = pd.Series(y_prob_arr < APPROVAL_PD_THRESHOLD, index=test_df.index)
    elif mitigation == "threshold" and strength > 0:
        # Use baseline model but apply group-aware threshold simulation
        scored = score_batch(test_df)
        df_scored = test_df.merge(scored[["id", "pd"]], on="id", how="inner")
        y_prob = df_scored["pd"]
        approved_arr = _apply_threshold_policy(
            y_prob.values, df_scored, strength=strength,
        )
        approved = pd.Series(approved_arr, index=df_scored.index)
        test_df = df_scored
    else:
        # Baseline: production model
        scored = score_batch(test_df)
        df_scored = test_df.merge(scored[["id", "pd"]], on="id", how="inner")
        y_prob = df_scored["pd"]
        approved = pd.Series((y_prob < APPROVAL_PD_THRESHOLD).values, index=df_scored.index)
        test_df = df_scored

    y_true = test_df["default_12m"]
    masks = _get_group_masks(test_df)

    by_group = {}
    for g_name, mask in masks.items():
        by_group[g_name] = _calc_metrics(test_df, y_true, y_prob, approved, mask)
        by_group[f"not_{g_name}"] = _calc_metrics(test_df, y_true, y_prob, approved, ~mask)

    return by_group


def _bootstrap_intersectional(
    df: pd.DataFrame,
    approved: pd.Series,
    mask: pd.Series,
    name: str,
    b_iterations: int = 200,
    seed: int = 42,
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


# ---------------------------------------------------------------------------
# T3: Frontier sweep — fairness gap vs expected profit
# ---------------------------------------------------------------------------

_DEFAULT_LGD = 0.45
_DEFAULT_MARGIN = 0.10
_DEFAULT_TICKET = 500_000


def _frontier_point(
    policy: dict[str, Any],
    lgd: float = _DEFAULT_LGD,
    margin: float = _DEFAULT_MARGIN,
    ticket: float = _DEFAULT_TICKET,
) -> dict[str, Any]:
    """Compute one frontier point: fairness gaps + expected profit for a policy."""
    test_df = _get_test_data()
    mitigation = policy.get("mitigation", "none")
    strength = float(policy.get("strength", 0.0))

    if mitigation == "reweighing" and strength > 0:
        model = _train_mitigated_model(strength=strength, seed=42)
        y_prob = _score_with_model(model, test_df)
        approved = y_prob < APPROVAL_PD_THRESHOLD
    elif mitigation == "threshold" and strength > 0:
        scored = score_batch(test_df)
        df_merged = test_df.merge(scored[["id", "pd"]], on="id", how="inner")
        y_prob = df_merged["pd"].values
        approved = _apply_threshold_policy(y_prob, df_merged, strength=strength)
        test_df = df_merged
    else:
        scored = score_batch(test_df)
        df_merged = test_df.merge(scored[["id", "pd"]], on="id", how="inner")
        y_prob = df_merged["pd"].values
        approved = y_prob < APPROVAL_PD_THRESHOLD
        test_df = df_merged

    y_true = test_df["default_12m"].values
    masks = _get_group_masks(test_df)

    # AIR and TPR gap for women_led
    w_mask = masks.get("women_led", pd.Series(False, index=test_df.index)).values
    ref_mask = ~w_mask

    app_w = np.mean(approved[w_mask]) if w_mask.sum() > 0 else 0.0
    app_ref = np.mean(approved[ref_mask]) if ref_mask.sum() > 0 else 0.0
    air = app_w / app_ref if app_ref > 0 else 0.0

    good_w = w_mask & (y_true == 0)
    good_ref = ref_mask & (y_true == 0)
    tpr_w = np.mean(approved[good_w]) if good_w.sum() > 0 else 0.0
    tpr_ref = np.mean(approved[good_ref]) if good_ref.sum() > 0 else 0.0
    tpr_gap = tpr_w - tpr_ref

    # Expected profit
    profit = compute_expected_profit(y_prob, y_true, APPROVAL_PD_THRESHOLD, lgd, margin, ticket)
    n_approved = int(np.sum(approved))

    return {
        "policy": policy,
        "air_women_led": round(air, 4),
        "tpr_gap_women_led": round(tpr_gap, 4),
        "n_approved": n_approved,
        "expected_profit_inr": round(profit, 0),
        "lgd": lgd,
        "margin": margin,
        "ticket_inr": ticket,
    }


def frontier_sweep(
    strengths: list[float] | None = None,
    lgd: float = _DEFAULT_LGD,
    margin: float = _DEFAULT_MARGIN,
    ticket: float = _DEFAULT_TICKET,
) -> list[dict[str, Any]]:
    """Sweep mitigation strength and compute frontier points.

    Returns list of dicts, each with fairness metrics and profit.
    """
    if strengths is None:
        strengths = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

    points = []
    for s in strengths:
        policy = {"mitigation": "none" if s == 0 else "reweighing", "strength": s}
        pt = _frontier_point(policy, lgd=lgd, margin=margin, ticket=ticket)
        points.append(pt)

    # Compute price of closing the gap (INR per point of AIR improvement)
    if len(points) >= 2:
        base = points[0]
        for pt in points[1:]:
            air_improvement = pt["air_women_led"] - base["air_women_led"]
            profit_loss = base["expected_profit_inr"] - pt["expected_profit_inr"]
            if abs(air_improvement) > 1e-6:
                pt["cost_per_air_point_inr"] = round(profit_loss / air_improvement, 0)
            else:
                pt["cost_per_air_point_inr"] = 0.0

    return points


# ---------------------------------------------------------------------------
# T4: Proxy audit — can we predict protected attr from neutral features?
# ---------------------------------------------------------------------------

def proxy_audit(seed: int = 42) -> dict[str, Any]:
    """Train a model to predict owner_gender from neutral model features.

    A high AUC means the model features leak demographic information (proxies).
    Result is stated honestly: "a high score means proxies leak".
    """
    df = _get_all_data()
    X = _prepare_features(df)
    # Binary target: women_led (female) vs others
    y = (df["owner_gender"] == "female").astype(int).values

    from sklearn.model_selection import train_test_split

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.3, random_state=seed, stratify=y,
    )

    proxy_model = lgb.LGBMClassifier(
        n_estimators=50, max_depth=3, random_state=seed, verbose=-1,
    )
    proxy_model.fit(X_tr, y_tr)

    y_pred = proxy_model.predict_proba(X_te)[:, 1]
    accuracy = float(np.mean((y_pred >= 0.5) == y_te))
    auc = float(roc_auc_score(y_te, y_pred))

    # Top proxy features
    importances = proxy_model.feature_importances_
    feature_names = model_features()
    top_idx = np.argsort(importances)[::-1][:5]
    top_proxies = [
        {"feature": feature_names[i], "importance": int(importances[i])}
        for i in top_idx
    ]

    return {
        "target": "owner_gender == female",
        "accuracy": round(accuracy, 4),
        "auc": round(auc, 4),
        "top_proxies": top_proxies,
        "interpretation": (
            "AUC close to 0.5 means model features carry little demographic signal. "
            "AUC above 0.7 means proxies leak — consider feature removal or regularisation."
        ),
        "_note": "Under our documented assumptions: stated honestly, not a compliance claim.",
    }


# ---------------------------------------------------------------------------
# T5: Recourse-equity gap integration
# ---------------------------------------------------------------------------

def _recourse_equity_gap() -> dict[str, Any]:
    """Compute recourse-equity data: median cost-to-approve by group.

    Uses core.recourse.recourse_equity() for gender and location groups.
    Returns dict with gender_equity and location_equity keys.
    """
    from core.recourse import recourse_equity

    gender_eq = recourse_equity("owner_gender")
    location_eq = recourse_equity("location_class")

    return {
        "gender_equity": gender_eq,
        "location_equity": location_eq,
    }


# ---------------------------------------------------------------------------
# Public API: fairness_report (contract: FairnessReport)
# ---------------------------------------------------------------------------

def fairness_report(policy: dict[str, Any] | None = None) -> FairnessReport:
    """Metrics by group + intersectional CIs for a policy.

    Policy dict keys (all optional):
        mitigation: "none" | "reweighing" | "threshold"
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


# ---------------------------------------------------------------------------
# Build artifacts
# ---------------------------------------------------------------------------

def build_artifacts(smoke: bool = False) -> None:
    """Write artifacts/fairness_groups.json, frontier.json, proxy_audit.json and metrics."""
    # 1. Baseline fairness report
    report = fairness_report({"mitigation": "none"})

    out_dir = ARTIFACTS
    out_dir.mkdir(parents=True, exist_ok=True)

    # 2. Frontier sweep (6 points)
    frontier = frontier_sweep(strengths=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0])

    frontier_path = out_dir / "frontier.json"
    frontier_path.write_text(json.dumps(frontier, indent=2, default=str), encoding="utf-8")

    # 3. Proxy audit
    audit = proxy_audit()
    audit_path = out_dir / "proxy_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")

    # 4. Recourse-equity gap
    equity = _recourse_equity_gap()

    # 5. Extend fairness_groups.json with all data
    fairness_data = {**report}
    fairness_data["recourse_equity"] = equity
    fairness_data["proxy_audit_summary"] = {
        "auc": audit["auc"],
        "accuracy": audit["accuracy"],
        "top_proxy": audit["top_proxies"][0]["feature"] if audit["top_proxies"] else "none",
    }

    groups_path = out_dir / "fairness_groups.json"
    groups_path.write_text(json.dumps(fairness_data, indent=2, default=str), encoding="utf-8")

    # 6. Cost-of-fairness sentence
    if len(frontier) >= 2:
        base_profit = frontier[0]["expected_profit_inr"]
        full_profit = frontier[-1]["expected_profit_inr"]
        cost = base_profit - full_profit
        cost_sentence = (
            f"Under our documented assumptions, closing the AIR gap from "
            f"{frontier[0]['air_women_led']:.4f} to {frontier[-1]['air_women_led']:.4f} "
            f"costs approximately INR {cost:,.0f} in expected profit "
            f"(illustrative parameters: LGD={frontier[0]['lgd']}, "
            f"margin={frontier[0]['margin']}, ticket=INR {frontier[0]['ticket_inr']:,.0f})."
        )
    else:
        cost_sentence = "Frontier sweep insufficient for cost computation."

    # 7. Write metrics
    write_metrics("fairness", {
        "women_led_air": report["adverse_impact_ratio"].get("women_led", 0.0),
        "rural_air": report["adverse_impact_ratio"].get("rural", 0.0),
        "new_to_credit_air": report["adverse_impact_ratio"].get("new_to_credit", 0.0),
        "women_led_tpr_gap": report["tpr_gap"].get("women_led", 0.0),
        "rural_tpr_gap": report["tpr_gap"].get("rural", 0.0),
        "new_to_credit_tpr_gap": report["tpr_gap"].get("new_to_credit", 0.0),
        "women_rural_intersectional_approval": report["intersectional"][0]["approval_rate"],
        "women_rural_intersectional_small_n": report["intersectional"][0]["small_n"],
        "proxy_audit_auc": audit["auc"],
        "proxy_audit_accuracy": audit["accuracy"],
        "frontier_points": len(frontier),
        "cost_of_fairness_sentence": cost_sentence,
        "_note": "Measured and mitigated under stated definitions: Positive outcome is Non-default.",
    })

    print("[fairness] fairness_groups.json written.")
    print(f"[fairness] frontier.json written ({len(frontier)} points).")
    print(f"[fairness] proxy_audit.json written (AUC={audit['auc']}).")
    print(f"[fairness] {cost_sentence}")
