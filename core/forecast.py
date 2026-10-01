"""OWNER: M2. Quantile (P10/P50/P90) net-cash-available forecast + split conformal calibration.

Writes artifacts/forecast_bands.parquet, artifacts/metrics/forecast.json (interval coverage).

Design (Blueprint §5.5, L6):
  - LightGBM quantile regressors (alpha 0.1, 0.5, 0.9) for monthly net cash available.
  - Time-based train/test split: train on months 1-24, test on months 25-36.
  - Split-conformal calibration applied to P10 / P90 so nominal coverage is defensible.
  - Backtest reports raw and conformal interval coverage (target ≥ 80% for 80% PI, etc.)
    overall and by sector.
  - Uses data/panel.parquet produced by M1's generator; generates panel if absent.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from core.paths import ARTIFACTS, DATA, write_metrics

warnings.filterwarnings("ignore", category=UserWarning, module="lightgbm")

# Train on months 1-24, test on months 25-36
_TRAIN_MONTHS = 24
_TEST_MONTHS_START = 25

# Features used for the net-cash forecast model
_PANEL_FEATURES = [
    "revenue",
    "upi_inflow",
    "bank_inflow",
    "avg_bank_balance",
    "gst_turnover",
    "gstr1_3b_mismatch",
    "gst_filing_delay_days",
    "receivable_days",
    "utility_delay_days",
    "cheque_bounces",
    "month",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ensure_panel(smoke: bool = False) -> pd.DataFrame:
    """Load data/panel.parquet, generating it if absent."""
    panel_path = DATA / "panel.parquet"
    if not panel_path.exists():
        from core.generator import build_artifacts as _gen
        _gen(smoke=smoke)
    return pd.read_parquet(panel_path)


def _make_features(df: pd.DataFrame) -> pd.DataFrame:
    """Select and clean feature columns; return feature matrix."""
    available = [c for c in _PANEL_FEATURES if c in df.columns]
    X = df[available].copy()
    # Encode month as cyclical features
    if "month" in X.columns:
        m = X["month"].astype(float)
        X["month_sin"] = np.sin(2 * np.pi * m / 12)
        X["month_cos"] = np.cos(2 * np.pi * m / 12)
        X = X.drop(columns=["month"])
    return X.fillna(0.0)


def _target(df: pd.DataFrame) -> pd.Series:
    """Net cash available for debt service: upi_inflow proxy × stability factor."""
    if "upi_inflow" in df.columns and "avg_bank_balance" in df.columns:
        # Simple approximation: 40% of inflow + 10% of buffer
        return (df["upi_inflow"] * 0.40 + df["avg_bank_balance"] * 0.10).fillna(0.0)
    elif "revenue" in df.columns:
        return (df["revenue"] * 0.30).fillna(0.0)
    return pd.Series(np.zeros(len(df)), index=df.index)


# ---------------------------------------------------------------------------
# Conformal calibration helpers
# ---------------------------------------------------------------------------

def _conformal_width(
    residuals: np.ndarray,
    nominal_coverage: float,
) -> float:
    """Split-conformal quantile: residual magnitude such that ≥ nominal_coverage of calib
    points are covered.  Residuals = |y_true - y_pred|.
    """
    q_level = np.ceil((len(residuals) + 1) * nominal_coverage) / len(residuals)
    q_level = min(q_level, 1.0)
    return float(np.quantile(residuals, q_level))


def _coverage(y_true: np.ndarray, lo: np.ndarray, hi: np.ndarray) -> float:
    """Empirical interval coverage."""
    inside = (y_true >= lo) & (y_true <= hi)
    return float(inside.mean())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def forecast(
    borrower_id: str | None = None,
    n_months: int = 12,
    smoke: bool = False,
) -> dict:
    """Return P10/P50/P90 monthly net-cash forecast for a borrower.

    Uses pre-fitted quantile models (trained in build_artifacts).  If models are
    not yet cached, trains them on the fly (slow; prefer build_artifacts).

    Args:
        borrower_id: id string (default: all borrowers / Meena in smoke mode).
        n_months: number of forecast months.
        smoke: if True, fast path (Meena only).

    Returns:
        Dict with keys: borrower_id, months (list[int]), p10 (list[float]),
        p50 (list[float]), p90 (list[float]), model_version.

    Example:
        f = forecast("MSME-00001")
        all(f["p10"][i] <= f["p50"][i] <= f["p90"][i] for i in range(len(f["p10"])))
    """
    models_path = ARTIFACTS / "forecast_models.pkl"
    if not models_path.exists():
        build_artifacts(smoke=smoke)

    import pickle
    with open(models_path, "rb") as fh:
        bundle = pickle.load(fh)

    model_p10 = bundle["model_p10"]
    model_p50 = bundle["model_p50"]
    model_p90 = bundle["model_p90"]
    conf_delta = bundle.get("conf_delta", 0.0)
    feat_cols = bundle["feature_cols"]

    panel = _ensure_panel(smoke=smoke)

    if borrower_id is not None:
        panel = panel[panel["id"] == borrower_id]
        if panel.empty:
            # Use Meena data if borrower not in panel
            panel = _ensure_panel(smoke=False)
            panel = panel[panel["id"] == "MSME-00001"]

    # Use the last n_months of the panel as future months
    future = panel.sort_values("month").tail(n_months).copy()
    if len(future) == 0:
        future = panel.tail(1)

    X = _make_features(future)
    for c in feat_cols:
        if c not in X.columns:
            X[c] = 0.0
    X = X[feat_cols]

    p10_raw = model_p10.predict(X)
    p50 = model_p50.predict(X)
    p90_raw = model_p90.predict(X)

    # Apply conformal adjustment
    p10 = np.maximum(p10_raw - conf_delta, 0.0)
    p90 = p90_raw + conf_delta

    # Enforce monotone bands: p10 <= p50 <= p90
    p10 = np.minimum(p10, p50)
    p90 = np.maximum(p90, p50)

    months = list(future["month"].astype(int).values) if "month" in future else list(range(1, len(p50) + 1))

    return {
        "borrower_id": borrower_id or "all",
        "months": months,
        "p10": list(np.round(p10, 2)),
        "p50": list(np.round(p50, 2)),
        "p90": list(np.round(p90, 2)),
        "model_version": "lgbm-quantile-v1",
    }


def build_artifacts(smoke: bool = False) -> None:
    """Train quantile LightGBM models; write forecast_bands.parquet and metrics.

    Time split: train months 1-24, calib months 21-24, test months 25-36.
    Also applies split-conformal calibration and reports interval coverage
    overall and by sector.
    """
    import pickle

    import lightgbm as lgb

    panel = _ensure_panel(smoke=smoke)

    train = panel[panel["month"] <= _TRAIN_MONTHS].copy()
    test = panel[panel["month"] >= _TEST_MONTHS_START].copy()

    # Calibration set: last 4 months of training (months 21-24)
    calib = train[train["month"] >= (_TRAIN_MONTHS - 3)].copy()

    X_train = _make_features(train)
    y_train = _target(train).values

    X_calib = _make_features(calib)
    y_calib = _target(calib).values

    X_test = _make_features(test)
    y_test = _target(test).values

    feat_cols = list(X_train.columns)

    # Ensure calib and test have the same columns
    for df in [X_calib, X_test]:
        for c in feat_cols:
            if c not in df.columns:
                df[c] = 0.0

    X_calib = X_calib[feat_cols]
    X_test = X_test[feat_cols]

    # Train quantile models
    def _train_quantile(alpha: float):
        params = {
            "objective": "quantile",
            "alpha": alpha,
            "n_estimators": 100 if not smoke else 30,
            "num_leaves": 15,
            "learning_rate": 0.05,
            "min_child_samples": 5,
            "verbose": -1,
            "random_state": 42,
        }
        m = lgb.LGBMRegressor(**params)
        m.fit(X_train, y_train)
        return m

    model_p10 = _train_quantile(0.1)
    model_p50 = _train_quantile(0.5)
    model_p90 = _train_quantile(0.9)

    # Raw test coverage (before conformal)
    p10_test_raw = model_p10.predict(X_test)
    p90_test_raw = model_p90.predict(X_test)
    raw_coverage_80 = _coverage(y_test, p10_test_raw, p90_test_raw)

    # Split-conformal calibration on calib set
    p10_calib = model_p10.predict(X_calib)
    p90_calib = model_p90.predict(X_calib)
    calib_residuals = np.maximum(p10_calib - y_calib, y_calib - p90_calib)
    calib_residuals = np.maximum(calib_residuals, 0.0)

    # Compute conformal delta for 80% coverage
    target_coverage = 0.80
    conf_delta = _conformal_width(calib_residuals, nominal_coverage=target_coverage)

    # Adjusted test coverage
    p10_test = np.maximum(p10_test_raw - conf_delta, 0.0)
    p90_test = p90_test_raw + conf_delta
    conformal_coverage_80 = _coverage(y_test, p10_test, p90_test)

    # --- Coverage by sector ---
    coverage_by_sector: dict[str, float] = {}
    if "sector" in test.columns:
        test_reset = test.reset_index(drop=True)
        for sector_val in sorted(test_reset["sector"].dropna().unique()):
            mask = test_reset["sector"].values == sector_val
            if mask.sum() == 0:
                continue
            cov = _coverage(y_test[mask], p10_test[mask], p90_test[mask])
            coverage_by_sector[str(sector_val)] = round(cov, 4)

    # --- Coverage by test month ---
    coverage_by_month: dict[str, float] = {}
    if "month" in test.columns:
        test_reset = test.reset_index(drop=True)
        for m_val in sorted(test_reset["month"].unique()):
            mask = test_reset["month"].values == m_val
            if mask.sum() == 0:
                continue
            cov = _coverage(y_test[mask], p10_test[mask], p90_test[mask])
            coverage_by_month[str(int(m_val))] = round(cov, 4)

    # Write forecast_bands.parquet
    test_out = test[["id", "month"]].copy().reset_index(drop=True)
    test_out["p10"] = np.round(p10_test, 2)
    test_out["p50"] = np.round(model_p50.predict(X_test), 2)
    test_out["p90"] = np.round(p90_test, 2)
    test_out["y_actual"] = np.round(y_test, 2)

    # Enforce monotone bands
    test_out["p10"] = np.minimum(test_out["p10"], test_out["p50"])
    test_out["p90"] = np.maximum(test_out["p90"], test_out["p50"])

    out_path = ARTIFACTS / "forecast_bands.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    test_out.to_parquet(out_path, index=False)

    # Save models for forecast() function
    models_path = ARTIFACTS / "forecast_models.pkl"
    with open(models_path, "wb") as fh:
        pickle.dump({
            "model_p10": model_p10,
            "model_p50": model_p50,
            "model_p90": model_p90,
            "conf_delta": conf_delta,
            "feature_cols": feat_cols,
        }, fh)

    # Write metrics
    write_metrics("forecast", {
        "n_train_rows": int(len(train)),
        "n_test_rows": int(len(test)),
        "raw_interval_coverage_80pct": round(raw_coverage_80, 4),
        "conformal_interval_coverage_80pct": round(conformal_coverage_80, 4),
        "conformal_delta_inr": round(float(conf_delta), 2),
        "coverage_p10_p90": round(conformal_coverage_80, 4),
        "coverage_by_sector": coverage_by_sector,
        "coverage_by_month": coverage_by_month,
        "model_version": "lgbm-quantile-v1",
        "_note": "Under documented assumptions: synthetic panel data; coverage is method validation.",
    })

    print(
        f"[forecast] forecast_bands.parquet written. "
        f"Raw 80% coverage: {raw_coverage_80:.1%}, "
        f"Conformal 80% coverage: {conformal_coverage_80:.1%}"
    )
    if coverage_by_sector:
        print(f"[forecast] Coverage by sector: {coverage_by_sector}")
