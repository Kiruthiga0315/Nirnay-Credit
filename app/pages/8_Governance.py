"""OWNER: M3. Page: Governance and Trust. UI only: call `core` functions; read artifacts via core.paths."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import streamlit as st

from app.components import ui
from core import governance
from core.reference import MEENA_ID

ui.page_header("Governance and Trust", "FREE-AI map, ledger, consent, gaming lab", "Regulator")

ui.stub_banner(None)
st.subheader("Decision ledger")
st.dataframe(governance.ledger(10))
st.subheader("Consent artefact")
st.json(governance.consent_artifact(MEENA_ID))
