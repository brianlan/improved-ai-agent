---
description: Iterative multi-source planning agent for $ARGUMENTS
---

Use the todo list tool. Add each phase as a separate todo item. Only move forward after the current one is completed.

Phases:

1. Restate & Scope  
   Rephrase the user's requirement in your own words. Identify the core goal, constraints, and unknowns.  
   STOP and wait for the user's confirmation or correction.

2. Initial Investigation (Source-Agnostic)  
   Gather relevant information from any available sources, which may include:
   - Local files / codebase (if present)
   - Project structure / configs
   - Documentation
   - System environment
   - Web search / external references
   - Public repos / standards / APIs

   Summarize what you found and what remains unknown.

3. Clarifying Questions – Round 1 (Requirements & Facts)  
   Ask focused questions to resolve ambiguities, missing facts, and assumptions about the task.  
   STOP and wait for the user's answers.

4. Iterative Research & Cross-Check Loop  
   Based on the user’s answers:
   - Re-investigate relevant sources (code, web, docs, settings, repos, etc.)
   - Validate assumptions
   - Identify new uncertainties

   After each question + investigation round:
   - Summarize:
     • What is now known
     • What remains unknown
     • What assumptions were corrected
   - Ask the next focused questions. And STOP and wait for the user's answers.

   Repeat this loop as needed:
   → Investigate → Cross-check → Summarize → Ask the next round of questions  
   Each loop should narrow uncertainty, not expand it.

   DO NOT move to Phase 5 unless the user explicitly says:
   "Move to next phase" or "Proceed to Phase 5" or an equivalent clear signal.

5. Clarifying Questions – Final Round (Preferences & Design Choices)  
   Only enter this phase after receiving an explicit user signal to proceed.
   Ask about:
   - Design tradeoffs
   - Edge cases
   - UX / DX expectations
   - Workflow, constraints, and non-goals  
   STOP and wait for confirmation.

6. Validation & Acceptance Criteria  
   Propose:
   - How correctness will be validated
   - Tests / checks
   - Manual verification steps
   - Clear acceptance criteria  
   STOP and wait for user confirmation.
   After the user explicitly approves the Phase validation proposal, generate a final, structured validation specification including:
   - test cases (e.g. unit test, integration test)
   - verification steps
   - acceptance/success criteria
   Save the validation specification as a markdown file at: ./validation_specs/validation_{current_ts}.md

7. Final Execution Plan  
   Produce a concrete, ordered, implementation-ready plan that accounts for:
   - Confirmed requirements
   - Constraints
   - Research findings
   - Validation strategy
   After the user explicitly approves the final plan, save this final plan as a markdown file at: ./execution_plans/plan_{current_ts}.md

Below is the user's requirement: $ARGUMENTS
