"""Tests for the governance backend decision ledger and override tracking."""
from core.governance import _hash_inputs, log_decision


def test_hash_inputs_stability():
    """Verify that identical inputs produce the identical stable hash."""
    inputs1 = {"revenue": 5000, "bureau_score": 750, "sector": "retail"}
    inputs2 = {"sector": "retail", "revenue": 5000, "bureau_score": 750}
    assert _hash_inputs(inputs1) == _hash_inputs(inputs2)

def test_ledger_append_only(tmp_path, monkeypatch):
    """Verify that ledger writes are append-only."""
    import core.governance
    test_ledger = tmp_path / "test_ledger.jsonl"
    monkeypatch.setattr(core.governance, "LEDGER_PATH", test_ledger)
    monkeypatch.setattr(core.governance, "ARTIFACTS", tmp_path)
    
    # Write first decision
    log_decision("MSME-001", "v1", {"rev": 100}, [{"reason": "test"}], "approve")
    entries_1 = core.governance.ledger(10)
    assert len(entries_1) == 1
    
    # Write second decision
    log_decision("MSME-002", "v1", {"rev": 200}, [{"reason": "test"}], "reject", override=True, override_reason="manual")
    entries_2 = core.governance.ledger(10)
    assert len(entries_2) == 2
    
    assert entries_2[0]["borrower_id"] == "MSME-001"
    assert entries_2[1]["borrower_id"] == "MSME-002"
    assert entries_2[1]["override"] is True
