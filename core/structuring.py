"""OWNER: M2. F4 DSCR-matched repayment structuring under the P10 cash-flow band."""
from __future__ import annotations

from core.contracts import Borrower, StructureResult
from core.reference import resolve


def structure(borrower: Borrower, target_dscr: float = 1.25) -> StructureResult:
    """Schedule sits under P10 / target_dscr in all but at most one month. STUB values.

    Example: structure("MSME-00001")["default_matched"] < structure("MSME-00001")["default_flat"]
    """
    b = resolve(borrower)
    seasonal = [1.0, 0.9, 0.7, 0.6, 0.7, 0.9, 1.1, 1.2, 1.1, 1.0, 0.9, 1.0]
    p10 = [round(60000 * s, 0) for s in seasonal]
    schedule = [round(x / target_dscr, 0) for x in p10]
    return {"borrower_id": str(b["id"]), "target_dscr": target_dscr, "tenor_months": 12,
            "schedule": schedule, "p10_band": p10, "default_flat": 0.11, "default_matched": 0.07}


def build_artifacts(smoke: bool = False) -> None:
    print("[structuring] STUB - M2 to implement")
