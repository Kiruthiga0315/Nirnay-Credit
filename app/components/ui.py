"""OWNER: M4. Shared UI helpers. API frozen after Gate 1: add new helpers, do not rename existing."""
from __future__ import annotations

import contextlib
from collections.abc import Callable
from typing import Any

import plotly.graph_objects as go
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
    with st.sidebar:
        st.title("Nirnay-Credit")
        st.caption("Governed MSME Lending Cockpit")
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


@contextlib.contextmanager
def card() -> Any:
    with st.container(border=True):
        yield


def kpi_row(kpis: list[tuple[str, str]] | list[tuple[str, str, str | None]]) -> None:
    cols = st.columns(len(kpis))
    for col, kpi_data in zip(cols, kpis, strict=True):
        with col:
            if len(kpi_data) == 3:
                kpi(kpi_data[0], kpi_data[1], help_=kpi_data[2])  # type: ignore
            else:
                kpi(kpi_data[0], kpi_data[1])


def pd_gauge(pd: float, threshold: float = 0.5) -> None:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pd,
        number={"valueformat": ".1%"},
        gauge={
            "axis": {"range": [0, 1], "tickformat": ".0%"},
            "bar": {"color": "#0F766E"},
            "steps": [
                {"range": [0, threshold], "color": "#E2E8F0"},
                {"range": [threshold, 1], "color": "#FEF3C7"}
            ],
            "threshold": {
                "line": {"color": "#B91C1C", "width": 4},
                "thickness": 0.75,
                "value": threshold
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)
    caption("probability of default calibrated against policy approval threshold.")


def reason_list(reasons: list[dict[str, Any]]) -> None:
    for r in reasons:
        st.write(f"- **{r['feature']}**: {r['text']} (Impact: {r['impact']:.3f})")


def persona_card(borrower: dict[str, Any]) -> None:
    html = f"""
    <div class="ps12-card" style="margin-bottom: 1rem;">
        <h4 style="margin-top: 0; color: #0F766E;">{borrower.get('business', 'Unknown Business')}</h4>
        <div class="ps12-caption">{borrower.get('id', '')} | {borrower.get('sector', '')}</div>
        <p style="margin-bottom: 0; font-size: 0.9rem; margin-top: 0.5rem;">
            Location: {borrower.get('location', 'N/A')} | Vintage: {borrower.get('vintage_years', 0)} years
        </p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def section(title: str, caption_text: str) -> None:
    st.subheader(title)
    caption(caption_text)


def download_button(label: str, data: bytes | str, file_name: str, mime: str) -> None:
    st.download_button(label, data, file_name=file_name, mime=mime)
