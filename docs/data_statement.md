---
owner: M1
status: draft
---
# Data statement

## What is this dataset?
This dataset represents a synthetic MSME population with hidden latents and observable noisy signals over a 36-month panel. It includes snapshot entity features (sector, location class, Udyam category) and dynamically generated monthly metrics (revenue, GST turnover, cheque bounces) that are functionally linked to a hidden latent capacity variable. A stochastic legacy policy is applied to generate past decisions (bureau + collateral + noise + overrides).

## Why synthetic data?
Public, real MSME alternative data (like daily cash flow and bank statement granular data) at the entity level does not exist due to privacy and proprietary concerns. Furthermore, synthetic data allows us to measure what real data cannot: the true outcomes for rejected firms (since we have the hidden ground truth). It provides an environment to safely test recourse logic and fairness under known conditions.

## Calibration Sources
- TODO(verify): MSME credit portfolio figures, ticket sizes, and sector mix.
- TODO(verify): Average expected default rates across Udyam categories.
- TODO(verify): Shock magnitudes (e.g. demonetisation and COVID).

## Limits
Results in this repository represent method validation under documented assumptions, not India-level forecasts or empirical claims. The generator relies on specific parameters (like `kappa` for timing vs solvency and `bias_strength`), meaning any improvement (like reject inference lift) is partially a product of the simulation design. Conclusions should be interpreted for direction and size within the context of the assumed parameters.
