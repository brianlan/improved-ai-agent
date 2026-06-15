# Engineering Notes

## Why This Is a Protocol, Not Only Prompts

Multi-agent refactoring planning fails when the agents share a long conversation without structure. The council should persist intermediate artifacts so disagreements, vetoes, and rejected ideas are auditable.

The coordinator is responsible for orchestration. The specialist prompts are responsible for viewpoint discipline. The schemas are responsible for making the output checkable.

## Recommended Implementation Phases

### Phase 1: Prompt-Only MVP

Use the `.opencode/agent` definitions and the `/refactor-council` command. The coordinator writes markdown artifacts and manually enforces the protocol.

This is enough to test whether the roles are useful and whether the final plans are more actionable than a single-agent plan.

### Phase 2: Lightweight Validation

Add a script that validates:

- required artifact files exist,
- final plan contains all required sections,
- every accepted task has safety constraints and verification,
- no safety-vetoed topic appears as an accepted task,
- rejected/postponed ideas are present.

The validator should not use an LLM. It should check files and structured frontmatter or JSON blocks.

### Phase 3: Structured Candidate Topics

Have the coordinator maintain `round-2/candidate-topics.json` using `.opencode/schemas/candidate-topic.schema.json`.

This makes Safety veto enforcement mechanical:

```text
safety_veto = true => consensus_level must be C or D
```

### Phase 4: Orchestration Script

Add a small runner that dispatches OpenCode prompts in sequence, stores outputs, and invokes validation. Keep the runner deterministic. It should orchestrate, not decide.

## Practical Defaults

- Keep specialists read-only.
- Let specialists use read-only shell commands when the project is large.
- Start with five specialists. Add more only after seeing repeated missing concerns.
- Limit debate to three rounds.
- Prefer narrow tasks that map to pull requests.
- Treat unresolved uncertainty as a plan output, not a failure.

## Failure Modes

### Agents Agree Too Easily

Tighten Round 2 prompts. Require each specialist to name at least one risk or explicitly say why there is no material risk.

### Plans Become Too Broad

Give ROI Analyst stronger authority to split or postpone work. Require every task to fit in a focused pull request.

### Safety Blocks Everything

Require Safety Guardian to provide constraints that would make a task acceptable where possible. Veto should be for concrete unresolved risk, not generic caution.

### Synthesizer Invents New Work

Compare final tasks against Round 2 consensus. Any task without a source candidate topic should be removed.

## Naming

Use planning-oriented names:

- `refactoring-planning-coordinator`
- `refactoring-plan-synthesizer`
- `refactoring-safety-guardian`
- `refactoring-test-strategist`

Avoid names like `refactoring-executor` unless the agent is allowed to edit code.
