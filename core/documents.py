"""OWNER: M4. F12 Credit Appraisal Memo (CAM) + borrower letters (en/hi/ta/mr), template-driven.

Numbers are injected from core.score, core.recourse, and core.structure.
No free-form generation. Native-speaker review needed for hi/ta/mr.

Public functions (contract-frozen signatures):
    make_cam(borrower) -> bytes  (UTF-8 encoded HTML)
    make_letter(borrower, lang='en') -> bytes  (UTF-8 encoded HTML)

Example:
    from core.documents import make_cam, make_letter
    from core.reference import MEENA
    cam = make_cam(MEENA)
    assert b'MSME-00001' in cam
"""
from __future__ import annotations

from core.contracts import Borrower
from core.reference import resolve

LANGS = ["en", "hi", "ta", "mr"]

# Define letter templates as a dictionary to avoid free generation
LETTER_TEMPLATES = {
    "en": {
        "title": "Loan Decision Letter",
        "greeting": "Dear",
        "body": "Your application has been reviewed. Here is the path to yes.",
        "note": "",
    },
    "hi": {
        "title": "Rin Nirnay Patra (Loan Decision Letter)",
        "greeting": "Priya",
        "body": "Aapke aavedan ki samiksha ki gayi hai. Yahan svikruti ka marg hai.",
        "note": "PENDING NATIVE REVIEW",
    },
    "ta": {
        "title": "Kadan Mudivukkadidham (Loan Decision Letter)",
        "greeting": "Anpulla",
        "body": "Ungal vinnappam mathippaayvuseyappattadu. Oppudhalukkaana vazhi idho.",
        "note": "PENDING NATIVE REVIEW",
    },
    "mr": {
        "title": "Karz Nirnay Patra (Loan Decision Letter)",
        "greeting": "Priya",
        "body": "Tumchya arjache punaravalokan kele gele aahe. Hoyakade janyacha marg yethe aahe.",
        "note": "PENDING NATIVE REVIEW",
    },
}

# CSS shared by CAM and letter
_CSS = """
body { font-family: 'Helvetica Neue', Arial, sans-serif; margin: 2rem; color: #1e293b; }
h1 { color: #0f766e; border-bottom: 2px solid #0f766e; padding-bottom: .4rem; }
h2 { color: #0f766e; font-size: 1rem; margin-top: 1.5rem; }
.box { border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem 1.25rem; margin: .75rem 0; background: #f8fafc; }
.kpi { display: inline-block; min-width: 140px; margin: .25rem .75rem .25rem 0; }
.kpi .val { font-size: 1.3rem; font-weight: bold; color: #0f766e; }
.kpi .lbl { font-size: .75rem; color: #64748b; }
.stub { background: #fef3c7; color: #b45309; padding: .3rem .7rem; border-radius: 6px;
        font-size: .8rem; margin-bottom: 1rem; }
.note { color: #dc2626; font-size: .8em; }
.footer { margin-top: 2rem; font-size: .8rem; color: #94a3b8; }
table { width: 100%; border-collapse: collapse; margin-top: .5rem; }
th, td { text-align: left; padding: .4rem .6rem; border-bottom: 1px solid #e2e8f0; font-size: .9rem; }
th { background: #f1f5f9; }
"""


def _inr(x: float) -> str:
    """Indian grouping: 1234567 -> INR 12,34,567."""
    neg = x < 0
    whole = f"{abs(x):.0f}"
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups: list[str] = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join([*groups, tail])
    return f"{'-' if neg else ''}INR {whole}"


def make_cam(borrower: Borrower) -> bytes:
    """Return the Credit Appraisal Memo as UTF-8-encoded HTML bytes.

    Injects live numbers from core.score, core.recourse, and core.structure.
    Shows a STUB banner when model_version starts with 'stub'.

    Example:
        doc = make_cam("MSME-00001")
        assert b'MSME-00001' in doc
        assert b'PD' in doc

    Args:
        borrower: feature dict (must contain 'id') or borrower id string.

    Returns:
        bytes: UTF-8 encoded HTML document.
    """
    # Import here to avoid circular imports at module level
    from core.models import APPROVAL_PD_THRESHOLD
    from core.models import score as _score
    from core.recourse import recourse as _recourse
    from core.structuring import structure as _structure

    b = resolve(borrower)
    bid = b.get("id", "UNKNOWN")

    # --- call core functions -------------------------------------------------
    try:
        s = _score(borrower)
    except Exception:  # noqa: BLE001
        s = {
            "pd": float("nan"), "pd_band": "unknown", "reasons": [],
            "data_confidence": 0, "model_version": "stub-error",
        }

    try:
        rec = _recourse(borrower)
    except Exception:  # noqa: BLE001
        rec = {"actions": [], "new_pd": float("nan"), "cost": 0.0,
               "months": 0.0, "valid_until_model": "unknown"}

    try:
        plan = _structure(borrower)
    except Exception:  # noqa: BLE001
        plan = {"schedule": [], "p10_band": [], "default_flat": float("nan"),
                "default_matched": float("nan"), "target_dscr": 1.25, "tenor_months": 0}

    # --- helpers -------------------------------------------------------------
    pd_val = s["pd"]
    approved = pd_val < APPROVAL_PD_THRESHOLD if not _is_nan(pd_val) else False
    decision_word = "APPROVED (under policy threshold)" if approved else "DECLINED (above policy threshold)"
    is_stub = str(s.get("model_version", "stub")).startswith("stub")
    stub_banner = (
        '<div class="stub">STUB DATA -- not a real model result. Do not use for decisions.</div>'
        if is_stub else ""
    )

    # reasons rows
    reason_rows = "".join(
        f"<tr><td>{r['feature']}</td><td>{r['text']}</td><td>{r['impact']:+.3f}</td></tr>"
        for r in s.get("reasons", [])
    )

    # recourse rows
    rec_rows = "".join(
        f"<tr><td>{a['label']}</td><td>{a['current']}</td><td>{a['target']}</td>"
        f"<td>{a['unit']}</td><td>{a['months']:.0f} months</td></tr>"
        for a in rec.get("actions", [])
    )

    # schedule summary
    schedule = plan.get("schedule", [])
    p10 = plan.get("p10_band", [])
    sched_rows = "".join(
        f"<tr><td>M{i+1}</td><td>{_inr(p10[i])}</td><td>{_inr(schedule[i])}</td></tr>"
        for i in range(min(len(schedule), len(p10)))
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>CAM - {bid}</title>
<style>{_CSS}</style></head>
<body>
{stub_banner}
<h1>Credit Appraisal Memo</h1>
<p style="color:#64748b; font-size:.85rem;">Prepared for internal use only.
This document is a decision aid under our documented assumptions.</p>

<div class="box">
  <h2>Borrower Profile</h2>
  <div class="kpi"><div class="val">{bid}</div><div class="lbl">Borrower ID</div></div>
  <div class="kpi"><div class="val">{b.get('business', 'N/A')}</div><div class="lbl">Business</div></div>
  <div class="kpi"><div class="val">{b.get('sector', 'N/A')}</div><div class="lbl">Sector</div></div>
  <div class="kpi"><div class="val">{b.get('udyam_category', 'N/A').upper()}</div><div class="lbl">Udyam Category</div></div>
  <div class="kpi"><div class="val">{b.get('vintage_months', 'N/A')} months</div><div class="lbl">Vintage</div></div>
  <div class="kpi"><div class="val">{_inr(float(b.get('requested_amount', 0)))}</div><div class="lbl">Requested Amount</div></div>
</div>

<div class="box">
  <h2>Risk Assessment</h2>
  <div class="kpi"><div class="val">{pd_val:.1%}</div><div class="lbl">PD (12m)</div></div>
  <div class="kpi"><div class="val">{s.get('pd_band','N/A').upper()}</div><div class="lbl">PD Band</div></div>
  <div class="kpi"><div class="val">{s.get('data_confidence', 0)}/100</div><div class="lbl">Data Confidence</div></div>
  <div class="kpi"><div class="val">{decision_word}</div><div class="lbl">Preliminary Decision</div></div>
  <p style="font-size:.8rem;color:#64748b;">Model version: {s.get('model_version', 'unknown')}</p>
  <h2>Key Reasons</h2>
  <table><tr><th>Feature</th><th>Plain-language text</th><th>Impact</th></tr>
  {reason_rows if reason_rows else '<tr><td colspan="3">No reasons available</td></tr>'}
  </table>
</div>

<div class="box">
  <h2>Path to Yes (Recourse)</h2>
  <div class="kpi"><div class="val">{rec.get('new_pd', float('nan')):.1%}</div><div class="lbl">New PD after recourse</div></div>
  <div class="kpi"><div class="val">{rec.get('months', 0):.0f} months</div><div class="lbl">Time to achieve</div></div>
  <p style="font-size:.8rem;color:#64748b;">Valid until model version: {rec.get('valid_until_model','unknown')}.
  Illustrative parameters under our documented assumptions.</p>
  <table><tr><th>Lever</th><th>Current</th><th>Target</th><th>Unit</th><th>Time</th></tr>
  {rec_rows if rec_rows else '<tr><td colspan="5">No recourse actions available</td></tr>'}
  </table>
</div>

<div class="box">
  <h2>Structured Repayment (DSCR-matched)</h2>
  <div class="kpi"><div class="val">{plan.get('target_dscr', 1.25):.2f}</div><div class="lbl">Target DSCR</div></div>
  <div class="kpi"><div class="val">{plan.get('default_matched', float('nan')):.1%}</div><div class="lbl">Default rate (matched)</div></div>
  <div class="kpi"><div class="val">{plan.get('default_flat', float('nan')):.1%}</div><div class="lbl">Default rate (flat EMI)</div></div>
  <table><tr><th>Month</th><th>P10 Cash</th><th>Instalment</th></tr>
  {sched_rows if sched_rows else '<tr><td colspan="3">No schedule available</td></tr>'}
  </table>
</div>

<div class="box">
  <h2>Fairness Note</h2>
  <p>This decision model operates within defined fairness constraints across protected segments.
  Owner gender and location class are never model inputs.
  Recourse uses only verifiable levers; gameable and immutable features are never offered as advice.</p>
</div>

<div class="box">
  <h2>Officer Decision Box</h2>
  <p><b>Preliminary decision:</b> {decision_word}</p>
  <p>Officer override decision: &nbsp;&nbsp; Approved &nbsp;&nbsp; / &nbsp;&nbsp;
     Declined &nbsp;&nbsp; / &nbsp;&nbsp; Structured</p>
  <p>Reason for override (if any):</p>
  <div style="border-bottom:1px solid #cbd5e1; margin: 1rem 0;"></div>
  <div style="border-bottom:1px solid #cbd5e1; margin: 1rem 0;"></div>
  <p>Officer signature: _______________________&nbsp;&nbsp;&nbsp;
     Date: _______________________</p>
</div>

<div class="footer">
  Model version: {s.get('model_version', 'unknown')} &nbsp;|&nbsp;
  Generated for: {bid} &nbsp;|&nbsp;
  This document is a decision aid; the final decision rests with the credit officer.
</div>
</body></html>"""
    return html.encode("utf-8")


def make_letter(borrower: Borrower, lang: str = "en") -> bytes:
    """Return a borrower-facing loan decision letter as UTF-8-encoded HTML bytes.

    Template-driven (numbers injected from core.score); no free-form generation.
    Four languages: en, hi, ta, mr. Non-English templates are marked PENDING NATIVE REVIEW.

    Example:
        doc = make_letter("MSME-00001", lang="en")
        assert b'MSME-00001' in doc
        assert b'PENDING NATIVE REVIEW' not in doc

    Args:
        borrower: feature dict (must contain 'id') or borrower id string.
        lang: language code ('en' | 'hi' | 'ta' | 'mr'). Defaults to 'en'.

    Returns:
        bytes: UTF-8 encoded HTML letter.
    """
    from core.models import score as _score

    b = resolve(borrower)
    bid = b.get("id", "UNKNOWN")

    if lang not in LETTER_TEMPLATES:
        lang = "en"

    template = LETTER_TEMPLATES[lang]

    # Get real PD and model version
    try:
        s = _score(borrower)
        pd_str = f"{s['pd']:.1%}"
        model_ver = s.get("model_version", "stub-error")
    except Exception:  # noqa: BLE001
        pd_str = "[unavailable]"
        model_ver = "stub-error"

    is_stub = str(model_ver).startswith("stub")
    stub_note = (
        "<p class=\"note\">[STUB DATA -- illustrative result only. Not a real lending decision.]</p>"
        if is_stub else ""
    )

    html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head><meta charset="utf-8"><title>{template['title']} - {bid}</title>
<style>
body {{ font-family: 'Helvetica Neue', Arial, sans-serif; margin: 2rem; line-height: 1.7; color: #1e293b; }}
h1 {{ color: #0f766e; }}
.note {{ color: #dc2626; font-size: 0.8em; }}
.footer {{ margin-top: 2rem; font-size: .8rem; color: #94a3b8; }}
</style></head>
<body>
<h1>{template['title']}</h1>
<p>Borrower ID: {bid}</p>
<p>Version: stub_letter_v1</p>
{stub_note}

<p>{template['greeting']} {b.get('business', 'Customer')},</p>
<p>{template['body']}</p>
<p><b>Probability of Default (12m):</b> {pd_str}</p>
<p>For the recommended steps to improve your profile, please contact your lender.</p>
<p class="note">{template['note']}</p>

<div class="footer">
  Model version: {model_ver} | This letter is a decision aid. The final decision rests
  with the credit officer. Wording: "illustrative parameters under our documented assumptions."
</div>
</body></html>"""
    return html.encode("utf-8")


def _is_nan(x: object) -> bool:
    try:
        import math
        return math.isnan(float(x))  # type: ignore
    except Exception:  # noqa: BLE001
        return False


def build_artifacts(smoke: bool = False) -> None:
    """Write CAM and letter artifacts for the reference borrower (Meena)."""
    from core.paths import ARTIFACTS
    from core.reference import MEENA

    out_dir = ARTIFACTS / "documents"
    out_dir.mkdir(parents=True, exist_ok=True)

    cam = make_cam(MEENA)
    (out_dir / "cam_MSME-00001.html").write_bytes(cam)

    for lang in LANGS:
        letter = make_letter(MEENA, lang=lang)
        (out_dir / f"letter_MSME-00001_{lang}.html").write_bytes(letter)

    print(f"[documents] wrote CAM + {len(LANGS)} letters to {out_dir}")
