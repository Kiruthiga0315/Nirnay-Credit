# Video Demo Script

## 1. Pitch Cut (4 Minutes)

| Time | Screen | Action/Spoken |
|---|---|---|
| 0:00-0:25 | Title | "Credit-gap estimates for Indian MSMEs range from ₹25 lakh crore to ₹60 trillion. Many viable firms are invisible to lenders. Meet Meena." |
| 0:25-1:05 | Borrower Decision (Page 2) | "Legacy policy rejected her due to a thin file. Our engine provides a calibrated PD ({recourse.meena_new_pd}) and three plain-language reasons." |
| 1:05-1:45 | Borrower Decision (Page 2) | *Action: Move a slider.* "The decision flips live. We show recourse options with a cost of {recourse.meena_cost}. The structured schedule sits under the P10 band, reducing default rate by {structuring.lift_matched_vs_flat}." |
| 1:45-2:10 | Borrower Portal | "Meena receives a local-language letter and a 6-month journey curve. The credit officer gets a CAM export." |
| 2:10-2:45 | Portfolio & Fairness (Page 1 & 3) | *Action: Switch to Portfolio.* "At equal loss ({models.legacy_loss_rate}), we unlock {models.extra_approvals_at_equal_loss} extra approvals. The fairness frontier shows the exact cost of inclusion in rupees." |
| 2:45-3:20 | Stress (Page 4) | *Action: Click 'Demonetisation-style shock'.* "Contagion spreads through the supplier-buyer graph. We can immediately see the expected loss and mitigation lever." |
| 3:20-3:40 | Early Warning | "After disbursal, our hazard model flags trouble {early_warning.mean_lead_time_months} months early." |
| 3:40-4:00 | Governance (Page 6) | "This is mapped to FREE-AI advisory guidance. We did not build a better score. We built a lending decision that everyone can trust, and measured where it breaks." |

## 2. Lightning Cut (90 Seconds)

| Time | Screen | Action/Spoken |
|---|---|---|
| 0:00-0:15 | Borrower Decision | "Meet Meena. Rejected by legacy, approved by our engine with clear reasons." |
| 0:15-0:30 | Borrower Decision | *Action: Move slider.* "Live recourse and DSCR-matched structuring." |
| 0:30-0:45 | Portfolio | "We unlock {models.extra_approvals_at_equal_loss} extra approvals at equal loss." |
| 0:45-1:00 | Stress | *Action: Click shock.* "One click replays shocks and measures tail loss." |
| 1:00-1:15 | Governance | "Decision ledger and FREE-AI mapping for regulatory trust." |
| 1:15-1:30 | Outro | "A lending decision that borrowers, officers, and regulators can trust." |

## 3. Deep-Dive Cut (8 Minutes)
*Includes the 4-Minute Pitch Cut, plus:*
- **4:00-5:00:** Model Cockpit (Page 5) - Show ablation, sensitivity grid, and OOT AUC of {models.auc_champion_oot}.
- **5:00-6:00:** Fairness Proxy Audit (Page 3) - Discuss how {fairness.women_led_air} AIR is achieved and audited.
- **6:00-7:00:** Policy Optimizer (Page 1) - Walk through LP relaxation scenarios.
- **7:00-8:00:** Gaming Lab & Story Mode (Page 6) - Run attacks on copied data and show non-repudiation features.
