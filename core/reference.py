"""Reference borrower (Meena) and deterministic helpers for STUB data. FROZEN."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from core.contracts import REFERENCE_BORROWER_ID
from core.paths import CONFIGS

MEENA: dict[str, Any] = json.loads((CONFIGS / "personas" / "meena.json").read_text(encoding="utf-8"))
MEENA_ID = REFERENCE_BORROWER_ID
TEST_BORROWER_IDS = [f"MSME-{i:05d}" for i in range(1, 21)]  # the 20 borrowers Page 2 must load


def stable_unit(key: str, salt: str = "") -> float:
    """Deterministic pseudo-random float in [0, 1) from a string key."""
    h = hashlib.sha256(f"{salt}|{key}".encode()).hexdigest()
    return int(h[:8], 16) / 16**8


def resolve(borrower: Any) -> dict[str, Any]:
    """Accept a dict (with 'id') or an id string; return a feature dict."""
    if isinstance(borrower, dict):
        return borrower
    if borrower == MEENA_ID:
        return dict(MEENA)
    return {"id": str(borrower)}
