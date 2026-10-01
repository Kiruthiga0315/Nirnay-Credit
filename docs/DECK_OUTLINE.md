# Pitch Deck Outline (10 Slides)

This outline specifies the slide structure, on-slide text, visual assets/screenshots, and exact backing metrics keys from `artifacts/metrics.json`. All external claims are marked *(re-verify before use)*.

---

## Slide 1: Problem
**Title:** The Invisible MSME  
**On-Slide Text:**  
- Estimated Indian MSME credit gap: **₹20–25 Lakh Crore ($250–300B)** *(Source: IFC / UK Sinha RBI Committee, 2019; re-verify before use)* to **₹60 Trillion** *(Source: Business Standard, Sep 2026; re-verify before use)*.
- Over **85%** of micro-enterprises lack access to formal credit due to thin bureau files.
- Viable enterprises are rejected by rigid rule-based cutoffs.  
**Screenshot/Visual:** Title splash & ecosystem macro context.  
**Metrics Key:** None (External sources noted).

---

## Slide 2: Insight
**Title:** Predictions Are Not Decisions  
**On-Slide Text:**  
- A risk score alone does not tell an underwriter how to help a borrower.
- The missing link in MSME lending is **trust and actionability**:
  1. Plain-language reasons for every decision.
  2. A feasible, counterfactual route to approval (Recourse).
  3. Transparent pricing of the cost of fairness.  
**Screenshot/Visual:** Conceptual diagram: *Score vs Governed Decision*.  
**Metrics Key:** None.

---

## Slide 3: Solution
**Title:** Nirnay-Credit: The Governed Decision Spine  
**On-Slide Text:**  
- One unified decision workflow: **Predict $\rightarrow$ Explain $\rightarrow$ Recourse $\rightarrow$ Structure $\rightarrow$ Stress-Test $\rightarrow$ Govern**.
- Built on open-source, deterministic Python core with full auditability.
- Designed as a decision aid for underwriters and credit committees.  
**Screenshot/Visual:** System Architecture Flowchart (README).  
**Metrics Key:** None.

---

## Slide 4: Live Product
**Title:** Meet Meena: The Borrower Decision  
**On-Slide Text:**  
- **Borrower**: `MSME-00001` (Textile Micro-enterprise, Surendranagar).
- **Legacy Rule**: Flat rejection (Thin credit file).
- **Nirnay Engine**: Calibrated $\text{PD} = 0.0661$ ($6.61\%$).
- **Actionable Recourse**: Shortening receivable cycle by 15 days flips decision to approval (Cost: $15.0$).  
**Screenshot/Visual:** Page 2: Borrower Decision Cockpit & Recourse Slider.  
**Metrics Key:** `recourse.meena_new_pd`, `recourse.meena_cost`.

---

## Slide 5: Evidence
**Title:** Predict & Perform at Portfolio Scale  
**On-Slide Text:**  
- Champion LightGBM Out-of-Time AUC: **$0.611$** (vs Challenger $0.540$).
- Baseline Legacy Loss Rate: **$7.5\%$**.
- **$+20$ Extra Approvals** unlocked at identical portfolio loss rate.
- Calibrated reject inference recovers viable excluded borrowers.  
**Screenshot/Visual:** Page 1: Portfolio Command Center & Scoreboard.  
**Metrics Key:** `models.auc_champion_oot`, `models.legacy_loss_rate`, `models.extra_approvals_at_equal_loss`.

---

## Slide 6: Fairness
**Title:** The Price of Inclusion  
**On-Slide Text:**  
- Women-led Adverse Impact Ratio (AIR): **$0.9984$** (near parity).
- We expose the multi-group fairness Pareto frontier.
- Direct rupee-quantification of policy choices: closing the inclusion gap costs an estimated **₹19.0 Lakh** in expected profit under documented assumptions.  
**Screenshot/Visual:** Page 3: Fairness Studio & Pareto Frontier Curve.  
**Metrics Key:** `fairness.women_led_air`, `fairness.cost_of_fairness_sentence`.

---

## Slide 7: Resilience
**Title:** Macro Stress-Testing & Network Contagion  
**On-Slide Text:**  
- Simulates systemic shocks (Demonetisation-style, GST-rollout, Covid-style).
- Graph engine models second-order buyer-supplier liquidity contagion.
- Dynamic mitigation levers prove **₹1.18–1.25 Crore** in expected loss reduction.  
**Screenshot/Visual:** Page 4: Stress & Contagion Dashboard.  
**Metrics Key:** `stress.demonetisation_style.EL`, `stress.demonetisation_style.mitigation_saved_inr`.

---

## Slide 8: Governance
**Title:** Trust by Design & Regulatory Mapping  
**On-Slide Text:**  
- Aligned to RBI's advisory **FREE-AI Framework** (Fairness, Reliability, Explainability, Ethics).
- Immutable SHA-256 Decision Ledger with non-repudiation audit trail.
- Post-disbursal hazard tracking provides **$2.18$ months** mean early warning lead time.  
**Screenshot/Visual:** Page 6: Governance, Audit Ledger & FREE-AI Matrix.  
**Metrics Key:** `early_warning.mean_lead_time_months`, `trust.clean_firms_share`.

---

## Slide 9: Impact
**Title:** Structuring for Repayment Success  
**On-Slide Text:**  
- Cash-flow matched repayment structuring tailored to seasonal revenues.
- Conformal quantile bands provide calibrated $88.6\%$ cash flow coverage.
- Achieves a **$28.2\%$ default rate reduction (lift)** compared to flat monthly EMIs.  
**Screenshot/Visual:** Page 2: Repayment Schedule Comparison & Cash Flow Chart.  
**Metrics Key:** `structuring.lift_matched_vs_flat`, `forecast.conformal_interval_coverage_80pct`.

---

## Slide 10: Roadmap
**Title:** The Path Forward  
**On-Slide Text:**  
- **Phase 1**: Account Aggregator (AA) live consented data integration pilot.
- **Phase 2**: Multi-tier Loss Given Default (LGD) and dynamic pricing engine.
- **Phase 3**: Multi-lender consortium challenger model governance.  
**Screenshot/Visual:** Roadmap timeline & contact / deployment links.  
**Metrics Key:** None.
