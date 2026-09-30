"""OWNER: M3. Page: Stress and Contagion. UI only: call `core` functions; read artifacts via core.paths."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import streamlit as st

import core
from app.components import ui
from core.stress import SCENARIO_IDS

ui.page_header("Stress and Contagion", "named replays, contagion, Monte Carlo", "Risk Head")

sc = st.selectbox("Scenario", SCENARIO_IDS)
res = ui.safe_call(core.stress, sc)
if res:
    ui.stub_banner(None)
    c1, c2 = st.columns(2)
    with c1:
        ui.kpi("Expected loss", ui.inr(res["expected_loss"]))
    with c2:
        ui.kpi("Tail loss (ES95)", ui.inr(res["es95"]))
    st.bar_chart(res["segment_losses"])
    ui.caption("loss by sector under the selected shock; illustrative parameters.")
