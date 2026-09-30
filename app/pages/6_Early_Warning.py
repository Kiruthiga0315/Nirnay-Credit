"""OWNER: M3. Page: Early Warning. UI only: call `core` functions; read artifacts via core.paths."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import streamlit as st

import core
from app.components import ui

ui.page_header("Early Warning", "watchlist and lead time", "Risk Head")

rows = ui.safe_call(core.watchlist, 25)
if rows:
    ui.stub_banner(None)
    st.dataframe(rows)
    ui.caption("borrowers ranked by monthly default hazard, with a suggested action.")
