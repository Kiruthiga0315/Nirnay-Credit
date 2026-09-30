"""OWNER: M2. Tests for core/features.py.

Covers:
- validate_spec() passes on the current spec.
- recompute_derived() on Meena's fields and with list inputs.
- All levers are verifiable and not gameable / protected.
- lever_config() returns correct info and raises for non-levers.
"""
from __future__ import annotations

import pytest

from core.features import (
    by_name,
    lever_config,
    levers,
    load_spec,
    model_features,
    recompute_derived,
    validate_spec,
)
from core.reference import MEENA

# ---------------------------------------------------------------------------
# T1 / T2: validate_spec()
# ---------------------------------------------------------------------------

def test_validate_spec_passes():
    """validate_spec() must not raise on the committed feature_spec.json."""
    validate_spec()  # raises ValueError on any violation


def test_spec_shape():
    spec = load_spec()
    for f in spec["features"]:
        assert f["mutability"] in spec["mutability_classes"], (
            f"Feature '{f['name']}' has unknown mutability '{f['mutability']}'"
        )
        assert f["monotone_pd"] in (-1, 0, 1), (
            f"Feature '{f['name']}' has invalid monotone_pd {f['monotone_pd']}"
        )
        assert f.get("label", "").strip(), f"Feature '{f['name']}' missing label"


def test_protected_never_model_inputs():
    b = by_name()
    for name in ("owner_gender", "location_class"):
        assert b[name]["model_input"] is False, (
            f"Protected attribute '{name}' must have model_input=False"
        )
    assert not {"owner_gender", "location_class"} & set(model_features())


def test_levers_are_verifiable_and_not_gameable():
    bn = by_name()
    for name in levers():
        assert bn[name]["mutability"] == "verifiable", (
            f"Lever '{name}' is '{bn[name]['mutability']}', must be 'verifiable'"
        )
    # Explicit gameable exclusion
    assert "avg_bank_balance_3m" not in levers()
    assert "upi_inflow_3m_avg" not in levers()


def test_levers_have_cost_and_months():
    """Every verifiable lever in the default list must have cost_per_unit and months_per_unit."""
    spec = load_spec()
    default_levers = spec["recourse_levers_default"]
    bn = by_name()
    for name in default_levers:
        f = bn[name]
        assert "cost_per_unit" in f, f"Lever '{name}' missing cost_per_unit"
        assert "months_per_unit" in f, f"Lever '{name}' missing months_per_unit"
        assert f["cost_per_unit"] >= 0, f"Lever '{name}' cost_per_unit < 0"
        assert f["months_per_unit"] > 0, f"Lever '{name}' months_per_unit <= 0"


def test_lever_config_returns_verifiable():
    cfg = lever_config("receivable_days")
    assert cfg["mutability"] == "verifiable"
    assert "step" in cfg
    assert "allowed_range" in cfg


def test_lever_config_raises_for_non_lever():
    with pytest.raises(KeyError):
        lever_config("bureau_score")         # immutable
    with pytest.raises(KeyError):
        lever_config("avg_bank_balance_3m")  # gameable
    with pytest.raises(KeyError):
        lever_config("__nonexistent__")      # not in spec


# ---------------------------------------------------------------------------
# T2: recompute_derived() on Meena
# ---------------------------------------------------------------------------

def test_recompute_derived_meena_cash_conversion():
    """On Meena's row, cash_conversion_days = receivable_days + inventory_days - payable_days."""
    row = dict(MEENA)
    row["inventory_days"] = 45.0
    row["payable_days"] = 30.0
    out = recompute_derived(row)
    expected = row["receivable_days"] + row["inventory_days"] - row["payable_days"]
    assert abs(out["cash_conversion_days"] - expected) < 0.01, (
        f"cash_conversion_days: expected {expected}, got {out['cash_conversion_days']}"
    )


def test_recompute_derived_no_crash_missing_keys():
    """recompute_derived() must not crash when derived inputs are absent."""
    row = {"id": "MSME-00001", "gst_filing_regularity": 0.92}
    out = recompute_derived(row)
    # cash_conversion_days not recomputed (missing inventory_days, payable_days)
    assert "cash_conversion_days" not in out


def test_recompute_derived_inflow_stability():
    """inflow_stability_cv = pstdev / mean of monthly_inflow list."""
    import statistics
    inflows = [100_000, 120_000, 80_000, 110_000, 95_000, 130_000]
    row = {"id": "X", "monthly_inflow": inflows}
    out = recompute_derived(row)
    expected_cv = statistics.pstdev(inflows) / statistics.mean(inflows)
    assert abs(out["inflow_stability_cv"] - expected_cv) < 0.001


def test_recompute_derived_revenue_growth():
    """revenue_growth_3m = (revenues[-1] / revenues[-4]) - 1."""
    revenues = [500_000, 520_000, 490_000, 510_000, 540_000, 560_000]
    row = {"id": "X", "monthly_revenue": revenues}
    out = recompute_derived(row)
    expected = (revenues[-1] / revenues[-4]) - 1.0
    assert abs(out["revenue_growth_3m"] - expected) < 0.001


def test_recompute_derived_is_pure():
    """recompute_derived() must not mutate the input dict."""
    row = {"id": "X", "receivable_days": 60.0, "inventory_days": 30.0, "payable_days": 20.0}
    original = dict(row)
    recompute_derived(row)
    assert row == original


def test_derived_features_not_in_levers():
    """Derived features must never appear in the recourse lever list."""
    derived = {f["name"] for f in load_spec()["features"] if f["mutability"] == "derived"}
    for name in levers():
        assert name not in derived, (
            f"Derived feature '{name}' must not be a recourse lever"
        )
