# Council Debate Protocol

## Purpose

The council creates behavior-preserving refactoring plans. It is designed for cases where a single-agent plan would miss architecture risks, behavior regressions, low-value churn, or missing verification.

## Roles

### Coordinator

The coordinator chairs the process. It understands the user request, defines the code scope, invokes specialists, aggregates findings, requests challenges, enforces veto rules, and hands only accepted material to the synthesizer.

The coordinator must not produce a final plan until:

- specialists have completed independent analysis,
- candidate topics have been classified,
- safety objections are explicitly handled,
- verification requirements are attached to accepted tasks,
- rejected ideas are preserved.

### Specialists

Specialists produce evidence-backed analysis from their assigned viewpoint:

- Code Smell Analyst: local maintainability issues.
- Architecture Reviewer: module boundaries, dependency direction, and abstraction fit.
- Safety Guardian: behavior preservation, contracts, data, security, performance, concurrency, rollout.
- Test Strategist: characterization tests, unit tests, integration tests, golden tests, manual checks.
- ROI Analyst: value, complexity, sequencing, postponement, and overengineering risk.

### Plan Synthesizer

The synthesizer writes the final plan from accepted council artifacts only. It must not add new refactoring tasks, broaden scope, or remove constraints.

## Round 1: Independent Analysis

Each specialist receives the original request and relevant code context. Specialists must not receive other specialists' conclusions in this round.

Required output:

```text
## Observations
## Proposed Refactoring Opportunities
## Risks
## Verification Needs
## Confidence
## Questions / Uncertainties
```

Every proposed opportunity should include evidence, likely files, and a narrow statement of intended behavior preservation.

## Round 2: Cross-Review and Consensus

The coordinator converts Round 1 findings into candidate topics. Each specialist reviews the candidate list and responds with:

```text
## Supported Topics
## Topics Accepted With Constraints
## Objections
## Rejected or Postponed Topics
## Required Verification Changes
## Safety Vetoes
```

Candidate topics are classified into one of four levels:

- Level A: accepted. No material objections.
- Level B: accepted with constraints. Objections are addressed by explicit constraints.
- Level C: unresolved. Mention as future work or open question, not an implementation task.
- Level D: rejected. Unsafe, too broad, low-value, or inconsistent with architecture.

## Safety Veto

Safety Guardian may veto a candidate topic when there is a concrete risk to behavior, public contracts, data integrity, performance-sensitive paths, security, permissions, concurrency, caching, transactions, or rollout safety.

Veto format:

```text
Veto: yes
Topic:
Reason:
Required changes to reconsider:
Minimum verification:
```

Rules:

- A vetoed topic cannot be Level A or Level B.
- A vetoed topic can only re-enter the plan after being narrowed or constrained and re-reviewed by Safety Guardian.
- If time or budget prevents re-review, the topic must be Level C or Level D.

## Round 3: Plan Synthesis

The synthesizer receives:

- original request,
- Round 1 reports,
- Round 2 consensus,
- accepted constraints,
- unresolved questions,
- rejected or postponed ideas.

The final plan must include:

```text
1. Refactoring goal
2. Scope and non-goals
3. Current problems
4. Agreed refactoring strategy
5. Step-by-step task breakdown
6. Dependencies between tasks
7. Risk level per task
8. Required tests / verification
9. Rollback strategy
10. Open questions
11. Rejected or postponed ideas and why
```

## Task Format

Each accepted task should use this structure:

```text
Task N: <specific action>

Why:
Scope:
Files likely involved:
Safety constraints:
Verification:
Risk:
Dependencies:
```

Tasks should be small enough to implement in a focused pull request. If a task requires multiple unrelated behavior-sensitive changes, split it.

