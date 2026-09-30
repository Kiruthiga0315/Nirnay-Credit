"""OWNER: M1. F14 external validity: same pipeline on ONE real public credit dataset (metrics only).
Writes artifacts/external_validity.json. Check the dataset licence first; never commit raw data."""
from __future__ import annotations

import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from core.models import WoEBinning, _evaluate_model, _evaluate_model_from_probs, _train_lgbm
from core.paths import DATA, write_json, write_metrics


def build_artifacts(smoke: bool = False) -> None:
    external_dir = DATA / "external"
    dataset_path = external_dir / "dataset.csv"

    if not dataset_path.exists():
        print("[external] Dataset not found. Skipping external validity.")
        write_json("external_validity.json", {"status": "dataset not loaded yet"})
        return

    print("[external] Found real public credit dataset. Running external validity...")
    df = pd.read_csv(dataset_path)

    # Minimal feature mapping assumption
    # We assume 'default_payment_next_month' as target (Taiwan credit card default dataset convention)
    # If not present, look for 'default' or similar
    target_col = "default_payment_next_month" if "default_payment_next_month" in df.columns else "default"
    if target_col not in df.columns:
        # Fallback to the last column being the target
        target_col = df.columns[-1]

    y = df[target_col].astype(int)
    X = df.drop(columns=[target_col])
    
    # We will use all numeric columns as features for simplicity
    numeric_cols = X.select_dtypes(include=["number"]).columns.tolist()
    if not numeric_cols:
        print("[external] No numeric features found. Skipping.")
        write_json("external_validity.json", {"status": "no numeric features found in dataset"})
        return
    
    X = X[numeric_cols]
    # Simple imputation for missing values
    X = X.fillna(X.median(numeric_only=True))

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Champion: WoE + Logistic Regression
    woe = WoEBinning(bins=5)
    # mock spec for WoE
    for col in X.columns:
        woe.bin_edges[col] = "continuous" # let it determine
    woe.fit(X_train, y_train)
    X_train_woe = woe.transform(X_train)
    X_test_woe = woe.transform(X_test)
    
    champion = LogisticRegression(random_state=42, max_iter=1000)
    champion.fit(X_train_woe, y_train)
    y_prob_champ = champion.predict_proba(X_test_woe)[:, 1]
    _, champ_metrics = _evaluate_model_from_probs(y_prob_champ, y_test.values)

    # Challenger: LightGBM
    monotone = [0] * len(numeric_cols) # No constraints for arbitrary external data
    
    # Split train for calibration
    X_tr_fit, X_tr_cal, y_tr_fit, y_tr_cal = train_test_split(X_train, y_train, test_size=0.2, random_state=42)
    challenger = _train_lgbm(X_tr_fit, y_tr_fit, monotone, seed=42)

    # Calibration
    calibrator = IsotonicRegression(out_of_bounds='clip')
    y_tr_cal_prob = challenger.predict_proba(X_tr_cal)[:, 1]
    calibrator.fit(y_tr_cal_prob, y_tr_cal)
    
    _, chall_metrics = _evaluate_model(challenger, X_test, y_test, calib=calibrator)

    metrics = {
        "auc_champion": champ_metrics["auc"],
        "ks_champion": champ_metrics["ks"],
        "ece_champion": champ_metrics["ece"],
        "auc_challenger": chall_metrics["auc"],
        "ks_challenger": chall_metrics["ks"],
        "ece_challenger": chall_metrics["ece"]
    }

    result = {
        "status": "loaded",
        "dataset": "dataset.csv",
        "n_samples": len(df),
        "target_col": target_col,
        "features": numeric_cols,
        "metrics": metrics
    }
    write_json("external_validity.json", result)
    write_metrics("external", metrics)
    print(f"[external] Completed. Challenger AUC on real data: {metrics['auc_challenger']:.4f}")
