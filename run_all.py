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

import os
os.environ["OMP_NUM_THREADS"] = "1"

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
        from core.models import run_grid
        run_grid(smoke=a.smoke)
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
    # Remove stale merged file so load_metrics() reads from metrics/*.json
    stale = ARTIFACTS / "metrics.json"
    if stale.exists():
        stale.unlink()
    merged = load_metrics()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "metrics.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print(f"metrics.json namespaces: {sorted(merged)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
