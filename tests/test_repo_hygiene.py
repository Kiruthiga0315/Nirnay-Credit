import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
BANNED = re.compile(r"bias-free|99% accurate|guaranteed approval|RBI-compliant", re.I)


def test_no_banned_wording_in_app_or_core():
    bad = []
    for p in list((ROOT / "app").rglob("*.py")) + list((ROOT / "core").rglob("*.py")):
        if BANNED.search(p.read_text(encoding="utf-8")):
            bad.append(str(p))
    assert not bad, f"banned wording in: {bad}"


def test_no_generated_files_tracked_placeholder():
    for d in ("data", "models", "artifacts"):
        assert (ROOT / d / ".gitkeep").exists()
