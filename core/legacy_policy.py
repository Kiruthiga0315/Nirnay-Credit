"""OWNER: M1. Stochastic legacy lender policy (bureau + collateral + noise + 5-10% overrides).

T4: Legacy policy generates observed_outcomes.parquet (outcomes ONLY for approved loans).
Oracle outcomes for everyone live in data/oracle.parquet and are never read by models.

The policy score is:
  score = w_bureau * normalised_bureau + w_collateral * collateral_value_ratio + noise
  approve if score > cutoff, PLUS 5-10% manual overrides/exceptions.

Overrides create overlap between approved and rejected populations, so reject
inference is identifiable (Blueprint L3).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.paths import CONFIGS, DATA, write_metrics


def _load_legacy_config() -> dict:
    """Load legacy policy parameters from grid.yaml."""
    import yaml
    with open(CONFIGS / "generator" / "grid.yaml", encoding="utf-8") as f:
        grid = yaml.safe_load(f)
    return grid["legacy_policy"]


def build_artifacts(smoke: bool = False) -> None:
    """Apply legacy policy to borrowers, write observed_outcomes.parquet.

    The legacy policy is STOCHASTIC:
    1. Score = f(bureau_score, collateral_value_ratio) + Gaussian noise
    2. Approve if score > cutoff
    3. 5-10% manual overrides: some below-cutoff firms get approved (exceptions)
       and some above-cutoff firms get rejected (errors/manual holds)
    4. Outcomes are observed ONLY for approved firms
    """
    # Load data produced by generator
    borrowers = pd.read_parquet(DATA / "borrowers.parquet")
    oracle = pd.read_parquet(DATA / "oracle.parquet")
    policy_cfg = _load_legacy_config()

    seed = 42  # deterministic
    rng = np.random.RandomState(seed)

    n = len(borrowers)
    noise_sd = policy_cfg.get("noise_sd", 0.15)
    override_rate = policy_cfg.get("override_rate", 0.075)

    # --- Compute legacy score ---
    # Normalise bureau score to [0, 1]; thin-file (NaN) gets a penalty (0.3)
    bureau = borrowers["bureau_score"].values.copy().astype(float)
    has_bureau = ~np.isnan(bureau)
    bureau_norm = np.full(n, 0.3)  # thin-file penalty
    bureau_norm[has_bureau] = (bureau[has_bureau] - 300.0) / 600.0  # [0, 1]

    collateral = borrowers["collateral_value_ratio"].values.astype(float)
    collateral_norm = np.clip(collateral / 2.0, 0, 1)  # [0, 1]

    # Weighted score
    w_bureau = 0.6
    w_collateral = 0.4
    noise = rng.normal(0, noise_sd, size=n)
    score = w_bureau * bureau_norm + w_collateral * collateral_norm + noise

    # --- Approval decision ---
    # Cutoff calibrated so approval rate ~ 60-70%
    cutoff = float(np.percentile(score, 35))  # top 65% approved

    base_approved = score > cutoff

    # --- Manual overrides (T4: 5-10%) ---
    # Split override budget: ~60% are exceptions (below cutoff approved),
    # ~40% are manual holds (above cutoff rejected)
    override_mask = rng.rand(n) < override_rate

    # Override direction: for firms below cutoff, override means approve
    # For firms above cutoff, override means reject
    approved = base_approved.copy()
    n_exception_approvals = 0
    n_exception_rejections = 0

    for i in range(n):
        if override_mask[i]:
            if not base_approved[i]:
                # Exception: approve a below-cutoff firm
                approved[i] = True
                n_exception_approvals += 1
            else:
                # Manual hold: reject an above-cutoff firm
                approved[i] = False
                n_exception_rejections += 1

    # --- Observed outcomes (only for approved firms) ---
    approved_ids = borrowers.loc[approved, "id"].values
    oracle_approved = oracle[oracle["id"].isin(approved_ids)].copy()

    observed = pd.DataFrame({
        "id": oracle_approved["id"].values,
        "default_12m": oracle_approved["default_12m"].values,
    })

    # --- Legacy decision table (for all firms, used by scoreboard) ---
    legacy_decisions = pd.DataFrame({
        "id": borrowers["id"].values,
        "legacy_score": score,
        "legacy_approved": approved.astype(int),
        "legacy_cutoff": cutoff,
        "has_bureau": has_bureau.astype(int),
        "override": override_mask.astype(int),
    })

    # --- Write artifacts ---
    DATA.mkdir(exist_ok=True, parents=True)
    observed.to_parquet(DATA / "observed_outcomes.parquet", index=False)
    legacy_decisions.to_parquet(DATA / "legacy_decisions.parquet", index=False)

    # --- Metrics ---
    approval_rate = float(approved.mean())
    override_share = float(override_mask.mean())
    n_approved_below = int(n_exception_approvals)
    n_rejected_above = int(n_exception_rejections)

    # Group-level approval rates
    female_mask = borrowers["owner_gender"].values == "female"
    male_mask = borrowers["owner_gender"].values == "male"
    rural_mask = borrowers["location_class"].values == "rural"
    metro_mask = borrowers["location_class"].values == "metro"
    urban_mask = borrowers["location_class"].values == "urban"

    female_approval = float(approved[female_mask].mean()) if female_mask.any() else 0.0
    male_approval = float(approved[male_mask].mean()) if male_mask.any() else 0.0
    rural_approval = float(approved[rural_mask].mean()) if rural_mask.any() else 0.0
    metro_approval = float(approved[metro_mask].mean()) if metro_mask.any() else 0.0
    urban_approval = float(approved[urban_mask].mean()) if urban_mask.any() else 0.0

    # Default rate among approved (observed)
    observed_default_rate = float(observed["default_12m"].mean()) if len(observed) > 0 else 0.0

    write_metrics("legacy_policy", {
        "approval_rate": approval_rate,
        "override_share": override_share,
        "n_approved_below_cutoff": n_approved_below,
        "n_rejected_above_cutoff": n_rejected_above,
        "cutoff": cutoff,
        "female_approval_rate": female_approval,
        "male_approval_rate": male_approval,
        "rural_approval_rate": rural_approval,
        "metro_approval_rate": metro_approval,
        "urban_approval_rate": urban_approval,
        "observed_default_rate": observed_default_rate,
        "n_approved": int(approved.sum()),
        "n_rejected": int((~approved).sum()),
    })

    print(f"[legacy_policy] approval_rate={approval_rate:.3f}, "
          f"override_share={override_share:.3f}, "
          f"exceptions_below_cutoff={n_approved_below}, "
          f"holds_above_cutoff={n_rejected_above}, "
          f"observed_default_rate={observed_default_rate:.3f}")
