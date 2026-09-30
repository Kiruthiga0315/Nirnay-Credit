"""OWNER: M4. Page: Portfolio Command Center. UI only: call `core` functions; read artifacts via core.paths."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import streamlit as st

import core
from app.components import ui

ui.page_header("Portfolio Command Center", "scoreboard, routing, economics", "Risk Head")

res = ui.safe_call(core.optimize, {})
if res:
    ui.stub_banner(None)
    c1, c2, c3 = st.columns(3)
    with c1:
        ui.kpi("Expected profit", ui.inr(res["expected_profit"]))
    with c2:
        ui.kpi("Expected loss", ui.inr(res["expected_loss"]))
    with c3:
        ui.kpi("Approved", str(len(res["approved_ids"])))
    ui.caption("stub numbers; the real scoreboard compares Legacy vs Ours at the same loss rate.")
