# PHASE 5 - Rehearsal and submission (H32-H36)
No new features. Submit early. No code changes in the final 90 minutes except critical fixes (rule of two).

---
## M1-P5 | Model: SONNET (Claude Sonnet 4.6 thinking) | Branch: m1/p5-hostile-judge
````text
You are the coding agent for M1 on repo `ps12` (FREEZE). FIRST read once: docs/ideas/PS12_Winning_Blueprint.md Section 11 and 12, docs/claims/*.md, artifacts/metrics.json, docs/data_statement.md.
Branch: m1/p5-hostile-judge. Edit ONLY: docs/HOSTILE_JUDGE.md, docs/claims/m1.md, docs/known_issues/m1.md.
T1. Write 30 hard, realistic judge questions across data validity, reject inference, leakage, calibration, fairness definitions, recourse causality, forecasting reliability, stress assumptions, regulation, deployment, ethics, and "why not deep learning".
    For each: a 20-second spoken answer grounded in a metrics.json key (cite the key) or an honest "we did not test that; here is what we would do". Never invent numbers; never claim compliance/bias-free.
T2. Mark the 5 questions we are most vulnerable on and add a "bridge sentence" for each. Format as a table: Question | Answer (<=60 words) | Evidence key | Risk (low/med/high).
T3. Cross-check every answer against docs/claims/*.md; list mismatches for the owners.
````

**Expected outputs / VERIFY**
| Output | Expected |
|---|---|
| `docs/HOSTILE_JUDGE.md` | 30 Q&A, each with an evidence key or an honesty statement; top-5 vulnerabilities flagged |

````text
QA reviewer, read-only. Read docs/HOSTILE_JUDGE.md and artifacts/metrics.json. Table Check | PASS/FAIL | Evidence: 1 exactly 30 questions; 2 every numeric statement matches metrics.json (sample 10); 3 no banned wording or compliance claims; 4 at least 5 flagged high-risk with bridge sentences; 5 answers <= 60 words. Verdict GO / FIX FIRST.
````

---
## M2-P5 | Model: FLASH | Branch: m2/p5-final-copy-audit
````text
You are the coding agent for M2 on repo `ps12` (FREEZE). Branch: m2/p5-final-copy-audit. Edit ONLY: docs/known_issues/m2.md and copy strings inside M2-owned files (no logic).
T1. Grep the whole repo (app/, core/, docs/, README) for: bias-free, unbiased, 99%, guaranteed, RBI-compliant, compliant, causal, "will increase". List each hit with file:line and the corrected wording; apply fixes only in M2-owned files, request others via known_issues.
T2. Check every fairness/recourse sentence carries its definition or the "decision aid" wording. T3. Produce a 1-page "fairness talking points" markdown (docs/FAIRNESS_TALKING_POINTS.md - allowed) with 5 sentences a presenter can say safely.
````

**Expected / VERIFY**
| Output | Expected |
|---|---|
| Banned-phrase grep | 0 hits |
| Talking points | 5 safe sentences |

````text
QA reviewer, read-only. Run the banned-phrase grep across the repo and read docs/FAIRNESS_TALKING_POINTS.md. Table Check | PASS/FAIL | Evidence: 1 zero banned hits; 2 talking points name their metric definitions; 3 no causal claims about recourse. Verdict GO / FIX FIRST.
````

---
## M3-P5 | Model: FLASH | Branch: m3/p5-release
````text
You are the coding agent for M3 on repo `ps12` (FREEZE). Branch: m3/p5-release. Edit ONLY: M3-owned files, docs/DEPLOY.md, docs/RELEASE_CHECKLIST.md, demo_snapshot/**.
T1. Write docs/RELEASE_CHECKLIST.md from Blueprint Section 13: repo public with README, deployed URL tested on a second device + network, backup video location, deck, metrics.json backs every number, three rehearsals done, format/deadline confirmed with organisers - with checkboxes and an owner per line.
T2. Final snapshot: full clean-clone run, `make snapshot` (or manual), commit demo_snapshot/, tag `v1.0` (only after rule-of-two approval), verify the deployed app reads the snapshot.
T3. Run the health check three times (H32, H34, H35) and log results in docs/known_issues/m3.md. Confirm cold start < 15 s on the deployed URL from mobile data.
````

**Expected / VERIFY**
| Output | Expected |
|---|---|
| Release checklist | every line has an owner, all ticked before submit |
| Tag / URL | `v1.0` tag; deployed app healthy |

````text
QA reviewer, read-only. Fresh clone at tag v1.0: run full `python run_all.py`, `python -m pytest`, open the deployed URL health endpoint, verify demo_snapshot/ matches a fresh build for 5 metric keys. Table Check | PASS/FAIL | Evidence: 1 clone-to-running < 10 min; 2 tests green; 3 deployed URL healthy; 4 snapshot metrics equal fresh metrics; 5 checklist fully ticked. Verdict GO / FIX FIRST.
````

---
## M4-P5 | Model: FLASH | Branch: m4/p5-rehearsal-kit
````text
You are the coding agent for M4 on repo `ps12` (FREEZE). Branch: m4/p5-rehearsal-kit. Edit ONLY: docs/REHEARSAL.md, docs/VIDEO_SCRIPT.md, docs/DECK_OUTLINE.md, README.md (copy only), docs/known_issues/m4.md.
T1. docs/REHEARSAL.md: run-of-show for 3 rehearsals (timer, roles: presenter, driver/next-screen pre-loader, hostile judge, note-taker), a stage checklist (laptop + phone + hotspot + recorded video on both, safe borrowers, fastest scenarios), what to say if the network fails (Story Mode), and a scoring sheet.
T2. Update the video script with any timing changes from rehearsal 1; add final subtitles text for the recorded backup video.
T3. Final README pass: live URL, video link, results table keys still valid (compare with artifacts/metrics.json).
````

**Expected / VERIFY**
| Output | Expected |
|---|---|
| Rehearsal kit | 3 rehearsals scheduled, timings recorded, backup video recorded and copied to two devices |

````text
QA reviewer, read-only. Read docs/REHEARSAL.md, docs/VIDEO_SCRIPT.md, README.md. Table Check | PASS/FAIL | Evidence: 1 roles and timer defined; 2 network-failure plan uses Story Mode + recorded video; 3 README URL/video placeholders filled; 4 README numbers still equal metrics.json. Verdict GO / FIX FIRST.
````

---
### SUBMIT (H35)
Confirm submission format and deadline with the organisers (the brochure date is 30 Sep 2026, and the listing says online), submit early, keep the video on two devices, freeze `main`.
