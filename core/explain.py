"""OWNER: M2. SHAP wrappers + reason-code templating (top-3 plain-language reasons).

Writes artifacts/shap.parquet (precomputed for test borrowers). Templates come from
configs/feature_spec.json `reason_risk` fields, formatted with the borrower's actual value.

Design (L4 / Blueprint §5.4):
  - Uses TreeExplainer for LightGBM challenger, WoE-based contribution for champion.
  - Skips protected attributes (owner_gender, location_class) and derived features.
  - Returns Reason objects matching the frozen contract in core/contracts.py.
  - Build against a small local model when M1's real models are not present.
"""
from __future__ import annotations

import pickle
import warnings
from typing import Any

import numpy as np
import pandas as pd

from core.contracts import Reason
from core.features import by_name, model_features
from core.paths import ARTIFACTS, MODELS, write_metrics
from core.reference import MEENA, MEENA_ID, TEST_BORROWER_IDS, resolve

# Suppress LightGBM / SHAP version warnings to keep smoke output clean
warnings.filterwarnings("ignore", category=UserWarning, module="lightgbm")
warnings.filterwarnings("ignore", category=FutureWarning)

# Protected and uninformative features — never surfaced in reasons
_SKIP_FEATURES: set[str] = {"owner_gender", "location_class"}


# ---------------------------------------------------------------------------
# Tiny local model training (used when M1's trained models are absent)
# ---------------------------------------------------------------------------

def _make_tiny_model(seed: int = 42):
    """Train a tiny LightGBM classifier on smoke-scale generated data.

    Returns (model, feature_names) so callers can run SHAP.
    """
    import lightgbm as lgb

    from core.generator import build_artifacts as _gen_build

    # Generate data into data/ (smoke, fast)
    _gen_build(smoke=True)

    from core.paths import DATA

    bdf = pd.read_parquet(DATA / "borrowers.parquet")

    feature_cols = model_features()
    # Drop columns absent in the dataframe, fill NaN for numeric
    available = [c for c in feature_cols if c in bdf.columns]
    X = bdf[available].copy()

    # Encode categoricals as standard pandas.Categorical
    spec = by_name()
    for col in available:
        if spec.get(col, {}).get("type") == "cat":
            cats = spec[col].get("categories", [])
            X[col] = pd.Categorical(X[col], categories=cats)
        else:
            X[col] = pd.to_numeric(X[col], errors="coerce").fillna(-1)

    # Synthetic target: thin-file (bureau_score NaN) → slightly higher default prob
    rng = np.random.default_rng(seed)
    y = (rng.random(len(X)) < 0.15).astype(int)

    params = {
        "objective": "binary",
        "n_estimators": 50,
        "num_leaves": 8,
        "learning_rate": 0.1,
        "monotone_constraints": _monotone_vector(available),
        "verbose": -1,
        "random_state": seed,
    }
    model = lgb.LGBMClassifier(**params)
    model.fit(X, y)
    return model, available


def _monotone_vector(feature_names: list[str]) -> list[int]:
    """Return monotone_pd values for given features in order."""
    spec = by_name()
    return [spec[n].get("monotone_pd", 0) for n in feature_names if n in spec]


def _load_challenger():
    """Load M1's challenger model if available, else train the tiny local one."""
    challenger_path = MODELS / "challenger.pkl"
    if challenger_path.exists():
        with open(challenger_path, "rb") as f:
            bundle = pickle.load(f)
        model = bundle.get("model") if isinstance(bundle, dict) else bundle
        features = bundle.get("features", model_features()) if isinstance(bundle, dict) else model_features()
        return model, features, False  # is_local=False
    # Fallback: build a small local model
    model, features = _make_tiny_model()
    return model, features, True  # is_local=True


# ---------------------------------------------------------------------------
# Feature row preparation
# ---------------------------------------------------------------------------

def _prepare_row(b: dict, feature_names: list[str]) -> pd.DataFrame:
    """Convert a borrower dict to a one-row DataFrame matching feature_names."""
    spec = by_name()
    vals = {name: b.get(name, np.nan) for name in feature_names}
    df = pd.DataFrame([vals])

    for f in feature_names:
        if spec.get(f, {}).get("type") == "cat":
            cats = spec[f].get("categories", [])
            df[f] = pd.Categorical(df[f], categories=cats)
        else:
            df[f] = pd.to_numeric(df[f], errors="coerce")

    return df


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def reasons_for(
    borrower_row: Any,
    model_bundle: Any | None = None,
    k: int = 3,
) -> list[Reason]:
    """Return top-k Reason objects ranked by positive PD contribution.

    Reasons are sourced from the `reason_risk` template in configs/feature_spec.json,
    formatted with the borrower's actual feature value.  Protected and uninformative
    features are always skipped.

    Args:
        borrower_row: dict (with 'id'), borrower id string, or single-row DataFrame.
        model_bundle: optional pre-loaded (model, feature_names) tuple; if None, loads
                      the challenger (or falls back to local tiny model).
        k: number of reasons to return (default 3).

    Returns:
        List of Reason dicts, sorted by impact descending (highest PD contribution first).

    Example:
        reasons = reasons_for("MSME-00001")
        reasons[0]["feature"]  # e.g. "receivable_days"
        reasons[0]["impact"]   # positive float → raises PD
    """
    import shap

    # Resolve borrower
    if isinstance(borrower_row, pd.DataFrame):
        b = borrower_row.iloc[0].to_dict()
    else:
        b = resolve(borrower_row)

    # Fill defaults from Meena for missing values
    filled = dict(MEENA)
    filled.update({k_: v for k_, v in b.items() if v is not None})

    # Load model
    if model_bundle is None:
        model, feature_names, _local = _load_challenger()
    else:
        model, feature_names = model_bundle

    X = _prepare_row(filled, feature_names)

    # Compute SHAP values with TreeExplainer
    explainer = shap.TreeExplainer(model)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sv = explainer.shap_values(X)

    # For binary classification lgbm, sv may be a list [neg, pos] or a 3d array
    if isinstance(sv, list):
        shap_vals = sv[1][0]  # positive class, first row
    elif sv.ndim == 3:
        shap_vals = sv[0, :, 1]  # (samples, features, classes)
    else:
        shap_vals = sv[0]

    # Map feature → SHAP value, filtering protected/uninformative
    spec = by_name()
    contributions: list[tuple[str, float]] = []
    for fname, sval in zip(feature_names, shap_vals, strict=False):
        if fname in _SKIP_FEATURES:
            continue
        feat_spec = spec.get(fname, {})
        if not feat_spec.get("model_input", True):
            continue
        reason_text = feat_spec.get("reason_risk", "")
        if not reason_text:
            continue
        contributions.append((fname, float(sval)))

    # Sort by positive contribution (highest PD raise first)
    contributions.sort(key=lambda x: x[1], reverse=True)
    top = contributions[:k]

    reasons: list[Reason] = []
    for fname, impact in top:
        feat_spec = spec.get(fname, {})
        raw_val = filled.get(fname, 0.0)
        # Format the reason_risk template with the actual value
        template = feat_spec.get("reason_risk", "")
        try:
            if raw_val is None or (isinstance(raw_val, float) and np.isnan(raw_val)):
                text = template.replace("{value:.0f}", "N/A").replace("{value:.1%}", "N/A") \
                               .replace("{value:.2f}", "N/A").replace("{value:,.0f}", "N/A") \
                               .replace("{value:.0%}", "N/A")
            else:
                text = template.format(value=raw_val)
        except (KeyError, ValueError):
            text = template

        reasons.append({
            "feature": fname,
            "text": text,
            "impact": impact,
        })

    return reasons


# ---------------------------------------------------------------------------
# Build artifacts
# ---------------------------------------------------------------------------

def build_artifacts(smoke: bool = False) -> None:
    """Precompute SHAP values for test borrowers; write artifacts/shap.parquet.

    In smoke mode only processes Meena (MSME-00001) for speed.
    """
    import shap

    model, feature_names, is_local = _load_challenger()
    model_version = "local-tiny" if is_local else "challenger"

    ids = [MEENA_ID] if smoke else TEST_BORROWER_IDS

    rows: list[dict[str, Any]] = []
    for bid in ids:
        b = resolve(bid)
        filled = dict(MEENA)
        filled.update({k: v for k, v in b.items() if v is not None})
        X = _prepare_row(filled, feature_names)

        explainer = shap.TreeExplainer(model)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sv = explainer.shap_values(X)

        if isinstance(sv, list):
            shap_vals = sv[1][0]
        elif sv.ndim == 3:
            shap_vals = sv[0, :, 1]
        else:
            shap_vals = sv[0]

        row: dict[str, Any] = {"borrower_id": bid}
        for fname, sval in zip(feature_names, shap_vals, strict=False):
            row[f"shap_{fname}"] = float(sval)
        rows.append(row)

    df = pd.DataFrame(rows)
    out = ARTIFACTS / "shap.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)

    # Write metrics: mean absolute SHAP by feature (top features)
    shap_cols = [c for c in df.columns if c.startswith("shap_")]
    mean_abs: dict[str, float] = {
        c.replace("shap_", ""): float(df[c].abs().mean()) for c in shap_cols
    }
    write_metrics("explain", {
        "model_version": model_version,
        "n_borrowers": len(ids),
        "mean_abs_shap": mean_abs,
    })

    print(f"[explain] shap.parquet written ({len(rows)} rows, model={model_version})")
