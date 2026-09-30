"""OWNER: M4. Page: Portfolio Command Center. UI only: call `core` functions; read artifacts via core.paths."""
import pathlib
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from app.components import ui
from app.components.routing import route_borrower
from core.paths import load_json

ui.page_header("Portfolio Command Center", "scoreboard, routing, economics", "Risk Head")

# ---------------------------------------------------------------------------
# Load scoreboard.json
# ---------------------------------------------------------------------------
scoreboard = load_json("scoreboard.json")

is_stub = False
if not scoreboard:
    is_stub = True
    scoreboard = {
      "model_version": "stub-v1",
      "iso_loss": {
        "target_loss_rate": 0.08,
        "approvals": {"legacy": 400, "approved_only": 420, "inferred": 450, "oracle": 500}
      },
      "iso_approval": {
        "target_n_approved": 400,
        "loss_rates": {"legacy": 0.08, "approved_only": 0.075, "inferred": 0.07, "oracle": 0.065}
      },
      "extra_approvals_at_equal_loss": 50
    }

ui.stub_banner(scoreboard.get("model_version", "stub"))

# ---------------------------------------------------------------------------
# T1: Scoreboard Toggle
# ---------------------------------------------------------------------------
ui.section("Scoreboard", "Legacy vs Approved-only vs Ours vs Oracle")

toggle = st.radio("View", ["ISO-LOSS (equal risk, more approvals)", "ISO-APPROVAL (same approvals, lower risk)"], horizontal=True)

col1, col2, col3, col4 = st.columns(4)

if "LOSS" in toggle:
    target_loss = scoreboard["iso_loss"]["target_loss_rate"]
    apps = scoreboard["iso_loss"]["approvals"]
    
    st.markdown(f"**Target Loss Rate:** {target_loss:.2%}")
    with col1:
        st.metric("Legacy", apps["legacy"])
    with col2:
        st.metric("Approved-only", apps["approved_only"], delta=int(apps["approved_only"]-apps["legacy"]))
    with col3:
        st.metric("Ours (Inferred)", apps["inferred"], delta=int(apps["inferred"]-apps["legacy"]))
    with col4:
        st.metric("Oracle", apps["oracle"], delta=int(apps["oracle"]-apps["legacy"]))
        
    st.metric("Extra approvals at equal loss", scoreboard.get("extra_approvals_at_equal_loss", apps["inferred"] - apps["legacy"]))
    current_approvals = apps["inferred"]
    current_loss_rate = target_loss
else:
    target_apps = scoreboard["iso_approval"]["target_n_approved"]
    loss = scoreboard["iso_approval"]["loss_rates"]
    
    st.markdown(f"**Target Approvals:** {target_apps}")
    with col1:
        st.metric("Legacy", f"{loss['legacy']:.2%}")
    with col2:
        st.metric("Approved-only", f"{loss['approved_only']:.2%}", delta=f"{loss['approved_only']-loss['legacy']:.2%}", delta_color="inverse")
    with col3:
        st.metric("Ours (Inferred)", f"{loss['inferred']:.2%}", delta=f"{loss['inferred']-loss['legacy']:.2%}", delta_color="inverse")
    with col4:
        st.metric("Oracle", f"{loss['oracle']:.2%}", delta=f"{loss['oracle']-loss['legacy']:.2%}", delta_color="inverse")
        
    current_approvals = target_apps
    current_loss_rate = loss["inferred"]

ui.caption("model performance compared to the legacy policy and oracle baselines.")

st.divider()

# ---------------------------------------------------------------------------
# T3: Economics Panel
# ---------------------------------------------------------------------------
ui.section("Portfolio Economics", "approvals × ticket × margin − EL − opex")

col_sl1, col_sl2, col_sl3 = st.columns(3)
with col_sl1:
    lgd = st.slider("Loss Given Default (LGD)", 0.0, 1.0, 0.45, 0.05)
with col_sl2:
    margin = st.slider("Margin", 0.0, 0.3, 0.10, 0.01)
with col_sl3:
    ticket = st.slider("Ticket Size (INR)", 200000, 2500000, 500000, 100000)

opex = 0  # Assuming 0 as per baseline

el = current_approvals * current_loss_rate * lgd * ticket
revenue = current_approvals * ticket * margin
profit = revenue - el - opex

with ui.card():
    ui.kpi_row([
        ("Total Approvals", str(current_approvals)),
        ("Expected Revenue", ui.inr(revenue)),
        ("Expected Loss (EL)", ui.inr(el)),
        ("Expected Profit", ui.inr(profit))
    ])

ui.caption(f"assumptions: LGD={lgd:.0%}, margin={margin:.0%}, ticket={ui.inr(ticket)}. EL = approvals × loss rate × LGD × ticket.")

st.divider()

# ---------------------------------------------------------------------------
# T2: Routing Table
# ---------------------------------------------------------------------------
ui.section("Routing Table", "rule layer over score + DSCR feasibility + data_confidence")

st.markdown("**Rules defined in `app.components.routing.route_borrower` (Thresholds visible below)**")
st.code(route_borrower.__doc__, language="markdown")

with ui.card():
    st.markdown("**Per-segment outcome share (illustrative)**")
    data = {
        "Segment": ["fast-track", "manual review", "structured repayment", "decline-with-recourse"],
        "Approvals %": ["40%", "30%", "20%", "0%"],
        "Expected Loss %": ["2.1%", "6.5%", "9.8%", "N/A"]
    }
    st.table(pd.DataFrame(data))

ui.caption("shows how borrowers fall into distinct operational paths and their aggregate risk.")
