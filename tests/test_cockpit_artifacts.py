import json

from core.models import build_artifacts
from core.paths import ARTIFACTS


def test_model_cockpit_artifacts():
    cockpit_path = ARTIFACTS / "model_cockpit.json"
    if not cockpit_path.exists():
        build_artifacts(smoke=True)
    
    assert cockpit_path.exists(), "Model cockpit artifacts not generated"
    
    with open(cockpit_path, encoding="utf-8") as f:
        artifacts = json.load(f)
        
    assert "roc" in artifacts
    assert "champion" in artifacts["roc"]
    assert "fpr" in artifacts["roc"]["champion"]
    
    assert "ks_curve" in artifacts
    assert "calibration" in artifacts
    assert "ablation" in artifacts
    assert "psi_features" in artifacts
    
    assert "bureau_only" in artifacts["ablation"]
    assert "thin_both" in artifacts["ablation"]
