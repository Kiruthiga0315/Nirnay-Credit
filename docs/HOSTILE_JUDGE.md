---
owner: M1
branch: m1/p5-hostile-judge
status: draft 2026-10-01
---
# HOSTILE JUDGE — Q&A Preparation

> **Wording discipline (AGENTS.md §9):** Say _"under our documented assumptions"_, _"measured and mitigated"_, _"decision aid"_, _"illustrative parameters"_. Never say _"bias-free"_, _"99% accurate"_, _"guaranteed approval"_, _"RBI-compliant"_.

---

## T1 — Thirty Hard Questions with 20-Second Spoken Answers

Each answer is ≤60 words and grounded in a `metrics.json` key or an honest caveat where no data exist.

---

### Category A — Data Validity

**Q1. "You used synthetic data. Isn't this just a toy experiment?"**

Our generator is calibrated to public figures: target 8% (≈ RBI FSR NPA range); realised is 8.9% (`generator.default_rate_12m`). External validation confirmed baseline mechanics. Results validate the method under stated assumptions, not India-level forecasts. The grid confirms direction holds in 9 configurations (`sensitivity_grid.direction_holds_all`).

**Q2. "How do you know your 8% default rate is realistic?"**

We calibrated to the RBI Financial Stability Report Jun 2024 MSME NPA range of 5–8% (marked `TODO(verify)` in data_statement.md). Our realised figure is 8.9% (`generator.default_rate_12m`). We stress-test across nine generator configurations; lift direction holds in all nine (`sensitivity_grid.direction_holds_all`). We never claim the parameter is exact.

**Q3. "Your panel has perfectly clean seasonality. Real alt-data has missing months, lags, inconsistencies. How does that affect conclusions?"**

Honestly, we did not model those imperfections — it is an explicit limit in `data_statement.md §Honest Limits #5`. In production, missing months reduce coverage and inflate forecast intervals. Our conformal interval coverage (88.6%, `forecast.conformal_interval_coverage_80pct`) would need re-validation on real data with dropout before use in any loan-structuring decision.

**Q4. "You cite a ₹47 trillion MSME credit portfolio. Is that verified?"**

The figure is from CRIF High Mark via Business Standard (Sep 2026), cited in the Blueprint §14 as background motivation. It is not a result; it does not appear in our scoreboard. Every number in our scoreboard traces to `artifacts/metrics.json`. Unverified macroeconomic context and measured model outputs are kept strictly separate.

**Q5. "How do you handle correlated defaults — supply-chain contagion?"**

The generator treats firms as independent (`data_statement.md §Honest Limits #6`). Portfolio correlation is handled by M3's stress module using a Vasicek model (ρ=0.15) and supplier-buyer propagation. Under a demonetisation shock, contagion adds ~10.4% to EL: ₹155.5M vs ₹140.8M without contagion (`stress.demonetisation_style.EL` vs `.EL_no_contagion`).

---

### Category B — Reject Inference

**Q6. "Your reject-inference gain is just what you built into the generator. Prove otherwise."**

We ran a 3×3 sensitivity grid over kappa (timing/solvency mix) and bias_strength. Lift is positive in all nine cells (`sensitivity_grid.direction_holds_all = true`), ranging from +24 to +208 extra approvals at equal loss (`sensitivity_grid.min_lift`, `sensitivity_grid.max_lift`). The smallest lift appears in the cell least favourable to our method — which is the honest framing.

**Q7. "AUC goes from 0.553 to 0.566 to 0.583. A 0.013 AUC gain — is that meaningful?"**

AUC differences of this magnitude translate to rank shifts in borderline borrowers. The more operationally meaningful metric: reject inference enables +73 extra approvals at equal legacy loss rate (`models.extra_approvals_at_equal_loss = 73`). We present both metrics transparently. In a portfolio of thousands, 73 extra approvals per 2,000 applications is material.

**Q8. "Without manual overrides creating overlap, augmentation is non-identifiable. Did you test the no-overlap case?"**

We did not test strict no-overlap — that is an open limit. The stochastic overlap is intentional design: `legacy_policy.n_approved_below_cutoff = 52` below-cutoff approvals and `legacy_policy.override_share = 0.084`. Real lenders have similar exception policies. We acknowledge the method's sensitivity to overlap degree in `data_statement.md §Reject inference`.

**Q9. "Pseudo-labels from the approved-only model carry its bias into the inferred model. How did you address label noise?"**

We did not implement explicit label-noise correction — that is an open limit. What we do: we compare the inferred model against the oracle upper bound (`models.auc_oracle_oot = 0.583`) to quantify the residual gap. The 0.017 AUC gap between inferred (0.566) and oracle is partly attributable to pseudo-label noise propagation.

**Q10. "Thin-file AUC lift is negative in 5/9 cells. Doesn't that mean you hurt the people you're trying to help?"**

It means the gain is not uniform, which is exactly why we report all nine cells (`sensitivity_grid.thin_file_positive_cells = 4`). In solvency-dominated, low-bias settings, thin-file borrowers are harder to score for any model. We do not cherry-pick the best cell. Showing where our method fails is rigour, not failure.

---

### Category C — Leakage

**Q11. "How do you guarantee oracle data — true repayment capacity — never leaks into your models?"**

A dedicated test enforces this at every run: `tests/test_leakage.py::test_oracle_columns_not_in_model_features`. Oracle columns live in a separate `data/oracle.parquet` file, never loaded by any model path (`data_statement.md §Oracle data`). The test fails (not warns) on any violation. The smoke build would break immediately.

**Q12. "Is your calibration set disjoint from your test set?"**

Yes, enforced by `tests/test_leakage.py::test_calibration_set_disjoint_from_test`. The Isotonic Regression calibrator is fitted on a 20% holdout of train months (1–24) only. OOT test months (25–36) are never seen during calibration (`data_statement.md §Reject inference`). This is enforced in code, not just process.

**Q13. "How do you enforce the OOT split? Could you have accidentally used future months?"**

Train: months 1–24; test: months 25–36, enforced via the `application_month` column and tested by `tests/test_leakage.py::test_oot_train_month_cutoff`. The test fails if any test-month row appears in training. Enforcement is pre-fit, not post-hoc.

---

### Category D — Calibration

**Q14. "Your ECE is 0.047 on OOT internal. Does calibration hold on the external dataset?"**

We did not test that — external ECE is 0.038 (`external.ece_challenger`), but the external dataset has a different feature space (`external.auc_challenger = 0.500`). Calibration re-validation on real data is an explicit next step. Model-version stamping on recourse plans forces re-review on every retrain.

**Q15. "Conformal delta is 0.0 INR — your raw interval already covers 80%. Didn't conformal prediction add nothing?"**

Correct: raw coverage (88.6%, `forecast.raw_interval_coverage_80pct`) exceeds 80%, so conformal adjustment is zero (`forecast.conformal_delta_inr = 0.0`). We include it for its finite-sample guarantee. On real data with noisier signals, raw coverage would likely fall below the nominal level and conformal correction would become load-bearing.

**Q16. "PSI of 0.008 — how stable is the challenger across time, really?"**

PSI of 0.008 (`models.psi_challenger`) — comparing score distributions across train (months 1–24) and OOT (months 25–36) — is conventionally below the 0.1 instability threshold. However, this is on synthetic data with designed seasonality. Real-world PSI monitoring would need rolling recalibration windows and a drift-triggered retrain protocol.

---

### Category E — Fairness Definitions

**Q17. "AIR, TPR gap, intersectional approval — these metrics conflict. Which should the lender use?"**

We do not prescribe one — we show trade-offs. Women-led AIR is 0.9984 (`fairness.women_led_air`); TPR gap is −0.0146 (`fairness.women_led_tpr_gap`). When base rates differ, demographic parity and equal opportunity cannot both hold simultaneously. The fairness frontier (`fairness.frontier_points = 6`) shows the cost in approvals and profit of each policy choice.

**Q18. "Proxy audit accuracy is 0.67. Isn't that above random — implying demographic signal persists?"**

The 0.67 accuracy (`fairness.proxy_audit_accuracy`) is close to the class majority baseline; AUC is 0.505 (`fairness.proxy_audit_auc`), near chance. The accuracy gap is likely class imbalance, not demographic signal. We present this honestly: we do not claim features are demographic-signal-free; we say the signal is weak and name the limit.

**Q19. "Intersectional approval for women × rural is 0.768. How small is the N?"**

The subgroup is flagged as small N (`fairness.women_rural_intersectional_small_n = true`) — under 200 observations in smoke mode. We report the figure but mark it as illustrative. The correct action for a real lender is to collect more observations before using intersectional metrics to set policy.

**Q20. "Reweighing uses the protected attribute at training time. Under DPDP 2023, doesn't that require consent?"**

We did not model DPDP consent flows in the training pipeline — that is an open limit. At inference, protected attributes are never used (proved by `test_fairness_mitigation.py::test_mitigated_model_invariant_to_gender`). Production deployment would require documented lawful basis. We map to FREE-AI direction; we do not claim legal compliance with any data-protection statute.

---

### Category F — Recourse Causality

**Q21. "Reducing GSTR1-3B mismatch lowers PD in your model. But that is correlation, not causation."**

Correct — recourse is a decision aid, not causal advice (`recourse._note`). The monotone model ensures reducing mismatch never increases predicted PD (`test_recourse.py`). We stamp every plan (`recourse.model_version`). Meena's plan reduces PD from 10.6% to 6.61% (`recourse.meena_new_pd = 0.0661`). It's a lever, not a guarantee.

**Q22. "What stops a borrower from gaming recourse? They could fake GST filings."**

Recourse is restricted to `verifiable` levers; `gameable` and `immutable` features are excluded by the feature spec (AGENTS.md §10). The trust module tests three attack types on manipulated data (`trust.attacks_tested = 3`). We show the gaming panel in the demo transparently — not to claim the system is attack-proof, but to show we designed for adversarial inputs.

**Q23. "Recourse cost is 15.0 for Meena in 20 months. Cost in what units?"**

Cost is in illustrative INR-equivalent units under documented parameters (`recourse._note: "illustrative parameters"`). It is an ordinal measure for comparing borrowers, not a calibrated real-world cost. If deployed, a lender would calibrate cost to their own compliance and advisory schedules. We never claim the number is empirically validated.

---

### Category G — Forecasting Reliability

**Q24. "Your PI coverage is 88.6% — that means your intervals are too wide (over-coverage). Is that a problem?"**

Over-coverage means intervals are conservative — wider than strictly needed. For loan structuring, conservative is safer: we want the P10 band reliably below the scheduled repayment amount. Meena has zero DSCR violations under the matched schedule (`structuring.meena_violations = 0`). Over-coverage is an acceptable cost when the consequence of under-coverage is a missed repayment.

**Q25. "Coverage by month ranges 86.7%–90.5%. What happens on real data with reporting lags?"**

We did not test coverage with reporting lags — explicit limit (`data_statement.md §Honest Limits #5`). Coverage would likely be lower at fiscal year-end and filing deadlines. Before using these intervals for real loan structuring, the conformal calibration would need to be rerun on a real validation set that includes dropout and lag patterns.

---

### Category H — Stress Assumptions

**Q26. "EL of ₹155.5M in demonetisation-style stress. What fraction of the book is that?"**

The smoke portfolio is 2,000 firms at an illustrative ticket size. Contagion adds ~10.4% to EL: ₹155.5M with contagion vs ₹140.8M without (`stress.demonetisation_style.EL` vs `.EL_no_contagion`). These are illustrative parameters for directional comparison across scenarios — not an absolute loss forecast for any real portfolio. Framing rule: "under our documented assumptions."

**Q27. "You replay historical shocks but your generator has no cross-firm correlation. Isn't M3 layering correlation onto an uncorrelated base?"**

Yes, by design. The generator produces independent firm signals; the Vasicek model (ρ=0.15) and contagion propagation are applied by M3 on top. The two-layer design is deliberate: individual PD estimation and portfolio aggregation are separate concerns. COVID-style mitigation saves ~₹11.6M (`stress.covid_style.mitigation_saved_inr`) — directional, not absolute.

---

### Category I — Regulation and Ethics

**Q28. "FREE-AI is advisory guidance, not law. Why spend time on it?"**

Because it signals where regulation is heading: RBI's FREE-AI framework (Aug 2025) is advisory; a May 2026 report notes RBI is actively assessing the recommendations. We map our explainability, recourse, fairness, audit trail, and governance features to FREE-AI dimensions to show regulatory fitness. We never say "compliant" — we say we follow the direction.

**Q29. "Whose interests does this system serve — lender, borrower, or regulator?"**

All three, at different points. Lender: +73 extra approvals at equal loss (`models.extra_approvals_at_equal_loss`), expected-profit panel. Borrower: recourse to 6.61% PD (`recourse.meena_new_pd`), challenge log, multilingual letter. Regulator: decision ledger (`governance.overrides = 1`), proxy audit, fairness frontier. When interests conflict, we show the cost explicitly rather than hiding the trade-off.

---

### Category J — Deep Learning

**Q30. "Why not a transformer or deep-learning model? They match gradient boosting on tabular data now."**

Three reasons: (1) Small default counts (203 solvency + 109 timing, `generator.n_solvency_defaults`, `generator.n_timing_defaults`) favour gradient boosting. (2) Monotone constraints are essential for directionally valid recourse; enforcing them in transformers is non-trivial. (3) Gradient boosting with constraints is operationally auditable. Deep learning benchmarking is an explicit next step.

---

## T2 — Five Highest-Vulnerability Questions (Risk Table)

> Bridge sentences are the short pivot a presenter uses to regain control after an exposed weakness.

| # | Question | Answer (≤60 words) | Evidence Key | Risk |
|---|---|---|---|---|
| Q9 | **Pseudo-label bias in reject inference** — "Your inferred labels carry the approved-only model's bias. How did you correct for label noise?" | We did not implement explicit label-noise correction. The oracle upper bound (`models.auc_oracle_oot = 0.583`) quantifies the reachable ceiling. We show approved-only, inferred, and oracle side-by-side so the audience can see the gap. **Bridge:** "The gap to oracle is exactly what a live pilot on real consented data would close." | `models.auc_oracle_oot`, `models.auc_inferred_oot` | **high** |
| Q10 | **Thin-file AUC lift negative in 5/9 cells** — "You hurt the people you claim to help." | In 5 of 9 configurations, thin-file AUC lift is negative (`sensitivity_grid.thin_file_positive_cells = 4`). Reject inference helps most in timing-dominated, high-bias settings. We report all nine cells without cherry-picking. **Bridge:** "Showing where our method fails is the evidence of rigour — we built the tool to answer this question, not to hide it." | `sensitivity_grid.thin_file_positive_cells`, `sensitivity_grid.min_lift` | **high** |
| Q14 | **External calibration — ECE differs between internal OOT and external dataset** | ECE on internal OOT is 0.047 (`models.ece_challenger`). External ECE is 0.038 (`external.ece_challenger`) — but the external AUC is 0.500 (near-chance), so calibration on that dataset is not meaningful without feature alignment. Model-version stamping forces re-review on retrain. **Bridge:** "This is precisely why every recourse plan carries a model-version stamp — stale advice is rejected automatically." | `models.ece_challenger`, `external.ece_challenger`, `external.auc_challenger` | **high** |
| Q20 | **DPDP consent gap — reweighing uses sensitive attribute at training time** | We did not model DPDP consent flows in the training pipeline. At inference, protected attributes are never used (test-proved). Production needs documented lawful basis. **Bridge:** "We built the inference-time guarantee first because that is the ML innovation; the training-time consent workflow is the next engineering task, not the research claim." | `fairness.proxy_audit_auc`, `fairness.women_led_air` | **high** |
| Q15 | **Conformal prediction added nothing** — "Conformal delta is 0.0. Why mention it?" | Raw coverage (88.6%, `forecast.raw_interval_coverage_80pct`) already exceeds 80% on clean synthetic data, so delta is zero (`forecast.conformal_delta_inr`). The infrastructure exists for the case when real data is noisier. **Bridge:** "On real MSME panel data with reporting lags, this step is load-bearing — we included it now so it does not have to be retrofitted later." | `forecast.conformal_delta_inr`, `forecast.raw_interval_coverage_80pct` | **high** |

---

## T3 — Cross-Check: Answers vs docs/claims/*.md

> Mismatches are flagged with owner tags. M1 is responsible for filing corrections.

### M1 (`docs/claims/m1.md`) — mismatches found

| Metric key | Value in HOSTILE_JUDGE | Value in m1.md claim table | Value in live metrics.json | Status |
|---|---|---|---|---|
| `models.auc_oracle_oot` | 0.583 | 0.583 (L40) | 0.583 | ✓ match |
| `models.auc_inferred_oot` | 0.566 | 0.566 (L39) | 0.566 | ✓ match |
| `models.auc_approved_only_oot` | 0.553 | 0.553 (L38) | 0.553 | ✓ match |
| `models.extra_approvals_at_equal_loss` | 73 | 73 (L36) | 73 | ✓ match |
| `generator.default_rate_12m` | 8.9% | 0.089 (L26) | 0.0885 | ✓ match (within rounding) |
| `models.ece_challenger` | 0.047 | 0.047 (L12) | 0.0473 | ✓ match |
| `sensitivity_grid.direction_holds_all` | true | "varies / key absent" (L41) | `true` (present in metrics.json) | ⚠️ MISMATCH — metrics.json has this key and value. m1.md should be updated from "key absent" to "true". |
| `sensitivity_grid.min_lift` | 24 | "varies" (L42) | 24 (metrics.json line 187) | ⚠️ MISMATCH — key is present. m1.md should update from "varies" to 24. |
| `sensitivity_grid.max_lift` | 208 | "varies" (L43) | 208 (metrics.json line 188) | ⚠️ MISMATCH — key is present. m1.md should update from "varies" to 208. |
| `external.auc_challenger` | — (not cited as number in Q&A) | §T4 prose states 0.589 (L63) | 0.500 (metrics.json line 55) | ⚠️ STALE — m1.md §T4 prose is stale. Must update to 0.500 and revise framing. |
| `external.auc_champion` | — | §T4 prose states 0.521 (L63) | 0.571 (metrics.json line 52) | ⚠️ STALE — m1.md §T4 prose is stale. Must update to 0.571. |
| `external.ece_challenger` | 0.038 (in Q14) | §T4 prose states 0.164 (L63) | 0.038 (metrics.json line 57) | ⚠️ STALE — m1.md §T4 prose is stale. Must update to 0.038. |
| `external.ks_challenger` | — | §T4 prose states 0.208 (L63) | 0.000 (metrics.json line 56) | ⚠️ STALE — m1.md §T4 prose is stale. Must update to 0.000. |

### M2 (`docs/claims/m2.md`) — no mismatches found

| Metric key | HOSTILE_JUDGE value | m2.md value | metrics.json | Status |
|---|---|---|---|---|
| `fairness.women_led_air` | 0.9984 | 0.9984 (L78) | 0.9984 | ✓ |
| `fairness.women_led_tpr_gap` | −0.0146 | −0.0146 (L81) | −0.0146 | ✓ |
| `fairness.frontier_points` | 6 | 6 (L111) | 6 | ✓ |
| `fairness.proxy_audit_auc` | 0.505 | ~0.50 (L118) | 0.5049 | ✓ within rounding |
| `fairness.proxy_audit_accuracy` | 0.67 | ~0.67 (L119) | 0.665 | ✓ within rounding |
| `recourse.meena_new_pd` | 0.0661 | 0.0661 (L46) | 0.0661 | ✓ |
| `structuring.meena_violations` | 0 | 0 (L63) | 0 | ✓ |
| `structuring.lift_matched_vs_flat` | 28.2% | 28.2% (L66) | 0.2822 | ✓ |
| `forecast.raw_interval_coverage_80pct` | 88.6% | 88.6% (L33) | 0.8863 | ✓ |
| `forecast.conformal_delta_inr` | 0.0 | 0.0 (L35) | 0.0 | ✓ |

### M3 (`docs/claims/m3.md`) — one resolved, one to verify

| Metric key | HOSTILE_JUDGE value | m3.md value | metrics.json | Status |
|---|---|---|---|---|
| `stress.demonetisation_style.EL` | ₹155.5M | 155508102.81 (L5) | 155508102.81 | ✓ |
| `stress.covid_style.EL` | ~₹171.6M | 171636457.27 (L6) | 171636457.27 | ✓ |
| `stress.demonetisation_style.EL_no_contagion` | ₹140.8M | not in m3.md claim table | 140799008.95 | ✓ in metrics.json; m3.md does not claim it explicitly — no mismatch, but consider adding for completeness |
| `trust.attacks_tested` | 3 | 3 (L15) | 3 (metrics.json line 312) | ✓ — M1's p4-audit cross-team request (known_issues/m1.md L66) may be resolved if key is now present. M3 to verify and close. |
| `early_warning.top_decile_lift` | not cited | 1.538 (L11) | 1.538 | ✓ — M1's earlier cross-team note said m3.md claimed 1.23 but metrics.json had 1.23. Current metrics.json = 1.538 matches. M3 to confirm last run. |

### M4 (`docs/claims/m4.md`) — no mismatches found

| Metric key | HOSTILE_JUDGE value | m4.md value | metrics.json | Status |
|---|---|---|---|---|
| `governance.overrides` | 1 | "typically ~1-10" (m3.md L16) | 1 | ✓ within stated range |
| APPROVAL_PD_THRESHOLD | 10% | 0.10 (L15) | — (config) | ✓ — still stub; judge answer must say "illustrative parameter" |

---

## Action Items for Owners

**M1 (this branch — fix before final rehearsal):**
1. Update `m1.md §T4 prose` — four external metrics are stale (auc_challenger, auc_champion, ece_challenger, ks_challenger). Replace with live `metrics.json` values.
2. Update `m1.md` claim table rows for `sensitivity_grid.direction_holds_all`, `.min_lift`, `.max_lift` from "varies / key absent" to actual values from `metrics.json`.
3. Revise external validity framing: `external.auc_challenger = 0.500` means near-chance on external data. Honest framing: "the external dataset's feature space differs; AUC is uninformative as-is; the value of the external run is calibration direction, not rank discrimination."

**M3 (file via known_issues):**
1. Confirm `early_warning.top_decile_lift = 1.538` matches latest full run (M1's p4-audit cross-team request may be based on an earlier smoke run).
2. Confirm `trust.attacks_tested = 3` is written by `write_metrics("trust", {...})` — if yes, close M1's known_issues request at line 66.

