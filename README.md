# PS12 - Governed MSME Lending Cockpit
Hackconquest Hackathon, Aether 2026 (TCET Mumbai) - PS 12: Predictive Credit Risk Analytics for MSMEs.

> Every MSME loan decision (approve, structure or decline) comes with a reason, a route to yes, a fairness cost
> and a stress-tested loss number, in one governed workflow.

## Quick start
    python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
    pip install -r requirements-dev.txt
    python run_all.py --smoke --keep-going                 # rebuild data -> models -> artifacts (tiny)
    python -m pytest && ruff check .                       # same checks CI runs
    streamlit run app/Home.py                              # open the cockpit (stubs until artifacts exist)

## Repo map
| Path | What |
|---|---|
| `core/` | pure-Python SDK (no Streamlit). Public API in `core/__init__.py`, types in `core/contracts.py` |
| `app/` | Streamlit UI: `Home.py`, `pages/` (one file per page), `components/` |
| `configs/` | `feature_spec.json` (single source of truth), generator grid, scenarios, Meena persona |
| `artifacts/`, `data/`, `models/` | generated, git-ignored |
| `demo_snapshot/` | committed snapshot used by the deployed app (M3 only) |
| `docs/` | contracts, artifacts, ownership, gates, claims, data statement, model card, idea docs, AI prompts |
| `docs/prompts/` | phase-by-phase Antigravity master + verification prompts |

## Team & workflow
See [CONTRIBUTING.md](CONTRIBUTING.md), [docs/OWNERSHIP.md](docs/OWNERSHIP.md), [docs/GATES.md](docs/GATES.md).
AI agents must follow [AGENTS.md](AGENTS.md).

## Status (fill from artifacts/metrics.json only)
TODO(M4): architecture diagram, data statement link, results table, limitations, live URL, demo video.

## Honest limits
Results come from synthetic data under documented assumptions and are method validation, not India-level forecasts.
Recourse is a decision aid, not causal. RBI FREE-AI is advisory guidance; we map to it and do not claim compliance.
