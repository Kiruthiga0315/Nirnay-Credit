# MSME Lending Model Card

## Intended Use
This model is intended to be used as a decision aid for underwriting MSME loans. It provides a calibrated Probability of Default (PD) over a 12-month horizon. It should NOT be used for fully automated decisions without human oversight (especially for overrides and exceptions). It strictly maps to advisory guidance rather than strict "guaranteed approval" or "RBI-compliant" claims.

## Data
- **Training**: Origin months 1-24, using approved-only outcomes to mirror typical lending data availability.
- **Testing**: Out-of-time (OOT) test set covering origin months 25-36.
- **Features**: Consists of traditional credit bureau scores and alternative data (e.g. GST filings, digital invoices).
- **Protected Attributes**: Attributes such as `owner_gender` and `location_class` are strictly excluded from the models to prevent direct disparate treatment.

## Models
- **Champion Model**: Logistic regression on WoE-binned features. Easily interpretable and stable, serving as the benchmark standard.
- **Challenger Model**: LightGBM tree-based classifier with monotonic constraints. Captures non-linearities while enforcing sensible relationships (e.g., higher receivable days monotonically increases risk).
- **Calibration**: Isotonic Regression fitted on a held-out slice of the training data ensures predicted probabilities are realistic default rates.

## Metrics
- **Champion AUC OOT**: {{ models.auc_champion_oot }}
- **Challenger AUC OOT**: {{ models.auc_challenger_oot }}
- **Challenger Gini OOT**: {{ models.gini_challenger_oot }}
- **Challenger Expected Calibration Error (ECE)**: {{ models.ece_challenger }}
- **Challenger Population Stability Index (PSI)**: {{ models.psi_challenger }}

### External Validity
- **External AUC Challenger**: {{ external.auc_challenger }}
- **External KS Challenger**: {{ external.ks_challenger }}
- **External ECE Challenger**: {{ external.ece_challenger }}

## Limits
1. Results are method validation, not India-level claims. Every improvement is partially a product of the simulation design.
2. Default mechanism is stylised. Real MSME defaults involve complex interactions.
3. Calibration targets are approximate. Actual MSME default rates vary widely.
