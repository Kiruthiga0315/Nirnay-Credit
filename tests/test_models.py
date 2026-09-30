import json

from core.features import by_name
from core.models import build_artifacts, score
from core.paths import ARTIFACTS
from core.reference import MEENA_ID, resolve


def test_leakage_guard():
    """Ensure the PRODUCTION scoring path never reads oracle or panel data.

    build_artifacts() and _compute_scoreboard() legitimately load oracle.parquet
    for evaluation/reference (Blueprint L3, ARTIFACTS.md). But the production
    functions score() and score_batch() must never touch oracle data.
    """
    import inspect

    from core.models import _lazy_load_models, score, score_batch

    for func in [score, score_batch, _lazy_load_models]:
        src = inspect.getsource(func)
        assert "oracle" not in src, f"Leakage: {func.__name__} references oracle!"
        assert "panel.parquet" not in src, f"Leakage: {func.__name__} references panel!"


def test_protected_attribute_invariance():
    """Changing protected attributes should not change the score."""
    base = dict(resolve(MEENA_ID))
    base_score = score(base)["pd"]
    
    # Change gender
    for g in ["male", "female", "other"]:
        b2 = dict(base)
        b2["owner_gender"] = g
        assert abs(score(b2)["pd"] - base_score) < 1e-6, f"Score changed for gender {g}"
        
    # Change location
    for loc in ["rural", "urban", "metro"]:
        b2 = dict(base)
        b2["location_class"] = loc
        assert abs(score(b2)["pd"] - base_score) < 1e-6, f"Score changed for location {loc}"


def test_monotonicity():
    """Check that monotone features behave as constrained."""
    spec = by_name()
    base = dict(resolve(MEENA_ID))
    
    for f_name, f_spec in spec.items():
        direction = f_spec.get("monotone_pd", 0)
        if direction == 0:
            continue
        
        # Determine a range to test
        val_range = f_spec.get("allowed_range")
        if not val_range or val_range[0] is None or val_range[1] is None:
            continue
            
        low, high = val_range[0], val_range[1]
        
        # Test low
        b_low = dict(base)
        b_low[f_name] = low
        pd_low = score(b_low)["pd"]
        
        # Test high
        b_high = dict(base)
        b_high[f_name] = high
        pd_high = score(b_high)["pd"]
        
        if direction == 1:
            # PD must not decrease when feature increases
            assert pd_high >= pd_low - 1e-5, f"Monotonicity violated for {f_name} (+1)"
        elif direction == -1:
            # PD must not increase when feature increases
            assert pd_high <= pd_low + 1e-5, f"Monotonicity violated for {f_name} (-1)"


def test_calibration_ece():
    """Check that calibration ECE is reasonable."""
    metrics_path = ARTIFACTS / "metrics" / "models.json"
    if not metrics_path.exists():
        build_artifacts(smoke=True)
        
    with open(metrics_path, encoding="utf-8") as f:
        metrics = json.load(f)
        
    ece = metrics.get("ece_challenger")
    assert ece is not None
    assert ece < 0.20, f"ECE {ece} is too high."


def test_meena_scores():
    """Meena borrower must receive a valid score."""
    res = score(MEENA_ID)
    assert isinstance(res["pd"], float)
    assert res["pd_band"] in ["low", "medium", "high"]
    assert len(res["reasons"]) == 3
    assert res["data_confidence"] > 0
    assert not res["model_version"].startswith("stub")
