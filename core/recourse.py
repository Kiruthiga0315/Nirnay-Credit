"""OWNER: M2. F3 counterfactual recourse over verifiable levers only (monotone challenger)."""
from __future__ import annotations

from core.contracts import Borrower, RecourseResult
from core.models import MODEL_VERSION, score
from core.reference import MEENA, resolve


def recourse(borrower: Borrower, levers: list[str] | None = None) -> RecourseResult:
    """Return up to 4 verifiable-lever actions, new PD, cost, months. STUB values.

    Example: recourse("MSME-00001")["new_pd"] -> 0.08 (stub)
    """
    b = resolve(borrower)
    cur = float(b.get("receivable_days", MEENA["receivable_days"]))
    dig = float(b.get("invoice_digitisation_share", MEENA["invoice_digitisation_share"]))
    actions = [
        {"lever": "receivable_days", "label": "Reduce receivable days", "current": cur,
         "target": max(30.0, cur - 20), "unit": "days", "cost": 2.0, "months": 4.0},
        {"lever": "invoice_digitisation_share", "label": "Digitise invoices", "current": dig,
         "target": min(1.0, dig + 0.25), "unit": "share", "cost": 1.0, "months": 2.0},
    ]
    p = score(b)["pd"]
    return {"borrower_id": str(b["id"]), "actions": actions, "new_pd": round(p * 0.57, 4),
            "cost": 3.0, "months": 4.0, "valid_until_model": MODEL_VERSION}


def build_artifacts(smoke: bool = False) -> None:
    print("[recourse] STUB - M2 to implement")
