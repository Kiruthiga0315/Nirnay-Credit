"""T4: Sensitivity grid tests.

Assertions:
1. Grid has exactly 9 cells (3 kappa × 3 bias_strength)
2. Deterministic under seed=42
3. Each cell has required keys
4. Lift and AUC values are numeric
"""
import json

import pytest

from core.paths import ARTIFACTS


@pytest.fixture(scope="module")
def grid():
    """Load or build sensitivity_grid.json."""
    grid_path = ARTIFACTS / "sensitivity_grid.json"
    if not grid_path.exists():
        from core.models import run_grid
        run_grid(smoke=True)

    with open(grid_path, encoding="utf-8") as f:
        return json.load(f)


def test_grid_has_9_cells(grid):
    """Grid must have exactly 9 cells (3×3)."""
    assert grid["n_cells"] == 9
    assert len(grid["cells"]) == 9


def test_grid_has_all_kappa_labels(grid):
    """Grid covers all kappa labels."""
    expected = {"high", "medium", "low"}
    actual = set(grid["kappa_labels"])
    assert expected == actual


def test_grid_has_all_bias_labels(grid):
    """Grid covers all bias_strength labels."""
    expected = {"weak", "medium", "strong"}
    actual = set(grid["bias_labels"])
    assert expected == actual


def test_grid_cells_have_required_keys(grid):
    """Each cell must have the required keys."""
    required = {
        "kappa", "bias_strength", "lift_approvals_at_equal_loss",
        "thin_file_auc_lift", "direction_holds",
        "auc_approved_only", "auc_inferred", "auc_oracle",
        "legacy_loss_rate", "n_test",
    }
    for i, cell in enumerate(grid["cells"]):
        missing = required - set(cell.keys())
        assert not missing, f"Cell {i} missing keys: {missing}"


def test_grid_cells_unique(grid):
    """No duplicate (kappa, bias_strength) pairs."""
    pairs = [(c["kappa"], c["bias_strength"]) for c in grid["cells"]]
    assert len(pairs) == len(set(pairs)), "Duplicate grid cells found"


def test_grid_lift_is_numeric(grid):
    """Lift values are numbers (int or float)."""
    for cell in grid["cells"]:
        assert isinstance(cell["lift_approvals_at_equal_loss"], (int, float))


def test_grid_auc_in_range(grid):
    """All AUC values in [0, 1]."""
    for cell in grid["cells"]:
        for key in ["auc_approved_only", "auc_inferred", "auc_oracle"]:
            assert 0.0 <= cell[key] <= 1.0, f"Cell {cell['kappa']}/{cell['bias_strength']}: {key}={cell[key]}"


def test_grid_direction_holds_is_bool(grid):
    """direction_holds is a boolean."""
    for cell in grid["cells"]:
        assert isinstance(cell["direction_holds"], bool)


def test_grid_n_test_positive(grid):
    """Each cell has positive n_test."""
    for cell in grid["cells"]:
        assert cell["n_test"] > 0


def test_grid_deterministic(grid):
    """Grid is deterministic: running again should give the same results.

    We test this by checking that the first cell's lift is the same
    as what we loaded (fixture is cached at module scope).
    """
    from core.models import run_grid
    grid2 = run_grid(smoke=True)
    for i in range(len(grid["cells"])):
        assert grid["cells"][i]["lift_approvals_at_equal_loss"] == \
            grid2["cells"][i]["lift_approvals_at_equal_loss"], \
            f"Cell {i} not deterministic"


def test_grid_model_version(grid):
    """Grid model version does not start with 'stub'."""
    assert not grid["model_version"].startswith("stub")
