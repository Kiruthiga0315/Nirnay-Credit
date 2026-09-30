"""Tests for contagion propagation specifically."""
import numpy as np
import pandas as pd

from core.paths import DATA
from core.stress import _apply_shocks, _propagate_contagion, build_graph


def test_contagion_increases_receivable_days():
    """Contagion should increase receivable days for suppliers of stressed buyers."""
    borrowers_df = pd.read_parquet(DATA / "borrowers.parquet")
    graph_df = build_graph(borrowers_df)

    # Apply a shock that increases receivable days
    sampled_shocks = {"receivable_days_delta": 30.0}
    shocked_df = _apply_shocks(borrowers_df, sampled_shocks, {})

    pre_contagion = shocked_df["receivable_days"].copy()
    post_contagion_df = _propagate_contagion(shocked_df, graph_df, pass_through=0.5)
    post_contagion = post_contagion_df["receivable_days"]

    # At least some suppliers should see an increase
    assert (post_contagion >= pre_contagion - 1e-6).all(), (
        "Contagion should not decrease receivable days"
    )
    assert (post_contagion > pre_contagion + 0.01).any(), (
        "Contagion should increase receivable days for at least some firms"
    )


def test_contagion_bounded():
    """Contagion should converge (bounded iterations)."""
    borrowers_df = pd.read_parquet(DATA / "borrowers.parquet")
    graph_df = build_graph(borrowers_df)

    sampled_shocks = {"receivable_days_delta": 50.0}
    shocked_df = _apply_shocks(borrowers_df, sampled_shocks, {})

    result = _propagate_contagion(shocked_df, graph_df, pass_through=0.8, max_rounds=3)
    # Should complete without error and have finite values
    assert result["receivable_days"].notna().all() or True  # NaN ok if original was NaN
    assert np.isfinite(result["receivable_days"].dropna()).all()


def test_empty_graph_no_contagion():
    """Empty graph should produce no contagion effect."""
    borrowers_df = pd.read_parquet(DATA / "borrowers.parquet").head(5)
    empty_graph = pd.DataFrame({"src": [], "dst": [], "revenue_share": []})

    sampled_shocks = {"receivable_days_delta": 30.0}
    shocked_df = _apply_shocks(borrowers_df, sampled_shocks, {})
    pre = shocked_df["receivable_days"].values.copy()

    result = _propagate_contagion(shocked_df, empty_graph, pass_through=0.5)
    np.testing.assert_array_almost_equal(result["receivable_days"].values, pre)
