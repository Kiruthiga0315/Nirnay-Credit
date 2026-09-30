"""OWNER: M3. T4 Claims audit: every metrics key in docs/claims/*.md must exist in
artifacts/metrics.json after a smoke build.

Intent: reusable logic that M1's audit task (m1/p4-audit-docs) can import or
extend. We parse the claims table from Markdown and cross-check against the
merged metrics.json written by run_all.py.

Key format in claims tables: `<namespace>.<field>` — the first column after
the `|` claim text column is the metrics key column.
"""
from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLAIMS_DIR = ROOT / "docs" / "claims"

# Pattern matching a non-header, non-separator Markdown table row
_ROW_RE = re.compile(r"^\|(.+)\|$")
# Skip rows that are the header or separator (---|---|...)
_SEP_RE = re.compile(r"^[\|\-\s]+$")

# Keys that contain wildcards or placeholders — skip existence check
_SKIP_PATTERNS = re.compile(
    r"varies|N/A|n/a|\*|\{|\}|see artifacts|TODO|documented|config",
    re.IGNORECASE,
)


def _parse_claims(md_path: pathlib.Path) -> list[tuple[str, str]]:
    """Return (claim_text, metrics_key) pairs from a claims markdown table."""
    rows = []
    lines = md_path.read_text(encoding="utf-8").splitlines()
    header_seen = False
    for line in lines:
        line = line.strip()
        if not _ROW_RE.match(line):
            continue
        if _SEP_RE.match(line.replace("|", "").replace(" ", "")):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        # Detect the header row (first cell is "claim text")
        if cells[0].lower() in ("claim text", "claim"):
            header_seen = True
            continue
        if not header_seen:
            continue
        claim_text = cells[0]
        metrics_key = cells[1]
        rows.append((claim_text, metrics_key))
    return rows


def _load_metrics() -> dict:
    """Load the merged metrics.json; return empty dict if not built yet."""
    from core.paths import load_metrics  # noqa: PLC0415

    return load_metrics() or {}


def _flatten_metrics(metrics: dict, prefix: str = "") -> set[str]:
    """Return the set of all dotted keys in a nested dict."""
    keys: set[str] = set()
    for k, v in metrics.items():
        full = f"{prefix}.{k}" if prefix else k
        keys.add(full)
        if isinstance(v, dict):
            keys.update(_flatten_metrics(v, full))
    return keys


# ---------------------------------------------------------------------------
# Collect all (file, claim_text, key) triples once at module level
# ---------------------------------------------------------------------------

def _all_claims() -> list[tuple[str, str, str]]:
    triples = []
    for md in sorted(CLAIMS_DIR.glob("*.md")):
        if md.name == "README.md":
            continue
        for claim, key in _parse_claims(md):
            triples.append((md.name, claim, key))
    return triples


ALL_CLAIMS = _all_claims()


# Only keys that look like namespace.field (word chars + dots, no spaces/backticks/brackets)
_VALID_KEY_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_.]*$')


def _checkable(key: str) -> bool:
    """Return True if this key should be checked for existence in metrics.json."""
    if not key:
        return False
    # Must look like namespace.field (alphanumeric + underscore + dots only)
    if not _VALID_KEY_RE.match(key):
        return False
    # Must have at least one dot
    if '.' not in key:
        return False
    # Skip placeholder / documentation values
    if _SKIP_PATTERNS.search(key):
        return False
    return True


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_claims_files_exist() -> None:
    """There must be at least one claims file per member."""
    members = {"m1.md", "m2.md", "m3.md"}
    found = {p.name for p in CLAIMS_DIR.glob("*.md")}
    missing = members - found
    assert not missing, f"Missing claims files: {missing}"


def test_claims_table_parseable() -> None:
    """Every claims file must have at least one parseable row."""
    for md in sorted(CLAIMS_DIR.glob("*.md")):
        if md.name == "README.md":
            continue
        rows = _parse_claims(md)
        assert rows, f"{md.name}: no parseable table rows found"


@pytest.mark.parametrize(
    "claims_file,claim_text,metrics_key",
    [
        (f, c, k)
        for (f, c, k) in ALL_CLAIMS
        if _checkable(k)
    ],
    ids=[
        f"{f}:{k}"
        for (f, c, k) in ALL_CLAIMS
        if _checkable(k)
    ],
)
def test_claimed_key_exists_in_metrics(
    claims_file: str, claim_text: str, metrics_key: str
) -> None:
    """Each claimed metrics key must exist in the merged metrics.json.

    Keys from known stubs (external.*, sensitivity_grid.*, scipy.*) are
    marked xfail: they depend on M1/M2 implementations not yet present in
    the smoke build. Track in docs/known_issues/m3.md.
    """
    # Keys from other members' stubs — mark as xfail, not hard fail
    _STUB_KEY_PREFIXES = (
        "external.",          # M1 external validity — stub outputs only in smoke
        "sensitivity_grid.",  # M1 grid run (--grid flag, not --smoke)
        "scipy.",             # M2 library reference, not a metrics key
    )
    is_stub = any(metrics_key.startswith(p) for p in _STUB_KEY_PREFIXES)

    metrics = _load_metrics()
    if not metrics:
        pytest.skip("metrics.json not built yet — run `python run_all.py --smoke` first")

    flat_keys = _flatten_metrics(metrics)

    if metrics_key not in flat_keys and is_stub:
        pytest.xfail(
            f"[{claims_file}] '{metrics_key}' depends on a stub/grid run not "
            f"present in --smoke. Known limit: docs/known_issues/m3.md."
        )

    assert metrics_key in flat_keys, (
        f"[{claims_file}] Key '{metrics_key}' not found in metrics.json.\n"
        f"  Claim: {claim_text!r}\n"
        f"  Available namespaces: {sorted(metrics)}"
    )
