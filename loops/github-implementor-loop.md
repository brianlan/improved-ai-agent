Execute the following tasks in strict priority order. Complete at most one actionable task per turn, then stop and wait for the next turn.

General rules:
* Use the `gh` CLI for all GitHub queries and updates.
* Be idempotent. Do not repeatedly process the same PR comment, review thread, conflict, issue, branch update, recommended improvement, or follow-up suggestion if it has already been handled.
* Before making any code change, verify:
  - target issue/PR number,
  - current directory,
  - current branch,
  - `git status --short`.
* Never make feature or PR-review changes directly in the main repository checkout. Use the main checkout only for coordination, fetching, and managing worktrees.
* Never mix work for different issues or PRs in the same worktree.
* If local python env is needed, use:
  `/home/rlan/anaconda3/envs/mykik_py311/bin/python`.

Worktree rules:
* Use one dedicated git worktree per issue or PR.
* Keep worktrees under:
  `../worktrees/`
* For a new issue:
  - branch: `agent/issue-<issue-number>-<short-slug>`
  - worktree: `../worktrees/issue-<issue-number>-<short-slug>`
  - create it from the latest `origin/<default-branch>`.
* For an existing PR:
  - use a dedicated worktree for that PR branch,
  - reuse it if it already exists,
  - otherwise fetch the PR branch and create a worktree for it.
* If `git worktree list` shows an existing worktree for the target branch, `cd` into it instead of creating a duplicate.
* If the target worktree has unexpected uncommitted changes, stop and report the situation. Do not overwrite, delete, or stash them.
* Before switching away from a worktree, leave it clean, committed and pushed, or stop and report why it cannot be safely left.

Priority 1: Maintain Existing PRs

Goal:
* Before starting new issues, handle open PRs that need action.
* A PR needs action if it has:
  - unresolved or unaddressed required reviewer feedback,
  - reviewer-agent feedback marked as requiring action,
  - reviewer-agent feedback marked as recommended action,
  - reviewer-agent feedback recommending a follow-up issue,
  - merge conflicts caused by changes in the base branch,
  - or a base-branch update requirement that prevents merging.

Detection:
* Inspect open PRs using `gh`.
* For each candidate PR, check at least:
  - `gh pr view <PR> --json number,title,state,isDraft,author,headRefName,headRefOid,baseRefName,mergeable,mergeStateStatus,reviewDecision,reviewRequests,comments,reviews,latestReviews,commits,statusCheckRollup`
  - `gh api repos/:owner/:repo/pulls/<PR>/comments --paginate`
  - `gh api repos/:owner/:repo/pulls/<PR>/reviews --paginate`
* Do not rely only on `reviewDecision` or `reviewRequests`.
* Empty `reviewDecision`, empty `reviewRequests`, or “No reviews” in the GitHub sidebar does not prove there is no actionable feedback.
* Treat the following as possible actionable feedback:
  - formal PR reviews,
  - review summaries,
  - inline review comments,
  - unresolved review threads,
  - regular PR comments that clearly request or recommend changes,
  - comments containing markers such as:
    - `Agent-Review: reviewer`
    - `Review-Decision: REQUEST_CHANGES`
    - `Review-Decision: COMMENT_ONLY`
    - `Action-Required: true`
    - `Action-Recommended: true`
    - `Follow-Up-Recommended: true`
    - `Review-Commit: <sha>`
* If reviewer and implementor use the same GitHub account, do not rely on author identity alone. Use timestamps, content, markers, and commit history.

Review feedback semantics:
* `REQUEST_CHANGES` or `Action-Required: true` means the feedback must be handled before proceeding to new issues.
* `COMMENT_ONLY` does not automatically mean “no action needed.”
* For COMMENT_ONLY feedback:
  - if `Action-Recommended: true`, evaluate it and either implement it, explicitly defer it, or ask for clarification;
  - if `Follow-Up-Recommended: true`, consider creating a follow-up issue instead of modifying the current PR;
  - if both `Action-Recommended: false` and `Follow-Up-Recommended: false`, treat it as informational unless the text clearly requests action.
* `APPROVE` with no required, recommended, or follow-up action does not require implementation work unless the PR has conflicts, failed checks, or base-branch update issues.

Actionability:
* Reviewer feedback is actionable if:
  - it asks for or recommends a code, test, documentation, behavior, or follow-up change, and
  - it has not been handled by a later commit, a direct explanatory reply, or a follow-up issue.
* Feedback is considered handled if one of the following happened after the feedback:
  - a commit plausibly implemented the requested or recommended change,
  - the implementor replied explaining why it is not being done,
  - the implementor asked for clarification,
  - a follow-up issue was created and linked,
  - or a later reviewer review superseded the feedback.
* If feedback contains `Review-Commit: <sha>`:
  - if the current PR head SHA equals that SHA, the feedback has not been handled by code changes yet;
  - if newer commits exist, inspect whether they plausibly addressed the feedback before deciding what remains.
* To avoid repeated handling, when replying to reviewer feedback include a short machine-readable block such as:

Agent-Review-Handled: implementor
Handled-Review-Commit: <Review-Commit>
Handled-Decision: IMPLEMENTED | DEFERRED | FOLLOW_UP_ISSUE | CLARIFICATION_REQUESTED
Handled-Reason: <brief reason>

Merge/base-branch maintenance:
* A PR also needs action if it was previously approved or otherwise ready, but is now not mergeable because the base branch changed.
* Treat merge/base-branch maintenance as actionable when:
  - `mergeable` is `CONFLICTING`,
  - `mergeStateStatus` indicates conflict or dirty state,
  - GitHub says the branch cannot be merged cleanly,
  - or the branch is behind the base branch and branch protection requires it to be updated.

Priority within Priority 1:
Handle the highest-priority actionable PR task in this order:
1. Merge conflicts or base-branch updates that block merging.
2. `REQUEST_CHANGES` or `Action-Required: true`.
3. Failed checks caused by the PR.
4. `COMMENT_ONLY` with `Action-Recommended: true`.
5. `Follow-Up-Recommended: true`.
6. Other unresolved review threads or clearly actionable comments.

Handling:
* Select the highest-priority actionable PR and handle only that PR this turn.
* Use or create the dedicated PR worktree.
* Inside the correct PR worktree:
  1. Fetch latest refs:
     `git fetch origin`
  2. Ensure the worktree is on the PR branch and clean.
  3. Inspect reviewer feedback, review comments, regular PR comments, commits, checks, and mergeability.
  4. If the PR is blocked because the base branch changed:
     - fetch the latest base branch from `origin/<baseRefName>`,
     - merge `origin/<baseRefName>` into the PR branch by default,
     - use rebase only if the repository convention clearly prefers rebase,
     - resolve conflicts if any,
     - run relevant validation commands,
     - commit the merge/conflict-resolution result if needed,
     - push the PR branch.
  5. If feedback is required:
     - implement the requested change if reasonable and safe,
     - or reply explaining why the requested change is unnecessary, obsolete, incorrect, or unsafe,
     - or ask for clarification if the feedback is ambiguous.
  6. If feedback is COMMENT_ONLY with `Action-Recommended: true`:
     - evaluate the suggestion instead of ignoring it,
     - implement it if it is small, clearly beneficial, and low risk,
     - otherwise reply that it is being deferred and briefly explain why,
     - if appropriate, create and link a follow-up issue.
  7. If feedback has `Follow-Up-Recommended: true`:
     - create a follow-up issue if the suggestion is valid but outside the current PR scope,
     - link the follow-up issue in a PR reply,
     - do not unnecessarily expand the current PR scope.
  8. If tests fail:
     - fix failures related to the PR changes when possible,
     - otherwise document the failure clearly in a PR reply.
  9. After pushing changes or replying, summarize what was addressed and include the handling marker when useful.

Completion:
* After pushing a fix, resolving a conflict, updating the PR branch from the base branch, replying to a reviewer, creating a follow-up issue, or asking for clarification, stop and wait for the next turn.
* If no open PR needs action, proceed to Priority 2.

Priority 2: Tackle Unassigned Issues

Goal:
* Start one new issue only when no existing PR needs maintenance.

Issue selection:
* Use `gh` to find one open issue that:
  - is unassigned,
  - has no linked PR,
  - is not already claimed by another active agent or contributor,
  - is not already being handled by an existing branch or worktree,
  - appears implementable without major product clarification.
* Prefer older, clearly scoped issues over vague or newly active issues.

Handling:
1. Claim the issue first, for example by assigning it to yourself if possible or commenting that you are starting work.
2. Re-check that no linked PR or competing claim appeared after claiming.
3. Draft a concise implementation plan.
4. Create or reuse the dedicated issue worktree.
5. Verify correct directory, branch, and clean or expected `git status --short`.
6. Implement the change.
7. Run backend tests, frontend tests, and Playwright E2E tests.
   - If a test command does not exist or cannot be determined, mention that in the PR body.
   - If tests fail due to your change, fix them before opening the PR.
   - Do not open a PR with known related test failures unless clearly documented.
8. Commit the changes with a clear message referencing the issue.
9. Push the branch.
10. Open a PR linked to the issue, including:
    - summary,
    - implementation notes,
    - test results,
    - linked issue number.

Completion:
* After opening one PR, stop and wait for the next turn.

Priority 3: Idle

* If neither Priority 1 nor Priority 2 applies, skip this turn.
* Do not create unnecessary branches, worktrees, comments, commits, or PRs while idle.