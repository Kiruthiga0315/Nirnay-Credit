"""OWNER: M3. Page: Stress and Contagion. UI only: call `core` functions; read artifacts via core.paths."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.components import ui
from core.paths import ARTIFACTS
from core.stress import SCENARIO_IDS, load_scenarios

ui.page_header("Stress & Contagion", "named replays, contagion, Monte Carlo, tornado", "Risk Head")

st.markdown(
    '<div class="ps12-caption" style="margin-bottom:1rem;">'
    "⚠️ All numbers are <b>illustrative parameters</b> under our documented assumptions."
    "</div>",
    unsafe_allow_html=True,
)

# ---------- scenario selector -------------------------------------------------
scenarios = load_scenarios()
cols = st.columns(len(SCENARIO_IDS))
selected = st.session_state.get("stress_scenario", SCENARIO_IDS[0])

for i, sid in enumerate(SCENARIO_IDS):
    label = scenarios[sid].get("label", sid)
    with cols[i]:
        if st.button(label, key=f"btn_{sid}", use_container_width=True):
            selected = sid
            st.session_state["stress_scenario"] = sid

# ---------- load precomputed artifact -----------------------------------------
artifact_path = ARTIFACTS / f"stress_{selected}.json"
if not artifact_path.exists():
    st.warning("Stress artifacts not yet built. Run `python run_all.py --smoke` first.")
    st.stop()

with open(artifact_path, encoding="utf-8") as f:
    data = json.load(f)

# ---------- KPI tiles ---------------------------------------------------------
st.subheader(f"📊 {scenarios[selected].get('label', selected)}")
st.caption(f"Inspiration: {scenarios[selected].get('inspiration', 'N/A')}")

kpi_cols = st.columns(4)
with kpi_cols[0]:
    ui.kpi("Base EL", ui.inr(data.get("base_el", 0)))
with kpi_cols[1]:
    ui.kpi("Stressed EL (with contagion)", ui.inr(data["expected_loss"]))
with kpi_cols[2]:
    ui.kpi("ES95 (Tail Loss)", ui.inr(data["es95"]))
with kpi_cols[3]:
    ui.kpi("First Failing Segment", data.get("first_failing_segment", "—"))

ui.caption(
    "Expected Loss = Σ PD×LGD×EAD across portfolio under the shocked scenario. "
    "ES95 = 95th percentile of Monte Carlo portfolio loss distribution (Vasicek single-factor model). "
    "First failing = sector with highest absolute loss share."
)

# ---------- Contagion comparison ----------------------------------------------
st.subheader("🔗 Contagion Impact")
comp_cols = st.columns(2)
with comp_cols[0]:
    ui.kpi("EL without contagion", ui.inr(data.get("el_no_contagion", 0)))
    ui.kpi("ES95 without contagion", ui.inr(data.get("es95_no_contagion", 0)))
with comp_cols[1]:
    ui.kpi("EL with contagion", ui.inr(data["expected_loss"]))
    ui.kpi("ES95 with contagion", ui.inr(data["es95"]))

el_lift = data["expected_loss"] - data.get("el_no_contagion", data["expected_loss"])
if el_lift > 0:
    st.info(f"Contagion adds {ui.inr(el_lift)} to expected loss via supplier-buyer propagation.")

ui.caption(
    "Contagion propagates stress through the supplier-buyer graph: "
    "Δreceivable_days_j = Σ w_ij × delay_i × pass_through. Revenue falls proportionally. "
    "Bounded to 3 rounds."
)

# ---------- Monte Carlo bands -------------------------------------------------
bands = data.get("bands", {})
if bands:
    st.subheader("📈 Monte Carlo Loss Distribution")
    band_df = pd.DataFrame([
        {"Percentile": "P5 (optimistic)", "Loss": bands["p5"]},
        {"Percentile": "P50 (median)", "Loss": bands["p50"]},
        {"Percentile": "P95 (tail)", "Loss": bands["p95"]},
    ])
    fig_bands = px.bar(
        band_df, x="Percentile", y="Loss",
        color="Percentile",
        color_discrete_sequence=["#22c55e", "#f59e0b", "#ef4444"],
    )
    fig_bands.update_layout(height=300, showlegend=False, yaxis_title="Portfolio Loss (INR)")
    st.plotly_chart(fig_bands, use_container_width=True)
    ui.caption("P5/P50/P95 of Monte Carlo portfolio loss distribution (2000 runs, Vasicek single-factor).")

# ---------- segment heatmap ---------------------------------------------------
heatmap_data = data.get("heatmap", [])
if heatmap_data:
    st.subheader("🗺️ Segment Heatmap (Sector × Size)")
    hm_df = pd.DataFrame(heatmap_data)
    hm_pivot = hm_df.pivot_table(index="sector", columns="size", values="loss", fill_value=0)
    fig_hm = px.imshow(
        hm_pivot.values,
        labels={"x": "Firm Size", "y": "Sector", "color": "Loss (INR)"},
        x=list(hm_pivot.columns),
        y=list(hm_pivot.index),
        color_continuous_scale="YlOrRd",
        aspect="auto",
    )
    fig_hm.update_layout(height=350)
    st.plotly_chart(fig_hm, use_container_width=True)
    ui.caption("Expected loss by sector and firm size bucket under the stressed scenario.")

# ---------- segment bar chart -------------------------------------------------
st.subheader("📊 Segment Losses")
seg = data.get("segment_losses", {})
if seg:
    seg_df = pd.DataFrame(list(seg.items()), columns=["Sector", "Loss"])
    seg_df = seg_df.sort_values("Loss", ascending=True)
    fig_seg = px.bar(
        seg_df, x="Loss", y="Sector", orientation="h",
        color="Loss", color_continuous_scale="Reds",
    )
    fig_seg.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig_seg, use_container_width=True)
    ui.caption("Loss by sector under the selected shock; illustrative parameters.")

# ---------- tornado chart -----------------------------------------------------
st.subheader("🌪️ Tornado (Assumption Sensitivity on ES95)")
tornado = data.get("tornado", [])
if tornado:
    tornado_df = pd.DataFrame(tornado)
    base_val = tornado_df["base"].iloc[0] if "base" in tornado_df.columns else data["es95"]

    fig_tornado = go.Figure()
    for _, row in tornado_df.iterrows():
        fig_tornado.add_trace(go.Bar(
            y=[row["assumption"]],
            x=[row["high"] - base_val],
            base=[base_val],
            orientation="h",
            marker_color="#ef4444",
            name="High",
            showlegend=False,
        ))
        fig_tornado.add_trace(go.Bar(
            y=[row["assumption"]],
            x=[row["low"] - base_val],
            base=[base_val],
            orientation="h",
            marker_color="#3b82f6",
            name="Low",
            showlegend=False,
        ))

    fig_tornado.update_layout(
        height=50 + 40 * len(tornado),
        barmode="overlay",
        xaxis_title="ES95 (INR)",
        yaxis_title="Assumption",
    )
    st.plotly_chart(fig_tornado, use_container_width=True)
    ui.caption(
        "One-at-a-time variation of each shock assumption on ES95. "
        "Blue = low end of range; red = high end. Sorted by impact width."
    )

# ---------- mitigation panel --------------------------------------------------
mitigation = data.get("mitigation", {})
if mitigation:
    st.subheader("🛡️ Mitigation: Restructure Top 10% Most Stressed")
    mit_cols = st.columns(3)
    with mit_cols[0]:
        ui.kpi("Borrowers Restructured", str(mitigation["restructured_count"]))
    with mit_cols[1]:
        ui.kpi("Loss Before", ui.inr(mitigation["loss_before_inr"]))
    with mit_cols[2]:
        ui.kpi("Loss Saved", ui.inr(mitigation["loss_saved_inr"]))

    ui.caption(
        "Top 10% borrowers by stressed PD are restructured (via core.structuring API or "
        "30% PD reduction fallback). Loss saved = loss_before − loss_after in INR."
    )

# ---------- contagion network (static plotly fallback) ------------------------
st.subheader("🌐 Supplier-Buyer Network (Top Edges)")
graph_path = pathlib.Path("data/graph.parquet")
if graph_path.exists():
    g_df = pd.read_parquet(graph_path)
    # Show top 50 edges by revenue_share
    top_edges = g_df.nlargest(50, "revenue_share")

    nodes = list(set(top_edges["src"].tolist() + top_edges["dst"].tolist()))
    node_idx = {n: i for i, n in enumerate(nodes)}
    n = len(nodes)

    # Simple circular layout
    import math
    angles = [2 * math.pi * i / n for i in range(n)]
    x_pos = [math.cos(a) for a in angles]
    y_pos = [math.sin(a) for a in angles]

    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    for _, row in top_edges.iterrows():
        si = node_idx[row["src"]]
        di = node_idx[row["dst"]]
        edge_x.extend([x_pos[si], x_pos[di], None])
        edge_y.extend([y_pos[si], y_pos[di], None])

    fig_net = go.Figure()
    fig_net.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line={"width": 0.5, "color": "#94a3b8"}, hoverinfo="none",
    ))
    fig_net.add_trace(go.Scatter(
        x=x_pos, y=y_pos, mode="markers+text",
        marker={"size": 8, "color": "#0f766e"},
        text=[n[:10] for n in nodes],
        textposition="top center",
        textfont={"size": 8},
        hoverinfo="text",
    ))
    fig_net.update_layout(
        height=400, showlegend=False,
        xaxis={"visible": False}, yaxis={"visible": False},
    )
    st.plotly_chart(fig_net, use_container_width=True)
    ui.caption(
        f"Top 50 supplier-buyer edges by revenue share. Total edges in graph: {len(g_df)}."
    )
else:
    st.info("Graph not yet built. Run `python run_all.py` first.")
