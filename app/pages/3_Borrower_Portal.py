"""OWNER: M4. Page: Borrower Portal. UI only: call `core` functions; read artifacts via core.paths."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import streamlit as st

import core
from app.components import ui
from core.reference import MEENA_ID, TEST_BORROWER_IDS

ui.page_header("Borrower Portal", "plain-language path to yes", "MSME owner")

bid = st.selectbox("Borrower", TEST_BORROWER_IDS, index=TEST_BORROWER_IDS.index(MEENA_ID))

ui.section("Your Application Status", "how we evaluated your business and what you can do next")

with ui.card():
    st.write("We have carefully reviewed your application. While we cannot offer the standard terms at this moment, here is a path to get your loan approved.")

ui.section("Download Your Letter", "official communication available in multiple languages")
lang = st.selectbox("Language", ["en", "hi", "ta", "mr"])
doc = ui.safe_call(core.make_letter, bid, lang)
if doc:
    ui.stub_banner(None)
    with ui.card():
        ui.download_button(f"Download Letter ({lang.upper()})", doc, file_name=f"letter_{bid}_{lang}.html", mime="text/html")
