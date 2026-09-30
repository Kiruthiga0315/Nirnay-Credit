"""OWNER: M2. Page: Fairness Studio. UI only: call `core` functions; read artifacts via core.paths."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import streamlit as st

import core
from app.components import ui

ui.page_header("Fairness Studio", "metrics, frontier, proxy audit", "Regulator / Risk Head")

rep = ui.safe_call(core.fairness_report, None)
if rep:
    ui.stub_banner(None)
    st.dataframe(rep["by_group"])
    ui.caption("approval and true-positive rates by group; gaps are measured, then mitigated under stated definitions.")
