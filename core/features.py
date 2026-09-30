"""OWNER: M2. Feature-spec loader + derived-feature recompute. Reads configs/feature_spec.json."""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from core.paths import CONFIGS


@lru_cache(maxsize=1)
def load_spec() -> dict[str, Any]:
    return json.loads((CONFIGS / "feature_spec.json").read_text(encoding="utf-8"))


def by_name() -> dict[str, dict[str, Any]]:
    return {f["name"]: f for f in load_spec()["features"]}


def model_features() -> list[str]:
    return [f["name"] for f in load_spec()["features"] if f["model_input"]]


def levers() -> list[str]:
    """Recourse levers: verifiable features only."""
    return [f["name"] for f in load_spec()["features"] if f["mutability"] == "verifiable"]


def recompute_derived(row: dict[str, Any]) -> dict[str, Any]:
    """Recompute derived features after a lever changes. M2 extends this."""
    out = dict(row)
    if all(k in out for k in ("receivable_days", "inventory_days", "payable_days")):
        out["cash_conversion_days"] = out["receivable_days"] + out["inventory_days"] - out["payable_days"]
    return out
