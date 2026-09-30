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
    ui.stub_banner(s["model_version"])
    c1, c2 = st.columns(2)
    with c1:
        ui.kpi("Probability of default", f"{s['pd']:.1%}")
    with c2:
        ui.kpi("Data confidence", f"{s['data_confidence']}/100")
    for r in s["reasons"]:
        st.write(f"- {r['text']}")
    rec = ui.safe_call(core.recourse, bid)
    if rec:
        st.write(f"Path to yes: PD {s['pd']:.1%} -> {rec['new_pd']:.1%} in about {rec['months']:.0f} months")
    plan = ui.safe_call(core.structure, bid)
    if plan:
        st.line_chart({"P10 cash available": plan["p10_band"], "Instalment": plan["schedule"]})
        ui.caption("instalments sit under the P10 cash-flow band, so repayment is easier in lean months.")
