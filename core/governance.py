"""OWNER: M3. F7 governance backend: model card, decision ledger, consent artefact, override log.
Ledger lives at artifacts/ledger.jsonl (append-only). UI helpers below."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from core.paths import ARTIFACTS, write_json

LEDGER_PATH = ARTIFACTS / "ledger.jsonl"


def _hash_inputs(inputs: dict[str, Any]) -> str:
    """Stable hash of input features for non-repudiation."""
    s = json.dumps(inputs, sort_keys=True, default=str)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def log_decision(
    borrower_id: str,
    model_version: str,
    inputs: dict[str, Any],
    reasons: list[dict[str, Any]],
    decision: str,
    override: bool = False,
    override_reason: str | None = None,
) -> str:
    """Log an immutable decision to the ledger."""
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    h = _hash_inputs(inputs)
    did = f"D-{timestamp[:10].replace('-', '')}-{borrower_id[:8]}-{h[:4]}"
    
    entry = {
        "decision_id": did,
        "timestamp": timestamp,
        "borrower_id": borrower_id,
        "model_version": model_version,
        "inputs_hash": h,
        "reasons": reasons,
        "decision": decision,
        "override": override,
        "override_reason": override_reason
    }
    
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
        
    return did


def ledger(n: int = 10) -> list[dict[str, Any]]:
    """Return the last n ledger entries."""
    if not LEDGER_PATH.exists():
        return []
    with open(LEDGER_PATH, encoding="utf-8") as f:
        lines = f.readlines()
    return [json.loads(line) for line in lines[-n:]]


def challenge_decision(decision_id: str, reason: str) -> None:
    """Entry point for borrower to challenge a decision."""
    log_path = ARTIFACTS / "challenges.jsonl"
    entry = {
        "decision_id": decision_id,
        "timestamp": datetime.now().isoformat(),
        "reason": reason
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def human_override_log(decision_id: str, officer_id: str, new_decision: str, reason: str) -> None:
    """Log an override."""
    log_path = ARTIFACTS / "overrides.jsonl"
    entry = {
        "decision_id": decision_id,
        "officer_id": officer_id,
        "new_decision": new_decision,
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def consent_artifact(borrower_id: str) -> dict[str, Any]:
    return {
        "borrower_id": borrower_id, 
        "purpose": "MSME credit assessment (STUB MOCK - No real AA integration)",
        "fields": ["GST returns", "bank statements", "UPI summary"], 
        "duration_months": 12,
        "minimisation_note": "Only fields required for the credit decision are requested."
    }


def build_artifacts(smoke: bool = False) -> None:
    import pandas as pd

    from core.models import score
    from core.paths import DATA
    
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    
    # Append-only rules test: usually we don't truncate, but for the generator build we reset.
    if LEDGER_PATH.exists():
        LEDGER_PATH.unlink()
        
    borrowers_path = DATA / "borrowers.parquet"
    if borrowers_path.exists():
        borrowers = pd.read_parquet(borrowers_path)
        n_seed = 10 if smoke else 50
        sample = borrowers.head(n_seed)
        
        overrides = 0
        for i, row in sample.iterrows():
            b_dict = row.to_dict()
            res = score(b_dict)
            decision = "approve" if res["pd_band"] == "low" else ("refer" if res["pd_band"] == "medium" else "reject")
            override = False
            override_reason = None
            if i % 10 == 0:
                override = True
                override_reason = "Manual override by officer 104"
                decision = "approve" if decision == "reject" else "reject"
                overrides += 1
                
            log_decision(
                borrower_id=res["borrower_id"],
                model_version=res["model_version"],
                inputs=b_dict,
                reasons=res["reasons"],
                decision=decision,
                override=override,
                override_reason=override_reason
            )
            
        write_json("metrics/governance.json", {"overrides": overrides})
        print(f"[governance] Generated {n_seed} ledger entries.")
    else:
        print("[governance] No borrowers data, skipped.")
