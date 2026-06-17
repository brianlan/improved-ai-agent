---
description: Run a human-in-the-loop, risk-aware refactoring council workflow
agent: refactoring-planning-coordinator
---

Use `refactoring-planning-coordinator` to run the Human-in-the-Loop Refactoring Council workflow.

This command is the authoritative protocol for the council. Do not require a separate `refactoring-council-protocol.md`.

User request:

```text
$ARGUMENTS
```

# Refactoring Council Protocol

## 1. Purpose

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
- unspoken human preferences,
- larger but worthwhile refactoring directions,
- insufficiently challenged proposals,
- approved directions that are not represented as executable work.

## 2. Scope of This Council

The council supports:

- small conservative refactoring,
- medium module-level refactoring,
- feature-area refactoring,
- multi-PR modular refactoring,
- human-approved risk-aware refactoring directions,
- behavior-preserving phased migrations inside a bounded module or feature area.

The council does not support:

- whole-system architecture redesign,
- multi-team platform strategy,
- broad product strategy,
- rewrites without incremental migration,
- refactoring plans that require behavior changes as a hidden dependency,
- unbounded "clean up the whole codebase" efforts.

A larger refactoring direction must not be rejected merely because it is larger than one PR.

A larger refactoring direction must be rejected, postponed, or escalated only when:

- evidence is weak,
- the value is unclear,
- the behavior boundary is unclear,
- architecture direction is unjustified,
- verification is not feasible,
- rollback is not feasible,
- the scope is strategic/system-wide rather than modular,
- the human declines the risk or investment.

## 3. Planning Posture

The council supports two planning postures.

### Conservative Incremental Posture

This is the default posture.

Use it when:

- the user asks for normal refactoring,
- the scope is small,
- risk tolerance is unclear,
- public behavior is sensitive,
- the council lacks enough evidence for a larger direction.

This posture prefers:

- small focused PRs,
- Level A tasks,
- conservative Level B tasks,
- behavior-preserving changes,
- minimal architecture movement,
- strong verification before movement.

### Risk-Aware Modular Posture

Use this posture when:

- the user explicitly asks to consider medium or larger refactoring,
- the council finds a larger direction with strong evidence and meaningful long-term value,
- conservative cleanup would leave the core structural problem unsolved,
- a module-level or feature-area boundary change appears justified,
- the larger direction can be phased into safe milestones,
- the human approves the risk-aware direction.

Risk-Aware Modular Posture does not mean reckless refactoring.

It means the council may surface a larger refactoring direction, explain its value, cost, risk, migration path, and verification requirements, then ask the human whether to approve it.

In this posture:

- large directions are represented as `Refactoring Direction` entries, not direct implementation tasks,
- approved directions must be decomposed into milestones,
- milestones must be decomposed into focused implementation tasks,
- each task must still preserve behavior and have verification,
- Safety Guardian veto rules still apply,
- human approval is required before a larger direction can shape the final plan.

## 4. Direction vs Task

The council must distinguish between `Refactoring Direction` and `Implementation Task`.

### Refactoring Direction

A Refactoring Direction is a larger design or module-level path.

Examples:

- Restructure validation flow inside a module.
- Split a large service into domain-local components.
- Introduce a module-local facade to simplify call sites.
- Gradually migrate duplicated logic behind a single internal interface.
- Reorganize feature-area boundaries to reduce dependency direction problems.

A Refactoring Direction:

- may span multiple PRs,
- may require multiple milestones,
- may be too large for one task,
- may require human approval,
- must include value, risk, migration, verification, and rollback discussion,
- must not be implemented as one broad task.

Use IDs:

```text
R-001, R-002, R-003, ...
```

### Implementation Task

An Implementation Task is a focused, executable step.

Examples:

- Add characterization tests for current validation behavior.
- Extract pure validation helper inside the existing module.
- Route one call path through the new module-local facade.
- Migrate one group of call sites.
- Remove old internal helper after parity verification.

An Implementation Task:

- should be small enough for a focused PR,
- must preserve behavior,
- must have acceptance criteria,
- must have verification,
- must have a do-not-do list,
- must have rollback notes.

Use IDs:

```text
T-001, T-002, T-003, ...
```

A larger Refactoring Direction can be approved, but only Level A or Level B implementation tasks may enter the executable final plan.

## 5. Approved Direction Coverage Rule

Every approved direction must be represented by executable work.

If a direction is classified as:

- `Direction Accepted by Human`, or
- `Direction Accepted with Constraints`,

then the final plan must include at least one of the following:

1. one or more Level A/B implementation tasks that directly implement the first milestone of the direction,
2. one or more Level A/B enabler tasks that explicitly unblock the direction,
3. a dedicated investigation/spike issue if implementation is not yet safe.

An approved direction must not appear only as descriptive text.

If a direction is approved but has no executable task, the coordinator must do one of:

- create an explicit first-milestone task,
- create an investigation/spike task,
- downgrade the direction to `Needs More Investigation`,
- ask the human whether to postpone the direction.

The synthesizer must fail its self-check if an approved direction has no corresponding issue-ready task.

## 6. Direction Status Precision Rule

The council must distinguish:

```text
Approved direction
Approved direction with constraints
Postponed direction
Rejected direction
Approved limited enabling task toward a postponed direction
```

Do not label a task as "R-xxx step" if R-xxx itself is postponed.

Instead write:

```text
Related postponed direction: R-xxx
Approved limited enabling task: T-yyy
This task does not approve the full direction.
```

## 7. Interaction Mode

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

- `--auto`
- `fully automatic`
- `run automatically`
- `do not ask me questions`
- `use defaults`
- `proceed without asking`

In Automatic Mode, the coordinator may use conservative defaults at Human Decision Gates, but it must record every default in `.refactor-council/human-decisions.md`.

If the user has not explicitly requested Automatic Mode, the coordinator must assume Interactive Mode.

## 8. Required Roles

The coordinator must invoke these specialist agents unless one is unavailable:

- `refactoring-code-smell-analyst`
- `refactoring-architecture-reviewer`
- `refactoring-safety-guardian`
- `refactoring-test-strategist`
- `refactoring-roi-analyst`
- `refactoring-plan-synthesizer`

If an agent is unavailable, the coordinator must explicitly state which role is missing and preserve that role's concerns in its own checklist before continuing.

## 9. Artifact Layout

Create or provide these artifacts:

```text
.refactor-council/
  state.md
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
    objection-resolution.md
    revised-topics.md
    consensus.md
  final-plan.md
  issue-ready-tasks.md
  artifact-self-check.md
```

If artifact writing is unavailable, provide the artifacts in the response with exact intended file paths.

## 10. State Artifact

The coordinator must maintain:

```text
.refactor-council/state.md
```

State schema:

```text
# Council State

Current round:
Last completed step:
Pending gate:
Pending decision ID:
Interaction mode:
Planning posture:
Approved directions:
Open blockers:
Subagent status:
Failure recovery notes:
Next action:
Last updated:
```

The coordinator must update `state.md` when:

- Round 0 starts or completes,
- a Human Decision Gate is triggered,
- a human answer is recorded,
- Round 1 starts or completes,
- Round 2A starts or completes,
- Round 2B starts or completes,
- consensus starts or completes,
- synthesis starts or completes,
- a subagent fails or produces unusable output,
- a scope explosion is detected,
- the workflow stops.

On resume, the coordinator must read `state.md` first.

## 11. Non-Negotiable Rules

1. Do not edit product code.
2. Do not edit tests, configs, docs, or source files outside `.refactor-council/`.
3. Only create or update council artifacts under `.refactor-council/`.
4. Bash commands must be read-only inspection commands.
5. Do not run formatters, fixers, dependency installers, migrations, generators, or commands that modify the working tree.
6. In Interactive Mode, do not continue past a triggered Human Decision Gate until the human answers.
7. In Interactive Mode, do not replace a Human Decision Gate with a default.
8. Do not produce a final plan until:
   - independent specialist analysis is complete,
   - candidate topics and directions have stable IDs,
   - material objections have been processed,
   - objection resolutions have been recorded,
   - safety vetoes have been handled,
   - all triggered human decision gates have been answered,
   - larger directions have been approved, rejected, postponed, or downgraded,
   - approved directions have executable task coverage,
   - accepted tasks have concrete verification requirements,
   - rejected or postponed ideas are preserved,
   - artifact self-check passes.

## 12. Question Tool Requirement

For every Human Decision Gate in Interactive Mode, the coordinator must use the `question` tool.

If the `question` tool is unavailable, the coordinator must stop and ask the question in the normal response, clearly marked as a blocking Human Decision Gate. The coordinator must not continue.

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

## 13. Failure Recovery Rules

### Malformed Subagent Output

If a subagent output does not follow the required format:

1. ask the same subagent once for corrected output,
2. if still malformed, extract only usable content,
3. mark the role's confidence as low,
4. record the issue in `state.md`,
5. continue only if that role's critical concerns are preserved.

### Subagent Violates Role

If a subagent proposes editing code, changing files, running unsafe commands, or exceeding scope:

1. ignore the unsafe action,
2. preserve only relevant analysis,
3. record the role violation in `state.md`,
4. do not treat the unsafe proposal as accepted council material.

### Hallucinated or Unverified Files

If a subagent references files not found in repository context:

1. mark the evidence as unverified,
2. do not use it as decisive evidence,
3. verify with read/glob/grep if permitted,
4. otherwise record it under unknowns.

### Scope Explosion

If Round 1 produces more than 12 candidate topics or more than 4 candidate directions:

1. record scope explosion risk in `state.md`,
2. trigger Human Gate 1,
3. ask the human to narrow, batch, or select topics/directions.

### Objection Loop

Limit targeted re-review to 2 cycles per item.

If unresolved after 2 cycles:

- escalate to human,
- classify as Needs More Investigation,
- or postpone.

Do not keep revising indefinitely.

## 14. Human Decision Gates

A Human Decision Gate is mandatory when a decision materially affects:

- refactoring scope,
- planning posture,
- risk tolerance,
- design direction,
- public behavior preservation,
- architecture boundary choices,
- whether to include or exclude larger refactoring directions,
- whether to approve a Risk-Aware Modular direction,
- whether an approved direction lacks executable coverage,
- whether to accept a Level B task with constraints,
- whether to postpone unresolved Level C topics,
- whether to produce issue-ready tasks.

## 15. Round 0: Intake and Context Collection

Goal: understand the request, target scope, repository context, constraints, likely verification commands, and planning posture.

Write `.refactor-council/input.md`:

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

Write `.refactor-council/context.md`:

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

- target scope,
- main refactoring goal,
- maximum acceptable risk,
- preference for small incremental PRs versus larger modular refactoring,
- whether Risk-Aware Modular Posture is allowed,
- behavior that must not change.

Suggested options:

```text
A. Conservative only: analyze high-value low-risk cleanup.
B. Risk-aware modular: allow larger module-level directions if evidence supports them.
C. Compare conservative and risk-aware options.
D. Stop and let me specify a narrower scope.
```

## 16. Round 1: Independent Specialist Analysis

Invoke each specialist independently.

Do not include other specialists' conclusions in any Round 1 prompt.

Each Round 1 prompt must include:

- original user request,
- target scope,
- planning posture,
- relevant code/file context,
- known constraints,
- explicit instruction not to edit code,
- explicit instruction to use read-only inspection only,
- instruction to distinguish implementation-sized tasks from larger refactoring directions,
- required Round 1 output format.

If the task tool supports parallel subagent invocation, Round 1 analyses may be invoked in parallel. If not, invoke sequentially, but do not share Round 1 results between specialists.

Persist each result:

```text
.refactor-council/round-1/code-smell.md
.refactor-council/round-1/architecture.md
.refactor-council/round-1/safety.md
.refactor-council/round-1/testability.md
.refactor-council/round-1/roi.md
```

## 17. Round 1 Required Output Format

Each specialist should return:

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
- Human decision needed: yes/no
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

## 18. Candidate Topic and Direction Creation

Every implementation-sized topic must have a stable ID:

```text
T-001, T-002, T-003, ...
```

Every larger direction must have a stable ID:

```text
R-001, R-002, R-003, ...
```

Write `.refactor-council/round-2/candidate-topics.md`.

Topic schema:

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

Direction schema:

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
Initial executable coverage:
Risk:
Human decision needed: yes/no
Council preliminary recommendation:
```

## 19. Human Gate 1: Candidate Topic and Direction Selection

Trigger this gate after Round 1 and before Round 2 if:

- more than 12 candidate topics are found,
- more than 4 candidate directions are found,
- candidate topics span multiple modules,
- candidate topics mix low-risk cleanup with higher-risk architecture changes,
- one or more larger refactoring directions are found,
- the council found both narrow and broader possible plans,
- the target scope may be larger than the user intended.

Suggested options:

```text
A. Conservative only: include only high-value / low-risk implementation topics.
B. Risk-aware modular: include the larger direction as a candidate direction and require phased review.
C. Compare conservative and risk-aware options before final planning.
D. Include a specific list of topic IDs and direction IDs.
E. Stop and let me narrow the scope manually.
```

## 20. Round 2A: Cross-Review and Objections

Ask each specialist to review candidate topics and candidate directions from their role.

Round 2 output format:

```text
## Supported Topics

For each topic:
- ID:
- Support reason:
- Strongest condition for support:

## Supported Directions

For each direction:
- ID:
- Support reason:
- Strongest condition for support:
- Required executable coverage:

## Topics Accepted With Constraints

For each topic:
- ID:
- Constraints:
- What would make this unacceptable:

## Directions Acceptable With Constraints

For each direction:
- ID:
- Constraints:
- Required milestone/task coverage:
- What would make this unacceptable:

## Material Objections

For each objection:
- Objection ID:
- Raised by:
- Target ID:
- Objection:
- Why it matters:
- Required change to resolve:
- If unresolved, recommended classification:

## Rejected or Postponed Topics

## Rejected or Postponed Directions

## Required Verification Changes

## Safety Vetoes
```

Persist results in:

```text
.refactor-council/round-2/objections.md
```

## 21. Safety Veto Rule

Safety vetoes may be full or partial.

Safety veto format:

```text
- Veto: yes
- ID:
- Veto scope: full item / partial scope
- Vetoed part, if partial:
- Severity: critical / high / medium
- Reason:
- Required changes to reconsider:
- Minimum verification:
- Recommended path:
```

Rules:

1. A full vetoed implementation topic cannot be Level A or Level B.
2. A full vetoed direction cannot be approved.
3. A partial veto requires the vetoed part to be removed, postponed, or isolated before the remaining item can proceed.
4. Critical vetoes require Safety Guardian re-review.
5. High and medium vetoes require either targeted re-review or explicit objection-resolution documentation.
6. If re-review is not completed, classify the item as unresolved, rejected, or postponed.
7. Veto unresolved risk, not size.

## 22. Round 2B: Objection Resolution, Revision, and Targeted Re-Review

Write:

```text
.refactor-council/round-2/objection-resolution.md
```

Every material objection and every safety veto must have a resolution entry.

Objection resolution schema:

```text
## Objection OBJ-001: <short name>

Raised by:
Target ID:
Original proposal:
Objection:
Why it matters:
Strongest supporting argument for original proposal:
Coordinator response:
Revision made:
Re-review requested from:
Re-review result:
Human decision, if any:
Final resolution:
Final classification impact:
```

Resolution status must be one of:

```text
Resolved by revision
Resolved by added constraint
Resolved by human decision
Resolved by partial veto narrowing
Not resolved — postponed
Not resolved — rejected
Not resolved — needs more investigation
```

Write `.refactor-council/round-2/revised-topics.md`.

Revised item schema:

```text
## Revised Item <T-001 or R-001>

Original item:
Objections:
Strongest supporting argument:
Revision:
New constraints:
Updated verification:
Updated phasing, if direction:
Updated executable coverage, if direction:
Vetoed parts removed, if any:
Remaining concerns:
Re-review requested from:
Re-review result:
```

Do not proceed to consensus until every material objection and safety veto has an objection-resolution entry.

## 23. Human Gate 2: Design Choices, Risk-Aware Directions, and Tradeoffs

Trigger this gate after Round 2A/2B and before final consensus if:

- a larger direction is plausible but requires human approval,
- an approved direction lacks executable coverage,
- a material architecture objection has multiple valid resolutions,
- Safety Guardian allows a topic or direction only under meaningful constraints,
- ROI Analyst recommends a larger direction that requires investment,
- the council must choose between conservative cleanup and risk-aware modular refactoring,
- the council must choose between local helper, module-local abstraction, or shared utility,
- a Level B topic depends on human risk tolerance,
- two or more specialists disagree and more than one reasonable path remains.

For larger directions, ask explicitly:

```text
Should the council treat R-xxx as an approved refactoring direction?

A. No. Keep only conservative tasks.
B. Yes, but require phased migration and characterization tests first.
C. Yes, and allow medium-risk milestones if rollback is clear.
D. Postpone R-xxx as future work.
E. Approve only an investigation/spike issue, not implementation yet.
```

If an approved direction lacks executable coverage, ask:

```text
R-xxx is approved as a direction, but it currently has no executable Level A/B task.

How should the council handle this?

A. Add a first-milestone implementation task.
B. Add an investigation/spike issue.
C. Downgrade the direction to Needs More Investigation.
D. Postpone the direction.
```

## 24. Round 3: Consensus Classification

Write:

```text
.refactor-council/round-2/consensus.md
```

### Direction Classification

For each `R-xxx`, classify as:

```text
Direction Accepted by Human
- Human explicitly approved the direction.
- Safety vetoes are cleared.
- Architecture concerns are addressed or constrained.
- Verification strategy is concrete enough to phase.
- Direction is modular/feature-area scoped, not strategic/system-wide.
- Direction has executable task coverage or an approved investigation/spike issue.

Direction Accepted with Constraints
- Human approved the direction with explicit constraints.
- Some objections remain but are manageable through phasing, verification, and scope control.
- The direction may shape milestones, but only Level A/B tasks may become implementation work.
- Direction has executable task coverage or an approved investigation/spike issue.

Direction Needs More Investigation
- Direction may be valuable but lacks evidence, design clarity, verification path, human approval, or executable task coverage.

Direction Rejected / Postponed
- Direction is unsafe, too broad, too strategic, too low-value, not modular, declined by the human, or not represented by executable work.
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
Executable coverage:
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
- Useful idea but has unresolved design choice, missing evidence, unclear owner, unclear verification, unanswered human decision, or missing direction coverage.

Level D: Rejected
- Unsafe, too broad as a task, too low-value, behavior-changing, architecture-inconsistent, speculative, or not a refactoring.
```

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

### Consensus Consistency Rules

Before finalizing consensus:

1. Count each listed item and make sure summary counts match actual entries.
2. Do not include an ID in a summary if no detailed entry exists.
3. Do not mark a direction as accepted if it lacks executable coverage.
4. Do not mark a task as Level A/B if it has unresolved material objections.
5. Do not mark a task as Level A/B if verification is vague.
6. Preserve rejected and postponed ideas.

## 25. Human Gate 3: Final Plan Approval

Trigger this gate before invoking `refactoring-plan-synthesizer` if:

- any direction is accepted,
- any Level B task remains,
- any open question could affect implementation,
- the final plan would contain more than 3 implementation tasks,
- the highest risk level is medium or higher,
- the user requested review before finalization,
- the council made a non-trivial scope, posture, or design decision during consensus.

Suggested options:

```text
A. Finalize this plan.
B. Make the plan more conservative.
C. Make the plan more ambitious within the approved modular scope.
D. Produce only the final plan, not issue-ready tasks.
E. Produce both final plan and issue-ready tasks.
```

## 26. Round 4: Plan Synthesis

Invoke `refactoring-plan-synthesizer` with only:

- original request,
- input artifact,
- context artifact,
- Round 1 summaries,
- candidate topics,
- refactoring directions,
- objections,
- objection-resolution,
- revised topics,
- consensus,
- human decisions,
- rejected or postponed ideas.

The synthesizer must not invent new implementation tasks.

The synthesizer may include an approved larger direction only if it is classified as:

- Direction Accepted by Human,
- Direction Accepted with Constraints.

Only Level A and Level B topics may become implementation tasks.

Persist:

```text
.refactor-council/final-plan.md
.refactor-council/issue-ready-tasks.md
.refactor-council/artifact-self-check.md
```

## 27. Artifact Self-Check

Before final response, write `.refactor-council/artifact-self-check.md`.

Required checks:

```text
# Artifact Self-Check

## Markdown Integrity

- [ ] Every fenced code block is closed.
- [ ] No issue section is accidentally inside a code block.
- [ ] No nested code fence breaks copy-paste rendering.
- [ ] Tables render correctly.

## Consensus Consistency

- [ ] Consensus summary counts match actual detailed entries.
- [ ] Every accepted direction has executable coverage.
- [ ] Every Level A/B task appears in issue-ready tasks.
- [ ] No Level C/D task appears as executable work.
- [ ] No postponed direction is labeled as an approved direction.

## Direction Coverage

For each approved direction:
- Direction ID:
- Covered by issue(s):
- Covered by milestone(s):
- Coverage type: implementation / enabler / investigation

## Verification Specificity

- [ ] Every issue has verification commands or explicit reason commands are unavailable.
- [ ] Every manual verification section has concrete steps and expected results.
- [ ] Medium-risk tasks include rollback notes.
- [ ] Behavior-sensitive tasks include characterization or parity verification.

## Traceability

- [ ] Every material objection appears in objection-resolution.md.
- [ ] Every resolved objection links to revised topic/direction or human decision.
- [ ] Every human decision used in final plan appears in human-decisions.md.
- [ ] Rejected/postponed ideas are preserved.
```

If any check fails, fix the artifact before returning.

## 28. Final Response Rule

If the workflow stops at a Human Decision Gate, the final response for that turn must contain only:

```text
The council has reached <Gate Name> and needs your decision before continuing.
```

Then ask the question using the `question` tool.

Do not summarize later rounds.

Do not claim the final plan is complete.

Do not create `.refactor-council/final-plan.md`.

Do not invoke `refactoring-plan-synthesizer`.

If the workflow completes, return a concise summary:

```text
Final plan: .refactor-council/final-plan.md
Issue-ready tasks: .refactor-council/issue-ready-tasks.md
Artifact self-check: .refactor-council/artifact-self-check.md
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