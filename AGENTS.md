# AGENTS.md - rules for every AI agent (Antigravity) working in this repo

Project: **PS12 governed MSME lending cockpit** (Hackconquest, Aether 2026). Four humans (M1-M4) build in
parallel, each with their own agent. These rules exist so four agents never collide.

## Read order (once per task, do not re-read files in loops)
1. this file  2. docs/OWNERSHIP.md  3. docs/CONTRACTS.md  4. docs/ARTIFACTS.md
5. only the Blueprint / Plan sections your prompt cites (docs/ideas/*.md)

## Golden rules
1. **Ownership.** Edit ONLY files your prompt lists as yours. Need a change elsewhere? Do not edit it:
   append a request to `docs/known_issues/<member>.md` and tell your human.
2. **Contracts are frozen.** Never edit `core/contracts.py`, `core/paths.py`, `core/reference.py`,
   `core/__init__.py`. Keep public function signatures and return keys EXACTLY as in the contracts.
   Replace stubs *inside your own module*; the UI and other members keep working.
3. **UI reads only artifacts.** `app/` calls `core.*` functions and reads `artifacts/` through
   `core.paths`. Never train, run SHAP, Monte Carlo or optimisation inside the UI.
4. **Namespaced outputs.** Write only your own artifacts (see docs/ARTIFACTS.md). Metrics go through
   `core.paths.write_metrics("<your_namespace>", {...})`. Never write to a shared file.
5. **No generated files in git.** Never commit `data/`, `models/`, `artifacts/` (only M3 commits
   `demo_snapshot/`).
6. **Determinism.** Seed = 42 by default; every random call takes a seed. `python run_all.py --smoke`
   must finish in under 2 minutes and the full build in under 10.
7. **No invented numbers.** Every number shown to a user or put on a slide must come from code and be
   logged in `docs/claims/<member>.md` with its key in `artifacts/metrics.json`. Never fabricate citations,
   dataset names, licences or URLs; write `TODO(verify)` instead. Expected ranges in prompts are sanity
   checks, not targets: if a result is outside, investigate the cause, do not tune it into range.
8. **Stubs are labelled.** Stub outputs keep `model_version` starting with `stub`. Real outputs must not.
9. **Wording rules.** Say: "under our documented assumptions", "measured and mitigated", "decision aid",
   "illustrative parameters". Never write: "bias-free", "99% accurate", "guaranteed approval",
   "RBI-compliant" (a test enforces this). FREE-AI is advisory guidance: we map to it, never claim compliance.
10. **Protected attributes** (owner_gender, location_class) are never model inputs. Recourse uses only
    `verifiable` levers; `gameable` and `immutable` features are never offered as advice.
11. **Dependencies.** Do not add packages. If one is essential, ask M3 (requirements.txt owner) via
    known_issues; use what is in requirements.txt.
12. **INR everywhere** (Indian grouping via `app.components.ui.inr`). Every chart has a one-line caption.
13. **Quality gate before you say "done":** `ruff check .` and `python -m pytest` pass, and
    `python run_all.py --smoke --keep-going` prints no FAIL for your stage. Add/extend tests for every
    function you implement (use Meena `MSME-00001` as the known borrower).
14. **Git.** Work on your branch `m<N>/<phase>-<topic>`, small conventional commits
    (`m2(recourse): monotone lever search`), never force-push, never commit to `main`, rebase on `main`
    before asking for a PR. No notebooks.
15. **Be quota-frugal.** Read each file once, make targeted diffs instead of rewriting files, and stop to
    report after each numbered task instead of looping.

## Definition of done (per page and per module)
See docs/GATES.md. A module is done when: contract test passes, unit tests exist, `--smoke` stage is OK,
artifacts are written, claims are logged, and known limits are written in `docs/known_issues/<member>.md`.
