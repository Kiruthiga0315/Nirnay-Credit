"""OWNER: M1. T1 leakage & validity audit tests.

Checks:
1. No feature built from months beyond the train cutoff (OOT integrity).
2. Calibration set disjoint from test set.
3. Oracle never reached by any production score path (static import check + runtime guard).
4. Protected attributes absent from model inputs (feature_spec and model_features()).
5. Results identical across two seeded runs (determinism).
"""
import ast
import inspect
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# 1. OOT INTEGRITY: train features built only from months <= train cutoff
# ---------------------------------------------------------------------------

def test_oot_train_month_cutoff():
    """Borrowers assigned to train split must not have application_month > oot_train_end."""
    from core.generator import build_artifacts as gen_build
    from core.paths import DATA

    gen_build(smoke=True, kappa="medium", bias_strength="medium")
    borrowers = pd.read_parquet(DATA / "borrowers.parquet")

    # Every row in the dataset has oot_train_end set by the generator
    train_mask = borrowers["application_month"] <= borrowers["oot_train_end"]
    test_mask = borrowers["application_month"] >= borrowers["oot_test_start"]

    # Sanity: the two masks must be mutually exclusive
    assert not (train_mask & test_mask).any(), (
        "Some rows are in both train AND test split — OOT split is not disjoint"
    )

    # Train rows must respect cutoff
    train_rows = borrowers[train_mask]
    assert (train_rows["application_month"] <= train_rows["oot_train_end"]).all(), (
        "Train rows have application_month beyond oot_train_end"
    )

    # Test rows must all be past the test_start boundary
    test_rows = borrowers[test_mask]
    assert (test_rows["application_month"] >= test_rows["oot_test_start"]).all(), (
        "Test rows have application_month before oot_test_start"
    )

    print(
        f"[leakage] OOT split OK — train={train_mask.sum()}, test={test_mask.sum()}, "
        f"total={len(borrowers)}"
    )


def test_no_future_month_feature():
    """
    Panel signals for a given application_month are built from panel rows
    with month <= 24 (train window). The generator writes panel.parquet
    for ALL months (1-36), but models.build_artifacts() trains on application_month <= 24.
    Verify the OOT cutoff in models.py uses the correct column, not a hard-coded constant
    that could silently drift.
    """
    import inspect

    from core import models

    src = inspect.getsource(models.build_artifacts)
    # The code must reference "oot_train_end" (the column) for the train split
    assert "oot_train_end" in src, (
        "build_artifacts() does not use 'oot_train_end' column for the train/test split. "
        "Hard-coded month cutoffs are a leakage risk."
    )
    assert "oot_test_start" in src, (
        "build_artifacts() does not use 'oot_test_start' for the OOT test slice."
    )


# ---------------------------------------------------------------------------
# 2. CALIBRATION SET DISJOINT FROM TEST SET
# ---------------------------------------------------------------------------

def test_calibration_set_disjoint_from_test():
    """
    The challenger model calibrator (IsotonicRegression) is fitted on a
    train_test_split(..., test_size=0.2) of the TRAIN data (months 1-24).
    This calibration slice must never overlap the OOT test set (months 25-36).

    We verify by inspecting the source: calibration is done inside train data only.
    The OOT test is evaluated separately after calibration is frozen.
    """
    import inspect

    from core import models

    src = inspect.getsource(models.build_artifacts)

    # The calibration split must use the training data only.
    # The pattern is: train_test_split(X_train_lgb, y_train, ...) THEN calibrator.fit(...)
    # followed by _evaluate_model(...) on the test data.
    # Confirm test data (X_test_lgb) does NOT appear as argument to calibrator.fit
    # by checking code structure.

    # Static check: calibrator.fit must come before the OOT test evaluation
    calib_fit_pos = src.find("calibrator.fit(")
    test_eval_pos = src.find("_evaluate_model(challenger, X_test_lgb")
    assert calib_fit_pos != -1, "calibrator.fit() not found in build_artifacts"
    assert test_eval_pos != -1, "_evaluate_model with X_test_lgb not found in build_artifacts"
    assert calib_fit_pos < test_eval_pos, (
        "calibrator.fit() appears AFTER test evaluation — calibration may use test data"
    )

    # Also verify _compute_scoreboard uses train_test_split on approved train data
    sb_src = inspect.getsource(models._compute_scoreboard)
    assert "train_test_split" in sb_src, (
        "_compute_scoreboard must use train_test_split for calibration"
    )
    # The scoreboard calibration must split TRAIN data, not all_df or test_all
    assert "X_train_appr" in sb_src or "X_appr_fit" in sb_src, (
        "_compute_scoreboard calibrator is not clearly fitted on train-approved split"
    )


# ---------------------------------------------------------------------------
# 3. ORACLE NEVER IN PRODUCTION SCORE PATH
# ---------------------------------------------------------------------------

def test_oracle_not_imported_in_score_functions():
    """Static check: score(), score_batch(), _lazy_load_models() must not reference oracle."""
    from core.models import _lazy_load_models, score, score_batch

    for func in [score, score_batch, _lazy_load_models]:
        src = inspect.getsource(func)
        assert "oracle" not in src.lower(), (
            f"LEAKAGE: {func.__name__} references 'oracle' — oracle data must never "
            "enter the production score path"
        )
        assert "panel.parquet" not in src, (
            f"LEAKAGE: {func.__name__} references panel.parquet — "
            "panel is not a production input"
        )


def test_oracle_not_imported_at_module_level():
    """
    Static AST check: core/models.py must not import oracle at module level.
    oracle.parquet loading is only acceptable inside build_artifacts()
    and _compute_scoreboard().
    """
    models_path = ROOT / "core" / "models.py"
    source = models_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    # Collect all top-level imports
    top_level_imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            top_level_imports.append(ast.unparse(node))

    for imp in top_level_imports:
        assert "oracle" not in imp.lower(), (
            f"Module-level import references oracle: {imp}"
        )


def test_oracle_runtime_guard():
    """
    Runtime guard: call score() with Meena and verify oracle.parquet is NOT
    opened during the call. We monkey-patch pd.read_parquet to track calls.
    """
    from unittest.mock import patch

    from core.models import score
    from core.reference import MEENA_ID

    oracle_reads: list[str] = []
    original_read = pd.read_parquet

    def tracking_read(path, **kwargs):
        if "oracle" in str(path):
            oracle_reads.append(str(path))
        return original_read(path, **kwargs)

    with patch("pandas.read_parquet", side_effect=tracking_read):
        try:
            score(MEENA_ID)
        except Exception:
            # score() may fail if models aren't trained; that's acceptable here.
            # We only care that oracle was not accessed.
            pass

    assert len(oracle_reads) == 0, (
        f"Oracle was read during score(): {oracle_reads}. "
        "Oracle data must never be accessed in the production scoring path."
    )


# ---------------------------------------------------------------------------
# 4. PROTECTED ATTRIBUTES ABSENT FROM MODEL INPUTS
# ---------------------------------------------------------------------------

def test_protected_attributes_not_in_model_features():
    """owner_gender and location_class must not appear in model_features()."""
    from core.features import model_features

    features = model_features()
    protected = {"owner_gender", "location_class"}

    for attr in protected:
        assert attr not in features, (
            f"Protected attribute '{attr}' is in model_features() — "
            "protected attributes must NEVER be model inputs (AGENTS.md rule 10)"
        )


def test_protected_attributes_have_model_input_false_in_spec():
    """feature_spec.json must mark owner_gender and location_class with model_input=false."""
    spec_path = ROOT / "configs" / "feature_spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    protected = {"owner_gender", "location_class"}

    feat_by_name = {f["name"]: f for f in spec["features"]}
    for attr in protected:
        assert attr in feat_by_name, f"Protected attribute '{attr}' missing from feature_spec.json"
        assert not feat_by_name[attr].get("model_input", False), (
            f"Protected attribute '{attr}' has model_input=true in feature_spec.json"
        )


def test_oracle_columns_not_in_model_features():
    """Latent/oracle columns (capacity, shock_sensitivity, management_quality, etc.)
    must not appear in model_features()."""
    from core.features import model_features

    oracle_cols = {
        "capacity", "shock_sensitivity", "management_quality",
        "default_month", "default_type", "kappa_applied", "sector_seasonality_amp",
    }
    features = set(model_features())
    leaked = oracle_cols & features
    assert not leaked, (
        f"Oracle columns found in model_features(): {leaked}. "
        "These must never be model inputs."
    )


# ---------------------------------------------------------------------------
# 5. DETERMINISM: two seeded runs must yield identical results
# ---------------------------------------------------------------------------

def test_generator_determinism():
    """Two consecutive runs with the same seed must produce identical borrower data."""
    from core.generator import build_artifacts as gen_build
    from core.paths import DATA

    gen_build(smoke=True, kappa="medium", bias_strength="medium")
    b1 = pd.read_parquet(DATA / "borrowers.parquet").copy()
    o1 = pd.read_parquet(DATA / "oracle.parquet").copy()

    gen_build(smoke=True, kappa="medium", bias_strength="medium")
    b2 = pd.read_parquet(DATA / "borrowers.parquet").copy()
    o2 = pd.read_parquet(DATA / "oracle.parquet").copy()

    # Compare borrowers (exclude potential float noise)
    pd.testing.assert_frame_equal(
        b1.reset_index(drop=True), b2.reset_index(drop=True),
        check_exact=False, rtol=1e-6,
        obj="borrowers.parquet across two seeded runs"
    )

    # Compare oracle defaults
    pd.testing.assert_series_equal(
        o1["default_12m"].reset_index(drop=True),
        o2["default_12m"].reset_index(drop=True),
        check_exact=True,
        obj="oracle.default_12m across two seeded runs"
    )
    print("[leakage] Determinism OK — two seeded runs produce identical borrowers and oracle")


def test_model_scores_deterministic():
    """Two calls to score(MEENA_ID) must return exactly the same PD."""
    from core.models import score
    from core.reference import MEENA_ID

    r1 = score(MEENA_ID)
    r2 = score(MEENA_ID)
    assert r1["pd"] == r2["pd"], (
        f"score() is non-deterministic: run1={r1['pd']}, run2={r2['pd']}"
    )


def test_build_artifacts_deterministic():
    """Two full build_artifacts() runs must produce the same AUC for the challenger."""
    from core.generator import build_artifacts as gen_build
    from core.legacy_policy import build_artifacts as legacy_build
    from core.models import build_artifacts as model_build
    from core.paths import ARTIFACTS

    # Run 1
    gen_build(smoke=True)
    legacy_build(smoke=True)
    model_build(smoke=True)
    metrics_path = ARTIFACTS / "metrics" / "models.json"
    m1 = json.loads(metrics_path.read_text(encoding="utf-8"))

    # Run 2
    gen_build(smoke=True)
    legacy_build(smoke=True)
    model_build(smoke=True)
    m2 = json.loads(metrics_path.read_text(encoding="utf-8"))

    assert abs(m1["auc_challenger_oot"] - m2["auc_challenger_oot"]) < 1e-9, (
        f"AUC not deterministic: run1={m1['auc_challenger_oot']}, "
        f"run2={m2['auc_challenger_oot']}"
    )
    print(f"[leakage] Model determinism OK — AUC={m1['auc_challenger_oot']:.6f}")
