# Function contracts (frozen at Gate 1, H3)
Types live in `core/contracts.py`. The UI calls only these functions. Reference borrower: **Meena, `MSME-00001`**
(fixture: `configs/personas/meena.json`).

| Function | Module / owner | Input | Output (TypedDict) |
|---|---|---|---|
| `score(borrower)` | models / M1 | dict or id | `ScoreResult` {pd, pd_band, reasons[3], data_confidence, model_version} |
| `recourse(borrower, levers=None)` | recourse / M2 | dict or id | `RecourseResult` {actions[], new_pd, cost, months, valid_until_model} |
| `structure(borrower, target_dscr=1.25)` | structuring / M2 | dict or id | `StructureResult` {schedule[], p10_band[], default_flat, default_matched} |
| `fairness_report(policy=None)` | fairness / M2 | policy dict | `FairnessReport` {by_group, adverse_impact_ratio, tpr_gap, intersectional} |
| `optimize(policy_params=None)` | optimizer / M2 | budget, caps, floor | `OptimizeResult` {approved_ids, expected_profit, expected_loss, exposure, fairness_gap} |
| `stress(scenario, params=None)` | stress / M3 | scenario id | `StressResult` {expected_loss, es95, segment_losses, first_failing_segment, tornado} |
| `watchlist(month=25)` | early_warning / M3 | month | `list[WatchRow]` |
| `trust(borrower)` / `attack(kind)` | trust / M3 | dict / attack id | `TrustResult` / `AttackResult` |
| `make_cam(borrower)` / `make_letter(borrower, lang)` | documents / M4 | dict, lang | `bytes` (HTML) |

## Rules
1. Signatures and return keys never change without the `contract-change` process (all 4 approvals).
2. Adding an OPTIONAL key to a result is allowed only through that same process (UI must not break).
3. Real implementations replace stubs inside the owner's module. `tests/test_contracts.py` must stay green.
4. Cross-module calls go through the public functions above (or a `core.<module>` helper the other owner
   documents in its docstring). Never import another module's private helpers.
5. Every function has a docstring with an example and a unit test on Meena.
6. Performance budgets: `score` < 0.2 s per borrower; slider re-score path < 1 s; any page cold start < 15 s.
