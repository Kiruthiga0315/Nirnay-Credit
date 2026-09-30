"""OWNER: M4. F12 Credit Appraisal Memo (CAM) + borrower letters (en/hi/ta/mr), template-driven.
Numbers are injected from structured JSON; no free-form generation. Native-speaker review needed."""
from __future__ import annotations

from core.contracts import Borrower
from core.reference import resolve

LANGS = ["en", "hi", "ta", "mr"]


def make_cam(borrower: Borrower) -> bytes:
    b = resolve(borrower)
    return f"<html><body><h1>Credit Appraisal Memo (STUB)</h1><p>{b['id']}</p></body></html>".encode()


def make_letter(borrower: Borrower, lang: str = "en") -> bytes:
    b = resolve(borrower)
    return f"<html><body><h1>Letter [{lang}] (STUB)</h1><p>{b['id']}</p></body></html>".encode()


def build_artifacts(smoke: bool = False) -> None:
    print("[documents] STUB - M4 to implement")
