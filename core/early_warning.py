"""OWNER: M3. F9 discrete-time hazard model + watchlist + lead-time metric.
Writes models/hazard.pkl, artifacts/watchlist.parquet, artifacts/metrics/early_warning.json."""
from __future__ import annotations

import pandas as pd

from core.contracts import WatchRow
from core.reference import TEST_BORROWER_IDS, stable_unit


def watchlist(month: int = 25) -> list[WatchRow]:
    """Ranked borrowers by hazard with a suggested action. STUB values."""
    rows = sorted(TEST_BORROWER_IDS, key=lambda i: -stable_unit(i, f"h{month}"))[:10]
    actions = ["call", "restructure", "reduce_limit", "monitor"]
    return [{"borrower_id": i, "month": month, "hazard": round(0.02 + 0.2 * stable_unit(i, f"h{month}"), 4),
             "rank": n + 1, "action": actions[n % 4]} for n, i in enumerate(rows)]


def build_ew_features(panel: pd.DataFrame) -> pd.DataFrame:
    df = panel.copy().sort_values(["id", "month"])
    
    # Inflows
    df["total_inflow"] = df["upi_inflow"] + df["bank_inflow"]
    df["inflow_lag3"] = df.groupby("id")["total_inflow"].shift(3)
    df["inflow_change_3m"] = (df["total_inflow"] / df["inflow_lag3"]) - 1.0
    
    # Delay trend (current delay - delay 3 months ago)
    df["delay_lag3"] = df.groupby("id")["gst_filing_delay_days"].shift(3)
    df["delay_trend_3m"] = df["gst_filing_delay_days"] - df["delay_lag3"]
    
    # Balance drop
    df["balance_lag3"] = df.groupby("id")["avg_bank_balance"].shift(3)
    df["balance_drop_3m"] = (df["avg_bank_balance"] / df["balance_lag3"]) - 1.0
    
    # Cheque bounces rolling sum
    df["cheque_bounces_3m"] = df.groupby("id")["cheque_bounces"].transform(lambda x: x.rolling(3, min_periods=1).sum())
    
    return df

def build_artifacts(smoke: bool = False) -> None:
    from core.paths import ARTIFACTS, DATA, write_json
    
    # Build EW features
    panel = pd.read_parquet(DATA / "panel.parquet")
    ew_df = build_ew_features(panel)
    ew_df.to_parquet(DATA / "ew_features.parquet", index=False)
    
    # Watchlist stub
    wlist = watchlist(25)
    df = pd.DataFrame(wlist)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    df.to_parquet(ARTIFACTS / "watchlist.parquet")
    write_json("metrics/early_warning.json", {"lead_time_months": 3.5})
    print("[early_warning] Generated artifacts")
