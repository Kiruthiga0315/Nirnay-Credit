"""OWNER: M4. Entry point: streamlit run app/Home.py"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import streamlit as st

from app.components import ui
from core.paths import artifact_path
from core.reference import MEENA

ui.page_header("PS12 - Governed MSME Lending Cockpit",
               "every application gets a reason, a route to yes, a fair price and a stress-tested loss",
               "All")

ui.section("Meet the Borrower", "our reference persona to understand the problem")
with ui.card():
    ui.persona_card(MEENA)
    st.write("Use the sidebar to explore how the lending cockpit manages this application. The pipeline evaluates probability of default, recourse, structured repayment, fairness and stress.")

ui.section("System Status", "pipeline artifact readiness")
have = artifact_path("metrics.json").exists()
if have:
    st.success("Artifacts found: real results are loaded.")
else:
    st.info("No artifacts yet: running on stubs.")

