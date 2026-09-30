import pandas as pd
import pytest

from core.paths import DATA
from core.stress import build_graph, get_base_metrics, load_scenarios, stress


def test_stress():
    borrowers_df = pd.read_parquet(DATA / "borrowers.parquet")
    base_el, _, _ = get_base_metrics(borrowers_df, 0.45)
    
    scenarios = load_scenarios()
    
    for s in scenarios:
        res = stress(s)
        assert res["expected_loss"] > base_el, f"Scenario {s} EL {res['expected_loss']} not greater than base {base_el}"
        assert res["es95"] >= res["expected_loss"], f"Scenario {s} ES95 {res['es95']} < EL {res['expected_loss']}"
        
    with pytest.raises(ValueError):
        stress("nope")

def test_graph_properties():
    borrowers_df = pd.read_parquet(DATA / "borrowers.parquet")
    graph_df = build_graph(borrowers_df)
    
    # no self loops
    assert not (graph_df["src"] == graph_df["dst"]).any()
    
    # revenue_share per supplier <= 1
    supplier_shares = graph_df.groupby("src")["revenue_share"].sum()
    assert (supplier_shares <= 1.0 + 1e-6).all()
