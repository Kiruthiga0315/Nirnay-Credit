import json

import pandas as pd

from core.generator import build_artifacts
from core.paths import CONFIGS, DATA


def test_generator_reproducibility_and_constraints():
    build_artifacts(smoke=True)
    with open(DATA / "generator_meta.json", encoding="utf-8") as f:
        meta1 = json.load(f)

    build_artifacts(smoke=True)
    with open(DATA / "generator_meta.json", encoding="utf-8") as f:
        meta2 = json.load(f)

    assert meta1["file_hashes"] == meta2["file_hashes"], "Runs are not reproducible"

    borrowers = pd.read_parquet(DATA / "borrowers.parquet")
    panel = pd.read_parquet(DATA / "panel.parquet")

    assert len(borrowers) == meta1["row_counts"]["borrowers"]
    assert len(panel) == meta1["row_counts"]["panel"]
    assert len(panel) == len(borrowers) * 36, f"Expected {len(borrowers) * 36} panel rows, got {len(panel)}"

    with open(CONFIGS / "personas" / "meena.json", encoding="utf-8") as f:
        meena = json.load(f)
    meena.pop("_note", None)

    meena_row = borrowers.iloc[0]
    assert meena_row["id"] == "MSME-00001"
    
    for k, v in meena.items():
        if pd.isna(v):
            assert pd.isna(meena_row[k])
        else:
            assert meena_row[k] == v

    with open(CONFIGS / "feature_spec.json", encoding="utf-8") as f:
        spec = json.load(f)

    feature_names = {feat["name"] for feat in spec["features"]}
    assert feature_names.issubset(set(borrowers.columns))

    nullable_features = {feat["name"] for feat in spec["features"] if feat.get("nullable", False)}
    for col in borrowers.columns:
        if col in ["id", "name", "business", "_note"]:
            continue
        if col not in nullable_features:
            assert not borrowers[col].isna().any(), f"Column {col} has NaN but is not nullable"

    # Bureau missingness tests
    total_thin = borrowers["bureau_score"].isna().mean()
    assert 0.30 <= total_thin <= 0.40, f"Total thin file share {total_thin:.3f} outside [0.30, 0.40]"

    female_thin = borrowers[borrowers["owner_gender"] == "female"]["bureau_score"].isna().mean()
    male_thin = borrowers[borrowers["owner_gender"] == "male"]["bureau_score"].isna().mean()
    assert female_thin > male_thin, f"Female missing {female_thin:.3f} not > Male missing {male_thin:.3f}"

    rural_thin = borrowers[borrowers["location_class"] == "rural"]["bureau_score"].isna().mean()
    metro_thin = borrowers[borrowers["location_class"] == "metro"]["bureau_score"].isna().mean()
    assert rural_thin > metro_thin, f"Rural missing {rural_thin:.3f} not > Metro missing {metro_thin:.3f}"
