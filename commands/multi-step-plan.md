---
description: Iterative multi-source planning agent for $ARGUMENTS
---

Use the todo list tool. Add each phase as a separate todo item. Only move forward after the current one is completed.

Phases:

1. Restate & Scope  
   Rephrase the user's requirement in your own words. Identify the core goal, constraints, and unknowns.  
   Use the `question` tool to ask the user to confirm or correct your restatement.

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
   Use the `question` tool to ask focused questions to resolve ambiguities, missing facts, and assumptions about the task.

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
    - Use the `question` tool to ask the next focused questions.

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
   Use the `question` tool to ask these final preference/design questions.

6. Validation & Acceptance Criteria  
   Propose:
   - How correctness will be validated
   - Tests / checks
   - Manual verification steps
   - Clear acceptance criteria  
   Use the `question` tool to ask for user confirmation/approval of the proposed validation approach.
   After the user explicitly approves the Phase validation proposal, generate a final, structured validation specification including:
   - test cases (e.g. unit test, integration test)
   - verification steps
   - acceptance/success criteria

7. Final Execution Plan  
   Produce a concrete, ordered, implementation-ready plan that accounts for:
   - Confirmed requirements
   - Constraints
   - Research findings
   - Validation strategy
   Use the `question` tool to ask for user approval of the final plan.

8. Session Name + Save Artifacts  
   After the user has approved the finalized requirements, validation criteria, and implementation plan:
   1) Create a proper, filesystem-safe name for the current task/session for later usage.
      - Check `./plan-build-validate/sessions` first to ensure no duplicate name exists.
      - If a duplicate exists, adjust the name deterministically (e.g., append `-2`, `-3`, etc.) until unique.
   2) Create the session folder: `./plan-build-validate/sessions/<a-proper-name>/`
   3) Save the finalized user requirements (including any supplements, clarifications, and disambiguation obtained from the user) to:
      - `./plan-build-validate/sessions/<a-proper-name>/user_requirements.md`
   4) Save the validation requirements and acceptance criteria (the finalized Phase 6 output) to:
      - `./plan-build-validate/sessions/<a-proper-name>/validation_criteria.md`
   5) Save ONLY the implementation part of the final plan (the finalized Phase 7 output) to:
      - `./plan-build-validate/sessions/<a-proper-name>/implementation_plan.md`
   DON'T proceed to the build/implementation stage. Just STOP here and report summary to the user. 

Below is the user's requirement: $ARGUMENTS
