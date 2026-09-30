# Gates and Definition of Done (from docs/ideas/PS12_36h_Elaborate_Plan.md)

| Gate | Hour | Passes when |
|---|---|---|
| Gate 1 | H3 | contracts frozen; every function returns stub data; all 8 pages render from stubs; CI green; hello-world URL live |
| Gate 2 | H10 | real `score()` + `artifacts/metrics.json` exist; deployed URL shows Page 2 with real Meena numbers |
| Gate 3 (walking skeleton) | H14-H16 | Meena flows end-to-end on the deployed URL: reject -> reasons -> recourse -> structured loan -> scoreboard -> one shock. If not true at H16: stop features, fix integration |
| Feature freeze | H26 | no new features; bugs, copy, performance, polish only |
| Rule of two | H30-H34 | contract/main changes need a second approver |
| Submit | H35 | buffer; no code changes in the final 90 minutes except critical fixes |

## Page Definition of Done
See "Acceptance Criteria" in the 36h plan (Section 5). Global: deployed URL works on phone and laptop; cold start < 15 s;
no stack trace after hard refresh; every chart captioned; INR formatting everywhere.

## Cut order if behind
F15 Copilot -> F11 gaming toggles -> F10 journey -> languages 4->2 -> F9 EW UI -> F8 optimizer -> contagion animation.
Never cut: Borrower Decision, Legacy-vs-Ours scoreboard, fairness frontier, stress replays, governance, external validity, story mode.
