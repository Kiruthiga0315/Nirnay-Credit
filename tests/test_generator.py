"""Tests for core.generator — T6 comprehensive test suite."""
import json

import numpy as np
import pandas as pd
import pytest

from core.generator import build_artifacts, load_config
from core.paths import CONFIGS, DATA


@pytest.fixture(scope="module", autouse=True)
def _generate_once():
    """Run generator once in smoke mode for all tests in this module."""
    build_artifacts(smoke=True, kappa="medium", bias_strength="medium")


def test_generator_reproducibility():
    """Two runs with the same seed produce identical file hashes."""
    build_artifacts(smoke=True)
    with open(DATA / "generator_meta.json", encoding="utf-8") as f:
        meta1 = json.load(f)

    build_artifacts(smoke=True)
    with open(DATA / "generator_meta.json", encoding="utf-8") as f:
        meta2 = json.load(f)

    assert meta1["file_hashes"] == meta2["file_hashes"], "Runs are not reproducible"


def test_row_counts():
    """Borrower and panel row counts match metadata."""
    with open(DATA / "generator_meta.json", encoding="utf-8") as f:
        meta = json.load(f)
    borrowers = pd.read_parquet(DATA / "borrowers.parquet")
    panel = pd.read_parquet(DATA / "panel.parquet")

    assert len(borrowers) == meta["row_counts"]["borrowers"]
    assert len(panel) == meta["row_counts"]["panel"]
    assert len(panel) == len(borrowers) * 36


def test_meena_exact():
    """Meena fixture (MSME-00001) is injected exactly as in meena.json."""
    borrowers = pd.read_parquet(DATA / "borrowers.parquet")
    with open(CONFIGS / "personas" / "meena.json", encoding="utf-8") as f:
        meena = json.load(f)
    meena.pop("_note", None)

    meena_row = borrowers[borrowers["id"] == "MSME-00001"].iloc[0]
    assert meena_row["id"] == "MSME-00001"

    for k, v in meena.items():
        if k == "id":
            continue
        if v is None or (isinstance(v, float) and np.isnan(v)):
            assert pd.isna(meena_row[k]), f"Meena {k} should be NaN"
        else:
            assert meena_row[k] == pytest.approx(v, abs=1e-6), (
                f"Meena {k}: expected {v}, got {meena_row[k]}"
            )


def test_feature_spec_coverage():
    """All feature_spec features are present in borrowers."""
    borrowers = pd.read_parquet(DATA / "borrowers.parquet")
    with open(CONFIGS / "feature_spec.json", encoding="utf-8") as f:
        spec = json.load(f)

    feature_names = {feat["name"] for feat in spec["features"]}
    assert feature_names.issubset(set(borrowers.columns)), (
        f"Missing features: {feature_names - set(borrowers.columns)}"
    )


def test_non_nullable_have_no_nans():
    """Non-nullable features in feature_spec have no NaN values in borrowers."""
    borrowers = pd.read_parquet(DATA / "borrowers.parquet")
    with open(CONFIGS / "feature_spec.json", encoding="utf-8") as f:
        spec = json.load(f)

    nullable_features = {feat["name"] for feat in spec["features"] if feat.get("nullable", False)}
    skip_cols = {"id", "name", "business", "_note"}

    for col in borrowers.columns:
        if col in skip_cols or col.startswith("oot_"):
            continue
        if col not in nullable_features:
            assert not borrowers[col].isna().any(), f"Column {col} has NaN but is not nullable"


def test_oracle_never_in_borrowers_or_panel():
    """Oracle latent columns must NEVER appear in borrowers or panel."""
    borrowers = pd.read_parquet(DATA / "borrowers.parquet")
    panel = pd.read_parquet(DATA / "panel.parquet")
    oracle = pd.read_parquet(DATA / "oracle.parquet")

    oracle_only_cols = {"capacity", "shock_sensitivity", "management_quality",
                        "default_month", "default_type", "default_12m",
                        "kappa_applied", "sector_seasonality_amp"}
    borrower_cols = set(borrowers.columns)
    panel_cols = set(panel.columns)

    assert oracle_only_cols.isdisjoint(borrower_cols), (
        f"Oracle columns leaked into borrowers: {oracle_only_cols & borrower_cols}"
    )
    assert oracle_only_cols.isdisjoint(panel_cols), (
        f"Oracle columns leaked into panel: {oracle_only_cols & panel_cols}"
    )
    # Oracle must have all latent columns
    for col in ["capacity", "shock_sensitivity", "management_quality",
                 "default_month", "default_type", "default_12m"]:
        assert col in oracle.columns, f"Oracle missing column {col}"


def test_thin_file_share_overall():
    """Overall thin-file share is 0.30-0.40."""
    borrowers = pd.read_parquet(DATA / "borrowers.parquet")
    total_thin = borrowers["bureau_score"].isna().mean()
    assert 0.30 <= total_thin <= 0.40, f"Total thin file share {total_thin:.3f} outside [0.30, 0.40]"


def test_thin_file_higher_for_women():
    """Women-led MSMEs have higher thin-file share than male-led (bias mechanism)."""
    borrowers = pd.read_parquet(DATA / "borrowers.parquet")
    female_thin = borrowers[borrowers["owner_gender"] == "female"]["bureau_score"].isna().mean()
    male_thin = borrowers[borrowers["owner_gender"] == "male"]["bureau_score"].isna().mean()
    assert female_thin > male_thin, (
        f"Female thin {female_thin:.3f} not > Male thin {male_thin:.3f}"
    )


def test_thin_file_higher_for_rural():
    """Rural MSMEs have higher thin-file share than metro (bias mechanism)."""
    borrowers = pd.read_parquet(DATA / "borrowers.parquet")
    rural_thin = borrowers[borrowers["location_class"] == "rural"]["bureau_score"].isna().mean()
    metro_thin = borrowers[borrowers["location_class"] == "metro"]["bureau_score"].isna().mean()
    assert rural_thin > metro_thin, (
        f"Rural thin {rural_thin:.3f} not > Metro thin {metro_thin:.3f}"
    )


def test_default_rate_sensible():
    """Default rate is in a sensible range (3-20%)."""
    oracle = pd.read_parquet(DATA / "oracle.parquet")
    default_rate = oracle["default_12m"].mean()
    assert 0.03 <= default_rate <= 0.20, (
        f"Default rate {default_rate:.3f} outside [0.03, 0.20]"
    )


def test_default_type_categories():
    """Default types are either 'timing', 'solvency', or '' (no default)."""
    oracle = pd.read_parquet(DATA / "oracle.parquet")
    valid_types = {"timing", "solvency", ""}
    actual_types = set(oracle["default_type"].unique())
    assert actual_types.issubset(valid_types), (
        f"Unexpected default types: {actual_types - valid_types}"
    )


def test_timing_share_measurable():
    """Among defaulters, the timing share is measurably > 0 and < 1."""
    oracle = pd.read_parquet(DATA / "oracle.parquet")
    defaulters = oracle[oracle["default_12m"] == 1]
    if len(defaulters) > 0:
        timing_count = (defaulters["default_type"] == "timing").sum()
        timing_share = timing_count / len(defaulters)
        assert timing_share > 0, "No timing defaults found"
        assert timing_share < 1.0, "All defaults are timing (no solvency)"


def test_kappa_affects_default_rates():
    """Default rate differs sensibly across kappa levels."""
    rates = {}
    for k_label in ("high", "medium", "low"):
        build_artifacts(smoke=True, kappa=k_label, bias_strength="medium")
        oracle = pd.read_parquet(DATA / "oracle.parquet")
        rates[k_label] = oracle["default_12m"].mean()

    # Rates should differ (not all identical)
    assert len(set(f"{v:.3f}" for v in rates.values())) > 1, (
        f"Default rates are identical across kappa: {rates}"
    )


def test_kappa_affects_timing_share():
    """Timing share of defaults should increase with kappa."""
    shares = {}
    for k_label in ("high", "medium", "low"):
        build_artifacts(smoke=True, kappa=k_label, bias_strength="medium")
        oracle = pd.read_parquet(DATA / "oracle.parquet")
        defaulters = oracle[oracle["default_12m"] == 1]
        if len(defaulters) > 0:
            shares[k_label] = (defaulters["default_type"] == "timing").mean()
        else:
            shares[k_label] = 0.0

    assert shares["high"] > shares["low"], (
        f"Timing share for kappa=high ({shares['high']:.3f}) "
        f"not > kappa=low ({shares['low']:.3f})"
    )


def test_oot_split_columns():
    """Out-of-time split columns exist with correct values."""
    borrowers = pd.read_parquet(DATA / "borrowers.parquet")
    assert "oot_train_start" in borrowers.columns
    assert "oot_train_end" in borrowers.columns
    assert "oot_test_start" in borrowers.columns
    assert "oot_test_end" in borrowers.columns

    assert borrowers["oot_train_start"].iloc[0] == 1
    assert borrowers["oot_train_end"].iloc[0] == 24
    assert borrowers["oot_test_start"].iloc[0] == 25
    assert borrowers["oot_test_end"].iloc[0] == 36


def test_load_config_all_grid_cells():
    """load_config works for all 9 grid cells."""
    for k in ("high", "medium", "low"):
        for b in ("weak", "medium", "strong"):
            cfg = load_config(kappa=k, bias_strength=b)
            assert "kappa" in cfg
            assert "bias_strength" in cfg
            assert cfg["seed"] == 42


def test_all_9_configs_generate():
    """All 9 grid configs generate in smoke mode without error."""
    for k in ("high", "medium", "low"):
        for b in ("weak", "medium", "strong"):
            build_artifacts(smoke=True, kappa=k, bias_strength=b)
            # If we got here, it didn't crash
            assert (DATA / "borrowers.parquet").exists()
            assert (DATA / "panel.parquet").exists()
            assert (DATA / "oracle.parquet").exists()
