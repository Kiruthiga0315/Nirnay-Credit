"""OWNER: M4. Page 2: Borrower Decision Cockpit.

Panels and their core calls:
- Borrower Picker          : core.reference.TEST_BORROWER_IDS / resolve
- PD Gauge + Band          : core.score  -> ScoreResult
- Data-Confidence Badge    : core.score  -> ScoreResult.data_confidence
- Key Reasons              : core.score  -> ScoreResult.reasons  (top 3)
- Recourse Card            : core.recourse -> RecourseResult
  (levers, total cost, max months, valid_until_model stamp)
- Schedule vs P10 Chart    : core.structure -> StructureResult
  (target_dscr from slider; re-called on every slider move)
- Live What-if Sliders     : core.score on a modified borrower copy
  (receivable_days, gst_filing_regularity, cheque_bounces_6m,
   invoice_digitisation_share) -- only verifiable levers, no gameable
- CAM Export               : core.make_cam -> bytes

UI rules: INR everywhere; every chart has a caption; STUB banner while
model_version starts with "stub"; friendly empty states via ui.safe_call;
no stack traces; st.cache_data for artifact loads.
"""
from __future__ import annotations

import copy
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import plotly.graph_objects as go
import streamlit as st

import core
from app.components import ui
from app.components.journey import SAFE_BORROWERS
from core.reference import MEENA, MEENA_ID, TEST_BORROWER_IDS, resolve

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
ui.page_header(
    "Borrower Decision",
    "PD - reasons - recourse - structured loan - what-if",
    "Credit Officer",
)

# ---------------------------------------------------------------------------
# Cached artifact loaders -- avoid re-calling core on every widget interaction
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def _cached_score(bid: str) -> dict:
    return core.score(bid)


@st.cache_data(show_spinner=False)
def _cached_recourse(bid: str) -> dict:
    return core.recourse(bid)


@st.cache_data(show_spinner=False)
def _cached_structure(bid: str, target_dscr: float) -> dict:
    return core.structure(bid, target_dscr=target_dscr)


@st.cache_data(show_spinner=False)
def _cached_cam(bid: str) -> bytes | None:
    return core.make_cam(bid)


# What-if re-score does NOT use cache because the borrower dict changes each
# slider interaction.  It is cheap (stub < 1 ms; budget < 0.2 s per contract).
def _rescore_whatif(base: dict, overrides: dict) -> dict:
    modified = copy.deepcopy(base)
    modified.update(overrides)
    return core.score(modified)


# ---------------------------------------------------------------------------
# Sidebar: borrower picker
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("---")
    st.subheader("Quick Presets")
    for _preset in SAFE_BORROWERS:
        if st.button(
            _preset["id"],
            key=f"dec_preset_{_preset['id']}",
            help=_preset["label"],
            use_container_width=True,
        ):
            st.session_state["selected_borrower"] = _preset["id"]

    st.markdown("---")
    st.subheader("Select Borrower")
    _default_bid = st.session_state.get("selected_borrower", MEENA_ID)
    if _default_bid not in TEST_BORROWER_IDS:
        _default_bid = MEENA_ID
    bid = st.selectbox(
        "Borrower ID",
        TEST_BORROWER_IDS,
        index=TEST_BORROWER_IDS.index(_default_bid),
        help="20 test borrowers (MSME-00001 to MSME-00020). Meena is MSME-00001.",
        key="decision_bid",
    )
    # Resolve the base feature dict for this borrower (used for what-if)
    b_base = resolve(bid)
    # For Meena use the full fixture; for others synthesise sensible defaults from MEENA
    if not b_base.get("receivable_days"):
        b_base = {**MEENA, **b_base}

    st.caption(f"Business: {b_base.get('business', 'N/A')}")
    st.caption(f"Sector: {b_base.get('sector', 'N/A')}")

# ---------------------------------------------------------------------------
# SECTION 1: Risk Assessment -- core.score
# ---------------------------------------------------------------------------
ui.section("Risk Assessment", "calibrated probability of default (12-month horizon)")

s = ui.safe_call(_cached_score, bid)

if s:
    ui.stub_banner(s.get("model_version"))

    col_gauge, col_reasons, col_badge = st.columns([1, 2, 1])

    with col_gauge:
        with ui.card():
            st.markdown("**PD Gauge vs Approval Threshold**")
            ui.pd_gauge(s["pd"], threshold=0.10)
            band_color = {"low": "green", "medium": "orange", "high": "red"}.get(
                s.get("pd_band", "high"), "grey"
            )
            st.markdown(
                f"**{s['pd_band'].upper()} risk** "
                f"-- PD {s['pd']:.1%} "
                f"({'APPROVED' if s['pd'] < 0.10 else 'DECLINED'} at policy threshold 10%)"
            )

    with col_reasons:
        with ui.card():
            st.markdown("**Key Drivers (top 3)**")
            ui.reason_list(s["reasons"])
            ui.caption(
                "impact > 0 raises default risk. "
                "These are decision aids under our documented assumptions, not guarantees."
            )

    with col_badge:
        with ui.card():
            dc = s["data_confidence"]
            colour = "#16a34a" if dc >= 80 else "#b45309" if dc >= 50 else "#b91c1c"
            st.markdown(
                f"""
                <div style="text-align:center; padding: 1rem 0;">
                  <div style="font-size:2.2rem; font-weight:bold; color:{colour};">{dc}</div>
                  <div style="font-size:0.85rem; color:#475569;">Data Confidence<br>/100</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            ui.caption(
                "cross-source reconciliation of GST, bank and UPI signals, "
                "measured and mitigated."
            )
            st.markdown(
                f"**Model version:** `{s.get('model_version', 'unknown')}`  \n"
                f"_{'STUB -- illustrative result' if str(s.get('model_version','')).startswith('stub') else 'real model'}_"
            )

else:
    st.info("Risk Assessment unavailable -- try another borrower.")

st.divider()

# ---------------------------------------------------------------------------
# SECTION 2: Recourse Card -- core.recourse
# ---------------------------------------------------------------------------
ui.section(
    "Path to Yes",
    "verifiable levers only; gameable and immutable features are never offered as advice.",
)

rec = ui.safe_call(_cached_recourse, bid)

if rec:
    current_pd = s["pd"] if s else None
    new_pd = rec["new_pd"]

    col_rec_kpis, col_rec_actions = st.columns([1, 2])

    with col_rec_kpis:
        with ui.card():
            st.metric(
                "New PD after recourse",
                f"{new_pd:.1%}",
                delta=f"{new_pd - current_pd:.1%}" if current_pd is not None else None,
                delta_color="inverse",
            )
            st.metric("Total effort (relative cost)", f"{rec['cost']:.1f}")
            st.metric("Months to achieve", f"{rec['months']:.0f} months")
            ui.caption(
                f"valid until model version `{rec['valid_until_model']}`. "
                "Recalculate if the model is retrained."
            )

    with col_rec_actions:
        with ui.card():
            st.markdown("**Recommended lever changes**")
            if rec.get("actions"):
                for action in rec["actions"]:
                    direction = (
                        "reduce"
                        if action["target"] < action["current"]
                        else "increase"
                    )
                    st.markdown(
                        f"**{action['label']}** -- {direction} from "
                        f"`{action['current']}` to `{action['target']}` {action['unit']}  \n"
                        f"&nbsp;&nbsp;&nbsp;Effort: {action['cost']:.1f} -- "
                        f"~{action['months']:.0f} month(s)"
                    )
            else:
                st.info("No recourse actions available for this borrower.")
            ui.caption(
                "illustrative parameters under our documented assumptions. "
                "Costs are relative feasibility scores, not INR amounts."
            )
else:
    st.info("Recourse unavailable for this borrower.")

st.divider()

# ---------------------------------------------------------------------------
# SECTION 3: Structured Repayment with DSCR slider -- core.structure
# ---------------------------------------------------------------------------
ui.section(
    "Structured Repayment",
    "DSCR-matched instalments sit under the P10 cash-flow band; defaults fall in lean months.",
)

target_dscr = st.slider(
    "Target DSCR (higher means smaller instalments, lower default risk)",
    min_value=1.00,
    max_value=2.00,
    value=1.25,
    step=0.05,
    format="%.2f",
    help="Debt Service Coverage Ratio: each instalment <= P10 cash / DSCR. Slide to explore.",
)

plan = ui.safe_call(_cached_structure, bid, target_dscr)

if plan:
    tenor = plan["tenor_months"]
    months_labels = [f"M{i+1}" for i in range(tenor)]
    schedule = plan["schedule"]
    p10 = plan["p10_band"]

    fig_sched = go.Figure()
    fig_sched.add_trace(
        go.Scatter(
            x=months_labels,
            y=p10,
            name="P10 cash available",
            line={"color": "#0F766E", "dash": "dot"},
            fill="tozeroy",
            fillcolor="rgba(15,118,110,0.08)",
        )
    )
    fig_sched.add_trace(
        go.Scatter(
            x=months_labels,
            y=schedule,
            name="Instalment (DSCR-matched)",
            line={"color": "#B91C1C"},
            mode="lines+markers",
        )
    )
    fig_sched.update_layout(
        height=320,
        margin={"l": 40, "r": 20, "t": 30, "b": 30},
        legend={"orientation": "h", "y": 1.08},
        yaxis={"tickformat": ",.0f", "title": "INR"},
        xaxis={"title": "Month"},
    )
    st.plotly_chart(fig_sched, use_container_width=True)
    ui.caption(
        "instalments (red) sit under the P10 cash-flow band (green shade); "
        f"DSCR-matched default rate {plan['default_matched']:.1%} vs flat-EMI "
        f"rate {plan['default_flat']:.1%}. Adjust the DSCR slider above to explore trade-offs."
    )

    with ui.card():
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Target DSCR", f"{plan['target_dscr']:.2f}")
        with c2:
            st.metric(
                "Default rate (matched)",
                f"{plan['default_matched']:.1%}",
                delta=f"{plan['default_matched'] - plan['default_flat']:.1%}",
                delta_color="inverse",
            )
        with c3:
            st.metric("Default rate (flat EMI)", f"{plan['default_flat']:.1%}")
else:
    st.info("Structured repayment unavailable for this borrower.")

st.divider()

# ---------------------------------------------------------------------------
# SECTION 4: Live What-if Sliders -- calls core.score on modified borrower copy
# (verifiable levers only; no gameable / immutable feature ever offered)
# ---------------------------------------------------------------------------
ui.section(
    "Live What-if Analysis",
    "move verifiable levers to see how the decision would change -- re-scores in under 1 second.",
)

with st.expander("Adjust verifiable levers", expanded=True):
    st.caption(
        "Gameable (UPI inflow, bank balance) and immutable (bureau score, vintage) levers "
        "are intentionally excluded. Only levers the borrower can change AND the lender can verify."
    )

    wi_col1, wi_col2 = st.columns(2)

    with wi_col1:
        wi_recv = st.slider(
            "Receivable days",
            min_value=15,
            max_value=150,
            value=int(b_base.get("receivable_days", 78)),
            step=5,
            help="Days customers take to pay. Lower is better.",
        )
        wi_gst = st.slider(
            "GST filing regularity (share)",
            min_value=0.0,
            max_value=1.0,
            value=float(b_base.get("gst_filing_regularity", 0.92)),
            step=0.05,
            format="%.2f",
            help="Proportion of last 12 months with on-time GST filing.",
        )

    with wi_col2:
        wi_bounce = st.slider(
            "Cheque bounces (last 6m)",
            min_value=0,
            max_value=10,
            value=int(b_base.get("cheque_bounces_6m", 1)),
            step=1,
            help="Number of cheque bounces in the last 6 months.",
        )
        wi_inv = st.slider(
            "Invoice digitisation share",
            min_value=0.0,
            max_value=1.0,
            value=float(b_base.get("invoice_digitisation_share", 0.35)),
            step=0.05,
            format="%.2f",
            help="Fraction of invoices that are digital/e-invoiced.",
        )

    overrides = {
        "receivable_days": wi_recv,
        "gst_filing_regularity": wi_gst,
        "cheque_bounces_6m": wi_bounce,
        "invoice_digitisation_share": wi_inv,
    }

    s_wi = ui.safe_call(_rescore_whatif, b_base, overrides)

    if s_wi and s:
        delta_pd = s_wi["pd"] - s["pd"]
        wi_c1, wi_c2, wi_c3 = st.columns(3)
        with wi_c1:
            st.metric("Original PD", f"{s['pd']:.1%}")
        with wi_c2:
            st.metric(
                "What-if PD",
                f"{s_wi['pd']:.1%}",
                delta=f"{delta_pd:+.1%}",
                delta_color="inverse",
                help="PD after applying the lever changes above.",
            )
        with wi_c3:
            original_approved = s["pd"] < 0.10
            whatif_approved = s_wi["pd"] < 0.10
            if not original_approved and whatif_approved:
                st.success("Decision FLIPS to APPROVED")
            elif original_approved and not whatif_approved:
                st.error("Decision FLIPS to DECLINED")
            else:
                status = "APPROVED" if whatif_approved else "DECLINED"
                st.info(f"Decision unchanged: {status}")

        ui.caption(
            "what-if PD uses the same model with lever values overridden; "
            "derived features are recomputed automatically. "
            "This is a decision aid under our documented assumptions, not a guarantee."
        )
    elif not s:
        st.info("Base score unavailable -- cannot compute what-if.")

st.divider()

# ---------------------------------------------------------------------------
# SECTION 5: CAM Export -- core.make_cam
# ---------------------------------------------------------------------------
ui.section(
    "Export",
    "generate the Credit Appraisal Memo for the credit file.",
)

cam = ui.safe_call(_cached_cam, bid)
if cam:
    with ui.card():
        st.markdown(
            "Download the **Credit Appraisal Memo** (HTML, printable). "
            "The CAM includes borrower profile, PD, reasons, structured schedule, "
            "fairness note, and officer decision box."
        )
        ui.download_button(
            "Download CAM (HTML)",
            cam,
            file_name=f"cam_{bid}.html",
            mime="text/html",
        )
        st.markdown("---")
        if st.button("Challenge this decision", type="primary"):
            # core.governance doesn't have a public helper for this yet, so we show a stub.
            st.success(f"Challenge for {bid} logged to decision ledger (STUB).")
else:
    st.info("CAM generation unavailable -- try another borrower.")
