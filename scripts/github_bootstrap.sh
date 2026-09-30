#!/usr/bin/env bash
# OPTIONAL. Run once by the repo creator (needs GitHub CLI `gh`, logged in).
# Branch protection on PRIVATE repos may need a paid GitHub plan; keep the repo public
# (the blueprint wants a public repo anyway) or protect main by team discipline.
set -euo pipefail
NAME="${1:-ps12}"
gh repo create "$NAME" --public --source=. --remote=origin --push
for l in "contract-change:d93f0b" "blocker:b60205" "phase-0:c5def5" "phase-1:c5def5" "phase-2:c5def5" \
         "phase-3:c5def5" "phase-4:c5def5" "phase-5:c5def5"; do
  gh label create "${l%%:*}" --color "${l##*:}" --force
done
gh api -X PUT "repos/{owner}/{repo}/branches/main/protection" --input - <<JSON
{
  "required_status_checks": {"strict": true, "contexts": ["ci"]},
  "enforce_admins": false,
  "required_pull_request_reviews": {"required_approving_review_count": 1, "require_code_owner_reviews": true},
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false
}
JSON
gh repo edit --delete-branch-on-merge --enable-squash-merge --enable-merge-commit=false --enable-rebase-merge=false
echo "Done. Now invite M2, M3, M4 as collaborators (Settings > Collaborators)."
