"""OWNER: M3. F6 stress engine: named replays, contagion, Monte Carlo, tornado.
Scenario definitions: configs/scenarios.yaml. Writes artifacts/stress_<scenario>.json."""
from __future__ import annotations

from typing import Any

from core.contracts import StressResult

SCENARIO_IDS = ["demonetisation_style", "gst_rollout_style", "covid_style",
                "rate_hike_2022_23_style", "custom"]


def stress(scenario: str, params: dict[str, Any] | None = None) -> StressResult:
    """Apply a named shock to inputs, re-score, return EL / ES95 / segments. STUB values."""
    return {"scenario": scenario, "expected_loss": 1_800_000.0, "es95": 4_100_000.0,
            "segment_losses": {"textile": 700_000.0, "retail_trading": 500_000.0,
                               "services": 300_000.0, "logistics": 300_000.0},
            "first_failing_segment": "textile",
            "tornado": [{"assumption": "pass_through", "low": 3_200_000.0, "high": 5_000_000.0}]}


def build_artifacts(smoke: bool = False) -> None:
    print("[stress] STUB - M3 to implement")
