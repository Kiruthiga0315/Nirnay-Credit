# PHASE 1 - Data and models (H3-H10) -> Gate 2
Goal: real `score()` and `artifacts/metrics.json` exist; deployed URL shows Page 2 with real Meena numbers.
Dependencies: M2 and M4 develop against stubs until M1's Gate-2 merge; do not wait, do not block.

---
## M1-P1A | Model: OPUS (Claude Opus 4.6 thinking) | Branch: m1/p1-generator-v1
````text
You are the coding agent for M1 on repo `ps12`. FIRST read once: AGENTS.md, docs/CONTRACTS.md, docs/ARTIFACTS.md, core/generator.py, configs/generator/grid.yaml,
configs/feature_spec.json, Blueprint Sections 3.3 (L2, L3, L5, L6), 5.2, 5.3 and Plan Section 4 Phase 1.
Branch: m1/p1-generator-v1. Edit ONLY: core/generator.py, core/legacy_policy.py, configs/generator/*, configs/personas/*, docs/data_statement.md, tests/test_generator.py, tests/test_legacy_policy.py,
docs/claims/m1.md, docs/known_issues/m1.md. After each task run ruff + pytest, commit `m1(generator): ...`, print status.

T1. Latents (hidden from models, stored ONLY in data/oracle.parquet): true repayment capacity, shock sensitivity, management quality, sector seasonality profile,
    and the timing-vs-solvency mix kappa (from grid.yaml axes). Observable signals stay noisy functions of latents.
T2. Default mechanism (12-month horizon): monthly hazard driven by cash shortfall (DSCR < 1 for k consecutive months = TIMING default) plus solvency shocks; kappa sets the timing share.
    Calibrate the overall default rate to a documented target from the config (record it; if you cite a public figure mark TODO(verify) - never invent citations).
T3. Bias mechanism (plausible, not cartoonish): women-led and rural firms have lower bureau coverage (thin-file) so legacy approves them less EVEN THOUGH true capacity is independent of gender given features.
    bias_strength scales the coverage gap. Thin-file share overall 30-40%.
T4. core/legacy_policy.py: STOCHASTIC legacy policy score = f(bureau_score, collateral_value_ratio) + noise, approve above cutoff, PLUS 5-10% manual overrides/exceptions (creates overlap so reject inference is identifiable).
    Outcomes are OBSERVED only for approved loans (data/observed_outcomes.parquet); oracle outcomes for everyone live in data/oracle.parquet and are never read by models.
T5. Out-of-time split columns (train months 1-24, test 25-36); `load_config(kappa, bias_strength)` finished; `--config kappa=low,bias_strength=strong` CLI works; all 9 grid configs generate in smoke mode.
T6. Update docs/data_statement.md with the mechanisms, parameters and honest limits. Tests: reproducibility; oracle never in borrowers/panel; thin-file share 0.30-0.40 and higher for women-led/rural;
    override share 0.05-0.10 and >0 approvals below cutoff; default rate differs sensibly across kappa (timing share measurable from oracle); Meena still exact.
Deliver a table of the realised statistics per config (default rate, thin-file share by group, approval rate by group, override share).
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| Files | `data/borrowers.parquet`, `panel.parquet`, `oracle.parquet`, `observed_outcomes.parquet`, `generator_meta.json` |
| Thin-file share | 30-40%, women-led and rural higher than others |
| Legacy overrides | 5-10% of decisions; approvals exist below the cutoff |
| Default rate | documented; single digits to low teens % is a plausible band; must state basis |
| Oracle | not referenced by any model code (`grep -r oracle core/models.py` empty) |
| Grid | 9 configs generate in smoke mode |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m1/p1-generator-v1. Run `python -m core.generator --smoke`, the 9 grid configs (`--config kappa=<k>,bias_strength=<b>`), `python -m pytest tests/test_generator.py tests/test_legacy_policy.py`, `ruff check .`.
Table Check | PASS/FAIL | Evidence: 1 only M1 files changed; 2 oracle data is written to data/oracle.parquet only and NOT joined into borrowers/panel; 3 print thin-file share overall and by owner_gender/location_class;
4 override share and count of approvals below cutoff; 5 default rate per kappa (should differ) and stated target; 6 out-of-time split columns exist (months 1-24 vs 25-36); 7 same seed twice -> same hashes;
8 Meena row unchanged; 9 docs/data_statement.md describes latents, default mechanism, bias mechanism, legacy policy and limits and contains no invented citations (search for URLs/years and list each for me to verify).
Red flags to report if present: default rate 0% or >30%, thin-file share outside 0.30-0.40, no overrides, models importing oracle. Verdict GO / FIX FIRST.
````

---
## M1-P1B | Model: PRO (Gemini 3.1 Pro High) | Branch: m1/p1-models
````text
You are the coding agent for M1 on repo `ps12`. FIRST read once: AGENTS.md, docs/CONTRACTS.md, core/models.py, core/features.py, configs/feature_spec.json, Blueprint Section 5.3.
Branch: m1/p1-models (from main after p1-generator-v1 is merged, or rebase on it). Edit ONLY: core/models.py, tests/test_models.py, docs/model_card.md, docs/claims/m1.md, docs/known_issues/m1.md.
If you need M2's reason-code function (core/explain.py) or M3's `trust`, call the PUBLIC functions with a graceful fallback (score() must still work if they are stubs).
After each task run ruff + pytest, commit `m1(models): ...`.

T1. Train on approved-only observed outcomes with the out-of-time split (train months 1-24, test 25-36). Champion: logistic regression on WoE-binned features (bin edges fitted on train only; missing bureau = its own bin).
    Never use protected attributes (owner_gender, location_class) as inputs.
T2. Challenger: LightGBM with monotone constraints taken from configs/feature_spec.json (monotone_pd). Isotonic or Platt calibration fitted on a held-out slice of TRAIN (not test).
T3. Metrics on the test months: AUC, Gini, KS, Brier, ECE, PSI (train vs test), expected profit at threshold (uses editable LGD from configs/scenarios.yaml lgd_default). Ablation: bureau-only vs alt-data-only vs both, overall and thin-file subset.
    Write artifacts via core.paths.write_metrics("models", {...}) with keys like `auc_champion_oot`, `auc_challenger_oot`, `ece_challenger`, `auc_thin_bureau_only`, `auc_thin_alt_data`; write models/champion.pkl, challenger.pkl, calibrator.pkl.
T4. Real `score(borrower)` honouring core/contracts.ScoreResult: calibrated PD from the challenger, pd_band, top-3 reasons via core.explain (fallback: generic text), data_confidence via core.trust.trust (fallback 80),
    model_version like "v1-<short hash of artifacts>" (must not start with "stub"). Also `score_batch(ids_or_df)` for other modules. score() < 0.2 s per borrower after a lazy model load.
T5. tests/test_models.py: leakage guard (no feature computed from months > train cutoff; oracle not imported), monotonicity check on a feature grid for every monotone feature, calibration ECE, protected-attribute invariance (changing owner_gender/location_class in the input dict does not change PD), Meena scores.
    Start docs/model_card.md (intended use as decision aid, data, models, metrics from metrics.json).
Deliver: metrics table + list of any red flags (suspiciously high AUC means leakage: investigate before reporting).
````

**Expected outputs (sanity bands, not targets)**
| Metric | Band / expectation |
|---|---|
| OOT AUC champion / challenger | roughly 0.65-0.85; challenger not worse than champion by more than about 0.01; AUC > 0.92 = suspect leakage |
| ECE (challenger, calibrated) | small (about < 0.03) |
| Ablation | both >= either alone; alt-data beats bureau-only on the thin-file subset (direction) |
| Monotonicity test | passes for every constrained feature |
| Protected attribute invariance | identical PD when gender/location changed |
| `score("MSME-00001")` | real PD, 3 reasons, version not starting with "stub" |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m1/p1-models (with generator merged). Run `python run_all.py --smoke --keep-going`, `python -m pytest tests/test_models.py`, `python -c "import core;print(core.score('MSME-00001'))"`, and print artifacts/metrics/models.json.
Table Check | PASS/FAIL | Evidence: 1 only M1 files; 2 train/test split is out-of-time (show code lines); 3 WoE bins fitted on train only; 4 calibration data disjoint from test; 5 protected attributes not in feature list; 6 monotone constraints read from feature_spec.json and monotonicity test passes;
7 report AUC/KS/Brier/ECE/PSI and flag AUC>0.92 as leakage suspect; 8 ablation table present incl. thin-file; 9 score() latency (time 20 calls); 10 model_version not "stub"; 11 no model code reads data/oracle.parquet; 12 claims logged in docs/claims/m1.md for every metric key.
Verdict GO / FIX FIRST + top 3 fixes.
````

---
## M2-P1 | Model: SONNET (Claude Sonnet 4.6 thinking) | Branch: m2/p1-explain-recourse-forecast
````text
You are the coding agent for M2 on repo `ps12`. FIRST read once: AGENTS.md, docs/CONTRACTS.md, core/features.py, core/explain.py, core/recourse.py, core/forecast.py, configs/feature_spec.json, Blueprint Sections 5.4, 5.5 and L4, L6.
Branch: m2/p1-explain-recourse-forecast. Edit ONLY: core/features.py, core/explain.py, core/recourse.py, core/forecast.py, configs/feature_spec.json, tests/test_explain.py, tests/test_recourse.py, tests/test_forecast.py, docs/claims/m2.md, docs/known_issues/m2.md.
Until M1's real models are merged (Gate 2, H10), build against a tiny model you fit yourself on `python -m core.generator --smoke` data inside your tests; then switch to `core.models` when it lands. After each task: ruff + pytest, commit `m2(...)`.

T1. core/explain.py: SHAP wrapper for the LightGBM challenger (TreeExplainer) and a WoE-contribution explainer for the champion; `reasons_for(borrower_row, model_bundle, k=3) -> list[Reason]` ranking by positive PD contribution,
    skipping features that are protected/uninformative, and rendering text from configs/feature_spec.json `reason_risk` templates (format with the borrower value). Precompute artifacts/shap.parquet for the test borrowers in build_artifacts.
T2. core/recourse.py v0 (champion or challenger, whichever is loadable): for the borrower, search only `verifiable` levers (feature_spec `recourse_levers_default`), grid/greedy on `step`, minimise total cost (cost_per_unit) subject to crossing the approval PD threshold;
    after every lever change call `features.recompute_derived`; re-score with the ACTUAL model; return the RecourseResult contract incl. valid_until_model = the scoring model version. Max 4 actions; if no feasible path, return the closest path with a flag in actions (keep contract keys).
T3. core/forecast.py baseline: monthly net cash available for debt service from the panel; LightGBM quantile models (alpha 0.1, 0.5, 0.9) with time-based split (train months 1-24, test 25-36); backtest raw interval coverage; write artifacts/forecast_bands.parquet and metrics via write_metrics("forecast", {...}).
T4. Tests: reasons never mention protected attributes; recourse only uses verifiable levers, new_pd < pd, monotone direction sensible (improving a lever never raises PD); forecast quantiles ordered P10 <= P50 <= P90.
Deliver: example output for Meena (reasons + recourse) and the raw coverage number.
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| Meena reasons | 3 plain-language sentences, no jargon, no protected attribute |
| Meena recourse | 2-4 verifiable levers, `new_pd` below approval threshold, `valid_until_model` = real version |
| Forecast quantiles | P10 <= P50 <= P90 for every row; raw coverage reported (may miss 80% nominal; conformal fixes it in Phase 2) |
| Files | `artifacts/shap.parquet`, `artifacts/forecast_bands.parquet`, `artifacts/metrics/forecast.json` |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m2/p1-explain-recourse-forecast. Run ruff, `python -m pytest tests/test_explain.py tests/test_recourse.py tests/test_forecast.py`, `python run_all.py --smoke --keep-going`, and print Meena's reasons + recourse.
Table Check | PASS/FAIL | Evidence: 1 only M2 files; 2 reasons come from feature_spec templates and never include owner_gender/location_class; 3 every recourse lever has mutability 'verifiable'; 4 derived features recomputed after each lever change (show code);
5 recourse re-scores with the real model, not a proxy formula; 6 new_pd < pd and reaching the threshold or flagged infeasible; 7 forecast uses a time-based split and quantiles are ordered; 8 raw coverage number reported;
9 no lever moves outside allowed_range; 10 claims logged. Verdict GO / FIX FIRST.
````

---
## M3-P1 | Model: PRO (Gemini 3.1 Pro High) | Branch: m3/p1-stress-graph-ew
````text
You are the coding agent for M3 on repo `ps12`. FIRST read once: AGENTS.md, docs/CONTRACTS.md, core/stress.py, core/early_warning.py, configs/scenarios.yaml, Blueprint Section 5.7, 36h Plan Section 1.4 (F9) and 4 Phase 1.
Branch: m3/p1-stress-graph-ew. Edit ONLY: core/stress.py, core/early_warning.py, core/trust.py, core/governance.py, configs/scenarios.yaml, tests/test_stress.py, tests/test_early_warning.py, run_all.py, docs/claims/m3.md, docs/known_issues/m3.md.
Use `core.models.score_batch` (M1) for re-scoring when available; fall back to the stub `score` until Gate 2. After each task: ruff + pytest, commit `m3(...)`.

T1. Stress engine v0 (input shocks, no graph): read scenarios from configs/scenarios.yaml; sample shock parameters from the stated ranges (seeded); apply to borrower inputs (revenue/receivable days/cost of debt/filing delay) using sector_sensitivity;
    recompute derived features; re-score; EL = PD x LGD x EAD (LGD editable from the yaml, EAD = requested_amount); portfolio ES95 by Monte Carlo (N runs from yaml) with a COMMON shock factor so defaults are correlated (document the assumption).
    stress(scenario, params) returns the contract StressResult; write artifacts/stress_<scenario>.json and metrics via write_metrics("stress", {...}); unknown scenario -> ValueError.
T2. Supplier-buyer graph generator: data/graph.parquet (src, dst, revenue_share) - sector-aware, heavy-tailed concentration, seeded, built from data/borrowers.parquet; NetworkX helpers for later contagion. Deterministic; smoke size ok.
T3. Early-warning feature pipeline: from data/panel.parquet build data/ew_features.parquet with lagged and rolling features (3-month change in inflows, filing delay trend, balance drop, cheque bounces), strictly using data up to month t (no lookahead), with a time-based split ready for Phase 2.
T4. Tests: baseline EL < EL under each shock for every named scenario; ES95 >= EL; runs are reproducible with the same seed; graph has no self loops and revenue_share per supplier <= 1; EW features never use future months (assert on synthetic panel).
Deliver: table of EL/ES95 per scenario (labelled illustrative).
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| `artifacts/stress_<scenario>.json` | 5 files (4 named + custom) |
| Each shock | EL(shock) > EL(baseline); ES95 >= EL |
| Same seed | identical numbers |
| `data/graph.parquet` | no self-loops, revenue_share in (0,1], per-supplier sum <= 1 |
| `data/ew_features.parquet` | no lookahead (tested) |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m3/p1-stress-graph-ew. Run ruff, `python -m pytest tests/test_stress.py tests/test_early_warning.py`, `python run_all.py --smoke --keep-going`.
Table Check | PASS/FAIL | Evidence: 1 only M3 files; 2 every scenario in scenarios.yaml runs and unknown raises ValueError; 3 print EL and ES95 for baseline and each scenario (EL must rise, ES95 >= EL); 4 Monte Carlo seeded and reproducible (run twice);
5 common shock factor documented in code/docstring; 6 graph checks (self loops, share sums); 7 EW features built with data <= month t only (show the code line and the test); 8 claims + parameter ranges labelled ILLUSTRATIVE, no invented citations. Verdict GO / FIX FIRST.
````

---
## M4-P1 | Model: SONNET (Claude Sonnet 4.6 thinking) | Branch: m4/p1-page2-cockpit
````text
You are the coding agent for M4 on repo `ps12`. FIRST read once: AGENTS.md, docs/CONTRACTS.md, app/components/*, app/pages/2_Borrower_Decision.py, 36h Plan Section 5 (Page 2 acceptance) and Blueprint Section 6.
Branch: m4/p1-page2-cockpit. Edit ONLY: app/Home.py, app/components/**, app/pages/1_Portfolio.py, app/pages/2_Borrower_Decision.py, app/pages/3_Borrower_Portal.py, core/documents.py, tests/test_documents.py, docs/claims/m4.md, docs/known_issues/m4.md.
(Page 7 Model Cockpit belongs to M1: do NOT edit it; if you need a component for it, add it to app/components/ and tell your human.) After each task: ruff + pytest, commit `m4(...)`.

T1. Borrower Decision skeleton -> real interactions using ONLY `core.score`, `core.recourse`, `core.structure`, `core.trust`: borrower picker (20 TEST_BORROWER_IDS, Meena default), PD gauge vs approval threshold, three reasons, data-confidence badge,
    recourse card (levers, cost, months, "valid until model <version>" stamp), schedule-vs-P10 chart with a target-DSCR slider (re-calls structure(); must feel instant).
T2. Live what-if sliders for the verifiable levers (receivable days, GST filing regularity, cheque bounces, invoice digitisation): on change call `core.score` on a modified copy of the borrower dict (use core.features.recompute_derived through the public API only if exported; otherwise just modify the lever values)
    and show PD and decision flip. Use st.cache_data for artifact loads; keep the re-score path < 1 s.
T3. Caching + robustness: cache artifact reads, wrap every panel in ui.safe_call, friendly empty states, no stack traces on hard refresh. Show the STUB banner while model_version starts with "stub".
T4. Wire deploy: confirm with M3 the public URL renders Page 2 (do not edit M3 files). Write two known issues you found in docs/known_issues/m4.md.
Deliver: list of components + which core calls each panel makes.
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| Page 2 | any of 20 borrowers loads; slider change updates PD in < 1 s; decision flips visibly for Meena when levers improve |
| Robustness | hard refresh shows no traceback |
| Gate 2 | with M1's models merged the banner disappears and Meena shows the real PD |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m4/p1-page2-cockpit. Run ruff, pytest (esp. page smoke), start the app and use Streamlit AppTest to load app/pages/2_Borrower_Decision.py for each of the 20 TEST_BORROWER_IDS, timing each run.
Table Check | PASS/FAIL | Evidence: 1 only M4 files; 2 all 20 borrowers render without exception; 3 median and max render time (<1 s target for slider re-run, <15 s cold); 4 app/ makes only calls to core.score/recourse/structure/trust (+paths/reference); 5 no heavy compute in app/;
6 every chart captioned; 7 recourse card shows valid_until_model; 8 STUB banner appears iff model_version starts with "stub"; 9 st.cache_data used for artifact reads. Verdict GO / FIX FIRST.
````

---
### GATE 2 (H10) - together
`main` has M1's real `score()` and `artifacts/metrics.json`; deployed URL shows Page 2 with real Meena numbers. If not: M1 gets help from M2, M4 fixes integration issues first.
