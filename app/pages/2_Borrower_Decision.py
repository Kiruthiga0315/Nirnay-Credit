"""OWNER: M4. Page: Borrower Decision. UI only: call `core` functions; read artifacts via core.paths."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import streamlit as st

import core
from app.components import ui
from core.reference import MEENA_ID, TEST_BORROWER_IDS

ui.page_header("Borrower Decision", "PD, reasons, recourse, structured loan", "Credit Officer")

bid = st.selectbox("Borrower", TEST_BORROWER_IDS, index=TEST_BORROWER_IDS.index(MEENA_ID))
s = ui.safe_call(core.score, bid)
if s:
    ui.stub_banner(s.get("model_version"))
    
    c1, c2 = st.columns([1, 2])
    with c1:
        ui.section("Risk Assessment", "calibrated probability of default")
        with ui.card():
            ui.pd_gauge(s["pd"], threshold=0.5)
            ui.kpi_row([("Data confidence", f"{s['data_confidence']}/100")])
    with c2:
        ui.section("Key Drivers", "top factors driving the decision")
        with ui.card():
            ui.reason_list(s["reasons"])
            
    rec = ui.safe_call(core.recourse, bid)
    if rec:
        ui.section("Path to Yes", "actionable steps to lower risk")
        with ui.card():
            st.write(f"**Target PD:** {rec['new_pd']:.1%} (Current: {s['pd']:.1%}) in approx {rec['months']:.0f} months")
            for action in rec.get("actions", []):
                st.write(f"- Change **{action['label']}** from {action['current']} to {action['target']} {action['unit']} (Cost: {action['cost']})")

    plan = ui.safe_call(core.structure, bid)
    if plan:
        ui.section("Structured Repayment", "matching instalments to cash flow")
        with ui.card():
            st.line_chart({"P10 cash available": plan["p10_band"], "Instalment": plan["schedule"]})
            ui.caption("instalments sit under the P10 cash-flow band, so repayment is easier in lean months.")
            
    cam = ui.safe_call(core.make_cam, bid)
    if cam:
        ui.section("Export", "generate formal documentation")
        ui.download_button("Download CAM (PDF/HTML)", cam, file_name=f"cam_{bid}.html", mime="text/html")
