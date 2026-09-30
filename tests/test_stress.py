"""Tests for stress engine with contagion."""
import pandas as pd
import pytest

from core.paths import DATA
from core.stress import (
    build_graph,
    get_base_metrics,
    load_scenarios,
    stress,
    stress_full,
)


def test_stress_el_rises():
    """Baseline EL < EL under each shock for every named scenario."""
    borrowers_df = pd.read_parquet(DATA / "borrowers.parquet")
    base_el, _, _ = get_base_metrics(borrowers_df, 0.45)

    for s in load_scenarios():
        res = stress(s)
        assert res["expected_loss"] > base_el, (
            f"Scenario {s}: EL {res['expected_loss']} not > base {base_el}"
        )


def test_es95_gte_el():
    """ES95 >= EL for every scenario."""
    for s in load_scenarios():
        res = stress(s)
        assert res["es95"] >= res["expected_loss"], (
            f"Scenario {s}: ES95 {res['es95']} < EL {res['expected_loss']}"
        )


def test_unknown_scenario_raises():
    with pytest.raises(ValueError, match="Unknown scenario"):
        stress("nope")


def test_reproducible():
    """Same seed produces identical results."""
    r1 = stress("covid_style")
    r2 = stress("covid_style")
    assert r1["es95"] == r2["es95"]
    assert r1["expected_loss"] == r2["expected_loss"]


def test_contagion_increases_es95():
    """With contagion ON, ES95 > ES95 with contagion OFF (same seed)."""
    for s in load_scenarios():
        full = stress_full(s)
        assert full["es95"] >= full["es95_no_contagion"], (
            f"Scenario {s}: contagion ES95 {full['es95']} < no-contagion {full['es95_no_contagion']}"
        )


def test_tornado_bars_ordered():
    """Tornado bars are sorted by impact width descending."""
    res = stress("covid_style")
    tornado = res["tornado"]
    widths = [abs(t["high"] - t["low"]) for t in tornado]
    assert widths == sorted(widths, reverse=True), "Tornado bars not sorted by width"


def test_mitigation_loss_saved_nonneg():
    """Mitigation loss saved >= 0."""
    for s in load_scenarios():
        full = stress_full(s)
        assert full["mitigation"]["loss_saved_inr"] >= 0, (
            f"Scenario {s}: negative loss saved"
        )


def test_graph_no_self_loops():
    borrowers_df = pd.read_parquet(DATA / "borrowers.parquet")
    graph_df = build_graph(borrowers_df)
    assert not (graph_df["src"] == graph_df["dst"]).any()


def test_graph_share_sums():
    borrowers_df = pd.read_parquet(DATA / "borrowers.parquet")
    graph_df = build_graph(borrowers_df)
    supplier_shares = graph_df.groupby("src")["revenue_share"].sum()
    assert (supplier_shares <= 1.0 + 1e-6).all()
