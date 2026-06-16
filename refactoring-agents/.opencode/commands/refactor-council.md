---
description: Run a human-in-the-loop, risk-aware refactoring council workflow
agent: refactoring-planning-coordinator
---

Use `refactoring-planning-coordinator` to run the Human-in-the-Loop Refactoring Council workflow.

This command is the authoritative protocol for the council. Do not require a separate `refactoring-council-protocol.md`.

User request:

```text
$ARGUMENTS
````

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
* unspoken human preferences,
* larger but worthwhile refactoring directions.

## Scope of This Council

The council supports:

* small conservative refactoring,
* medium module-level refactoring,
* feature-area refactoring,
* multi-PR modular refactoring,
* human-approved risk-aware refactoring directions,
* behavior-preserving phased migrations inside a bounded module or feature area.

The council does not support:

* whole-system architecture redesign,
* multi-team platform strategy,
* broad product strategy,
* rewrites without incremental migration,
* refactoring plans that require behavior changes as a hidden dependency,
* unbounded “clean up the whole codebase” efforts.

A larger refactoring direction must not be rejected merely because it is larger than one PR.

A larger refactoring direction must be rejected, postponed, or escalated only when:

* evidence is weak,
* the value is unclear,
* the behavior boundary is unclear,
* architecture direction is unjustified,
* verification is not feasible,
* rollback is not feasible,
* the scope is strategic/system-wide rather than modular,
* the human declines the risk or investment.

## Planning Posture

The council supports two planning postures.

### Conservative Incremental Posture

This is the default posture.

Use it when:

* the user asks for normal refactoring,
* the scope is small,
* risk tolerance is unclear,
* public behavior is sensitive,
* the council lacks enough evidence for a larger direction.

This posture prefers:

* small focused PRs,
* Level A tasks,
* conservative Level B tasks,
* behavior-preserving changes,
* minimal architecture movement,
* strong verification before movement.

### Risk-Aware Modular Posture

Use this posture when:

* the user explicitly asks to consider medium or larger refactoring,
* the council finds a larger direction with strong evidence and meaningful long-term value,
* conservative cleanup would leave the core structural problem unsolved,
* a module-level or feature-area boundary change appears justified,
* the larger direction can be phased into safe milestones,
* the human approves the risk-aware direction.

Risk-Aware Modular Posture does not mean reckless refactoring.

It means the council may surface a larger refactoring direction, explain its value, cost, risk, migration path, and verification requirements, then ask the human whether to approve it.

In this posture:

* large directions are represented as `Refactoring Direction` entries, not direct implementation tasks,
* approved directions must be decomposed into milestones,
* milestones must be decomposed into focused implementation tasks,
* each task must still preserve behavior and have verification,
* Safety Guardian veto rules still apply,
* human approval is required before a larger direction can shape the final plan.

## Direction vs Task

The council must distinguish between `Refactoring Direction` and `Implementation Task`.

### Refactoring Direction

A Refactoring Direction is a larger design or module-level path.

Examples:

* Restructure validation flow inside a module.
* Split a large service into domain-local components.
* Introduce a module-local facade to simplify call sites.
* Gradually migrate duplicated logic behind a single internal interface.
* Reorganize feature-area boundaries to reduce dependency inversion problems.

A Refactoring Direction:

* may span multiple PRs,
* may require multiple milestones,
* may be too large for one task,
* may require human approval,
* must include value, risk, migration, verification, and rollback discussion,
* must not be implemented as one broad task.

Use IDs:

```text
R-001, R-002, R-003, ...
```

### Implementation Task

An Implementation Task is a focused, executable step.

Examples:

* Add characterization tests for current validation behavior.
* Extract pure validation helper inside the existing module.
* Route one call path through the new module-local facade.
* Migrate one group of call sites.
* Remove old internal helper after parity verification.

An Implementation Task:

* should be small enough for a focused PR,
* must preserve behavior,
* must have acceptance criteria,
* must have verification,
* must have a do-not-do list,
* must have rollback notes.

Use IDs:

```text
T-001, T-002, T-003, ...
```

A larger Refactoring Direction can be approved, but only Level A or Level B implementation tasks may enter the executable final plan.

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
   * candidate topics and directions have stable IDs,
   * material objections have been processed,
   * safety vetoes have been handled,
   * all triggered human decision gates have been answered,
   * larger directions have been approved, rejected, or postponed,
   * accepted tasks have concrete verification requirements,
   * rejected or postponed ideas are preserved.

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
    refactoring-directions.md
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
Decision D-001: Planning posture

The council found both conservative cleanup topics and a larger module-level refactoring direction.

Which planning posture should the council use?

A. Conservative only: include high-value low-risk cleanup.
B. Risk-aware modular: include the larger direction as a human-approved refactoring direction, then split it into milestones.
C. Compare both options in the final plan.
D. Stop and let me narrow the scope.

Council recommendation: B.
Reason: The larger direction appears to address the root structural issue while still allowing phased, behavior-preserving implementation.
```

After invoking the `question` tool, stop. Resume only after receiving the human's answer.

## Human Decision Gates

The council is not required to be fully automatic.

At designated gates, the coordinator must ask the human for decisions that materially affect the refactoring plan.

In Interactive Mode, Human Decision Gates are hard stops.

In Automatic Mode, the coordinator may use conservative defaults and must record them.

A Human Decision Gate is mandatory when a decision materially affects:

* refactoring scope,
* planning posture,
* risk tolerance,
* design direction,
* public behavior preservation,
* architecture boundary choices,
* whether to include or exclude larger refactoring directions,
* whether to approve a Risk-Aware Modular direction,
* whether to accept a Level B task with constraints,
* whether to postpone unresolved Level C topics,
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

Goal: understand the request, target scope, repository context, constraints, likely verification commands, and planning posture.

The coordinator should inspect the repository with read-only commands when useful.

Write `.refactor-council/input.md` with:

```text
# Input

## User Request

## Target Scope

## Inferred Goal

## Planning Posture

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

## Larger Direction Signals

## Likely Verification Commands

## Unknowns
```

### Human Gate 0: Scope, Intent, Risk Preference, and Planning Posture

Trigger this gate before Round 1 if any of these are unclear and materially affect the plan:

* target scope,
* main refactoring goal,
* maximum acceptable risk,
* preference for small incremental PRs versus larger modular refactoring,
* whether Risk-Aware Modular Posture is allowed,
* behavior that must not change.

In Interactive Mode, ask with the `question` tool and stop.

In Automatic Mode, use conservative defaults and record them.

Possible questions:

```text
1. What is the target scope: file, module, feature area, or whole repository?
2. What is the main goal: readability, testability, architecture cleanup, reducing duplication, or preparing for future features?
3. What is the maximum acceptable risk level?
4. Should the council prefer small incremental PRs, or may it consider a larger module-level refactoring direction?
5. Are there public APIs, error messages, data formats, performance behavior, or undocumented behaviors that must not change?
```

If Automatic Mode is active and safe defaults are needed, use:

```text
- Use Conservative Incremental Posture.
- Prefer small incremental PRs.
- Preserve all external behavior.
- Do not change public APIs, error messages, data formats, storage semantics, authorization, or performance-sensitive behavior.
- Treat unclear behavior as behavior to preserve.
- Prefer Level A and conservative Level B tasks.
```

## Round 1: Independent Specialist Analysis

Goal: collect independent evidence-backed viewpoints.

Invoke each specialist independently. Do not include other specialists' conclusions in any Round 1 prompt.

Each specialist prompt must include:

* original user request,
* target scope,
* planning posture,
* relevant code/file context,
* known constraints,
* explicit instruction not to edit code,
* explicit instruction to use read-only inspection only,
* instruction to distinguish local tasks from larger directions,
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
- May indicate larger direction: yes/no

## Possible Larger Refactoring Directions

For each direction:
- Direction:
- Evidence:
- Why conservative cleanup may be insufficient:
- Potential value:
- Potential risk:
- Phasing possibility:
- Human decision needed: yes/no:
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

## Human Gate 1: Candidate Topic and Direction Selection

After Round 1, the coordinator aggregates findings into candidate topics and possible refactoring directions.

Each implementation-sized topic must have a stable ID:

```text
T-001, T-002, T-003, ...
```

Each larger direction must have a stable ID:

```text
R-001, R-002, R-003, ...
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
Related direction: R-xxx / none
```

Write `.refactor-council/round-2/refactoring-directions.md`.

Refactoring direction schema:

```text
## Direction R-001: <short name>

Source agents:
Problem:
Evidence:
Why conservative cleanup may be insufficient:
Proposed direction:
Scope boundary:
Out-of-scope:
Expected value:
Do-nothing cost:
Architecture impact:
Safety concerns:
Verification strategy:
Phasing / milestones:
Rollback strategy:
Estimated implementation shape:
Risk:
Human decision needed: yes/no
Council preliminary recommendation:
```

Trigger Human Gate 1 after Round 1 and before Round 2 if:

* more than 5 candidate topics are found,
* candidate topics span multiple modules,
* candidate topics mix low-risk cleanup with higher-risk architecture changes,
* one or more larger refactoring directions are found,
* the council found both narrow and broader possible plans,
* the target scope may be larger than the user intended,
* one or more specialists raised questions that materially affect topic or direction selection.

In Interactive Mode, ask the human which topics and directions should enter Round 2 using the `question` tool and stop.

Suggested options:

```text
A. Conservative only: include only high-value / low-risk implementation topics.
B. Risk-aware modular: include the larger direction as a candidate direction and require phased review.
C. Compare conservative and risk-aware options before final planning.
D. Include a specific list of topic IDs and direction IDs.
E. Stop and let me narrow the scope manually.
```

In Automatic Mode, default to:

```text
Focus on high-value / low-risk topics and conservative medium-risk topics with clear verification. Do not approve larger directions automatically.
```

Record the decision or default in `.refactor-council/human-decisions.md`.

## Round 2A: Cross-Review and Objections

Goal: make specialists challenge candidate topics and candidate directions from their role.

Ask each specialist to review the candidate list and direction list.

Round 2 review output:

```text
## Supported Topics

## Supported Directions

## Topics Accepted With Constraints

## Directions Acceptable With Constraints

## Material Objections

For each objection:
- ID:
- Objection:
- Why it matters:
- Required change to resolve:
- If unresolved, recommended classification:

## Rejected or Postponed Topics

## Rejected or Postponed Directions

## Required Verification Changes

## Safety Vetoes
```

Persist all challenges and objections in:

```text
.refactor-council/round-2/objections.md
```

## Safety Veto Rule

The Safety Guardian may veto a topic or direction when there is concrete unresolved risk to:

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
ID:
Reason:
Required changes to reconsider:
Minimum verification:
```

Rules:

1. A vetoed implementation topic cannot be Level A or Level B.
2. A vetoed refactoring direction cannot be approved.
3. A vetoed item can only re-enter the plan after being narrowed or constrained and re-reviewed by Safety Guardian.
4. If re-review is not completed, classify the item as unresolved, rejected, or postponed.

The Safety Guardian must not veto solely because an item is medium-sized or multi-step. Veto unresolved risk, not size.

## Material Objection Rule

If Architecture Reviewer, ROI Analyst, or Test Strategist raises a material objection, the coordinator must do one of:

1. revise the topic or direction and request targeted re-review,
2. classify it as unresolved, rejected, or postponed,
3. escalate it to Human Gate 2.

Do not silently ignore material objections.

## Round 2B: Topic / Direction Revision and Targeted Re-Review

Goal: transform debated topics and directions into safer, narrower, more executable proposals.

For each item with material objections:

1. summarize the objection,
2. narrow or constrain the topic/direction,
3. write a revised topic/direction,
4. request targeted re-review from the objecting specialist,
5. request Safety Guardian re-review if behavior-sensitive.

Write `.refactor-council/round-2/revised-topics.md`.

Revised item schema:

```text
## Revised Item <T-001 or R-001>

Original item:
Objections:
Revision:
New constraints:
Updated verification:
Updated phasing, if direction:
Remaining concerns:
Re-review result:
```

## Human Gate 2: Design Choices, Risk-Aware Directions, and Tradeoffs

After Round 2A/2B, ask the human when there are unresolved design choices or larger refactoring directions that materially affect the final plan.

Trigger this gate after Round 2A/2B and before final consensus if:

* a larger direction is plausible but requires human approval,
* a material architecture objection has multiple valid resolutions,
* Safety Guardian allows a topic or direction only under meaningful constraints,
* ROI Analyst recommends a larger direction that requires investment,
* ROI Analyst recommends postponing a topic that another agent considers important,
* the council must choose between conservative cleanup and risk-aware modular refactoring,
* the council must choose between local helper, module-local abstraction, or shared utility,
* the council must choose between smaller PRs and a larger coherent refactor,
* a Level B topic depends on human risk tolerance,
* two or more specialists disagree and more than one reasonable path remains.

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

Option C, if useful:
- Description:
- Pros:
- Cons:
- Risk:
- Verification impact:

Council recommendation:
Consequence if unanswered:
```

For larger directions, ask explicitly:

```text
Should the council treat R-xxx as an approved refactoring direction?

A. No. Keep only conservative tasks.
B. Yes, but require phased migration and characterization tests first.
C. Yes, and allow medium-risk milestones if rollback is clear.
D. Postpone R-xxx as future work.
```

In Automatic Mode, use the most conservative option that:

* preserves behavior,
* minimizes architecture disruption,
* keeps tasks small,
* avoids new abstractions unless clearly justified,
* has concrete verification,
* does not automatically approve larger directions.

Record the decision or default in `.refactor-council/human-decisions.md`.

## Round 3: Consensus Classification

Goal: classify each direction and task into a stable decision.

Write `.refactor-council/round-2/consensus.md`.

### Direction Classification

For each `R-xxx`, classify as:

```text
Direction Accepted by Human
- Human explicitly approved the direction.
- Safety vetoes are cleared.
- Architecture concerns are addressed or constrained.
- Verification strategy is concrete enough to phase.
- Direction is modular/feature-area scoped, not strategic/system-wide.

Direction Accepted with Constraints
- Human approved the direction with explicit constraints.
- Some objections remain but are manageable through phasing, verification, and scope control.
- The direction may shape milestones, but only Level A/B tasks may become implementation work.

Direction Needs More Investigation
- Direction may be valuable but lacks evidence, design clarity, verification path, or human approval.

Direction Rejected / Postponed
- Direction is unsafe, too broad, too strategic, too low-value, not modular, or declined by the human.
```

Direction consensus schema:

```text
## Direction R-001: <short name>

Classification:
Reason:
Human decision:
Accepted constraints:
Required phasing:
Required verification:
Risk:
Rejected alternatives:
```

### Task Classification

For each `T-xxx`, classify as:

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
- Human decision is resolved.
- Verification path is concrete.
- Risk is acceptable.

Level C: Unresolved / future work
- Useful idea but has unresolved design choice, missing evidence, unclear owner, unclear verification, or unanswered human decision.

Level D: Rejected
- Unsafe, too broad as a task, too low-value, behavior-changing, architecture-inconsistent, speculative, or not a refactoring.
```

In Interactive Mode, do not classify a topic as Level B if it depends on an unanswered human decision.

Task consensus schema:

```text
## Topic T-001: <short name>

Classification:
Reason:
Related direction:
Accepted constraints:
Required verification:
Risk:
Dependencies:
Human decisions:
Rejected alternatives:
```

## Human Gate 3: Final Plan Approval

Trigger this gate before invoking `refactoring-plan-synthesizer` if:

* any direction is accepted,
* any Level B task remains,
* any open question could affect implementation,
* the final plan would contain more than 3 implementation tasks,
* the highest risk level is medium or higher,
* the user requested review before finalization,
* the council made a non-trivial scope, posture, or design decision during consensus.

In Interactive Mode, ask whether to finalize, make the plan more conservative, make it more ambitious, or convert accepted tasks into issue-ready specs.

Suggested options:

```text
A. Finalize this plan.
B. Make the plan more conservative.
C. Make the plan more ambitious within the approved modular scope.
D. Produce only the final plan, not issue-ready tasks.
E. Produce both final plan and issue-ready tasks.
```

Use the `question` tool and stop after asking.

Do not invoke the synthesizer until the human answers.

In Automatic Mode, default to:

```text
Finalize the conservative plan and produce issue-ready tasks. Do not include unapproved larger directions.
```

Record the decision or default in `.refactor-council/human-decisions.md`.

## Round 4: Plan Synthesis

Invoke `refactoring-plan-synthesizer` with only:

* original request,
* `.refactor-council/input.md`,
* `.refactor-council/context.md`,
* Round 1 summaries,
* candidate topics,
* refactoring directions,
* objections,
* revised topics,
* consensus,
* human decisions,
* rejected or postponed ideas.

The synthesizer must not invent new implementation tasks.

The synthesizer may include an approved larger direction only if it is classified as:

* Direction Accepted by Human,
* Direction Accepted with Constraints.

The synthesizer may only include implementation tasks that were classified as:

* Level A,
* Level B.

The synthesizer must not include Level C or Level D topics as implementation tasks.

The synthesizer must not include rejected, postponed, or unapproved directions as active plan directions. Mention them under open questions or rejected/postponed ideas.

Write:

```text
.refactor-council/final-plan.md
```

Final plan required structure:

```text
# Refactoring Plan

## 1. Refactoring Goal

## 2. Planning Posture

## 3. Scope and Non-Goals

## 4. Current Problems

## 5. Approved Refactoring Direction, if any

## 6. Agreed Refactoring Strategy

## 7. Phased Milestones

For each milestone:
### Milestone N: <specific milestone>

Goal:
Scope:
Exit criteria:
Verification:
Risk:
Dependencies:

## 8. Step-by-Step Task Breakdown

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
Related direction / milestone:

## 9. Dependencies Between Tasks

## 10. Risk Summary

## 11. Required Tests / Verification

## 12. Rollback Strategy

## 13. Open Questions

## 14. Rejected or Postponed Ideas

## 15. Human Decisions Applied
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

## Related Direction / Milestone
```

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
Planning posture:
Approved directions:
Accepted task count:
Highest risk level:
Verification categories:
Rejected/postponed idea count:
Unresolved blockers:
Human decisions used:
```

Do not paste the entire final plan unless the user asks for it.
