"""OWNER: M3. F9 discrete-time hazard model + watchlist + lead-time metric.

Writes models/hazard.pkl, data/ew_features.parquet, artifacts/watchlist.parquet,
artifacts/metrics/early_warning.json.

Design & Methodology:
- Discrete-time hazard: monthly probability of default h(t) = P(default in month t | survived up to t-1).
- Time-based out-of-time split: train strictly on months 1-24, evaluate strictly on months 25-36.
- Feature construction: all features at month t use data <= month t ONLY (lagged & rolling statistics).
- Metric definitions:
  - top_decile_lift: (default rate in top decile of predicted hazard) / (overall default rate in OOT).
  - lead_time_months: for each defaulting borrower in OOT (months 25-36), months between the
    first month predicted hazard exceeded top-decile threshold and the actual default month.
"""
from __future__ import annotations

import pickle
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd

from core.contracts import WatchRow
from core.paths import ARTIFACTS, DATA, MODELS, write_metrics

# Feature column definitions for hazard model (all use data <= month t only)
HAZARD_FEATURE_COLS = [
    "inflow_change_3m",
    "inflow_drop_1m",
    "delay_trend_3m",
    "delay_avg_3m",
    "balance_drop_3m",
    "avg_bank_balance_3m",
    "cheque_bounces_3m",
    "cheque_bounces_6m",
    "gstr1_3b_mismatch_3m",
    "receivable_trend_3m",
    "revenue_growth_3m",
    "utility_delay_3m",
    "vintage_months",
    "requested_amount",
    "bureau_score",
    "gst_filing_delay_days",
    "gstr1_3b_mismatch",
    "receivable_days",
    "cheque_bounces",
]


def build_ew_features(panel: pd.DataFrame, borrowers: pd.DataFrame | None = None) -> pd.DataFrame:
    """Construct early warning features using data <= month t strictly.

    Args:
        panel: Monthly panel DataFrame with columns [id, month, revenue, upi_inflow, bank_inflow, ...].
        borrowers: Optional borrowers DataFrame for static firm metadata.

    Returns:
        DataFrame with lagged/rolling time-series features and static features.
    """
    df = panel.copy().sort_values(["id", "month"]).reset_index(drop=True)
    df["total_inflow"] = df["upi_inflow"] + df["bank_inflow"]

    # Grouped rolling and lagged features (strictly <= month t)
    grp = df.groupby("id")

    # Inflow growth and drop
    df["inflow_lag1"] = grp["total_inflow"].shift(1)
    df["inflow_lag3"] = grp["total_inflow"].shift(3)
    df["inflow_change_3m"] = np.where(
        df["inflow_lag3"].isna(),
        np.nan,
        ((df["total_inflow"] / (df["inflow_lag3"] + 1e-6)) - 1.0).clip(-1.0, 5.0),
    )
    df["inflow_drop_1m"] = np.where(
        df["inflow_lag1"].isna(),
        np.nan,
        ((df["total_inflow"] / (df["inflow_lag1"] + 1e-6)) - 1.0).clip(-1.0, 5.0),
    )

    # GST filing delay trends
    df["delay_lag3"] = grp["gst_filing_delay_days"].shift(3)
    df["delay_trend_3m"] = np.where(
        df["delay_lag3"].isna(),
        np.nan,
        df["gst_filing_delay_days"] - df["delay_lag3"],
    )
    df["delay_avg_3m"] = grp["gst_filing_delay_days"].transform(
        lambda x: x.rolling(3, min_periods=1).mean()
    )

    # Bank balance trends
    df["balance_lag3"] = grp["avg_bank_balance"].shift(3)
    df["balance_drop_3m"] = np.where(
        df["balance_lag3"].isna(),
        np.nan,
        ((df["avg_bank_balance"] / (df["balance_lag3"] + 1e-6)) - 1.0).clip(-1.0, 5.0),
    )
    df["avg_bank_balance_3m"] = grp["avg_bank_balance"].transform(
        lambda x: x.rolling(3, min_periods=1).mean()
    )

    # Cheque bounces rolling count
    df["cheque_bounces_3m"] = grp["cheque_bounces"].transform(
        lambda x: x.rolling(3, min_periods=1).sum()
    )
    df["cheque_bounces_6m"] = grp["cheque_bounces"].transform(
        lambda x: x.rolling(6, min_periods=1).sum()
    )

    # GSTR mismatch rolling average
    df["gstr1_3b_mismatch_3m"] = grp["gstr1_3b_mismatch"].transform(
        lambda x: x.rolling(3, min_periods=1).mean()
    )

    # Receivable days trend
    df["receivable_lag3"] = grp["receivable_days"].shift(3)
    df["receivable_trend_3m"] = (df["receivable_days"] - df["receivable_lag3"]).fillna(0.0)

    # Revenue growth
    df["revenue_lag3"] = grp["revenue"].shift(3)
    df["revenue_growth_3m"] = (
        (df["revenue"] / (df["revenue_lag3"] + 1e-6)) - 1.0
    ).clip(-1.0, 5.0).fillna(0.0)

    # Utility delay rolling average
    df["utility_delay_3m"] = grp["utility_delay_days"].transform(
        lambda x: x.rolling(3, min_periods=1).mean()
    )

    # Attach static borrower features if available
    if borrowers is None and (DATA / "borrowers.parquet").exists():
        borrowers = pd.read_parquet(DATA / "borrowers.parquet")

    if borrowers is not None:
        static_cols = [c for c in ["id", "vintage_months", "requested_amount", "bureau_score"] if c in borrowers.columns]
        df = df.merge(borrowers[static_cols], on="id", how="left")
    else:
        for c in ["vintage_months", "requested_amount", "bureau_score"]:
            if c not in df.columns:
                df[c] = np.nan

    return df


def _assign_action(hazard: float, top_decile_cutoff: float, row: pd.Series | dict[str, Any]) -> str:
    """Action recommendation rule based on hazard and leading distress indicators.

    Rules:
    - If hazard >= top_decile_cutoff:
      - If delay_trend_3m > 10 or receivable_trend_3m > 15: 'restructure' (working capital / delay shock)
      - Else if cheque_bounces_3m >= 2 or balance_drop_3m < -0.35: 'reduce_limit' (severe liquidity crisis)
      - Else: 'call' (early borrower outreach)
    - Else: 'monitor'
    """
    if hazard >= top_decile_cutoff:
        delay_trend = float(row.get("delay_trend_3m", 0.0))
        rec_trend = float(row.get("receivable_trend_3m", 0.0))
        bounces = float(row.get("cheque_bounces_3m", 0.0))
        bal_drop = float(row.get("balance_drop_3m", 0.0))

        if delay_trend > 10.0 or rec_trend > 15.0:
            return "restructure"
        if bounces >= 2.0 or bal_drop < -0.35:
            return "reduce_limit"
        return "call"
    return "monitor"


def train_hazard_model(
    ew_df: pd.DataFrame | None = None,
    oracle_df: pd.DataFrame | None = None,
) -> tuple[lgb.LGBMClassifier, dict[str, Any]]:
    """Train discrete-time hazard model on months 1-24 and evaluate on months 25-36.

    Returns:
        Trained LightGBM model and OOT evaluation metrics dictionary.
    """
    if ew_df is None:
        if (DATA / "ew_features.parquet").exists():
            ew_df = pd.read_parquet(DATA / "ew_features.parquet")
        else:
            panel = pd.read_parquet(DATA / "panel.parquet")
            ew_df = build_ew_features(panel)

    if oracle_df is None:
        oracle_df = pd.read_parquet(DATA / "oracle.parquet")

    df = ew_df.copy()
    def_dict = dict(zip(oracle_df["id"], oracle_df["default_month"], strict=False))
    df["default_month"] = df["id"].map(def_dict).fillna(0).astype(int)

    # Construct discrete-time risk set: firm is at risk if it has not defaulted before current month
    risk_set = (df["default_month"] == 0) | (df["month"] <= df["default_month"])
    df_risk = df[risk_set].copy()

    # Binary hazard target y: 1 if firm defaulted in month t, 0 otherwise
    df_risk["y"] = (
        (df_risk["default_month"] > 0) & (df_risk["month"] == df_risk["default_month"])
    ).astype(int)

    # Time-based split: Train <= 24, Test 25..36
    train_mask = df_risk["month"] <= 24
    test_mask = df_risk["month"] >= 25

    train_data = df_risk[train_mask]
    test_data = df_risk[test_mask].copy()

    X_train = train_data[HAZARD_FEATURE_COLS]
    y_train = train_data["y"]

    clf = lgb.LGBMClassifier(
        n_estimators=150,
        learning_rate=0.03,
        num_leaves=12,
        scale_pos_weight=5.0,
        random_state=42,
        verbose=-1,
    )
    clf.fit(X_train, y_train)

    # Predict hazard on OOT test data
    X_test = test_data[HAZARD_FEATURE_COLS]
    test_preds = clf.predict_proba(X_test)[:, 1]
    test_data["pred_hazard"] = test_preds

    # Top-decile lift evaluation strictly out-of-time (months 25-36)
    q90_cutoff = float(test_data["pred_hazard"].quantile(0.90))
    top_decile = test_data[test_data["pred_hazard"] >= q90_cutoff]
    base_default_rate = float(test_data["y"].mean())
    top_decile_default_rate = float(top_decile["y"].mean())
    lift = (
        round(top_decile_default_rate / base_default_rate, 3)
        if base_default_rate > 0
        else 1.0
    )

    # Lead time metric: months of warning before default for OOT defaulters (months 25-36)
    oot_defaulters = oracle_df[
        (oracle_df["default_month"] >= 25) & (oracle_df["default_month"] <= 36)
    ]
    lead_times: list[float] = []

    for _, def_row in oot_defaulters.iterrows():
        b_id = def_row["id"]
        d_month = int(def_row["default_month"])
        # History of borrower up to default month in test period
        b_history = test_data[(test_data["id"] == b_id) & (test_data["month"] <= d_month)]
        warnings = b_history[b_history["pred_hazard"] >= q90_cutoff]
        if len(warnings) > 0:
            first_warning_month = int(warnings["month"].min())
            lead_time = float(max(0, d_month - first_warning_month))
            lead_times.append(lead_time)
        else:
            lead_times.append(0.0)

    median_lead_time = float(np.median(lead_times)) if lead_times else 0.0
    mean_lead_time = float(np.mean(lead_times)) if lead_times else 0.0

    metrics = {
        "top_decile_lift": lift,
        "median_lead_time_months": round(median_lead_time, 2),
        "mean_lead_time_months": round(mean_lead_time, 2),
        "oot_defaulters_count": len(oot_defaulters),
        "oot_eval_months": [25, 36],
        "top_decile_cutoff": round(q90_cutoff, 4),
        "base_default_rate_oot": round(base_default_rate, 5),
        "top_decile_default_rate_oot": round(top_decile_default_rate, 5),
    }

    return clf, metrics


def _load_or_train_hazard_model() -> lgb.LGBMClassifier:
    """Load cached hazard model from models/hazard.pkl or train if absent."""
    model_path = MODELS / "hazard.pkl"
    if model_path.exists():
        with open(model_path, "rb") as f:
            return pickle.load(f)

    # Train and save
    clf, _ = train_hazard_model()
    MODELS.mkdir(parents=True, exist_ok=True)
    with open(model_path, "wb") as f:
        pickle.dump(clf, f)
    return clf


def watchlist(month: int = 25, limit: int | None = 10) -> list[WatchRow]:
    """Ranked borrowers by monthly default hazard with suggested action.

    Args:
        month: Calendar month in evaluation window (typically 25-36).
        limit: Optional maximum number of top-hazard borrowers to return (default 10).

    Returns:
        List of WatchRow TypedDicts sorted by hazard descending (highest hazard = rank 1).
    """
    ew_path = DATA / "ew_features.parquet"
    if not ew_path.exists():
        panel = pd.read_parquet(DATA / "panel.parquet")
        ew_df = build_ew_features(panel)
        ew_df.to_parquet(ew_path, index=False)
    else:
        ew_df = pd.read_parquet(ew_path)

    month_df = ew_df[ew_df["month"] == month].copy()
    if month_df.empty:
        # Fallback to closest available month or empty
        available_months = ew_df["month"].unique()
        if len(available_months) > 0:
            closest_m = min(available_months, key=lambda m: abs(m - month))
            month_df = ew_df[ew_df["month"] == closest_m].copy()
        else:
            return []

    clf = _load_or_train_hazard_model()
    X = month_df[HAZARD_FEATURE_COLS]
    hazards = clf.predict_proba(X)[:, 1]
    month_df["hazard"] = hazards

    # Determine 90th percentile threshold for top decile actions across active cohort
    top_decile_cutoff = float(month_df["hazard"].quantile(0.90))

    # Sort descending by hazard
    month_df = month_df.sort_values("hazard", ascending=False).reset_index(drop=True)

    if limit is not None and limit > 0:
        month_df = month_df.iloc[:limit]

    rows: list[WatchRow] = []
    for rank_idx, (_, row) in enumerate(month_df.iterrows(), start=1):
        h_val = round(float(row["hazard"]), 4)
        action = _assign_action(h_val, top_decile_cutoff, row)
        rows.append({
            "borrower_id": str(row["id"]),
            "month": int(month),
            "hazard": h_val,
            "rank": rank_idx,
            "action": action,
        })

    return rows


def get_borrower_hazard_trajectory(borrower_id: str) -> list[dict[str, Any]]:
    """Return historical hazard trajectory across all 36 months for a given borrower."""
    ew_path = DATA / "ew_features.parquet"
    if not ew_path.exists():
        panel = pd.read_parquet(DATA / "panel.parquet")
        ew_df = build_ew_features(panel)
    else:
        ew_df = pd.read_parquet(ew_path)

    b_df = ew_df[ew_df["id"] == borrower_id].sort_values("month").copy()
    if b_df.empty:
        return []

    clf = _load_or_train_hazard_model()
    X = b_df[HAZARD_FEATURE_COLS]
    hazards = clf.predict_proba(X)[:, 1]
    b_df["hazard"] = hazards

    return [
        {"month": int(row["month"]), "hazard": round(float(row["hazard"]), 4)}
        for _, row in b_df.iterrows()
    ]


def build_artifacts(smoke: bool = False) -> None:
    """Generate all early warning artifacts: features, model, watchlist, and metrics."""
    DATA.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    # 1. Build EW features
    panel = pd.read_parquet(DATA / "panel.parquet")
    borrowers = pd.read_parquet(DATA / "borrowers.parquet") if (DATA / "borrowers.parquet").exists() else None
    ew_df = build_ew_features(panel, borrowers)
    ew_df.to_parquet(DATA / "ew_features.parquet", index=False)

    # 2. Train hazard model and evaluate strictly out-of-time (months 25-36)
    oracle_df = pd.read_parquet(DATA / "oracle.parquet") if (DATA / "oracle.parquet").exists() else None
    clf, metrics = train_hazard_model(ew_df, oracle_df)

    # Save model
    with open(MODELS / "hazard.pkl", "wb") as f:
        pickle.dump(clf, f)

    # 3. Generate watchlist for month 25 (default evaluation start)
    wlist = watchlist(25)
    df_wlist = pd.DataFrame(wlist)
    df_wlist.to_parquet(ARTIFACTS / "watchlist.parquet", index=False)

    # 4. Write metrics
    write_metrics("early_warning", metrics)
    print(f"[early_warning] Hazard model trained. OOT Top-Decile Lift: {metrics['top_decile_lift']}x, "
          f"Median Lead Time: {metrics['median_lead_time_months']}m (Mean: {metrics['mean_lead_time_months']}m)")
