# GitHub setup (10 minutes, done by ONE person, ideally M3)
1. Create the repo (public recommended; the blueprint wants a public repo) and push this folder:
   `git init -b main && git add -A && git commit -m "chore: scaffold" && git remote add origin <url> && git push -u origin main`
2. Invite the other three as collaborators.
3. Replace CODEOWNERS handles: `python scripts/set_owners.py M1=@a M2=@b M3=@c M4=@d`, commit, push.
4. Protect `main`: Settings > Branches > require a pull request, 1 approval, code-owner review, status check **ci**,
   linear history, block force pushes. (Or run `scripts/github_bootstrap.sh` with the GitHub CLI.
   Protection on private repos may need a paid plan.)
5. Settings > General: allow squash merging only; auto-delete head branches.
6. Everyone: `git clone`, `python -m venv .venv`, activate, `pip install -r requirements-dev.txt`,
   `python run_all.py --smoke --keep-going`, `python -m pytest`, `streamlit run app/Home.py`.
7. In Antigravity, open the cloned folder as the workspace so `AGENTS.md` is picked up
   (check the Rules panel; `.agent/rules/00-ps12.md` points to it as a fallback).
