"""Filesystem contract. FROZEN. The UI reads ONLY through these helpers.

Lookup order for artifacts: artifacts/ (fresh local build) -> demo_snapshot/artifacts/ (committed
by M3 for deploy). Heavy files are never committed to feature branches.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MODELS = ROOT / "models"
ARTIFACTS = ROOT / "artifacts"
SNAPSHOT = ROOT / "demo_snapshot"
CONFIGS = ROOT / "configs"


def artifact_path(name: str) -> Path:
    """Path of an artifact, preferring a fresh local build over the committed snapshot."""
    fresh = ARTIFACTS / name
    if fresh.exists():
        return fresh
    snap = SNAPSHOT / "artifacts" / name
    return snap if snap.exists() else fresh


def load_json(name: str, default: Any = None) -> Any:
    p = artifact_path(name)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(name: str, obj: Any) -> Path:
    """Atomic write into artifacts/. `name` may include a sub-folder, e.g. 'metrics/models.json'."""
    p = ARTIFACTS / name
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, p)
    return p


def write_metrics(namespace: str, metrics: dict[str, Any]) -> Path:
    """Each module writes ONLY its own namespace: artifacts/metrics/<namespace>.json.
    run_all.py merges all namespaces into artifacts/metrics.json (no shared-file conflicts)."""
    return write_json(f"metrics/{namespace}.json", metrics)


def load_metrics() -> dict[str, Any]:
    merged = load_json("metrics.json")
    if merged is not None:
        return merged
    out: dict[str, Any] = {}
    for base in (SNAPSHOT / "artifacts" / "metrics", ARTIFACTS / "metrics"):
        if base.exists():
            for p in sorted(base.glob("*.json")):
                out[p.stem] = json.loads(p.read_text(encoding="utf-8"))
    return out
