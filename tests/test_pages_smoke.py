"""Every page must render without an exception (Streamlit AppTest). Owner: M3."""
import pathlib

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES = sorted((ROOT / "app" / "pages").glob("*.py")) + [ROOT / "app" / "Home.py"]


@pytest.mark.parametrize("path", PAGES, ids=lambda p: p.name)
def test_page_renders(path):
    at = AppTest.from_file(str(path), default_timeout=30).run()
    assert not at.exception, f"{path.name}: {at.exception}"
