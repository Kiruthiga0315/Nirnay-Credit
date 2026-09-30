"""OWNER: M3. Page: Governance and Trust. UI only: call `core` functions; read artifacts via core.paths."""
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import streamlit as st

from app.components import ui
from core import governance
from core.paths import load_json
from core.reference import MEENA_ID

ui.page_header("Governance and Trust", "FREE-AI map, ledger, consent, gaming lab", "Regulator")

st.markdown("### FREE-AI Advisory Guidance Map")
st.info("We map our governance practices to advisory guidance (e.g. FREE-AI principles); we do not claim compliance. TODO(verify) exact wording against the RBI report.")
free_ai_data = [
    {"Principle": "Fairness", "Implementation": "Group fairness checks on gender and location (Phase 2), unbiased legacy policy baseline."},
    {"Principle": "Reliability", "Implementation": "Monotone constraints, data confidence scoring (0-100), out-of-time evaluation."},
    {"Principle": "Explainability", "Implementation": "SHAP reason codes, ledger inputs hash, accessible UI for dispute."},
    {"Principle": "Ethics", "Implementation": "Immutable append-only decision ledger, human-in-the-loop overrides."},
    {"Principle": "Accountability", "Implementation": "Model cards, versioned artifacts, gaming lab testing before deployment."}
]
st.table(pd.DataFrame(free_ai_data))
st.caption("Figure 8.1: Mapping of FREE-AI themes to implementation features.")

st.subheader("Decision Ledger")
ledger_entries = governance.ledger(50)
if ledger_entries:
    df_ledger = pd.DataFrame(ledger_entries)
    f_decision = st.selectbox("Filter by Decision", ["All", "approve", "refer", "reject"])
    if f_decision != "All":
        df_ledger = df_ledger[df_ledger["decision"] == f_decision]
    st.dataframe(df_ledger, use_container_width=True)
    st.caption("Figure 8.2: Immutable append-only decision ledger with hash stability.")
else:
    st.write("No ledger entries found. Run `python run_all.py`.")

st.subheader("Consent Artefact (MOCK)")
consent = governance.consent_artifact(MEENA_ID)
with st.expander(f"Consent Details: {MEENA_ID}"):
    st.json(consent)
st.caption("Figure 8.3: Mocked Account Aggregator consent artefact.")

st.subheader("Gaming Lab (Vulnerability Testing)")
try:
    gaming_lab = load_json("gaming_lab.json")
    for attack, results in gaming_lab.items():
        with st.expander(f"Attack Simulation: {attack}"):
            col1, col2 = st.columns(2)
            col1.metric("Flagged Firms (Before)", results["flagged_before"])
            col1.metric("AUC (Before)", f"{results['auc_before']:.4f}")
            col2.metric("Flagged Firms (After)", results["flagged_after"])
            col2.metric("AUC (After)", f"{results['auc_after']:.4f}")
    st.caption("Figure 8.4: Vulnerability testing against gaming attacks using cycle detection and z-scores.")
except Exception:
    st.info("Run `python run_all.py --smoke` to generate gaming lab results.")

st.subheader("Model Card")
model_card_path = pathlib.Path("docs/model_card.md")
if model_card_path.exists():
    with open(model_card_path, encoding="utf-8") as f:
        st.download_button("Download Model Card", f.read(), file_name="model_card.md")
    st.caption("Figure 8.5: Standardised model documentation for accountability.")
else:
    st.write("Model card not generated yet.")
