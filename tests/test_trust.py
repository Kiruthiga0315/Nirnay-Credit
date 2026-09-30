"""Tests for data trust reconciliation, confidence scoring, and attack simulation."""

from core.reference import MEENA
from core.trust import ATTACKS, attack, audit_borrower, trust


def test_trust_meena():
    """Verify trust evaluation on reference borrower Meena (MSME-00001)."""
    res = trust(MEENA)
    assert res["borrower_id"] == "MSME-00001"
    assert 0 <= res["data_confidence"] <= 100
    assert isinstance(res["flags"], list)


def test_trust_hand_built_inconsistent_firm():
    """Verify that a firm with deliberate cross-source contradictions is flagged."""
    inconsistent_firm = {
        "id": "MSME-SYNTH-FRAUD",
        "sector": "auto_components",
        "revenue": 1000000.0,
        "gst_turnover": 4500000.0,  # 4.5x bank deposits -> inflated turnover
        "bank_inflow": 500000.0,
        "upi_inflow": 1500000.0,    # 1.5M/2.0M = 75% > 70% UPI in auto_components -> anomalous UPI
        "gstr1_3b_mismatch": 0.28,  # > 15% mismatch -> GSTR mismatch
        "gst_filing_delay_days": 40.0,  # > 30 days -> chronic delay
        "gst_filing_regularity": 0.50,
        "inflow_stability_cv": 0.02,  # CV < 0.05 on >500k -> artificial smoothing
        "bureau_score": None,       # thin file
    }

    res = trust(inconsistent_firm)
    assert res["borrower_id"] == "MSME-SYNTH-FRAUD"
    assert res["data_confidence"] <= 20
    flags = res["flags"]

    assert "FLAG_INFLATED_TURNOVER" in flags
    assert "FLAG_GSTR_MISMATCH" in flags
    assert "FLAG_CHRONIC_GST_DELAY" in flags
    assert "FLAG_ANOMALOUS_UPI" in flags
    assert "FLAG_ARTIFICIAL_SMOOTHING" in flags
    assert "FLAG_THIN_FILE" in flags


def test_trust_confidence_monotone_in_inconsistency():
    """Verify data_confidence is strictly monotonically non-increasing in discrepancies."""
    clean_firm = {
        "id": "MSME-CLEAN",
        "sector": "retail_trading",
        "revenue": 2000000.0,
        "gst_turnover": 2000000.0,
        "bank_inflow": 1500000.0,
        "upi_inflow": 500000.0,
        "gstr1_3b_mismatch": 0.02,
        "gst_filing_delay_days": 3.0,
        "gst_filing_regularity": 0.95,
        "inflow_stability_cv": 0.25,
        "bureau_score": 750,
    }

    conf_clean, flags_clean = audit_borrower(clean_firm)
    assert conf_clean == 100
    assert len(flags_clean) == 0

    # Step 1: Introduce GSTR mismatch (+20 penalty)
    step1 = dict(clean_firm, gstr1_3b_mismatch=0.20)
    conf_1, _ = audit_borrower(step1)

    # Step 2: Add inflated GST turnover (+25 penalty)
    step2 = dict(step1, gst_turnover=5000000.0)
    conf_2, _ = audit_borrower(step2)

    # Step 3: Add chronic GST filing delay (+10 penalty)
    step3 = dict(step2, gst_filing_delay_days=45.0)
    conf_3, _ = audit_borrower(step3)

    # Step 4: Add circular transfer pattern (+20 penalty)
    step4 = dict(step3, inflow_stability_cv=0.01)
    conf_4, _ = audit_borrower(step4)

    assert conf_clean > conf_1 >= conf_2 >= conf_3 >= conf_4
    assert 0 <= conf_4 <= 100


def test_attack_results():
    """Verify attack simulation returns valid AttackResult TypedDicts."""
    for kind in ATTACKS:
        res = attack(kind)
        assert res["attack"] == kind
        assert 0 <= res["flagged_before"] <= res["flagged_after"]
        assert 0.0 <= res["auc_after"] <= res["auc_before"] <= 1.0
