1. Inspect the current git status and git diff (leave untracked files as-is).
2. Stage only relevant modified/added files (do not include unrelated or generated files).
3. Write a clear commit message:
Format:
<type>: <short summary>
* What changed
* Why it changed (if inferable from diff)
Use one of: feat, fix, refactor, perf, docs, test, chore, style.
If the intent is unclear, describe only observable changes. Do not invent reasons.
If secrets, large binaries, or suspicious files are detected, stop and warn instead of committing.
After committing:
* If push=true → push to current branch.
* If create_pr=true → create a PR using the commit summary as title and a short description of changes.
Be concise. No fluff.
