"""OWNER: M1. F1 synthetic MSME generator (Blueprint 5.2).

Writes: data/borrowers.parquet, data/panel.parquet, data/oracle.parquet (true outcomes; NEVER
loaded by any model), data/observed_outcomes.parquet (legacy-approved only), data/generator_meta.json.
Must inject configs/personas/meena.json as MSME-00001.
CLI: python -m core.generator --smoke [--config kappa=medium,bias_strength=medium]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from core.paths import CONFIGS, DATA, write_metrics

# ---------------------------------------------------------------------------
# Default-rate calibration target.
# TODO(verify): RBI Financial Stability Report (Jun 2024) reports MSME NPA
#   ratio ~5-8%. We target ~8% 12-month default rate for medium-kappa as a
#   plausible upper bound for unsecured MSME lending. This is an illustrative
#   parameter under our documented assumptions.
# ---------------------------------------------------------------------------
_DEFAULT_RATE_TARGET = 0.08  # 12-month horizon, medium kappa

# Sector seasonality profiles (amplitude of seasonal revenue swing)
_SECTOR_SEASONALITY = {
    "textile": 0.30,
    "food_processing": 0.20,
    "auto_components": 0.15,
    "retail_trading": 0.25,
    "logistics": 0.10,
    "services": 0.08,
}

# Sector-specific phase offsets (months) for seasonal peaks
_SECTOR_PHASE = {
    "textile": 3,       # peaks around festival season
    "food_processing": 0,
    "auto_components": 6,
    "retail_trading": 3,
    "logistics": 9,
    "services": 0,
}


def load_config(kappa: str = "medium", bias_strength: str = "medium") -> dict[str, Any]:
    """Load generator config for a given (kappa, bias_strength) grid cell."""
    with open(CONFIGS / "generator" / "grid.yaml", encoding="utf-8") as f:
        grid = yaml.safe_load(f)
    return {
        "n_firms": grid["n_firms"],
        "n_firms_smoke": grid["n_firms_smoke"],
        "seed": grid["seed"],
        "months": grid["months"],
        "oot_split": grid["oot_split"],
        "kappa": grid["axes"]["kappa"][kappa],
        "kappa_label": kappa,
        "bias_strength": grid["axes"]["bias_strength"][bias_strength],
        "bias_strength_label": bias_strength,
        "legacy_policy": grid["legacy_policy"],
        "default_rate_target": grid.get("default_rate_target", _DEFAULT_RATE_TARGET),
    }


def _generate_latents(n: int, rng: np.random.RandomState) -> pd.DataFrame:
    """T1: generate hidden latent variables for each firm.

    These are NEVER exposed to any model — stored only in oracle.parquet.
    - capacity: true repayment capacity (0.3–1.8)
    - shock_sensitivity: vulnerability to solvency shocks (0–1)
    - management_quality: management competence (0.3–1.0)
    - sector_seasonality_amp: amplitude of seasonal revenue swings
    """
    return pd.DataFrame({
        "capacity": rng.uniform(0.3, 1.8, size=n),
        "shock_sensitivity": rng.beta(2, 5, size=n),  # skewed low
        "management_quality": rng.beta(5, 2, size=n) * 0.7 + 0.3,  # skewed high, [0.3, 1.0]
    })


def _generate_entities(n: int, spec: list[dict], rng: np.random.RandomState) -> pd.DataFrame:
    """Generate the observable entity-level features from feature_spec."""
    df = pd.DataFrame()
    for feat in spec:
        name = feat["name"]
        dtype = feat["type"]
        if name == "bureau_score":
            continue  # handled separately with bias mechanism
        if dtype == "cat":
            cats = feat["categories"]
            df[name] = rng.choice(cats, size=n)
        elif dtype == "int":
            low, high = feat.get("allowed_range", [0, 100])
            if high is None:
                high = 1000000
            df[name] = rng.randint(low, high + 1, size=n)
        elif dtype == "float":
            low, high = feat.get("allowed_range", [0, 1])
            if high is None:
                high = 10000000
            df[name] = rng.uniform(low, high, size=n)
    return df


def _apply_bureau_bias(df: pd.DataFrame, config: dict, rng: np.random.RandomState) -> np.ndarray:
    """T3: bias mechanism — women-led and rural firms have lower bureau coverage.

    True capacity is independent of gender given features. The only channel
    is bureau *coverage* (thin-file), so the legacy policy (which depends
    on bureau score) rejects them more. bias_strength scales the coverage gap.
    """
    n = len(df)
    b_strength = config["bias_strength"]
    base_thin = config["legacy_policy"].get("thin_file_share", 0.35)

    missing_prob = np.full(n, base_thin, dtype=float)
    # Women-led: higher missing probability
    missing_prob += np.where(df["owner_gender"].values == "female",
                             0.06 * b_strength, -0.04 * b_strength)
    # Rural: higher; metro: lower
    missing_prob += np.where(
        df["location_class"].values == "rural",
        0.06 * b_strength,
        np.where(df["location_class"].values == "metro",
                 -0.06 * b_strength, 0.0),
    )
    missing_prob = np.clip(missing_prob, 0.05, 0.95)

    is_missing = rng.rand(n) < missing_prob
    bureau_vals = rng.uniform(300.0, 900.0, size=n)
    bureau_vals[is_missing] = np.nan
    return bureau_vals


def _generate_panel(
    firm_ids: np.ndarray,
    entities: pd.DataFrame,
    latents: pd.DataFrame,
    config: dict,
    rng: np.random.RandomState,
) -> pd.DataFrame:
    """Generate monthly panel signals as noisy functions of latents (T1)."""
    months = config["months"]
    n_firms = len(firm_ids)
    n_rows = n_firms * months

    # Repeat latents and entity info across months
    capacity = np.repeat(latents["capacity"].values, months)
    mgmt_q = np.repeat(latents["management_quality"].values, months)

    sectors = entities["sector"].values if "sector" in entities.columns else np.full(n_firms, "services")
    sector_amp = np.array([_SECTOR_SEASONALITY.get(s, 0.1) for s in sectors])
    sector_phase = np.array([_SECTOR_PHASE.get(s, 0) for s in sectors])

    month_arr = np.tile(np.arange(1, months + 1), n_firms)

    # Sector-specific seasonality
    amp_rep = np.repeat(sector_amp, months)
    phase_rep = np.repeat(sector_phase, months)
    seasonality = amp_rep * np.sin(2 * np.pi * (month_arr - phase_rep) / 12) + 1.0

    # Base revenue driven by capacity and management quality
    base_revenue = 500000 * capacity * mgmt_q * seasonality
    noise = rng.normal(1.0, 0.10, size=n_rows)

    revenue = base_revenue * noise
    revenue = np.maximum(revenue, 10000)  # floor

    panel = pd.DataFrame({
        "id": np.repeat(firm_ids, months),
        "month": month_arr,
        "revenue": revenue,
        "upi_inflow": revenue * rng.uniform(0.3, 0.6, size=n_rows),
        "bank_inflow": revenue * rng.uniform(0.4, 0.7, size=n_rows),
        "avg_bank_balance": revenue * 0.15 * mgmt_q + rng.normal(30000, 8000, size=n_rows),
        "gst_turnover": revenue * rng.uniform(0.90, 1.10, size=n_rows),
        "gstr1_3b_mismatch": np.clip(
            rng.exponential(0.03, size=n_rows) / mgmt_q, 0, 1
        ),
        "gst_filing_delay_days": np.clip(
            rng.exponential(5, size=n_rows) / mgmt_q, 0, 60
        ),
        "receivable_days": np.clip(
            rng.normal(60, 15, size=n_rows) / capacity, 15, 150
        ),
        "utility_delay_days": np.clip(
            rng.exponential(2, size=n_rows) / mgmt_q, 0, 60
        ),
        "cheque_bounces": rng.poisson(np.clip(0.8 / capacity, 0.05, 5), size=n_rows),
    })
    return panel


def _compute_defaults(
    firm_ids: np.ndarray,
    latents: pd.DataFrame,
    panel: pd.DataFrame,
    entities: pd.DataFrame,
    config: dict,
    rng: np.random.RandomState,
) -> pd.DataFrame:
    """T2: 12-month default mechanism.

    Monthly hazard driven by:
    1. Cash shortfall (DSCR < 1 for k consecutive months = TIMING default)
    2. Solvency shocks (random adverse events)

    kappa sets the timing share: kappa * timing_hazard + (1-kappa) * solvency_hazard.
    Calibrate overall default rate to config target.
    """
    months = config["months"]
    n_firms = len(firm_ids)
    kappa = config["kappa"]

    capacity = latents["capacity"].values
    shock_sens = latents["shock_sensitivity"].values
    mgmt_q = latents["management_quality"].values

    # --- Monthly obligation: realistic EMI based on requested_amount ---
    # Assume 12-month tenor, ~12% annual rate => monthly EMI ≈ amount / 11
    requested = entities["requested_amount"].values.astype(float)
    monthly_obligation = requested / 11.0  # rough EMI

    # --- Build DSCR matrix efficiently ---
    # Pivot panel to (n_firms, months) revenue matrix
    panel_sorted = panel.sort_values(["id", "month"])
    revenue_matrix = panel_sorted["revenue"].values.reshape(n_firms, months)
    dscr_matrix = revenue_matrix / monthly_obligation[:, np.newaxis]

    # --- TIMING defaults: DSCR < 1 for k consecutive months ---
    k_consecutive = 3
    timing_default_month = np.zeros(n_firms, dtype=int)
    below_threshold = dscr_matrix < 1.0

    for firm_idx in range(n_firms):
        consecutive = 0
        for m in range(months):
            if below_threshold[firm_idx, m]:
                consecutive += 1
                if consecutive >= k_consecutive:
                    timing_default_month[firm_idx] = m + 1
                    break
            else:
                consecutive = 0

    # --- SOLVENCY defaults: monthly shock hazard ---
    # Base hazard calibrated so cumulative 36-month solvency default ≈ 8-12%
    # for an average firm. h_monthly ≈ 1 - (1-target)^(1/36) ≈ 0.0023 for 8%
    # Scale by shock_sensitivity (mean ~0.29) and inverse capacity.
    base_solvency_hazard = 0.008  # per-month, before firm adjustments
    solvency_default_month = np.zeros(n_firms, dtype=int)

    for firm_idx in range(n_firms):
        h = (base_solvency_hazard *
             (0.3 + shock_sens[firm_idx]) /
             np.clip(mgmt_q[firm_idx] * capacity[firm_idx], 0.15, 2.0))
        for m in range(months):
            if rng.rand() < h:
                solvency_default_month[firm_idx] = m + 1
                break

    # --- Combine: kappa controls the mix ---
    default_month = np.zeros(n_firms, dtype=int)
    default_type = np.full(n_firms, "", dtype=object)

    for firm_idx in range(n_firms):
        t_def = timing_default_month[firm_idx]
        s_def = solvency_default_month[firm_idx]

        if t_def > 0 and s_def > 0:
            # Both triggered — take whichever is earlier
            if t_def <= s_def:
                default_month[firm_idx] = t_def
                default_type[firm_idx] = "timing"
            else:
                default_month[firm_idx] = s_def
                default_type[firm_idx] = "solvency"
        elif t_def > 0:
            # Timing only — accept with probability kappa
            if rng.rand() < kappa:
                default_month[firm_idx] = t_def
                default_type[firm_idx] = "timing"
        elif s_def > 0:
            # Solvency only — accept with probability (1 - kappa)
            if rng.rand() < (1.0 - kappa):
                default_month[firm_idx] = s_def
                default_type[firm_idx] = "solvency"

    # 12-month default indicator (for the train window: months 1-24)
    default_12m = (default_month > 0) & (default_month <= 12)

    oracle = pd.DataFrame({
        "id": firm_ids,
        "capacity": capacity,
        "shock_sensitivity": shock_sens,
        "management_quality": mgmt_q,
        "default_month": default_month,
        "default_type": default_type,
        "default_12m": default_12m.astype(int),
        "kappa_applied": kappa,
    })
    return oracle


def _add_oot_split(borrowers: pd.DataFrame, config: dict) -> pd.DataFrame:
    """T5: add out-of-time split columns. Train: months 1-24, test: 25-36."""
    oot = config["oot_split"]
    train_start, train_end = oot["train_months"]
    test_start, test_end = oot["test_months"]
    borrowers["oot_train_start"] = train_start
    borrowers["oot_train_end"] = train_end
    borrowers["oot_test_start"] = test_start
    borrowers["oot_test_end"] = test_end
    return borrowers


def build_artifacts(smoke: bool = False, kappa: str = "medium", bias_strength: str = "medium") -> None:
    """Main entry point: generate all data artifacts."""
    config = load_config(kappa=kappa, bias_strength=bias_strength)
    n_firms = config["n_firms_smoke"] if smoke else config["n_firms"]
    rng = np.random.RandomState(config["seed"])

    with open(CONFIGS / "feature_spec.json", encoding="utf-8") as f:
        spec = json.load(f)

    # --- Generate n_gen synthetic firms (Meena is prepended) ---
    n_gen = n_firms - 1
    entities = _generate_entities(n_gen, spec["features"], rng)
    entities.insert(0, "id", [f"MSME-{i:05d}" for i in range(2, n_gen + 2)])

    # Bureau scores with bias mechanism (T3)
    entities["bureau_score"] = _apply_bureau_bias(entities, config, rng)

    # --- Latents (T1) ---
    latents_gen = _generate_latents(n_gen, rng)

    # --- Inject Meena as MSME-00001 ---
    with open(CONFIGS / "personas" / "meena.json", encoding="utf-8") as f:
        meena = json.load(f)
    meena.pop("_note", None)

    # Add any feature_spec columns missing from meena
    for col in entities.columns:
        if col not in meena and col != "id":
            meena[col] = entities[col].iloc[0]

    meena_df = pd.DataFrame([meena])

    # Align columns between meena and entities
    for col in meena_df.columns:
        if col not in entities.columns:
            if isinstance(meena_df[col].iloc[0], str):
                entities[col] = ""
            else:
                entities[col] = np.nan
    for col in entities.columns:
        if col not in meena_df.columns:
            meena_df[col] = entities[col].iloc[0]

    # Ensure column order matches
    col_order = list(meena_df.columns)
    entities = entities[col_order]

    # Cast types to match
    for col in entities.columns:
        if col in meena_df.columns:
            meena_df[col] = meena_df[col].astype(entities[col].dtype)

    borrowers = pd.concat([meena_df, entities], ignore_index=True)

    # Meena latents: good capacity, low shock sensitivity, high management quality
    meena_latents = pd.DataFrame({
        "capacity": [1.2],
        "shock_sensitivity": [0.15],
        "management_quality": [0.85],
    })
    latents_all = pd.concat([meena_latents, latents_gen], ignore_index=True)

    # Add sector_seasonality_amp to latents
    sectors = borrowers["sector"].values
    latents_all["sector_seasonality_amp"] = [_SECTOR_SEASONALITY.get(s, 0.1) for s in sectors]

    # --- OOT split columns (T5) ---
    borrowers = _add_oot_split(borrowers, config)

    # --- Panel (T1: noisy functions of latents) ---
    firm_ids = borrowers["id"].values
    panel_df = _generate_panel(firm_ids, borrowers, latents_all, config, rng)

    # --- Defaults (T2: hazard mechanism) ---
    oracle_df = _compute_defaults(firm_ids, latents_all, panel_df, borrowers, config, rng)
    # Merge remaining latent columns
    oracle_df["sector_seasonality_amp"] = latents_all["sector_seasonality_amp"].values

    # --- Write artifacts ---
    DATA.mkdir(exist_ok=True, parents=True)
    borrowers.to_parquet(DATA / "borrowers.parquet", index=False)
    panel_df.to_parquet(DATA / "panel.parquet", index=False)
    oracle_df.to_parquet(DATA / "oracle.parquet", index=False)

    # --- Generator meta ---
    def file_hash(path: Path) -> str:
        return hashlib.md5(path.read_bytes()).hexdigest()

    meta = {
        "seed": config["seed"],
        "config": {k: v for k, v in config.items()},
        "row_counts": {
            "borrowers": len(borrowers),
            "panel": len(panel_df),
            "oracle": len(oracle_df),
        },
        "file_hashes": {
            "borrowers": file_hash(DATA / "borrowers.parquet"),
            "panel": file_hash(DATA / "panel.parquet"),
        },
    }
    with open(DATA / "generator_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)

    # --- Metrics ---
    total_thin = float(borrowers["bureau_score"].isna().mean())
    female_mask = borrowers["owner_gender"] == "female"
    male_mask = borrowers["owner_gender"] == "male"
    rural_mask = borrowers["location_class"] == "rural"
    urban_mask = borrowers["location_class"] == "urban"
    metro_mask = borrowers["location_class"] == "metro"

    default_rate_12m = float(oracle_df["default_12m"].mean())
    timing_defaults = oracle_df[oracle_df["default_type"] == "timing"]
    solvency_defaults = oracle_df[oracle_df["default_type"] == "solvency"]
    timing_share = len(timing_defaults) / max(1, len(oracle_df[oracle_df["default_12m"] == 1]))

    write_metrics("generator", {
        "thin_file_share_total": total_thin,
        "thin_file_share_female": float(borrowers.loc[female_mask, "bureau_score"].isna().mean()),
        "thin_file_share_male": float(borrowers.loc[male_mask, "bureau_score"].isna().mean()),
        "thin_file_share_rural": float(borrowers.loc[rural_mask, "bureau_score"].isna().mean()),
        "thin_file_share_urban": float(borrowers.loc[urban_mask, "bureau_score"].isna().mean()),
        "thin_file_share_metro": float(borrowers.loc[metro_mask, "bureau_score"].isna().mean()),
        "default_rate_12m": default_rate_12m,
        "default_rate_target": config["default_rate_target"],
        "timing_share_of_defaults": timing_share,
        "n_timing_defaults": len(timing_defaults),
        "n_solvency_defaults": len(solvency_defaults),
        "n_firms": len(borrowers),
        "kappa": config["kappa"],
        "kappa_label": config["kappa_label"],
        "bias_strength": config["bias_strength"],
        "bias_strength_label": config["bias_strength_label"],
    })

    print(f"[generator] {len(borrowers)} firms, {len(panel_df)} panel rows, "
          f"default_rate_12m={default_rate_12m:.3f}, timing_share={timing_share:.3f}, "
          f"thin_file={total_thin:.3f}, kappa={config['kappa_label']}, "
          f"bias={config['bias_strength_label']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--config", type=str, default="kappa=medium,bias_strength=medium")
    args = parser.parse_args()

    cfg_dict = dict(item.split("=") for item in args.config.split(",")) if args.config else {}
    k_val = cfg_dict.get("kappa", "medium")
    b_val = cfg_dict.get("bias_strength", "medium")
    build_artifacts(smoke=args.smoke, kappa=k_val, bias_strength=b_val)
