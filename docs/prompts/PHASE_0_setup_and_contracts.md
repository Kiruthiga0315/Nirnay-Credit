# PHASE 0 - Setup and contracts (H0-H3) -> Gate 1
Goal: contracts frozen, every function returns realistic stub data, all 8 pages render, CI green, hello-world URL live.
The scaffold already exists in the repo; these prompts finish it. Do the "First 60 minutes" checklist from
docs/ideas/PS12_36h_Elaborate_Plan.md Section 11 together (confirm submission format, deadline, live vs recorded).

---
## M1-P0 | Model: PRO (Gemini 3.1 Pro High) | Branch: m1/p0-generator-v0
````text
You are the coding agent for M1 (Data & Modelling Lead) on repo `ps12`.
FIRST read once: AGENTS.md, docs/OWNERSHIP.md, docs/CONTRACTS.md, docs/ARTIFACTS.md, configs/feature_spec.json,
configs/generator/grid.yaml, configs/personas/meena.json, and Blueprint Section 5.2 (docs/ideas/PS12_Winning_Blueprint.md).
Branch: m1/p0-generator-v0 (from latest main). You may edit ONLY: core/generator.py, core/legacy_policy.py,
configs/generator/*, configs/personas/*, docs/data_statement.md, tests/test_generator.py, docs/claims/m1.md,
docs/known_issues/m1.md. Never edit contracts/paths/reference/__init__. Other changes: request in docs/known_issues/m1.md.
After each task: run `ruff check . && python -m pytest`, commit as `m1(generator): ...`, print a 3-line status.

T1. Generator v0 in core/generator.py: entity table for N firms (default n_firms from grid.yaml; --smoke uses n_firms_smoke):
    sector, location_class (metro/urban/rural), udyam_category, vintage_months, owner_gender, requested_amount,
    supplier_concentration, customer_concentration. Monthly panel for 36 months with observable signals as noisy functions of a
    hidden latent `capacity`: revenue, upi_inflow, bank_inflow, avg_bank_balance, gst_turnover, gstr1_3b_mismatch,
    gst_filing_delay_days, receivable_days, utility_delay_days, cheque_bounces. Snapshot columns at application time must match the
    names in configs/feature_spec.json exactly (bureau_score may be NaN = thin file). Fully seeded (seed 42), vectorised (numpy/pandas).
T2. Inject configs/personas/meena.json EXACTLY as row MSME-00001 (all borrower-level fields), plus a plausible seasonal 36-month panel for her.
T3. CLI: `python -m core.generator --smoke` writes data/borrowers.parquet, data/panel.parquet, data/generator_meta.json (seed, config, row counts,
    file hashes). Implement `build_artifacts(smoke)` so `python run_all.py --stage generator --smoke` works. Full run must take < 3 minutes.
T4. Stub the 3x3 grid loader (kappa x bias_strength from grid.yaml): `load_config(kappa=..., bias_strength=...)`; no dynamics yet.
T5. tests/test_generator.py: reproducibility (two runs same hash), Meena row exact, columns superset of model features in feature_spec, no NaN except
    nullable features, row counts (firms x 36 for the panel). Draft docs/data_statement.md sections (what/why synthetic/limits); leave calibration
    sources as TODO(verify) - never invent citations.
Deliver: working CLI, tests green, short summary of column names produced. Do NOT implement default/hazard mechanics yet (Phase 1).
````

**Expected outputs (Gate-1 view)**
| Output | Sanity expectation |
|---|---|
| `python run_all.py --stage generator --smoke` | prints `OK generator`, < 1 min |
| `data/borrowers.parquet` | 2,000 rows (smoke); `MSME-00001` present with Meena's exact values |
| `data/panel.parquet` | 2,000 x 36 = 72,000 rows |
| `data/generator_meta.json` | seed=42, config, hashes |
| Same seed twice | identical hash |
| `pytest tests/test_generator.py` | green |

**VERIFY (paste in a new chat, model: FLASH)**
````text
You are an independent QA reviewer. Do NOT modify any tracked file (scratch in /tmp only). Checkout branch m1/p0-generator-v0.
Run: `python run_all.py --stage generator --smoke`; `python -m pytest tests/test_generator.py`; `ruff check .`; `git diff --stat main`.
Verify and report as a table (Check | PASS/FAIL | Evidence):
1 Only allowed files changed (core/generator.py, core/legacy_policy.py, configs/generator/*, configs/personas/*, docs/data_statement.md, tests/test_generator.py, docs/claims/m1.md, docs/known_issues/m1.md).
2 data/borrowers.parquet has 2000 rows; MSME-00001 fields equal configs/personas/meena.json.
3 data/panel.parquet has 72000 rows and 36 months per firm.
4 Every model_input feature in configs/feature_spec.json is a column (bureau_score NaN allowed).
5 Two runs with the same seed produce identical file hashes (run twice, compare generator_meta.json hashes).
6 No random call without a seed (grep for np.random. / random. usage).
7 Bureau missing share is between 0.30 and 0.40 and is higher for women-led and rural firms (print numbers) - only report, may not be implemented yet.
8 No generated files are tracked by git (`git ls-files data models artifacts`).
Verdict GO / FIX FIRST + top 3 fixes.
````

---
## M2-P0 | Model: SONNET (Claude Sonnet 4.6 thinking) | Branch: m2/p0-feature-spec
````text
You are the coding agent for M2 (Decision Science Lead) on repo `ps12`.
FIRST read once: AGENTS.md, docs/OWNERSHIP.md, docs/CONTRACTS.md, core/contracts.py, configs/feature_spec.json, core/features.py,
and Blueprint Sections 5.4 (recourse), 5.5 (DSCR), 5.6 (fairness) + 36h Plan Section 2.2-2.3.
Branch: m2/p0-feature-spec. You may edit ONLY: configs/feature_spec.json, core/features.py, core/explain.py, core/recourse.py, core/forecast.py,
core/structuring.py, core/fairness.py, core/optimizer.py, tests/test_features.py, tests/test_m2_stubs.py, docs/claims/m2.md, docs/known_issues/m2.md.
Never edit contracts/paths/reference/__init__. After each task: `ruff check . && python -m pytest`, commit `m2(...)`, 3-line status.

T1. Review configs/feature_spec.json (24 features). For each: confirm mutability class, monotone_pd direction (business sense), plain-language
    `reason_risk` and `advice` text, allowed_range and step for levers. Add for each verifiable lever: `cost_per_unit` (relative feasibility cost) and
    `months_per_unit` (time to move one step) as clearly-labelled ILLUSTRATIVE fields. Keep protected attributes model_input=false.
T2. core/features.py: add `validate_spec()` (raises on invalid class, missing label, gameable lever, protected model_input), `lever_config(name)`,
    and a complete `recompute_derived(row)` that recomputes every derived feature listed in `derived_from` (cash_conversion_days, inflow stability, etc. where inputs exist).
T3. Make the stubs in recourse/structuring/fairness/optimizer return REALISTIC but deterministic, borrower-dependent values (use core.reference.stable_unit and
    the borrower's fields) so UI developers see variety. Keep signatures and return keys identical to core/contracts.py; keep model_version "stub-..." semantics
    (recourse.valid_until_model must equal core.models.MODEL_VERSION). Meena must remain: PD 14% -> recourse new_pd < approval threshold.
T4. Tests: tests/test_features.py (validate_spec passes, recompute_derived on Meena, levers are verifiable & non-gameable), tests/test_m2_stubs.py (all M2
    functions on 20 TEST_BORROWER_IDS: keys match contracts, schedule<=P10/target_dscr in all but <=1 month, new_pd<pd).
T5. Write docs/known_issues/m2.md with any contract improvements you would propose (do NOT edit contracts).
Deliver: summary of changes to feature_spec.json and the list of default recourse levers.
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| `validate_spec()` | passes; raises on a deliberately broken spec in tests |
| Recourse levers | 3-4 verifiable features, none gameable/immutable |
| 20 stub borrowers | varied PDs, valid structure schedules |
| `pytest` | green (contract tests included) |

**VERIFY (FLASH)**
````text
You are an independent QA reviewer. Do NOT edit tracked files. Checkout m2/p0-feature-spec. Run `ruff check .`, `python -m pytest`, `git diff --stat main`.
Report a table Check | PASS/FAIL | Evidence:
1 Only M2-owned files changed. 2 core/contracts.py unchanged (`git diff main -- core/contracts.py` empty).
3 python -c "from core.features import validate_spec; validate_spec()" succeeds.
4 Every lever in core.features.levers() has mutability 'verifiable', cost_per_unit and months_per_unit, and none is 'gameable'.
5 owner_gender and location_class have model_input false and are absent from model_features().
6 For all 20 TEST_BORROWER_IDS: core.recourse(...)['new_pd'] < core.score(...)['pd'] when pd >= 0.10 (list exceptions), structure() satisfies schedule[i] <= p10_band[i]/target_dscr for all but at most one month.
7 Stub outputs differ across borrowers (not constants).
8 No banned wording (bias-free, 99% accurate, guaranteed approval, RBI-compliant).
Verdict GO / FIX FIRST + top 3 fixes.
````

---
## M3-P0 | Model: FLASH (switch to SONNET if CI fails twice) | Branch: m3/p0-platform
````text
You are the coding agent for M3 (Risk Systems & Platform Lead) on repo `ps12`.
FIRST read once: AGENTS.md, docs/OWNERSHIP.md, docs/GITHUB_SETUP.md, run_all.py, .github/workflows/ci.yml, configs/scenarios.yaml, and 36h Plan Sections 2.5, 6, 11.
Branch: m3/p0-platform. You may edit ONLY: run_all.py, Makefile, requirements*.txt, .github/**, scripts/**, configs/scenarios.yaml, core/stress.py, core/early_warning.py,
core/trust.py, core/governance.py, tests/test_pages_smoke.py, tests/test_m3_stubs.py, docs/DEPLOY.md, docs/claims/m3.md, docs/known_issues/m3.md, demo_snapshot/**.
Never edit contracts/paths/reference/__init__. After each task: `ruff check . && python -m pytest`, commit `m3(...)`, 3-line status.

T1. Verify run_all.py: `--smoke`, `--stage`, `--keep-going`, `--list` behave; add `--grid` flag that (for now) just prints the 9 grid configs from configs/generator/grid.yaml.
T2. CI: make sure .github/workflows/ci.yml job is named `ci` (branch protection depends on it), caches pip, and fails on lint/test/smoke errors. Add `.pre-commit-config.yaml` with ruff.
T3. requirements: ensure every package the blueprint stack needs is present and importable (lightgbm, shap, fairlearn, networkx, statsmodels, scipy, pyvis, plotly, streamlit, pyarrow, pyyaml).
    Write `scripts/check_env.py` that imports each and prints versions; document `pip freeze > requirements.lock` step in docs/DEPLOY.md.
T4. Make stubs in stress/early_warning/trust/governance realistic and deterministic per scenario/borrower (keep signatures + keys identical to core/contracts.py, keep "stub" semantics).
    Validate configs/scenarios.yaml loads (yaml) and that stress() accepts every scenario id in it; unknown id -> ValueError.
T5. tests/test_m3_stubs.py for all M3 functions; keep tests/test_pages_smoke.py green (all 8 pages + Home).
T6. Write docs/DEPLOY.md: step-by-step for Streamlit Community Cloud (repo -> app/Home.py, Python 3.11, requirements.txt), Hugging Face Spaces alternative,
    the local fallback command, and the `make snapshot` / manual snapshot steps. Mark items only a human can do (creating the app, secrets) as MANUAL.
Deliver: list of MANUAL steps for the human (GitHub protection, deploy URL creation).
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| CI on a test PR | job `ci` green |
| `python scripts/check_env.py` | all imports OK |
| `python run_all.py --list` | 15 stages |
| Unknown scenario | `ValueError` |
| Human step | hello-world URL live at Gate 1 (record it in docs/DEPLOY.md) |

**VERIFY (FLASH)**
````text
You are an independent QA reviewer. Do NOT edit tracked files. Checkout m3/p0-platform. Run `ruff check .`, `python -m pytest`, `python run_all.py --smoke --keep-going`, `python run_all.py --list`, `python scripts/check_env.py`.
Report Check | PASS/FAIL | Evidence:
1 Only M3-owned files changed. 2 CI job name is exactly `ci`. 3 --list shows 15 stages with owners. 4 check_env imports all packages.
5 stress() works for every scenario id in configs/scenarios.yaml and raises ValueError for 'nope'. 6 pytest includes and passes the 9 page smoke tests.
7 docs/DEPLOY.md has MANUAL markers and a local fallback command. 8 No secrets or .env committed (`git ls-files | grep -i -E "secret|\.env"`).
Verdict GO / FIX FIRST + top 3 fixes.
````

---
## M4-P0 | Model: PRO (Gemini 3.1 Pro High) | Branch: m4/p0-design-system
````text
You are the coding agent for M4 (Product, UI & Story Lead) on repo `ps12`.
FIRST read once: AGENTS.md, docs/OWNERSHIP.md, docs/CONTRACTS.md, app/components/*.py, app/pages/*.py, 36h Plan Sections 1.3, 2.4, 5 (acceptance criteria).
Branch: m4/p0-design-system. You may edit ONLY: app/Home.py, app/components/**, app/pages/1_Portfolio.py, app/pages/2_Borrower_Decision.py,
app/pages/3_Borrower_Portal.py, core/documents.py, README.md, docs/QA_PREP.md, docs/claims/m4.md, docs/known_issues/m4.md, tests/test_ui_format.py, tests/test_documents.py.
Other pages belong to M1/M2/M3: do not edit them; if the shared components need an addition for them, add it to app/components/ (you own it) and tell your human.
Never edit contracts/paths/reference/__init__. After each task: `ruff check . && python -m pytest`, commit `m4(...)`, 3-line status.

T1. Design system in app/components/: one typeface, one accent colour (already teal), spacing tokens, `card()` context manager, `kpi_row()`, `pd_gauge(pd, threshold)` (Plotly),
    `reason_list()`, `persona_card(borrower)` for Meena, `section(title, caption)` enforcing the "How to read this" caption, `download_button` helper, `inr()` kept as-is.
    Keep every existing helper name (API stability) and keep components free of business logic.
T2. Consistent page shell: sidebar branding, page header, STUB banner logic (banner when model_version starts with "stub"), global INR formatting, empty/error states through safe_call.
T3. Upgrade Home.py (Meena story card, status of artifacts, how to explore) and Pages 1-3 layouts using ONLY core.* calls. Page 2 must load any of the 20 TEST_BORROWER_IDS,
    show PD gauge, 3 reasons, recourse card, and the schedule-vs-P10 chart. Page 3 shows a plain-language path to yes and the letter download in 4 languages (stub content ok).
T4. core/documents.py: real HTML template structure for the Credit Appraisal Memo (borrower profile, PD + reasons, forecast/DSCR chart placeholder, structure, fairness note,
    model version, officer decision box) and the letter templates (en/hi/ta/mr) driven by a dict; non-English text marked "PENDING NATIVE REVIEW". No free generation.
T5. tests: tests/test_documents.py (bytes returned, contains borrower id, version stamp), keep tests/test_ui_format.py green. Rewrite README architecture section placeholder only.
Deliver: screenshots not needed; list components and their signatures.
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| `streamlit run app/Home.py` | Home + pages render, teal theme, STUB banners visible |
| Page 2 | 20 borrowers selectable; Meena default; chart caption present |
| CAM / letter | downloadable HTML with borrower id + model version |
| Tests | green |

**VERIFY (FLASH)**
````text
You are an independent QA reviewer. Do NOT edit tracked files. Checkout m4/p0-design-system. Run `ruff check .`, `python -m pytest`, then start `streamlit run app/Home.py --server.headless true` and fetch http://localhost:8501/_stcore/health.
Report Check | PASS/FAIL | Evidence:
1 Only M4-owned files changed. 2 All 9 AppTest smoke tests pass. 3 Every chart/table in pages 1-3 has a ui.caption/section caption (grep).
4 No page imports from core.<module> internals except via `core` (grep `from core\.` in app/ - only core.paths, core.reference, core.stress.SCENARIO_IDS, core.governance allowed) - list violations.
5 No heavy compute in app/ (grep for lightgbm, shap, sklearn, optimize loops). 6 make_cam/make_letter return HTML containing the id and model version; non-English letters carry the PENDING NATIVE REVIEW marker.
7 inr() unit tests present. 8 No banned wording.
Verdict GO / FIX FIRST + top 3 fixes.
````

---
### GATE 1 (H3) - all four together (5 minutes)
Merge the four P0 PRs. Then on fresh clone: `python run_all.py --smoke --keep-going && python -m pytest && streamlit run app/Home.py`.
Passes when: all 8 pages render on stubs, CI green, hello-world URL live, contracts frozen (announce "contracts frozen" in the chat).
