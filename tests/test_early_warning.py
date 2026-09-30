"""Tests for early warning hazard model, out-of-time evaluation, and watchlist."""
import numpy as np
import pandas as pd

from core.early_warning import (
    build_ew_features,
    get_borrower_hazard_trajectory,
    train_hazard_model,
    watchlist,
)
from core.paths import DATA
from core.reference import REFERENCE_BORROWER_ID


def test_ew_features_no_lookahead():
    """Verify that features at month t use data <= t strictly without lookahead."""
    df = pd.DataFrame({
        "id": ["A", "A", "A", "A"],
        "month": [1, 2, 3, 4],
        "upi_inflow": [100, 110, 120, 130],
        "bank_inflow": [200, 210, 220, 230],
        "gst_filing_delay_days": [2, 4, 6, 8],
        "avg_bank_balance": [1000, 900, 800, 700],
        "cheque_bounces": [0, 1, 0, 1],
        "gstr1_3b_mismatch": [0.01, 0.02, 0.01, 0.03],
        "receivable_days": [30, 35, 40, 45],
        "revenue": [500, 520, 540, 560],
        "utility_delay_days": [0, 1, 2, 1],
    })
    res = build_ew_features(df)

    # Month 1 must have no 3m lag (NaN)
    assert pd.isna(res.loc[(res["id"] == "A") & (res["month"] == 1), "inflow_change_3m"].iloc[0])

    # Month 4 3m change is based strictly on month 1:
    # month 4 total inflow = 130 + 230 = 360, month 1 = 100 + 200 = 300 -> change = 360/300 - 1 = 0.20
    assert np.isclose(res.loc[(res["id"] == "A") & (res["month"] == 4), "inflow_change_3m"].iloc[0], 0.2)


def test_hazard_model_out_of_time_split():
    """Verify model is trained on months <= 24 and evaluated strictly on months 25-36."""
    panel = pd.read_parquet(DATA / "panel.parquet")
    borrowers = pd.read_parquet(DATA / "borrowers.parquet")
    oracle = pd.read_parquet(DATA / "oracle.parquet")

    ew_df = build_ew_features(panel, borrowers)
    clf, metrics = train_hazard_model(ew_df, oracle)

    assert clf is not None
    assert metrics["oot_eval_months"] == [25, 36]
    assert metrics["top_decile_lift"] > 1.0
    assert metrics["median_lead_time_months"] >= 0.0


def test_watchlist_contract_and_sorted():
    """Verify watchlist returns contract WatchRow items sorted descending by hazard."""
    wlist = watchlist(25)
    assert len(wlist) > 0

    valid_actions = {"call", "restructure", "reduce_limit", "monitor"}

    for idx, row in enumerate(wlist):
        assert "borrower_id" in row
        assert "month" in row and row["month"] == 25
        assert "hazard" in row and 0.0 <= row["hazard"] <= 1.0
        assert "rank" in row and row["rank"] == idx + 1
        assert "action" in row and row["action"] in valid_actions

    # Check strictly monotonic descending sorting by hazard
    hazards = [r["hazard"] for r in wlist]
    for i in range(len(hazards) - 1):
        assert hazards[i] >= hazards[i + 1], f"Watchlist not sorted at index {i}: {hazards[i]} < {hazards[i+1]}"


def test_meena_in_early_warning():
    """Verify Meena (MSME-00001) has valid early warning trajectory."""
    traj = get_borrower_hazard_trajectory(REFERENCE_BORROWER_ID)
    assert len(traj) > 0
    for pt in traj:
        assert 1 <= pt["month"] <= 36
        assert 0.0 <= pt["hazard"] <= 1.0
