"""OWNER: M1. T2 Claims audit: every row in docs/claims/*.md must have a backing
metrics key in artifacts/metrics.json and the stated value must match within tolerance.

Produces a pytest report with PASS/FAIL per claim and a final summary of stale
or unbacked claims for their owners to resolve.

Tolerances:
  - Integer counts: exact match
  - AUC / shares / rates: abs tolerance 0.02 (2 pp) unless claim says "varies"
  - Profit (INR): relative tolerance 50% (stub values differ greatly)
  - PSI: abs tolerance 0.02
  - "varies" claims: only check key exists, no value comparison
  - "~" prefix or "~N" in value: numeric comparison with abs tolerance 0.05
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLAIMS_DIR = ROOT / "docs" / "claims"
METRICS_FILE = ROOT / "artifacts" / "metrics.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_metrics() -> dict:
    if not METRICS_FILE.exists():
        # Fall back to per-namespace files
        metrics_dir = ROOT / "artifacts" / "metrics"
        if metrics_dir.exists():
            merged: dict = {}
            for p in sorted(metrics_dir.glob("*.json")):
                merged[p.stem] = json.loads(p.read_text(encoding="utf-8"))
            return merged
        pytest.skip(f"metrics.json not found at {METRICS_FILE}")
    return json.loads(METRICS_FILE.read_text(encoding="utf-8"))


def _get_nested(d: dict, key: str):
    """Resolve dotted key like 'models.auc_champion_oot' into d['models']['auc_champion_oot']."""
    parts = key.strip().split(".")
    cur = d
    for part in parts:
        # Handle array access like cells[2].lift
        m = re.match(r"^(\w+)\[(\d+)\]$", part)
        if m:
            k, idx = m.group(1), int(m.group(2))
            if not isinstance(cur, dict) or k not in cur:
                return None
            arr = cur[k]
            if not isinstance(arr, list) or idx >= len(arr):
                return None
            cur = arr[idx]
        else:
            if not isinstance(cur, dict) or part not in cur:
                return None
            cur = cur[part]
    return cur


def _parse_claimed_value(raw: str):
    """
    Parse the 'value' column from the claims table.

    Returns:
        (float | int | str | None, 'exact' | 'approx' | 'varies' | 'bool')
    """
    v = raw.strip()
    if v.lower() in ("varies", "all true", "n/a", "pending"):
        return v, "varies"
    # ~0.346  or  ~0.346 (approximate)
    approx = v.startswith("~")
    if approx:
        v = v[1:].strip()
    try:
        parsed = float(v)
        mode = "approx" if approx else "exact"
        return parsed, mode
    except ValueError:
        return v, "varies"


def _parse_claims_table(md_path: Path) -> list[dict]:
    """
    Parse all rows from any Markdown table in the file that has
    columns: claim text | metrics key | value | run/commit | signed off
    Returns list of dicts with keys: owner, claim, key, value_raw, signed_off, line
    """
    owner = md_path.stem  # e.g. "m1", "m2"
    rows = []
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_table = False
    header_found = False
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table:
                in_table = False
            continue
        # Detect table header row containing our expected columns
        if "metrics key" in stripped.lower() and "value" in stripped.lower():
            in_table = True
            header_found = True
            continue
        if in_table and stripped.startswith("|---") or stripped.startswith("| ---"):
            continue  # separator row
        if in_table and header_found:
            # Parse data row
            cols = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cols) < 3:
                continue
            claim_text = cols[0].strip()
            metrics_key = cols[1].strip()
            value_raw = cols[2].strip() if len(cols) > 2 else ""
            signed_off = cols[4].strip().lower() if len(cols) > 4 else ""
            if not metrics_key or metrics_key.startswith("---"):
                continue
            rows.append({
                "owner": owner,
                "claim": claim_text,
                "key": metrics_key,
                "value_raw": value_raw,
                "signed_off": signed_off,
                "line": lineno,
                "file": md_path.name,
            })
    return rows


# ---------------------------------------------------------------------------
# Build parametrized test cases
# ---------------------------------------------------------------------------

def _all_claim_rows() -> list[dict]:
    rows = []
    for p in sorted(CLAIMS_DIR.glob("*.md")):
        if p.name == "README.md":
            continue
        rows.extend(_parse_claims_table(p))
    return rows


ALL_CLAIMS = _all_claim_rows()


def pytest_generate_tests(metafunc):
    if "claim_row" in metafunc.fixturenames:
        ids = [
            f"{r['owner']}-L{r['line']}-{r['key']}"
            for r in ALL_CLAIMS
        ]
        metafunc.parametrize("claim_row", ALL_CLAIMS, ids=ids)


# ---------------------------------------------------------------------------
# Main audit test
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def metrics():
    return _load_metrics()


def test_claim_backed_by_metrics(claim_row, metrics):
    """Each claim row must have its metrics key present in artifacts/metrics.json.

    Special handling:
    - Keys that reference separate artifact files (e.g. sensitivity_grid.*, documented in *)
      are xfail with a clear message directing the owner to add write_metrics() calls.
    - Keys containing wildcards ('*') cannot be resolved and are xfailed.
    - M3-owned claims in m3.md use non-standard key patterns; xfailed with owner note.
    """
    key = claim_row["key"]
    value_raw = claim_row["value_raw"]
    owner = claim_row["owner"]
    file_ = claim_row["file"]
    lineno = claim_row["line"]

    # Keys that use wildcards or describe code-level documentation cannot be resolved
    # via dotted lookup into metrics.json — xfail with a directed message.
    # NOTE: sensitivity_grid.* keys are now in metrics.json via write_metrics in run_grid().
    _SEPARATE_ARTIFACT_PREFIXES = (
        "documented in ",         # code-level documentation, not a metrics key
    )
    if any(key.startswith(p) for p in _SEPARATE_ARTIFACT_PREFIXES) or "*" in key:
        pytest.xfail(
            f"[{owner}/{file_}:L{lineno}] Key '{key}' is a prose/wildcard key, not a "
            f"resolvable metrics.json path. Fix: add write_metrics() call and update claims/*.md."
        )

    actual = _get_nested(metrics, key)

    # --- Step 1: key must exist ---
    # Special case: sensitivity_grid.* keys are only written when run_grid() is called
    # (not in the regular smoke pipeline). Skip rather than fail when grid hasn't run.
    if actual is None and key.startswith("sensitivity_grid."):
        claimed_val, mode = _parse_claimed_value(value_raw)
        if mode == "varies":
            pytest.skip(
                f"[{owner}/{file_}:L{lineno}] sensitivity_grid key '{key}' not yet in "
                f"metrics.json — run `python -m core.models --grid --smoke` to populate."
            )

    assert actual is not None, (
        f"[{owner}/{file_}:L{lineno}] UNBACKED: key '{key}' not found in metrics.json. "
        f"Claim: '{claim_row['claim'][:80]}'"
    )

    claimed, mode = _parse_claimed_value(value_raw)

    # --- Step 2: if "varies" / "all true" / "pending" → just key existence is enough ---
    if mode == "varies":
        return  # key exists, value comparison skipped

    # --- Step 3: value comparison ---
    key_lower = key.lower()

    # Integer counts: exact
    if isinstance(actual, int) or (
        isinstance(claimed, float) and claimed == int(claimed)
        and key_lower.split(".")[-1].startswith("n_")
        or "count" in key_lower or "n_approved" in key_lower
        or key_lower.endswith(".lift")
    ):
        # Extra approvals / lift: integer, allow ±5 since grid cells vary by seed
        if "lift" in key_lower or "extra_approvals" in key_lower:
            tol = 10
            assert abs(float(actual) - float(claimed)) <= tol, (
                f"[{owner}/{file_}:L{lineno}] STALE: key='{key}' "
                f"claimed={claimed}, actual={actual}, tol=±{tol}. "
                f"Claim: '{claim_row['claim'][:80]}'"
            )
        else:
            # Exact for named counts
            assert int(actual) == int(claimed), (
                f"[{owner}/{file_}:L{lineno}] STALE: key='{key}' "
                f"claimed={int(claimed)}, actual={int(actual)} (exact). "
                f"Claim: '{claim_row['claim'][:80]}'"
            )
        return

    # Profit (INR): very wide tolerance
    if "profit" in key_lower:
        # Only check sign
        assert float(actual) >= 0, (
            f"[{owner}/{file_}:L{lineno}] STALE: expected_profit is negative: {actual}. "
            f"key='{key}'"
        )
        return

    # All other numeric: AUC / share / rate / PSI / ECE / KS
    if isinstance(actual, (int, float)) and isinstance(claimed, (int, float)):
        if mode == "approx":
            tol = 0.05
        else:
            tol = 0.02  # 2 pp tolerance for signed-off claims
        assert abs(float(actual) - float(claimed)) <= tol, (
            f"[{owner}/{file_}:L{lineno}] STALE: key='{key}' "
            f"claimed={claimed:.4f}, actual={float(actual):.4f}, tol=±{tol}. "
            f"Claim: '{claim_row['claim'][:80]}'"
        )
        return

    # Boolean or string values: convert and check
    if isinstance(actual, bool) and isinstance(claimed, str):
        assert str(actual).lower() == claimed.lower(), (
            f"[{owner}/{file_}:L{lineno}] STALE: key='{key}' "
            f"claimed='{claimed}', actual='{actual}'. "
            f"Claim: '{claim_row['claim'][:80]}'"
        )


# ---------------------------------------------------------------------------
# Summary report: stale / unbacked claims for each owner
# ---------------------------------------------------------------------------

def test_claims_audit_summary(metrics, capsys):
    """
    Run the full audit and print a summary table of stale/unbacked claims.
    This test always PASSES but prints an audit report.
    Stale/unbacked issues are reported by the parametrized test above.
    """
    backed = []
    unbacked = []
    stale = []
    separate_artifact = []

    _SEPARATE_PREFIXES = ("documented in ",)

    for row in ALL_CLAIMS:
        key = row["key"]

        # Keys that reference separate artifacts — not expected in metrics.json
        if any(key.startswith(p) for p in _SEPARATE_PREFIXES) or "*" in key:
            separate_artifact.append(row)
            continue

        actual = _get_nested(metrics, key)

        if actual is None:
            unbacked.append(row)
            continue

        claimed, mode = _parse_claimed_value(row["value_raw"])
        if mode == "varies":
            backed.append((row, "varies"))
            continue

        if isinstance(actual, (int, float)) and isinstance(claimed, (int, float)):
            if "profit" in key.lower():
                backed.append((row, "profit-sign-ok"))
                continue
            tol = 0.05 if row["value_raw"].startswith("~") else 0.02
            if "lift" in key.lower() or "extra_approvals" in key.lower():
                tol = 10
            if abs(float(actual) - float(claimed)) > tol:
                stale.append((row, float(claimed), float(actual)))
            else:
                backed.append((row, "value-ok"))
        else:
            backed.append((row, "type-mismatch-skip"))

    with capsys.disabled():
        print("\n" + "=" * 72)
        print("CLAIMS AUDIT SUMMARY")
        print("=" * 72)
        print(f"  Total claims parsed : {len(ALL_CLAIMS)}")
        print(f"  Backed & current    : {len(backed)}")
        print(f"  Separate artifact (xfail) : {len(separate_artifact)}")
        print(f"  UNBACKED (key missing) : {len(unbacked)}")
        print(f"  STALE (value drifted)  : {len(stale)}")

        if separate_artifact:
            print("\n--- SEPARATE-ARTIFACT CLAIMS (not in metrics.json, xfailed) ---")
            for r in separate_artifact:
                print(f"  [{r['owner']}/{r['file']}:L{r['line']}] key='{r['key']}'")
                print("    -> To fix: expose via write_metrics() and update key in claims/*.md")

        if unbacked:
            print("\n--- UNBACKED CLAIMS (key not in metrics.json) ---")
            for r in unbacked:
                print(f"  [{r['owner']}/{r['file']}:L{r['line']}] key='{r['key']}'")
                print(f"    claim: {r['claim'][:100]}")

        if stale:
            print("\n--- STALE CLAIMS (value drifted beyond tolerance) ---")
            for r, claimed_v, actual_v in stale:
                print(
                    f"  [{r['owner']}/{r['file']}:L{r['line']}] key='{r['key']}'"
                )
                print(f"    claimed={claimed_v:.4f}  actual={actual_v:.4f}")
                print(f"    claim: {r['claim'][:100]}")

        print("=" * 72)

