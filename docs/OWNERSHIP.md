# Ownership map (one owner per file)

| Member | Role | Owns |
|---|---|---|
| **M1** | Data & Modelling Lead | `core/generator.py` `legacy_policy.py` `models.py` `external.py`; `configs/generator/`; `configs/personas/`; `app/pages/7_Model_Cockpit.py`; `docs/data_statement.md`; `docs/model_card.md`; claims sign-off |
| **M2** | Decision Science Lead | `core/features.py` `explain.py` `recourse.py` `forecast.py` `structuring.py` `fairness.py` `optimizer.py`; `configs/feature_spec.json`; `app/pages/4_Fairness_Studio.py` |
| **M3** | Risk Systems & Platform Lead | `core/stress.py` `early_warning.py` `trust.py` `governance.py`; `configs/scenarios.yaml`; `run_all.py`; `Makefile`; `requirements*.txt`; `.github/`; `scripts/`; `tests/test_pages_smoke.py`; `demo_snapshot/`; pages 5, 6, 8; deploy |
| **M4** | Product, UI & Story Lead | `core/documents.py`; `app/Home.py`; `app/components/`; pages 1, 2, 3; `README.md`; deck; video; `docs/QA_PREP.md`; claims compiler |
| **All (frozen)** | | `core/contracts.py` `paths.py` `reference.py` `__init__.py`; `docs/CONTRACTS.md`; `docs/ARTIFACTS.md` |

Tests: each member adds files named `tests/test_<module>.py` for their own modules (no shared test files).
Load balancing: if M3 or M4 is overloaded at H16, move one page by a CODEOWNERS PR (e.g. page 6 -> M1).
