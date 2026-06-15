---
description: Run the three-round refactoring council workflow
agent: refactoring-planning-coordinator
---

Use `refactoring-planning-coordinator` to run the Council Debate + Safety Veto + Structured Consensus + Plan Synthesizer workflow.

Follow `.opencode/docs/refactoring-council-protocol.md` if available. Produce artifacts under `.refactor-council/` in the target project.

User request:

```text
$ARGUMENTS
```

Requirements:

- Do not edit product code.
- Run Round 1 independently across the specialist subagents.
- Run Round 2 cross-review and explicitly process Safety Guardian vetoes.
- Run Round 3 through `refactoring-plan-synthesizer`.
- Final response should summarize artifact locations, accepted task count, highest risk level, verification categories, rejected/postponed count, and unresolved blockers.
