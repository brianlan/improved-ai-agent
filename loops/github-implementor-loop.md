Execute the following tasks in strict priority order. Complete at most one actionable task per turn, then stop and wait for the next turn.

General rules:
* Use the `gh` CLI for all GitHub queries and updates.
* Be idempotent. Do not repeatedly process the same PR comment, review thread, conflict, issue, branch update, recommended improvement, follow-up suggestion, or merge-ready PR if it has already been handled.
* Before making any code change, verify:
  - target issue/PR number,
  - current directory,
  - current branch,
  - `git status --short`.
* Never make feature or PR-review changes directly in the main repository checkout. Use the main checkout only for coordination, fetching, and managing worktrees.
* Never mix work for different issues or PRs in the same worktree.
* Never push directly to the default branch.
* Never merge a PR unless it satisfies every auto-merge gate listed below.
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
* Before starting new issues, handle open PRs that need maintenance or are safely eligible for automatic merge.
* A PR needs action if it has:
  - unresolved or unaddressed required reviewer feedback,
  - reviewer-agent feedback marked as requiring action,
  - reviewer-agent feedback marked as recommended action,
  - reviewer-agent feedback recommending a follow-up issue,
  - failed checks caused by the PR,
  - merge conflicts caused by changes in the base branch,
  - a base-branch update requirement that prevents merging,
  - or a valid reviewer approval that explicitly allows automatic merge.

Detection:
* Inspect open PRs using `gh`.
* For each candidate PR, check at least:
  - `gh pr view <PR> --json number,title,state,isDraft,author,headRefName,headRefOid,baseRefName,mergeable,mergeStateStatus,reviewDecision,reviewRequests,comments,reviews,latestReviews,commits,statusCheckRollup,labels,autoMergeRequest`
  - `gh api repos/:owner/:repo/pulls/<PR>/comments --paginate`
  - `gh api repos/:owner/:repo/pulls/<PR>/reviews --paginate`
* Do not rely only on `reviewDecision` or `reviewRequests`.
* Empty `reviewDecision`, empty `reviewRequests`, or “No reviews” in the GitHub sidebar does not prove that there is no actionable feedback.
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
    - `Review-Decision: APPROVE`
    - `Action-Required: true`
    - `Action-Recommended: true`
    - `Follow-Up-Recommended: true`
    - `Merge-Allowed: true`
    - `Auto-Merge-Allowed: true`
    - `Review-Commit: <sha>`

Review feedback semantics:
* `REQUEST_CHANGES` or `Action-Required: true` means the feedback must be handled before proceeding to new issues or merging.
* `COMMENT_ONLY` does not automatically mean “no action needed.”
* For COMMENT_ONLY feedback:
  - if `Action-Recommended: true`, evaluate it and either implement it, explicitly defer it, or ask for clarification;
  - if `Follow-Up-Recommended: true`, consider creating a follow-up issue instead of modifying the current PR;
  - if both `Action-Recommended: false` and `Follow-Up-Recommended: false`, treat it as informational unless the text clearly requests action.
* `APPROVE` with no required, recommended, or follow-up action does not require implementation work unless the PR has conflicts, failed checks, base-branch update issues, or is eligible for safe auto-merge.
* `Merge-Allowed: true` only means the reviewer thinks the PR is not blocked from a human/manual merge perspective.
* `Merge-Allowed: true` alone is NOT permission for this agent to merge.
* `Auto-Merge-Allowed: true` means the reviewer believes the PR may be safe for automatic merge, but this agent must still independently verify every auto-merge gate before merging.

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
* A PR needs maintenance if it was previously approved or otherwise ready, but is now not mergeable because the base branch changed.
* Treat merge/base-branch maintenance as actionable when:
  - `mergeable` is `CONFLICTING`,
  - `mergeStateStatus` indicates conflict or dirty state,
  - GitHub says the branch cannot be merged cleanly,
  - or the branch is behind the base branch and branch protection requires it to be updated.
* Base-branch maintenance means updating the PR branch from the base branch. It does NOT mean merging the PR into the default branch.
* To update a PR branch:
  - fetch the latest base branch from `origin/<baseRefName>`,
  - merge `origin/<baseRefName>` into the PR branch by default,
  - use rebase only if the repository convention clearly prefers rebase,
  - resolve conflicts if any,
  - run relevant validation commands,
  - commit the merge/conflict-resolution result if needed,
  - push the PR branch.

Safe auto-merge policy:
* Automatic PR merge is allowed only when ALL auto-merge gates pass.
* Never merge based on intuition, convenience, or approval alone.
* Never merge if any gate cannot be verified.
* Never merge a PR by locally merging into the default branch or pushing to the default branch.
* If merging is allowed, use GitHub PR merge through `gh pr merge`.
* Use the repository's established merge method if it is obvious from prior PRs.
* If the repository's merge method is unclear, do not auto-merge; leave a short PR comment or report that the PR is merge-ready but merge method is unclear.

Auto-merge gates:
A PR may be automatically merged only if ALL of the following are true:

1. PR state and target:
   - the PR is open;
   - the PR is not draft;
   - the PR targets the repository default branch;
   - the PR branch belongs to this repository or is otherwise safe to merge.

2. Reviewer approval:
   - there is a latest reviewer-agent review containing `Agent-Review: reviewer`;
   - that review has `Review-Decision: APPROVE`;
   - that review has `Merge-Allowed: true`;
   - that review has `Auto-Merge-Allowed: true`;
   - that review contains `Review-Commit: <sha>`;
   - the current PR head SHA exactly equals that `Review-Commit`;
   - there is no later reviewer review or comment that supersedes, weakens, or contradicts that approval.

3. No unresolved feedback:
   - there is no `REQUEST_CHANGES`;
   - there is no `Action-Required: true`;
   - there is no unhandled `Action-Recommended: true`;
   - there is no unhandled `Follow-Up-Recommended: true`;
   - there are no unresolved review threads or clearly actionable comments;
   - there are no human comments indicating hold, wait, stop, manual review, do-not-merge, needs-human-review, blocked, or similar.

4. Checks and mergeability:
   - all required checks are passing;
   - there are no failing checks caused by the PR;
   - checks are not pending or unknown;
   - the PR is mergeable;
   - there are no merge conflicts;
   - the branch is not behind the base branch in a way that branch protection rejects.

5. Labels:
   - the PR does not have blocking labels such as:
     - `do-not-merge`,
     - `manual-merge-only`,
     - `needs-human-review`,
     - `blocked`,
     - `hold`,
     - `wip`.
   - if the repository uses an explicit `automerge` or `automerge-ok` label convention, require that label before merging.

6. Scope and risk:
   - the PR is small or moderate in scope;
   - the PR has a clear linked issue or clear purpose;
   - the PR body includes a useful summary and test results;
   - the PR does not touch high-risk areas unless the reviewer explicitly explains why auto-merge is still safe.
* Treat these as high-risk areas:
   - authentication,
   - authorization,
   - permissions,
   - security-sensitive logic,
   - secrets,
   - encryption,
   - payment,
   - billing,
   - user data deletion,
   - database migrations,
   - schema changes,
   - deployment,
   - infrastructure,
   - CI/CD,
   - dependency management,
   - lockfiles,
   - broad refactors.

7. Final pre-merge refresh:
   - immediately before merging, re-fetch PR metadata;
   - re-check current head SHA;
   - re-check latest reviews/comments;
   - re-check labels;
   - re-check checks;
   - re-check mergeability.
* If anything changed during the final refresh, do not merge and re-evaluate on a later turn.

Auto-merge handling:
* If a PR passes every auto-merge gate:
  1. Do not modify code.
  2. Do not create a new commit.
  3. Use `gh pr merge <PR>` with the repository's established merge method.
  4. Delete the PR branch only if it is clearly safe and owned by this agent/repository convention.
  5. After merge, stop and wait for the next turn.
* If a PR is approved but does not pass every auto-merge gate:
  - do not merge;
  - if useful, leave a brief PR comment explaining that it is merge-ready for human review or which gate blocked auto-merge;
  - then stop only if you took an action, otherwise continue evaluating Priority 1 candidates.

Priority within Priority 1:
Handle the highest-priority actionable PR task in this order:
1. Merge conflicts or base-branch updates that block merging.
2. `REQUEST_CHANGES` or `Action-Required: true`.
3. Failed checks caused by the PR.
4. `COMMENT_ONLY` with `Action-Recommended: true`.
5. `Follow-Up-Recommended: true`.
6. Other unresolved review threads or clearly actionable comments.
7. PRs that pass every auto-merge gate.

Handling:
* Select the highest-priority actionable PR and handle only that PR this turn.
* Use or create the dedicated PR worktree when code, tests, conflict resolution, or branch updates are needed.
* A dedicated worktree is not required for pure metadata actions such as commenting or auto-merging, but PR metadata must still be freshly verified.
* Inside the correct PR worktree when worktree work is needed:
  1. Fetch latest refs:
     `git fetch origin`
  2. Ensure the worktree is on the PR branch and clean.
  3. Inspect reviewer feedback, review comments, regular PR comments, commits, checks, and mergeability.
  4. If the PR is blocked because the base branch changed:
     - update the PR branch from the base branch using the merge/base-branch maintenance rules above.
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
* If no code or branch maintenance is needed and the PR passes every auto-merge gate, perform auto-merge according to the auto-merge handling rules.

Completion:
* After pushing a fix, resolving a conflict, updating the PR branch from the base branch, replying to a reviewer, creating a follow-up issue, asking for clarification, or auto-merging one PR, stop and wait for the next turn.
* If no open PR needs maintenance and no PR passes every auto-merge gate, proceed to Priority 2.

Priority 2: Tackle Unassigned Issues

Goal:
* Start one new issue only when no existing PR needs maintenance or safe auto-merge.

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
* Do not create unnecessary branches, worktrees, comments, commits, PRs, or merges while idle.