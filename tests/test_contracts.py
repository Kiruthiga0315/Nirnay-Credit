"""Contract tests: every public function returns exactly the keys in core/contracts.py for Meena.
When you replace a stub with real code these must keep passing."""
from typing import get_type_hints

import core
from core import contracts as c
from core.reference import MEENA_ID

ID = MEENA_ID


def keys(td):
    return set(get_type_hints(td))


def test_score():
    r = core.score(ID)
    assert set(r) == keys(c.ScoreResult)
    assert 0 <= r["pd"] <= 1 and len(r["reasons"]) == 3 and 0 <= r["data_confidence"] <= 100


def test_recourse_only_verifiable_levers():
    from core.features import by_name
    r = core.recourse(ID)
    assert set(r) == keys(c.RecourseResult)
    for a in r["actions"]:
        assert set(a) == keys(c.RecourseAction)
        assert by_name()[a["lever"]]["mutability"] == "verifiable"


def test_structure():
    r = core.structure(ID)
    assert set(r) == keys(c.StructureResult)
    assert len(r["schedule"]) == len(r["p10_band"]) == r["tenor_months"]


def test_fairness_optimize_stress_watch_trust():
    assert set(core.fairness_report(None)) == keys(c.FairnessReport)
    assert set(core.optimize({})) == keys(c.OptimizeResult)
    assert set(core.stress("covid_style")) == keys(c.StressResult)
    assert all(set(w) == keys(c.WatchRow) for w in core.watchlist(25))
    assert set(core.trust(ID)) == keys(c.TrustResult)
    assert set(core.attack("circular_upi")) == keys(c.AttackResult)


def test_documents_return_bytes():
    assert isinstance(core.make_cam(ID), bytes)
    assert isinstance(core.make_letter(ID, "ta"), bytes)


def test_determinism():
    assert core.score(ID) == core.score(ID)
