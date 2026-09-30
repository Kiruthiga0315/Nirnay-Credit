"""FROZEN CONTRACTS (Gate 1, H3). Shared by all four members.

Change rule: PR labelled `contract-change`, approved by ALL four members, and the same PR must
update docs/CONTRACTS.md, the stubs in core/*.py and tests/test_contracts.py.

Every result dict carries enough info for the UI to render without extra calls.
STUB results have model_version starting with "stub" -> the UI shows a STUB banner.
"""
from __future__ import annotations

from typing import Any, TypedDict

REFERENCE_BORROWER_ID = "MSME-00001"  # Meena
Borrower = dict[str, Any] | str  # a feature dict (must contain "id") or a borrower id


class Reason(TypedDict):
    feature: str
    text: str      # plain-language sentence, rendered from configs/feature_spec.json
    impact: float  # contribution to PD; positive raises risk


class ScoreResult(TypedDict):
    borrower_id: str
    pd: float                # calibrated probability of default (12m)
    pd_band: str             # "low" | "medium" | "high"
    reasons: list[Reason]    # top 3
    data_confidence: int     # 0-100
    model_version: str


class RecourseAction(TypedDict):
    lever: str               # feature name; must be mutability == "verifiable"
    label: str
    current: float
    target: float
    unit: str
    cost: float              # relative feasibility cost (unitless, >= 0)
    months: float            # estimated months to achieve


class RecourseResult(TypedDict):
    borrower_id: str
    actions: list[RecourseAction]
    new_pd: float
    cost: float
    months: float
    valid_until_model: str   # model version the advice is valid for


class StructureResult(TypedDict):
    borrower_id: str
    target_dscr: float
    tenor_months: int
    schedule: list[float]    # instalment per month (INR)
    p10_band: list[float]    # P10 net cash available for debt service per month (INR)
    default_flat: float      # simulated default rate, flat EMI
    default_matched: float   # simulated default rate, DSCR-matched schedule


class FairnessReport(TypedDict):
    policy: dict[str, Any]                       # e.g. {"mitigation": "reweighing", "strength": 0.5}
    by_group: dict[str, dict[str, float]]        # group -> {n, approval_rate, tpr, ece, ...}
    adverse_impact_ratio: dict[str, float]       # group -> approval ratio vs reference
    tpr_gap: dict[str, float]
    intersectional: list[dict[str, Any]]         # {group, n, approval_rate, ci_low, ci_high, small_n}


class OptimizeResult(TypedDict):
    approved_ids: list[str]
    expected_profit: float   # INR
    expected_loss: float     # INR
    exposure: float          # INR
    fairness_gap: dict[str, float]


class StressResult(TypedDict):
    scenario: str
    expected_loss: float     # INR
    es95: float              # INR, 95% expected shortfall
    segment_losses: dict[str, float]
    first_failing_segment: str
    tornado: list[dict[str, Any]]  # {assumption, low, high} of ES95


class WatchRow(TypedDict):
    borrower_id: str
    month: int
    hazard: float
    rank: int
    action: str              # "call" | "restructure" | "reduce_limit" | "monitor"


class TrustResult(TypedDict):
    borrower_id: str
    data_confidence: int     # 0-100
    flags: list[str]


class AttackResult(TypedDict):
    attack: str              # circular_upi | window_dressing | invoice_round_tripping
    flagged_before: int
    flagged_after: int
    auc_before: float
    auc_after: float


# ---- function signatures (implemented in the module of the owner) ----------------------------
# score(borrower) -> ScoreResult                            core/models.py        M1
# recourse(borrower, levers=None) -> RecourseResult         core/recourse.py      M2
# structure(borrower, target_dscr=1.25) -> StructureResult  core/structuring.py   M2
# fairness_report(policy=None) -> FairnessReport            core/fairness.py      M2
# optimize(policy_params=None) -> OptimizeResult            core/optimizer.py     M2
# stress(scenario, params=None) -> StressResult             core/stress.py        M3
# watchlist(month=25) -> list[WatchRow]                     core/early_warning.py M3
# trust(borrower) -> TrustResult ; attack(kind) -> AttackResult   core/trust.py   M3
# make_cam(borrower) -> bytes ; make_letter(borrower, lang) -> bytes  core/documents.py M4
