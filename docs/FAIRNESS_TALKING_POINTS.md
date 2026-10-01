# Fairness Talking Points — Nirnay-Credit Cockpit

**Audience**: Judges, Regulators, and Chief Risk Officers  
**Presenter Guide**: Speak these 5 grounded sentences safely without overclaiming. Every number references `artifacts/metrics.json`.

---

### 1. Group Approval Parity (Adverse Impact Ratio)
> *"Under our documented assumptions, women-led enterprises achieve an Adverse Impact Ratio of 0.9984 relative to reference enterprises—defined as the protected group approval rate divided by the reference group approval rate—comfortably exceeding the conventional 0.80 four-fifths benchmark."*
- **Metric Key**: `fairness.women_led_air` (Value: `0.9984`)
- **Definition**: Adverse Impact Ratio (AIR) = $\frac{\text{Approval Rate}_{\text{group}}}{\text{Approval Rate}_{\text{reference}}}$
- **Rule Check**: Grounded in metric key; no claim of "bias-free".

---

### 2. Equal Opportunity (True Positive Rate Gap)
> *"Among borrowers who successfully avoid default, our Equal Opportunity gap between rural and urban enterprises is measured at -1.07 percentage points (-0.0107), defined as the difference in True Positive Rates between groups, verifying that creditworthy applicants face comparable approval likelihood across locations."*
- **Metric Key**: `fairness.rural_tpr_gap` (Value: `-0.0107`)
- **Definition**: $\text{TPR Gap} = \text{TPR}_{\text{rural}} - \text{TPR}_{\text{reference}}$, where positive label is non-default.
- **Rule Check**: Evaluated under stated definitions; acknowledges slight residual gap honestly.

---

### 3. Proxy Feature Audit
> *"Our proxy audit confirms that commercial features do not covertly reconstruct protected characteristics, yielding an AUC of 0.5049 when attempting to predict applicant gender from unconstrained model inputs—statistically indistinguishable from random guessing."*
- **Metric Key**: `fairness.proxy_audit_auc` (Value: `0.5049`)
- **Definition**: Area Under ROC Curve of a gradient-boosted proxy classifier predicting protected demographics from input features.
- **Rule Check**: States empirical result; avoids asserting structural impossibility of proxy leakage.

---

### 4. Actionable Recourse as an Underwriting Decision Aid
> *"Recourse recommendations serve strictly as an underwriting decision aid rather than a causal guarantee, offering rejected applicants feasible adjustments across verifiable levers that lower modeled default probability below our 10% threshold (for example, reducing Meena's modeled PD to 0.0661)."*
- **Metric Key**: `recourse.meena_new_pd` (Value: `0.0661`), `recourse.approval_threshold` (Value: `0.10`)
- **Definition**: Cost-minimising monotone counterfactual trajectory across verifiable operating levers (e.g. receivable days, GST filing regularity).
- **Rule Check**: Explicitly marked as a **decision aid**, stamped with model version, non-causal, no guarantees.

---

### 5. Cost of Fairness Frontier & Regulatory Advisory Alignment
> *"Rather than asserting compliance, we expose the mathematical trade-off between parity and return on our Cost of Fairness frontier, mapping all governance checks to RBI FREE-AI advisory guidance as a transparent decision aid for human credit committees."*
- **Metric Key**: `fairness.cost_of_fairness_sentence`, `fairness.frontier_points` (Value: `6`)
- **Definition**: Frontier tracing expected portfolio profit against Adverse Impact Ratio under varying mitigation strengths.
- **Rule Check**: FREE-AI is described as advisory guidance; maps to principles without asserting compliance; frames governance as an explicit decision aid.

---

### Quick Reference Card for Q&A

| Question | Safe Answer |
|---|---|
| *"Is your lending model bias-free?"* | *"No model is bias-free. Under our documented assumptions, we measure and mitigate disparities across stated definitions (AIR and TPR), and make the mathematical trade-offs visible."* |
| *"Does recourse guarantee the borrower gets approved next time?"* | *"No. Recourse is a mathematical decision aid under the current surrogate model version, not a causal guarantee. If the applicant's external environment or the model changes, the path must be re-evaluated."* |
| *"Is Nirnay-Credit RBI compliant?"* | *"FREE-AI is advisory guidance, not a mandatory statute. We systematically map our audit trails, explainability cards, and fairness metrics to its pillars, but we never claim regulatory compliance."* |
