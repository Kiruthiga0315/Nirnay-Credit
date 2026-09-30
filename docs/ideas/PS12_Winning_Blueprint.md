# PS 12: Predictive Credit Risk Analytics for MSMEs
## Audit, Revised Strategy and Winning Blueprint
**Event:** Hackconquest Hackathon, Aether 2026 (TCET Mumbai) · **Date on brochure:** 30 Sept 2026 · **Prize pool:** ₹20,000

> Nobody can guarantee a win: judging is subjective and we do not know the other teams. What this document does is maximise every variable we control: scope that actually ships, claims that survive questioning, and a demo that is memorable in four minutes.

---

## 0. Executive Summary

| Item | Verdict |
|---|---|
| **PS 12 as a choice** | **8 / 10.** Strong impact story, room to differentiate, feasible with synthetic data. Main weakness: no public real MSME alt-data. |
| **Current plan (the .md), as written** | **6.5 / 10.** Concept is 9.5/10 (unusually deep). Feasibility is about 4/10: eight research-grade features cannot be built and polished in one hackathon window. |
| **Plan after the fixes below** | **8.5 to 9 / 10**, provided we follow the tiered scope and protect demo time. |

**The five moves that matter most**

1. **Cut to a "thin thread" that ships (Section 4).** Seven of the eight features get merged, shrunk, or demoted. The decision page (score → reason → recourse → structured loan) is the product.
2. **Fix the circular-validation problem (L2).** Add a real-data external-validity slide, run the generator under several assumptions, and calibrate parameters to public figures.
3. **Make governance the closer, not the afterthought.** RBI's FREE-AI framework (Aug 2025) gives us a regulator-language rubric to map every feature against.
4. **Add three cheap, high-wow items:** live what-if sliders on the borrower page, a one-click historical shock replay (demonetisation, GST rollout, COVID, 2022-23 rate cycle), and an auto-generated Credit Appraisal Memo.
5. **Engineer the demo like a product launch:** precomputed artifacts, sub-second interactions, a recorded backup video, and one hero scoreboard ("Legacy vs Ours").

---

## 1. Problem Statement Decoded

### 1.1 The statement, in plain terms

> Build an interactive dashboard that evaluates and visualises predictive credit-risk models for MSMEs using **alternative data** (not just credit scores), with **explainable ML, cash-flow forecasting, borrower segmentation, fairness/bias analysis, and scenario simulation**.

### 1.2 Hidden requirements (what judges silently score)

| # | Hidden requirement | What it means for us |
|---|---|---|
| 1 | "Evaluates and visualises models" | This is a **model-evaluation cockpit**, not just a scorer: ROC/KS, calibration, out-of-time results, champion vs challenger, drift. |
| 2 | "Instead of relying **solely** on traditional scores" | We must **prove** alt-data adds value: ablation of bureau-only vs alt-data-only vs both, especially on thin-file borrowers. |
| 3 | "Explainable" | Reason codes a credit officer and a borrower can read, not a SHAP beeswarm. |
| 4 | "Cash-flow forecasting" | Forecast must change a decision (loan structure), with uncertainty bands. |
| 5 | "Segmentation" | Segments must map to lender actions. |
| 6 | "Fairness and bias" | More than one metric, plus proxy checks, plus the cost of mitigation. |
| 7 | "Scenario-based simulations" | Shocks applied to borrower inputs and portfolio, with correlated failure, not a slider that multiplies PD. |
| 8 | "Interactive" | Judges must be able to touch it. |

### 1.3 Requirement-to-deliverable map (our definition of done)

| PS requirement | Minimum viable proof (Tier 0) | Upgrade that wins (Tier 1+) |
|---|---|---|
| Alt-data predictive models | Champion (WoE logistic) vs challenger (monotone LightGBM), out-of-time test, calibrated | Bureau-only vs alt-data ablation; reject-inference scoreboard |
| Explainable ML | Top-3 reason codes in plain language | Counterfactual recourse; borrower letter in English/Hindi/Tamil |
| Cash-flow forecasting | P10/P50/P90 monthly inflow forecast with backtested coverage | DSCR-matched repayment schedule; conformal intervals |
| Risk segmentation | 4 action segments in a routing table | Segment-level cost to underwrite and loss |
| Fairness and bias | Two metrics by group + one mitigation + frontier chart | Proxy audit; intersectional view; recourse-equity gap |
| Scenario simulation | 4 named shocks re-scoring borrower inputs; EL and 95% tail loss | Supplier-buyer contagion graph; Monte Carlo bands |
| Interactive dashboard | 6 Streamlit pages, cached | Live what-if sliders; Credit Appraisal Memo export |

### 1.4 Why this problem matters (context and evidence)

- India's MSME credit portfolio grew about 12.5% year on year to roughly ₹47.4 trillion as of June 2026 (CRIF High Mark), and the Udyam portal shows more than 6.2 crore registered enterprises as of early 2026.
- Credit-gap estimates vary widely by source: about ₹25 lakh crore as of March 2025 (Deloitte), about ₹30 lakh crore (industry estimates), and about ₹60 trillion in another September 2026 report. **Quote the range and name the source; never a single number.**
- The same Deloitte-based summary says only about 14% of MSMEs have formal credit access.
- NBFCs already hold roughly 45-54% of ₹2-25 lakh business loans and use GST, bank-statement and digital-payment signals. **Implication: "we use alt-data" is not a differentiator any more. Recourse, fairness, structuring and governance are.**
- Industry estimates put delayed payments owed to MSMEs at about ₹8 trillion, which supports cash-flow-matched repayment design.
- RBI's FREE-AI committee report (Aug 2025) sets out seven guiding principles, six pillars and 26 recommendations, including board-approved AI policy, consumer transparency with a way to challenge AI decisions, and data minimisation aligned to the DPDP Act. It is advisory as released, but signals where supervision is heading.

*(Full source list in Section 12. Re-check any number before putting it on a slide.)*

---

## 2. Audit of the PS Choice

### 2.1 Scorecard

| Criterion | Score /10 | Reasoning |
|---|---|---|
| Technical feasibility in hackathon time | 8 | Tabular ML and dashboards are well-tooled; risk is scope, not difficulty. |
| Data availability | 6 | No public real MSME alt-data. Synthetic data is unavoidable, so credibility depends on how we build and disclose it. |
| Differentiation headroom | 9 | Baseline submissions are XGBoost + SHAP + Prophet + K-means. Decision-oriented depth is rare. |
| Demo appeal | 7 | Credit risk is abstract; needs a persona and live interactivity to land. |
| Impact and relevance | 9 | Large, quantified credit gap; regulatory tailwinds (FREE-AI, Account Aggregator, ULI). |
| Skill fit (ML + cloud) | 9 | Uses ML, explainability and deployment skills that also work as a portfolio piece. |
| Crowding risk | 7 | Fraud PSs (04, 07) will absorb many ML teams, but expect a few other credit-risk dashboards. Unknown; plan as if at least three teams build "XGBoost + SHAP + charts". |
| **Overall** | **8 / 10** | **Viable and worth doing, if scope is disciplined.** |

### 2.2 Verdict

Go with PS 12. The PS rewards breadth, but most teams will deliver six disconnected tabs. Our edge is **depth on decisions**.

---

## 3. Audit of the Current Plan

### 3.1 What the plan gets right (keep these)

- The "decision spine" idea (predict → explain → recourse → structure → fairness → stress → govern) is a genuinely strong organising principle.
- Naming selection bias, temporal leakage, fairness-metric incompatibility, proxy discrimination and gaming shows real domain literacy.
- The generator with hidden ground truth is clever: it lets us measure what real data cannot.
- "Honest limits up front" and "never say bias-free" are exactly right.
- The Meena persona is a good narrative device.

### 3.2 Scorecard

| Dimension | Score /10 | Note |
|---|---|---|
| Originality and depth | 9.5 | Best part of the plan. |
| Coherence | 9 | One spine, consistent connections. |
| Feasibility in a hackathon window | **4** | Eight features, four role views, contagion graph, adversarial lab, governance panel. |
| Validity and credibility | 6.5 | Several headline claims are circular (see L2). |
| Demo readiness | 6 | Seven steps in about four minutes; no interactivity plan; no fallback. |
| Risk management | 7 | Risks are listed, but the cut order still leaves too much. |
| **Overall (as written)** | **6.5 / 10** | Brilliant essay, risky build. |

### 3.3 Loopholes and problems, with fixes

| ID | Severity | Problem | Fix |
|---|---|---|---|
| **L1** | Critical | **Scope vs time.** F1 to F8 are each mini research projects; the plan's own cut order still ships seven. Integration usually fails first. | Adopt the tiers in Section 4. Merge F5 into the portfolio page, shrink F7 to toggles, elevate F8. Freeze features at the 60% time mark. |
| **L2** | Critical | **Circular validation.** "Recovered X% of creditworthy borrowers", "PD falls from X to Y through restructuring", and fairness gaps are all functions of assumptions **we wrote into the generator**. A sharp judge will say "you designed a world where you win." | (a) Frame results as **method validation**, not India-level claims. (b) Run **at least three generator configurations** (for example different default-mechanism mix, bias strength, shock size) and show conclusions hold in direction. (c) Add an **external-validity slide**: run the same pipeline on one real public credit dataset (metrics only). (d) Calibrate base rates and shock sizes to public figures and cite them. |
| **L3** | High | **Reject inference is not identifiable if the legacy policy is deterministic.** If everyone below a cutoff is rejected, there is no overlap, so the data cannot say what rejected borrowers would do; any gain is assumption-driven. Literature also shows reject-inference gains are often modest. It is also hard to explain in 30 seconds. | Make the legacy policy **stochastic**: add noise plus about 5-10% manual overrides/exceptions, which creates overlap. Report three numbers: approved-only model, reject-inference model, oracle. Expect a modest lift and say so. On the slide, show one plain chart: "Legacy vs Ours at the same loss rate." |
| **L4** | High | **Recourse can propose impossible or inconsistent actions.** Features are linked (receivable days ↔ cash conversion ↔ inflow stability); generic counterfactual tools ignore that. Advice also expires when the model is retrained. | Use **monotonic constraints** in the challenger so directions always make sense. Limit actions to 3-4 verifiable levers. Recompute derived features after each change. Stamp advice with model version and "valid until re-scored". Always call it a *decision aid*, not a guarantee. |
| **L5** | High | **Fairness implementation risk.** Fairlearn's `ThresholdOptimizer` sets **group-specific thresholds**, which needs the protected attribute at decision time and is disparate treatment. Also, measured gaps depend on the bias we injected. | Lead with **in-processing/reweighing** (no attribute needed at inference), for example `ExponentiatedGradient` with a parity constraint. Show group-aware thresholds only as a *"regulator-mandated inclusion policy simulation"*. Add an **intersectional** view (women-led × rural) with confidence intervals, and flag small-n. Do not collect caste. |
| **L6** | Medium | **Cash-flow credibility.** Generated series have clean seasonality, so forecasts look artificially good; the "P10-P25 inflow" rule is ad hoc; the "PD drops" claim assumes defaults are largely timing-driven. | Use a **DSCR rule under P10 inflow** (bankers understand DSCR). Use **split conformal** intervals for coverage you can defend. In the generator, include a parameter for how much default is timing vs solvency and show the lift **shrinks but persists** when solvency dominates. |
| **L7** | Medium | **Contagion parameters are unanchored** (buyer-supplier graph is invented). | Use **named historical replays** (demonetisation Nov 2016, GST rollout Jul 2017, COVID lockdown Mar 2020, 2022-23 rate-hike cycle) with parameter *ranges*, Monte Carlo, and a tornado chart showing which assumption drives the result. Label as illustrative. |
| **L8** | Medium | **F7 (adversarial lab) is a separate build** and overlaps with the fraud PSs. | Shrink to a **"Try to game it" panel**: three attack toggles (circular UPI, pre-application balance window-dressing, invoice round-tripping) and two detectors (cycle detection with NetworkX; balance-spike z-score). Show before/after AUC and flagged count. |
| **L9** | Medium | **Governance treated as a footer.** The plan cites RBI generally but not FREE-AI. | Elevate it: FREE-AI principle → feature map, decision ledger, consent-artefact mock, human override log, model card. This is our **closing act**. |
| **L10** | High | **Demo density.** Seven steps in three to four minutes is about 30 seconds each; four role views are too many; live SHAP/Monte Carlo can lag or crash on stage. | Three wow moments, two role views (Credit Officer, Risk Head), everything **precomputed and cached**, interactions on a lightweight scoring function, plus a **recorded backup video**. |
| **L11** | Medium | **Impact is stated in ratios but not in rupees.** | Add an **economics panel**: approvals × ticket × margin − EL − opex, with sliders for LGD, margin and ticket size (state assumptions). Use ₹2-25 lakh ticket bands as the realistic range. |
| **L12** | Medium | **Missing basics:** no LGD/EAD assumption; no ablation proving alt-data value; no score for thin-file segment specifically. | Add EL = PD × LGD × EAD with stated LGD; add the ablation chart; report thin-file AUC separately. |
| **L13** | High | **No integration contract.** Typical failure: models done, UI not connected. | Define artifacts on day one: `borrowers.parquet`, `panel.parquet`, `model_champion.pkl`, `model_challenger.pkl`, `precomputed/*.json`. The UI reads only these files. |
| **L14** | Low | **Regulatory statements can go stale** (MSME classification thresholds, DPDP Rules, RBI digital-lending directions). | Quote only what we verified (FREE-AI, DPDP Act 2023 principles). Add "verify current version" to any regulatory number before the deck is final. |

---

## 4. Revised Strategy

### 4.1 Winning thesis

> **Every MSME loan decision (approve, structure, or decline) should come with a reason, a route to yes, a fairness cost, and a stress-tested loss number.**

**Pitch line (12 seconds):**
"Credit models tell lenders *whether*. We tell them *why*, *how to say yes*, *what it costs to be fair*, and *what breaks in a downturn*, in one governed workflow."

**Optional product name:** *RinSetu* (ऋण सेतु, "bridge for credit") or *Vishwas Credit Cockpit* (trust). Pick either; do not spend more than five minutes on it.

### 4.2 What changes from the current plan

| Original | Change | Why |
|---|---|---|
| F1 Generator + reject inference | **Keep, but stochastic legacy policy, documented, calibrated**; reject inference becomes a *scoreboard*, not a research thread | L2, L3 |
| F2 Recourse | **Keep as the hero feature**, constrained to 3-4 levers, monotone model | L4 |
| F3 Priced fairness | **Keep, simplified**: 2 metrics + reweighing/in-processing + frontier + proxy audit | L5 |
| F4 Cash-flow structuring | **Keep, upgraded to DSCR under P10 with conformal bands** | L6 |
| F5 Segmentation | **Merge** into a routing table on the portfolio page | Mostly a rule layer over scores |
| F6 Contagion | **Keep, with named historical replays** | L7 |
| F7 Adversarial lab | **Shrink** to a "Try to game it" panel | L8 |
| F8 Governance | **Elevate** to the closer, mapped to FREE-AI | L9 |
| (new) | Credit Appraisal Memo export | Real-world artefact bankers recognise |
| (new) | Borrower letter in English/Hindi/Tamil | FREE-AI consumer transparency; strong demo moment |
| (new) | Mock Account Aggregator consent screen | Shows deployability at low cost |
| (new) | External-validity slide on a real public dataset | Answers "is this real?" |
| (new) | Economics panel in ₹ | Ties model to profit |

### 4.3 Scope tiers

**Tier 0: must ship (the thin thread, about 60% of effort)**
1. Synthetic generator v1: about 20k firms × 24-36 months, seeded, documented, with a stochastic legacy policy and out-of-time split.
2. Models: WoE-logistic champion + monotone LightGBM challenger; calibration; AUC, KS, Brier; ablation (bureau-only / alt-data / both).
3. **Borrower Decision page:** calibrated PD, top-3 plain-language reasons, recourse (3 levers), structured repayment under DSCR, with live sliders.
4. **Legacy vs Ours scoreboard** (iso-loss and iso-approval views).
5. **Fairness frontier** with one mitigation and a plain-language summary.
6. **Stress page:** four named scenarios, EL and 95% tail loss, segment heatmap.
7. **Governance page:** model card, FREE-AI map, decision ledger.

**Tier 1: should ship (adds most of the wow)**
- Supplier-buyer contagion propagation with Monte Carlo bands.
- Action-mapped routing table (fast-track / manual review / structured repayment / decline with recourse).
- Credit Appraisal Memo export (HTML or PDF).
- Multilingual borrower letter (template-first).
- Mock Account Aggregator consent screen.
- Economics panel in ₹.
- External-validity slide (real public dataset).

**Tier 2: stretch (only if Tier 0 and 1 are stable)**
- "Try to game it" adversarial panel.
- Conformal interval polish and coverage chart.
- Auto challenger monitoring (PSI alerts).
- Proxy audit visual.

### 4.4 Feature scoring (impact vs effort)

| Feature | Wow in demo | Judge-credibility | Effort | Priority |
|---|---|---|---|---|
| Live what-if sliders on decision page | 10 | 7 | Low | **Tier 0** |
| Counterfactual recourse | 9 | 9 | Medium | **Tier 0** |
| Legacy vs Ours scoreboard | 8 | 9 | Low-Medium | **Tier 0** |
| DSCR-matched structuring | 8 | 9 | Medium | **Tier 0** |
| Fairness frontier | 7 | 9 | Medium | **Tier 0** |
| Named shock replay | 9 | 7 | Medium | **Tier 0/1** |
| Contagion graph | 8 | 7 | Medium-High | Tier 1 |
| Credit Appraisal Memo export | 8 | 8 | Low | Tier 1 |
| Borrower letter in 3 languages | 8 | 6 | Low | Tier 1 |
| FREE-AI governance map | 6 | 10 | Low | **Tier 0** |
| AA consent mock | 5 | 7 | Low | Tier 1 |
| Try to game it | 7 | 8 | Medium | Tier 2 |

### 4.5 What NOT to build

- No blockchain, no real Account Aggregator integration, no free-form chatbot.
- No more than six dashboard pages.
- No feature that cannot be explained in one sentence to a non-ML judge.
- No numbers on slides that are not produced by the code in the repo.

---

## 5. Technical Blueprint

### 5.1 Architecture

```
                 ┌──────────────────────────────┐
                 │ 1. Synthetic MSME generator  │  seeded, documented, calibrated
                 │  (latent capacity → signals) │
                 └──────────────┬───────────────┘
                                │ borrowers.parquet, panel.parquet
                 ┌──────────────▼───────────────┐
                 │ 2. Legacy policy (stochastic)│  bureau + collateral + overrides
                 └──────────────┬───────────────┘
                                │ observed outcomes (approved only)
        ┌───────────────────────▼────────────────────────┐
        │ 3. Models: WoE-logistic champion,              │
        │    monotone LightGBM challenger, calibration,  │
        │    reject inference, out-of-time test          │
        └──────┬──────────────┬──────────────┬───────────┘
               │              │              │
     ┌─────────▼───┐  ┌───────▼──────┐  ┌────▼────────────┐
     │ 4a. Reasons │  │ 4b. Cash-flow│  │ 4c. Fairness    │
     │  + Recourse │  │ quantiles +  │  │ metrics, proxy  │
     │             │  │ DSCR schedule│  │ audit, frontier │
     └─────────┬───┘  └───────┬──────┘  └────┬────────────┘
               └──────────────┼──────────────┘
                     ┌────────▼────────┐
                     │ 5. Stress engine│  input shocks + contagion + Monte Carlo
                     └────────┬────────┘
                     ┌────────▼────────┐
                     │ 6. Governance   │  model card, FREE-AI map, decision ledger
                     └────────┬────────┘
                     ┌────────▼────────┐
                     │ 7. Streamlit UI │  reads only precomputed artifacts
                     └─────────────────┘
```

### 5.2 Synthetic generator specification

**Entity table (per MSME):** sector (textile, food processing, auto components, retail trading, logistics, services), location class (metro / urban / rural), Udyam category, vintage, owner gender, size, supplier and customer concentration.

**Latents (hidden from models):** true repayment capacity, shock sensitivity, management quality, sector seasonality profile, timing-vs-solvency mix parameter κ.

**Monthly panel (observable signals, noisy functions of latents):** revenue, UPI and bank inflows, average bank balance, GST turnover reported, GSTR-1 vs GSTR-3B mismatch, GST filing delay, receivable days, utility payment delay, cheque bounces, supplier and buyer links.

**Default mechanism:** hazard model driven by cash shortfall (DSCR below 1 for k consecutive months) plus solvency shocks; κ controls the timing-vs-solvency mix.

**Legacy policy:** score = f(bureau score, collateral) + noise, with 30-40% thin-file (missing bureau) and about 5-10% manual overrides. Approve above cutoff.

**Bias mechanism (plausible, not cartoonish):** women-led and rural firms have lower bureau coverage (thin-file), so legacy approves them less **even though true capacity is independent of gender given features**. This lets us test whether alt-data reduces the gap and whether proxies leak.

**Calibration to reality:** anchor default rates, sector mix, ticket sizes and shock magnitudes to public figures (for example RBI or SIDBI-TransUnion CIBIL MSME reports, CRIF High Mark, and the ₹2-25 lakh ticket bands). Cite them in the README. Verify numbers before quoting.

**Sensitivity grid:** run at least three configs, for example (κ high / medium / low) × (bias weak / strong). Show the conclusion holds in direction.

### 5.3 Models and evaluation

| Element | Choice | Reason |
|---|---|---|
| Champion | Logistic regression on WoE-binned features | Bankers' standard; interpretable |
| Challenger | LightGBM with **monotonic constraints** | Accuracy plus sensible recourse and explanations |
| Calibration | Isotonic or Platt on a held-out slice | PD must be a real probability |
| Split | Out-of-time (train months 1-24, test 25-36) | Avoids leakage |
| Metrics | AUC, Gini, KS, Brier, calibration/ECE, PSI, expected profit at threshold | Beyond accuracy |
| Ablation | Bureau-only vs alt-data-only vs both, plus thin-file subset | Proves "not solely traditional scores" |
| Reject inference | Augmentation or parceling; compare approved-only vs inferred vs oracle | Honest lift measurement |
| Expected loss | EL = PD × LGD × EAD (LGD stated, editable) | Turns PD into rupees |

### 5.4 Recourse engine

1. Tag features: **immutable** (age, gender, location), **mutable and verifiable** (GST filing regularity, receivable days, bounce count, invoice digitisation), **gameable** (average balance; excluded from advice).
2. Search only over 3-4 verifiable levers, using the monotone challenger so direction is always sensible.
3. Recompute derived features after each change; re-score with the actual model.
4. Attach feasibility cost and estimated months to achieve; stamp with model version.
5. **Recourse equity:** compare median cost-to-approve across groups (women-led vs others, rural vs urban).

### 5.5 Cash-flow structuring (DSCR)

- Forecast monthly net cash available for debt service with P10/P50/P90 via quantile GBM, then widen/narrow with **split conformal** so coverage is defensible; backtest and report coverage.
- Choose a repayment schedule (or moratorium) so that **P10 cash available ≥ target DSCR × instalment** in all but at most one month of the tenor.
- Compare flat EMI vs matched schedule on simulated default rate for the same borrowers and report the lift, plus the reduced lift under the solvency-heavy config.

### 5.6 Fairness module

- Groups: women-led, rural, new-to-credit; intersectional pairs with confidence intervals.
- Metrics: adverse-impact (approval-rate) ratio, TPR gap (equal opportunity), calibration by group, recourse-cost gap.
- Mitigation: reweighing and in-processing (no protected attribute at inference). Group-aware thresholds shown only as a policy simulation.
- **Frontier chart:** fairness gap vs expected profit vs approvals; a slider lets the lender pick a policy and see the portfolio change.
- **Proxy audit:** train a model to predict the protected attribute from "neutral" features; report accuracy and top proxy features.
- State plainly: metrics conflict mathematically when base rates differ, so we expose the trade-off instead of hiding it.

### 5.7 Stress engine

- Shocks change **inputs** (revenue, receivable days, cost of debt, filing delays), then the model re-scores.
- **Named scenarios:** demonetisation-style cash squeeze, GST-rollout compliance shock, COVID-style demand collapse, 2022-23-style rate-hike cycle, plus a custom slider.
- **Contagion:** for supplier *j*, receivable days rise and revenue falls in proportion to buyer stress and revenue share; `Δreceivable_days_j = Σ_i w_ij × delay_i`.
- Outputs: expected loss, expected shortfall at 95%, first-failing segments, a tornado chart of assumption sensitivity, and one "mitigation lever" (for example, restructure the top 10% most stressed borrowers and show loss saved).

### 5.8 Governance layer (our closer)

| FREE-AI theme (Aug 2025, advisory) | Where we show it |
|---|---|
| Trust and accountability | Model card, decision ledger (model version, inputs, reasons, officer override) |
| Fairness and equity | Fairness frontier, proxy audit, recourse-equity gap |
| Understandable by design | Reason codes, recourse, borrower letter |
| People first / consumer protection | "Challenge this decision" button leading to human review log |
| Resilience and safety | Stress tests, drift (PSI), champion-challenger, gaming panel |
| Data protection (DPDP-aligned) | Mock AA consent artefact: purpose, data fields, duration; minimisation note |
| Innovation | Sandbox-style what-if environment |

*(Principles paraphrased from public summaries; confirm exact wording in the RBI report before quoting.)*

### 5.9 Stack

- **Data/ML:** Python, pandas, scikit-learn, LightGBM, SHAP, Fairlearn, NetworkX, statsmodels, MAPIE or a hand-rolled split conformal.
- **UI:** Streamlit multi-page + Plotly (fastest path). React only if a team member is already fast in it.
- **Deploy:** one public URL (Streamlit Community Cloud, Hugging Face Spaces, or Azure App Service) **plus** a local fallback and recorded video.
- **Rule:** the UI never trains models live. It loads artifacts and runs lightweight scoring.

---

## 6. Dashboard Design (six pages)

| Page | Audience | Hero element | Wow interaction |
|---|---|---|---|
| 1. Portfolio Command Center | Risk Head | Legacy vs Ours scoreboard, routing table | Toggle iso-loss / iso-approval |
| 2. Borrower Decision | Credit Officer | PD, reasons, recourse, structured loan | **Live sliders re-score instantly** |
| 3. Fairness Studio | Regulator / Risk Head | Fairness frontier, proxy audit | Policy slider changes the portfolio |
| 4. Stress and Contagion | Risk Head | Scenario cards, supplier-buyer graph | One-click historical replay |
| 5. Model Cockpit | Data Science / Regulator | ROC, KS, calibration, ablation, PSI, champion vs challenger | Toggle thin-file segment |
| 6. Governance and Trust | Regulator | FREE-AI map, decision ledger, consent mock, "Try to game it" | Attack toggles show flags |

Two role views in the demo: **Credit Officer** and **Risk Head**. The regulator view is Page 6, not a separate mode.

---

## 7. Execution Plan

The brochure lists 30 Sept 2026 as the event date, and the Unstop listing shows it as online, so **confirm the exact deadline and whether pitching is live or by recorded video with the organisers.** Scale the plan below to the time you actually have.

### 7.1 Time plan (24-hour version; compress proportionally)

| Block | Hours | Goal | Exit criterion |
|---|---|---|---|
| A. Contract and generator | 0-3 | Artifact contract, generator v1, legacy policy | `borrowers.parquet` + `panel.parquet` exist, seeded |
| B. Models | 3-7 | Champion, challenger, calibration, OOT, ablation | Metrics JSON saved |
| C. Decision layer | 7-12 | Reasons, recourse, DSCR structuring | Borrower page works end to end |
| D. Portfolio layer | 12-16 | Scoreboard, fairness frontier, stress with named scenarios | Pages 1, 3, 4 running |
| E. **Freeze features** | 16 | No new features after this point | |
| F. Governance and polish | 16-20 | Model card, FREE-AI map, ledger, memo export, copy | Page 6 done |
| G. Demo prep | 20-24 | Rehearse three times, record backup video, deck, README | Video recorded, deploy tested on a second device |

**If only 12 hours:** ship Tier 0 minus contagion (use input shocks only), reduce the sensitivity grid to two configs, skip Tier 1 except the Credit Appraisal Memo.
**If only 6 hours:** one config, champion + challenger, Borrower Decision page with recourse and structuring, Legacy vs Ours scoreboard, one fairness chart, one shock scenario, model card. Narrate the rest as roadmap.

### 7.2 Roles (scale to team size)

| Role | Owns |
|---|---|
| Data and models | Generator, legacy policy, models, calibration, ablation |
| Decision features | Recourse, DSCR structuring, fairness, stress engine |
| UI and demo | Streamlit pages, styling, memo export, deploy |
| Story and QA | Deck, script, README, Q&A prep, testing every claim against code |

With a two-person team, merge into (Data + Decision) and (UI + Story).

### 7.3 Rules that prevent disasters

1. Artifact contract on day one; UI only reads artifacts.
2. Precompute everything heavy (SHAP values, Monte Carlo, frontier).
3. Fixed random seeds; a single `make demo` or `python run_all.py`.
4. Feature freeze at the 16-hour mark (or 65% of the time you have).
5. Deploy early (hour ~10) so hosting problems appear while there is time.
6. Every number on a slide must have a line in `results/metrics.json`.

---

## 8. Demo Script (about 4 minutes)

**Persona:** Meena runs a women-led textile unit; thin credit file; strong seasonal cash flows.

| Time | Screen | What we say and do |
|---|---|---|
| 0:00-0:25 | Title + one stat | "Credit-gap estimates for Indian MSMEs range from ₹25 lakh crore to ₹60 trillion depending on the source. Many viable firms are invisible to lenders. Meet Meena." |
| 0:25-1:10 | Borrower Decision | Legacy policy: rejected (thin file). Our engine: calibrated PD, three plain-language reasons. Show ablation tile: alt-data lifts thin-file AUC. |
| 1:10-1:50 | Same page, sliders | **Wow #1.** Judge picks a lever (receivable days, GST regularity); decision and PD update instantly; recourse and months-to-achieve shown. Then the **structured schedule**: instalments sit under the P10 band in trough months; flat-EMI vs matched default rate shown. |
| 1:50-2:15 | Borrower letter / memo | **Wow #2.** One click: borrower letter in Tamil or Hindi plus the Credit Appraisal Memo for the officer. |
| 2:15-2:50 | Portfolio + Fairness | Legacy vs Ours scoreboard (same loss rate, more approvals). Fairness frontier: slide the policy, watch approvals, profit and gap move. State the cost of fairness in rupees. |
| 2:50-3:30 | Stress | **Wow #3.** Click "Demonetisation-style shock": contagion spreads through the supplier-buyer graph; show expected loss, tail loss, first-failing segment, and one mitigation lever. |
| 3:30-4:00 | Governance and close | FREE-AI map, decision ledger, consent artefact. Optional 10-second "Try to game it" toggle. Close with hero numbers and the honest-limits line. |

**Closing line:**
"We did not build a better score. We built a lending decision that a borrower, a credit officer and a regulator can each trust, and we measured what it costs and where it breaks."

**Fallback plan:** recorded 3-4 minute video of the same flow; local copy running; screenshots in the deck; pre-picked "safe" borrowers (Meena and two others) that are known to work.

**Hero numbers to headline (fill from the code, never invent):**

| Metric | Value |
|---|---|
| Additional approvals at same loss rate vs legacy | *[from run]* |
| Approved-only vs reject-inferred vs oracle gap | *[from run]* |
| Thin-file AUC: bureau-only vs alt-data | *[from run]* |
| Default-rate change, flat EMI vs DSCR-matched | *[from run, per config]* |
| Approval-rate ratio and TPR gap before/after mitigation | *[from run]* |
| Tail loss (95% ES) under each named shock | *[from run]* |
| Interval coverage (forecast) | *[from run]* |

---

## 9. Impact Story

**For MSMEs:** a reason and a route to yes instead of a silent rejection; repayment schedules that fit seasonal cash flow.
**For lenders:** more creditworthy approvals at controlled loss, lower underwriting cost through routing, and a portfolio that has been stress-tested for correlated failure.
**For regulators and society:** measured fairness with visible trade-offs, decisions that can be challenged, and audit trails aligned with the direction of RBI's FREE-AI recommendations.

**How to quantify (all from the synthetic pipeline, with stated assumptions):**

- Extra approvals at equal loss = (approvals under our policy) − (approvals under legacy) at the threshold that matches legacy loss.
- Expected profit = approvals × ticket × margin − EL − opex, with editable LGD, margin and ticket.
- Underwriting cost saved = (share auto-routed to fast-track) × (manual review cost) with a stated unit cost.
- Fairness cost = change in expected profit per point of gap closed, from the frontier.

**Framing rule:** say "under our documented assumptions, the method recovers X"; never "this will increase MSME lending by X% in India."

---

## 10. Judging-Criteria Alignment

| Typical criterion | What we show |
|---|---|
| Innovation | Recourse + priced fairness + DSCR structuring + contagion in one decision spine |
| Technical depth | Out-of-time validation, calibration, monotone models, conformal intervals, reject-inference scoreboard |
| Impact and feasibility | ₹ economics panel, AA consent flow, FREE-AI mapping, deployable architecture |
| UX and presentation | Persona-led demo, live sliders, three wow moments, two role views |
| Completeness vs PS | Requirement map (Section 1.3) covers every PS module |
| Honesty and rigour | Data statement, sensitivity grid, external-validity slide, stated limits |

---

## 11. Judge Q&A Prep

| Question | Answer |
|---|---|
| "Is this real data?" | "Synthetic, with a documented generator calibrated to public figures. That lets us measure something real data cannot: what happens to borrowers the legacy policy rejected. We also ran the same pipeline on a real public credit dataset to check the method holds outside our own assumptions." |
| "Isn't your result just what you built into the generator?" | "Partly, which is why we tested three generator configurations and report where the lift shrinks. Results are method validation, not India-level forecasts." |
| "How do you handle rejected applicants you never observed?" | "The legacy policy includes overrides, which gives overlap. We compare approved-only, reject-inferred and oracle, and we expect a modest gain." |
| "Which fairness definition did you pick?" | "We show several because they conflict when base rates differ. The lender chooses a policy and sees its cost in approvals and profit." |
| "Doesn't fairness mitigation use protected attributes?" | "Our main mitigation works without the attribute at decision time. Group-aware thresholds appear only as a policy simulation." |
| "Can borrowers game your recourse?" | "Recourse is limited to verifiable levers; gameable features are excluded, and the gaming panel shows how our detectors respond to three attacks." |
| "Is recourse causal?" | "No. It is a decision aid constrained by a monotone model and stamped with a model version." |
| "How reliable are your cash-flow forecasts?" | "We report backtested interval coverage and use conformal calibration. Schedules rely on the P10 band, not the mean." |
| "What if the economy shifts?" | "PSI drift monitoring plus scenario replays of past shocks with Monte Carlo bands; parameters are ranges, not point claims." |
| "How would this deploy?" | "Consent-based data via Account Aggregator, scoring service behind the lender's LOS, dashboard as the governance layer; the decision ledger supports audits." |
| "How does this fit regulation?" | "It follows the direction of RBI's FREE-AI recommendations: explainability, fairness, consumer recourse, governance. FREE-AI is advisory as released; we do not claim compliance." |
| "Why not a deep-learning model?" | "Tabular data with small default counts favours gradient boosting, and we need monotone constraints for sensible recourse." |
| "What would you do next?" | "Pilot on real, consented data with a partner lender; add LGD modelling and a challenger governance cycle." |

---

## 12. Risks and Honest Limits

| Risk | Mitigation |
|---|---|
| Scope explosion | Tiers, feature freeze, artifact contract |
| Synthetic data seen as "fake" | Data statement, calibration citations, sensitivity grid, external-validity slide |
| Live demo failure | Precompute, cache, recorded video, safe borrower set |
| Overclaiming | Wording rules below |
| Fairness overreach | "Measured and mitigated under stated definitions" |
| Overconfident forecasts | Always show intervals and backtest coverage |
| Stale regulatory claims | Quote only verified items; re-check before final deck |

**Wording rules**
- Say: "under our documented assumptions", "measured and mitigated", "decision aid", "illustrative parameters".
- Never say: "bias-free", "99% accurate", "guaranteed approval", "RBI-compliant".

**Limits to state up front:** results come from synthetic data with stated assumptions; contagion parameters are assumptions with uncertainty bands; recourse is not causal; FREE-AI is advisory guidance and we map to it rather than claim compliance.

---

## 13. Submission Checklist

- [ ] Confirm format with organisers (live pitch vs recorded, repo vs deck) and the exact deadline
- [ ] Public GitHub repo with README: problem, architecture diagram, data statement, how to run, results table, limitations
- [ ] Deployed URL tested on a second device and network
- [ ] 3-4 minute backup video
- [ ] Deck (8 slides): Problem · Insight · Solution spine · Live product · Evidence (scoreboard + external validity) · Fairness and stress · Governance/FREE-AI · Impact and roadmap
- [ ] `results/metrics.json` backs every number in the deck
- [ ] Three full rehearsals with a timer; one teammate plays a hostile judge using Section 11

---

## 14. Sources Consulted

- RBI FREE-AI Committee report (Aug 2025), plus summaries: Chambers and Partners, KPMG India, Dvara Research, Scrut. Also a May 2026 report noting RBI is assessing the recommendations.
- MSME credit portfolio ₹47.4 trillion (June 2026, CRIF High Mark), via Business Standard, 21 Sep 2026.
- Credit gap estimates: Deloitte via Whalesbook (₹25 lakh crore, March 2025; 14% formal access); RXIL (about ₹30 lakh crore; over 6.2 crore Udyam registrations); Business Standard, 11 Sep 2026 (about ₹60 trillion; about ₹8 trillion delayed payments).
- NBFC share of small-ticket MSME loans and alt-data underwriting: FlexiLoans report via Business Standard, Sep 2026.
- Event details: Hackconquest brochure (provided) and Unstop listing.

*Figures come from industry and media reports and differ by methodology. Re-verify before putting any on a slide.*
