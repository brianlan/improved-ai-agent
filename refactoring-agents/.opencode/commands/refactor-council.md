---
description: Run a human-in-the-loop small/medium refactoring council workflow
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

* architecture risks,
* behavior regressions,
* low-value cleanup,
* overengineering,
* missing verification,
* unclear design choices,
* unsafe sequencing,
* unspoken human preferences.

## Scope of This Council

This council is optimized for **small and medium behavior-preserving refactoring plans**.

It is suitable for:

* focused file-level refactoring,
* small module refactoring,
* medium feature-area cleanup,
* decomposition of oversized functions/classes/services,
* module-local responsibility cleanup,
* dependency-direction cleanup inside a focused area,
* incremental extraction of pure logic,
* testability improvements,
* safe multi-PR refactoring sequences.

It is not intended to produce implementation plans for:

* whole-repository refactoring,
* large architecture redesign,
* cross-system rewrites,
* long-running migration programs,
* replacement of core architectural patterns,
* broad package restructuring across unrelated areas,
* refactoring that requires large-scale team coordination.

The council must not turn a large architecture redesign idea into implementation tasks in this workflow.

However, the council should not ignore large refactoring insights. If it discovers larger architecture problems, it must preserve them as:

```text
Future RFC Candidates
```

or under:

```text
Rejected or Postponed Ideas
```

Large ideas should be described clearly, with evidence and rationale, but they must not become Level A or Level B implementation tasks in this council run.

## Complexity Budget

Default complexity budget for this council:

* Prefer one focused file, module, or feature area.
* Prefer 2–5 implementation tasks.
* Each implementation task should fit into one focused PR.
* A medium plan may contain a sequence of focused PRs.
* Avoid plans that require broad repository-wide coordination.
* Avoid plans that require many unrelated modules to change together.
* Avoid long-running migration programs.

If the plan appears to require more than 5–7 implementation tasks, the coordinator must either:

1. ask the human to narrow the scope,
2. split the work into multiple council runs,
3. classify part of the work as future RFC / postponed work.

## Interaction Mode

The council supports two modes.

### Interactive Mode

Interactive Mode is the default.

In Interactive Mode, Human Decision Gates are blocking checkpoints.

When a Human Decision Gate is triggered, the coordinator must:

1. ask the human using the `question` tool,
2. stop the council workflow immediately after asking,
3. not continue to the next round,
4. not invoke more specialist agents,
5. not invoke the plan synthesizer,
6. not create `.refactor-council/final-plan.md`,
7. resume only after the human answers.

The coordinator must not use timeout-based defaults.

The coordinator must never say:

```text
If you do not answer within N seconds, I will proceed.
```

Human decisions are not time-limited unless the user explicitly requests Automatic Mode.

### Automatic Mode

Automatic Mode is allowed only when the user explicitly says one of:

* `--auto`
* `fully automatic`
* `run automatically`
* `do not ask me questions`
* `use defaults`
* `proceed without asking`

In Automatic Mode, the coordinator may use conservative defaults at Human Decision Gates, but it must record every default in `.refactor-council/human-decisions.md`.

If the user has not explicitly requested Automatic Mode, the coordinator must assume Interactive Mode.

### Explicit Mode Flags

If the user includes:

```text
--interactive
```

use Interactive Mode.

If the user includes:

```text
--auto
```

use Automatic Mode.

If neither flag is included, use Interactive Mode.

## Required Roles

The coordinator must invoke these specialist agents unless one is unavailable:

* `refactoring-code-smell-analyst`
* `refactoring-architecture-reviewer`
* `refactoring-safety-guardian`
* `refactoring-test-strategist`
* `refactoring-roi-analyst`
* `refactoring-plan-synthesizer`

If an agent is unavailable, the coordinator must explicitly state which role is missing and preserve that role's concerns in its own checklist before continuing.

## Non-Negotiable Rules

1. Do not edit product code.
2. Do not edit tests, configs, docs, or source files outside `.refactor-council/`.
3. Only create or update council artifacts under `.refactor-council/`.
4. Bash commands must be read-only inspection commands.
5. Do not run formatters, fixers, dependency installers, migrations, generators, or commands that modify the working tree.
6. In Interactive Mode, do not continue past a triggered Human Decision Gate until the human answers.
7. In Interactive Mode, do not replace a Human Decision Gate with a default.
8. Do not produce a final plan until:

   * independent specialist analysis is complete,
   * candidate topics have stable IDs,
   * material objections have been processed,
   * safety vetoes have been handled,
   * all triggered human decision gates have been answered,
   * accepted tasks have concrete verification requirements,
   * rejected or postponed ideas are preserved,
   * larger architecture ideas have been moved to Future RFC Candidates or Rejected/Postponed Ideas.

In Automatic Mode only, Human Decision Gates may be resolved with conservative defaults, and every default must be recorded.

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

## Resume Rules

The council may be invoked multiple times across a human-in-the-loop workflow.

At the start of every invocation, the coordinator must check whether `.refactor-council/` already exists.

If previous council artifacts exist, the coordinator must:

1. read `.refactor-council/human-decisions.md` if present,
2. identify the latest completed round,
3. identify whether the previous run stopped at a Human Decision Gate,
4. treat the user's latest message as the answer to the pending gate when appropriate,
5. record the answer in `.refactor-council/human-decisions.md`,
6. resume from the next step instead of restarting from Round 0.

Do not restart the council from scratch unless the user explicitly asks to restart.

If the current user message changes the original scope materially, record that as a new human decision and update `.refactor-council/input.md`.

## Question Tool Requirement

For every Human Decision Gate in Interactive Mode, the coordinator must use the `question` tool.

Do not ask Human Decision Gate questions only as normal markdown text.

Do not bury Human Decision Gate questions inside artifacts.

Do not continue the council workflow after asking a Human Decision Gate question.

Each `question` tool request must include:

```text
Decision ID:
Gate:
Question:
Context:
Why this matters:
Options:
Council recommendation:
Consequence of each option:
Whether multiple options are allowed:
```

The question should be specific and decision-oriented.

Bad question:

```text
Do you have any preferences?
```

Good question:

```text
Decision D-001: Refactoring scope

The council found both low-risk local cleanup opportunities and broader architecture concerns.

Which scope should the council use for this run?

A. Only high-value local cleanup inside the target module.
B. Local cleanup plus small architecture-boundary improvements in directly related files.
C. Stop and let me narrow the target files manually.
D. Record broader architecture concerns as future RFC candidates, but do not include them as implementation tasks.

Council recommendation: B.
Reason: It balances useful cleanup with controlled risk.
```

After invoking the `question` tool, stop. Resume only after receiving the human's answer.

## Human Decision Gates

The council is not required to be fully automatic.

At designated gates, the coordinator must ask the human for decisions that materially affect the refactoring plan.

In Interactive Mode, Human Decision Gates are hard stops.

In Automatic Mode, the coordinator may use conservative defaults and must record them.

A Human Decision Gate is mandatory when a decision materially affects:

* refactoring scope,
* risk tolerance,
* design direction,
* public behavior preservation,
* architecture boundary choices,
* whether to include or exclude candidate topics,
* whether to accept a Level B task with constraints,
* whether to postpone unresolved Level C topics,
* whether to record a large design issue as a Future RFC Candidate,
* whether to produce issue-ready tasks.

A Human Decision Gate is optional only when the decision does not materially change the plan.

Each human decision request must include:

```text
Decision ID:
Gate:
Context:
Why this matters:
Options:
Council recommendation:
Consequence of each option:
Whether multiple options are allowed:
```

Record every human answer or automatic default in `.refactor-council/human-decisions.md`:

```text
## Decision D-001: <title>

Gate:
Question:
Options:
User choice:
Council recommendation:
Final decision:
Impact on plan:
Mode: Interactive / Automatic
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

Trigger this gate before Round 1 if any of these are unclear and materially affect the plan:

* target file, module, or focused feature area,
* main refactoring goal,
* maximum acceptable risk,
* preference for very small PRs versus a medium multi-PR sequence,
* behavior that must not change.

In Interactive Mode, ask with the `question` tool and stop.

In Automatic Mode, use conservative defaults and record them.

Possible questions:

```text
1. What is the target scope: file, small module, focused feature area, or directly related call sites?
2. What is the main goal: readability, testability, architecture-boundary cleanup, reducing duplication, or preparing for a near-term feature?
3. What is the maximum acceptable risk level for this council run?
4. Should the council prefer very small PRs, or allow a medium-sized sequence of focused PRs?
5. Are there public APIs, error messages, data formats, performance behavior, or undocumented behaviors that must not change?
```

Whole-repository refactoring is out of scope for this council run.

If whole-repository or large architecture issues are discovered, record them as Future RFC Candidates rather than implementation tasks.

If Automatic Mode is active and safe defaults are needed, use:

```text
- Prefer small incremental PRs.
- Preserve all external behavior.
- Do not change public APIs, error messages, data formats, storage semantics, authorization, or performance-sensitive behavior.
- Treat unclear behavior as behavior to preserve.
- Prefer Level A and conservative Level B tasks.
- Keep large architecture redesign ideas as Future RFC Candidates, not implementation tasks.
```

## Round 1: Independent Specialist Analysis

Goal: collect independent evidence-backed viewpoints.

Invoke each specialist independently. Do not include other specialists' conclusions in any Round 1 prompt.

Each specialist prompt must include:

* original user request,
* target scope,
* relevant code/file context,
* known constraints,
* explicit instruction not to edit code,
* explicit instruction to use read-only inspection only,
* instruction to keep this council scoped to small/medium behavior-preserving refactoring,
* instruction to record larger architecture ideas as Future RFC Candidates rather than implementation tasks,
* required Round 1 output format.

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

## Future RFC Candidates

For each larger idea that is valuable but out of scope for this council:
- Idea:
- Evidence:
- Why it is larger than this council run:
- Potential future benefit:
- Why it should not become an implementation task now:

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
Future RFC candidate: yes/no
```

Do not include Future RFC Candidates as implementation candidate topics unless the human explicitly asks to start a separate strategic planning process.

Trigger Human Gate 1 after Round 1 and before Round 2 if:

* more than 5 candidate topics are found,
* candidate topics span multiple modules,
* candidate topics mix low-risk cleanup with higher-risk architecture changes,
* the council found both narrow and broad possible plans,
* the target scope may be larger than the user intended,
* one or more specialists raised questions that materially affect topic selection,
* the plan appears likely to exceed the default complexity budget.

In Interactive Mode, ask the human which topics should enter Round 2 using the `question` tool and stop.

Suggested options:

```text
A. Include only high-value / low-risk topics.
B. Include high-value topics up to medium risk if verification is concrete.
C. Include a specific list of topic IDs.
D. Narrow the scope and run this council only on one focused area.
E. Record broader architecture ideas as Future RFC Candidates only.
```

In Automatic Mode, default to:

```text
Focus on high-value / low-risk topics and conservative medium-risk topics with clear verification. Move large architecture ideas to Future RFC Candidates.
```

Record the decision or default in `.refactor-council/human-decisions.md`.

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

## Future RFC Candidates

For each larger idea:
- Topic or idea ID:
- Why this should be future RFC, not implementation work now:

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

* behavior,
* public contracts,
* data integrity,
* performance-sensitive paths,
* security,
* authorization,
* concurrency,
* caching,
* transactions,
* migrations,
* rollout safety,
* rollback feasibility.

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

## Large Redesign Handling Rule

If any specialist identifies a topic as a large architecture redesign, whole-repository refactor, cross-system rewrite, or long-running migration program, the coordinator must not classify it as Level A or Level B in this council run.

The coordinator must classify it as one of:

```text
Level C: Future RFC candidate
Level D: Rejected for this council run
```

The coordinator should preserve:

* evidence,
* why it matters,
* potential future benefit,
* why it is out of scope now,
* what would need to be true before reconsidering it.

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

A revised topic must remain within the small/medium council scope. If narrowing is not possible, classify it as Future RFC or postponed.

## Human Gate 2: Design Choices and Tradeoffs

After Round 2A/2B, ask the human when there are unresolved design choices that materially affect the final plan.

Trigger this gate after Round 2A/2B and before final consensus if:

* a material architecture objection has multiple valid small/medium resolutions,
* Safety Guardian allows a topic only under meaningful constraints,
* ROI Analyst recommends postponing a topic that another agent considers important,
* the council must choose between local helper, module-local abstraction, or existing boundary-preserving location,
* the council must choose between very small PRs and a medium multi-PR sequence,
* a Level B topic depends on human risk tolerance,
* two or more specialists disagree and more than one reasonable small/medium path remains,
* the council needs human confirmation to move a larger idea to Future RFC Candidates.

In Interactive Mode, ask the human to choose among explicit options using the `question` tool and stop.

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

In Automatic Mode, use the most conservative option that:

* preserves behavior,
* minimizes architecture disruption,
* keeps the task small,
* avoids new abstractions unless clearly justified,
* has concrete verification,
* moves large redesign ideas to Future RFC Candidates rather than implementation work.

Record the decision or default in `.refactor-council/human-decisions.md`.

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
- The topic is within small/medium council scope.

Level B: Accepted with constraints
- No active safety veto.
- Objections exist but are addressed by explicit constraints.
- Human decision is resolved.
- Verification path is concrete.
- Risk is acceptable.
- The topic is within small/medium council scope.

Level C: Unresolved / future work / Future RFC candidate
- Useful idea but has unresolved design choice, missing evidence, unclear owner, unclear verification, or unanswered human decision.
- Larger architecture ideas belong here when they may be valuable but exceed this council's scope.

Level D: Rejected
- Unsafe, too broad, too low-value, behavior-changing, architecture-inconsistent, speculative, not a refactoring, or too large for this council run.
```

In Interactive Mode, do not classify a topic as Level B if it depends on an unanswered human decision.

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
Future RFC notes:
```

## Human Gate 3: Final Plan Approval

Trigger this gate before invoking `refactoring-plan-synthesizer` if:

* any Level B task remains,
* any open question could affect implementation,
* the final plan would contain more than 5 implementation tasks,
* the highest risk level is medium or higher,
* the user requested review before finalization,
* the council made a non-trivial scope or design decision during consensus,
* there is a Future RFC Candidate that the human may want to keep visible in the final plan.

Do not trigger Gate 3 merely because a small low-risk plan has 1–3 Level A tasks with concrete verification and no material objections.

In Interactive Mode, ask whether to finalize, make the plan more conservative, narrow scope, or produce issue-ready specs.

Suggested options:

```text
A. Finalize this plan.
B. Make the plan more conservative.
C. Narrow the plan to fewer implementation tasks.
D. Produce only the final plan, not issue-ready tasks.
E. Produce both final plan and issue-ready tasks.
F. Keep Future RFC Candidates visible in the final plan.
```

Use the `question` tool and stop after asking.

Do not invoke the synthesizer until the human answers.

In Automatic Mode, default to:

```text
Finalize the conservative plan, produce issue-ready tasks, and keep Future RFC Candidates visible but out of implementation tasks.
```

Record the decision or default in `.refactor-council/human-decisions.md`.

## Round 4: Plan Synthesis

Invoke `refactoring-plan-synthesizer` with only:

* original request,
* `.refactor-council/input.md`,
* `.refactor-council/context.md`,
* Round 1 summaries,
* Round 2 candidate topics,
* objections,
* revised topics,
* consensus,
* human decisions,
* Future RFC Candidates,
* rejected or postponed ideas.

The synthesizer must not invent new implementation tasks.

The synthesizer may only include implementation tasks that were classified as:

* Level A,
* Level B.

The synthesizer must not include Level C or Level D topics as implementation tasks. Mention them under open questions, Future RFC Candidates, or rejected/postponed ideas.

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

## 11. Future RFC Candidates

## 12. Rejected or Postponed Ideas

## 13. Human Decisions Applied
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

Do not create issue-ready tasks for Future RFC Candidates. They are not implementation tasks in this council run.

## Final Response Rule

If the workflow stops at a Human Decision Gate, the final response for that turn must contain only:

```text
The council has reached <Gate Name> and needs your decision before continuing.
```

Then ask the question using the `question` tool.

Do not summarize later rounds.

Do not claim the final plan is complete.

Do not create `.refactor-council/final-plan.md`.

Do not invoke `refactoring-plan-synthesizer`.

The final plan may only be produced after all triggered Human Decision Gates have been answered or after the user explicitly switches to Automatic Mode.

If the workflow completes, return a concise summary:

```text
Final plan: .refactor-council/final-plan.md
Issue-ready tasks: .refactor-council/issue-ready-tasks.md
Accepted task count:
Highest risk level:
Verification categories:
Future RFC candidate count:
Rejected/postponed idea count:
Unresolved blockers:
Human decisions used:
```

Do not paste the entire final plan unless the user asks for it.
