"""OWNER: M4. Page: Portfolio Command Center. UI only: call `core` functions; read artifacts via core.paths.

Policy Optimizer (F8): four sliders (loss cap, budget, sector cap, inclusion floor)
call core.optimize and show approved count, expected profit, EL, fairness gap and
the price of inclusion in INR (under documented assumptions).
"""
import pathlib
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import core
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
# Scoreboard Toggle
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
# Economics Panel
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
# Policy Optimizer sliders (F8)
# ---------------------------------------------------------------------------
ui.section("Policy Optimizer", "adjust constraints to see the price of inclusion in ₹")
st.caption(
    "How to read this: move the sliders to change portfolio policy. "
    "The optimizer maximises expected profit subject to your constraints "
    "(under documented stub assumptions). 'Price of inclusion' = profit lost "
    "by raising the inclusion floor."
)

with ui.card():
    col_l, col_r = st.columns(2)
    with col_l:
        budget = st.slider(
            "Budget (₹ lakhs)",
            min_value=50,
            max_value=500,
            value=200,
            step=10,
            key="opt_budget",
            help="Maximum total exposure the portfolio can hold.",
        )
        loss_cap = st.slider(
            "Loss cap (₹ lakhs)",
            min_value=5,
            max_value=100,
            value=15,
            step=5,
            key="opt_loss_cap",
            help="Maximum total expected loss across the portfolio.",
        )
    with col_r:
        inclusion_floor = st.slider(
            "Inclusion floor (%)",
            min_value=0,
            max_value=70,
            value=30,
            step=5,
            key="opt_inclusion",
            help="Minimum approval share for women-led and rural firms.",
        )
        sector_cap = st.slider(
            "Sector cap (%)",
            min_value=20,
            max_value=100,
            value=40,
            step=5,
            key="opt_sector_cap",
            help="Maximum share any single sector can occupy in the approved portfolio.",
        )

policy_params = {
    "budget": budget * 100_000,         # lakhs -> INR
    "loss_cap": loss_cap * 100_000,     # lakhs -> INR
    "inclusion_floor": inclusion_floor / 100.0,
    "sector_cap": sector_cap / 100.0,
}

res = ui.safe_call(core.optimize, policy_params)
if res:
    ui.stub_banner(None)

    # Compute price of inclusion: profit at current floor vs floor=0
    res_no_floor = ui.safe_call(core.optimize, {**policy_params, "inclusion_floor": 0.0})
    price_of_inclusion = 0.0
    if res_no_floor:
        price_of_inclusion = max(0.0, res_no_floor["expected_profit"] - res["expected_profit"])

    st.markdown("#### Optimised Portfolio")
    ui.kpi_row([
        ("Approved", str(len(res["approved_ids"]))),
        ("Expected profit", ui.inr(res["expected_profit"])),
        ("Expected loss", ui.inr(res["expected_loss"])),
        ("Exposure", ui.inr(res["exposure"])),
    ])
    st.markdown("")

    col_fg, col_pi = st.columns(2)
    with col_fg:
        st.markdown("**Fairness gap** (approval share minus overall rate)")
        fg = res["fairness_gap"]
        for group, gap in fg.items():
            colour = "green" if gap >= 0 else "red"
            st.markdown(
                f"- **{group.replace('_', ' ').title()}**: "
                f":{colour}[{gap:+.1%}]"
            )
    with col_pi:
        st.markdown("**Price of inclusion**")
        st.metric(
            label=f"Profit cost of {inclusion_floor}% inclusion floor",
            value=ui.inr(price_of_inclusion),
            help="Profit difference vs no inclusion constraint (under documented assumptions).",
        )

    ui.caption(
        "numbers under documented stub assumptions; real optimizer runs on M2's LP relaxation. "
        "Fairness gap = protected-group approval share minus overall approval rate."
    )

st.divider()

# ---------------------------------------------------------------------------
# Routing Table
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
