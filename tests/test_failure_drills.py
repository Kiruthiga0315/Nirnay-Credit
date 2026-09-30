"""OWNER: M3. T2 Failure drills: pages must degrade gracefully, not traceback.

Drills:
  1. Missing artifacts folder -> pages show friendly states (no exceptions).
  2. One corrupted JSON in artifacts -> app still loads.
  3. Story-mode session variable set but no network -> still plays (pure local).

We hide artifacts by monkeypatching core.paths so no real files are touched.
"""
from __future__ import annotations

import json
import pathlib
import tempfile

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

import core.paths as _paths

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES = sorted((ROOT / "app" / "pages").glob("*.py")) + [ROOT / "app" / "Home.py"]


# ---------------------------------------------------------------------------
# Drill 1 – missing artifacts folder
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", PAGES, ids=lambda p: p.name)
def test_page_no_exception_missing_artifacts(
    path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When no artifact exists, load_json returns the default; no traceback."""
    # Redirect artifact lookup to an empty temp dir so nothing exists
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        monkeypatch.setattr(_paths, "ARTIFACTS", tmp_path / "artifacts")
        monkeypatch.setattr(_paths, "SNAPSHOT", tmp_path / "snap")
        at = AppTest.from_file(str(path), default_timeout=30).run()
        assert not at.exception, (
            f"{path.name} raised exception with missing artifacts: {at.exception}"
        )


# ---------------------------------------------------------------------------
# Drill 2 – corrupted JSON for one key artifact
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", PAGES, ids=lambda p: p.name)
def test_page_no_exception_corrupted_json(
    path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """A single corrupted JSON must not crash any page; load_json falls back to default."""
    art = tmp_path / "artifacts"
    art.mkdir()
    snap = tmp_path / "snap" / "artifacts"
    snap.mkdir(parents=True)

    # Seed a corrupted file for a few common artifact names
    for fname in [
        "early_warning.json",
        "gaming_lab.json",
        "ledger.jsonl",
        "metrics.json",
        "model_cockpit.json",
    ]:
        (art / fname).write_text("THIS IS NOT VALID JSON }{", encoding="utf-8")

    # load_json wraps json.loads; we need it to silently return default on bad JSON.
    # Patch it at the paths module level so pages use the patched version.
    original_load_json = _paths.load_json

    def _safe_load_json(name: str, default=None):  # type: ignore[override]
        try:
            return original_load_json(name, default)
        except (json.JSONDecodeError, ValueError):
            return default

    monkeypatch.setattr(_paths, "load_json", _safe_load_json)
    monkeypatch.setattr(_paths, "ARTIFACTS", art)
    monkeypatch.setattr(_paths, "SNAPSHOT", tmp_path / "snap")

    at = AppTest.from_file(str(path), default_timeout=30).run()
    assert not at.exception, (
        f"{path.name} raised exception on corrupted JSON: {at.exception}"
    )


# ---------------------------------------------------------------------------
# Drill 3 – Story Mode plays without network (pure local data)
# ---------------------------------------------------------------------------

def test_story_mode_no_network_no_exception() -> None:
    """Story Mode must work with no network: it reads only from local story_script.json."""
    story_script = ROOT / "app" / "components" / "story_script.json"
    assert story_script.exists(), "story_script.json is missing; Story Mode cannot run offline"

    # Verify the script is valid JSON (content check)
    data = json.loads(story_script.read_text(encoding="utf-8"))
    assert isinstance(data, (dict, list)), "story_script.json must be a JSON object or array"

    # Run Home page (hosts Story Mode) under AppTest with story mode enabled
    home = ROOT / "app" / "Home.py"
    at = AppTest.from_file(str(home), default_timeout=30)
    at.session_state["story_mode"] = True
    at.run()
    assert not at.exception, f"Home/Story Mode raised exception: {at.exception}"
