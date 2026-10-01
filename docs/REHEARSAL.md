# Pitch Rehearsal Kit & Stage Run-of-Show

This document establishes the run-of-show, team role distribution, stage resilience checklist, network failure protocol, and scoring rubrics across 3 mandatory rehearsal runs.

---

## 1. Team Roles & Responsibilities

| Role | Team Member | Primary Duties |
| :--- | :--- | :--- |
| **Presenter** | M4 / Primary Speaker | Delivers the core narrative, maintains eye contact with judges, commands pace, opens and closes pitch. |
| **Driver / Pre-loader** | M2 / Co-driver | Operates demo laptop, pre-loads next tabs/screens, executes slider actions smoothly, manages backup toggle if needed. |
| **Hostile Judge** | M1 / Adversary | Simulates aggressive skeptical questioning (governance, causality, leakage, synthetic data limits). |
| **Note-taker & Timer** | M3 / Operator | Tracks stopwatch splits, logs visual/audio glitches, records Q&A points, tallies rubric scores. |

---

## 2. Run-of-Show (3 Rehearsals Schedule)

### Rehearsal 1: Timing & Technical Flow (Dry Run)
* **Goal**: Establish strict 4-minute time discipline and seamless screen-action synchronisation.
* **Target Timing**: 3m 45s (15s buffer).

```text
[0:00 - 0:25] (25s) Slide 1-2 / Problem Hook & Thesis ("Meet Meena, thin file MSME")
[0:25 - 1:05] (40s) Screen 1 (Page 2: Borrower Cockpit) - Legacy Reject vs Calibrated PD
[1:05 - 1:45] (40s) Screen 2 (Page 2: Recourse & Structuring) - Live Slider Flip + DSCR Schedule
[1:45 - 2:10] (25s) Screen 3 (Documents/Portal) - Multi-language Sanction Letter + CAM Export
[2:10 - 2:45] (35s) Screen 4 (Page 1 & 3: Portfolio & Fairness) - Equal Loss Frontier & Rupee Cost
[2:45 - 3:20] (35s) Screen 5 (Page 4: Stress & Contagion) - Demonetisation Shock & Mitigation
[3:20 - 3:40] (20s) Screen 6 (Page 6: Governance) - Hazard Model Lead Time & FREE-AI Alignment
[3:40 - 4:00] (20s) Slide 10 / Wrap-up & Call to Action ("Governed decision spine")
[4:00 - 6:00] (2m) Simulated Hostile Q&A (3 rapid-fire questions)
```

### Rehearsal 2: Adversarial Q&A & Stress Drill
* **Goal**: Defend against hostile judge inquiries without breaking character or exceeding time limits.
* **Focus**: Causal boundaries of recourse, synthetic vs real distributions, privacy guarantees ($\varepsilon = 1.42$).

### Rehearsal 3: Zero-Network Failure Simulation (Battle Ready)
* **Goal**: Full pitch conducted in disconnected airplane mode using pre-rendered offline snapshots and Story Mode.
* **Target Timing**: 3m 50s.

---

## 3. Stage & Hardware Checklist

### Primary & Secondary Hardware
- [ ] **Primary Laptop**: AC power connected, screen sleep disabled, display resolution set to 1080p (1920x1080), browser zoom at 100%.
- [ ] **Backup Laptop**: Identical branch checked out, local dev server running on `http://localhost:8501`.
- [ ] **Mobile Hotspot**: 5G/4G hotspot active, credentials pre-saved on both laptops; primary Wi-Fi set to auto-connect to hotspot.
- [ ] **Pre-recorded Video**: 1080p 60fps MP4 recording stored locally on desktop (`C:\demo\nirnay_demo_4min.mp4`) and on smartphone with VLC/QuickTime ready.
- [ ] **Presentation Deck**: PDF version exported locally in addition to web presentation.

### Demo Presets & Safe Data Paths
- [ ] **Safe Primary Borrower**: `MSME-00001` (Meena - Textile Micro Enterprise, Surendranagar). Fast, predictable recourse convergence (< 150ms).
- [ ] **Fallback Borrowers**: `MSME-00002` (Rajesh - Auto Ancillary), `MSME-00003` (Priya - Food Processing).
- [ ] **Fastest Stress Scenario**: `demonetisation_style` or `gst_rollout_style` (pre-computed graph contagion).
- [ ] **Pre-loaded Browser Tabs**:
  1. `Tab 1`: Home / Executive Dashboard
  2. `Tab 2`: Page 2 — Borrower Decision Cockpit (`MSME-00001` pre-selected)
  3. `Tab 3`: Page 3 — Fairness Studio & Frontier
  4. `Tab 4`: Page 4 — Stress & Macro Contagion
  5. `Tab 5`: Page 6 — Governance & Trust Ledger

---

## 4. Network Failure & Glitch Protocol (Story Mode)

If live cloud connectivity stutters or drops on stage, execute the following pivot immediately:

### Driver Action:
1. Instantly toggle **Story Mode** checkbox in the sidebar or switch to the pre-loaded local tab (`localhost:8501`).
2. If browser completely freezes, open the local MP4 backup video in full screen (`Ctrl+F` / `Cmd+F`).

### Presenter Spoken Recovery Script:
> *"While our cloud node negotiates edge latency, notice that our decision spine is fully deterministic. On this local audit snapshot, every calculation—from Meena's calibrated 6.61% PD to the ₹1.18 Crore contagion mitigation—runs deterministically under our documented assumptions."*

### Key Rules During Glitches:
- **Never apologise or stall**: Transition into the explanation of the mathematical and governance spine.
- **Never reload a broken page repeatedly**: Move immediately to the next pre-loaded tab or offline video.
- **Driver and Presenter remain in sync**: Driver uses hand signal (tap on laptop lid) to indicate local offline mode is active.

---

## 5. Rehearsal Scoring & Evaluation Sheet

| Category | Evaluation Criteria | Target Standard | Rehearsal 1 | Rehearsal 2 | Rehearsal 3 |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Hook & Problem** | Clear articulation of ₹25L Cr gap & thin-file MSME hurdle | ≤ 25s, punchy, no jargon | / 5 | / 5 | / 5 |
| **Live Interaction** | Recourse slider smoothly adjusted, schedule explained | Seamless flip, < 150ms | / 5 | / 5 | / 5 |
| **Portfolio & Fairness**| Rupee cost of fairness explained, equal-loss approvals highlighted | Precise numbers cited | / 5 | / 5 | / 5 |
| **Stress & Governance**| Macro shock contagion demonstrated, FREE-AI alignment stated | Clear defense of limits | / 5 | / 5 | / 5 |
| **Pacing & Timing** | Strict completion within allotted 4-minute window | 3m 40s – 3m 55s | / 5 | / 5 | / 5 |
| **Q&A Defense** | Confident, honest answers referencing documented assumptions | No defensive rambling | / 5 | / 5 | / 5 |
| **Overall Score** | Total points across all 6 dimensions | **≥ 27 / 30** | / 30 | / 30 | / 30 |

---

## 6. Hostile Q&A Quick-Response Matrix

| Hostile Question | Core Defense & Grounding |
| :--- | :--- |
| *"Is recourse offering causal guarantees to the borrower?"* | *"No. Under our documented framework, recourse is a mathematical decision aid showing feasible paths under the trained surrogate, not a causal guarantee."* |
| *"How do you prevent borrowers from gaming alternative levers?"* | *"Our gaming lab explicitly audits feature sensitivity and assigns confidence haircuts to gameable or unverified inputs."* |
| *"Why test on synthetic data rather than live bureau records?"* | *"Synthetic data with calibrated parameters ($\kappa = 0.5$, $\text{bias} = 1.0$) allows full open-source reproducibility and stress testing without privacy leakage."* |
| *"Does this comply with RBI circulars?"* | *"FREE-AI is advisory guidance; we systematically map our audit trails, ledgers, and fairness metrics to its pillars, but never claim formal regulatory compliance."* |
