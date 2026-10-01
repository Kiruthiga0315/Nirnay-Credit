# Release & Submission Checklist (Owner: M3)

Project: **PS12 Nirnay-Credit** (Hackconquest, Aether 2026).
Derived from **Blueprint Section 13** & **Phase 5 Submission Gates**.

Every item has an assigned owner. All checkboxes must be verified prior to final submission freeze.

---

## 1. Submission & Organizer Confirmation
- [x] **Format & Deadline Confirmed:** Confirmed submission guidelines (online portal link, deck upload format, live pitch / recorded video requirements). | **Owner: M4**
- [x] **Submission Deadline Target:** Submission prepared early (by H35, 90 mins before freeze) to allow buffer for network / portal issues. | **Owner: M3**

---

## 2. Repository & Documentation Readiness
- [x] **Public Repository & Clean Git History:** Repository is accessible with clean linear commit history and no temporary/large unversioned files. | **Owner: M3**
- [x] **Comprehensive README:** Problem statement, architecture diagram, data statement, quick-start, results table, and honest limits clearly documented. | **Owner: M4**
- [x] **Model Card & Data Statement:** [docs/model_card.md](file:///Users/haseena/Nirnay-Credit/docs/model_card.md) and [docs/data_statement.md](file:///Users/haseena/Nirnay-Credit/docs/data_statement.md) complete with synthetic generator disclosures. | **Owner: M1**
- [x] **Deploy Guide & Release Notes:** [docs/DEPLOY.md](file:///Users/haseena/Nirnay-Credit/docs/DEPLOY.md) details local, cloud, and offline playback steps. | **Owner: M3**

---

## 3. Live Deployment & Fallback Verification
- [x] **Public Live URL Active:** Streamlit Community Cloud app deployed and verified accessible at https://nirnay-credit-fb5mqsdhqu8qkyhj7un2fr.streamlit.app/. | **Owner: M3**
- [x] **Second Device & Network Tested:** Deployed URL tested on a secondary mobile device over cellular 4G/5G data with cold start < 15s. | **Owner: M3**
- [x] **Local Offline Fallback:** [scripts/offline_demo.sh](file:///Users/haseena/Nirnay-Credit/scripts/offline_demo.sh) and [scripts/offline_demo.bat](file:///Users/haseena/Nirnay-Credit/scripts/offline_demo.bat) tested in dry-run mode using [demo_snapshot/artifacts/](file:///Users/haseena/Nirnay-Credit/demo_snapshot/artifacts/). | **Owner: M3**
- [x] **Backup Demo Video:** 3-4 minute high-definition walkthrough recorded and saved locally on at least two team laptops/phones (`demo_snapshot/video/backup_demo.mp4` / external drive). | **Owner: M4**

---

## 4. Evidence, Numbers & Integrity
- [x] **`metrics.json` Backs Every Claim:** Every single number on the deck, README, and narrative is traceable to [artifacts/metrics.json](file:///Users/haseena/Nirnay-Credit/artifacts/metrics.json) (enforced by `pytest tests/test_claims.py`). | **Owner: M1 / M3**
- [x] **Banned Phrases Audit Clean:** Grep confirms zero occurrences of unscientific/overclaiming language (`bias-free`, `unbiased`, `99% accurate`, `guaranteed approval`, `RBI-compliant`). | **Owner: M2**
- [x] **Advisory Wording Enforced:** FREE-AI is consistently framed as an advisory guidance mapping, not a compliance badge. | **Owner: M2**

---

## 5. Pitch Deck & Narrative Assets
- [x] **8-Slide Pitch Deck Finalized:** Problem $\rightarrow$ Insight $\rightarrow$ Solution Spine $\rightarrow$ Live Product $\rightarrow$ Evidence (Scoreboard + External Validity) $\rightarrow$ Fairness & Stress $\rightarrow$ Governance/FREE-AI $\rightarrow$ ₹ Economics & Impact. | **Owner: M4**
- [x] **Hostile Judge Q&A Prepared:** 30 rigorous defense questions and top-5 vulnerability bridge sentences documented in [docs/HOSTILE_JUDGE.md](file:///Users/haseena/Nirnay-Credit/docs/HOSTILE_JUDGE.md). | **Owner: M1**
- [x] **Fairness & Recourse Talking Points:** Presenter quick-reference sheet finalized in [docs/FAIRNESS_TALKING_POINTS.md](file:///Users/haseena/Nirnay-Credit/docs/FAIRNESS_TALKING_POINTS.md). | **Owner: M2**

---

## 6. Rehearsals & Team Run-of-Show
- [x] **Rehearsal 1 (Timing & Flow):** Complete dry run of 4-minute pitch and live dashboard navigation with timer. | **Owner: All (M1-M4)**
- [x] **Rehearsal 2 (Hostile Judge Interruption):** Simulated Q&A with hostile judge persona testing technical edge cases. | **Owner: All (M1-M4)**
- [x] **Rehearsal 3 (Offline / Failure Drill):** Simulated live network failure switching seamlessly to Story Mode / offline demo. | **Owner: All (M1-M4)**
- [x] **Role Assignments Locked:** Presenter (M4), Driver/Pre-loader (M3), Technical Defender (M1), Ethics/Governance Defender (M2). | **Owner: M4**

---

## 7. Submission Sign-off (Rule of Two)
- [x] **Primary Sign-off (M3 Platform/Release):** Build green, test suite clean, release snapshot committed.
- [x] **Secondary Sign-off (M4 Story/Submission):** Narrative aligned, deck ready, submission link verified.
