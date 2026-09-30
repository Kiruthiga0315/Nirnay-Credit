"""OWNER: M1. F1 synthetic MSME generator (Blueprint 5.2).

Writes: data/borrowers.parquet, data/panel.parquet, data/oracle.parquet (true outcomes; NEVER
loaded by any model), data/generator_meta.json. Must inject configs/personas/meena.json as
MSME-00001. CLI: python -m core.generator --smoke [--config kappa=medium,bias_strength=medium]
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


def load_config(kappa: str = "medium", bias_strength: str = "medium") -> dict[str, Any]:
    with open(CONFIGS / "generator" / "grid.yaml", encoding="utf-8") as f:
        grid = yaml.safe_load(f)
    return {
        "n_firms": grid["n_firms"],
        "n_firms_smoke": grid["n_firms_smoke"],
        "seed": grid["seed"],
        "months": grid["months"],
        "kappa": grid["axes"]["kappa"][kappa],
        "bias_strength": grid["axes"]["bias_strength"][bias_strength],
        "legacy_policy": grid["legacy_policy"],
    }


def build_artifacts(smoke: bool = False, kappa: str = "medium", bias_strength: str = "medium") -> None:
    config = load_config(kappa=kappa, bias_strength=bias_strength)
    n_firms = config["n_firms_smoke"] if smoke else config["n_firms"]
    np.random.seed(config["seed"])

    with open(CONFIGS / "feature_spec.json", encoding="utf-8") as f:
        spec = json.load(f)

    n_gen = n_firms - 1
    df = pd.DataFrame()
    df["id"] = [f"MSME-{i:05d}" for i in range(2, n_gen + 2)]

    # Generate all non-bureau features first
    for feat in spec["features"]:
        name = feat["name"]
        dtype = feat["type"]
        if name == "bureau_score":
            continue
        if dtype == "cat":
            cats = feat["categories"]
            df[name] = np.random.choice(cats, size=n_gen)
        elif dtype == "int":
            low, high = feat.get("allowed_range", [0, 100])
            if high is None:
                high = 1000000
            df[name] = np.random.randint(low, high, size=n_gen)
        elif dtype == "float":
            low, high = feat.get("allowed_range", [0, 1])
            if high is None:
                high = 10000000
            df[name] = np.random.uniform(low, high, size=n_gen)

    # Generate bureau_score with conditioned thin-file missingness
    b_strength = config["bias_strength"]
    base_thin = config["legacy_policy"].get("thin_file_share", 0.35)

    missing_prob = np.full(n_gen, base_thin)
    missing_prob += np.where(df["owner_gender"] == "female", 0.06 * b_strength, -0.04 * b_strength)
    missing_prob += np.where(
        df["location_class"] == "rural",
        0.06 * b_strength,
        np.where(df["location_class"] == "metro", -0.06 * b_strength, 0.0),
    )
    missing_prob = np.clip(missing_prob, 0.05, 0.95)

    is_missing = np.random.rand(n_gen) < missing_prob
    bureau_vals = np.random.uniform(300.0, 900.0, size=n_gen)
    bureau_vals[is_missing] = np.nan
    df["bureau_score"] = bureau_vals

    with open(CONFIGS / "personas" / "meena.json", encoding="utf-8") as f:
        meena = json.load(f)

    meena.pop("_note", None)

    # Fill remaining required columns for meena if they don't exist in json but exist in df
    for col in df.columns:
        if col not in meena and col != "id":
            meena[col] = df[col].iloc[0]

    meena_df = pd.DataFrame([meena])

    # Align columns
    for col in meena_df.columns:
        if col not in df.columns:
            if isinstance(meena_df[col].iloc[0], str):
                df[col] = ""
            else:
                df[col] = np.nan

    # Sort columns to match
    df = df[meena_df.columns]

    for col in df.columns:
        if col in meena_df.columns:
            meena_df[col] = meena_df[col].astype(df[col].dtype)

    borrowers = pd.concat([meena_df, df], ignore_index=True)

    months = config["months"]
    firm_ids = borrowers["id"].values
    capacity = np.random.uniform(0.5, 1.5, size=n_firms)
    capacity[0] = 1.2  # Meena

    n_rows = n_firms * months
    panel_df = pd.DataFrame({
        "id": np.repeat(firm_ids, months),
        "month": np.tile(np.arange(1, months + 1), n_firms),
        "capacity_latent": np.repeat(capacity, months),
    })

    seasonality = np.sin(2 * np.pi * panel_df["month"] / 12) * 0.2 + 1.0
    base_revenue = 500000 * panel_df["capacity_latent"] * seasonality
    noise = np.random.normal(1.0, 0.1, size=n_rows)

    panel_df["revenue"] = base_revenue * noise
    panel_df["upi_inflow"] = panel_df["revenue"] * np.random.uniform(0.3, 0.6, size=n_rows)
    panel_df["bank_inflow"] = panel_df["revenue"] * np.random.uniform(0.4, 0.7, size=n_rows)
    panel_df["avg_bank_balance"] = panel_df["bank_inflow"] * 0.5 + np.random.normal(50000, 10000, size=n_rows)
    panel_df["gst_turnover"] = panel_df["revenue"] * np.random.uniform(0.9, 1.1, size=n_rows)
    panel_df["gstr1_3b_mismatch"] = np.random.uniform(0, 0.1, size=n_rows) / panel_df["capacity_latent"]
    panel_df["gst_filing_delay_days"] = np.random.exponential(5, size=n_rows) / panel_df["capacity_latent"]
    panel_df["receivable_days"] = np.random.normal(60, 15, size=n_rows) / panel_df["capacity_latent"]
    panel_df["utility_delay_days"] = np.random.exponential(2, size=n_rows) / panel_df["capacity_latent"]
    panel_df["cheque_bounces"] = np.random.poisson(0.5, size=n_rows)

    panel_df.drop(columns=["capacity_latent"], inplace=True)

    DATA.mkdir(exist_ok=True, parents=True)
    borrowers.to_parquet(DATA / "borrowers.parquet", index=False)
    panel_df.to_parquet(DATA / "panel.parquet", index=False)

    # oracle data
    oracle_df = pd.DataFrame({
        "id": firm_ids,
        "capacity_latent": capacity,
    })
    oracle_df.to_parquet(DATA / "oracle.parquet", index=False)

    def file_hash(path: Path) -> str:
        return hashlib.md5(path.read_bytes()).hexdigest()

    meta = {
        "seed": config["seed"],
        "config": config,
        "row_counts": {
            "borrowers": len(borrowers),
            "panel": len(panel_df),
        },
        "file_hashes": {
            "borrowers": file_hash(DATA / "borrowers.parquet"),
            "panel": file_hash(DATA / "panel.parquet"),
        },
    }
    with open(DATA / "generator_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # Write generator metrics
    total_thin = float(borrowers["bureau_score"].isna().mean())
    female_thin = float(borrowers[borrowers["owner_gender"] == "female"]["bureau_score"].isna().mean())
    male_thin = float(borrowers[borrowers["owner_gender"] == "male"]["bureau_score"].isna().mean())
    rural_thin = float(borrowers[borrowers["location_class"] == "rural"]["bureau_score"].isna().mean())
    urban_thin = float(borrowers[borrowers["location_class"] == "urban"]["bureau_score"].isna().mean())
    metro_thin = float(borrowers[borrowers["location_class"] == "metro"]["bureau_score"].isna().mean())

    write_metrics("generator", {
        "thin_file_share_total": total_thin,
        "thin_file_share_female": female_thin,
        "thin_file_share_male": male_thin,
        "thin_file_share_rural": rural_thin,
        "thin_file_share_urban": urban_thin,
        "thin_file_share_metro": metro_thin,
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--config", type=str, default="kappa=medium,bias_strength=medium")
    args = parser.parse_args()

    cfg_dict = dict(item.split("=") for item in args.config.split(",")) if args.config else {}
    k_val = cfg_dict.get("kappa", "medium")
    b_val = cfg_dict.get("bias_strength", "medium")
    build_artifacts(smoke=args.smoke, kappa=k_val, bias_strength=b_val)
