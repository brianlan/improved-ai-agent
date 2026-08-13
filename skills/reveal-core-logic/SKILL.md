---
name: reveal-core-logic
description: Refactor existing code so its core workflow is immediately visible and implementation details unfold through coherent semantic layers.
disable-model-invocation: true
---

# Reveal Core Logic

Refactor existing code so a reader encounters the **core narrative before implementation detail**.

Preserve observable behavior, interfaces that must remain stable, data formats, and correctness constraints.

This skill optimizes one thing above all others:

> **Make the core logic obvious through progressive disclosure.**

All other rules in this skill serve that goal. Do not improve one local property by damaging a clearer narrative or a useful semantic hierarchy.

Use `$ARGUMENTS` to determine scope. If scope is not explicit, focus on the code currently being worked on rather than expanding into unrelated parts of the repository.

# Priority

Apply the following priorities in order.

## 1. Core narrative

The important workflow must be recognizable directly from the code.

## 2. Progressive disclosure

The reader should be able to understand the code by moving from purpose → workflow → stage → mechanics.

## 3. Supporting structure

Use semantic altitude, repeated-unit visibility, semantic compression, and boundary containment to protect that progressive disclosure.

When supporting rules conflict, prefer the structure that preserves the clearer core narrative and hierarchy.

---

# Leading concepts

## Core narrative

The smallest sequence of meaningful operations that explains what the code accomplishes from initiation to outcome.

It describes the important **verbs** of the system rather than the mechanics used to implement them.

## Happy path

The normal successful workflow.

At orchestration levels, this path should dominate the reading experience.

## Semantic altitude

The conceptual level at which a statement operates.

Higher-altitude statements describe workflow, responsibilities, or meaningful transformations.

Lower-altitude statements describe realization details such as representation manipulation, formatting, indexing, serialization, primitive computation, protocol mechanics, or local bookkeeping.

## Progressive disclosure

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

Opening one meaningful operation should reveal the next useful level of understanding.

## Semantic compression

A boundary provides semantic compression when its name lets the reader hold several implementation details as one meaningful thought.

## Meaningful boundary

A boundary is meaningful when it carries an important concept in the code's narrative or hierarchy.

Typical meaningful boundaries represent a:

* workflow step;
* transformation;
* responsibility;
* repeated unit of work;
* coherent stage;
* meaningful piece of context.

Its value comes from the concept it exposes, not from its size.

## Boundary leakage

A meaningful boundary leaks when its caller must manipulate lower-level pieces that conceptually belong behind that boundary.

Leakage weakens progressive disclosure because the implementation structure becomes visible at the wrong semantic altitude.

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

Express the workflow internally as a short ordered sequence of meaningful verbs.

For example:

```text
receive → interpret → decide → execute → publish
```

rather than:

```text
read field → construct key → mutate map → call helper → write bytes
```

The actual verbs must come from the program. Do not impose a predefined architecture.

### Completion criterion

You can state a short core narrative in which every operation:

1. represents meaningful progress toward the outcome;
2. can be understood without unrelated mechanics; and
3. matters enough that hiding it would materially weaken understanding of the workflow.

---

## 2. Align the narrative with the code

Locate where each major narrative operation appears in the implementation.

A meaningful operation may be expressed by:

* a function or method;
* a compact self-explanatory block;
* an operation on an existing abstraction;
* another structural unit natural to the language and codebase.

Aim for **narrative–structure alignment**:

> Important verbs in the reader's mental model should be recognizable in the visible code structure.

When an important operation is scattered across lower-level mechanics, give it an appropriate structural expression.

When distinct meaningful operations are fused into an opaque block, expose the distinctions necessary for understanding.

Keep code inline when its meaning is already obvious and another boundary would merely add navigation.

### Completion criterion

Every major operation from the core narrative has a recognizable counterpart in the code unless its inline representation is already clearer.

A reader does not need to infer an important workflow step from scattered implementation detail.

---

## 3. Expose the happy path

Restructure the highest relevant orchestration layer so it reads primarily as:

> What happens next?

Use meaningful operations to hide details that do not belong at this altitude.

Prefer semantic compression over mechanical extraction.

The target is not shorter functions. A longer coherent narrative is better than a shorter function made of weak abstractions.

### Completion criterion

Reading only the highest relevant orchestration layer is sufficient to answer:

* What happens first?
* What are the major stages?
* What meaningful unit is repeatedly processed, if any?
* What outcome or effect is produced?

The reader obtains those answers mainly from visible operations rather than reverse-engineering mechanics.

---

## 4. Expose meaningful repeated units

Inspect structures that repeatedly perform meaningful work, including loops, batches, handlers, pipelines, dispatch, traversal, callbacks, task execution, or state transitions.

Ask:

> What happens once per unit?

When one iteration conceptually performs one meaningful operation but its body exposes many lower-level mechanics, make that operation visible.

The enclosing repeated structure should remain at its own semantic altitude.

### Completion criterion

For every major repeated or delegated unit at an orchestration level, the once-per-unit operation is immediately recognizable without mentally executing a dense implementation block.

---

## 5. Align semantic altitude

For each orchestration unit, determine the semantic altitude implied by its purpose.

Its major statements should normally operate near that altitude.

A coherent layer resembles:

```text
acquire
interpret
plan
execute
report
```

A mixed layer resembles:

```text
meaningful operation
representation manipulation
meaningful operation
primitive computation
bookkeeping
meaningful operation
```

When lower-level mechanics interrupt a higher-level narrative, place those mechanics behind a meaningful boundary at the next level down.

Then inspect the lower level as well. It should reveal a coherent next stage rather than simply inherit the same mixture.

### Completion criterion

For every changed orchestration unit:

1. major statements operate at approximately one semantic altitude;
2. movement downward occurs through a meaningful boundary; and
3. opening that boundary reveals a coherent next level.

---

## 6. Classify boundaries before changing them

Before removing, merging, or substantially changing an existing or newly introduced boundary, determine whether it is **meaningful**.

Ask:

* Does its name express an important narrative verb?
* Does it represent the meaningful once-per-unit operation of a loop or handler?
* Does it create a useful step in progressive disclosure?
* Does it provide real semantic compression?
* Would inlining it force the caller to understand lower-level mechanics?

If the answer is yes, treat it as a **meaningful boundary**.

Meaningful boundaries are structural assets. Preserve their conceptual role unless the surrounding narrative itself is wrong.

If a boundary adds little meaning and mainly relocates obvious code, it may be simplified, merged, or inlined when doing so improves the narrative.

### Completion criterion

Every boundary being removed or collapsed has been judged expendable because it contributes little narrative meaning or progressive disclosure.

No useful narrative step disappears merely to simplify an interface or reduce indirection.

---

## 7. Repair boundary leakage without collapsing meaning

Inspect meaningful boundaries for leakage.

Ask:

> Does the caller interact with concepts appropriate to its own altitude, or must it assemble the callee's internal machinery?

Detailed arguments are not automatically leakage. They may be genuinely independent inputs.

Leakage exists when callers are forced to know pieces mainly because of how the callee is implemented.

When a **meaningful boundary leaks**, preserve the boundary's conceptual role first.

Then look for the smallest change that moves lower-level ownership back behind the boundary.

Depending on the existing design, this may involve:

* deriving implementation-specific values inside the lower layer;
* relocating ownership of state;
* passing an already meaningful existing object;
* changing which layer prepares information;
* adjusting responsibility boundaries;
* using another idiom natural to the codebase.

Choose the representation from the code's actual needs.

A leaking meaningful boundary should normally be **repaired rather than erased**.

Removing it is appropriate only when, after re-evaluating the narrative, the boundary itself no longer represents a useful concept.

### Completion criterion

For each changed meaningful boundary:

1. its narrative role remains visible;
2. the caller primarily speaks in concepts appropriate to its own altitude;
3. implementation-specific structure is owned by the layer that uses it;
4. remaining detailed inputs are genuinely meaningful to the caller; and
5. leakage was not "solved" merely by inlining the hidden implementation into the caller.

---

## 8. Verify progressive disclosure recursively

Read the changed structure top-down.

At every orchestration level, ask:

> Does this level explain one coherent part of the workflow before exposing its mechanics?

Apply the **collapse test**:

> If implementations below this level are hidden, does the visible code still explain the workflow at this level?

Apply the **expand test**:

> If one major operation is opened, does it reveal one coherent next level?

Apply the **call-site test**:

> Does invoking the operation preserve its abstraction, or does the caller have to reconstruct its implementation structure?

Apply the **preservation test**:

> Did improving a lower-level concern remove a useful operation from the higher-level narrative?

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
* the expand test;
* the call-site test; and
* the preservation test.

A local improvement has not degraded a higher-level narrative.

---

## 9. Review abstraction value

Inspect every helper, method, class, data holder, or other structural boundary introduced or retained by the refactoring.

Ask:

> What meaning does this boundary allow the reader to hold as one thought?

Strong boundaries support the progressive-disclosure hierarchy.

Weak boundaries mostly increase navigation or bundle unrelated values.

Prefer the minimum structure that preserves the useful hierarchy.

Do not introduce a class, context object, parameter object, manager, wrapper, or other container merely to hide a long argument list.

Bundling is useful only when the bundle itself represents a coherent concept with meaningful ownership.

### Completion criterion

Every introduced abstraction has a clear explanatory or ownership role.

Its existence improves the hierarchy rather than merely relocating complexity.

---

# Final reading test

Return to the highest relevant entry point and read the code as a new reader.

## Narrative test

Can the core workflow be stated using operations visibly present in the code?

## Happy-path test

Can the normal successful workflow be followed before understanding supporting mechanics?

## Repetition test

For important repeated or delegated work, is the once-per-unit operation apparent?

## Altitude test

Does each orchestration unit mostly speak at one semantic altitude?

## Collapse test

With lower-level implementations hidden, does each visible level explain itself?

## Expand test

Does opening one operation reveal one coherent next level?

## Call-site test

Do meaningful calls preserve their abstraction rather than expose unnecessary lower-level structure?

## Preservation test

Did any attempt to simplify an interface or abstraction make the surrounding narrative less visible?

## Compression test

Do structural boundaries reduce the implementation detail the reader must hold simultaneously?

If a local change improves one test while making a higher-priority test worse, prefer the version that better preserves the core narrative and progressive disclosure.

---

# Stop condition

Stop when all of the following are true:

1. The core narrative is directly visible in the code structure.
2. The happy path reads as a coherent sequence of meaningful operations.
3. Major narrative operations have recognizable structural counterparts unless their inline form is clearer.
4. Important repeated or delegated units expose what happens once per unit.
5. Changed orchestration layers operate at coherent semantic altitudes.
6. Progressive disclosure works recursively across the hierarchy.
7. Meaningful boundaries retain their narrative role.
8. Boundary leakage has been reduced where it materially obscured higher-level code.
9. Boundary improvements have not pushed lower-level mechanics back into callers.
10. Introduced abstractions provide semantic compression or meaningful ownership.
11. Further restructuring would mostly rename, relocate, bundle, shorten, or subdivide code without revealing additional meaning.

The target is:

> **The minimum hierarchy that makes the core logic obvious while preserving the meaningful boundaries that carry it.**

# Verification

Preserve observable behavior while restructuring.

Run the most relevant existing tests, checks, type checks, linters, builds, or executable validations available for the changed code.

Fix unintended behavioral changes introduced by restructuring.

Finish by briefly reporting:

* the core narrative identified;
* which details previously obscured it;
* which meaningful boundaries were exposed or preserved;
* which boundary leakage was repaired;
* any tempting simplification that was intentionally avoided because it would weaken progressive disclosure;
* the checks used to verify behavior.

