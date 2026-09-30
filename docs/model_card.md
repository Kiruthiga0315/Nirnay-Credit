# MSME Lending Model Card

**Status**: v2 (audit-finalised 2026-10-01). All metric values are sourced directly from `artifacts/metrics.json` — no hand-written numbers.

## Intended Use

This model is a **decision aid** for underwriting MSME loans. It provides a calibrated Probability of Default (PD) over a 12-month horizon. It should **not** be used for fully automated decisions without human oversight (especially for overrides and exceptions). It is advisory guidance: we map to FREE-AI advisory principles and do not claim RBI-compliance. Phrases such as "guaranteed approval", "bias-free", or "99% accurate" are prohibited.

## Data

- **Training**: Origin months 1-24, using approved-only outcomes to mirror typical lending data availability (selection bias present; mitigated by reject inference).
- **Testing**: Out-of-time (OOT) test set covering origin months 25-36. The OOT split uses `oot_train_end` / `oot_test_start` columns (not hard-coded constants) — see `tests/test_leakage.py`.
- **Calibration**: IsotonicRegression fitted on a held-out 20% slice of train data (never touching OOT test data — disjointness test-enforced).
- **Features**: Traditional credit bureau scores and alternative data (GST filings, digital invoices, bank balance, UPI inflows, cheque bounces, etc.). Full list in `configs/feature_spec.json`.
- **Protected Attributes**: `owner_gender` and `location_class` have `model_input=false` in `feature_spec.json` and are verified absent from `model_features()` by `tests/test_leakage.py::test_protected_attributes_not_in_model_features`.
- **Oracle isolation**: `data/oracle.parquet` (true latents and outcomes for all firms) is loaded only inside `build_artifacts()` for evaluation purposes and is **never accessible via `score()` or `score_batch()`** — enforced by `tests/test_leakage.py::test_oracle_runtime_guard`.

## Models

- **Champion Model**: Logistic regression on WoE-binned features. Easily interpretable and stable, serving as the benchmark standard.
- **Challenger Model**: LightGBM tree-based classifier with monotonic constraints. Captures non-linearities while enforcing sensible relationships (e.g., higher receivable days monotonically increases risk).
- **Calibration**: Isotonic Regression fitted on a held-out slice of the training data ensures predicted probabilities reflect realistic default rates.
- **model_version**: `v2-reject-inference` (must not start with `stub` in production runs).

## Metrics (sourced from `artifacts/metrics.json`)

### Internal OOT performance

| Metric | Champion | Challenger |
|---|---|---|
| AUC OOT | `models.auc_champion_oot` = 0.611 | `models.auc_challenger_oot` = 0.540 |
| Gini OOT | — | `models.gini_challenger_oot` = 0.080 |
| KS OOT | — | `models.ks_challenger_oot` = 0.160 |
| Brier score OOT | — | `models.brier_challenger_oot` = 0.073 |
| ECE (calibration) | — | `models.ece_challenger` = 0.047 |
| PSI (stability) | — | `models.psi_challenger` = 0.008 |

Note: AUC values are low (~0.54-0.61) — this reflects genuine low signal in the generated dataset, not a coding error. See `docs/known_issues/m1.md`.

### Reject-inference scoreboard (OOT, oracle outcomes)

| Model | AUC OOT | Approvals at equal loss |
|---|---|---|
| Legacy policy | ~0.52 | 411 (baseline) |
| Approved-only | `models.auc_approved_only_oot` = 0.553 | 419 |
| Reject-inferred | `models.auc_inferred_oot` = 0.566 | 484 |
| Oracle (ref only) | `models.auc_oracle_oot` = 0.583 | 534 |

Extra approvals at equal loss vs legacy: `models.extra_approvals_at_equal_loss` = **+73** (medium kappa, medium bias, smoke mode).

### Ablation

| Model | AUC OOT |
|---|---|
| Bureau score only | `models.auc_bureau_only` = 0.440 |
| Alt data only (no bureau) | `models.auc_alt_data` = 0.572 |
| Thin-file, bureau only | `models.auc_thin_bureau_only` = 0.500 |
| Thin-file, alt data | `models.auc_thin_alt_data` = 0.599 |

### External Validity

| Metric | Champion | Challenger |
|---|---|---|
| AUC | `external.auc_champion` = 0.521 | `external.auc_challenger` = 0.589 |
| KS | `external.ks_champion` = 0.146 | `external.ks_challenger` = 0.208 |
| ECE | `external.ece_champion` = 0.120 | `external.ece_challenger` = 0.164 |

Note: External dataset may not be present in all environments (`[external] Dataset not found. Skipping.`). Values above are from the last successful run with external data available.

## Fairness

| Metric | Value (from `artifacts/metrics.json`) |
|---|---|
| Women-led Adverse Impact Ratio (AIR) | `fairness.women_led_air` = 0.998 |
| Rural AIR | `fairness.rural_air` = 0.979 |
| New-to-credit AIR | `fairness.new_to_credit_air` = 0.967 |
| Women-led TPR gap | `fairness.women_led_tpr_gap` = −0.015 |
| Rural TPR gap | `fairness.rural_tpr_gap` = −0.011 |

Positive outcome is defined as **non-default**. Measured and mitigated under stated definitions.

## Limits

1. Results are method validation, not India-level claims. Every improvement is partially a product of the simulation design.
2. Default mechanism is stylised. Real MSME defaults involve complex interactions (supply-chain, regulatory, seasonal).
3. Calibration targets are approximate. Actual MSME default rates vary widely by sector, vintage, and product.
4. AUC signal is low (~0.54-0.61), reflecting the difficulty of the synthetic task.
5. External dataset licences are unverified (TODO(verify) — see `docs/known_issues/m1.md`).
6. APPROVAL_PD_THRESHOLD is a stub placeholder (0.10) — see `docs/known_issues/m1.md`.
