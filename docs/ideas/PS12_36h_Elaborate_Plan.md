# PS 12: 36-Hour, 4-Member Elaborate Build Plan
### Companion to `PS12_Winning_Blueprint.md`
**This file supersedes Section 4.3 (scope tiers), Section 7 (execution plan) and Section 8 (demo script) of the blueprint.** Everything else in the blueprint (audit, loopholes L1-L14, technical specs, Q&A, wording rules) still applies.

> With 36 hours and four people, the earlier "thin thread only" advice relaxes. We can build the full decision spine **plus** several extra features. The trade-off changes from *"what can we afford?"* to *"how do we stay integrated, polished and calm?"* The dangers now are integration debt, half-finished pages, and a tired team on demo day.

---

## 1. The Elaborate Scope

### 1.1 Product in one line
**A governed MSME lending cockpit:** every application gets a reason, a route to yes, a repayment plan that fits its cash flow, a fairness cost, a stress-tested loss, and an early-warning watch after disbursal.

### 1.2 Feature set (all in scope, with owners in Section 3)

| # | Feature | Tier | What the judge sees |
|---|---|---|---|
| F1 | Synthetic MSME generator (documented, calibrated, stochastic legacy policy) + reject inference scoreboard | Core | "Legacy vs Ours" at equal loss, with oracle comparison |
| F2 | Champion/challenger models, calibration, out-of-time, ablation (bureau vs alt-data vs both) | Core | Model Cockpit page |
| F3 | Reason codes + **counterfactual recourse** (3-4 verifiable levers) | Core | Borrower Decision page |
| F4 | **DSCR-matched repayment structuring** with conformal cash-flow bands | Core | Schedule sitting under the P10 band |
| F5 | **Priced fairness** (metrics, in-processing mitigation, frontier, proxy audit, recourse-equity gap) | Core | Fairness Studio |
| F6 | **Stress and contagion** (named historical replays, supplier-buyer graph, Monte Carlo, tornado) | Core | Stress page |
| F7 | **Governance layer** (model card, FREE-AI map, decision ledger, consent mock, override log) | Core | Governance page |
| F8 | **Policy Optimizer** (maximise expected profit under loss budget, sector caps, inclusion floor) | Extended | Sliders that reshape the approved portfolio |
| F9 | **Early-warning system** (discrete-time hazard on the monthly panel; watchlist; lead-time metric) | Extended | "We flag trouble N months early" |
| F10 | **Recourse journey simulator** (Meena acts on advice; PD path over 6 months) | Extended | Animated PD curve crossing the approval line |
| F11 | **Data-trust panel** (cross-source reconciliation: GST vs bank vs UPI; gaming flags; "Try to game it") | Extended | Attack toggles, flags light up |
| F12 | **Credit Appraisal Memo** export + **borrower letter** in English/Hindi/Tamil/Marathi | Extended | One-click documents |
| F13 | **Borrower Portal** view (Meena's own screen) | Extended | Third persona with plain-language path to yes |
| F14 | **External-validity slide** (same pipeline on one real public credit dataset) | Extended | Answers "is this real?" |
| F15 | **Analyst Copilot** (optional): natural-language Q&A over precomputed results only | Stretch | "Ask the portfolio a question" |
| F16 | **Story Mode**: scripted auto-play of the demo, plus a guided tour for judges exploring alone | Extended | Removes stage risk |

### 1.3 Pages (8), demo depth on five

| Page | Persona | Contains |
|---|---|---|
| 1. Portfolio Command Center | Risk Head | Scoreboard, routing table, economics panel (₹), Policy Optimizer |
| 2. Borrower Decision | Credit Officer | PD, reasons, recourse, structured schedule, live sliders, CAM export |
| 3. Borrower Portal | MSME owner | Plain-language reason, path to yes, journey simulator, multilingual letter |
| 4. Fairness Studio | Regulator / Risk Head | Metrics by group, frontier, proxy audit, recourse-equity gap |
| 5. Stress and Contagion | Risk Head | Named replays, contagion graph, Monte Carlo, tornado, mitigation lever |
| 6. Early Warning | Risk Head | Watchlist, hazard curves, lead-time metric, suggested pre-emptive restructures |
| 7. Model Cockpit | Data Science | ROC/KS, calibration, ablation, thin-file view, PSI, champion vs challenger, sensitivity grid, external validity |
| 8. Governance and Trust | Regulator | FREE-AI map, decision ledger, consent artefact, data-trust panel, gaming lab, model card |

**Rule:** build breadth, demo depth. A judge who explores freely must find every page polished, but the pitch only walks through the five that carry the story.

### 1.4 New feature specs (beyond the blueprint)

**F8 Policy Optimizer**
- Decision variable: approve/decline (relaxed to 0-1) per applicant, plus optional structured-repayment flag.
- Objective: maximise Σ x_i × (expected margin_i − EL_i − cost_i).
- Constraints: total exposure ≤ budget; total EL ≤ loss cap; sector share ≤ cap; approval share of women-led / rural / new-to-credit ≥ inclusion floor.
- Solve with an LP relaxation (`scipy.optimize.linprog` or PuLP) and round; compare with the greedy threshold rule.
- UI: four sliders (loss cap, budget, sector cap, inclusion floor) → approved list, expected profit, EL, fairness gap. Shows the **price of inclusion in ₹**.

**F9 Early-warning system**
- Discrete-time hazard model (LightGBM) on the monthly panel using lagged and rolling features (3-month change in inflows, filing delays, balance drop, bounce count).
- Outputs: monthly default hazard per borrower, ranked watchlist, and a suggested action (call, restructure, reduce limit).
- Metrics: time-dependent AUC or lift at top decile, and **median lead time** (months of warning before default). Evaluated out of time.

**F10 Recourse journey simulator**
- Take a rejected borrower, apply the recommended levers gradually over six months, regenerate the affected panel features, re-score monthly.
- Show the PD curve and the month it crosses the approval threshold. Repeat for a group (women-led vs others) to show **time-to-approval equity**.

**F11 Data-trust panel**
- Reconciliation ratios: GST-reported turnover vs bank credits vs UPI inflow; flag inconsistent firms.
- Cycle detection on the UPI graph (NetworkX); pre-application balance-spike z-score.
- "Try to game it": toggles for circular transfers, window-dressing, invoice round-tripping; show flagged count and AUC before/after.
- Output a **data-confidence score** (0-100) shown next to each PD, so uncertainty is visible.

**F12 Documents**
- Credit Appraisal Memo (1-2 pages): borrower profile, PD and reasons, forecast and DSCR chart, structure, fairness note, model version, officer decision box.
- Borrower letter: template-driven (numbers and reasons injected from structured JSON), four languages; have a native speaker review the Hindi/Tamil/Marathi text.

**F14 External validity**
- Pick one real public credit-default dataset (for example a well-known consumer or firm-level default dataset; check licence and availability). Run the same champion/challenger, calibration and fairness code.
- Show only method metrics (AUC, KS, calibration). Caption: "Same pipeline, real data, no synthetic assumptions."

**F15 Analyst Copilot (stretch, only after the feature freeze is safe)**
- An LLM that answers **only** from precomputed JSON via a small set of tools (`get_metric`, `get_segment_loss`, `get_scenario_result`). No free-form numbers; numbers are validated against the tool output before display. Temperature 0.
- If it is not rock solid by hour 28, cut it without regret.

**F16 Story Mode**
- A "Play demo" button navigates the app through Meena's flow with prefilled states and timed callouts, so the demo survives a shaky network and a nervous presenter. A guided tour (5 steps) helps judges exploring alone.

---

## 2. Architecture and the Team Contract

### 2.1 Repo layout

```
ps12/
├── core/                    # pure Python "SDK" used by the UI (no Streamlit imports)
│   ├── generator.py         # F1
│   ├── legacy_policy.py
│   ├── features.py          # feature_spec loader, derived-feature recompute
│   ├── models.py            # champion, challenger, calibration, inference
│   ├── explain.py           # SHAP wrappers, reason-code templating
│   ├── recourse.py          # F3
│   ├── forecast.py          # quantile + conformal
│   ├── structuring.py       # DSCR schedule optimizer
│   ├── fairness.py          # metrics, mitigation, frontier, proxy audit
│   ├── stress.py            # shocks, contagion, Monte Carlo
│   ├── optimizer.py         # F8
│   ├── early_warning.py     # F9
│   ├── trust.py             # F11 reconciliation, cycles, gaming
│   ├── documents.py         # F12 CAM + letters
│   └── governance.py        # model card, ledger, consent mock
├── data/                    # borrowers.parquet, panel.parquet, graph.parquet
├── models/                  # champion.pkl, challenger.pkl, calibrator.pkl, hazard.pkl
├── artifacts/               # metrics.json, scoreboard.json, frontier.json, stress_*.json, shap.parquet ...
├── app/                     # Streamlit pages + components + theme
├── tests/                   # smoke tests, metric unit tests, AppTest page tests
├── configs/                 # generator configs (3x3 grid), scenario definitions
├── docs/                    # data statement, model card, claims register, assumptions
├── run_all.py               # regenerates data → models → artifacts
└── README.md
```

### 2.2 Function contracts (agree in hour 0, freeze by hour 3)

| Function | Input | Output | Owner |
|---|---|---|---|
| `score(borrower)` | dict or row id | `{pd, pd_band, reasons[3], data_confidence}` | Member 1 |
| `recourse(borrower, levers)` | dict | `{actions[], new_pd, cost, months, valid_until_model}` | Member 2 |
| `structure(borrower, target_dscr)` | dict | `{schedule[], p10_band[], default_flat, default_matched}` | Member 2 |
| `fairness_report(policy)` | policy params | metrics by group, intersectional CIs | Member 2 |
| `optimize(policy_params)` | budget, caps, floor | approved ids, profit, EL, gaps | Member 2 |
| `stress(scenario, params)` | scenario id | EL, ES95, segment losses, first-fail, tornado | Member 3 |
| `watchlist(month)` | month | ranked borrowers, hazards, actions | Member 3 |
| `trust(borrower)` / `attack(kind)` | dict / attack id | confidence, flags / before-after metrics | Member 3 |
| `make_cam(borrower)` / `make_letter(borrower, lang)` | dict | HTML/PDF bytes | Member 4 (with Member 3) |

**Contract rules**
- The UI calls only these functions and reads only `artifacts/`.
- Nothing heavy runs in the UI; SHAP, Monte Carlo, frontiers and the hazard model are precomputed by `run_all.py`.
- Every function has a docstring with input/output examples and a unit test with one known borrower (Meena, id `MSME-00001`).

### 2.3 Feature spec file (single source of truth)

`configs/feature_spec.json` lists, for each feature: name, type, unit, **mutability class** (immutable / verifiable / gameable), **monotone direction** for the challenger, plain-language label for reason codes, allowed range for recourse, derived-feature dependencies. Members 1, 2 and 4 all read it.

### 2.4 UI approach

- **Default: Streamlit multi-page + Plotly** with a custom theme (one typeface, one accent colour, INR formatting, consistent card components). Fastest route to a polished result.
- **Alternative:** FastAPI + React only if one teammate has shipped React dashboards before. Decide at **hour 2** and do not revisit.
- Graph views: PyVis or streamlit-agraph for the contagion graph, with a static Plotly fallback.
- Every chart carries a one-line "How to read this" caption for non-ML judges.

### 2.5 Working agreements

- Git: `main` is always runnable; short-lived feature branches; merge at least every 2 hours; no notebooks in `main` (export to modules).
- Pinned `requirements.txt`, fixed seeds, `python run_all.py` rebuilds everything in under ten minutes.
- One Slack/WhatsApp channel with a hard rule: post a message when a contract changes.
- A **claims register** (`docs/claims.md`): every number on a slide maps to a line in `artifacts/metrics.json`. Member 4 owns it; Member 1 signs off.

---

## 3. Team Roles

| Member | Role | Owns | Also supports |
|---|---|---|---|
| **M1** | Data and Modelling Lead | F1 generator, legacy policy, F2 models, calibration, reject inference, ablation, sensitivity grid, F14 external validity | Model Cockpit page, claims sign-off |
| **M2** | Decision Science Lead | F3 recourse, F4 forecasting + DSCR structuring, F5 fairness, F8 optimizer | Borrower Decision + Fairness pages (logic) |
| **M3** | Risk Systems and Platform Lead | F6 stress/contagion, F9 early warning, F11 trust panel, F7 governance backend, CI, deployment, tests | Stress, Early Warning, Governance pages (logic) |
| **M4** | Product, UI and Story Lead | Design system, all Streamlit pages, F12 documents, F13 portal, F16 story mode, deck, video, README, Q&A | Integrates everyone's outputs, runs rehearsals |

**Load balancing:** M4 has the widest surface. From hour 14 onward, M1 and M2 each take over one page's UI (Model Cockpit for M1; Fairness Studio for M2) so M4 can concentrate on Pages 1-3, story mode, and the deck. Whoever owns cloud deployment should stand up the public URL by hour 12.

---

## 4. Hour-by-Hour Plan (36 hours)

Times are elapsed hours. Two **gated** milestones matter most: the **walking skeleton** (Gate 3, hour 14) and the **feature freeze** (hour 26).

### Phase 0: Setup and contracts (H0-H3)

| All | Deliverable |
|---|---|
| Together (H0-H1) | Confirm submission format and deadline with organisers; agree scope, contracts (Section 2.2), repo layout, seeds; pick UI stack (decision at H2) |
| M1 | Generator v0 with entity table and monthly panel; configs for the 3×3 grid stubbed |
| M2 | `feature_spec.json` draft; stub functions returning realistic fake data so the UI can start |
| M3 | Repo, CI (lint + smoke test), deploy skeleton (hello-world at a public URL), scenario definitions file |
| M4 | Design system: theme, card, KPI tile, chart wrapper, page shell; Meena persona card |

**Gate 1 (H3):** contracts frozen; UI can render stubbed data from every function.

### Phase 1: Data and models (H3-H10)

| Member | Deliverable |
|---|---|
| M1 | Generator v1: latents, signals, hazard-based defaults with κ mix, bias mechanism, legacy policy with overrides, out-of-time split; champion (WoE logistic) and challenger (monotone LightGBM); calibration; metrics JSON; ablation |
| M2 | Reason-code templating; recourse v0 on the champion; quantile forecasting baseline |
| M3 | Stress engine v0 (input shocks, no graph yet); supplier-buyer graph generator; early-warning feature pipeline |
| M4 | Pages 2 and 7 layouts with stubs; Borrower Decision skeleton with sliders wired to `score()` |

**Gate 2 (H10):** real `score()` and `metrics.json` exist; deployed URL shows Page 2 with real Meena numbers.

### Phase 2: Decision layer (H10-H16)

| Member | Deliverable |
|---|---|
| M1 | Reject-inference (approved-only vs inferred vs oracle); scoreboard JSON (iso-loss, iso-approval); generator sensitivity grid running |
| M2 | Recourse on challenger with monotone constraints; conformal forecasts; DSCR structuring; fairness metrics v1 |
| M3 | Contagion propagation; named scenarios; Monte Carlo; hazard model v0; trust-panel reconciliation |
| M4 | Pages 1, 2, 5 wired to real functions; economics panel; routing table |

**Gate 3, walking skeleton (H14-H16):** Meena flows end-to-end (reject → reasons → recourse → structured loan → scoreboard → one shock) on the deployed URL. **If this is not true by H16, stop adding features and fix integration first.**

### Phase 3: Depth and extended features (H16-H26)

| Member | Deliverable |
|---|---|
| M1 | Real-data external validity (F14); PSI drift; champion/challenger panel; Model Cockpit page UI |
| M2 | Fairness in-processing + reweighing; frontier; proxy audit; recourse-equity gap; Policy Optimizer (F8); Fairness Studio UI |
| M3 | Early-warning watchlist and lead-time metric; gaming lab and data-confidence score; decision ledger; consent mock; tornado chart; Pages 5, 6, 8 logic |
| M4 | Recourse journey (F10); Borrower Portal (F13); CAM and letters (F12) with multilingual review; Page 3, Page 1 polish; story mode script |

**Sleep plan (see Section 6):** first shift sleeps around H14-H19; second around H20-H25 (staggered so two people are always awake and integration never stalls).

### Feature freeze (H26)

No new features after this point. Only bug fixes, copy, performance and polish.

### Phase 4: Hardening and story (H26-H32)

| Member | Deliverable |
|---|---|
| M1 | Verify every metric; write `docs/data_statement.md`, model card; check calibration/OOT claims; final numbers into `metrics.json` |
| M2 | Fairness wording review; edge-case testing of recourse and structuring on 50 random borrowers; performance profiling |
| M3 | Load and failure testing (cold start, refresh mid-demo); smoke tests on every page (Streamlit `AppTest`); backup local build; monitor deploy |
| M4 | Deck, README with architecture diagram, story mode final, guided tour, claims register, demo video first take |

### Phase 5: Rehearsal and submission (H32-H36)

| Time | Activity |
|---|---|
| H32-H33 | Full rehearsal 1 (timed); teammate plays hostile judge using the blueprint's Q&A table |
| H33-H34 | Fix everything rehearsal 1 exposed; record final backup video |
| H34-H35 | Rehearsal 2 and 3; test on a second device and a phone hotspot |
| H35-H36 | **Buffer.** Submit early; no code changes in the final 90 minutes except critical fixes |

### Cut rules if you fall behind (drop in this order)

1. F15 Analyst Copilot
2. F11 "Try to game it" toggles (keep the reconciliation ratios)
3. F10 Journey simulator (keep static recourse)
4. Languages: reduce from four to two (English plus one)
5. F9 Early warning UI (keep the metric slide)
6. F8 Policy Optimizer (keep the threshold-rule scoreboard)
7. Contagion graph animation (keep static graph and numbers)

**Never cut:** Borrower Decision, Legacy vs Ours scoreboard, fairness frontier, stress with named replays, governance page, external-validity slide, story mode.

---

## 5. Acceptance Criteria (Definition of Done per Page)

| Page | Done when |
|---|---|
| 1. Portfolio | Scoreboard shows Legacy / Approved-only / Ours with the iso-loss toggle; routing table with per-segment loss and approval share; ₹ economics panel with editable LGD, margin and ticket; optimizer sliders update in under 2 seconds |
| 2. Borrower Decision | Any of 20 test borrowers loads; sliders re-score in under 1 second; recourse shows three levers with cost and months; schedule chart shows instalments under the P10 band; CAM downloads |
| 3. Borrower Portal | Plain-language reason, path to yes, PD-over-time chart, letter in four languages, no jargon |
| 4. Fairness Studio | Two or more metrics by group with confidence intervals; frontier chart; policy slider; proxy audit table; recourse-equity gap |
| 5. Stress | Four named replays plus custom; EL, ES95, first-failing segment, tornado; contagion view; one mitigation lever with ₹ saved |
| 6. Early Warning | Watchlist ranks by hazard; lead-time metric shown with out-of-time caption; action suggestion per borrower |
| 7. Model Cockpit | ROC/KS, calibration, ablation, thin-file view, PSI, champion vs challenger, sensitivity grid, external-validity panel |
| 8. Governance | FREE-AI map, ledger with at least 10 logged decisions, consent artefact, gaming lab before/after, model card download |

**Global:** deployed URL works on phone and laptop; cold start under 15 seconds; no page shows a stack trace after a hard refresh; every chart has a caption; INR formatting everywhere.

---

## 6. Endurance and Quality (36 hours is a marathon)

- **Two staggered sleep shifts** of 4-5 hours; nobody works unrested beyond hour ~20 without a break. Tired teams break integration.
- Pre-order food and water; assign a person to do a 10-minute "is main still green?" check every 3 hours.
- **Rule of two:** no change to the contract or `main` between H30 and H34 without a second person's approval.
- Keep a `KNOWN_ISSUES.md`; honest, visible limits beat hidden bugs.
- Run `python run_all.py` from a clean clone at H12, H24 and H32 to catch "works on my machine" failures.

---

## 7. Evidence Package (what makes claims credible)

| Evidence | Where shown | Defends against |
|---|---|---|
| Documented generator + calibration sources | Data statement, Model Cockpit | "Is this fake data?" |
| 3×3 sensitivity grid (κ × bias strength) | Model Cockpit | "You built the world you win in" |
| External-validity slide on real public data | Model Cockpit, deck | "Does the method work outside your assumptions?" |
| Approved-only vs inferred vs oracle | Portfolio scoreboard | "Selection bias?" |
| Ablation incl. thin-file AUC | Model Cockpit | "Why not just bureau scores?" |
| Interval coverage backtest | Borrower Decision | "Are forecasts reliable?" |
| Lead-time metric (out of time) | Early Warning | "Is early warning real?" |
| Gaming before/after | Governance | "Can it be gamed?" |
| Fairness frontier + CIs | Fairness Studio | "Which fairness, at what cost?" |
| Tornado of assumptions | Stress | "How sensitive is the tail loss?" |
| FREE-AI map + ledger + consent mock | Governance | "Can this be deployed responsibly?" |

---

## 8. Demo Versions

**Time is unknown, so prepare three cuts of the same story.** All start with Meena and end on governance.

### 8.1 Pitch cut (about 4 minutes; primary)

| Time | Screen | Beat |
|---|---|---|
| 0:00-0:25 | Title | Credit-gap range (₹25 lakh crore to ₹60 trillion depending on source; name it). "Viable firms are invisible to lenders. Meet Meena." |
| 0:25-1:05 | Borrower Decision | Legacy rejects (thin file). Ours: calibrated PD, three plain reasons, data-confidence score. |
| 1:05-1:45 | Same page | **Wow #1:** judge moves a slider, decision flips live. Recourse and months-to-yes. Schedule under P10 band. |
| 1:45-2:10 | Borrower Portal | **Wow #2:** Meena's Tamil letter and 6-month journey curve; CAM export for the officer. |
| 2:10-2:45 | Portfolio + Fairness | Scoreboard at equal loss; optimizer sliders show price of inclusion in ₹; frontier. |
| 2:45-3:20 | Stress | **Wow #3:** click "Demonetisation-style shock"; contagion; EL, tail loss, mitigation lever. |
| 3:20-3:40 | Early Warning | "After disbursal we flag trouble N months early" (lead-time metric). |
| 3:40-4:00 | Governance + close | FREE-AI map, ledger, gaming toggle (10 s), honest-limits line, closing line. |

### 8.2 Lightning cut (90 seconds)
Meena rejected → live slider flip → scoreboard at equal loss → shock replay → governance map → close.

### 8.3 Deep-dive cut (8 minutes, for judge table time)
Pitch cut plus Model Cockpit (ablation, sensitivity grid, external validity), Fairness proxy audit, Policy Optimizer scenarios, gaming lab, and Story Mode as backup.

**Presentation rules**
- One presenter drives; a second person pre-loads the next screen and watches the clock.
- Use Story Mode if the network is unstable; keep the recorded video ready on a laptop and a phone.
- Pre-select three "safe" borrowers (Meena and two others) and the scenarios that render fastest.

**Closing line:**
"We did not build a better score. We built a lending decision that a borrower, a credit officer and a regulator can each trust, and we measured what it costs and where it breaks."

---

## 9. Deck (10 slides)

1. Problem: invisible MSMEs (cite the range and source)
2. Insight: predictions are not decisions; trust is the gap
3. Solution: the decision spine (one diagram)
4. Live product (screenshots of Borrower Decision + Portfolio)
5. Evidence: scoreboard, ablation, external validity, sensitivity grid
6. Fairness: frontier and the price of inclusion
7. Resilience: named replays, contagion, early warning lead time
8. Governance: FREE-AI map, ledger, consent, gaming lab
9. Impact: ₹ economics with stated assumptions; honest limits
10. Roadmap: pilot with a lender on consented data; add LGD modelling; challenger governance cycle

---

## 10. Extra Risks Created by the Bigger Scope

| Risk | Mitigation |
|---|---|
| Integration debt (four people, many modules) | Contracts in hour 0-3; walking skeleton by H16; merge every 2 hours |
| Half-finished pages | Definition of Done per page (Section 5); cut rules (Section 4) |
| Performance on stage | Precompute; caching; scoring function lightweight; Story Mode |
| Translation errors | Native-speaker review of Hindi/Tamil/Marathi letters; fixed templates, no free generation |
| Copilot hallucination | Tool-only answers, number validation, easy cut |
| Fatigue | Staggered sleep; rule of two after H30; buffer in H35-H36 |
| Feature creep after H26 | Hard freeze; new ideas go to the roadmap slide |
| Overclaiming | Wording rules in the blueprint (Section 12): "under our documented assumptions", "measured and mitigated", never "bias-free" or "RBI-compliant" |

---

## 11. First 60 Minutes Checklist

- [ ] Confirm submission format, deadline, live vs recorded pitch, and judging criteria with the organisers
- [ ] Agree roles (Section 3) and the UI stack decision time (hour 2)
- [ ] Create the repo with the layout in Section 2.1 and branch rules
- [ ] Write `feature_spec.json` and the function contracts, with Meena (`MSME-00001`) as the reference borrower
- [ ] Stand up a deployed hello-world URL
- [ ] Draft the claims register file so every number gets logged from the start
- [ ] Schedule sleep shifts and the H16, H26, H32 checkpoints
