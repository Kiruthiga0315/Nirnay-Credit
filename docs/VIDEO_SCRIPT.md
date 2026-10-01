# Video Demo Script & Subtitle Track

This document contains the timed spoken script, screen actions, and metrics bindings for all three presentation cuts, along with the master `.srt` subtitle track for recorded backup playback.

---

## 1. Master Pitch Cut (4 Minutes)

| Timestamp | Visual / Page Target | Driver Screen Action | Presenter Spoken Track | Metrics Key Binding |
| :--- | :--- | :--- | :--- | :--- |
| **0:00 - 0:25** | Title / Slides 1-3 | Display Title Slide; fade to problem context. | *"Credit-gap estimates for Indian MSMEs range from ₹20 to ₹25 Lakh Crore. Over 85% of viable micro-enterprises are invisible to formal lenders due to thin credit files. Today we introduce Nirnay-Credit: a governed decision spine that turns invisible MSMEs into bankable borrowers."* | External: IFC / UK Sinha Committee |
| **0:25 - 1:05** | Page 2: Borrower Cockpit | Select borrower `MSME-00001` (Meena). Highlight legacy decline vs calibrated assessment. | *"Meet Meena, running a textile micro-enterprise in Surendranagar. Under legacy bureau-only rules, she was rejected with an arbitrary cutoff. Our engine evaluates non-traditional cash-flow indicators, computing a calibrated probability of default of {recourse.meena_new_pd} with clear, plain-language contributing factors."* | `{recourse.meena_new_pd}` (0.0661) |
| **1:05 - 1:45** | Page 2: Recourse & Structuring | Drag the receivable days slider to 45 days. Click 'Recalculate Schedule'. | *"Rather than a flat rejection, we provide actionable recourse. By reducing receivable delay by 15 days—at an estimated cost metric of {recourse.meena_cost}—her decision flips to approval. Next, our DSCR-matched structuring shapes repayments around seasonal cash flows, achieving a {structuring.lift_matched_vs_flat} default rate reduction versus flat EMIs."* | `{recourse.meena_cost}` (15.0), `{structuring.lift_matched_vs_flat}` (28.2%) |
| **1:45 - 2:10** | Borrower Portal & CAM | Toggle multilingual sanction letter (Hindi / Tamil) and open CAM HTML preview. | *"Meena receives a transparent sanction letter in her regional language explaining her terms, while the credit committee receives a fully automated Credit Assessment Memorandum with cryptographic hashes."* | N/A |
| **2:10 - 2:45** | Page 1 & 3: Portfolio & Fairness | Switch to Portfolio Dashboard, then Fairness Studio. Hover over the Fairness Frontier. | *"At portfolio scale, maintaining equal credit loss of {models.legacy_loss_rate}, our model unlocks {models.extra_approvals_at_equal_loss} additional approvals. In our Fairness Studio, we achieve an Adverse Impact Ratio of {fairness.women_led_air} for women-led enterprises and explicitly price the cost of inclusion in Rupees."* | `{models.legacy_loss_rate}` (7.5%), `{models.extra_approvals_at_equal_loss}` (20), `{fairness.women_led_air}` (0.9984) |
| **2:45 - 3:20** | Page 4: Stress & Contagion | Select 'Demonetisation-style shock'. Click 'Propagate Contagion'. | *"When macroeconomic shocks hit, our graph propagation engine models buyer-supplier contagion. We quantify tail expected shortfall and evaluate structural liquidity mitigations in real time."* | `{stress.demonetisation_style.EL}` |
| **3:20 - 3:40** | Page 6: Governance & EW | Scroll to Hazard Early Warning chart & FREE-AI mapping matrix. | *"Post-disbursal, our hazard model flags emerging distress with a mean lead time of {early_warning.mean_lead_time_months} months, enabling proactive restructuring before default."* | `{early_warning.mean_lead_time_months}` (2.18m) |
| **3:40 - 4:00** | Slide 10: Conclusion | Switch to final roadmap slide. | *"Nirnay-Credit does not claim 'bias-free' AI or 100% accuracy. We deliver a mathematically governed, stress-tested decision aid mapped to RBI FREE-AI advisory guidance that borrowers, officers, and regulators can trust."* | Governance Pillar |

---

## 2. Lightning Pitch Cut (90 Seconds)

| Timestamp | Visual Target | Spoken Track |
| :--- | :--- | :--- |
| **0:00 - 0:20** | Page 2: Borrower Cockpit | *"Indian MSMEs face a ₹25 Lakh Crore credit gap because legacy bureau models reject thin-file borrowers. Meet Meena: rejected by legacy rules, approved by our calibrated decision engine with clear contributing factors."* |
| **0:20 - 0:40** | Page 2: Recourse & Structuring | *"We provide actionable counterfactual recourse and seasonal DSCR repayment structuring that yields a 28.2% default reduction over rigid EMIs."* |
| **0:40 - 1:00** | Page 1 & 3: Portfolio & Fairness | *"At portfolio scale, we unlock 20 extra approvals at equal loss while maintaining a 0.9984 Adverse Impact Ratio for women-led enterprises."* |
| **1:00 - 1:15** | Page 4 & 6: Stress & Trust | *"We model supply-chain contagion under macro shocks and audit all decisions against RBI FREE-AI governance pillars."* |
| **1:15 - 1:30** | Conclusion | *"A transparent, stress-tested lending decision engine built for the next 100 million enterprises."* |

---

## 3. Technical Deep-Dive Cut (8 Minutes)

* **0:00 - 4:00**: Master Pitch Cut (Full walkthrough).
* **4:00 - 5:00**: **Model Cockpit & Reject Inference (Page 5)** — Examination of Champion vs Challenger performance, 3-parameter Weibull calibration curves, and OOT evaluation (`models.auc_champion_oot` = 0.611).
* **5:00 - 6:00**: **Fairness Studio & Proxy Auditing (Page 3)** — Demonstration of proxy leakage auditing against protected attributes and Linear Programming optimization along the Pareto frontier.
* **6:00 - 7:00**: **Contagion Graph & Stress Simulation (Page 4)** — Interactive tuning of sector shock vectors, network propagation depth, and dynamic liquidity buffers.
* **7:00 - 8:00**: **Governance, Cryptographic Ledger & Gaming Lab (Page 6)** — Adversarial perturbation testing against gameable inputs and immutable SHA-256 decision ledger audit.

---

## 4. Master Subtitles Track (`subtitles.srt`)

```text
1
00:00:01,000 --> 00:00:06,000
Credit-gap estimates for Indian MSMEs range between 20 to 25 Lakh Crore Rupees.

2
00:00:06,500 --> 00:00:12,000
Over 85% of viable micro-enterprises remain excluded due to thin bureau credit files.

3
00:00:12,500 --> 00:00:18,500
Meet Meena: a textile entrepreneur in Surendranagar rejected by conventional cutoff rules.

4
00:00:19,000 --> 00:00:25,000
Our decision engine evaluates non-traditional cash flows, computing a calibrated PD of 6.61%.

5
00:00:25,500 --> 00:00:32,000
Instead of a flat rejection, we provide actionable recourse: shortening receivable delays flips the decision.

6
00:00:32,500 --> 00:00:39,000
Our DSCR-matched cash flow structuring reduces default risk by 28.2% compared to flat EMIs.

7
00:00:39,500 --> 00:00:46,000
Meena receives a clear sanction letter in her native language while officers receive an automated CAM.

8
00:00:46,500 --> 00:00:53,000
At portfolio scale, we unlock 20 additional approvals at equal loss with a 0.9984 women-led AIR.

9
00:00:53,500 --> 00:01:00,000
Under macroeconomic shocks, our graph engine simulates contagion and proves liquidity mitigation.

10
00:01:00,500 --> 00:01:07,000
Post-disbursal hazard tracking flags distress over 2 months early for timely intervention.

11
00:01:07,500 --> 00:01:14,000
Nirnay-Credit: a mathematically governed lending cockpit aligned with RBI FREE-AI guidance.
```
