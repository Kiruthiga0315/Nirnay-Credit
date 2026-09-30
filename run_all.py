"""OWNER: M3. One command rebuilds data -> models -> artifacts.

  python run_all.py                 # full build
  python run_all.py --smoke         # tiny build (CI, quick checks)
  python run_all.py --stage models  # one stage
  python run_all.py --keep-going    # do not stop on the first failing stage
  python run_all.py --list

Each stage calls core.<module>.build_artifacts(smoke). Stage order = dependency order.
Adding a stage = one line in STAGES (M3 only).
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
import time

from core.paths import ARTIFACTS, load_metrics

STAGES = [  # (name, module, owner)
    ("generator", "core.generator", "M1"),
    ("legacy_policy", "core.legacy_policy", "M1"),
    ("models", "core.models", "M1"),
    ("explain", "core.explain", "M2"),
    ("forecast", "core.forecast", "M2"),
    ("recourse", "core.recourse", "M2"),
    ("structuring", "core.structuring", "M2"),
    ("fairness", "core.fairness", "M2"),
    ("optimizer", "core.optimizer", "M2"),
    ("stress", "core.stress", "M3"),
    ("early_warning", "core.early_warning", "M3"),
    ("trust", "core.trust", "M3"),
    ("external", "core.external", "M1"),
    ("governance", "core.governance", "M3"),
    ("documents", "core.documents", "M4"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--stage")
    ap.add_argument("--keep-going", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--grid", action="store_true", help="Print the 9 grid configs from configs/generator/grid.yaml")
    a = ap.parse_args()
    if a.list:
        for n, m, o in STAGES:
            print(f"{n:15s} {m:22s} {o}")
        return 0
    if a.grid:
        import yaml

        from core.paths import CONFIGS
        grid_path = CONFIGS / "generator" / "grid.yaml"
        if not grid_path.exists():
            print(f"Error: {grid_path} does not exist.")
            return 1
        with open(grid_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        axes = data.get("axes", {})
        kappa_opts = axes.get("kappa", {})
        bias_opts = axes.get("bias_strength", {})
        grid_configs = []
        for k_name, k_val in kappa_opts.items():
            for b_name, b_val in bias_opts.items():
                grid_configs.append({
                    "kappa_label": k_name,
                    "kappa": k_val,
                    "bias_strength_label": b_name,
                    "bias_strength": b_val,
                })
        print(f"Grid configurations ({len(grid_configs)} runs) from {grid_path.name}:")
        for idx, cfg in enumerate(grid_configs, 1):
            print(f"  [{idx}/9] kappa={cfg['kappa_label']} ({cfg['kappa']}), bias_strength={cfg['bias_strength_label']} ({cfg['bias_strength']})")
        return 0
    failures = []
    for name, mod, owner in STAGES:
        if a.stage and a.stage != name:
            continue
        t0 = time.time()
        try:
            importlib.import_module(mod).build_artifacts(smoke=a.smoke)
            print(f"OK   {name:14s} ({owner}) {time.time() - t0:5.1f}s")
        except Exception as e:  # noqa: BLE001
            failures.append((name, owner, repr(e)))
            print(f"FAIL {name:14s} ({owner}) {e!r}")
            if not a.keep_going:
                break
    merged = load_metrics()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "metrics.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print(f"metrics.json namespaces: {sorted(merged)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
