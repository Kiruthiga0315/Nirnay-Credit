"""Tests for journey simulator and story mode – OWNER: M4.

Tests:
- journey PD curve is non-increasing when all levers move toward target
- story script has valid page targets (string, non-empty)
- story script slide ids are contiguous
- story script total duration matches last slide end
- SAFE_BORROWERS list has exactly 3 entries with distinct IDs
- page smoke for Home (Story Mode controls present)
- page smoke for 1_Portfolio (optimizer sliders present)
- page smoke for 3_Borrower_Portal (journey chart section present)

Reference borrower: Meena (MSME-00001).
"""
from __future__ import annotations

import json
import pathlib
from unittest.mock import patch

import pytest

pytest.importorskip("pandas")  # skip if pandas unavailable

from core.reference import MEENA, MEENA_ID

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_REPO = pathlib.Path(__file__).resolve().parents[1]
_SCRIPT_PATH = _REPO / "app" / "components" / "story_script.json"
_HOME_PATH = _REPO / "app" / "Home.py"
_P1_PATH = _REPO / "app" / "pages" / "1_Portfolio.py"
_P3_PATH = _REPO / "app" / "pages" / "3_Borrower_Portal.py"


# ---------------------------------------------------------------------------
# Helper: mock score so PD decreases monotonically when features improve
# ---------------------------------------------------------------------------
def _mock_score_from_receivable_days(borrower):
    """Return a deterministic PD that falls as receivable_days improves."""
    import core.contracts as cc

    rd = float(borrower.get("receivable_days", 78.0)) if isinstance(borrower, dict) else 78.0
    # Normalise: 78 days -> pd ~0.40, 28 days -> pd ~0.05
    pd = max(0.01, 0.01 + 0.40 * (rd / 100.0))
    return cc.ScoreResult(
        borrower_id=borrower.get("id", MEENA_ID) if isinstance(borrower, dict) else str(borrower),
        pd=round(pd, 4),
        pd_band="medium" if pd > 0.25 else "low",
        reasons=[{"feature": "receivable_days", "text": "Receivable days are high.", "impact": 0.15}],
        data_confidence=80,
        model_version="stub-test",
    )


# ---------------------------------------------------------------------------
# T1: journey simulator
# ---------------------------------------------------------------------------
class TestJourneySimulator:
    def test_pd_non_increasing_with_improving_levers(self):
        """PD curve must be non-increasing when levers move toward better targets."""
        from app.components.journey import simulate_journey

        # Recourse: reduce receivable_days from 78 to 28 (score mock decreases PD)
        recourse_result = {
            "borrower_id": MEENA_ID,
            "actions": [
                {
                    "lever": "receivable_days",
                    "label": "Receivable days",
                    "current": 78.0,
                    "target": 28.0,
                    "unit": "days",
                    "cost": 15.0,
                    "months": 6.0,
                }
            ],
            "new_pd": 0.07,
            "cost": 15.0,
            "months": 6.0,
            "valid_until_model": "stub-test",
        }

        with patch("app.components.journey.core.score", side_effect=_mock_score_from_receivable_days):
            result = simulate_journey(MEENA, recourse_result, months=6)

        pd_curve = result["pd_curve"]
        assert len(pd_curve) == 7, f"Expected 7 PD values (month 0..6), got {len(pd_curve)}"
        # Non-increasing: each value <= previous
        for i in range(1, len(pd_curve)):
            assert pd_curve[i] <= pd_curve[i - 1] + 1e-6, (
                f"PD rose at month {i}: {pd_curve[i - 1]} -> {pd_curve[i]}"
            )

    def test_simulate_journey_returns_required_keys(self):
        from app.components.journey import simulate_journey

        with patch("app.components.journey.core.score", side_effect=_mock_score_from_receivable_days):
            result = simulate_journey(MEENA, None, months=6)

        for key in ("months", "pd_curve", "approval_month", "threshold", "model_version", "interpolation"):
            assert key in result, f"Missing key: {key}"

    def test_simulate_journey_months_list_length(self):
        from app.components.journey import simulate_journey

        with patch("app.components.journey.core.score", side_effect=_mock_score_from_receivable_days):
            result = simulate_journey(MEENA, None, months=6)

        assert result["months"] == list(range(7))
        assert len(result["pd_curve"]) == 7

    def test_simulate_journey_interpolation_documented(self):
        from app.components.journey import simulate_journey

        with patch("app.components.journey.core.score", side_effect=_mock_score_from_receivable_days):
            result = simulate_journey(MEENA, None, months=6)

        assert result["interpolation"] == "s-curve"

    def test_approval_month_detected_when_threshold_crossed(self):
        from app.components.journey import APPROVAL_THRESHOLD, simulate_journey

        recourse_result = {
            "borrower_id": MEENA_ID,
            "actions": [
                {
                    "lever": "receivable_days",
                    "current": 78.0,
                    "target": 1.0,   # extreme improvement -> PD will drop below threshold
                    "unit": "days",
                    "cost": 15.0,
                    "months": 6.0,
                }
            ],
            "new_pd": 0.01,
            "cost": 15.0,
            "months": 6.0,
            "valid_until_model": "stub-test",
        }

        with patch("app.components.journey.core.score", side_effect=_mock_score_from_receivable_days):
            result = simulate_journey(MEENA, recourse_result, months=6)

        pd_curve = result["pd_curve"]
        approval_month = result["approval_month"]
        if any(pd < APPROVAL_THRESHOLD for pd in pd_curve):
            assert approval_month is not None
            assert pd_curve[approval_month] < APPROVAL_THRESHOLD


# ---------------------------------------------------------------------------
# T3: Story script validation
# ---------------------------------------------------------------------------
class TestStoryScript:
    @pytest.fixture(scope="class")
    def script(self):
        assert _SCRIPT_PATH.exists(), f"story_script.json not found at {_SCRIPT_PATH}"
        return json.loads(_SCRIPT_PATH.read_text(encoding="utf-8"))

    def test_script_has_slides(self, script):
        assert "slides" in script
        assert len(script["slides"]) > 0

    def test_slide_page_targets_are_non_empty_strings(self, script):
        for slide in script["slides"]:
            pt = slide.get("page_target")
            assert isinstance(pt, str) and pt.strip(), (
                f"Slide {slide.get('id')} has invalid page_target: {pt!r}"
            )

    def test_slide_ids_are_contiguous(self, script):
        ids = [s["id"] for s in script["slides"]]
        assert ids == list(range(len(ids))), f"Slide IDs not contiguous: {ids}"

    def test_slide_callouts_are_non_empty(self, script):
        for slide in script["slides"]:
            callout = slide.get("callout", "")
            assert callout.strip(), f"Slide {slide.get('id')} has empty callout"

    def test_total_duration_consistent(self, script):
        """Last slide end time must equal or exceed total_duration_seconds."""
        total = script.get("total_duration_seconds", 0)
        last_end = script["slides"][-1].get("time_end", 0)
        assert last_end >= total - 1, (
            f"total_duration_seconds={total} but last slide ends at {last_end}"
        )

    def test_guided_tour_has_5_steps(self, script):
        tour = script.get("guided_tour", [])
        assert len(tour) == 5, f"Guided tour must have 5 steps, got {len(tour)}"

    def test_guided_tour_page_targets_valid(self, script):
        for step in script.get("guided_tour", []):
            pt = step.get("page_target")
            assert isinstance(pt, str) and pt.strip(), (
                f"Tour step {step.get('step')} has invalid page_target: {pt!r}"
            )


# ---------------------------------------------------------------------------
# T4: Safe borrower presets
# ---------------------------------------------------------------------------
class TestSafeBorrowers:
    def test_exactly_three_presets(self):
        from app.components.journey import SAFE_BORROWERS

        assert len(SAFE_BORROWERS) == 3, f"Expected 3 presets, got {len(SAFE_BORROWERS)}"

    def test_preset_ids_are_distinct(self):
        from app.components.journey import SAFE_BORROWERS

        ids = [p["id"] for p in SAFE_BORROWERS]
        assert len(set(ids)) == len(ids), f"Preset IDs not distinct: {ids}"

    def test_meena_is_first_preset(self):
        from app.components.journey import SAFE_BORROWERS

        assert SAFE_BORROWERS[0]["id"] == MEENA_ID

    def test_preset_ids_in_test_borrower_range(self):
        from app.components.journey import SAFE_BORROWERS
        from core.reference import TEST_BORROWER_IDS

        for preset in SAFE_BORROWERS:
            assert preset["id"] in TEST_BORROWER_IDS, (
                f"Preset {preset['id']} not in TEST_BORROWER_IDS"
            )


# ---------------------------------------------------------------------------
# Page smoke tests (AppTest)
# ---------------------------------------------------------------------------
try:
    from streamlit.testing.v1 import AppTest

    _HAS_APPTEST = True
except ImportError:
    _HAS_APPTEST = False


@pytest.mark.skipif(not _HAS_APPTEST, reason="streamlit AppTest unavailable")
class TestPageSmoke:
    def _run(self, path: pathlib.Path, timeout: int = 30):
        at = AppTest.from_file(str(path), default_timeout=timeout)
        with patch("core.models.score", side_effect=_mock_score_from_receivable_days):
            at.run()
        return at

    def test_home_no_exception(self):
        at = self._run(_HOME_PATH)
        assert not at.exception

    def test_home_has_story_button(self):
        at = self._run(_HOME_PATH)
        button_labels = [b.label for b in at.button]
        assert any("Play Demo" in lbl or "Play" in lbl for lbl in button_labels), (
            f"No 'Play Demo' button found; buttons: {button_labels}"
        )

    def test_portfolio_no_exception(self):
        at = self._run(_P1_PATH)
        assert not at.exception

    def test_portfolio_has_optimizer_sliders(self):
        at = self._run(_P1_PATH)
        slider_labels = [s.label for s in at.slider]
        # Expect at least one slider related to optimizer (budget, loss cap, etc.)
        assert len(slider_labels) >= 2, (
            f"Expected ≥2 sliders in Portfolio, got {slider_labels}"
        )

    def test_portal_no_exception(self):
        at = self._run(_P3_PATH)
        assert not at.exception

    def test_portal_no_jargon(self):
        """Page 3 must not contain ML jargon."""
        source = _P3_PATH.read_text(encoding="utf-8")
        jargon = ["SHAP", "AUC", "Gini", " PD ", " DSCR "]
        # Comments and docstrings are allowed; scan visible strings only (heuristic: st.write / st.markdown calls)
        import re

        strings_in_source = re.findall(r'(?:st\.write|st\.markdown|st\.subheader|st\.title)\s*\(\s*["\']([^"\']+)["\']', source)
        found_jargon = [j for j in jargon if any(j in s for s in strings_in_source)]
        assert not found_jargon, f"Jargon found in Page 3 user-visible strings: {found_jargon}"
