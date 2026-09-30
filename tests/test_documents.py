"""Tests for core.documents — OWNER: M4.

Reference borrower: Meena (MSME-00001). All tests must pass with stub model.
Requires pandas (transitively via core.__init__ -> core.early_warning).
On Python 3.14 32-bit where no pandas wheel exists, tests are skipped.
"""
import pytest

pytest.importorskip("pandas")  # skip entire module if pandas is unavailable

from core.documents import make_cam, make_letter
from core.reference import MEENA


def test_make_cam_returns_bytes() -> None:
    """make_cam must return bytes."""
    doc = make_cam(MEENA)
    assert isinstance(doc, bytes)


def test_make_cam_contains_borrower_id() -> None:
    """CAM must include the borrower ID."""
    doc = make_cam(MEENA)
    assert MEENA["id"].encode() in doc


def test_make_cam_contains_pd() -> None:
    """CAM must mention PD (probability of default)."""
    content = make_cam(MEENA).decode("utf-8")
    assert "PD" in content


from unittest.mock import patch


@patch("core.models.score")
def test_make_cam_contains_stub_banner_for_stub_model(mock_score) -> None:
    """When model_version starts with 'stub', the CAM must show a STUB notice."""
    mock_score.return_value = {
        "borrower_id": "MSME-00001",
        "pd": 0.05,
        "pd_band": "low",
        "reasons": [],
        "data_confidence": 80,
        "model_version": "stub-0"
    }
    content = make_cam(MEENA).decode("utf-8")
    # stub-0 is the current MODEL_VERSION, so STUB DATA must appear
    assert "STUB" in content


def test_make_cam_has_officer_decision_box() -> None:
    """CAM must have an officer decision box for the credit file."""
    content = make_cam(MEENA).decode("utf-8")
    assert "Officer" in content or "officer" in content


def test_make_cam_has_recourse_section() -> None:
    """CAM must have a Path to Yes / recourse section."""
    content = make_cam(MEENA).decode("utf-8")
    assert "Recourse" in content or "Path to Yes" in content


def test_make_cam_has_structured_repayment() -> None:
    """CAM must have a Structured Repayment section."""
    content = make_cam(MEENA).decode("utf-8")
    assert "DSCR" in content or "Structured" in content


def test_make_cam_has_fairness_note() -> None:
    """CAM must include a fairness note."""
    content = make_cam(MEENA).decode("utf-8")
    assert "Fairness" in content or "fairness" in content


def test_make_cam_no_protected_attributes_as_inputs() -> None:
    """CAM fairness note must state protected attributes are not model inputs."""
    content = make_cam(MEENA).decode("utf-8")
    assert "owner gender" in content.lower() or "location class" in content.lower()


def test_make_letter_returns_bytes() -> None:
    """make_letter must return bytes."""
    doc = make_letter(MEENA, lang="en")
    assert isinstance(doc, bytes)


def test_make_letter_en_no_pending_review() -> None:
    """English letter must not have PENDING NATIVE REVIEW."""
    doc_en = make_letter(MEENA, lang="en")
    assert "PENDING NATIVE REVIEW" not in doc_en.decode("utf-8")


def test_make_letter_hi_pending_review() -> None:
    """Hindi letter must be marked PENDING NATIVE REVIEW."""
    doc = make_letter(MEENA, lang="hi")
    content = doc.decode("utf-8")
    assert MEENA["id"] in content
    assert "PENDING NATIVE REVIEW" in content


def test_make_letter_ta_pending_review() -> None:
    """Tamil letter must be marked PENDING NATIVE REVIEW."""
    doc = make_letter(MEENA, lang="ta")
    assert "PENDING NATIVE REVIEW" in doc.decode("utf-8")


def test_make_letter_mr_pending_review() -> None:
    """Marathi letter must be marked PENDING NATIVE REVIEW."""
    doc = make_letter(MEENA, lang="mr")
    assert "PENDING NATIVE REVIEW" in doc.decode("utf-8")


def test_make_letter_unknown_lang_falls_back_to_en() -> None:
    """Unknown lang must silently fall back to English."""
    doc = make_letter(MEENA, lang="xx")
    content = doc.decode("utf-8")
    assert "Loan Decision Letter" in content
    assert "PENDING NATIVE REVIEW" not in content


def test_make_letter_contains_borrower_id() -> None:
    """Letter must contain the borrower ID."""
    doc = make_letter(MEENA, lang="en")
    assert MEENA["id"].encode() in doc


def test_make_letter_stub_version_tag() -> None:
    """Letter must include the version tag for traceability."""
    content = make_letter(MEENA, lang="en").decode("utf-8")
    assert "stub_letter_v1" in content


def test_make_cam_from_id_string() -> None:
    """make_cam must accept a borrower ID string as well as a dict."""
    doc = make_cam("MSME-00001")
    assert isinstance(doc, bytes)
    assert b"MSME-00001" in doc


def test_make_letter_from_id_string() -> None:
    """make_letter must accept a borrower ID string."""
    doc = make_letter("MSME-00001", lang="en")
    assert isinstance(doc, bytes)
    assert b"MSME-00001" in doc
