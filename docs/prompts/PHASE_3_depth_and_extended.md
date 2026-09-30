# PHASE 3 - Depth and extended features (H16-H26) -> FEATURE FREEZE at H26
Sleep plan: staggered shifts (see 36h Plan Section 6); two people awake at all times so integration never stalls.
Cut order if behind: Copilot -> gaming toggles -> journey -> languages 4->2 -> EW UI -> optimizer -> contagion animation.

---
## M1-P3 | Model: PRO (Gemini 3.1 Pro High) | Branch: m1/p3-external-cockpit
````text
You are the coding agent for M1 on repo `ps12`. FIRST read once: AGENTS.md, docs/ARTIFACTS.md, core/models.py, core/external.py, app/pages/7_Model_Cockpit.py, Blueprint Sections 3.3 (L2), 5.3, 6 and 36h Plan 1.4 (F14), 5 (Page 7 acceptance), 7 (evidence).
Branch: m1/p3-external-cockpit. Edit ONLY: core/external.py, core/models.py, app/pages/7_Model_Cockpit.py, tests/test_external.py, tests/test_cockpit_artifacts.py, docs/model_card.md, docs/data_statement.md, docs/claims/m1.md, docs/known_issues/m1.md.
Commit `m1(...)`; ruff + pytest after each task. Report after each task.

T1. External validity (F14): propose 2-3 candidate real public credit-default datasets and list their licences as TODO(verify) in docs/known_issues/m1.md for the HUMAN to confirm and download manually into data/external/ (git-ignored; never commit raw data, never fake a download).
    core/external.py loads the file from data/external/, applies a minimal documented feature mapping, runs the SAME champion/challenger/calibration code paths on a time- or random-split as the dataset allows, and writes artifacts/external_validity.json (AUC, KS, ECE only) + write_metrics("external", {...}).
    If the dataset is missing, build_artifacts must skip gracefully and the page must show "external validity: dataset not loaded yet".
T2. Model Cockpit artifacts (precomputed in build_artifacts): ROC points, KS curve, calibration bins (reliability) for champion and challenger, ablation table (bureau-only / alt-data-only / both, overall + thin-file), PSI per feature (train vs test), champion-vs-challenger metrics, sensitivity-grid summary, external-validity panel.
T3. Page 7 (Model Cockpit) UI reading those artifacts only: ROC/KS, calibration plot, ablation chart with a thin-file toggle, PSI table with a traffic-light column, champion vs challenger panel, 3x3 sensitivity grid heatmap, external-validity card, captions ("How to read this") on every chart.
T4. Finalise docs/model_card.md sections that come from metrics (intended use, data, metrics, limits) using keys from artifacts/metrics.json only. Tests: artifacts schema (keys present), page renders with and without the external dataset.
Deliver: list of metric keys added to claims.
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| Artifacts | ROC, KS, calibration, ablation, PSI, grid summary JSON/parquet present |
| Page 7 | renders all panels; thin-file toggle changes ablation numbers; external card shows numbers or the "not loaded" message |
| External validity | metrics only, licence noted as TODO(verify) until a human confirms |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m1/p3-external-cockpit. Run ruff, pytest, `python run_all.py --smoke --keep-going`, AppTest for pages/7_Model_Cockpit.py (with and without data/external/).
Table Check | PASS/FAIL | Evidence: 1 only M1 files; 2 no raw external data tracked or downloaded automatically; 3 external run uses the same model code path; 4 page has ROC, KS, calibration, ablation (+thin-file toggle), PSI, champion vs challenger, grid heatmap, external card;
5 every chart has a caption; 6 numbers on page equal artifacts/metrics.json values (spot-check 5); 7 model_card contains only metrics-backed statements; 8 claims logged for every new key. Verdict GO / FIX FIRST.
````

---
## M2-P3A | Model: OPUS (Claude Opus 4.6 thinking) | Branch: m2/p3-fairness-mitigation
````text
You are the coding agent for M2 on repo `ps12`. FIRST read once: AGENTS.md, core/fairness.py, core/models.py (public API), Blueprint Sections 3.3 (L5), 5.6 and the Q&A rows on fairness (Section 11).
Branch: m2/p3-fairness-mitigation. Edit ONLY: core/fairness.py, core/recourse.py, tests/test_fairness_mitigation.py, docs/claims/m2.md, docs/known_issues/m2.md.
Commit `m2(fairness): ...`; ruff + pytest after each task.

T1. Mitigation WITHOUT the protected attribute at inference: reweighing and/or Fairlearn ExponentiatedGradient with a demographic-parity/equal-opportunity constraint during TRAINING (protected attribute used only in training/evaluation), producing a mitigated model whose predict path takes the same features as before.
    Prove it in a test: flipping owner_gender/location_class in the input does not change the mitigated PD.
T2. Group-aware thresholds ONLY as a labelled policy simulation ("regulator-mandated inclusion policy simulation"), never as the default decision path.
T3. Frontier: sweep the mitigation strength; for each point record fairness gap (AIR and TPR gap), expected profit (editable LGD/margin/ticket), approvals, and price of closing the gap in INR per point; write artifacts/frontier.json; `fairness_report(policy)` accepts {"mitigation": ..., "strength": ...} and returns metrics for that policy.
T4. Proxy audit: train a model to predict the protected attribute from the "neutral" model features; report accuracy/AUC and the top proxy features -> artifacts/proxy_audit.json. State the result honestly (a high score means proxies leak).
T5. Recourse-equity gap: use recourse_equity() to compute median cost-to-approve by group (women-led vs others, rural vs urban) and time-to-approval equity -> artifacts/fairness_groups.json (extend, do not overwrite other keys).
Deliver: frontier table (3 points) and the plain-language cost-of-fairness sentence in INR, wrapped in "under our documented assumptions".
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| `frontier.json` | >= 6 policy points; gap shrinks as strength rises while profit/approvals change (report the shape as measured) |
| Invariance test | passes (no protected attribute at inference) |
| `proxy_audit.json` | protected-attribute predictability + top proxy features |
| Wording | "measured and mitigated", never "bias-free" |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m2/p3-fairness-mitigation. Run ruff, pytest tests/test_fairness_mitigation.py, `python run_all.py --smoke --keep-going`; print artifacts/frontier.json summary, proxy_audit.json, fairness_groups.json.
Table Check | PASS/FAIL | Evidence: 1 only M2 files; 2 mitigated model's predict path excludes protected attributes (show the code + the invariance test); 3 group-aware thresholds only in a function/param labelled simulation; 4 frontier has >=6 points and each has gap, profit, approvals;
5 profit uses editable assumptions (not hard-coded); 6 proxy audit reports metric + top features; 7 recourse-equity computed for women-led vs others and rural vs urban; 8 grep for banned wording -> none; 9 claims logged. Verdict GO / FIX FIRST.
````

---
## M2-P3B | Model: SONNET (Claude Sonnet 4.6 thinking) | Branch: m2/p3-optimizer-page4
````text
You are the coding agent for M2 on repo `ps12`. FIRST read once: AGENTS.md, core/optimizer.py, core/fairness.py, app/pages/4_Fairness_Studio.py, 36h Plan 1.4 (F8), 5 (Page 4 acceptance), Blueprint 9.
Branch: m2/p3-optimizer-page4. Edit ONLY: core/optimizer.py, app/pages/4_Fairness_Studio.py, tests/test_optimizer.py, docs/claims/m2.md, docs/known_issues/m2.md.
Commit `m2(...)`; ruff + pytest after each task.

T1. Policy Optimizer (F8) using scipy.optimize.linprog (or PuLP only if already in requirements): variables x_i in [0,1]; maximise sum x_i*(expected margin_i - EL_i - cost_i); constraints: total exposure <= budget, total EL <= loss cap, sector share <= cap, approval share of women-led / rural / new-to-credit >= inclusion floor.
    Round the LP solution (document the rounding) and compare with the greedy threshold rule. `optimize(policy_params)` returns the OptimizeResult contract; precompute a grid of policies into artifacts (writes via write_metrics("optimizer", {...})) so sliders are instant; a live call must return in < 2 s.
T2. Price of inclusion in INR = profit(no floor) - profit(with floor) at the same loss cap; report by floor value.
T3. Fairness Studio page (page 4) complete: metrics by group with CIs, frontier chart with a policy slider (moves approvals/profit/gap), proxy audit table, recourse-equity gap, "simulation only" label on group-aware thresholds, plain-language cost-of-fairness sentence, captions.
    The optimizer sliders live on Page 1 (M4 owns it): expose optimize() only; do not edit page 1.
T4. Tests: constraints satisfied by returned solution; profit(no floor) >= profit(floor); greedy vs LP comparison; page smoke.
Deliver: two policy examples with INR numbers.
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| `optimize()` | constraints hold; live call < 2 s; profit never higher with a stricter floor |
| Page 4 | frontier + slider works; simulation label visible; INR price of inclusion shown |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m2/p3-optimizer-page4. Run ruff, pytest tests/test_optimizer.py, AppTest pages/4_Fairness_Studio.py, and time `core.optimize({...})` 5 times.
Table Check | PASS/FAIL | Evidence: 1 only M2 files; 2 verify constraints on the returned solution (exposure, EL, sector cap, inclusion floor) with your own calculation; 3 profit non-increasing as the floor rises; 4 rounding documented; 5 latency < 2 s; 6 page has frontier slider, proxy table, equity gap, captions, simulation label; 7 INR formatting; 8 claims logged. Verdict GO / FIX FIRST.
````

---
## M3-P3A | Model: PRO (Gemini 3.1 Pro High) | Branch: m3/p3-early-warning-page6
````text
You are the coding agent for M3 on repo `ps12`. FIRST read once: AGENTS.md, core/early_warning.py, app/pages/6_Early_Warning.py, run_all.py, 36h Plan 1.4 (F9), 5 (Page 6 acceptance).
Branch: m3/p3-early-warning-page6. Edit ONLY: core/early_warning.py, app/pages/6_Early_Warning.py, run_all.py, tests/test_early_warning.py, docs/claims/m3.md, docs/known_issues/m3.md.
Commit `m3(...)`; ruff + pytest after each task.

T1. Improve the hazard model (calibration of hazards, monotone constraints where sensible), time-dependent evaluation out-of-time; metrics: top-decile lift, median lead time, and lead time by segment. Suggested pre-emptive action per borrower (call / restructure / reduce_limit / monitor) with a documented rule table.
T2. For the top of the watchlist compute "estimated loss avoided" if the suggested restructure is applied (use core.structure via its public API) - clearly labelled illustrative.
T3. Page 6: watchlist ranked by hazard for a month selector (25-36), hazard curves for a selected borrower, lead-time metric card with the out-of-time caption, suggested actions, INR loss-avoided card, captions.
T4. Wire `python run_all.py --grid` to call core.models.run_grid(smoke) if it exists (print a clear message otherwise). Tests: watchlist stable ordering, no lookahead, page smoke.
Deliver: lead-time and lift numbers as measured.
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| Page 6 | month selector, watchlist, hazard curves, lead-time card with caption "evaluated out of time" |
| Metrics | lift and lead time as measured (no target) |
| `run_all --grid` | runs the sensitivity grid when M1's function exists |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m3/p3-early-warning-page6. Run ruff, pytest, AppTest pages/6_Early_Warning.py, `python run_all.py --grid --smoke` and print early_warning metrics.
Table Check | PASS/FAIL | Evidence: 1 only M3 files; 2 evaluation strictly out-of-time; 3 lead-time definition in code; 4 action rules documented in a table in code/docs; 5 loss-avoided card labelled illustrative and uses public core.structure; 6 page reads artifacts; 7 --grid works or prints a clear message; 8 claims logged. Verdict GO / FIX FIRST.
````

---
## M3-P3B | Model: SONNET (Claude Sonnet 4.6 thinking) | Branch: m3/p3-trust-governance-page8
````text
You are the coding agent for M3 on repo `ps12`. FIRST read once: AGENTS.md, core/trust.py, core/governance.py, app/pages/8_Governance.py, Blueprint Sections 5.8 (FREE-AI map), L8, L9, 36h Plan 1.4 (F11), 5 (Page 8 acceptance), 12 (wording rules).
Branch: m3/p3-trust-governance-page8. Edit ONLY: core/trust.py, core/governance.py, app/pages/8_Governance.py, tests/test_trust.py, tests/test_governance.py, docs/claims/m3.md, docs/known_issues/m3.md.
Commit `m3(...)`; ruff + pytest after each task.

T1. "Try to game it" lab (F11): three attacks applied to a copy of the data: circular UPI transfers, pre-application balance window-dressing, invoice round-tripping. Two detectors: NetworkX cycle detection on the UPI graph and balance-spike z-score (plus reconciliation flags from Phase 2).
    attack(kind) returns AttackResult (flagged before/after, AUC before/after); write artifacts/gaming_lab.json. Report honestly what is and is not caught.
T2. Data-confidence score 0-100 (documented formula, uses reconciliation + detector flags) surfaced by trust(borrower); keep the score() integration (M1 calls trust).
T3. Governance backend: append-only decision ledger artifacts/ledger.jsonl (decision id, timestamp, borrower id, model version, inputs hash, reasons, decision, officer override + reason); `log_decision(...)`, `ledger(n)`, human-override log, "challenge this decision" entry point; consent artefact (purpose, data fields, duration, minimisation note - MOCK, labelled as such, no real Account Aggregator integration);
    seed the ledger with >= 10 realistic decisions from the pipeline (not hand-typed).
T4. Page 8: FREE-AI map table (theme -> where we show it; wording "we map to advisory guidance; we do not claim compliance"; principles paraphrased, TODO(verify) exact wording against the RBI report), ledger with filters, consent artefact card, gaming-lab toggles with before/after, model card download (docs/model_card.md), captions.
T5. Tests: ledger append-only + hash stable; attack results change flagged counts; page smoke; banned-wording test still green.
Deliver: what the detectors catch vs miss.
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| Ledger | >= 10 logged decisions; append-only |
| Gaming lab | flagged count rises after attacks, AUC change reported honestly, limits stated |
| Page 8 | FREE-AI map, ledger, consent mock (labelled mock), model-card download |
| Wording | "map to / direction of", never "compliant" |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m3/p3-trust-governance-page8. Run ruff, pytest, AppTest pages/8_Governance.py, `python run_all.py --smoke --keep-going`, print artifacts/gaming_lab.json and the first 3 ledger lines.
Table Check | PASS/FAIL | Evidence: 1 only M3 files; 2 ledger has >= 10 rows generated by code, append-only (show code); 3 gaming lab: flagged_before < flagged_after for each attack; report AUC change; 4 consent artefact labelled MOCK; 5 FREE-AI page never says compliant/compliance-achieved (grep) and marks exact wording TODO(verify);
6 data_confidence formula documented and in [0,100]; 7 page has captions; 8 claims logged. Verdict GO / FIX FIRST.
````

---
## M4-P3A | Model: PRO (Gemini 3.1 Pro High) | Branch: m4/p3-documents-portal
````text
You are the coding agent for M4 on repo `ps12`. FIRST read once: AGENTS.md, core/documents.py, app/pages/3_Borrower_Portal.py, 36h Plan 1.4 (F12, F13), 5 (Page 3 acceptance), Blueprint 3.3 (L4, L14).
Branch: m4/p3-documents-portal. Edit ONLY: core/documents.py, app/pages/3_Borrower_Portal.py, app/pages/2_Borrower_Decision.py, app/components/**, tests/test_documents.py, docs/claims/m4.md, docs/known_issues/m4.md.
Commit `m4(...)`; ruff + pytest after each task.

T1. Credit Appraisal Memo (1-2 pages, printable HTML with print CSS): borrower profile, PD + top reasons, forecast + DSCR chart (inline SVG or base64 PNG from precomputed bands), structured schedule, fairness note (from fairness artifacts), data-confidence, model version + "valid until re-scored" stamp, officer decision box, generated timestamp. Numbers come from core.* calls / artifacts only.
T2. Borrower letters in English, Hindi, Tamil, Marathi: fixed templates, numbers and reasons injected from structured JSON (reason texts and lever names translated via a dictionary in the module), plain language, no jargon; every non-English letter carries a visible "PENDING NATIVE REVIEW" marker until a native speaker signs off (record sign-off in docs/known_issues/m4.md when the human tells you).
T3. Borrower Portal (page 3, Meena's own screen): plain-language decision, "your path to yes" (levers with months), her repayment schedule in simple words, language switcher, letter download, "challenge this decision" button, no ML jargon anywhere.
T4. Tests: documents contain id, model version, and every injected number; templates for 4 languages exist and non-English carry the marker; page smoke. Keep INR formatting.
Deliver: file names of templates and the review checklist for native speakers.
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| CAM | 1-2 printable pages with all listed sections and version stamp |
| Letters | 4 languages, template-driven, review marker on hi/ta/mr |
| Page 3 | jargon-free, language switch works, downloads work |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m4/p3-documents-portal. Run ruff, pytest tests/test_documents.py, AppTest pages/3_Borrower_Portal.py; generate CAM for 3 borrowers and letters in 4 languages for Meena into /tmp and inspect them.
Table Check | PASS/FAIL | Evidence: 1 only M4 files; 2 CAM includes profile, PD, reasons, DSCR chart, schedule, fairness note, model version, officer box; 3 every number in the letter equals core.* outputs (compare 5 numbers); 4 hi/ta/mr letters show PENDING NATIVE REVIEW; 5 no free-form generation (templates only);
6 portal contains no jargon terms (PD, DSCR, SHAP, AUC, Gini) - grep; 7 INR grouping correct; 8 no banned wording. Verdict GO / FIX FIRST.
````

---
## M4-P3B | Model: SONNET (Claude Sonnet 4.6 thinking) | Branch: m4/p3-journey-story
````text
You are the coding agent for M4 on repo `ps12`. FIRST read once: AGENTS.md, app/components/*, app/pages/2_Borrower_Decision.py, app/pages/3_Borrower_Portal.py, 36h Plan 1.4 (F10, F16), 8 (demo versions).
Branch: m4/p3-journey-story. Edit ONLY: app/Home.py, app/components/**, app/pages/1_Portfolio.py, app/pages/2_Borrower_Decision.py, app/pages/3_Borrower_Portal.py, tests/test_journey_story.py, docs/claims/m4.md, docs/known_issues/m4.md.
Commit `m4(...)`; ruff + pytest after each task.

T1. Recourse journey simulator (F10) in app/components/journey.py (light: 6 calls to core.score, no heavy compute): apply Meena's recommended levers gradually over 6 months (linear or S-curve, documented), recompute PD monthly via the public API, show the PD curve and the month it crosses the approval threshold; group comparison view (women-led vs others) only if M2's recourse_equity artifact exists.
T2. Page 1: add Policy Optimizer sliders (loss cap, budget, sector cap, inclusion floor) calling core.optimize (precomputed grid preferred), showing approved count, expected profit, EL, fairness gap and the price of inclusion in INR.
T3. Story Mode (F16): a "Play demo" control that walks through Meena's flow with prefilled state, timed callouts and next/previous buttons, following the 4-minute pitch cut in the 36h Plan Section 8.1 (script stored in app/components/story_script.json); plus a 5-step guided tour for judges exploring alone. It must run offline from precomputed artifacts.
T4. Pre-select three "safe" borrowers (Meena + two) and the fastest scenarios; expose them as one-click presets. Tests: journey PD non-increasing when levers improve; story script has valid page targets; page smoke.
Deliver: the story script table (time, page, callout).
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| Journey | 6-month PD curve, crossing month shown |
| Page 1 optimizer sliders | update in < 2 s |
| Story mode | plays the 4-minute cut offline; guided tour of 5 steps |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m4/p3-journey-story. Run ruff, pytest, AppTest pages 1-3, and simulate the story script step by step (each target page loads without exception).
Table Check | PASS/FAIL | Evidence: 1 only M4 files; 2 journey PD curve non-increasing for Meena and crossing month shown; 3 journey uses only public core.score (no models loaded in app/); 4 optimizer sliders respond < 2 s; 5 story script total time ~ 4 minutes and every step points to an existing page;
6 story mode works with the network disabled (only local artifacts); 7 three safe borrower presets exist; 8 no banned wording. Verdict GO / FIX FIRST.
````

---
### FEATURE FREEZE (H26) - together
Merge everything green. After this: bug fixes, copy, performance and polish only. New ideas go to the roadmap slide. Announce "FREEZE" in the chat and update the repo README status line.
