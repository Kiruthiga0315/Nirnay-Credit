"""OWNER: M1. Page: Model Cockpit. UI only: call `core` functions; read artifacts via core.paths."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.components import ui
from core.paths import load_json, load_metrics

ui.page_header("Model Cockpit", "ROC, KS, calibration, ablation, external validity", "Data Science")

cockpit = load_json("model_cockpit.json")
grid = load_json("sensitivity_grid.json")
external = load_json("external_validity.json")
m = load_metrics()

if not cockpit:
    ui.stub_banner(None)
    st.info("No cockpit metrics yet. Run: python run_all.py")
    st.stop()

st.header("Champion vs Challenger")
col1, col2, col3, col4 = st.columns(4)
champ_m = cockpit["champion_metrics"]
chall_m = cockpit["challenger_metrics"]
col1.metric("AUC (Challenger)", f"{chall_m['auc']:.3f}", f"{chall_m['auc'] - champ_m['auc']:.3f}")
col2.metric("Gini (Challenger)", f"{chall_m['gini']:.3f}", f"{chall_m['gini'] - champ_m['gini']:.3f}")
col3.metric("KS Statistic", f"{chall_m['ks']:.3f}", f"{chall_m['ks'] - champ_m['ks']:.3f}")
col4.metric("ECE", f"{chall_m['ece']:.3f}", f"{chall_m['ece'] - champ_m['ece']:.3f}", delta_color="inverse")

with st.expander("How to read this"):
    st.write("Comparison of the Logistic Regression Champion vs LightGBM Challenger on out-of-time test data.")

st.header("ROC and KS Curves")
col_roc, col_ks = st.columns(2)
with col_roc:
    fig_roc = go.Figure()
    fig_roc.add_trace(go.Scatter(x=cockpit["roc"]["champion"]["fpr"], y=cockpit["roc"]["champion"]["tpr"], name="Champion"))
    fig_roc.add_trace(go.Scatter(x=cockpit["roc"]["challenger"]["fpr"], y=cockpit["roc"]["challenger"]["tpr"], name="Challenger"))
    fig_roc.add_trace(go.Scatter(x=[0, 1], y=[0, 1], line=dict(dash="dash"), name="Random"))
    fig_roc.update_layout(title="ROC Curve", xaxis_title="False Positive Rate", yaxis_title="True Positive Rate")
    st.plotly_chart(fig_roc, use_container_width=True)
    st.caption("How to read this: Higher curve = better rank ordering.")

with col_ks:
    fig_ks = go.Figure()
    # For challenger
    t = cockpit["ks_curve"]["challenger"]["thresholds"]
    cg = cockpit["ks_curve"]["challenger"]["cum_good"]
    cb = cockpit["ks_curve"]["challenger"]["cum_bad"]
    fig_ks.add_trace(go.Scatter(x=t, y=cg, name="Cum. Good (Challenger)", line=dict(dash="dot")))
    fig_ks.add_trace(go.Scatter(x=t, y=cb, name="Cum. Bad (Challenger)"))
    fig_ks.update_layout(title="KS Curve (Challenger)", xaxis_title="Threshold", yaxis_title="Cumulative %")
    st.plotly_chart(fig_ks, use_container_width=True)
    st.caption("How to read this: Maximum vertical distance between curves is the KS statistic.")

st.header("Calibration")
fig_cal = go.Figure()
fig_cal.add_trace(go.Scatter(x=cockpit["calibration"]["champion"]["prob_pred"], y=cockpit["calibration"]["champion"]["prob_true"], mode="lines+markers", name="Champion"))
fig_cal.add_trace(go.Scatter(x=cockpit["calibration"]["challenger"]["prob_pred"], y=cockpit["calibration"]["challenger"]["prob_true"], mode="lines+markers", name="Challenger"))
fig_cal.add_trace(go.Scatter(x=[0, 1], y=[0, 1], line=dict(dash="dash"), name="Perfect Calibration"))
fig_cal.update_layout(title="Reliability Curve", xaxis_title="Predicted Probability", yaxis_title="True Fraction of Positives")
st.plotly_chart(fig_cal, use_container_width=True)
st.caption("How to read this: Closer to the diagonal dashed line = better calibrated probabilities.")

st.header("Ablation & Thin-File Segment")
ablation_thin_toggle = st.toggle("Show Thin-File Segment Only", False)
abl = cockpit["ablation"]
if ablation_thin_toggle:
    data = {"Features": ["Bureau Only", "Alt Data Only", "Both"], "AUC": [abl["thin_bureau_only"], abl["thin_alt_data"], abl["thin_both"]]}
else:
    data = {"Features": ["Bureau Only", "Alt Data Only", "Both"], "AUC": [abl["bureau_only"], abl["alt_data_only"], abl["both"]]}
df_abl = pd.DataFrame(data)
fig_abl = px.bar(df_abl, x="Features", y="AUC", title="Ablation AUC")
fig_abl.update_layout(yaxis=dict(range=[0.4, 0.9]))
st.plotly_chart(fig_abl, use_container_width=True)
st.caption("How to read this: Shows the value of alt-data vs traditional bureau scores, overall and for thin-file borrowers.")

st.header("Population Stability Index (PSI)")
psi_data = [{"Feature": k, "PSI": v} for k, v in cockpit["psi_features"].items()]
df_psi = pd.DataFrame(psi_data).sort_values("PSI", ascending=False)
def color_psi(val):
    if val < 0.1:
        return 'color: green'
    elif val < 0.2:
        return 'color: orange'
    return 'color: red'
st.dataframe(df_psi.style.map(color_psi, subset=['PSI']), use_container_width=True)
st.caption("How to read this: <0.1 is stable (green), 0.1-0.2 is minor shift (orange), >0.2 is major shift (red).")

if grid:
    st.header("Sensitivity Grid (3x3)")
    st.write("Robustness of 'extra approvals at equal loss' across generator assumptions.")
    grid_df = pd.DataFrame(grid["cells"])
    if not grid_df.empty:
        # Pivot to create heatmap
        pivot = grid_df.pivot(index="kappa", columns="bias_strength", values="lift_approvals_at_equal_loss")
        fig_heat = px.imshow(pivot, text_auto=True, aspect="auto", title="Lift (Extra Approvals)")
        st.plotly_chart(fig_heat, use_container_width=True)
    st.caption("How to read this: Positive lift means the method works even under different simulation assumptions.")

st.header("External Validity")
if external and external.get("status") == "loaded":
    metrics = external["metrics"]
    st.success(f"Successfully loaded dataset: {external['dataset']} ({external['n_samples']} samples)")
    col1, col2, col3 = st.columns(3)
    col1.metric("AUC (Champion vs Challenger)", f"{metrics['auc_champion']:.3f}", f"{metrics['auc_challenger'] - metrics['auc_champion']:.3f}")
    col2.metric("KS (Challenger)", f"{metrics['ks_challenger']:.3f}")
    col3.metric("ECE (Challenger)", f"{metrics['ece_challenger']:.3f}")
    st.caption("How to read this: Results on a real public dataset to prove the pipeline works outside our synthetic data.")
else:
    st.warning("External validity: dataset not loaded yet.")
