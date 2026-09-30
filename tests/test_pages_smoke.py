"""OWNER: M3. Smoke tests: every page renders without exception via Streamlit AppTest.

T1 covers:
  - All 8 pages + Home render with no exception.
  - Each page cold-starts (fresh AppTest) in < 15 s.
  - The 3 safe-borrower presets and every named scenario are exercised on pages
    that accept them (no exceptions expected).
"""
from __future__ import annotations

import pathlib
import time

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES = sorted((ROOT / "app" / "pages").glob("*.py")) + [ROOT / "app" / "Home.py"]

SAFE_BORROWER_IDS = ["MSME-00001", "MSME-00005", "MSME-00010"]

SCENARIOS = [
    "demonetisation_style",
    "gst_rollout_style",
    "covid_style",
    "rate_hike_2022_23_style",
    "custom",
]

# Pages that accept a borrower_id via session_state
BORROWER_PAGES = {
    "2_Borrower_Decision.py",
    "3_Borrower_Portal.py",
}

# Pages that accept a scenario via session_state
SCENARIO_PAGES = {
    "5_Stress_Contagion.py",
}

COLD_START_LIMIT_S = 15.0


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _run_page(path: pathlib.Path, **session_state: object) -> AppTest:
    """Run a page under AppTest with optional initial session state."""
    at = AppTest.from_file(str(path), default_timeout=COLD_START_LIMIT_S)
    for k, v in session_state.items():
        at.session_state[k] = v
    return at.run()


# ---------------------------------------------------------------------------
# T1a – basic render: no exception, cold start < COLD_START_LIMIT_S
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", PAGES, ids=lambda p: p.name)
def test_page_renders_no_exception(path: pathlib.Path) -> None:
    """Each page renders without raising an exception (cold start)."""
    t0 = time.monotonic()
    at = _run_page(path)
    elapsed = time.monotonic() - t0
    assert not at.exception, f"{path.name}: {at.exception}"
    assert elapsed < COLD_START_LIMIT_S, (
        f"{path.name}: cold start took {elapsed:.1f}s ≥ {COLD_START_LIMIT_S}s limit"
    )


@pytest.mark.parametrize("path", PAGES, ids=lambda p: p.name)
def test_page_cold_restart_no_exception(path: pathlib.Path) -> None:
    """Hard refresh (fresh AppTest instance) also renders without exception."""
    # Simulate hard refresh by creating a *second* fresh AppTest
    at = AppTest.from_file(str(path), default_timeout=COLD_START_LIMIT_S).run()
    assert not at.exception, f"{path.name} on hard refresh: {at.exception}"


# ---------------------------------------------------------------------------
# T1b – safe borrowers on borrower pages
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "page_name,borrower_id",
    [
        (page_name, bid)
        for page_name in BORROWER_PAGES
        for bid in SAFE_BORROWER_IDS
    ],
)
def test_borrower_pages_with_safe_presets(page_name: str, borrower_id: str) -> None:
    """Borrower pages render without exception for each of the 3 safe presets."""
    path = ROOT / "app" / "pages" / page_name
    if not path.exists():
        pytest.skip(f"{page_name} not found")
    at = _run_page(path, borrower_id=borrower_id)
    assert not at.exception, (
        f"{page_name} with borrower {borrower_id}: {at.exception}"
    )


# ---------------------------------------------------------------------------
# T1c – every named scenario on stress page
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "page_name,scenario",
    [
        (page_name, scenario)
        for page_name in SCENARIO_PAGES
        for scenario in SCENARIOS
    ],
)
def test_scenario_pages_with_all_scenarios(page_name: str, scenario: str) -> None:
    """Stress page renders without exception for each named scenario."""
    path = ROOT / "app" / "pages" / page_name
    if not path.exists():
        pytest.skip(f"{page_name} not found")
    at = _run_page(path, selected_scenario=scenario)
    assert not at.exception, (
        f"{page_name} with scenario {scenario}: {at.exception}"
    )
