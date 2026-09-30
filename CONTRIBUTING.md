# Working agreement (read once, follow always)

## The one idea
**Every file has exactly one owner.** Merge conflicts only happen when two people edit one file, so we
never do. Ownership map: `docs/OWNERSHIP.md` (enforced by `.github/CODEOWNERS`).

## Daily flow
    git checkout main && git pull
    git checkout -b m2/p2-recourse           # m<member>/<phase>-<topic>
    ... work only in your files ...
    ruff check . && python -m pytest && python run_all.py --smoke --keep-going
    git add -A && git commit -m "m2(recourse): monotone lever search"
    git pull --rebase origin main            # every time, before pushing
    git push -u origin m2/p2-recourse        # open a PR, squash-merge after CI is green + 1 review

- **Merge at least every 2 hours.** Small PRs. `main` is always runnable (CI enforces it).
- **Reviewer** = any other member; M3 is merge captain (watches `main` is green).
- **Commit format:** `m<N>(<area>): <what>`.

## Things that cause conflicts, and the rule that prevents them
| Hot spot | Rule |
|---|---|
| `core/contracts.py`, `paths.py`, `reference.py`, `__init__.py`, `docs/CONTRACTS.md`, `docs/ARTIFACTS.md` | Frozen at Gate 1 (H3). Change only via PR labelled `contract-change` with **all 4 approvals**, announced in the group chat. The same PR updates the stubs and tests. |
| `requirements.txt`, `Makefile`, `run_all.py`, CI | M3 only. Need a package? Message M3; a 1-line PR lands in minutes. |
| Metrics / claims / known issues | One file **per member** (`docs/claims/m2.md`, `artifacts/metrics/<namespace>.json`). M4 compiles. |
| Pages | One file per page, one owner per page. Shared look-and-feel lives in `app/components/` (M4 only). |
| Generated data | Git-ignored. Everyone rebuilds with `python run_all.py`. Only M3 commits `demo_snapshot/`. |
| Notebooks | Not in git. Export logic into `core/`. |

## If you get a merge conflict
You edited a file you don't own. Abort (`git merge --abort` / `git rebase --abort`), revert that file
(`git checkout origin/main -- <file>`), and file a request with the owner instead.

## Rule of two (H30-H34)
No change to contracts or `main` without a second person's approval. From H34, only critical fixes.

## Before every PR
- [ ] only my files  - [ ] contract untouched  - [ ] `ruff` + `pytest` + `--smoke` green
- [ ] new numbers logged in `docs/claims/<me>.md`  - [ ] rebased on latest `main`

## Channel etiquette
Post one line when: a contract changes, `main` breaks, you merge something others depend on, or a gate is passed.
