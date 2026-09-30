# Antigravity prompt pack (PS12)

How to use
1. Open the cloned repo as the Antigravity workspace (so AGENTS.md is loaded).
2. Pick the model shown in the prompt header, paste the prompt block (everything inside the fence), send once.
3. When the agent finishes, open a NEW conversation on **Gemini 3.8 Flash**, paste the matching VERIFY block.
4. Compare the result to the "Expected outputs" table. Only when every row is green: open the PR.
5. Each member runs only their own prompts. Prompts are self-contained, so if someone's quota runs out,
   a teammate can run that prompt on their own account on the same branch name + their own clone, then push.

Model key (Antigravity model picker on Google AI Pro; verify names in your picker, the list changes)
| Code | Model | Use for |
|---|---|---|
| **OPUS** | Claude Opus 4.6 (thinking) | the 5 correctness-critical pastes only (generator/bias, reject inference, recourse+DSCR, fairness, contagion) |
| **PRO** | Gemini 3.1 Pro (High) | multi-file module builds, pipelines, heavy UI work |
| **SONNET** | Claude Sonnet 4.6 (thinking) | balanced logic + integration + audits |
| **FLASH** | Gemini 3.8 Flash | config plumbing, docs, templates, tests, ALL verification prompts |

Quota strategy (Pro plans throttle, so spend deliberately)
- Gemini models and Claude/GPT models have separate quota pools: alternate between them.
- One paste per member per phase (two only where the prompt says so). Each paste already breaks work into tasks
  with commit points, so do not re-paste; reply `continue T3` if the agent stops early.
- If a Claude pool is empty, run the same prompt on PRO. If the Gemini pool is empty, use SONNET. Do not use GPT-OSS-120b.
- Verification always on FLASH. Do not let agents re-read the whole repo repeatedly.

Safe rules when an agent misbehaves: `git diff --stat` after every task; if it touched files you do not own,
`git checkout -- <file>` and re-prompt with "You edited files you do not own; revert and continue".

Numbers in the "Expected outputs" tables are SANITY BANDS from the blueprint logic, not targets. If a result is outside a band,
investigate why (leakage, bug, assumption); never tune it into range.

## Routing table (who pastes what, on which model)
| Phase | M1 | M2 | M3 | M4 |
|---|---|---|---|---|
| 0 Setup (H0-3) | PRO | SONNET | FLASH | PRO |
| 1 Data & models (H3-10) | 1A OPUS, 1B PRO | SONNET | PRO | SONNET |
| 2 Decision layer (H10-16) | OPUS | 2A OPUS, 2B PRO | 2A OPUS, 2B PRO | PRO |
| 3 Depth (H16-26) | PRO | 3A OPUS, 3B SONNET | 3A PRO, 3B SONNET | 3A PRO, 3B SONNET |
| 4 Hardening (H26-32) | SONNET | SONNET | FLASH | PRO |
| 5 Rehearsal (H32-36) | SONNET | FLASH | FLASH | FLASH |
Opus pastes in total: 5 (M1 x2, M2 x2, M3 x1). Every VERIFY prompt runs on FLASH.
