# M4 QA Prep

This document contains Q&A preparation for the final presentation, based on Section 11 of the Blueprint.

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

## M4 Specific UI Checks
- **Design System**: Ensure font, teal accent color, and spacing are consistent across all views.
- **Page Layout**: Check the sidebar and page headers.
- **Documents**: Confirm that `core.documents.make_cam` and `core.documents.make_letter` return valid HTML.
- **Multilingual Support**: Ensure English, Hindi, Tamil, and Marathi letters render properly without translation errors.
- **Error States**: Verify `safe_call` masks Python exceptions with a friendly warning.
