---
owner: M1
status: v1
---
# Data statement

## What is this dataset?

A fully synthetic MSME population of ~20,000 firms (2,000 in smoke mode) with:

- **Entity-level features** aligned to `configs/feature_spec.json`: sector, location class, Udyam category, vintage, owner gender, bureau score, collateral, GST signals, cash-flow proxies, concentration indices, and requested loan amount.
- **Monthly panel** (36 months): revenue, UPI/bank inflows, GST turnover, filing delays, receivable days, cheque bounces — all generated as **noisy functions of hidden latent variables** (signals, not ground truth).
- **Oracle data** (`data/oracle.parquet`): true repayment capacity, shock sensitivity, management quality, sector seasonality profile, default month, default type (timing vs solvency), and the 12-month default indicator. **This file is NEVER loaded by any model or UI.**
- **Observed outcomes** (`data/observed_outcomes.parquet`): default outcomes only for firms approved by the stochastic legacy policy. This is the training signal available to models.

A reference borrower **Meena (MSME-00001)** is injected exactly from `configs/personas/meena.json`.

## Latent variable structure (hidden from models)

| Latent | Distribution | Role |
|---|---|---|
| `capacity` | Uniform(0.3, 1.8) | True repayment capacity; drives revenue and DSCR |
| `shock_sensitivity` | Beta(2, 5) | Vulnerability to solvency shocks; skewed low |
| `management_quality` | 0.3 + 0.7·Beta(5, 2) | Competence; affects filing delays, mismatch, utility delays |
| `sector_seasonality_amp` | Lookup by sector | Amplitude of seasonal revenue swings |
| `kappa` (grid axis) | {0.2, 0.5, 0.8} | Timing-vs-solvency mix parameter |

Observable signals are noisy functions of latents. True capacity is **independent of gender given features** — the only channel from protected attributes to outcomes is through bureau coverage (thin-file mechanism).

## Default mechanism (12-month horizon)

Monthly hazard from two channels:

1. **Timing (cash-flow) defaults:** when a firm's DSCR (revenue / monthly EMI obligation) falls below 1.0 for **k=3 consecutive months**, a timing default is triggered.
2. **Solvency (shock) defaults:** each month, a random shock occurs with probability `base_hazard × (0.3 + shock_sensitivity) / (management_quality × capacity)`. Base hazard = 0.008/month.

The parameter **κ (kappa)** controls the mix:
- If both channels trigger, the earlier one is used.
- If only timing triggers, it is accepted with probability κ.
- If only solvency triggers, it is accepted with probability (1 − κ).

This means kappa=high produces more timing-driven defaults; kappa=low produces more solvency-driven defaults.

### Calibration

- TODO(verify): Default rate target of ~8% (12-month horizon) is anchored to RBI Financial Stability Report (Jun 2024) MSME NPA ratio ~5-8%. This is an illustrative parameter under our documented assumptions.
- Realised default rates across the 3×3 grid range from ~8-10% in smoke mode.

## Bias mechanism (plausible, not cartoonish)

Women-led and rural firms have **lower bureau coverage** (higher thin-file / missing bureau score rate), so the legacy lender (which relies on bureau score) approves them less, **even though true repayment capacity is independent of gender given features**.

The `bias_strength` parameter (weak=0.5, medium=1.0, strong=1.5) scales the coverage gap:
- Base thin-file share: 35% (configurable)
- Women-led: +6% × bias_strength
- Rural: +6% × bias_strength
- Male-led: −4% × bias_strength
- Metro: −6% × bias_strength

Overall thin-file share is calibrated to 30-40%.

## Legacy policy (stochastic)

Legacy lender score = 0.6 × normalised_bureau + 0.4 × collateral_value_ratio + N(0, 0.15).
Approve if score > 35th-percentile cutoff, **plus 5-10% manual overrides/exceptions** (some below-cutoff firms approved, some above-cutoff firms rejected). This creates overlap so reject inference is identifiable (Blueprint L3).

Outcomes are observed only for approved firms.

## Sensitivity grid (3×3 = 9 configurations)

| kappa \ bias | weak | medium | strong |
|---|---|---|---|
| **high** (0.8) | ✓ | ✓ | ✓ |
| **medium** (0.5) | ✓ | ✓ | ✓ |
| **low** (0.2) | ✓ | ✓ | ✓ |

All 9 configs generate deterministically (seed=42) in both full (20k) and smoke (2k) modes.

## Out-of-time split

- Train: months 1-24
- Test: months 25-36

## Parameters and their sources

| Parameter | Value | Source |
|---|---|---|
| `default_rate_target` | 0.08 | TODO(verify): RBI FSR Jun 2024, MSME NPA ~5-8% |
| `thin_file_share` | 0.35 | Blueprint range 0.30-0.40 |
| `override_rate` | 0.075 | Blueprint range 0.05-0.10 |
| `noise_sd` (legacy score) | 0.15 | Calibrated for realistic score dispersion |
| `k_consecutive` (timing) | 3 months | Illustrative parameter |
| `base_solvency_hazard` | 0.008/month | Calibrated to ~8% 12m default rate |
| `monthly_obligation` | requested_amount / 11 | Rough EMI for 12-month tenor at ~12% |

## Honest limits

1. **Results are method validation, not India-level claims.** Every improvement (e.g. reject-inference lift) is partially a product of the simulation design.
2. **Default mechanism is stylised.** Real MSME defaults involve complex interactions (supply-chain, regulatory, seasonal) that a two-channel hazard model cannot fully capture.
3. **Bias mechanism is one-dimensional.** Real discrimination operates through multiple channels (collateral valuation bias, relationship lending, geographic branch density), not just bureau coverage.
4. **Calibration targets are approximate.** The 8% default rate is an illustrative parameter; actual MSME default rates vary widely by sector, vintage, and product.
5. **Panel signals have perfect alignment.** Real alt-data has missing months, reporting lags, and cross-source inconsistencies that are not modelled here.
6. **No correlation structure.** Firm-to-firm correlations (supply chain, geographic, sectoral) are not modelled in the generator. The stress module (M3) adds these downstream.
7. **Conclusions should be interpreted for direction and relative size** within the context of the assumed parameters.
