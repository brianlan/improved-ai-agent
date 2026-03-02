---
description: A phased agent that restates requirements, investigates sources, asks clarifying questions iteratively, and generates final specifications for $ARGUMENTS
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

6. Generate Final Requirement  
   Synthesize all gathered information into a comprehensive, actionable requirement document that includes:
   - Clear problem statement and objectives
   - All confirmed constraints and assumptions
   - Accepted design decisions and tradeoffs
   - Edge cases and non-goals explicitly defined
   - Measurable acceptance criteria
   Present this in a structured format that serves as unambiguous guidance for implementation.

Below is the user's requirement: $ARGUMENTS
