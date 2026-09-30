@echo off
:: scripts\offline_demo.bat — OWNER: M3
:: =====================================================================
:: Offline Demo Build Script (Windows)
:: =====================================================================
:: Creates a virtual environment, installs from requirements.lock
:: (or requirements.txt if lock absent), and launches the app from
:: demo_snapshot/ — no internet connection required.
::
:: Usage (laptop):
::   scripts\offline_demo.bat
::
:: Usage (phone hotspot / air-gapped):
::   Pre-download wheels:
::     pip download -r requirements.lock -d wheel_cache\
::   Then set these env vars before running:
::     set PIP_FIND_LINKS=wheel_cache
::     set PIP_NO_INDEX=1
::     scripts\offline_demo.bat
::
:: Environment variables (set before calling):
::   PORT      Streamlit port  (default: 8501)
::   VENV_DIR  Virtual env dir (default: .venv_offline)
::   DRY_RUN   Set to 1 to print commands without executing them.
:: =====================================================================
setlocal EnableDelayedExpansion

set "REPO_ROOT=%~dp0.."
if not defined PORT set PORT=8501
if not defined VENV_DIR set "VENV_DIR=%REPO_ROOT%\.venv_offline"
if not defined DRY_RUN set DRY_RUN=0

echo ==== Nirnay-Credit Offline Demo (Windows) ====
echo Repo root : %REPO_ROOT%
echo Venv      : %VENV_DIR%
echo Port      : %PORT%
echo Dry-run   : %DRY_RUN%
echo.

:: ── 1. Python version guard ──────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: python not found on PATH. Install Python 3.10+. >&2
    exit /b 1
)
echo [1] Python found.

:: ── 2. Create virtual environment ───────────────────────────────────
echo [2] Creating venv at %VENV_DIR% ...
if "%DRY_RUN%"=="1" (
    echo [DRY-RUN] python -m venv "%VENV_DIR%"
) else (
    python -m venv "%VENV_DIR%"
)

:: ── 3. Install dependencies ──────────────────────────────────────────
set "LOCKFILE=%REPO_ROOT%\requirements.lock"
set "REQFILE=%REPO_ROOT%\requirements-dev.txt"
if exist "%LOCKFILE%" (
    echo [3] Installing from requirements.lock ^(pinned^) ...
    if "%DRY_RUN%"=="1" (
        echo [DRY-RUN] "%VENV_DIR%\Scripts\pip" install -r "%LOCKFILE%"
    ) else (
        "%VENV_DIR%\Scripts\pip" install --quiet --upgrade pip
        "%VENV_DIR%\Scripts\pip" install --quiet -r "%LOCKFILE%"
    )
) else (
    echo [3] requirements.lock not found -- falling back to requirements-dev.txt ...
    if "%DRY_RUN%"=="1" (
        echo [DRY-RUN] "%VENV_DIR%\Scripts\pip" install -r "%REQFILE%"
    ) else (
        "%VENV_DIR%\Scripts\pip" install --quiet --upgrade pip
        "%VENV_DIR%\Scripts\pip" install --quiet -r "%REQFILE%"
    )
)

:: ── 4. Snapshot check ───────────────────────────────────────────────
set "SNAP_ARTIFACTS=%REPO_ROOT%\demo_snapshot\artifacts"
echo [4] Checking demo_snapshot\artifacts ...
if not exist "%SNAP_ARTIFACTS%" (
    echo ERROR: %SNAP_ARTIFACTS% not found. >&2
    echo        Run "make snapshot" first ^(requires internet + full build^). >&2
    exit /b 1
)
echo     Snapshot directory found.

:: ── 5. Launch Streamlit from snapshot ───────────────────────────────
echo [5] Launching app ^(reads from demo_snapshot/^) ...
echo     Open http://localhost:%PORT% in your browser.
echo.
if "%DRY_RUN%"=="1" (
    echo [DRY-RUN] "%VENV_DIR%\Scripts\streamlit" run "%REPO_ROOT%\app\Home.py" --server.port %PORT%
) else (
    "%VENV_DIR%\Scripts\streamlit" run "%REPO_ROOT%\app\Home.py" ^
        --server.port %PORT% ^
        --server.headless true ^
        --browser.gatherUsageStats false
)
endlocal
