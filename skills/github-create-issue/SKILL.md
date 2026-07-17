---
name: github-create-issue
description: Create or draft GitHub issues from an ad hoc feature, bug, or engineering discussion. Use when the user asks to turn a conversation into issue(s), write an issue, or create/publish issue(s). Route large technical requirement documents to breakdown-requirement-into-issues instead.
---

# Goal

Turn a messy feature, bug, refactor, or engineering discussion into small,
self-contained GitHub issue drafts. Create issues only with explicit user or
trusted workflow authorization.

This skill handles ad hoc discussion. Use
`breakdown-requirement-into-issues` for a large technical requirement
document. This skill plans work and creates issues; implementation is a
separate task.

## Modes

- **Draft mode:** The user asks for a draft, plan, proposal, or issue text
  without clearly asking to create or publish it. Do not run write commands.
  Output the issue plan and complete proposed bodies when the context supports
  them; if blocking details are missing, ask the questions instead of
  inventing content, then stop.
- **Create mode:** The user explicitly asks to create, publish, or post the
  issue(s). Perform the preflight below and create them with `gh`.
- **Agent-authorized create:** `github-implementor-loop` may explicitly ask
  this skill to create one concrete, linked follow-up issue from reviewer
  feedback. That request authorizes only the named follow-up, not unrelated
  issue creation.
- **Ambiguous mode:** Treat the request as draft mode and ask whether the user
  wants the proposed issue(s) created.

If the user authorizes one issue but the analysis finds multiple required
boundaries, show the split and ask before creating multiple issues.

## Agent Contract

Implementation and documentation/planning issues created for
`github-implementor-loop` and `github-reviewer-loop` must use the exact
section names in the implementation template below. Those agents treat the
issue body as the PR acceptance contract, not as background information.

Every implementation or documentation/planning issue also includes
`Developer Checklist` and `Requirement Traceability`. For an ad hoc issue
without formal requirement IDs, traceability names the source discussion and
key decisions or says `None`.

An implementor follow-up handoff must identify the current PR or issue, state
why the work is outside the current scope, and name the concrete follow-up
goal. Link the created issue back in the PR reply and report its number in the
handling marker required by `github-implementor-loop`. Route a multi-issue
follow-up to `breakdown-requirement-into-issues`.

## Workflow

### 1. Resolve context

Read the full relevant conversation. Separate confirmed requirements,
constraints, decisions, rejected alternatives, assumptions, open questions,
and requested outcomes.

Before putting conversation content into an issue or handing it to another
skill, remove credentials,
tokens, secret values, private URLs, and unnecessary personal data. Replace
essential sensitive details with safe placeholders. Ask the user for a safe
description when the sensitive detail is necessary to reproduce the problem.

In create mode or agent-authorized create mode:

1. Resolve the target repository from an explicit `owner/repo` or `--repo`
   instruction. Otherwise verify the current repository. Always verify
   authentication:

   ```bash
   gh repo view --repo OWNER/REPO --json nameWithOwner,defaultBranch  # explicit target
   gh repo view --json nameWithOwner,defaultBranch                    # current repo
   gh auth status
   ```

   Run only the repository lookup that matches the request, then use the
   verified `OWNER/REPO` in every later command.

2. Stop if the repository or authorization cannot be verified. Never guess
   the target repository.
3. Inspect existing labels with `gh label list --repo OWNER/REPO`.
4. Search for duplicates and related work using sanitized issue terms. Run
   separate searches for each proposed title and its most specific domain
   terms, replacing the quoted example with the actual sanitized strings:

   ```bash
   gh issue list --repo OWNER/REPO --state all --search "TITLE_OR_DISTINCTIVE_TERMS" --limit 100
   gh pr list --repo OWNER/REPO --state all --search "TITLE_OR_DISTINCTIVE_TERMS" --limit 100
   ```

   If an exact duplicate exists, report it and stop. If related work exists,
   reference it in the draft and explain why this work is distinct.

In draft mode, use available repository context when useful. Mark unknown
files, commands, or repository details as assumptions instead of inventing
them.

Completion criterion: the mode, sanitized source material, and create target
when applicable are known; every blocking unknown is either clarified or
listed for the user.

### 2. Choose the issue boundary

Create one issue when it has one coherent goal, one implementable path, and
can be tested and reviewed as one focused change.

Split only at a real boundary:

- separate ownership or independently reviewable work;
- a dependency that requires a different change to land first;
- a distinct independently shippable vertical slice; or
- a blocking investigation that must resolve an unknown before implementation.

Risk, API involvement, infrastructure involvement, or user-visible behavior
alone does not justify a split.

Use one of these issue types:

- **Implementation:** a concrete behavior or code change with an agreed path.
- **Investigation:** a blocking question, spike, or design validation. Its
  deliverable is evidence and a decision, not speculative production code.
- **Planning or documentation:** a non-behavioral task with an explicit
  no-test justification.

For every issue, record a temporary ID, title, type, goal, scope, out of
scope, dependencies, and required validation. An implementation issue has a
chosen approach. An investigation issue has a question and decision
criteria instead of a chosen implementation.

In this agent integration, publish only implementation and
documentation/planning issues to the unassigned queue. Keep investigation
issues in draft form unless the user names another owner or workflow for
them; the implementor loop does not execute investigation work.

Completion criterion: each issue has one clear boundary, no unresolved
implementation choice unless it is an investigation, and explicit
dependency direction.

### 3. Draft the issue bodies

Use concrete content, not placeholders or HTML comments. Omit a section only
when it is genuinely irrelevant; use `None` where a required section has no
items.

#### Implementation issue

```markdown
## Summary

## Background / Context

## Problem

## Goal / Expected Behavior

## Scope

## Out of Scope

## Chosen Implementation Approach

## Implementation Plan

## Relevant Files / Areas

## Acceptance Criteria

## Tests Required

## Manual Verification / Self-Check

## Reviewer Acceptance Checklist

## Dependencies

## Follow-Up Work

## Definition of Done

## Developer Checklist

## Requirement Traceability
```

The body must explain enough for an implementor to work without rereading the
conversation. Acceptance criteria describe observable behavior. Tests name
the behavior or regression they prove; they do not merely say “add tests.”
Bug issues include a regression test when feasible. Refactor issues describe
how behavior preservation is verified. Manual verification names exact
repository commands when known, records expected results, and labels unknown
commands as repo-specific. The reviewer checklist must tell the reviewer what
to inspect, not merely say “review the PR.”

#### Investigation issue

```markdown
## Question

## Context

## In Scope

## Out of Scope

## Investigation Plan

## Deliverables / Decision Criteria

## Relevant Files / Areas

## Validation

## Dependencies / Follow-Up

## Definition of Done
```

State that the investigation does not promise a production implementation.
Require evidence, alternatives considered, the recommended decision, and
the implementation issue(s) to create next. Require tests only for executable
artifacts produced by the investigation.

#### Planning or documentation issue

Use the implementation template unchanged so both agents can parse it. In
`## Tests Required`, write `None` and a `No-Test Justification` subsection.
Keep `## Manual Verification / Self-Check` with applicable documentation or
planning checks. Explain why the task changes no executable behavior.

### 4. Apply the quality gate

Before creating or presenting an issue, verify that every issue has:

- a specific title and one clear goal;
- the canonical section names when the issue is intended for the implementor
  and reviewer loops;
- concrete scope and out of scope;
- an approach or investigation question appropriate to its type;
- observable acceptance or decision criteria;
- named tests or a valid no-test justification;
- verification steps and dependencies;
- a developer checklist and requirement traceability;
- no unresolved choice hidden in an implementation issue;
- no secrets or unnecessary private data;
- no duplicate of existing work; and
- no empty placeholders.

If an ambiguity could change behavior, scope, ownership, acceptance, or safe
reproduction, treat it as blocking and ask the user instead of turning it into
a confident implementation assumption. If it cannot change those things,
label it as a non-blocking assumption in the issue body.

## Create Issues

Only enter this section in create mode or agent-authorized create mode.

Do not publish an investigation issue into this agent integration. Keep it in
the draft output and ask who owns it unless the user has named another owner
or workflow. Publish implementation and documentation/planning issues only
when their dependencies are not blocked by that investigation.

1. Write each final body to a temporary Markdown file to avoid shell escaping
   problems.
2. Create issues in dependency order with the verified repository:

   ```bash
   gh issue create --repo OWNER/REPO \
     --title "Specific title" \
     --body-file /tmp/issue-body.md
   ```

   Apply only labels confirmed by `gh label list`.
3. Record each successful mapping from temporary ID to issue number and URL.
4. If any creation fails, stop. Report every successful issue, the failed
   command and error, and a retry plan that checks existing created issues
   first. Do not claim that the full set was created.
5. After all issues exist, replace temporary dependency IDs with GitHub issue
   references using `gh issue edit --repo OWNER/REPO` or comments. If an edit
   or comment fails, stop and report the created issues, failed command, and
   retry plan.
6. Verify every created issue with `gh issue view <number> --repo OWNER/REPO`
   and confirm its title, body, labels, and dependency links. If verification
   fails, stop and report the unverified issue instead of claiming completion.

The creation step is complete only when every requested issue has succeeded
and every created issue has been verified.

## Final Response

In draft mode, report the proposed issue plan, complete bodies, assumptions,
and any blocking questions.

In create mode or agent-authorized create mode, report each issue number,
title, URL, type, and dependency order. Also report any partial failure,
skipped duplicate, redaction, or unresolved assumption. Never claim creation
without a successful command and verification.
