"""OWNER: M3. Page: Early Warning. UI only: call `core` functions; read artifacts via core.paths."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import streamlit as st

import core
from app.components import ui
from core.early_warning import estimate_loss_avoided, get_borrower_hazard_trajectory
from core.paths import load_metrics

ui.page_header("Early Warning", "watchlist and lead time", "Risk Head")

# Month selector (25-36)
month = st.selectbox("Select Month (OOT)", options=list(range(25, 37)), index=0)

st.subheader(f"Watchlist - Month {month}")
rows = ui.safe_call(core.watchlist, month)

if rows:
    ui.stub_banner(None)
    st.dataframe(rows)
    ui.caption("Borrowers ranked by monthly default hazard, with a suggested action.")

    borrower_ids = [r["borrower_id"] for r in rows]
    selected_bid = st.selectbox("Select Borrower for Details", options=borrower_ids)

    if selected_bid:
        st.subheader("Hazard Trajectory")
        traj = get_borrower_hazard_trajectory(selected_bid)
        if traj:
            import pandas as pd
            df_traj = pd.DataFrame(traj).set_index("month")
            st.line_chart(df_traj)
            ui.caption("Hazard curve over 36 months.")
        
        st.subheader("Estimated Loss Avoided if Restructured")
        loss_info = estimate_loss_avoided(selected_bid)
        st.metric(
            label="Estimated Loss Avoided", 
            value=ui.inr(loss_info["loss_avoided"]),
            help="Difference in expected loss between flat EMI and DSCR-matched schedule."
        )
        ui.caption("Illustrative loss avoided using public API from core.structuring")

st.divider()
st.subheader("System Metrics")
metrics = load_metrics().get("early_warning", {})
if metrics:
    c1, c2, c3 = st.columns(3)
    c1.metric("Top Decile Lift", f"{metrics.get('top_decile_lift', 0)}x")
    c2.metric("Median Lead Time", f"{metrics.get('median_lead_time_months', 0)}m")
    c3.metric("Mean Lead Time", f"{metrics.get('mean_lead_time_months', 0)}m")

    lead_time_seg = metrics.get("lead_time_by_segment", {})
    if lead_time_seg:
        st.write("Lead Time by Segment")
        st.json(lead_time_seg)

st.subheader("Suggested Pre-emptive Actions Rule Table")
st.markdown("""
| Condition | Hazard Level | Leading Distress Indicators | Action |
| --- | --- | --- | --- |
| 1 | Top Decile | delay_trend_3m > 10 OR receivable_trend_3m > 15 | **restructure** (working capital / delay shock) |
| 2 | Top Decile | cheque_bounces_3m >= 2 OR balance_drop_3m < -0.35 | **reduce_limit** (severe liquidity crisis) |
| 3 | Top Decile | None of the above | **call** (early borrower outreach) |
| 4 | Below Top Decile | Any | **monitor** |
""")
