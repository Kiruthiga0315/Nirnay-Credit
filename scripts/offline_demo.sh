#!/usr/bin/env bash
# scripts/offline_demo.sh — OWNER: M3
# =====================================================================
# Offline Demo Build Script
# =====================================================================
# Creates a virtual environment, installs from requirements.lock (or
# requirements.txt if the lock file is absent), and launches the app
# from demo_snapshot/ — no internet connection required.
#
# Usage (laptop):
#   chmod +x scripts/offline_demo.sh
#   ./scripts/offline_demo.sh
#
# Usage (phone hotspot / air-gapped):
#   Same command; requirements.lock pins exact versions so pip resolves
#   entirely from the local wheel cache if you ran --download beforehand.
#   To pre-download wheels: pip download -r requirements.lock -d ./wheel_cache/
#   Then: PIP_FIND_LINKS=./wheel_cache PIP_NO_INDEX=1 ./scripts/offline_demo.sh
#
# Environment variables:
#   PORT      Streamlit port  (default: 8501)
#   VENV_DIR  Virtual env dir (default: .venv_offline)
#   DRY_RUN   Set to 1 to print commands without executing them.
# =====================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-8501}"
VENV_DIR="${VENV_DIR:-${REPO_ROOT}/.venv_offline}"
DRY_RUN="${DRY_RUN:-0}"

run() {
  if [[ "${DRY_RUN}" == "1" ]]; then
    echo "[DRY-RUN] $*"
  else
    "$@"
  fi
}

echo "==== Nirnay-Credit Offline Demo ===="
echo "Repo root : ${REPO_ROOT}"
echo "Venv      : ${VENV_DIR}"
echo "Port      : ${PORT}"
echo "Dry-run   : ${DRY_RUN}"
echo ""

# ── 1. Python version guard ──────────────────────────────────────────
PYTHON=$(command -v python3.11 || command -v python3 || command -v python)
PY_VER=$("${PYTHON}" -c "import sys; print('%d.%d' % sys.version_info[:2])")
echo "[1] Python: ${PYTHON} (${PY_VER})"
if [[ "${PY_VER}" < "3.10" ]]; then
  echo "ERROR: Python 3.10+ required." >&2
  exit 1
fi

# ── 2. Create virtual environment ───────────────────────────────────
echo "[2] Creating venv at ${VENV_DIR} ..."
run "${PYTHON}" -m venv "${VENV_DIR}"
ACTIVATE="${VENV_DIR}/bin/activate"

# ── 3. Install dependencies ──────────────────────────────────────────
LOCKFILE="${REPO_ROOT}/requirements.lock"
REQFILE="${REPO_ROOT}/requirements-dev.txt"
if [[ -f "${LOCKFILE}" ]]; then
  echo "[3] Installing from requirements.lock (pinned) ..."
  run "${VENV_DIR}/bin/pip" install --quiet --upgrade pip
  run "${VENV_DIR}/bin/pip" install --quiet -r "${LOCKFILE}"
else
  echo "[3] requirements.lock not found — falling back to requirements-dev.txt ..."
  run "${VENV_DIR}/bin/pip" install --quiet --upgrade pip
  run "${VENV_DIR}/bin/pip" install --quiet -r "${REQFILE}"
fi

# ── 4. Snapshot check ───────────────────────────────────────────────
SNAP_ARTIFACTS="${REPO_ROOT}/demo_snapshot/artifacts"
echo "[4] Checking demo_snapshot/artifacts ..."
if [[ ! -d "${SNAP_ARTIFACTS}" ]]; then
  if [[ "${DRY_RUN}" == "1" ]]; then
    echo "    [DRY-RUN] demo_snapshot/artifacts not found (would be created via 'make snapshot')."
  else
    echo "ERROR: ${SNAP_ARTIFACTS} not found." >&2
    echo "       Run 'make snapshot' first (requires internet + full build)." >&2
    exit 1
  fi
else
  echo "    Found $(find "${SNAP_ARTIFACTS}" -type f | wc -l | tr -d ' ') artifact file(s)."
fi

# ── 5. Launch Streamlit from snapshot ───────────────────────────────
echo "[5] Launching app (reads from demo_snapshot/) ..."
echo "    Open http://localhost:${PORT} in your browser."
echo ""
run "${VENV_DIR}/bin/streamlit" run \
  "${REPO_ROOT}/app/Home.py" \
  --server.port "${PORT}" \
  --server.headless true \
  --browser.gatherUsageStats false
