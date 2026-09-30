"""OWNER: M2. F8 Policy Optimizer (LP relaxation + rounding vs greedy threshold)."""
from __future__ import annotations

from typing import Any

from core.contracts import OptimizeResult
from core.reference import TEST_BORROWER_IDS


def optimize(policy_params: dict[str, Any] | None = None) -> OptimizeResult:
    """Maximise expected profit under loss cap, budget, sector cap, inclusion floor. STUB."""
    return {"approved_ids": TEST_BORROWER_IDS[:12], "expected_profit": 4_200_000.0,
            "expected_loss": 900_000.0, "exposure": 21_000_000.0,
            "fairness_gap": {"women_led": -0.05, "rural": -0.06}}


def build_artifacts(smoke: bool = False) -> None:
    print("[optimizer] STUB - M2 to implement")
