# PHASE 2 - Decision layer (H10-H16) -> Gate 3 (walking skeleton)
Goal: Meena flows end-to-end on the deployed URL: reject -> reasons -> recourse -> structured loan -> scoreboard -> one shock.
If not true at H16: stop adding features and fix integration.

---
## M1-P2 | Model: OPUS (Claude Opus 4.6 thinking) | Branch: m1/p2-reject-inference-grid
````text
You are the coding agent for M1 on repo `ps12`. FIRST read once: AGENTS.md, docs/ARTIFACTS.md, core/models.py, core/legacy_policy.py, Blueprint Sections 3.3 (L2, L3), 5.3 (reject inference), 9 (impact), 36h Plan Section 4 Phase 2 and 7 (evidence).
Branch: m1/p2-reject-inference-grid. Edit ONLY: core/models.py, core/generator.py, core/legacy_policy.py, configs/generator/*, tests/test_scoreboard.py, tests/test_grid.py, docs/data_statement.md, docs/claims/m1.md, docs/known_issues/m1.md.
Commit small: `m1(scoreboard): ...`. Run ruff + pytest after each task.

T1. Reject inference (augmentation or parcelling, your judgement; explain choice in a docstring). Train three models on the same features: (a) approved-only, (b) reject-inferred, (c) ORACLE trained with true outcomes for all firms
    (oracle used ONLY here for evaluation/reference, never in any production score path). Expect a MODEST gain; report honestly.
T2. artifacts/scoreboard.json with two views, both including Legacy / Approved-only / Ours (inferred) / Oracle: ISO-LOSS (approvals at the loss rate the legacy policy achieved) and ISO-APPROVAL (loss at the legacy approval rate);
    also extra approvals at equal loss, thin-file/women-led/rural breakdown, and expected profit using editable LGD/margin/ticket. Evaluate on the out-of-time test months, using oracle outcomes for the not-observed rejected firms.
T3. Sensitivity grid: run kappa (high/medium/low) x bias_strength (weak/medium/strong) end-to-end (generator -> legacy -> models -> scoreboard) in smoke mode (and full mode when asked); write artifacts/sensitivity_grid.json with, per cell,
    lift (approvals at equal loss), thin-file AUC lift, and whether the direction holds. `python run_all.py --grid` must call this (M3 owns run_all; if the flag is missing put a request in known_issues/m1.md and expose `core.models.run_grid(smoke)`).
T4. Tests: scoreboard invariants (oracle >= inferred >= approved-only in expectation is NOT assumed - assert only structural facts: iso-loss uses the same loss rate, counts consistent), grid has 9 cells, deterministic under seed.
Deliver: the scoreboard table and a one-paragraph plain statement of what the grid says (including where the lift shrinks).
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| `scoreboard.json` | Legacy / Approved-only / Ours / Oracle in both views; extra approvals at equal loss reported (may be small) |
| `sensitivity_grid.json` | 9 cells; direction of lift stated per cell; lift smaller when solvency dominates (kappa low) |
| Honesty | reject-inference gain modest; oracle sets the ceiling; no claim beyond the grid |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m1/p2-reject-inference-grid. Run ruff, pytest (tests/test_scoreboard.py tests/test_grid.py), `python run_all.py --smoke --keep-going`, then print artifacts/scoreboard.json and artifacts/sensitivity_grid.json.
Table Check | PASS/FAIL | Evidence: 1 only M1 files; 2 oracle data used only in evaluation and the oracle model (grep usages); 3 evaluation is on out-of-time months; 4 iso-loss and iso-approval both present and consistent (same loss/approval definition as legacy);
5 grid has 9 cells and each has lift + direction; 6 lift shrinks (but persists or not - report honestly) when solvency dominates; 7 results are deterministic (run twice); 8 every number has a claims row in docs/claims/m1.md; 9 wording: no "recovered X% of India's..." claims.
Verdict GO / FIX FIRST + top 3 fixes.
````

---
## M2-P2A | Model: OPUS (Claude Opus 4.6 thinking) | Branch: m2/p2-recourse-dscr
````text
You are the coding agent for M2 on repo `ps12`. FIRST read once: AGENTS.md, docs/CONTRACTS.md, core/recourse.py, core/structuring.py, core/forecast.py, core/models.py (public API only), Blueprint Sections 3.3 (L4, L6), 5.4, 5.5.
Branch: m2/p2-recourse-dscr. Edit ONLY: core/recourse.py, core/structuring.py, core/forecast.py, core/features.py, configs/feature_spec.json, tests/test_recourse.py, tests/test_structuring.py, tests/test_forecast.py, docs/claims/m2.md, docs/known_issues/m2.md.
Commit small `m2(...)`. ruff + pytest after each task.

T1. Recourse on the monotone challenger: levers limited to feature_spec `verifiable` features (3-4), search minimal-cost combination to cross the approval threshold, recompute derived features after every change, re-score with the real model, attach feasibility cost and months to achieve,
    stamp valid_until_model. Add `recourse_equity(group)` helper computing median cost-to-approve by group (women-led vs others, rural vs urban) for M2's fairness page later. Guarantee: improving a lever never raises PD (test on a grid).
T2. Split conformal on the quantile forecasts: calibrate on a held-out slice, produce P10/P50/P90 with conformal adjustment; backtest empirical coverage of the nominal 80% interval on the test months and by sector; write metrics forecast.coverage_p10_p90 and forecast.coverage_by_sector.
T3. DSCR structuring under P10: choose repayment schedule (or moratorium) so that P10 cash available >= target_dscr x instalment in ALL BUT AT MOST ONE month of the tenor; total instalments must repay principal + interest for the requested amount (state rate assumption in ASSUMPTIONS via known_issues if missing).
    Compare flat EMI vs matched schedule on SIMULATED default rate for the same borrowers using the generator's default mechanism (ask for a generator helper via known_issues/m2.md if needed; else simulate shortfalls from the forecast distribution) and report default_flat/default_matched; ALSO report the result under the solvency-heavy generator config and state the lift shrinks or persists honestly.
T4. Tests: schedule <= P10/target_dscr all but <=1 month for 50 random borrowers; sum(schedule) covers principal; recourse monotone; conformal coverage within +/-5pp of 80% on test months (if outside, report and investigate, do not tune).
Deliver: Meena recourse + structure outputs and the coverage number.
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| Recourse | <= 4 verifiable levers, new_pd < approval threshold or flagged infeasible, months and cost present |
| Conformal coverage | nominal 80%; empirical roughly 0.75-0.85 on test months |
| Structure | violations <= 1 month per schedule; matched default <= flat default (in the timing-heavy config); lift smaller in solvency-heavy config |
| Equity helper | median cost-to-approve by group available |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m2/p2-recourse-dscr. Run ruff, pytest (tests/test_recourse.py tests/test_structuring.py tests/test_forecast.py), `python run_all.py --smoke --keep-going`, print forecast metrics and Meena's recourse + structure.
Table Check | PASS/FAIL | Evidence: 1 only M2 files; 2 levers are verifiable only; 3 derived features recomputed and real model re-scored; 4 monotone test (improving lever never raises PD) passes; 5 conformal coverage on TEST months (report number, nominal 0.80, flag if outside 0.75-0.85);
6 for 50 random borrowers: months violating instalment <= P10/target_dscr never exceed 1; 7 principal repaid; 8 default_flat vs default_matched reported for both a timing-heavy and solvency-heavy config with honest wording; 9 claims logged. Verdict GO / FIX FIRST.
````

---
## M2-P2B | Model: PRO (Gemini 3.1 Pro High) | Branch: m2/p2-fairness-metrics
````text
You are the coding agent for M2 on repo `ps12`. FIRST read once: AGENTS.md, docs/CONTRACTS.md, core/fairness.py, Blueprint Sections 3.3 (L5), 5.6, and 36h Plan Section 4 Phase 2.
Branch: m2/p2-fairness-metrics. Edit ONLY: core/fairness.py, tests/test_fairness.py, app/pages/4_Fairness_Studio.py, docs/claims/m2.md, docs/known_issues/m2.md.
Commit `m2(fairness): ...`; ruff + pytest after each task.

T1. Metrics v1 (real, using core.models.score_batch on the test months and true outcomes where fairness definitions need them; document which outcome you use): adverse-impact (approval-rate) ratio, TPR gap (equal opportunity), calibration by group (ECE),
    for groups women_led, rural, new_to_credit (from feature_spec groups). Contract: fairness_report(policy) -> FairnessReport.
T2. Intersectional view (women_led x rural, women_led x new_to_credit) with bootstrap 95% confidence intervals (seeded, B configurable) and `small_n` flag when n < 200.
T3. Write artifacts/fairness_groups.json and metrics via write_metrics("fairness", {...}). Add a first version of the Fairness Studio page: group table, AIR and TPR-gap bars with CIs, plain-language summary text generated from the numbers ("measured under stated definitions"), captions. No mitigation yet (Phase 3).
T4. Tests: metrics on a hand-built toy example match hand-computed values; bootstrap seeded; small_n flag; wording test (no banned phrases).
Deliver: table of the measured gaps under the current legacy policy vs our policy.
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| `fairness_groups.json` | AIR, TPR gap, ECE for 3 groups + 2 intersections with CIs and small-n flags |
| Page 4 | renders real numbers with captions; summary text says "measured", never "bias-free" |
| Tests | toy-example metrics equal hand-computed values |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m2/p2-fairness-metrics. Run ruff, pytest tests/test_fairness.py, `python run_all.py --smoke --keep-going`, AppTest for app/pages/4_Fairness_Studio.py.
Table Check | PASS/FAIL | Evidence: 1 only M2 files; 2 toy test values verified by hand (recompute 1 example yourself); 3 metrics use out-of-time test data; 4 CIs from a seeded bootstrap; 5 small_n flagged; 6 page has captions and no banned wording; 7 protected attributes used only to compute group metrics, never as model input; 8 claims logged. Verdict GO / FIX FIRST.
````

---
## M3-P2A | Model: OPUS (Claude Opus 4.6 thinking) | Branch: m3/p2-contagion-stress
````text
You are the coding agent for M3 on repo `ps12`. FIRST read once: AGENTS.md, docs/CONTRACTS.md, core/stress.py, configs/scenarios.yaml, data/graph.parquet builder (your own code), Blueprint Sections 3.3 (L7), 5.7.
Branch: m3/p2-contagion-stress. Edit ONLY: core/stress.py, configs/scenarios.yaml, tests/test_stress.py, tests/test_contagion.py, docs/claims/m3.md, docs/known_issues/m3.md, app/pages/5_Stress_Contagion.py.
Commit `m3(stress): ...`; ruff + pytest after each task.

T1. Contagion propagation on the supplier-buyer graph: for supplier j, delta_receivable_days_j = sum_i w_ij * delay_i (w = revenue share, delay from buyer stress and the yaml pass_through range); revenue at j falls in proportion to buyer stress and revenue share; iterate a bounded number of rounds; re-score with the real model.
T2. Named replays (4) + custom: sample ranges (seeded), Monte Carlo bands (P5/P50/P95 of loss), EL, ES95, segment heatmap data (sector x size), first-failing segment (earliest month or highest loss share - define and document), tornado (one-at-a-time variation of each assumption range on ES95) written to artifacts/tornado.json.
T3. Mitigation lever: restructure the top 10% most stressed borrowers (use core.structure via the public API; fallback: reduce their PD by the stub recourse effect) and report loss saved in INR.
T4. Page 5 UI: scenario buttons (one-click replay), KPI tiles (EL, ES95, first failing segment), segment heatmap, tornado, contagion network view (PyVis or static Plotly fallback), mitigation panel with INR saved, captions, "illustrative parameters" label. Precompute everything; page loads artifacts only.
T5. Tests: with contagion ON, ES95 > ES95 with contagion OFF (same seed); tornado bars ordered; mitigation loss saved >= 0; reproducible.
Deliver: table of results per scenario with contagion on/off (labelled illustrative).
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| `stress_<scenario>.json` x5, `tornado.json` | present, seeded |
| Contagion effect | ES95 with contagion > without (same seed) |
| Mitigation | loss saved >= 0 in INR |
| Page 5 | one click replay < 2 s (precomputed); "illustrative" label visible |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m3/p2-contagion-stress. Run ruff, pytest (tests/test_stress.py tests/test_contagion.py), `python run_all.py --smoke --keep-going`, AppTest for pages/5_Stress_Contagion.py, time it.
Table Check | PASS/FAIL | Evidence: 1 only M3 files; 2 formula delta_receivable_days_j = sum_i w_ij*delay_i implemented (show lines); 3 ES95 with vs without contagion; 4 tornado file exists and is ordered; 5 first-failing-segment definition documented; 6 mitigation saved >= 0;
7 page reads artifacts only (no Monte Carlo in app/); 8 every scenario labelled illustrative and no unverified citations; 9 reproducibility (run twice). Verdict GO / FIX FIRST.
````

---
## M3-P2B | Model: PRO (Gemini 3.1 Pro High) | Branch: m3/p2-hazard-trust
````text
You are the coding agent for M3 on repo `ps12`. FIRST read once: AGENTS.md, docs/CONTRACTS.md, core/early_warning.py, core/trust.py, data/ew_features.parquet builder, 36h Plan Section 1.4 (F9, F11) and Section 4 Phase 2.
Branch: m3/p2-hazard-trust. Edit ONLY: core/early_warning.py, core/trust.py, tests/test_early_warning.py, tests/test_trust.py, docs/claims/m3.md, docs/known_issues/m3.md.
Commit `m3(ew): ...` / `m3(trust): ...`; ruff + pytest after each task.

T1. Hazard model v0: discrete-time hazard (LightGBM) on data/ew_features.parquet, time-based split (train up to month 24, evaluate 25-36), monthly default hazard per borrower; save models/hazard.pkl; `watchlist(month)` returns the contract WatchRow list (rank, hazard, action from simple rules: top decile + trend -> call/restructure/reduce_limit/monitor).
T2. Metrics: lift at top decile and median lead time (months of warning before default) out-of-time; write via write_metrics("early_warning", {...}). Report honestly if lead time is small.
T3. Trust reconciliation: ratios GST-reported turnover vs bank credits vs UPI inflow per firm; flag inconsistent firms (document thresholds); `trust(borrower)` returns data_confidence 0-100 (documented formula) + human-readable flags; write artifacts/trust.json.
T4. Tests: hazard evaluated strictly out-of-time; watchlist sorted by hazard; trust flags on a hand-built inconsistent firm; data_confidence monotone in inconsistency.
Deliver: lead-time and lift numbers + trust flag counts.
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| `models/hazard.pkl`, `artifacts/watchlist.parquet` | present |
| Metrics | top-decile lift > 1 and median lead time > 0 months, evaluated out-of-time (report as measured) |
| `trust(Meena)` | confidence 0-100 with readable flags |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m3/p2-hazard-trust. Run ruff, pytest (tests/test_early_warning.py tests/test_trust.py), `python run_all.py --smoke --keep-going`, print artifacts/metrics/early_warning.json.
Table Check | PASS/FAIL | Evidence: 1 only M3 files; 2 features use data <= t only; 3 evaluation months 25-36 only; 4 lead time defined in code + docstring; 5 watchlist sorted by hazard; 6 trust thresholds documented and confidence formula in docstring; 7 data_confidence in [0,100]; 8 claims logged. Verdict GO / FIX FIRST.
````

---
## M4-P2 | Model: PRO (Gemini 3.1 Pro High) | Branch: m4/p2-pages-1-5-wired
````text
You are the coding agent for M4 on repo `ps12`. FIRST read once: AGENTS.md, docs/CONTRACTS.md, app/components/*, pages 1-3, Blueprint Sections 4.4, 6, 9 and 36h Plan Section 5 (Page 1 acceptance) and 8.1.
Branch: m4/p2-pages-1-5-wired. Edit ONLY: app/Home.py, app/components/**, app/pages/1_Portfolio.py, app/pages/2_Borrower_Decision.py, app/pages/3_Borrower_Portal.py, core/documents.py, tests/test_documents.py, docs/claims/m4.md, docs/known_issues/m4.md.
Pages 4, 5, 6, 7, 8 belong to other members: consume their public functions/artifacts in your pages, never edit theirs. Commit `m4(...)`; ruff + pytest after each task.

T1. Page 1 Portfolio Command Center: Legacy vs Approved-only vs Ours vs Oracle scoreboard from artifacts/scoreboard.json with an ISO-LOSS / ISO-APPROVAL toggle (fall back to labelled stub if the artifact is missing), extra-approvals-at-equal-loss KPI, captions.
T2. Routing table (rule layer over score + DSCR feasibility + data_confidence): fast-track / manual review / structured repayment / decline-with-recourse, with per-segment loss and approval share. Rules live in ONE documented function in app/components (thresholds visible in the UI).
T3. Economics panel in INR: approvals x ticket x margin - EL - opex with editable LGD, margin, ticket size (Blueprint Section 9 formulas; ticket bands INR 2-25 lakh); assumptions shown on screen; nothing hard-coded without a label.
T4. Borrower Decision: add "Challenge this decision" button (writes to the decision ledger through core.governance's public helper if available, else shows a stub confirmation) and the CAM export button (core.make_cam).
T5. Integration: run the full Meena path on the deployed URL with M3 (reject -> reasons -> recourse -> structured loan -> scoreboard -> one shock on Page 5). Write findings to docs/known_issues/m4.md. Fix only in your own files.
Deliver: the Gate-3 checklist with PASS/FAIL per step.
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| Page 1 | scoreboard with toggle, routing table with per-segment loss/approval share, editable economics panel |
| Meena path | works end to end on the deployed URL (Gate 3) |
| CAM | downloads for any of the 20 borrowers |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m4/p2-pages-1-5-wired (with all Phase 2 branches merged into a scratch local branch). Run ruff, pytest, AppTest for pages 1-3, and walk the Meena path programmatically: score -> recourse -> structure -> optimize -> stress('demonetisation_style').
Table Check | PASS/FAIL | Evidence: 1 only M4 files; 2 scoreboard toggle works and reads artifacts/scoreboard.json; 3 routing rules in one documented function and thresholds visible; 4 economics panel: change LGD/margin/ticket and confirm profit changes (compute one example by hand);
5 INR formatting everywhere; 6 CAM downloads for 5 random borrowers; 7 no heavy compute in app/; 8 Gate 3 steps each PASS/FAIL. Verdict GO / FIX FIRST.
````

---
### GATE 3 (H14-H16) - together, on the DEPLOYED URL
Meena: rejected by legacy -> our PD + 3 reasons -> recourse -> structured loan under P10 -> scoreboard -> Demonetisation-style shock. All four watch one person do it live on a phone and a laptop.
If any step fails: stop new features; the owner of the failing step fixes it while others test other borrowers. Then sleep shift 1 (H14-H19) per docs/ideas 36h plan Section 6.
