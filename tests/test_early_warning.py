import numpy as np
import pandas as pd

from core.early_warning import build_ew_features


def test_ew_features_no_lookahead():
    # synthetic panel
    df = pd.DataFrame({
        "id": ["A", "A", "A", "A"],
        "month": [1, 2, 3, 4],
        "upi_inflow": [100, 110, 120, 130],
        "bank_inflow": [200, 210, 220, 230],
        "gst_filing_delay_days": [2, 4, 6, 8],
        "avg_bank_balance": [1000, 900, 800, 700],
        "cheque_bounces": [0, 1, 0, 1]
    })
    res = build_ew_features(df)
    
    # check that month 1 has no 3m change
    assert pd.isna(res.loc[(res["id"] == "A") & (res["month"] == 1), "inflow_change_3m"].iloc[0])
    
    # check month 4 3m change is based on month 1
    # total inflow month 4 = 130+230 = 360. month 1 = 100+200 = 300. change = 360/300 - 1 = 0.2
    assert np.isclose(res.loc[(res["id"] == "A") & (res["month"] == 4), "inflow_change_3m"].iloc[0], 0.2)
