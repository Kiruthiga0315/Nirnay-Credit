"""OWNER: M4. One typeface, one accent colour, consistent cards. Call apply_theme() on every page."""
import streamlit as st

ACCENT = "#0F766E"
WARN = "#B45309"
BAD = "#B91C1C"


def apply_theme() -> None:
    st.markdown(
        f"""<style>
        .block-container {{padding-top: 1.5rem; max-width: 1200px;}}
        .ps12-card {{border: 1px solid #E2E8F0; border-radius: 12px; padding: 1rem 1.25rem; background: #fff;}}
        .ps12-caption {{color: #475569; font-size: 0.85rem; margin-top: -0.25rem;}}
        .ps12-stub {{background: #FEF3C7; color: {WARN}; padding: .4rem .8rem; border-radius: 8px; font-size: .85rem;}}
        </style>""",
        unsafe_allow_html=True,
    )
