---
name: reveal-core-logic
description: Refactor existing code so its core workflow is immediately visible and implementation details unfold through coherent semantic layers.
disable-model-invocation: true
---

# Reveal Core Logic

Refactor existing code so a reader encounters the **core narrative before implementation detail**.

Preserve observable behavior, interfaces that must remain stable, data formats, and correctness constraints.

Concentrate restructuring effort on the normal successful workflow. Keep supporting concerns stable unless moving them is necessary to expose that workflow.

Use `$ARGUMENTS` to determine scope. If scope is not explicit, focus on the code currently being worked on rather than expanding into unrelated parts of the repository.

## Leading concepts

### Core narrative

The smallest sequence of meaningful operations that explains what the code accomplishes from initiation to outcome.

It describes the important **verbs** of the system rather than the mechanics used to implement them.

### Happy path

The normal successful workflow.

The happy path should dominate the reading experience at orchestration levels.

### Semantic altitude

The conceptual level at which a statement operates.

Higher-altitude statements describe workflow, responsibilities, or meaningful transformations.

Lower-altitude statements describe how those operations are realized: representation handling, formatting, indexing, primitive computation, serialization, protocol mechanics, local bookkeeping, or similar detail.

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

Expanding one meaningful operation should reveal the next useful level of understanding.

### Semantic compression

A boundary earns its existence when its name allows several implementation details to be understood as one meaningful concept.

A boundary that merely moves or shortens code provides little semantic compression.

### Boundary leakage

A semantic boundary leaks when understanding or invoking it requires its caller to manipulate lower-level pieces that conceptually belong behind that boundary.

A good boundary hides implementation structure at both:

* the implementation body; and
* the call site.

The goal is not minimal argument count. The goal is that callers work primarily with concepts appropriate to their own semantic altitude.

---

# Process

## 1. Reconstruct the core narrative

Read enough surrounding code to understand what the implementation actually does before restructuring it.

Identify:

* where the relevant workflow begins;
* what meaningful entities or information move through it;
* the major operations or transformations;
* where meaningful outcomes or side effects occur;
* what constitutes the normal successful path.

Express the result internally as a short ordered sequence of verbs.

For example:

```text
receive → interpret → decide → execute → publish
```

rather than:

```text
read field → build string → index map → call helper → write bytes
```

The actual verbs must come from the program. Do not force the code into a predefined architecture.

### Completion criterion

You can state a short core narrative in which every operation:

1. represents meaningful progress toward the program's outcome;
2. can be understood without unrelated implementation mechanics; and
3. is important enough that hiding it would materially weaken understanding of the workflow.

---

## 2. Align the narrative with the code structure

For each major operation in the reconstructed narrative, locate where that operation is visible in the code.

A meaningful operation may appear as:

* a clearly named function or method call;
* a compact self-explanatory block;
* an operation on an existing abstraction;
* another structural unit appropriate to the language and codebase.

Aim for **narrative–structure alignment**:

> The important verbs in the reader's mental model should be recognizable in the visible code structure.

When an important operation is spread across lower-level mechanics, give that operation an appropriate structural boundary.

When several distinct narrative operations are hidden behind one opaque block, expose the distinctions necessary to understand the workflow.

Keep implementation inline when its meaning is already obvious and introducing another boundary would add navigation without adding understanding.

### Completion criterion

Every major operation from the core narrative has a recognizable structural counterpart, unless its inline implementation is already the clearest expression of that operation.

A reader does not need to reconstruct an important workflow step from scattered mechanics.

---

## 3. Expose the happy path

Restructure the highest relevant orchestration layer so the normal successful workflow reads as a coherent sequence.

Prefer visible statements that answer:

> What happens next?

Use semantic compression to move distracting mechanics one level lower.

The target is not shorter functions. A longer function with one coherent narrative is preferable to a shorter function assembled from weak abstractions.

### Completion criterion

Reading only the highest relevant orchestration layer is sufficient to answer:

* What happens first?
* What are the major stages?
* What meaningful unit is repeatedly processed, if any?
* What meaningful outcome or effect is produced?

The answers come primarily from the visible operations rather than reverse-engineering implementation details.

---

## 4. Expose repeated units of work

Inspect structures that repeatedly perform meaningful work, including loops, batches, handlers, pipelines, dispatch, traversal, callbacks, task execution, or state transitions.

Ask:

> What meaningful operation happens once per unit?

The repeated structure should make that answer apparent.

If one iteration conceptually performs one operation but its body exposes many unrelated mechanics, restructure the body so the once-per-unit operation becomes visible.

### Completion criterion

For every major repeated or delegated unit at an orchestration level, a reader can identify what happens once per unit without mentally executing a dense collection of lower-level steps.

---

## 5. Align semantic altitude

Determine the semantic altitude implied by each orchestration unit's purpose.

Its major statements should normally operate at approximately that same altitude.

A coherent orchestration layer resembles:

```text
acquire
interpret
plan
execute
report
```

An altitude mixture resembles:

```text
meaningful operation
representation manipulation
path or key construction
meaningful operation
primitive computation
bookkeeping
meaningful operation
```

When lower-altitude mechanics interrupt a higher-level narrative, place them behind a meaningful boundary at the next level down.

Then inspect that boundary itself. It should reveal a coherent next layer rather than move the same mixture elsewhere.

### Completion criterion

For each changed orchestration unit:

1. its major statements operate at approximately one semantic altitude;
2. descent to a lower altitude occurs through a meaningful boundary; and
3. opening that boundary reveals a coherent next level of detail.

---

## 6. Contain implementation detail at boundaries

Inspect the interfaces between the semantic layers created or exposed by the refactoring.

A boundary does not fully provide progressive disclosure if its body is hidden but its caller still needs to enumerate the internal pieces of that hidden layer.

For each meaningful call or boundary, ask:

> Does the caller provide concepts that belong at the caller's semantic altitude, or is it assembling the callee's internal machinery?

For example, an operation conceptually expressed as:

```python
result = execute(task, context)
```

keeps its call site near the caller's narrative.

An interface such as:

```python
result = execute(
    task_id,
    raw_payload,
    cache_handle,
    retry_state,
    serializer,
    output_directory,
    timeout_seconds,
    internal_flags,
)
```

may indicate leakage if those pieces mainly describe how `execute` works rather than what the caller is deciding.

The number of parameters is only a signal, never the criterion. A function may legitimately need many independent inputs. Likewise, a short argument list can still expose the wrong concepts.

When leakage obscures the caller's narrative, look for the smallest appropriate way to restore the boundary. Depending on the existing design, that may mean passing an already meaningful object, relocating ownership of state, adjusting the responsibility boundary, or using another idiom natural to the codebase.

Choose the representation from the code's needs. Do not introduce an object, class, context container, closure, or framework pattern merely to reduce parameter count.

### Completion criterion

At each changed semantic boundary:

1. the caller primarily speaks in concepts appropriate to its own altitude;
2. lower-level implementation structure is owned by the layer that uses it;
3. invoking the operation does not force the caller to reconstruct the callee's internals; and
4. any remaining detailed arguments are independently meaningful inputs rather than accidental pieces of hidden implementation.

---

## 7. Verify progressive disclosure recursively

Read the changed structure top-down.

At every orchestration layer, ask:

> Does this level explain one coherent part of the workflow before exposing its mechanics?

Apply the **collapse test**:

> If implementations below this level are collapsed, does the visible code still explain the workflow at this level?

Apply the **expand test**:

> If one major operation is expanded, does it reveal one coherent next level of explanation?

Apply the **call-site test**:

> Does using the operation preserve the abstraction, or does its invocation expose the lower level that the operation was meant to hide?

The desired structure behaves like controlled zoom:

```text
overview
    ↓
stage workflow
    ↓
local algorithm or mechanism
    ↓
primitive implementation
```

### Completion criterion

Every changed orchestration layer passes:

* the collapse test;
* the expand test; and
* the call-site test.

The hierarchy remains explanatory as the reader moves both downward into implementations and horizontally across call sites.

---

## 8. Review abstraction value

Inspect every helper, method, class, data holder, or other structural boundary introduced by this refactoring.

Ask:

> What meaning does this boundary allow the reader to hold as one thought?

Strong boundaries represent a meaningful:

* workflow step;
* transformation;
* responsibility;
* unit of work;
* piece of context;
* level of explanation.

Keep straightforward mechanics local when a new boundary would mostly increase navigation.

Prefer the smallest structural change that restores a coherent narrative and useful progressive disclosure.

### Completion criterion

Every introduced boundary has a clear explanatory role.

Inlining or removing it would make the surrounding workflow materially harder to understand, or would cause lower-level implementation structure to leak upward again.

---

# Final reading test

Return to the highest relevant entry point and read the code in normal reading order.

Judge the resulting code as a reader encountering it for the first time.

## Narrative test

Can the core workflow be stated using operations visibly present in the code?

## Happy-path test

Can the normal successful workflow be followed before understanding supporting mechanics?

## Repetition test

For every important repeated or delegated unit, is the once-per-unit operation apparent?

## Altitude test

Does each orchestration unit mostly speak at one semantic altitude?

## Collapse test

With lower-level implementations hidden, does each visible layer still explain itself?

## Expand test

Does opening one operation reveal one coherent next level?

## Call-site test

Do calls preserve their semantic boundary, or do lower-level implementation details leak into the caller?

## Compression test

Do introduced boundaries reduce the number of implementation details the reader must hold simultaneously?

If a test fails, continue restructuring at the layer where it fails.

---

# Stop condition

Stop when all of the following are true:

1. The core narrative is visible in the code structure.
2. The happy path reads as a coherent sequence of meaningful operations.
3. Every major narrative operation has a recognizable structural counterpart unless its inline form is clearer.
4. Major repeated or delegated units expose what happens once per unit.
5. Each changed orchestration layer operates at a coherent semantic altitude.
6. Progressive disclosure works recursively across the hierarchy.
7. Semantic boundaries hide unnecessary implementation structure from their callers as well as from their readers.
8. Introduced boundaries provide meaningful semantic compression.
9. Further restructuring would mostly rename, relocate, shorten, bundle, or subdivide code without revealing additional meaning.

The target is the **minimum hierarchy that makes the core logic obvious without leaking its implementation structure upward**.

# Verification

Preserve observable behavior while restructuring.

Run the most relevant existing tests, checks, type checks, linters, builds, or executable validations available for the changed code.

Fix unintended behavioral changes introduced by restructuring.

Finish by briefly reporting:

* the core narrative identified;
* which structural details previously obscured it;
* which boundaries or orchestration layers were changed;
* any important boundary leakage that was removed;
* the checks used to verify behavior.

