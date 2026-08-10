---
name: compile-requirement
description: Convert an initial feature, product, or system requirement into a validated, implementation-neutral, ready-to-use requirement specification through phased investigation and iterative clarification. Use when the user wants to clarify, compile, formalize, or refine requirements, acceptance criteria, constraints, workflows, or a PRD-style specification before implementation.
---

# Compile Requirement

Turn the user's initial requirement into a precise specification at the behavior and externally observable outcomes level. Work interactively and stop whenever user input is required.

Create a plan with one item for each of the six phases below when a planning tool is available. Keep exactly one phase in progress and complete each phase before advancing.

## Maintain the Abstraction Contract

Specify what the system must do and guarantee without prescribing how to build it.

Allow:

- User journeys, workflows, and state transitions
- Domain entities and conceptual definitions
- Constraints, invariants, policies, and compliance, security, or privacy requirements
- Error classes and observable failure-handling outcomes
- Measurable performance, reliability, availability, throughput, and cost outcomes
- Observable and auditable evidence, without instrumentation design
- Rollout, migration, and backward-compatibility outcomes
- Conceptual component labels only when they clarify responsibility

Exclude unless explicitly mandated by the user:

- Code, algorithms, classes, variables, modules, or file layouts
- Database schemas, tables, or columns
- API endpoints and routes
- UI wireframes, screen layouts, or pixel-level specifications
- Vendor or service selections
- Step-by-step implementation instructions

Apply this test: a competent engineer must be able to change the implementation approach while still satisfying every requirement.

## Apply Quality Gates

Before finalizing each shall requirement, verify that it is:

- Atomic: expresses one idea
- Unambiguous: replaces vague qualities with defined measures
- Observable and testable: identifies evidence of satisfaction
- Necessary: traces to a goal or use case
- Feasible within confirmed constraints
- Traceable to a goal or scenario

## Follow the Phases

### Phase 1: Restate and Scope

Rephrase the request. Identify the goals, constraints, unknowns, and intended audience.

Ask the user:

- Who will consume the specification: product, engineering, a cross-team group, a vendor, or someone else?
- What hard constraints apply, including platform, compliance, mandated technology, and timeline?
- What evidence or success metrics will prove the work is done?

Use the available structured question tool when practical; otherwise ask concise plain-text questions. Wait for the answers before continuing.

End the phase with a scope block containing:

- In scope
- Initial out of scope and non-goals
- Key risks and unknowns

### Phase 2: Validate Constraints and Facts

Investigate only enough to validate relevant facts and constraints; do not expand scope. Inspect applicable local files, project structure, configuration, documentation, RFCs, runtime constraints, and authoritative external references.

Report:

- Confirmed facts and constraints
- Remaining unknowns
- Assumptions that require user confirmation

### Phase 3: Ask Clarifying Questions, Round 1

Ask focused questions that unlock acceptance criteria, define actors and entities, establish boundaries, and clarify constraints and failure modes. Prefer a small set of high-impact questions. Wait for the user's answers.

### Phase 4: Iterate and Cross-check

For each answer cycle:

1. Reinspect relevant evidence.
2. Validate or correct assumptions.
3. Identify only uncertainties revealed by the answers.
4. Summarize what is known, what remains unknown, and which assumptions changed.
5. Ask the next focused questions and wait.

Ensure every cycle narrows uncertainty. Do not enter Phase 5 until the user explicitly says to move to the next phase, proceed to Phase 5, or gives an equivalent clear instruction. If uncertainty is already narrow, ask the user for that explicit approval rather than advancing automatically.

### Phase 5: Ask Final Tradeoff Questions

After explicit approval, confirm:

- Priority tradeoffs such as latency, cost, and correctness
- Edge cases and non-goals
- Outcome-level UX and developer-experience expectations
- Rollout, migration, and backward-compatibility expectations
- Behavior-affecting compliance, security, and privacy requirements

Wait for the answers before generating the specification.

### Phase 6: Generate the Requirement Document

Produce an implementation-guiding but implementation-neutral document with this structure:

1. **Outcomes (Why)**
   - Problem statement
   - Objectives and success metrics
   - Stakeholders and target users
2. **Capabilities (What)**
   - Primary workflows and user journeys
   - System responsibilities and boundaries
   - Conceptual domain entities and definitions
   - Explicit assumptions and constraints
3. **Requirements (Shall)**
   - Functional requirements
   - Non-functional requirements: performance, reliability, security, privacy, and cost
   - Data and domain definitions
   - Observability and auditability
   - Operations and lifecycle: deployment, migration, rollback, and support
   - Edge cases and failure handling
   - Non-goals

Write atomic statements in the form `The system shall ...`. Give every requirement a stable identifier and acceptance criteria.

End with:

- Acceptance criteria, including measurable test evidence
- Decision log with rationale
- Open questions labeled blocking or non-blocking
- Traceability mapping requirements to goals or use cases

Run the quality gates across all shall requirements before presenting the document. Remove implementation details that violate the abstraction contract unless they are explicit user constraints; label mandated implementation constraints as such.
