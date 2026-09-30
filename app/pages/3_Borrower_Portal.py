"""OWNER: M4. Page: Borrower Portal. UI only: call `core` functions; read artifacts via core.paths."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import streamlit as st

import core
from app.components import ui
from core.reference import MEENA_ID

ui.page_header("Borrower Portal", "plain-language path to yes", "MSME owner")

lang = st.selectbox("Language", ["en", "hi", "ta", "mr"])
doc = ui.safe_call(core.make_letter, MEENA_ID, lang)
if doc:
    ui.stub_banner(None)
    st.download_button("Download letter", doc, file_name=f"letter_{lang}.html", mime="text/html")
