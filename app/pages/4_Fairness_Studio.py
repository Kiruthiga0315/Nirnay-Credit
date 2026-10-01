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
from core import paths

ui.page_header("Fairness Studio", "metrics, frontier, proxy audit", "Regulator / Risk Head")
ui.caption("All metrics in this studio are evaluated under documented assumptions as an underwriting decision aid.")

rep = ui.safe_call(core.fairness_report, None)
if rep:
    # 1. Plain-language summary
    women_air = rep["adverse_impact_ratio"].get("women_led", 0.0)
    rural_air = rep["adverse_impact_ratio"].get("rural", 0.0)
    
    st.info(
        f"**Summary (Decision Aid):** Under our documented assumptions, the approval rate for women-led businesses is "
        f"{women_air:.2f}x the rate of other businesses (Adverse Impact Ratio). For rural businesses, it is {rural_air:.2f}x. "
        f"These metrics are measured and mitigated under stated definitions, with 'Non-default' acting as the positive outcome. "
        f"This cockpit functions as a decision aid to quantify trade-offs, not an automated judgment."
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
    ui.caption("Approval rate, true-positive rate (TPR: fraction of non-defaulters approved), and expected calibration error (ECE) by group as an underwriting decision aid under documented assumptions.")
    
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
        ui.caption("Adverse Impact Ratio (AIR): Group approval rate divided by reference group approval rate (decision aid threshold: 0.80).")

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
        ui.caption("Equal Opportunity (TPR Gap): Group TPR minus reference group TPR, measuring parity in identifying non-defaulters as an underwriting decision aid.")
        
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
        ui.caption("Intersectional approval rates measured under stated definitions with 95% bootstrap confidence intervals (decision aid). Small N warning flagged when n < 200.")


st.divider()
st.subheader("Cost of Fairness Frontier (Decision Aid)")
st.warning("Simulation only (Decision Aid): Group-aware thresholds and parameters are illustrative regulator-mandated policy simulations, and are never used as the default decision path.")
frontier = paths.load_json("frontier.json")
if frontier:
    f_df = pd.DataFrame(frontier)
    if "policy" in f_df.columns:
        f_df["strength"] = f_df["policy"].apply(lambda x: x.get("strength", 0.0))
        fig_front = px.line(f_df, x="air_women_led", y="expected_profit_inr", title="Profit vs. AIR Frontier", markers=True)
        st.plotly_chart(fig_front, use_container_width=True)
        
        st.write("### Policy Simulator")
        st.write("Explore the simulated cost of fairness. As we enforce higher fairness constraints, expected profit may decline.")
        selected_strength = st.slider("Select Mitigation Strength", 0.0, 1.0, 0.0, 0.2)
        sel_row = f_df[f_df["strength"] == selected_strength]
        if not sel_row.empty:
            profit = sel_row.iloc[0]['expected_profit_inr']
            air = sel_row.iloc[0]['air_women_led']
            st.metric("Simulated Expected Profit", ui.inr(profit))
            st.metric("Simulated AIR (Women-led)", f"{air:.4f}")
    ui.caption("Cost of Fairness Frontier: Illustrative trade-off showing how policy constraints affect expected portfolio profit under documented assumptions (decision aid).")

st.divider()
st.subheader("Proxy Audit (Decision Aid)")
proxy_audit = paths.load_json("proxy_audit.json")
if proxy_audit:
    st.write(f"**Target**: `{proxy_audit.get('target', 'N/A')}`")
    st.write(f"**AUC**: {proxy_audit.get('auc', 0.0):.4f} | **Accuracy**: {proxy_audit.get('accuracy', 0.0):.4f}")
    st.write(f"*{proxy_audit.get('interpretation', '')}*")
    
    proxies = proxy_audit.get("top_proxies", [])
    if proxies:
        st.dataframe(pd.DataFrame(proxies), use_container_width=True)
    ui.caption("Proxy Audit: Identifies statistical correlations between unconstrained features and protected attributes (decision aid under documented assumptions; not a regulatory compliance claim).")

st.divider()
st.subheader("Recourse Equity Gap (Decision Aid)")
fairness_groups = paths.load_json("fairness_groups.json")
if fairness_groups and "recourse_equity" in fairness_groups:
    req = fairness_groups["recourse_equity"]
    for eq_key, eq_data in req.items():
        st.write(f"#### {eq_key.replace('_', ' ').title()}")
        group_df = pd.DataFrame(eq_data["by_group"]).T
        st.dataframe(group_df)
        note_str = eq_data.get("_note", "")
        st.caption(f"{note_str} Recourse equity evaluates median cost-to-approve disparity across groups as an underwriting decision aid.")
