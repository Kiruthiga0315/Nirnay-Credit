"""OWNER: M3. F11 data-trust: GST/bank/UPI reconciliation, cycle detection, gaming lab.
Writes artifacts/trust.json, artifacts/gaming_lab.json."""
from __future__ import annotations

from core.contracts import AttackResult, Borrower, TrustResult
from core.reference import resolve, stable_unit

ATTACKS = ["circular_upi", "window_dressing", "invoice_round_tripping"]


def trust(borrower: Borrower) -> TrustResult:
    b = resolve(borrower)
    return {"borrower_id": str(b["id"]), "data_confidence": 70 + int(25 * stable_unit(str(b["id"]), "conf")),
            "flags": []}


def attack(kind: str) -> AttackResult:
    """Before/after AUC and flagged count for one attack. STUB values."""
    k_hash = stable_unit(kind, "hash")
    return {"attack": kind, 
            "flagged_before": int(3 + 5 * k_hash), 
            "flagged_after": int(41 + 10 * k_hash), 
            "auc_before": round(0.78 - 0.05 * k_hash, 2), 
            "auc_after": round(0.74 - 0.02 * k_hash, 2)}


def build_artifacts(smoke: bool = False) -> None:
    from core.paths import write_json
    res = {a: attack(a) for a in ATTACKS}
    write_json("gaming_lab.json", res)
    write_json("trust.json", {"attacks_tested": len(ATTACKS)})
    write_json("metrics/trust.json", {"avg_data_confidence": 75})
    print("[trust] STUB - generated artifacts")
