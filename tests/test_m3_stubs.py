import pytest

from core.early_warning import watchlist
from core.governance import consent_artifact, ledger
from core.reference import TEST_BORROWER_IDS
from core.stress import stress
from core.trust import attack, trust


def test_stress():
    res = stress("demonetisation_style")
    assert res["scenario"] == "demonetisation_style"
    assert res["expected_loss"] > 0
    assert "es95" in res
    assert "textile" in res["segment_losses"]

    with pytest.raises(ValueError, match="Unknown scenario id"):
        stress("nope")

def test_early_warning():
    w = watchlist(25)
    assert len(w) == 10
    assert "hazard" in w[0]
    assert w[0]["action"] in ["call", "restructure", "reduce_limit", "monitor"]
    assert "rank" in w[0]

def test_trust():
    b_id = TEST_BORROWER_IDS[0]
    res = trust(b_id)
    assert res["borrower_id"] == b_id
    assert 0 <= res["data_confidence"] <= 100

def test_attack():
    res = attack("circular_upi")
    assert res["attack"] == "circular_upi"
    assert res["flagged_before"] < res["flagged_after"]

def test_governance():
    L = ledger(5)
    assert len(L) == 5
    assert "decision_id" in L[0]
    
    ca = consent_artifact("MSME-00001")
    assert ca["borrower_id"] == "MSME-00001"
