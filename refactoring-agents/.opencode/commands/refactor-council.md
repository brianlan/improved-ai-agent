---
description: Run a human-in-the-loop refactoring council workflow
agent: refactoring-planning-coordinator
---

Use `refactoring-planning-coordinator` to run the Human-in-the-Loop Refactoring Council workflow.

This command is the authoritative protocol for the council. Do not require a separate `refactoring-council-protocol.md`.

User request:

```text
$ARGUMENTS
```

# Refactoring Council Protocol

## Purpose

The council creates detailed, meaningful, safe, behavior-preserving, and executable refactoring plans.

The council does not edit product code. It studies the repository, debates refactoring opportunities from multiple viewpoints, asks humans for key decisions when needed, and produces a final plan that can later guide implementation.

The council is designed for cases where a single-agent plan may miss:

- architecture risks,
- behavior regressions,
- low-value cleanup,
- overengineering,
- missing verification,
- unclear design choices,
- unsafe sequencing,
- unspoken human preferences.

## Required Roles

The coordinator must invoke these specialist agents unless one is unavailable:

- `refactoring-code-smell-analyst`
- `refactoring-architecture-reviewer`
- `refactoring-safety-guardian`
- `refactoring-test-strategist`
- `refactoring-roi-analyst`
- `refactoring-plan-synthesizer`

If an agent is unavailable, the coordinator must explicitly state which role is missing and preserve that role's concerns in its own checklist before continuing.

## Non-Negotiable Rules

1. Do not edit product code.
2. Do not edit tests, configs, docs, or source files outside `.refactor-council/`.
3. Only create or update council artifacts under `.refactor-council/`.
4. Bash commands must be read-only inspection commands.
5. Do not run formatters, fixers, dependency installers, migrations, generators, or commands that modify the working tree.
6. Do not produce a final plan until:
   - independent specialist analysis is complete,
   - candidate topics have stable IDs,
   - material objections have been processed,
   - safety vetoes have been handled,
   - human decision gates have been resolved or explicitly defaulted,
   - accepted tasks have concrete verification requirements,
   - rejected or postponed ideas are preserved.

## Artifact Layout

Create or provide these artifacts:

```text
.refactor-council/
  input.md
  context.md
  human-decisions.md
  round-1/
    code-smell.md
    architecture.md
    safety.md
    testability.md
    roi.md
  round-2/
    candidate-topics.md
    objections.md
    revised-topics.md
    consensus.md
  final-plan.md
  issue-ready-tasks.md
```

If artifact writing is unavailable, provide the artifacts in the response with exact intended file paths.

## Human Decision Gates

The council is not required to be fully automatic.

At designated gates, the coordinator may stop and ask the human for decisions that materially affect the refactoring plan. The coordinator must not ask vague questions. It must present options, consequences, and a recommended default.

If the human explicitly asks for a fully automatic run, the coordinator may proceed using conservative defaults and must record them in `.refactor-council/human-decisions.md`.

If a decision is important but not answered, record:

```text
Decision ID:
Question:
Options:
Default used:
Reason for default:
Impact on plan:
```

## Round 0: Intake and Context Collection

Goal: understand the request, target scope, repository context, constraints, and likely verification commands.

The coordinator should inspect the repository with read-only commands when useful.

Write `.refactor-council/input.md` with:

```text
# Input

## User Request

## Target Scope

## Inferred Goal

## Non-Goals

## Known Constraints

## Assumptions

## Human Decisions So Far
```

Write `.refactor-council/context.md` with:

```text
# Repository Context

## Files / Modules Inspected

## Relevant Entry Points

## Relevant Tests

## Existing Architecture Notes

## Public Contracts / Behavior-Sensitive Areas

## Likely Verification Commands

## Unknowns
```

### Human Gate 0: Scope, Intent, and Risk Preference

Ask the human only if the answer materially affects the plan.

Possible questions:

```text
1. What is the target scope: file, module, feature area, or whole repository?
2. What is the main goal: readability, testability, architecture cleanup, reducing duplication, or preparing for future features?
3. What is the maximum acceptable risk level?
4. Should the council prefer small incremental PRs over a larger coherent redesign?
5. Are there public APIs, error messages, data formats, performance behavior, or undocumented behaviors that must not change?
```

If safe defaults are needed, use:

```text
- Prefer small incremental PRs.
- Preserve all external behavior.
- Do not change public APIs, error messages, data formats, storage semantics, authorization, or performance-sensitive behavior.
- Treat unclear behavior as behavior to preserve.
- Prefer Level A and conservative Level B tasks.
```

Record the gate result in `.refactor-council/human-decisions.md`.

## Round 1: Independent Specialist Analysis

Goal: collect independent evidence-backed viewpoints.

Invoke each specialist independently. Do not include other specialists' conclusions in any Round 1 prompt.

Each specialist prompt must include:

- original user request,
- target scope,
- relevant code/file context,
- known constraints,
- explicit instruction not to edit code,
- explicit instruction to use read-only inspection only,
- required Round 1 output format.

Persist each result:

```text
.refactor-council/round-1/code-smell.md
.refactor-council/round-1/architecture.md
.refactor-council/round-1/safety.md
.refactor-council/round-1/testability.md
.refactor-council/round-1/roi.md
```

Required Round 1 output:

```text
## Observations

## Proposed Refactoring Opportunities

For each opportunity:
- Finding:
- Evidence:
- Suggested refactoring:
- Behavior preservation boundary:
- Likely files:
- Risk:
- Confidence:

## Risks

## Verification Needs

## Questions for Human Decision

For each question:
- Question:
- Why it matters:
- Options:
- Recommended default:
- Consequence if unanswered:

## Ideas to Avoid

For each idea:
- Idea:
- Why it is tempting:
- Why it should be avoided:

## Confidence

## Questions / Uncertainties
```

## Human Gate 1: Candidate Topic Selection

After Round 1, the coordinator aggregates findings into candidate topics.

Each topic must have a stable ID:

```text
T-001, T-002, T-003, ...
```

Write `.refactor-council/round-2/candidate-topics.md`.

Candidate topic schema:

```text
## Topic T-001: <short name>

Source agents:
Initial proposal:
Evidence:
Likely files:
Behavior preservation boundary:
Expected value:
Architecture concerns:
Safety concerns:
Verification requirements:
Risk:
Open questions:
Human decision needed: yes/no
```

If there are too many candidate topics, or if scope is ambiguous, ask the human to choose:

```text
A. Include all reasonable topics.
B. Focus only on high-value / low-risk topics.
C. Focus on a specific topic ID list.
D. Stop and narrow the analysis.
```

Record the decision in `.refactor-council/human-decisions.md`.

If no human response is available and the user did not ask for a fully interactive flow, default to:

```text
Focus on high-value / low-risk topics and conservative medium-risk topics with clear verification.
```

## Round 2A: Cross-Review and Objections

Goal: make specialists challenge the candidate topics from their role.

Ask each specialist to review the candidate list.

Round 2 review output:

```text
## Supported Topics

## Topics Accepted With Constraints

## Material Objections

For each objection:
- Topic ID:
- Objection:
- Why it matters:
- Required change to resolve:
- If unresolved, recommended classification:

## Rejected or Postponed Topics

## Required Verification Changes

## Safety Vetoes
```

Persist all challenges and objections in:

```text
.refactor-council/round-2/objections.md
```

## Safety Veto Rule

The Safety Guardian may veto a topic when there is concrete unresolved risk to:

- behavior,
- public contracts,
- data integrity,
- performance-sensitive paths,
- security,
- authorization,
- concurrency,
- caching,
- transactions,
- migrations,
- rollout safety,
- rollback feasibility.

Veto format:

```text
Veto: yes
Topic:
Reason:
Required changes to reconsider:
Minimum verification:
```

Rules:

1. A vetoed topic cannot be Level A or Level B.
2. A vetoed topic can only re-enter the plan after being narrowed or constrained and re-reviewed by Safety Guardian.
3. If re-review is not completed, classify the topic as Level C or Level D.

## Material Objection Rule

If Architecture Reviewer, ROI Analyst, or Test Strategist raises a material objection, the coordinator must do one of:

1. revise the topic and request targeted re-review,
2. classify the topic as Level C or Level D,
3. escalate the topic to Human Gate 2.

Do not silently ignore material objections.

## Round 2B: Topic Revision and Targeted Re-Review

Goal: transform debated topics into safer, narrower, more executable topics.

For each topic with a material objection:

1. summarize the objection,
2. narrow or constrain the topic,
3. write a revised topic,
4. request targeted re-review from the objecting specialist,
5. request Safety Guardian re-review if behavior-sensitive.

Write `.refactor-council/round-2/revised-topics.md`.

Revised topic schema:

```text
## Revised Topic T-001

Original topic:
Objections:
Revision:
New constraints:
Updated verification:
Remaining concerns:
Re-review result:
```

## Human Gate 2: Design Choices and Tradeoffs

After Round 2A/2B, ask the human when there are unresolved design choices that materially affect the final plan.

Question format:

```text
## Decision D-001: <decision title>

Context:
Why this matters:

Option A:
- Description:
- Pros:
- Cons:
- Risk:
- Verification impact:

Option B:
- Description:
- Pros:
- Cons:
- Risk:
- Verification impact:

Council recommendation:
Consequence if unanswered:
```

Record the decision in `.refactor-council/human-decisions.md`.

If no human response is available, use the most conservative option that:

- preserves behavior,
- minimizes architecture disruption,
- keeps the task small,
- avoids new abstractions unless clearly justified,
- has concrete verification.

## Round 3: Consensus Classification

Goal: classify each topic into a stable decision.

Write `.refactor-council/round-2/consensus.md`.

Classification levels:

```text
Level A: Accepted
- No safety veto.
- No material architecture objection.
- Verification path is concrete.
- Scope is narrow enough for one focused PR.
- ROI is medium or high.

Level B: Accepted with constraints
- No active safety veto.
- Objections exist but are addressed by explicit constraints.
- Human decision is resolved or a conservative default is recorded.
- Verification path is concrete.
- Risk is acceptable.

Level C: Unresolved / future work
- Useful idea but has unresolved design choice, missing evidence, unclear owner, unclear verification, or unanswered human decision.

Level D: Rejected
- Unsafe, too broad, too low-value, behavior-changing, architecture-inconsistent, speculative, or not a refactoring.
```

Consensus entry schema:

```text
## Topic T-001: <short name>

Classification:
Reason:
Accepted constraints:
Required verification:
Risk:
Dependencies:
Human decisions:
Rejected alternatives:
```

## Round 4: Plan Synthesis

Invoke `refactoring-plan-synthesizer` with only:

- original request,
- `.refactor-council/input.md`,
- `.refactor-council/context.md`,
- Round 1 summaries,
- Round 2 candidate topics,
- objections,
- revised topics,
- consensus,
- human decisions,
- rejected or postponed ideas.

The synthesizer must not invent new implementation tasks.

The synthesizer may only include implementation tasks that were classified as:

- Level A,
- Level B.

The synthesizer must not include Level C or Level D topics as implementation tasks. Mention them under open questions or rejected/postponed ideas.

Write:

```text
.refactor-council/final-plan.md
```

Final plan required structure:

```text
# Refactoring Plan

## 1. Refactoring Goal

## 2. Scope and Non-Goals

## 3. Current Problems

## 4. Agreed Refactoring Strategy

## 5. Step-by-Step Task Breakdown

For each task:
### Task N: <specific action>

Why:
Preconditions:
Scope:
Files likely involved:
Behavior invariants:
Safety constraints:
Implementation notes:
Do-not-do list:
Acceptance criteria:
Verification:
Verification commands:
Risk:
Dependencies:

## 6. Dependencies Between Tasks

## 7. Risk Summary

## 8. Required Tests / Verification

## 9. Rollback Strategy

## 10. Open Questions

## 11. Rejected or Postponed Ideas

## 12. Human Decisions Applied
```

## Issue-Ready Tasks

After final plan synthesis, create:

```text
.refactor-council/issue-ready-tasks.md
```

Each issue-ready task should be independently copy-pastable into a GitHub issue.

Issue task schema:

```text
# Issue: <title>

## Background

## Goal

## Scope

## Non-Goals

## Files Likely Involved

## Behavior Invariants

## Implementation Notes

## Do-Not-Do List

## Acceptance Criteria

## Required Tests / Verification

## Verification Commands

## Dependencies

## Risk

## Rollback Notes
```

## Final Response

Return a concise summary:

```text
Final plan: .refactor-council/final-plan.md
Issue-ready tasks: .refactor-council/issue-ready-tasks.md
Accepted task count:
Highest risk level:
Verification categories:
Rejected/postponed idea count:
Unresolved blockers:
Human decisions used:
```

Do not paste the entire final plan unless the user asks for it.