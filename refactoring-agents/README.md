# Refactoring Agents

This repository defines an OpenCode-based council workflow for producing high-quality refactoring plans. The agents do not edit code. They inspect, debate, classify risk, and synthesize an implementation plan with explicit verification requirements.

## Architecture

The default workflow is:

```text
User request
  -> refactoring-planning-coordinator
  -> Round 1: independent specialist analysis
  -> Round 2: cross-review, constraints, and safety veto
  -> Round 3: structured consensus and plan synthesis
  -> Final refactoring plan
```

Agents:

- `refactoring-planning-coordinator`: primary chair that runs the protocol and enforces rules.
- `refactoring-code-smell-analyst`: finds local maintainability and code-quality issues.
- `refactoring-architecture-reviewer`: evaluates boundaries, dependencies, and architecture fit.
- `refactoring-safety-guardian`: protects behavior, contracts, data, performance, security, and rollout safety.
- `refactoring-test-strategist`: defines how the plan proves behavior is preserved.
- `refactoring-roi-analyst`: ranks work by value, complexity, scope, and sequencing.
- `refactoring-plan-synthesizer`: writes the final plan from accepted council material only.

## OpenCode Usage

Run OpenCode from a target project and ask for the council workflow with the coordinator agent. The coordinator should invoke the specialist subagents and write artifacts under `.refactor-council/` in the target project.

Example request:

```text
Use refactoring-planning-coordinator to create a refactoring plan for src/order without changing behavior.
```

If you copy this repository's `.opencode` directory into a project, OpenCode can load the agent definitions, command template, protocol docs, schemas, and examples from project-specific configuration.

The reusable command template lives at `.opencode/commands/refactor-council.md` and uses `$ARGUMENTS` for the user request.

## Outputs

Each council run should create:

```text
.refactor-council/
  input.md
  round-1/
    code-smell.md
    architecture.md
    safety.md
    testability.md
    roi.md
  round-2/
    candidate-topics.md
    objections.md
    consensus.md
  final-plan.md
```

The final plan must include rejected or postponed ideas. That prevents future implementors from repeating discarded analysis.

## Design Rules

- Specialists propose and review plans; they do not edit code.
- Round 1 is independent. Specialists should not see each other's findings.
- Safety Guardian can veto a topic. Vetoed topics cannot appear as accepted work.
- Plan Synthesizer cannot invent tasks that were not accepted in council material.
- Every accepted task needs scope, safety constraints, verification, risk, and dependencies.
- Uncertainties must stay visible instead of being smoothed into false confidence.
