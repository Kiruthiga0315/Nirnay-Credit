"""OWNER: M4. F12 Credit Appraisal Memo (CAM) + borrower letters (en/hi/ta/mr), template-driven.
Numbers are injected from structured JSON; no free-form generation. Native-speaker review needed."""
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
        "note": ""
    },
    "hi": {
        "title": "ऋण निर्णय पत्र (Loan Decision Letter)",
        "greeting": "प्रिय",
        "body": "आपके आवेदन की समीक्षा की गई है। यहाँ स्वीकृति का मार्ग है।",
        "note": "PENDING NATIVE REVIEW"
    },
    "ta": {
        "title": "கடன் முடிவு கடிதம் (Loan Decision Letter)",
        "greeting": "அன்புள்ள",
        "body": "உங்கள் விண்ணப்பம் மதிப்பாய்வு செய்யப்பட்டது. ஒப்புதலுக்கான வழி இதோ.",
        "note": "PENDING NATIVE REVIEW"
    },
    "mr": {
        "title": "कर्ज निर्णय पत्र (Loan Decision Letter)",
        "greeting": "प्रिय",
        "body": "तुमच्या अर्जाचे पुनरावलोकन केले गेले आहे. होयकडे जाण्याचा मार्ग येथे आहे.",
        "note": "PENDING NATIVE REVIEW"
    }
}


def make_cam(borrower: Borrower) -> bytes:
    b = resolve(borrower)
    bid = b.get("id", "UNKNOWN")
    
    html = f"""
    <html>
    <head><style>body {{ font-family: sans-serif; }} .box {{ border: 1px solid #ccc; padding: 10px; margin: 10px 0; }}</style></head>
    <body>
        <h1>Credit Appraisal Memo</h1>
        <div class="box">
            <h3>Borrower Profile</h3>
            <p>ID: {bid}</p>
            <p>Business: {b.get('business', 'N/A')} | Sector: {b.get('sector', 'N/A')}</p>
        </div>
        <div class="box">
            <h3>PD & Reasons</h3>
            <p>PD: [INSERT PD HERE]</p>
            <ul><li>[Reason 1 Placeholder]</li><li>[Reason 2 Placeholder]</li><li>[Reason 3 Placeholder]</li></ul>
        </div>
        <div class="box">
            <h3>Forecast & DSCR Structure</h3>
            <p>[DSCR CHART PLACEHOLDER]</p>
            <p>Structure Details: [SCHEDULE PLACEHOLDER]</p>
        </div>
        <div class="box">
            <h3>Fairness Note</h3>
            <p>This decision model operates within defined fairness constraints across protected segments.</p>
        </div>
        <div class="box">
            <h3>Model Version</h3>
            <p>Version: stub_model_v1</p>
        </div>
        <div class="box">
            <h3>Officer Decision Box</h3>
            <p>Decision: Approved / Declined / Structured</p>
            <br><br>
            <p>Signature: ___________________</p>
        </div>
    </body>
    </html>
    """
    return html.encode("utf-8")


def make_letter(borrower: Borrower, lang: str = "en") -> bytes:
    b = resolve(borrower)
    bid = b.get("id", "UNKNOWN")
    
    if lang not in LETTER_TEMPLATES:
        lang = "en"
        
    template = LETTER_TEMPLATES[lang]
    
    html = f"""
    <html>
    <head><style>body {{ font-family: sans-serif; line-height: 1.6; }} .note {{ color: red; font-size: 0.8em; }}</style></head>
    <body>
        <h1>{template['title']}</h1>
        <p>ID: {bid}</p>
        <p>Version: stub_letter_v1</p>
        <p>{template['greeting']} {b.get('business', 'Customer')},</p>
        <p>{template['body']}</p>
        <p>PD: [INSERT PD HERE]</p>
        <p>Conditions: [INSERT CONDITIONS HERE]</p>
        <p class="note">{template['note']}</p>
    </body>
    </html>
    """
    return html.encode("utf-8")


def build_artifacts(smoke: bool = False) -> None:
    print("[documents] STUB - M4 to implement")
