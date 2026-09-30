"""OWNER: M1. F1 synthetic MSME generator (Blueprint 5.2). STUB until Phase 0/1.

Writes: data/borrowers.parquet, data/panel.parquet, data/oracle.parquet (true outcomes; NEVER
loaded by any model), data/generator_meta.json. Must inject configs/personas/meena.json as
MSME-00001. CLI: python -m core.generator --smoke [--config kappa=medium,bias_strength=medium]
"""
from __future__ import annotations


def build_artifacts(smoke: bool = False) -> None:
    print("[generator] STUB - M1 to implement")


if __name__ == "__main__":
    build_artifacts(smoke=True)
