"""OWNER: M2. Feature-spec loader + derived-feature recompute. Reads configs/feature_spec.json."""
from __future__ import annotations

import json
import statistics
from functools import lru_cache
from typing import Any

from core.paths import CONFIGS

_VALID_MUTABILITY = {"immutable", "verifiable", "gameable", "derived"}


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


def lever_config(name: str) -> dict[str, Any]:
    """Return the full spec dict for a named lever; raises KeyError if not a verifiable lever.

    Example:
        cfg = lever_config("receivable_days")
        cfg["step"]          # -> 5
        cfg["cost_per_unit"] # -> 1.5  (illustrative)
    """
    spec = by_name()
    if name not in spec:
        raise KeyError(f"Feature '{name}' not in spec.")
    f = spec[name]
    if f["mutability"] != "verifiable":
        raise KeyError(f"Feature '{name}' is '{f['mutability']}', not 'verifiable'.")
    return f


def validate_spec() -> None:
    """Raise ValueError if the spec is invalid.

    Checks:
    - Every feature has a valid mutability class.
    - Every feature has a non-empty label.
    - No gameable feature has allowed_range + step (would imply it's usable as lever).
    - Protected attributes (owner_gender, location_class) have model_input=False.

    Example:
        validate_spec()  # passes silently on a valid spec
    """
    spec = load_spec()
    seen_names: set[str] = set()
    protected = {"owner_gender", "location_class"}

    for f in spec["features"]:
        name = f["name"]

        # Duplicate check
        if name in seen_names:
            raise ValueError(f"Duplicate feature name: '{name}'")
        seen_names.add(name)

        # Valid mutability class
        mut = f.get("mutability")
        if mut not in _VALID_MUTABILITY:
            raise ValueError(
                f"Feature '{name}' has invalid mutability '{mut}'. "
                f"Must be one of {sorted(_VALID_MUTABILITY)}."
            )

        # Non-empty label
        label = f.get("label", "")
        if not label or not label.strip():
            raise ValueError(f"Feature '{name}' has a missing or empty label.")

        # Gameable features must NOT have a step (that would make them actionable levers)
        if mut == "gameable" and "step" in f:
            raise ValueError(
                f"Gameable feature '{name}' must not have a 'step' field — "
                "it cannot be offered as a recourse lever."
            )

        # Protected attributes must not be model inputs
        if name in protected and f.get("model_input", False):
            raise ValueError(
                f"Protected attribute '{name}' has model_input=true. "
                "Protected attributes must never be model inputs."
            )

        # Verifiable levers must have advice text
        if mut == "verifiable" and not f.get("advice", "").strip():
            raise ValueError(
                f"Verifiable lever '{name}' is missing 'advice' text. "
                "Every lever must have plain-language advice."
            )

        # Verifiable levers must have allowed_range and step
        if mut == "verifiable":
            if "allowed_range" not in f:
                raise ValueError(f"Verifiable lever '{name}' is missing 'allowed_range'.")
            if "step" not in f:
                raise ValueError(f"Verifiable lever '{name}' is missing 'step'.")


def recompute_derived(row: dict[str, Any]) -> dict[str, Any]:
    """Recompute all derived features after a lever change.

    Supported derived features:
    - cash_conversion_days = receivable_days + inventory_days - payable_days
    - inflow_stability_cv  = std(monthly_inflow) / mean(monthly_inflow)  [if monthly_inflow list provided]
    - revenue_growth_3m    = (last_month_revenue / three_months_ago_revenue) - 1  [if monthly_revenue list provided]

    Inputs in *row* that are lists (e.g. 'monthly_inflow', 'monthly_revenue') are used to derive
    scalar summary statistics. Missing inputs leave the derived feature unchanged.

    Example on Meena (receivable_days=78, inventory_days not in meena.json -> skipped):
        out = recompute_derived({"id": "MSME-00001", "receivable_days": 55,
                                  "inventory_days": 40, "payable_days": 30})
        out["cash_conversion_days"]  # -> 65.0

    Example with monthly_inflow:
        out = recompute_derived({"id": "X", "monthly_inflow": [100, 120, 80, 110]})
        out["inflow_stability_cv"]   # -> std/mean of [100, 120, 80, 110]
    """
    out = dict(row)

    # --- cash_conversion_days -------------------------------------------------
    keys_ccc = ("receivable_days", "inventory_days", "payable_days")
    if all(k in out and out[k] is not None for k in keys_ccc):
        out["cash_conversion_days"] = round(
            float(out["receivable_days"])
            + float(out["inventory_days"])
            - float(out["payable_days"]),
            2,
        )

    # --- inflow_stability_cv --------------------------------------------------
    inflows = out.get("monthly_inflow")
    if isinstance(inflows, (list, tuple)) and len(inflows) >= 2:
        mean_inf = statistics.mean(inflows)
        if mean_inf > 0:
            stdev_inf = statistics.pstdev(inflows)
            out["inflow_stability_cv"] = round(stdev_inf / mean_inf, 4)

    # --- revenue_growth_3m ----------------------------------------------------
    revenues = out.get("monthly_revenue")
    if isinstance(revenues, (list, tuple)) and len(revenues) >= 2:
        base = float(revenues[-4]) if len(revenues) >= 4 else float(revenues[0])
        latest = float(revenues[-1])
        if base > 0:
            out["revenue_growth_3m"] = round((latest / base) - 1.0, 4)

    return out
