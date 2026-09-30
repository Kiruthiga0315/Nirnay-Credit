"""OWNER: M3. F6 stress engine: named replays, contagion, Monte Carlo, tornado.
Scenario definitions: configs/scenarios.yaml. Writes artifacts/stress_<scenario>.json."""
from __future__ import annotations

from typing import Any

import yaml

from core.contracts import StressResult
from core.paths import CONFIGS
from core.reference import stable_unit

_scenarios = None

def load_scenarios() -> dict[str, Any]:
    global _scenarios
    if _scenarios is None:
        p = CONFIGS / "scenarios.yaml"
        if p.exists():
            with open(p, encoding="utf-8") as f:
                _scenarios = yaml.safe_load(f).get("scenarios", {})
        else:
            _scenarios = {}
    return _scenarios

SCENARIO_IDS = list(load_scenarios().keys())

def stress(scenario: str, params: dict[str, Any] | None = None) -> StressResult:
    """Apply a named shock to inputs, re-score, return EL / ES95 / segments. STUB values."""
    scenarios = load_scenarios()
    if scenario not in scenarios:
        raise ValueError(f"Unknown scenario id: {scenario}")
        
    s_hash = stable_unit(scenario, "hash")
    el = 1_000_000.0 + 800_000.0 * s_hash
    es95 = el * (1.5 + 1.0 * stable_unit(scenario, "tail"))
    
    return {
        "scenario": scenario, 
        "expected_loss": round(el, 2), 
        "es95": round(es95, 2),
        "segment_losses": {
            "textile": round(el * 0.35, 2), 
            "retail_trading": round(el * 0.25, 2),
            "services": round(el * 0.15, 2), 
            "logistics": round(el * 0.15, 2)
        },
        "first_failing_segment": "textile" if s_hash > 0.5 else "retail_trading",
        "tornado": [{"assumption": "pass_through", "low": round(es95 * 0.8, 2), "high": round(es95 * 1.2, 2)}]
    }

def build_artifacts(smoke: bool = False) -> None:
    from core.paths import write_json
    scenarios = load_scenarios()
    for s in scenarios:
        res = stress(s)
        write_json(f"stress_{s}.json", res)
    print("[stress] STUB - generated artifacts")
