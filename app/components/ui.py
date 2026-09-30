"""OWNER: M4. Shared UI helpers. API frozen after Gate 1: add new helpers, do not rename existing."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import streamlit as st

from app.components.theme import apply_theme


def inr(x: float, decimals: int = 0) -> str:
    """Indian digit grouping: 1234567 -> ₹12,34,567."""
    neg = x < 0
    whole, _, frac = f"{abs(x):.{decimals}f}".partition(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups: list[str] = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join([*groups, tail])
    return f"{'-' if neg else ''}₹{whole}{('.' + frac) if frac else ''}"


def page_header(title: str, subtitle: str, persona: str) -> None:
    st.set_page_config(page_title=f"{title} | PS12", layout="wide")
    apply_theme()
    st.title(title)
    st.caption(f"Persona: {persona} - {subtitle}")


def caption(text: str) -> None:
    """Every chart carries a one-line 'How to read this' caption."""
    st.markdown(f'<div class="ps12-caption">How to read this: {text}</div>', unsafe_allow_html=True)


def stub_banner(model_version: str | None) -> None:
    if model_version is None or str(model_version).startswith("stub"):
        st.markdown('<div class="ps12-stub">STUB DATA - not a real model result. Do not screenshot for the deck.</div>',
                    unsafe_allow_html=True)


def kpi(label: str, value: str, help_: str | None = None) -> None:
    st.metric(label, value, help=help_)


def safe_call(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any | None:
    """Never show a stack trace to a judge: friendly message instead."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:  # noqa: BLE001
        st.warning(f"This panel is temporarily unavailable ({type(e).__name__}). Try another borrower.")
        return None
