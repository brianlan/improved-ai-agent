---

name: reveal-core-logic
description: Refactor existing code so its core workflow is immediately visible and its implementation unfolds through coherent levels of abstraction.
disable-model-invocation: true
------------------------------

# Reveal Core Logic

Refactor existing code so a reader encounters the **core narrative before implementation detail**.

Preserve observable behavior, interfaces, data formats, and correctness constraints.

This skill is about structural readability. Concentrate restructuring effort on making the normal successful workflow legible. Keep supporting concerns stable unless moving them is necessary to expose that workflow.

Use `$ARGUMENTS` to determine scope. If scope is not explicit, focus on the code currently being worked on rather than expanding into unrelated parts of the repository.

## Leading concepts

Use these concepts consistently while working.

### Core narrative

The smallest sequence of meaningful operations that explains what the code accomplishes from initiation to outcome.

It describes the important **verbs** of the system, not the mechanics used to implement them.

### Happy path

The normal successful workflow.

The happy path should dominate the reading experience at orchestration levels. Supporting branches may remain nearby when they belong there, but they should not obscure what normally happens.

### Semantic altitude

The conceptual level at which a statement operates.

Higher-altitude statements describe workflow, responsibilities, or meaningful transformations.

Lower-altitude statements describe how those operations are realized: representation handling, indexing, formatting, serialization, protocol details, local bookkeeping, primitive computations, or similar mechanics.

### Progressive disclosure

Code should reveal itself in useful layers:

```text
purpose
    ↓
major workflow
    ↓
one stage's workflow
    ↓
implementation mechanics
```

Expanding one operation should reveal the next useful level of understanding, rather than an arbitrary collection of details.

### Semantic compression

A helper or abstraction earns its existence when its name expresses the meaning of several implementation details as one useful concept.

Extraction that merely shortens a function without adding meaning is not semantic compression.

---

# Process

## 1. Reconstruct the core narrative

Read enough surrounding code to understand what the implementation actually does before changing its structure.

Identify:

* where the relevant workflow begins;
* what meaningful entities or information move through it;
* the major operations or transformations;
* where meaningful outcomes or side effects occur;
* what constitutes the normal successful path.

Express the result internally as a short ordered sequence of verbs.

For example, the level of description should resemble:

```text
receive → interpret → decide → execute → publish
```

rather than:

```text
read field → build string → index map → call helper → write bytes
```

The exact verbs depend on the program. Do not force the workflow into a predefined architecture.

Distinguish **core operations** from details that merely implement those operations.

### Completion criterion

This step is complete only when you can state a short core narrative in which every operation:

1. represents meaningful progress toward the program's outcome;
2. can be understood without explaining unrelated implementation mechanics; and
3. is important enough that hiding it would make the workflow materially harder to understand.

---

## 2. Map the narrative onto the code structure

Compare the reconstructed core narrative with the existing orchestration structure.

For each major operation in the narrative, locate where that operation is visible in the code.

A core operation may already appear as:

* a clearly named function call;
* a compact, self-explanatory block;
* a method or operation on an existing abstraction;
* another structural unit appropriate to the language and codebase.

The goal is **narrative–structure alignment**:

> The important verbs in the reader's mental model should be recognizable in the code's visible structure.

When an important narrative operation is currently spread across many lower-level statements, restructure it so the operation itself becomes visible.

When several narrative operations are fused into one opaque operation, expose the distinctions that matter for understanding the workflow.

Keep an operation inline when its implementation is already compact and clearer than introducing another level of indirection.

### Completion criterion

This step is complete only when every major operation from the core narrative can be pointed to in the orchestration structure without reconstructing it from scattered implementation details.

A reader should not need to infer a major workflow step from filenames, field manipulation, temporary variables, primitive control flow, or bookkeeping when that step has a meaningful conceptual identity of its own.

---

## 3. Expose the happy path

Restructure the highest relevant orchestration layer so the normal successful workflow reads as a coherent sequence.

Prefer statements whose names describe **what happens next**.

Implementation mechanics should appear only when they are genuinely part of the meaning at that level.

Use semantic compression to move distracting detail one level down when a meaningful operation can represent it.

Preserve locally obvious code when hiding it would make the reader chase a helper for no gain.

The target is not a particular function length. A longer function with one coherent narrative can be clearer than a shorter function assembled from weak abstractions.

### Completion criterion

Reading only the highest relevant orchestration layer should be sufficient to answer:

* What happens first?
* What are the major stages?
* What is repeatedly processed or acted upon, if anything?
* What meaningful result or effect does the workflow produce?

The answers should come primarily from visible operations, not from reverse-engineering implementation details.

---

## 4. Check repeated orchestration

Pay special attention to any structure that repeatedly performs a meaningful unit of work, including:

* loops;
* batches;
* dispatch tables;
* request or message handlers;
* pipelines;
* recursive traversal;
* callbacks;
* task execution;
* state-machine transitions;
* other repeated or delegated workflows.

The body of such a structure often contains a hidden narrative of its own.

Ask:

> What meaningful operation happens once per iteration, item, request, task, state, or unit of work?

If the answer is conceptually simple but the body mixes selection, mechanics, transformation, persistence, bookkeeping, and other lower-level details, expose the meaningful per-unit operation.

The repeated structure itself should remain understandable at its own altitude.

### Completion criterion

For every major repeated or delegated unit of work at an orchestration level, the reader can identify what happens **once per unit** without mentally executing a dense block of lower-level mechanics.

---

## 5. Align semantic altitude

Review each orchestration function and each structural unit changed during the refactoring.

Determine the semantic altitude implied by its purpose.

Then inspect its major statements.

Statements at one orchestration level should normally describe peer operations such as:

```text
acquire
interpret
plan
execute
report
```

A passage that repeatedly alternates between a meaningful operation and its low-level realization creates an altitude jump:

```text
meaningful operation
primitive mechanics
representation detail
meaningful operation
local bookkeeping
meaningful operation
```

When such a jump interrupts the narrative, place the lower-altitude work behind a meaningful boundary at the next level down.

After extraction, inspect the new helper as well. It should reveal a coherent next level rather than merely inherit the same mixture in a different location.

### Completion criterion

This step is complete only when:

1. the major statements within each changed orchestration unit operate at approximately one semantic altitude;
2. movement to a lower altitude occurs through a meaningful boundary; and
3. following that boundary reveals a coherent next level of detail.

---

## 6. Verify progressive disclosure at every orchestration layer

Do not stop after cleaning only the outermost function.

Read the changed call structure top-down.

At each orchestration layer, apply the same test:

> Does this level explain one coherent part of the workflow before exposing its mechanics?

Then apply the **collapse test**:

> If implementation bodies below this level were collapsed in the editor, would the visible code still explain the workflow at this level?

Next apply the **expand test**:

> If I expand one major operation, do I receive the next useful level of explanation?

A good structure should behave like controlled zoom:

```text
overview
    ↓ expand one operation
stage workflow
    ↓ expand one operation
local algorithm or mechanism
    ↓
primitive implementation
```

Avoid structures where clean outer layers merely lead into another dense mixture of unrelated altitudes.

### Completion criterion

Every changed orchestration layer independently passes both:

* the collapse test; and
* the expand test.

The hierarchy remains explanatory as the reader moves downward, not only at the top.

---

## 7. Review abstraction value

Inspect every helper, method, class, or other boundary introduced by this refactoring.

Ask what semantic compression it provides.

A strong boundary lets the reader replace several details with one meaningful thought.

A weak boundary merely gives a name to code that was already easier to read inline.

Prefer boundaries that represent:

* a meaningful workflow step;
* a meaningful transformation;
* a meaningful responsibility;
* a coherent next level of explanation.

Keep straightforward mechanics local when introducing a boundary would add navigation without reducing cognitive load.

### Completion criterion

Every newly introduced structural boundary has a clear explanatory role in the progressive-disclosure hierarchy.

Removing its name and inlining its body would make the surrounding narrative meaningfully harder to read.

---

# Final reading test

Before stopping, return to the highest relevant entry point and read the code in normal reading order.

Do not judge it from memory of the refactoring.

Perform these tests.

## Narrative test

Can you state the core workflow using the operations that are visibly present in the code?

Important verbs from the reconstructed narrative should have recognizable structural counterparts.

## Happy-path test

Can a new reader follow the normal successful workflow without first understanding supporting mechanics?

## Repetition test

For every important repeated or delegated unit of work, is the once-per-unit operation apparent?

## Altitude test

Does each orchestration unit mostly speak at one semantic altitude?

## Collapse test

With lower-level implementations hidden, does each visible level still explain itself?

## Expand test

Does expanding one operation reveal one coherent next level of understanding?

## Compression test

Do introduced boundaries remove cognitive detail, rather than merely move lines elsewhere?

If any test fails, continue restructuring at the level where it fails.

---

# Stop condition

Stop when all of the following are true:

1. The core narrative is visible in the code structure.
2. The happy path reads as a coherent sequence of meaningful operations.
3. Every major narrative operation has a recognizable structural counterpart unless its inline form is already clearer.
4. Major repeated or delegated units expose what happens once per unit.
5. Each changed orchestration layer operates at a coherent semantic altitude.
6. Progressive disclosure works across the hierarchy, not only at the outermost level.
7. Introduced boundaries provide semantic compression.
8. Further restructuring would mostly rename, relocate, shorten, or subdivide code without revealing additional meaning.

The target is the **minimum hierarchy that makes the core logic obvious**.

---

# Verification

Preserve observable behavior while restructuring.

Run the most relevant existing tests, checks, type checks, linters, builds, or executable validations available for the changed code.

Fix any unintended behavioral change introduced by the restructuring.

Finish by briefly reporting:

* the core narrative identified;
* which parts of the previous structure obscured it;
* the structural changes used to expose it;
* the checks used to verify behavior.

