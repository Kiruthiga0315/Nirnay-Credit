"""OWNER: M1. Champion (WoE logistic), challenger (monotone LightGBM), calibration, score().

Writes: models/champion.pkl, models/challenger.pkl, models/calibrator.pkl,
artifacts/metrics/models.json, artifacts/scoreboard.json, artifacts/sensitivity_grid.json.
"""
from __future__ import annotations

from core.contracts import Borrower, ScoreResult
from core.reference import MEENA_ID, resolve, stable_unit

MODEL_VERSION = "stub-0"
APPROVAL_PD_THRESHOLD = 0.10  # placeholder; M1 derives the real cutoff from the policy


def score(borrower: Borrower) -> ScoreResult:
    """Return calibrated PD, band, top-3 reasons, data confidence. STUB values are deterministic.

    Example: score("MSME-00001") -> {"pd": 0.14, "pd_band": "high", ...}
    """
    b = resolve(borrower)
    bid = str(b["id"])
    pd_ = 0.14 if bid == MEENA_ID else round(0.03 + 0.25 * stable_unit(bid, "pd"), 4)
    band = "low" if pd_ < 0.06 else "medium" if pd_ < 0.12 else "high"
    reasons = [
        {"feature": "receivable_days", "text": "STUB: customers take long to pay.", "impact": 0.030},
        {"feature": "bureau_score", "text": "STUB: thin credit file.", "impact": 0.025},
        {"feature": "cheque_bounces_6m", "text": "STUB: one cheque bounced recently.", "impact": 0.010},
    ]
    return {
        "borrower_id": bid, "pd": pd_, "pd_band": band, "reasons": reasons,
        "data_confidence": 70 + int(25 * stable_unit(bid, "conf")), "model_version": MODEL_VERSION,
    }


def build_artifacts(smoke: bool = False) -> None:
    print("[models] STUB - M1 to implement")
