"""Tests for core/forecast.py (M2 ownership).

Contract:
- forecast() returns p10 <= p50 <= p90 for every month.
- build_artifacts() writes forecast_bands.parquet and metrics/forecast.json.
- Interval coverage (from metrics) is a float in [0, 1].
Reference borrower: Meena (MSME-00001).
"""
from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def forecast_built(tmp_path_factory):
    """Build forecast artifacts (smoke mode, fast)."""
    from core.forecast import build_artifacts

    build_artifacts(smoke=True)


@pytest.fixture(scope="module")
def meena_forecast(forecast_built):
    from core.forecast import forecast

    return forecast("MSME-00001", smoke=True)


# ---------------------------------------------------------------------------
# Quantile ordering tests
# ---------------------------------------------------------------------------

def test_forecast_keys(meena_forecast):
    required = {"borrower_id", "months", "p10", "p50", "p90", "model_version"}
    assert required.issubset(set(meena_forecast)), (
        f"Missing keys: {required - set(meena_forecast)}"
    )


def test_forecast_lists_equal_length(meena_forecast):
    n = len(meena_forecast["months"])
    assert len(meena_forecast["p10"]) == n
    assert len(meena_forecast["p50"]) == n
    assert len(meena_forecast["p90"]) == n


def test_forecast_quantiles_ordered(meena_forecast):
    """P10 <= P50 <= P90 must hold for every month."""
    for i, (lo, mid, hi) in enumerate(
        zip(meena_forecast["p10"], meena_forecast["p50"], meena_forecast["p90"], strict=False)
    ):
        assert lo <= mid + 1e-6, f"Month {i}: p10={lo} > p50={mid}"
        assert mid <= hi + 1e-6, f"Month {i}: p50={mid} > p90={hi}"


def test_forecast_non_negative(meena_forecast):
    """All forecast values must be non-negative (cash cannot be negative)."""
    for v in meena_forecast["p10"] + meena_forecast["p50"] + meena_forecast["p90"]:
        assert v >= -1e-6, f"Negative forecast value: {v}"


def test_forecast_model_version_set(meena_forecast):
    assert meena_forecast["model_version"], "model_version must be non-empty."


# ---------------------------------------------------------------------------
# Artifact tests
# ---------------------------------------------------------------------------

def test_forecast_bands_parquet_written(forecast_built):
    from core.paths import ARTIFACTS

    assert (ARTIFACTS / "forecast_bands.parquet").exists(), (
        "forecast_bands.parquet not written."
    )


def test_forecast_metrics_written(forecast_built):
    from core.paths import ARTIFACTS

    assert (ARTIFACTS / "metrics" / "forecast.json").exists(), (
        "metrics/forecast.json not written."
    )


def test_forecast_metrics_coverage_in_range(forecast_built):
    """Interval coverage must be a float in [0, 1]."""
    import json

    from core.paths import ARTIFACTS

    p = ARTIFACTS / "metrics" / "forecast.json"
    assert p.exists(), "metrics/forecast.json not found."
    m = json.loads(p.read_text(encoding="utf-8"))
    cov = m.get("conformal_interval_coverage_80pct")
    assert cov is not None, "conformal_interval_coverage_80pct not in metrics."
    assert 0.0 <= float(cov) <= 1.0, f"Coverage out of [0,1]: {cov}"


def test_forecast_bands_monotone():
    """forecast_bands.parquet: p10 <= p50 <= p90 per row."""
    import pandas as pd

    from core.paths import ARTIFACTS

    df = pd.read_parquet(ARTIFACTS / "forecast_bands.parquet")
    assert (df["p10"] <= df["p50"] + 1e-6).all(), "p10 > p50 in forecast_bands"
    assert (df["p50"] <= df["p90"] + 1e-6).all(), "p50 > p90 in forecast_bands"


def test_forecast_bands_has_required_columns():
    import pandas as pd

    from core.paths import ARTIFACTS

    df = pd.read_parquet(ARTIFACTS / "forecast_bands.parquet")
    for col in ("id", "month", "p10", "p50", "p90"):
        assert col in df.columns, f"Missing column '{col}' in forecast_bands.parquet"
