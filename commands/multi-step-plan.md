---
description: Multi-step plan generator for $ARGUMENTS
---

Use the todo list tool to add each step as a separate todo item, start with the first, and only move on after making it completed. 

Steps:
1. Rephrase - Clearly restate the user's requirement in your own words to confirm understanding and reduce ambiguity. STOP and wait for the user's confirmation. 
2. Investigate - Explore the existing codebase, project structure, documentation, and conventions that relate to the requirement. Identify relevant files, patterns, and dependencies.
3. Ask Questions - Identify unclear, ambiguous, or missing information in the requirement. Ask focused questions that reduce risk and prevent incorrect assumptions. STOP and wait for the user's answers. 
4. Cross-check - Perform a second pass to verify consistency with the codebase. Cross-check assumptions, confirm technical constraints, and validate facts.
5. Ask Questions - Ask for user preferences, design choices, edge-case expectations, and workflow details that affect implementation. STOP and wait for the user's answers.
6. Propose Validation Method - Describe how the final work can be validated. Include tests, checks, manual verification steps, and acceptance criteria. STOP and wait for the user's confirmation.
7. Generate Final Plan - Produce a concrete, ordered execution plan that a developer can follow to implement the feature correctly and safely.

Below is the user requirement: $ARGUMENTS
