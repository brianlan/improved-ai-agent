---
name: breakdown-requirement-into-issues
description: Break down a large technical requirement document, PRD, or specification into traceable, dependency-ordered GitHub issues. Use when the user provides a substantial requirement and wants an implementation backlog, issue decomposition, or issues created. Use github-create-issue for an ad hoc feature or bug discussion.
---

# Goal

Turn a large technical requirement into a small, sequenced backlog that an
engineer can implement one issue at a time. Preserve the source document's
requirements, decisions, non-goals, and traceability while keeping each issue
within one real implementation boundary.

This skill plans and creates issues. It does not implement source changes.
Use `github-create-issue` for an ad hoc feature or bug discussion.

## Modes

- **Draft mode:** Default when the request asks to analyze, plan, decompose,
  or propose issues without explicitly asking to create or publish them. Do
  not run GitHub write commands. `DRY_RUN_ONLY` is an alias for this mode.
- **Create mode:** Enter only when the user explicitly asks to create,
  publish, or post the planned issues. `CREATE_ISSUES` is an alias for this
  mode. Run the preflight and creation procedure below.
- **Agent-authorized create:** `github-implementor-loop` may explicitly ask
  this skill to decompose one concrete, linked follow-up from reviewer
  feedback and create those follow-up issues. That authorizes only the named
  follow-up scope.
- **Ambiguous mode:** Treat the request as draft mode and ask whether the
  user wants the plan created.

If the user authorizes one issue but decomposition finds multiple required
boundaries, show the split and ask before creating multiple issues.

## Input Contract

The normal input is the final document produced by
`commands/compile-requirement.md`. It may be supplied directly or inside a
`<TECH_SPEC>` block. Accept the document's three layers:

- **Outcomes:** problem, objectives, success metrics, stakeholders, and users;
- **Capabilities:** workflows, responsibilities, boundaries, domain
  definitions, assumptions, and constraints; and
- **Requirements:** atomic behavioral statements grouped under functional,
  non-functional, data/domain, observability, operations/lifecycle, and edge
  case headings.

Also consume the document's acceptance criteria, decision log, open
questions, non-goals, and traceability section. The compiler may not assign
stable IDs; infer them during inventory as described below. Preserve its
abstraction level and do not invent vendor choices, endpoints, schemas, or
file layouts that the requirement or repository does not support.

## Agent Contract

Implementation and documentation/planning issues created for
`github-implementor-loop` and `github-reviewer-loop` must use the exact
section names in the shared template below. Those agents treat the issue body
as the PR acceptance contract.

The shared contract adds two breakdown-specific sections:

- `Requirement Traceability` maps the issue to source requirement IDs.
- `Developer Checklist` records implementation and verification completion.

The implementor loop consumes implementation and documentation/planning
issues. Keep investigation issues in draft form unless the user names
another owner or workflow for them.

For an agent-authorized multi-issue follow-up, return every temporary-ID to
GitHub-issue mapping to the implementor. The implementor must put the list in
the `Follow-Up-Issues: #123, #124` handling field and link every issue in the
PR reply.

## Workflow

### 1. Inventory the requirement

Read the complete requirement document and available repository context.
Sanitize secrets, credentials, private URLs, and unnecessary personal data
before quoting or handing the document to another skill.

Extract and summarize:

- outcomes, objectives, and success metrics;
- workflows, system boundaries, and responsibilities;
- functional and non-functional requirements;
- domain entities, data, persistence, and compatibility constraints;
- configuration, operations, lifecycle, deployment, and observability needs;
- edge cases, acceptance criteria, and non-goals;
- assumptions, decisions, constraints, and open questions; and
- requirement IDs and source traceability.

Preserve explicit IDs exactly. If the document has none, assign IDs from the
requirement category and a normalized short slug, such as
`FR-retry-expired-payment` or `OQ-api-contract`. Do not use list positions as
the ID. Resolve slug collisions with a distinguishing noun and preserve the
mapping in the plan and issue bodies.

Completion criterion: every source requirement is either mapped to one or
more proposed issues, recorded as a non-goal, or listed as an unresolved
question; no requirement is silently dropped.

### 2. Map implementation boundaries

Use repository investigation when context is available to identify existing
files, modules, tests, commands, APIs, and patterns. Mark unknown areas as
assumptions instead of inventing paths.

Consider these areas without treating each as an automatic issue boundary:

- domain and business logic;
- persistence and migrations;
- configuration and settings;
- APIs and integrations;
- frontend behavior and state;
- tests and end-to-end workflows;
- observability and auditability;
- deployment, compatibility, and documentation.

Split only at a real boundary: separate ownership, a dependency that must
land first, an independently shippable vertical slice, or a blocking
investigation. API, UI, infrastructure, risk, or test involvement alone does
not justify a split.

For each proposed issue, determine its temporary ID, title, type, goal,
scope, out of scope, dependencies, requirement IDs, and validation. Identify
the dependency order and parallelizable work.

Completion criterion: every issue has one clear boundary, every dependency
has a direction, and the plan shows which issue should land first.

### 3. Handle ambiguity and issue types

Use these issue types:

- **Implementation:** concrete behavior or code change with an agreed path.
- **Documentation/planning:** non-behavioral work with a valid no-test
  justification and documentation-specific verification.
- **Investigation:** a blocking question or design validation whose deliverable
  is evidence and a decision, not speculative production code.

Treat an ambiguity as blocking when it could change behavior, scope,
ownership, acceptance, sequencing, or safe reproduction. In draft mode,
include an investigation issue or an explicit clarification question. In
create mode, keep investigation issues out of the implementor queue unless
the user names another owner or workflow. Do not create implementation issues
that depend on an unresolved blocking decision.

Completion criterion: each implementation issue has one chosen approach;
each investigation has a question and decision criteria; each non-behavioral
issue explains why production tests do not apply.

### 4. Produce the planning output

In draft mode, output these sections in order:

1. `Requirement Inventory`
2. `Dependency Analysis`
3. `Proposed Issue Plan`
4. `Risk / Ambiguity Check`
5. Complete proposed issue bodies in dependency order

The issue plan table must include:

```text
Temp ID | Title | Type | Depends On | Blocks | Requirement IDs | Required Tests | Notes
```

Do not include an implementation issue unless its required tests can be
named. Include parallelizable work and non-goals in the analysis, not as
hidden issue scope.

### 5. Draft issue bodies

Use concrete content. Replace every placeholder, omit no required contract
section, and never copy secrets or unnecessary private data.

#### Implementation or documentation/planning issue

Use these exact headings:

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

For implementation issues, `Tests Required` names behavior, regression, and
edge-case coverage. Bug fixes include a regression test when feasible;
features include behavior tests; refactors include behavior-preservation
verification.

For documentation/planning issues, put `None` and a `No-Test Justification`
subsection in `Tests Required`. Keep `Manual Verification / Self-Check` with
the applicable documentation or planning checks.

Every issue must include observable acceptance criteria, exact verification
commands when known, explicit dependencies, and relevant requirement IDs.
Use `Depends on #123`, `Blocks #124`, and `Related to #125` when issue numbers
exist. Use temporary IDs until then.

#### Investigation issue

Investigation issues are draft-only for the implementor integration unless
another owner or workflow is explicitly named. Use:

```markdown
## Summary

## Background / Context

## Question

## Scope

## Out of Scope

## Investigation Plan

## Deliverables / Decision Criteria

## Manual Verification / Self-Check

## Dependencies

## Follow-Up Work

## Definition of Done

## Requirement Traceability
```

State that the investigation does not promise a production implementation.
Require evidence, alternatives considered, a recommended decision, and the
implementation issue(s) to create next.

### 6. Apply the quality gate

Before presenting or creating any issue, verify:

- the title and goal are specific;
- the issue has one real boundary;
- scope and out of scope are explicit;
- implementation issues have a chosen approach;
- investigation issues have decision criteria;
- tests or a valid no-test justification are named;
- manual verification and exact commands are included when known;
- dependencies and requirement IDs are explicit;
- every source requirement is accounted for;
- non-goals are not included;
- the issue does not duplicate existing work;
- no unresolved blocking choice is hidden in an implementation issue; and
- no placeholders, secrets, or unnecessary private data remain.

If an issue fails a gate, fix the draft before creation. If a blocking
ambiguity cannot be resolved from the document or repository, ask the user in
draft mode or stop creation and report it.

## Create Issues

Only enter this section in create mode or agent-authorized create mode.

Do not publish an investigation issue into the implementor queue. Keep it in
the draft output and ask who owns it unless the user named another owner or
workflow. Publish implementation and documentation/planning issues only when
their dependencies are not blocked by that investigation.

1. Resolve the repository from an explicit `owner/repo` or `--repo`. Otherwise
   verify the current repository. Always verify authentication:

   ```bash
   gh repo view --json nameWithOwner,defaultBranch
   gh auth status
   ```

2. Inspect labels and search all existing issues and PRs before creating.
   Search each proposed title, stable requirement ID, and the most specific
   domain terms from the requirement inventory:

   ```bash
   gh label list
   gh issue list --repo OWNER/REPO --state all --search "relevant keywords" --limit 100
   gh pr list --repo OWNER/REPO --state all --search "relevant keywords" --limit 100
   ```

   Stop for an exact duplicate. Record related work and explain the
   distinction.
3. Write each final body to a temporary Markdown file and create issues in
   dependency order:

   ```bash
   gh issue create --repo OWNER/REPO \
     --title "Specific title" \
     --body-file /tmp/issue-T01.md
   ```

   Apply only labels confirmed by `gh label list`.
4. Record each temporary-ID-to-issue mapping. If any creation fails, stop and
   report successful issues, the failed command and error, and a retry plan
   that checks existing issues first. Do not claim the full set was created.
5. Replace temporary dependency IDs with GitHub references using
   `gh issue edit` or comments after all issues exist.
6. Verify every created issue with `gh issue view` and confirm its title,
   body, labels, dependency links, and requirement traceability.

Creation is complete only when every allowed requested issue succeeded and was
verified. Investigation drafts are reported separately with their proposed
owner or unresolved ownership question.

## Final Response

In draft mode, report the requirement inventory, dependency analysis, issue
plan, complete bodies, risks, assumptions, and blocking questions.

In create mode or agent-authorized create mode, report every issue number,
title, URL, type, dependency order, and requirement coverage. Report skipped
investigation drafts, duplicates, redactions, partial failures, and
unresolved assumptions. Never claim creation without successful commands and
verification.
