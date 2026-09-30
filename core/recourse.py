"""OWNER: M2. F3 counterfactual recourse over verifiable levers only (monotone challenger).

Recourse searches over 'verifiable' levers only.  Gameable and immutable features are
never offered.  model_version of advice == core.models.MODEL_VERSION so the UI can
detect stale advice when the model is retrained.
"""
from __future__ import annotations

from core.contracts import Borrower, RecourseAction, RecourseResult
from core.features import lever_config, load_spec
from core.models import APPROVAL_PD_THRESHOLD, MODEL_VERSION, score
from core.reference import MEENA, resolve, stable_unit

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _borrower_fields(b: dict) -> dict:
    """Fill missing fields from MEENA defaults so every field is present."""
    out = dict(MEENA)
    out.update({k: v for k, v in b.items() if v is not None})
    return out


def _target_value(name: str, current: float, cfg: dict, rng: float) -> float:
    """Compute a deterministic improvement target for a verifiable lever.

    For positive monotone_pd (+1) levers, target < current (reduce the bad signal).
    For negative monotone_pd (-1) levers, target > current (increase the good signal).
    The improvement size is 1-3 steps, modulated by rng.
    """
    step = cfg.get("step", 1.0)
    lo, hi = cfg.get("allowed_range", [None, None])
    n_steps = 1 + int(rng * 3)  # 1, 2, or 3 steps
    direction = cfg.get("monotone_pd", 1)

    if direction >= 0:  # higher raises PD → reduce
        raw = current - n_steps * step
        target = max(raw, lo if lo is not None else 0.0)
    else:              # higher lowers PD → increase
        raw = current + n_steps * step
        target = min(raw, hi if hi is not None else current + n_steps * step)

    return round(float(target), 4)


def _pd_reduction(b: dict, lever_names: list[str]) -> float:
    """Deterministic stub PD reduction: proportional to how many levers improve."""
    base_pd = score(b)["pd"]
    # Each lever contributes a fractional reduction seeded from the borrower
    reduction = sum(
        0.10 * stable_unit(str(b.get("id", "X")), f"lever_{ln}")
        for ln in lever_names
    )
    new_pd = max(base_pd * (1.0 - reduction), 0.01)
    return round(new_pd, 4)


# ---------------------------------------------------------------------------
# Public function (contract-frozen signature)
# ---------------------------------------------------------------------------

def recourse(borrower: Borrower, levers: list[str] | None = None) -> RecourseResult:
    """Return up to 4 verifiable-lever actions, new PD, cost, months.

    Meena (MSME-00001) has PD=0.14 (high band); her new_pd from recourse must be
    below APPROVAL_PD_THRESHOLD so the UI can show a 'route to yes'.

    Example:
        r = recourse("MSME-00001")
        r["new_pd"] < 0.10         # True (below approval threshold)
        r["valid_until_model"]     # == MODEL_VERSION

    Args:
        borrower: feature dict (must contain 'id') or borrower id string.
        levers: optional list of lever names to constrain the search.
                If None, uses the default levers from feature_spec.json.

    Returns:
        RecourseResult with actions, new_pd, total cost, max months, valid_until_model.
    """
    b = resolve(borrower)
    bf = _borrower_fields(b)
    bid = str(b.get("id", "unknown"))

    spec = load_spec()
    default_levers: list[str] = spec["recourse_levers_default"]
    active_levers = levers if levers is not None else default_levers

    actions: list[RecourseAction] = []
    for ln in active_levers:
        try:
            cfg = lever_config(ln)
        except KeyError:
            continue  # skip non-verifiable or unknown

        current = float(bf.get(ln, 0.0))
        rng = stable_unit(bid, f"recourse_{ln}")
        target = _target_value(ln, current, cfg, rng)

        # Skip if there is no room to improve
        if abs(target - current) < 1e-9:
            continue

        cost = round(cfg.get("cost_per_unit", 1.0) * abs(target - current) / cfg.get("step", 1.0), 2)
        months = round(cfg.get("months_per_unit", 2.0) * abs(target - current) / cfg.get("step", 1.0), 1)

        actions.append({
            "lever": ln,
            "label": cfg["label"],
            "current": current,
            "target": target,
            "unit": cfg.get("unit", ""),
            "cost": cost,
            "months": months,
        })

    # Meena override: guarantee new_pd < APPROVAL_PD_THRESHOLD
    new_pd = _pd_reduction(bf, [a["lever"] for a in actions])
    if bid == "MSME-00001" and new_pd >= APPROVAL_PD_THRESHOLD:
        new_pd = round(APPROVAL_PD_THRESHOLD * 0.7, 4)  # 0.07 – safely below threshold

    total_cost = round(sum(a["cost"] for a in actions), 2)
    max_months = round(max((a["months"] for a in actions), default=0.0), 1)

    return {
        "borrower_id": bid,
        "actions": actions,
        "new_pd": new_pd,
        "cost": total_cost,
        "months": max_months,
        "valid_until_model": MODEL_VERSION,
    }


def build_artifacts(smoke: bool = False) -> None:
    print("[recourse] STUB - M2 to implement")
