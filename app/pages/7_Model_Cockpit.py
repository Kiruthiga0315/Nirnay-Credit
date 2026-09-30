"""OWNER: M1. Page: Model Cockpit. UI only: call `core` functions; read artifacts via core.paths."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import streamlit as st

from app.components import ui
from core.paths import load_metrics

ui.page_header("Model Cockpit", "ROC, KS, calibration, ablation, external validity", "Data Science")

m = load_metrics()
if m:
    st.json(m)
else:
    ui.stub_banner(None)
    st.info("No metrics yet. Run: python run_all.py")
