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
st.subheader("Meet Meena")
st.write(f"{MEENA['business']} - {MEENA['sector']} - thin credit file, seasonal cash flows.")
st.write("Use the sidebar to open the pages. Data shown is STUB until the pipeline artifacts exist.")
have = artifact_path("metrics.json").exists()
st.info("Artifacts found: real results are loaded." if have else "No artifacts yet: running on stubs.")
