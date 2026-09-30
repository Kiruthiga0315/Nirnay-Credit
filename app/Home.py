"""OWNER: M4. Entry point: streamlit run app/Home.py

Story Mode (F16): Play demo button navigates through Meena's flow with
timed callouts and next/previous controls (script: app/components/story_script.json).
Guided tour (5 steps) helps judges exploring alone.
Presets: three safe borrowers exposed as one-click shortcuts.
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import streamlit as st

from app.components import ui
from app.components.journey import SAFE_BORROWERS
from core.paths import artifact_path
from core.reference import MEENA

# ---------------------------------------------------------------------------
# Page header (must be first Streamlit call)
# ---------------------------------------------------------------------------
ui.page_header(
    "PS12 – Governed MSME Lending Cockpit",
    "every application gets a reason, a route to yes, a fair price and a stress-tested loss",
    "All",
)

# ---------------------------------------------------------------------------
# Load story script
# ---------------------------------------------------------------------------
_SCRIPT_PATH = pathlib.Path(__file__).resolve().parent / "components" / "story_script.json"


@st.cache_data(show_spinner=False)
def _load_script() -> dict:
    return json.loads(_SCRIPT_PATH.read_text(encoding="utf-8"))


script = _load_script()
slides = script["slides"]
tour_steps = script["guided_tour"]

# ---------------------------------------------------------------------------
# Sidebar: Story Mode controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("---")
    st.subheader("🎬 Story Mode")
    if "story_slide" not in st.session_state:
        st.session_state.story_slide = -1  # -1 = not playing

    playing = st.session_state.story_slide >= 0

    if not playing:
        if st.button("▶ Play Demo (4 min)", key="story_play_btn", use_container_width=True):
            st.session_state.story_slide = 0
            st.rerun()
    else:
        slide_idx = st.session_state.story_slide
        current = slides[slide_idx]
        st.info(f"**Step {slide_idx + 1}/{len(slides)}**\n\n{current['page']}")
        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("◀ Prev", key="story_prev", disabled=(slide_idx == 0)):
                st.session_state.story_slide -= 1
                st.rerun()
        with col_next:
            if st.button("Next ▶", key="story_next", disabled=(slide_idx >= len(slides) - 1)):
                st.session_state.story_slide += 1
                st.rerun()
        if st.button("⏹ Stop Demo", key="story_stop", use_container_width=True):
            st.session_state.story_slide = -1
            st.rerun()

    st.markdown("---")
    st.subheader("🗺 Guided Tour")
    if "tour_step" not in st.session_state:
        st.session_state.tour_step = -1

    if st.session_state.tour_step < 0:
        if st.button("Start Tour", key="tour_start", use_container_width=True):
            st.session_state.tour_step = 0
            st.rerun()
    else:
        step_idx = st.session_state.tour_step
        step = tour_steps[step_idx]
        st.success(f"**Tour step {step['step']}/5**\n\n→ {step['page']}\n\n{step['tip']}")
        col_tp, col_tn = st.columns(2)
        with col_tp:
            if st.button("◀", key="tour_prev", disabled=(step_idx == 0)):
                st.session_state.tour_step -= 1
                st.rerun()
        with col_tn:
            if st.button("▶", key="tour_next", disabled=(step_idx >= len(tour_steps) - 1)):
                st.session_state.tour_step += 1
                st.rerun()
        if st.button("End Tour", key="tour_end", use_container_width=True):
            st.session_state.tour_step = -1
            st.rerun()

# ---------------------------------------------------------------------------
# Story Mode callout banner (active only when playing)
# ---------------------------------------------------------------------------
if st.session_state.get("story_slide", -1) >= 0:
    slide = slides[st.session_state.story_slide]
    st.info(
        f"🎬 **Demo step {st.session_state.story_slide + 1}/{len(slides)} · {slide['page']}**\n\n"
        f"{slide['callout']}\n\n"
        f"_Use the sidebar ◀ / ▶ buttons or navigate to **{slide['page_target']}**._"
    )

# ---------------------------------------------------------------------------
# Meet the borrower
# ---------------------------------------------------------------------------
ui.section("Meet the Borrower", "our reference persona to understand the problem")
with ui.card():
    ui.persona_card(MEENA)
    st.write(
        "Use the sidebar to explore how the lending cockpit manages this application. "
        "The pipeline evaluates probability of default, recourse, structured repayment, "
        "fairness and stress."
    )

# ---------------------------------------------------------------------------
# One-click borrower presets (T4)
# ---------------------------------------------------------------------------
ui.section("Quick Start – Safe Presets", "pre-loaded borrowers for fast exploration")
with ui.card():
    st.caption(
        "How to read this: click a borrower to set them as the active selection across pages "
        "2 and 3. These three are validated with the stub model and render reliably."
    )
    cols = st.columns(len(SAFE_BORROWERS))
    for col, preset in zip(cols, SAFE_BORROWERS, strict=False):
        with col:
            if st.button(
                preset["label"].split(" – ")[0],
                key=f"preset_btn_{preset['id']}",
                help=preset["note"],
                use_container_width=True,
            ):
                st.session_state["selected_borrower"] = preset["id"]
                st.toast(f"Selected {preset['id']} – navigate to Borrower Decision or Portal.")

    active = st.session_state.get("selected_borrower", "MSME-00001")
    st.caption(f"Active: **{active}**")

# ---------------------------------------------------------------------------
# System status
# ---------------------------------------------------------------------------
ui.section("System Status", "pipeline artifact readiness")
have = artifact_path("metrics.json").exists()
if have:
    st.success("Artifacts found: real results are loaded.")
else:
    st.info("No artifacts yet: running on stubs.")
