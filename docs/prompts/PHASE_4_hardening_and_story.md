# PHASE 4 - Hardening and story (H26-H32)
Rule of two from H30: no change to contracts or `main` without a second person's approval.
Everything here is verification, docs and polish: no new features.

---
## M1-P4 | Model: SONNET (Claude Sonnet 4.6 thinking) | Branch: m1/p4-audit-docs
````text
You are the coding agent for M1 on repo `ps12` (FEATURE FREEZE is active: no new features). FIRST read once: AGENTS.md, docs/claims/*.md, artifacts/metrics.json, docs/data_statement.md, docs/model_card.md.
Branch: m1/p4-audit-docs. Edit ONLY: docs/data_statement.md, docs/model_card.md, docs/claims/m1.md, docs/known_issues/m1.md, tests/test_leakage.py, tests/test_claims.py, core/models.py, core/generator.py (bug fixes only).
Commit `m1(audit): ...`; ruff + pytest after each task.

T1. Leakage & validity audit as tests: no feature built from months beyond the train cutoff; calibration set disjoint from test; oracle never reached by any score path (static import check + runtime guard); protected attributes absent from model inputs; results identical across two seeded runs.
T2. Claims audit (tests/test_claims.py): for EVERY row in docs/claims/*.md the metrics key exists in artifacts/metrics.json and the stated value equals the current value (tolerance stated). Produce a list of stale/unbacked claims for the owners.
T3. Finalise docs/data_statement.md (generator, latents, mechanisms, calibration sources with each figure marked verified/TODO(verify), sensitivity grid, limits) and docs/model_card.md from metrics keys only. Regenerate the final artifacts with `python run_all.py` (full) and record commit hash + date in the claims file.
T4. Write the "external validity" and "sensitivity grid" plain-language paragraphs for the deck into docs/claims/m1.md (each sentence linked to a key).
Deliver: audit table (check, result) and the list of unbacked claims.
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| `pytest tests/test_leakage.py tests/test_claims.py` | green |
| Claims audit | 0 unbacked claims (or a written list for owners) |
| Full `python run_all.py` | < 10 min from a clean clone |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Fresh clone of main plus m1/p4-audit-docs; run `python run_all.py` (time it), `python -m pytest`, `ruff check .`.
Table Check | PASS/FAIL | Evidence: 1 full build time < 10 min; 2 tests/test_leakage.py and tests/test_claims.py pass; 3 pick 10 random claims from docs/claims/*.md and confirm key + value in artifacts/metrics.json; 4 data_statement lists every calibration figure as verified or TODO(verify), no invented citations; 5 model_card statements all backed by metrics keys; 6 no banned wording. Verdict GO / FIX FIRST.
````

---
## M2-P4 | Model: SONNET (Claude Sonnet 4.6 thinking) | Branch: m2/p4-edge-cases-wording
````text
You are the coding agent for M2 on repo `ps12` (FEATURE FREEZE active). FIRST read once: AGENTS.md, core/recourse.py, core/structuring.py, core/fairness.py, core/optimizer.py, app/pages/4_Fairness_Studio.py, Blueprint Section 12 (wording rules).
Branch: m2/p4-edge-cases-wording. Edit ONLY: M2-owned core files (bug fixes only), app/pages/4_Fairness_Studio.py (copy only), tests/test_edge_cases.py, docs/claims/m2.md, docs/known_issues/m2.md.
Commit `m2(hardening): ...`; ruff + pytest after each task.

T1. Property tests on 50 random borrowers + 5 extreme cases (zero balance, huge ticket, all levers at bounds, missing bureau, extreme seasonality): recourse never proposes gameable/immutable levers, never leaves allowed_range, new_pd < pd or flagged infeasible; schedules satisfy DSCR (all but <=1 month), repay principal, no negative instalments; optimizer constraints hold for 10 random policies.
T2. Performance profile: score + recourse + structure for a slider change must be < 1 s; profile and fix hot spots inside your modules (cache model loads, vectorise).
T3. Fairness wording review: list every fairness-related string in the app and docs and rewrite unsafe phrasing (bias-free, guaranteed, compliant, causal recourse) into the approved wording; every fairness claim carries its definition. Confirm recourse advice carries "decision aid, not a guarantee" + model version stamp.
T4. Fix any failures you find within your own files; log others in docs/known_issues/m2.md for the owner.
Deliver: list of bugs found/fixed and the timing table.
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| Edge-case tests | green; extremes handled without exceptions |
| Slider path | < 1 s |
| Wording | zero banned phrases; definitions attached to fairness claims |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m2/p4-edge-cases-wording. Run ruff, pytest tests/test_edge_cases.py, time 20 slider-style calls (score->recourse->structure), grep the repo for banned wording and for "causal".
Table Check | PASS/FAIL | Evidence: 1 only M2 files/allowed copy edits; 2 edge cases pass; 3 latency median/max; 4 grep results; 5 recourse text includes decision-aid disclaimer + version stamp; 6 every fairness statement names its metric definition; 7 claims logged. Verdict GO / FIX FIRST.
````

---
## M3-P4 | Model: FLASH (switch to SONNET if flaky) | Branch: m3/p4-reliability
````text
You are the coding agent for M3 on repo `ps12` (FEATURE FREEZE active). FIRST read once: AGENTS.md, docs/DEPLOY.md, tests/test_pages_smoke.py, run_all.py, 36h Plan Sections 6, 10.
Branch: m3/p4-reliability. Edit ONLY: M3-owned files (core/stress|early_warning|trust|governance bug fixes only), tests/**, run_all.py, Makefile, scripts/**, docs/DEPLOY.md, docs/known_issues/m3.md, demo_snapshot/**.
Commit `m3(reliability): ...`.

T1. Smoke tests: AppTest on all 8 pages + Home for the 3 safe borrowers and every scenario; add a test that a hard refresh (fresh AppTest) shows no exception and each page renders in < 15 s cold.
T2. Failure drills (as tests/scripts): missing artifacts folder -> pages show friendly states (not tracebacks); one corrupted JSON -> app still loads; network disabled -> Story Mode still plays.
T3. Backup build: `scripts/offline_demo.sh` (and a Windows .bat) that creates the venv, installs from requirements.lock, runs the app from demo_snapshot with no network; `make snapshot` refreshes demo_snapshot/ from a full run. Document in docs/DEPLOY.md, incl. how to run it on a laptop and a phone hotspot.
T4. CI: add a job step that runs `python run_all.py --smoke` and fails if metrics.json misses any claimed key from docs/claims/*.md (reuse M1's claims test; do not duplicate logic).
T5. Health-check script `scripts/health_check.py` for the 10-minute "is main still green?" check every 3 hours (pull main, run smoke tests, print a one-line status).
Deliver: reliability table (page, cold start s, warm s).
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| Cold start | each page < 15 s |
| Failure drills | friendly messages, no traces |
| Offline build | app runs from `demo_snapshot/` with the network off |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m3/p4-reliability. Run ruff, pytest, `python scripts/health_check.py`, then simulate: rename artifacts/ and open each page via AppTest; corrupt one JSON in a temp copy; run the offline script in dry-run mode if it has one.
Table Check | PASS/FAIL | Evidence: 1 only M3 files; 2 cold-start times per page; 3 missing-artifact drill: no exception on any page; 4 corrupted-JSON drill; 5 offline script exists for bash and Windows and docs explain it; 6 CI runs smoke + claims check; 7 health_check prints a one-line status. Verdict GO / FIX FIRST.
````

---
## M4-P4 | Model: PRO (Gemini 3.1 Pro High) | Branch: m4/p4-readme-deck-video
````text
You are the coding agent for M4 on repo `ps12` (FEATURE FREEZE active). FIRST read once: AGENTS.md, README.md, docs/claims/*.md, artifacts/metrics.json, 36h Plan Sections 8, 9 (deck), Blueprint Sections 10, 11, 13.
Branch: m4/p4-readme-deck-video. Edit ONLY: README.md, docs/QA_PREP.md, docs/claims/m4.md, docs/known_issues/m4.md, docs/DECK_OUTLINE.md, docs/VIDEO_SCRIPT.md, app/Home.py, app/components/** (copy/polish only).
Commit `m4(docs): ...`.

T1. README (final): problem, one-line thesis, architecture diagram (Mermaid), data statement summary + link, how to run (3 commands), results table pulled ONLY from artifacts/metrics.json keys (list keys next to each number), live URL, limitations (honest limits), team, license placeholder, credits.
T2. docs/DECK_OUTLINE.md: the 10 slides from 36h Plan Section 9, each with: title, the exact on-slide text, which screenshot/page to use, and the metrics.json key behind every number. Slides use ONLY numbers present in the claims register; credit-gap figures quoted as a RANGE with named sources marked "re-verify before use".
T3. docs/VIDEO_SCRIPT.md: the 4-minute pitch cut with timings, spoken words, screen actions, and the hero-number placeholders {key} to fill from metrics.json; plus 90-second and 8-minute cuts.
T4. Compile docs/claims/README.md index of all claim files; list any number in README/deck without a claims row (must be zero).
T5. Copy polish across app pages 1-3 + Home: every chart has a caption, no jargon on the portal, wording rules obeyed.
Deliver: the list of hero numbers with keys.
````

**Expected outputs**
| Output | Sanity expectation |
|---|---|
| README | runs from a fresh clone in 3 commands; every number traceable |
| Deck outline | 10 slides, each number keyed |
| Video script | 3 cuts, timings add up |

**VERIFY (FLASH)**
````text
QA reviewer, read-only. Checkout m4/p4-readme-deck-video. Follow README from a fresh clone (venv, install, smoke run, tests, app health). Check docs/DECK_OUTLINE.md and docs/VIDEO_SCRIPT.md.
Table Check | PASS/FAIL | Evidence: 1 README quick start works; 2 every number in README/deck/video maps to a key in artifacts/metrics.json and a claims row (sample 10); 3 credit-gap figures shown as a range with sources marked re-verify; 4 cut timings sum to ~4:00 / ~1:30 / ~8:00; 5 no banned wording; 6 limitations section present. Verdict GO / FIX FIRST.
````

---
### CHECKPOINT (H32) - together
Full clean-clone run `python run_all.py && python -m pytest`, deployed URL on a phone and a laptop, claims register complete, `KNOWN_ISSUES` visible and honest. Then Phase 5.
