"""OWNER: M3. F7 governance backend: model card, decision ledger, consent artefact, override log.
Ledger lives at artifacts/ledger.jsonl (append-only). UI helpers below."""
from __future__ import annotations

from typing import Any


def ledger(n: int = 10) -> list[dict[str, Any]]:
    return [{"decision_id": f"D-{i:04d}", "borrower_id": f"MSME-{i:05d}", "model_version": "stub-0",
             "decision": "approve" if i % 2 else "refer", "override": False} for i in range(1, n + 1)]


def consent_artifact(borrower_id: str) -> dict[str, Any]:
    return {"borrower_id": borrower_id, "purpose": "MSME credit assessment (STUB)",
            "fields": ["GST returns", "bank statements", "UPI summary"], "duration_months": 12,
            "minimisation_note": "Only fields required for the credit decision are requested."}


def build_artifacts(smoke: bool = False) -> None:
    import json

    from core.paths import ARTIFACTS, write_json
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACTS / "ledger.jsonl", "w", encoding="utf-8") as f:
        for row in ledger(10):
            f.write(json.dumps(row) + "\n")
    write_json("metrics/governance.json", {"overrides": 0})
    print("[governance] STUB - generated artifacts")
