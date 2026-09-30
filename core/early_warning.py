"""OWNER: M3. F9 discrete-time hazard model + watchlist + lead-time metric.
Writes models/hazard.pkl, artifacts/watchlist.parquet, artifacts/metrics/early_warning.json."""
from __future__ import annotations

from core.contracts import WatchRow
from core.reference import TEST_BORROWER_IDS, stable_unit


def watchlist(month: int = 25) -> list[WatchRow]:
    """Ranked borrowers by hazard with a suggested action. STUB values."""
    rows = sorted(TEST_BORROWER_IDS, key=lambda i: -stable_unit(i, f"h{month}"))[:10]
    actions = ["call", "restructure", "reduce_limit", "monitor"]
    return [{"borrower_id": i, "month": month, "hazard": round(0.02 + 0.2 * stable_unit(i, f"h{month}"), 4),
             "rank": n + 1, "action": actions[n % 4]} for n, i in enumerate(rows)]


def build_artifacts(smoke: bool = False) -> None:
    print("[early_warning] STUB - M3 to implement")
