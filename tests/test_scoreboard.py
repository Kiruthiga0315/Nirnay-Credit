"""T4: Scoreboard invariant tests.

Structural assertions only — we do NOT assume oracle >= inferred >= approved-only
because that is an empirical expectation, not a structural guarantee.

We assert:
1. iso-loss uses the same loss rate for all models
2. count consistency (n_test, approvals sum up correctly)
3. required keys and types are present
4. expected profit uses the same editable parameters
"""
import json

import pytest

from core.paths import ARTIFACTS


@pytest.fixture(scope="module")
def scoreboard():
    """Load or build scoreboard.json."""
    sb_path = ARTIFACTS / "scoreboard.json"
    if not sb_path.exists():
        # Build the pipeline in smoke mode to generate the scoreboard
        from core.generator import build_artifacts as gen_build
        from core.legacy_policy import build_artifacts as legacy_build
        from core.models import build_artifacts as models_build

        gen_build(smoke=True)
        legacy_build(smoke=True)
        models_build(smoke=True)

    with open(sb_path, encoding="utf-8") as f:
        return json.load(f)


def test_scoreboard_has_required_keys(scoreboard):
    """Scoreboard JSON has all required top-level keys."""
    required = {
        "model_version", "n_test", "legacy_loss_rate", "legacy_approval_rate",
        "iso_loss", "iso_approval", "extra_approvals_at_equal_loss",
        "auc", "subgroups", "expected_profit",
    }
    assert required.issubset(set(scoreboard.keys())), \
        f"Missing keys: {required - set(scoreboard.keys())}"


def test_iso_loss_uses_same_target_rate(scoreboard):
    """iso-loss view: all models evaluated at the same legacy loss rate."""
    target = scoreboard["iso_loss"]["target_loss_rate"]
    assert target == scoreboard["legacy_loss_rate"], \
        "iso-loss target must match legacy_loss_rate"
    assert isinstance(target, float)
    assert 0.0 <= target <= 1.0


def test_iso_approval_uses_same_count(scoreboard):
    """iso-approval view: all models evaluated at the same legacy approval count."""
    target_n = scoreboard["iso_approval"]["target_n_approved"]
    n_legacy = scoreboard["iso_loss"]["approvals"]["legacy"]
    assert target_n == n_legacy, \
        "iso-approval target_n_approved must equal legacy approval count"


def test_iso_loss_has_all_models(scoreboard):
    """iso-loss view contains all four model variants."""
    models = set(scoreboard["iso_loss"]["approvals"].keys())
    expected = {"legacy", "approved_only", "inferred", "oracle"}
    assert models == expected, f"Expected {expected}, got {models}"


def test_iso_approval_has_all_models(scoreboard):
    """iso-approval view contains all four model variants."""
    models = set(scoreboard["iso_approval"]["loss_rates"].keys())
    expected = {"legacy", "approved_only", "inferred", "oracle"}
    assert models == expected


def test_auc_has_all_models(scoreboard):
    """AUC dict contains all four model variants."""
    models = set(scoreboard["auc"].keys())
    expected = {"legacy", "approved_only", "inferred", "oracle"}
    assert models == expected


def test_approval_counts_nonnegative(scoreboard):
    """All approval counts must be non-negative and <= n_test."""
    n_test = scoreboard["n_test"]
    for model, count in scoreboard["iso_loss"]["approvals"].items():
        assert 0 <= count <= n_test, f"{model}: {count} not in [0, {n_test}]"


def test_loss_rates_in_range(scoreboard):
    """All loss rates must be in [0, 1]."""
    for model, rate in scoreboard["iso_approval"]["loss_rates"].items():
        assert 0.0 <= rate <= 1.0, f"{model}: loss rate {rate} not in [0, 1]"


def test_auc_in_range(scoreboard):
    """All AUC values must be in [0, 1]."""
    for model, auc in scoreboard["auc"].items():
        assert 0.0 <= auc <= 1.0, f"{model}: AUC {auc} not in [0, 1]"


def test_subgroups_present(scoreboard):
    """Subgroup breakdowns include thin_file, women_led, rural."""
    expected = {"thin_file", "women_led", "rural"}
    assert expected.issubset(set(scoreboard["subgroups"].keys()))


def test_subgroup_n_positive(scoreboard):
    """Each subgroup has a positive count."""
    for group, data in scoreboard["subgroups"].items():
        assert data["n"] > 0, f"Subgroup {group} has n=0"


def test_expected_profit_has_editable_params(scoreboard):
    """Expected profit section has editable LGD, margin, ticket."""
    ep = scoreboard["expected_profit"]
    assert "lgd" in ep
    assert "margin" in ep
    assert "ticket" in ep
    assert 0.0 < ep["lgd"] < 1.0
    assert 0.0 < ep["margin"] < 1.0
    assert ep["ticket"] > 0


def test_expected_profit_has_all_models(scoreboard):
    """Expected profit contains all four model variants."""
    models = set(scoreboard["expected_profit"]["values"].keys())
    expected = {"legacy", "approved_only", "inferred", "oracle"}
    assert models == expected


def test_extra_approvals_consistent(scoreboard):
    """extra_approvals = inferred approvals - legacy approvals."""
    ea = scoreboard["extra_approvals_at_equal_loss"]
    inferred = scoreboard["iso_loss"]["approvals"]["inferred"]
    legacy = scoreboard["iso_loss"]["approvals"]["legacy"]
    assert ea == inferred - legacy


def test_n_test_positive(scoreboard):
    """n_test is positive."""
    assert scoreboard["n_test"] > 0


def test_model_version_not_stub(scoreboard):
    """Model version does not start with 'stub'."""
    assert not scoreboard["model_version"].startswith("stub")
