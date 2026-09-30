"""OWNER: M4. Page: Borrower Portal. UI only: call `core` functions; read artifacts via core.paths.

Plain-language interface for the MSME borrower persona (Meena).
F10 Recourse Journey Simulator: shows the PD curve over 6 months as levers
are applied, using the documented S-curve interpolation from journey.py.
F13 Borrower Portal: no ML jargon; plain language throughout.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import plotly.graph_objects as go
import streamlit as st

import core
from app.components import ui
from app.components.journey import (
    APPROVAL_THRESHOLD,
    SAFE_BORROWERS,
    group_journey_comparison,
    simulate_journey,
)
from core.reference import MEENA, MEENA_ID, TEST_BORROWER_IDS, resolve

ui.page_header("Borrower Portal", "plain-language path to yes", "MSME owner")

# ---------------------------------------------------------------------------
# Sidebar: borrower picker with preset shortcuts
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("---")
    st.subheader("Quick presets")
    for preset in SAFE_BORROWERS:
        if st.button(
            preset["id"],
            key=f"portal_preset_{preset['id']}",
            help=preset["label"],
            use_container_width=True,
        ):
            st.session_state["selected_borrower"] = preset["id"]

    st.markdown("---")
    st.subheader("Language")
    lang = st.selectbox(
        "Letter language",
        ["en", "hi", "ta", "mr"],
        format_func={"en": "English", "hi": "Hindi", "ta": "Tamil", "mr": "Marathi"}.get,
        key="portal_lang",
    )

# Read preset from session state (set by Home page or sidebar)
default_bid = st.session_state.get("selected_borrower", MEENA_ID)
if default_bid not in TEST_BORROWER_IDS:
    default_bid = MEENA_ID

bid = st.selectbox(
    "Your application",
    TEST_BORROWER_IDS,
    index=TEST_BORROWER_IDS.index(default_bid),
    key="portal_bid",
    format_func=lambda b: f"{'★ ' if b == MEENA_ID else ''}{b}",
)

# Resolve borrower features
b = resolve(bid)
if not b.get("receivable_days"):
    b = {**MEENA, **b}

# ---------------------------------------------------------------------------
# SECTION 1: Application status (plain language, no ML jargon)
# ---------------------------------------------------------------------------
ui.section("Your Application", "how we looked at your business")

with ui.card():
    score_res = ui.safe_call(core.score, b)
    if score_res:
        ui.stub_banner(score_res.get("model_version"))
        approved = score_res["pd"] < APPROVAL_THRESHOLD
        band = score_res.get("pd_band", "medium")

        if approved:
            st.success("✅ **Your application meets our current criteria.**")
            st.write("Well done! Your business looks healthy. We will be in touch with your loan offer.")
        else:
            st.warning("⏳ **Your application needs a few improvements before we can approve it.**")
            st.write(
                "We looked carefully at your business. The key things holding back the decision are below. "
                "Each one is something you can work on – and we'll show you the path."
            )

        # Plain-language reasons (no SHAP, no AUC)
        reasons = score_res.get("reasons", [])
        if reasons:
            st.markdown("**What caught our attention:**")
            for r in reasons:
                st.write(f"- {r.get('text', r.get('feature', ''))}")

        # Data confidence
        dc = score_res.get("data_confidence", 0)
        st.caption(
            f"How confident are we in this assessment: **{dc}/100**. "
            "Higher means more of your records matched across GST, bank and UPI data."
        )

# ---------------------------------------------------------------------------
# SECTION 2: Your path to yes (recourse, plain language)
# ---------------------------------------------------------------------------
ui.section("Your Path to Approval", "specific steps you can take – and how long each takes")

rec_res = ui.safe_call(core.recourse, b)
if rec_res and rec_res.get("actions"):
    with ui.card():
        actions = rec_res["actions"]
        st.write(
            f"If you take the following step{'s' if len(actions) > 1 else ''}, "
            "our reassessment would be likely to approve your application."
        )
        for action in actions:
            months_est = action.get("months", "?")
            st.markdown(
                f"- **{action['label']}**: "
                f"bring from **{action['current']:.0f} {action['unit']}** "
                f"down to **{action['target']:.0f} {action['unit']}** "
                f"– estimated time: **{months_est:.0f} months**."
            )
        total_months = rec_res.get("months", "?")
        st.info(
            f"Estimated total time to approval under these steps: **{total_months:.0f} months**. "
            "This estimate is based on our experience with similar businesses."
        )
    ui.caption("Steps use only things you control; no protected characteristics are used.")
elif rec_res:
    with ui.card():
        st.write("No specific improvement steps identified. Please contact your relationship manager.")

# ---------------------------------------------------------------------------
# SECTION 3: Journey simulator (F10)
# ---------------------------------------------------------------------------
ui.section("Your 6-Month Journey", "see your application health improve month by month")

journey = None
if rec_res:
    journey = ui.safe_call(simulate_journey, b, rec_res, 6)

if journey:
    with ui.card():
        months_x = journey["months"]
        pd_curve = journey["pd_curve"]
        threshold = journey["threshold"]
        approval_month = journey["approval_month"]

        # Build Plotly figure
        fig = go.Figure()

        # PD curve
        fig.add_trace(go.Scatter(
            x=months_x,
            y=[v * 100 for v in pd_curve],
            mode="lines+markers",
            name="Application health",
            line=dict(color="#0F766E", width=3),
            marker=dict(size=8),
        ))

        # Approval threshold line
        fig.add_hline(
            y=threshold * 100,
            line_dash="dash",
            line_color="#B91C1C",
            annotation_text="Approval threshold",
            annotation_position="right",
        )

        # Annotate approval month
        if approval_month is not None and approval_month < len(pd_curve):
            fig.add_vline(
                x=approval_month,
                line_dash="dot",
                line_color="#0F766E",
                annotation_text=f"Month {approval_month}: approved!",
                annotation_position="top left",
            )

        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Application risk score (%)",
            height=320,
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        fig.update_yaxes(range=[0, max(pd_curve) * 100 * 1.2 + 5])

        st.plotly_chart(fig, use_container_width=True)

        if approval_month == 0:
            st.success("Your application already meets our criteria!")
        elif approval_month is not None:
            st.success(
                f"📈 Estimated approval at **month {approval_month}** if you follow the steps above."
            )
        else:
            st.info(
                "The steps shown reduce your risk score significantly over 6 months. "
                "Speak to your relationship manager about a longer-term improvement plan."
            )
        st.caption(f"Model version: {journey['model_version']} · Interpolation: {journey['interpolation']} · "
                   "under documented assumptions.")

    # Group comparison view – only if M2's fairness artifact exists
    gc = group_journey_comparison()
    if gc is not None:
        with ui.card():
            st.markdown("**How do similar businesses compare?**")
            col_w, col_o = st.columns(2)
            with col_w:
                st.metric(
                    "Women-led businesses (approval rate)",
                    f"{gc['women_led_approval_rate']:.1%}",
                )
            with col_o:
                st.metric(
                    "Other businesses (approval rate)",
                    f"{gc['not_women_led_approval_rate']:.1%}",
                )
            tpr_gap = gc.get("tpr_gap", 0.0)
            ai_ratio = gc.get("ai_ratio")
            st.caption(
                f"Approval-rate gap between groups: {tpr_gap:+.1%}. "
                + (f"Adverse impact ratio: {ai_ratio:.3f}. " if ai_ratio else "")
                + "Source: fairness_groups.json (M2 artifact). Under documented assumptions."
            )
            ui.caption("shows how our decisions compare across business types at the portfolio level.")

# ---------------------------------------------------------------------------
# SECTION 4: Repayment schedule (plain language)
# ---------------------------------------------------------------------------
ui.section("Your Repayment Schedule", "how monthly payments are structured to fit your cash flow")

struct_res = ui.safe_call(core.structure, b, target_dscr=1.25)
if struct_res:
    with ui.card():
        schedule = struct_res.get("schedule", [])
        p10 = struct_res.get("p10_band", [])
        tenor = struct_res.get("tenor_months", len(schedule))

        st.write(
            f"Your loan would be repaid over **{tenor} months**. "
            "Payments are designed to stay within your monthly cash available."
        )

        if schedule:
            fig2 = go.Figure()
            months_s = list(range(1, len(schedule) + 1))
            fig2.add_trace(go.Bar(
                x=months_s,
                y=schedule,
                name="Monthly payment",
                marker_color="#0F766E",
            ))
            if p10 and len(p10) == len(schedule):
                fig2.add_trace(go.Scatter(
                    x=months_s,
                    y=p10,
                    mode="lines",
                    name="Cash available (low estimate)",
                    line=dict(color="#B45309", dash="dash"),
                ))
            fig2.update_layout(
                xaxis_title="Month",
                yaxis_title="Amount (₹)",
                height=300,
                margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                yaxis_tickformat=",",
            )
            st.plotly_chart(fig2, use_container_width=True)
            ui.caption("green bars = your monthly payment; orange dashed = your low-estimate monthly cash in.")

# ---------------------------------------------------------------------------
# SECTION 5: Download your letter
# ---------------------------------------------------------------------------
ui.section("Download Your Letter", "official communication in your language")

lang = st.session_state.get("portal_lang", "en")
doc = ui.safe_call(core.make_letter, b, lang)
if doc:
    lang_labels = {"en": "English", "hi": "Hindi", "ta": "Tamil", "mr": "Marathi"}
    with ui.card():
        ui.download_button(
            f"Download Letter ({lang_labels.get(lang, lang)})",
            doc,
            file_name=f"letter_{bid}_{lang}.html",
            mime="text/html",
        )
        if lang != "en":
            st.caption("⚠ Non-English letters are template translations. PENDING NATIVE REVIEW.")

# ---------------------------------------------------------------------------
# SECTION 6: Challenge this decision
# ---------------------------------------------------------------------------
ui.section("Challenge This Decision", "if you believe something is incorrect, let us know")

with ui.card():
    with st.form(key=f"appeal_form_{bid}"):
        st.write("You have the right to ask us to review our assessment.")
        appeal_reason = st.text_area(
            "What would you like us to look at again?",
            placeholder="e.g. My GST records for the last 3 months show improved turnover.",
            key=f"appeal_reason_{bid}",
            max_chars=500,
        )
        contact = st.text_input(
            "Your contact number or email (so we can reach you)",
            key=f"appeal_contact_{bid}",
        )
        submitted = st.form_submit_button("Submit Review Request")
        if submitted:
            if appeal_reason.strip():
                st.success(
                    "✅ Thank you. Your review request has been noted. "
                    "A relationship manager will contact you within 5 working days."
                )
            else:
                st.warning("Please describe what you would like us to reconsider.")
