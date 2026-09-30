#!/usr/bin/env python3
"""OWNER: M3. scripts/health_check.py
10-minute "is main still green?" check.

Run manually:    python scripts/health_check.py
Schedule (cron): */3 * * * * python /path/to/scripts/health_check.py >> health.log 2>&1

The script:
  1. Pulls origin/main (if --pull is set, default: True for scheduled, skip if --no-pull).
  2. Runs `python run_all.py --smoke --keep-going` (< 2 min by contract).
  3. Prints a single-line status line and exits 0 on green, 1 on red.

One-line output format:
  [2026-09-30T18:05:40Z] GREEN  smoke=OK tests=OK branch=main sha=cf466d3
  [2026-09-30T18:05:40Z] RED    smoke=FAIL(governance) tests=OK branch=main sha=cf466d3
"""
from __future__ import annotations

import argparse
import datetime
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], *, cwd: Path = ROOT, timeout: int = 600) -> tuple[int, str]:
    """Run a subprocess; return (returncode, combined_output)."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.returncode, result.stdout + result.stderr


def git_sha() -> str:
    rc, out = run(["git", "rev-parse", "--short", "HEAD"])
    return out.strip() if rc == 0 else "unknown"


def git_branch() -> str:
    rc, out = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return out.strip() if rc == 0 else "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description="One-line health check for Nirnay-Credit main.")
    ap.add_argument("--pull", action="store_true", default=True, help="git pull before check (default)")
    ap.add_argument("--no-pull", dest="pull", action="store_false", help="skip git pull")
    ap.add_argument("--skip-tests", action="store_true", help="skip pytest (smoke only)")
    args = ap.parse_args()

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── 1. Pull ──────────────────────────────────────────────────────
    pull_status = "skipped"
    if args.pull:
        rc, _ = run(["git", "pull", "--ff-only", "origin", "main"])
        pull_status = "OK" if rc == 0 else "FAIL"

    branch = git_branch()
    sha = git_sha()

    # ── 2. Smoke run ────────────────────────────────────────────────
    python = sys.executable
    smoke_rc, smoke_out = run(
        [python, "run_all.py", "--smoke", "--keep-going"],
        timeout=180,
    )
    smoke_status = "OK" if smoke_rc == 0 else "FAIL"
    # Extract failing stage names from output for concise status
    fail_stages = [
        line.split()[1] for line in smoke_out.splitlines() if line.startswith("FAIL ")
    ]
    if fail_stages:
        smoke_status = f"FAIL({','.join(fail_stages)})"

    # ── 3. Tests ────────────────────────────────────────────────────
    test_status = "skipped"
    if not args.skip_tests:
        test_rc, test_out = run(
            [python, "-m", "pytest", "--tb=no", "-q", "--timeout=120"],
            timeout=600,
        )
        test_status = "OK" if test_rc == 0 else "FAIL"

    # ── 4. Print one-liner & exit ────────────────────────────────────
    overall = "GREEN" if (smoke_status == "OK" and test_status in {"OK", "skipped"}) else "RED"
    line = (
        f"[{now}] {overall:5s}  "
        f"pull={pull_status} smoke={smoke_status} tests={test_status} "
        f"branch={branch} sha={sha}"
    )
    print(line)
    sys.stdout.flush()

    return 0 if overall == "GREEN" else 1


if __name__ == "__main__":
    sys.exit(main())
