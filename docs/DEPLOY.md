# Deploy Guide (Owner: M3)

## Quick Start (3 commands from a fresh clone)

```bash
pip install -r requirements-dev.txt   # install dependencies
python run_all.py                      # build all artifacts (< 10 min)
streamlit run app/Home.py             # open http://localhost:8501
```

For a faster check: `python run_all.py --smoke` (< 2 min) then `streamlit run app/Home.py`.

---

## Offline Demo (No Internet Required)

Use this when demoing from a **laptop**, **air-gapped machine**, or a **phone hotspot**.
The app reads from `demo_snapshot/` and never calls any external API.

### Linux / macOS

```bash
# 1. Give execute permission (one-time):
chmod +x scripts/offline_demo.sh

# 2. Run (creates .venv_offline, installs from requirements.lock, launches app):
./scripts/offline_demo.sh

# 3. Open in browser:  http://localhost:8501
```

Optional environment variables:
| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `8501` | Streamlit port |
| `VENV_DIR` | `.venv_offline` | Virtual env location |
| `DRY_RUN` | `0` | Set `1` to print commands without running |

### Windows

```bat
scripts\offline_demo.bat
```

Same environment variables apply (set them with `set VAR=VALUE` before running).

### Phone Hotspot / Fully Air-Gapped

Pre-download all wheels **before** disconnecting:

```bash
pip download -r requirements.lock -d ./wheel_cache/
```

Then run offline:

```bash
# macOS / Linux:
PIP_FIND_LINKS=./wheel_cache PIP_NO_INDEX=1 ./scripts/offline_demo.sh

# Windows:
set PIP_FIND_LINKS=wheel_cache
set PIP_NO_INDEX=1
scripts\offline_demo.bat
```

> **Phone hotspot tip:** Connect the laptop to the hotspot, pre-download the wheel cache
> at full speed, then tether turns off for the demo. The app never makes outbound calls.

---

## Creating / Refreshing the Demo Snapshot

`demo_snapshot/` contains pre-built artifacts committed to git by M3 only.
Refresh it after any significant model or data change:

```bash
make snapshot
# equivalent to:
python run_all.py && \
  rm -rf demo_snapshot/artifacts && \
  mkdir -p demo_snapshot && \
  cp -r artifacts demo_snapshot/artifacts
```

Then commit the result (M3 only):

```bash
git add demo_snapshot/
git commit -m "m3(snapshot): refresh demo artifacts $(date +%Y-%m-%d)"
```

> **Rule (AGENTS.md §5):** Never commit `data/`, `models/`, or `artifacts/` to feature
> branches. Only M3 commits `demo_snapshot/`.

---

## Lock Requirements

Before deploying, lock the exact package versions:

```bash
pip freeze > requirements.lock
git add requirements.lock && git commit -m "m3(lock): pin requirements $(date +%Y-%m-%d)"
```

---

## Streamlit Community Cloud (Recommended)

1. **[MANUAL]** Push your repository to GitHub and ensure `main` branch is protected.
2. **[MANUAL]** Go to [share.streamlit.io](https://share.streamlit.io) and click "New app".
3. Point to your repository, branch `main`, and main file path `app/Home.py`.
4. Select Python version 3.11.
5. In advanced settings, add any necessary secrets.
6. Click Deploy. Streamlit will install from `requirements.lock` (if present) else `requirements.txt`.

---

## Hugging Face Spaces (Alternative)

1. **[MANUAL]** Go to [huggingface.co/spaces](https://huggingface.co/spaces) and click "Create new Space".
2. Name the space, select "Streamlit" as the SDK.
3. Choose the Space hardware.
4. **[MANUAL]** Link your GitHub repository or push code directly to the HF Space remote.
5. Ensure `app/Home.py` is the startup file (configure in Space settings).
6. Set any secrets in the Space settings.

---

## Health Check (Every 3 Hours)

The `scripts/health_check.py` script verifies main is green:

```bash
# One-off check (no pull):
python scripts/health_check.py --no-pull

# Scheduled (cron, every 3 hours):
0 */3 * * * /path/to/.venv/bin/python /path/to/scripts/health_check.py >> /tmp/health.log 2>&1
```

Output format: `[2026-09-30T18:05Z] GREEN  pull=OK smoke=OK tests=OK branch=main sha=cf466d3`

Or via Makefile: `make health`

---

## CI Gates

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every PR and push to main:

| Step | What it checks |
|---|---|
| `ruff check .` | Zero lint errors |
| `python run_all.py --smoke --keep-going` | All pipeline stages run without FAIL |
| `pytest tests/test_claims.py` | Every claimed key in `docs/claims/*.md` exists in `metrics.json` |
| `pytest` (remaining tests) | All unit/integration tests pass |
