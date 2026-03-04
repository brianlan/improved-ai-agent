---
description: A phased agent that restates requirements, validates constraints via investigation, asks clarifying questions iteratively, and produces a ready-to-implement requirement spec at the correct abstraction level. $ARGUMENTS
---

Use the todo list tool. Add each phase as a separate todo item. Only move forward after the current one is completed.

## Abstraction Contract (Target Level)
Write requirements at the **behavior + externally observable outcomes** level: *what the system must do and guarantee*, without prescribing how to build it.

**Allowed**
- Conceptual components (e.g., “policy engine”, “queue”, “audit log”) **only as labels** for responsibilities
- User journeys / workflows / state transitions
- Domain entities + definitions (conceptual, not schema)
- Error classes and failure handling as outcomes
- Constraints, invariants, policies, compliance/security/privacy requirements
- Non-functional requirements (SLOs, availability, latency, throughput, cost constraints)
- Observability outcomes (what must be measurable/auditable), not instrumentation design
- Rollout/migration/backward-compatibility outcomes

**Disallowed (unless explicitly required by user constraints)**
- Implementation code, algorithms, class/variable names
- File/module layout, DB schemas/tables/columns
- API endpoints/routes, UI wireframes, pixel-level UI specs
- Vendor/service selections (e.g., Redis/Kafka/Postgres) unless the user mandates them
- “How-to” step-by-step build instructions

**Heuristic**
If a competent engineer could change the implementation approach and **still satisfy the requirement**, the statement is at the right level. If changing the approach would violate it, it’s probably too low-level.

## Quality Gates (Apply before finalizing any “Shall” requirements)
Each requirement must be:
- **Atomic** (one idea)
- **Unambiguous** (no vague terms like “fast” without a measure)
- **Observable/Testable** (clear evidence exists)
- **Necessary** (traces to a goal/use case)
- **Feasible** given stated constraints
- **Traceable** (maps to a goal or scenario)

## Phases

### 1. Restate & Scope (Lock the abstraction early)
Rephrase the user's requirement in your own words. Identify core goal(s), constraints, unknowns, and the **intended audience** for the requirement doc.

Must ask (using the `question` tool):
- Who is the audience/consumer (PM/Eng/Cross-team/Vendor)?
- What are hard constraints (platform, compliance, must-use tech, timeline)?
- What is “done” (acceptance evidence / success metrics)?

End this phase with a short Scope block:
- In-scope
- Out-of-scope / non-goals (initial)
- Key risks/unknowns

### 2. Constraint & Fact Validation (Investigation, not scope creep)
Gather relevant info from available sources **only to validate facts/constraints** (do not invent new scope). Sources may include:
- Local files / codebase (if present)
- Project structure / configs
- Documentation / RFCs
- System environment / runtime constraints
- External references (standards, APIs) if needed for correctness

Output:
- What is confirmed (facts/constraints)
- What is still unknown
- What assumptions you are *not* allowed to make without asking

### 3. Clarifying Questions — Round 1 (Requirements & Facts)
Use the `question` tool to ask focused questions that resolve ambiguities and missing facts.
Prioritize questions that:
- Unlock acceptance criteria
- Fix definitions (users, entities, boundaries)
- Clarify constraints and failure modes

### 4. Iterative Cross-Check Loop (Narrow uncertainty)
Based on the user’s answers:
- Re-investigate relevant sources (docs, code, settings, standards, etc.)
- Validate assumptions
- Identify new uncertainties

After each loop:
- Summarize
  - What is now known
  - What remains unknown
  - What assumptions changed/corrected
- Ask the next focused questions with the `question` tool

Repeat as needed:
→ Investigate → Cross-check → Summarize → Ask next questions  
Each loop must **narrow uncertainty**, not expand it.

**Hard gate:** DO NOT move to Phase 5 unless the user explicitly says:
“Move to next phase”, “Proceed to Phase 5”, or an equivalent clear signal.

### 5. Clarifying Questions — Final Round (Preferences & tradeoffs)
Only enter after explicit user signal.
Ask about:
- Priority tradeoffs (e.g., latency vs. cost vs. correctness)
- Edge cases and non-goals (confirm)
- UX/DX expectations at the outcome level (not UI design)
- Rollout / migration / backward compatibility expectations
- Compliance/security/privacy requirements that affect behavior

### 6. Generate Final Requirement Document (Ready-to-use spec)
Synthesize all gathered information into a requirement document that is **implementation-guiding but not implementation-prescribing**.

#### Required structure (Three-layer)
1) **Outcomes (Why)**
- Problem statement
- Objectives and success metrics
- Stakeholders and target users

2) **Capabilities (What)**
- Primary workflows / user journeys
- System responsibilities and boundaries
- Domain entities + definitions (conceptual)
- Assumptions and constraints (explicit)

3) **Requirements (Shall)**
Write atomic “The system shall …” statements grouped by taxonomy below, each with acceptance criteria.

#### Requirement taxonomy (use these headings)
- Functional requirements
- Non-functional requirements (performance, reliability, security, privacy, cost)
- Data & domain definitions (conceptual)
- Observability & auditability (outcomes, evidence)
- Operations & lifecycle (deployment, migration, rollback, support)
- Edge cases & failure handling
- Non-goals

#### Include these sections at the end
- **Acceptance criteria** (measurable, with test evidence)
- **Decision log** (decisions made + rationale)
- **Open questions** (blocking and non-blocking)
- **Traceability** (map requirements → goals/use cases)

#### Anti-patterns (do NOT write)
Unless the user explicitly mandates them, do not include:
- Specific tech/vendor choices (Redis/Kafka/Postgres/etc.)
- Endpoints/routes/UI layouts/screens
- DB schemas/tables/columns
- Class/variable names, modules, file structure
- Algorithm selections or code snippets

Apply the **Quality Gates** checklist before final output.

---

Below is the user's requirement: $ARGUMENTS
