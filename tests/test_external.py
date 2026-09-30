import json
from unittest.mock import patch

import pandas as pd

from core.external import build_artifacts
from core.paths import ARTIFACTS


def test_external_missing_file(tmp_path):
    # It should skip gracefully
    with patch("core.external.DATA", tmp_path):
        build_artifacts(smoke=True)
        # Should output "dataset not loaded yet" in external_validity.json
        out_path = ARTIFACTS / "external_validity.json"
        assert out_path.exists()
        with open(out_path) as f:
            res = json.load(f)
        assert res["status"] == "dataset not loaded yet"

def test_external_with_file(tmp_path):
    # Provide a minimal valid file
    ext_dir = tmp_path / "external"
    ext_dir.mkdir(parents=True)
    df = pd.DataFrame({
        "feature1": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] * 5,
        "feature2": [10, 9, 8, 7, 6, 5, 4, 3, 2, 1] * 5,
        "default_payment_next_month": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1] * 5
    })
    df.to_csv(ext_dir / "dataset.csv", index=False)
    
    with patch("core.external.DATA", tmp_path):
        build_artifacts(smoke=True)
        out_path = ARTIFACTS / "external_validity.json"
        assert out_path.exists()
        with open(out_path) as f:
            res = json.load(f)
        assert res["status"] == "loaded"
        assert "auc_champion" in res["metrics"]
        
        metrics_path = ARTIFACTS / "metrics" / "external.json"
        assert metrics_path.exists()
        with open(metrics_path) as f:
            metrics = json.load(f)
        assert "auc_champion" in metrics
