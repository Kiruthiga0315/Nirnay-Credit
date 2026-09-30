"""OWNER: M2. Page: Fairness Studio. UI only: call `core` functions; read artifacts via core.paths."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import core
from app.components import ui

ui.page_header("Fairness Studio", "metrics, frontier, proxy audit", "Regulator / Risk Head")

rep = ui.safe_call(core.fairness_report, None)
if rep:
    # 1. Plain-language summary
    women_air = rep["adverse_impact_ratio"].get("women_led", 0.0)
    rural_air = rep["adverse_impact_ratio"].get("rural", 0.0)
    
    st.info(
        f"**Summary:** Under our documented assumptions, the approval rate for women-led businesses is "
        f"{women_air:.2f}x the rate of other businesses. For rural businesses, it is {rural_air:.2f}x. "
        f"These metrics are measured and mitigated under stated definitions, with 'Non-default' acting as the positive outcome."
    )
    
    # 2. Group metrics table
    st.subheader("Metrics by Group")
    group_df = pd.DataFrame(rep["by_group"]).T
    group_df = group_df[["n", "approval_rate", "tpr", "ece"]]
    group_df.index.name = "Group"
    st.dataframe(group_df.style.format({
        "n": "{:,.0f}",
        "approval_rate": "{:.1%}",
        "tpr": "{:.1%}",
        "ece": "{:.4f}"
    }), use_container_width=True)
    ui.caption("Approval rate, true-positive rate (TPR), and expected calibration error (ECE) by group.")
    
    col1, col2 = st.columns(2)
    
    # 3. AIR Bar Chart
    with col1:
        st.subheader("Adverse Impact Ratio (AIR)")
        air_df = pd.DataFrame({
            "Group": list(rep["adverse_impact_ratio"].keys()),
            "AIR": list(rep["adverse_impact_ratio"].values())
        })
        fig_air = px.bar(air_df, x="Group", y="AIR", title="Approval Rate Ratio (vs Reference)", text="AIR")
        fig_air.add_hline(y=0.8, line_dash="dash", line_color="red", annotation_text="0.8 Threshold")
        fig_air.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        st.plotly_chart(fig_air, use_container_width=True)
        ui.caption("Adverse Impact Ratio: Approval rate of the group divided by the approval rate of its reference group.")

    # 4. TPR Gap Bar Chart
    with col2:
        st.subheader("Equal Opportunity (TPR Gap)")
        tpr_df = pd.DataFrame({
            "Group": list(rep["tpr_gap"].keys()),
            "TPR Gap": list(rep["tpr_gap"].values())
        })
        fig_tpr = px.bar(tpr_df, x="Group", y="TPR Gap", title="TPR Gap (vs Reference)", text="TPR Gap")
        fig_tpr.add_hline(y=0, line_color="black")
        fig_tpr.update_traces(texttemplate='%{text:.3f}', textposition='outside')
        st.plotly_chart(fig_tpr, use_container_width=True)
        ui.caption("TPR Gap: True Positive Rate of the group minus the TPR of its reference group.")
        
    st.divider()
    
    # 5. Intersectional View with CIs
    st.subheader("Intersectional View (Bootstrap 95% CI)")
    inter_data = rep["intersectional"]
    if inter_data:
        groups = [d["group"] for d in inter_data]
        rates = [d["approval_rate"] for d in inter_data]
        errors_low = [d["approval_rate"] - d["ci_low"] for d in inter_data]
        errors_high = [d["ci_high"] - d["approval_rate"] for d in inter_data]
        flags = [" (Small N!)" if d.get("small_n") else "" for d in inter_data]
        labels = [f"{g}{f}" for g, f in zip(groups, flags, strict=False)]
        
        fig_int = go.Figure(data=go.Bar(
            name='Approval Rate',
            x=labels,
            y=rates,
            error_y=dict(
                type='data',
                symmetric=False,
                array=errors_high,
                arrayminus=errors_low
            )
        ))
        fig_int.update_layout(title_text="Approval Rates with 95% CIs for Intersectional Groups", yaxis_title="Approval Rate")
        st.plotly_chart(fig_int, use_container_width=True)
        ui.caption("Measured under stated definitions. Small N warning flagged when n < 200.")
