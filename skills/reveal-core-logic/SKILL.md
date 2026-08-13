---
name: reveal-core-logic
description: Refactor existing code so its core workflow is immediately visible and implementation details unfold through coherent semantic layers.
disable-model-invocation: true
---

# Reveal Core Logic

Refactor existing code so a reader encounters the **core narrative before implementation detail**.

Preserve observable behavior, interfaces that must remain stable, data formats, and correctness constraints.

Optimize in this order:

1. **Core narrative visibility**
2. **Progressive disclosure**
3. Supporting structural quality

Semantic altitude, repeated-unit visibility, boundary containment, and semantic compression are means to those goals. Never improve one of them by making the higher-level narrative harder to follow.

Use `$ARGUMENTS` to determine scope. If scope is not explicit, stay within the code currently being worked on rather than expanding into unrelated parts of the repository.

# Core concepts

## Core narrative

The smallest sequence of meaningful operations that explains what the code accomplishes from initiation to outcome.

It describes important **verbs**, not the mechanics used to implement them.

## Semantic altitude

The conceptual level at which code speaks.

Higher-altitude code describes workflow, responsibilities, or meaningful transformations. Lower-altitude code describes their realization: representation handling, primitive computation, formatting, serialization, indexing, protocols, bookkeeping, and similar mechanics.

## Progressive disclosure

Code should support controlled zoom:

```text
purpose
    ↓
major workflow
    ↓
one stage's workflow
    ↓
implementation mechanics
```

Each level should explain itself before requiring the reader to descend.

## Meaningful boundary

A function, method, block, object, or other structural boundary is meaningful when it lets the reader hold several details as one useful concept.

Typical examples are a workflow step, transformation, responsibility, repeated unit of work, coherent stage, or meaningful piece of context.

## Boundary leakage

A meaningful boundary leaks when using it forces the caller to manipulate implementation pieces that conceptually belong inside the lower layer.

The number of arguments is only a signal. Leakage is about **ownership of concepts**, not parameter count.

---

# Process

## 1. Reconstruct the narrative

Read enough surrounding code to understand the actual workflow before restructuring it.

Identify:

* where the relevant workflow begins;
* the meaningful entities or information moving through it;
* the major operations or transformations;
* important outcomes or side effects;
* the normal successful path.

Reduce that understanding internally to a short ordered sequence of meaningful verbs.

Prefer:

```text
receive → interpret → decide → execute → publish
```

over descriptions of field access, path construction, primitive control flow, serialization, or other mechanics.

Do not impose a predefined architecture. Derive the narrative from the code.

### Completion criterion

Every operation in the reconstructed narrative:

* represents meaningful progress toward the outcome;
* can be understood without unrelated mechanics; and
* matters enough that hiding it would materially weaken understanding of the workflow.

---

## 2. Build the orchestration audit

Before restructuring, enumerate the **orchestration sites** in scope that shape how a reader follows the workflow.

Include, where relevant:

* entry points;
* top-level workflow functions;
* major stages called from them;
* loops or other repeated units of meaningful work;
* handlers, callbacks, dispatch, pipelines, traversal, or state transitions;
* existing boundaries that carry an important narrative step.

Maintain this as an internal audit list while working.

For each site, determine:

1. what narrative operation it should communicate;
2. what semantic altitude it should occupy;
3. whether its repeated unit of work, if any, is immediately apparent;
4. which meaningful boundaries it depends on.

This inventory is the coverage boundary for the refactoring. Do not stop after improving only the most obvious functions.

### Completion criterion

Every orchestration site in scope has been identified and has a clear intended role in the narrative.

There is no major workflow, repeated unit, or meaningful boundary in scope that remains unaudited merely because another part of the code already looks good.

---

## 3. Restructure for progressive disclosure

Work top-down through the audit list.

At each orchestration site, make the visible code express the workflow appropriate to that level.

### Expose the narrative

Important verbs in the reader's mental model should have recognizable counterparts in the code.

When an important operation is scattered across lower-level mechanics, give it a meaningful structural expression.

Keep code inline when it is already the clearest expression of the operation.

### Expose repeated units

For any loop, handler, batch, traversal, dispatch, or other repeated workflow, ask:

> What meaningful operation happens once per unit?

Make that operation apparent without requiring the reader to mentally execute a dense body.

### Keep one semantic altitude

The major statements within an orchestration site should normally operate at approximately the altitude implied by that site's purpose.

When lower-level mechanics interrupt the narrative, move them behind a meaningful boundary at the next level down.

Then inspect that lower level too: it should reveal a coherent next stage rather than merely inherit the same mixture.

### Preserve meaningful boundaries

Before removing or merging a boundary, ask whether it already carries useful narrative meaning.

A boundary is worth preserving when it:

* expresses an important narrative verb;
* exposes the meaningful once-per-unit operation of repeated work;
* creates a useful level in progressive disclosure; or
* provides genuine semantic compression.

Treat such boundaries as structural assets.

A weak boundary that merely relocates obvious code may be simplified when doing so improves the narrative.

### Completion criterion

Every orchestration site in the audit now:

* communicates its intended narrative operation;
* exposes meaningful repeated work;
* speaks at a coherent semantic altitude; and
* descends through meaningful boundaries when more detail is required.

---

## 4. Repair boundaries without collapsing the hierarchy

After the narrative hierarchy is visible, inspect the meaningful boundaries in the audit for leakage.

Ask at each call site:

> Is the caller supplying concepts appropriate to its own level, or reconstructing the callee's implementation machinery?

When a meaningful boundary leaks, **preserve its conceptual role first**.

Then use the smallest change that restores ownership to the appropriate layer. This may involve:

* deriving implementation-specific values inside the layer that uses them;
* relocating preparation or state ownership;
* passing an already meaningful existing object;
* adjusting the responsibility boundary;
* using another idiom natural to the codebase.

Detailed inputs may remain when they are genuinely independent concepts at the caller's level.

Do not create a class, context object, parameter object, manager, wrapper, or generic container merely to hide an argument list. A bundle is useful only when the bundle itself represents a coherent concept with meaningful ownership.

A leaking meaningful boundary should normally be **repaired, not erased**.

Removing it is appropriate only when its narrative role is itself weak or unnecessary.

### Completion criterion

For every meaningful boundary in the audit:

* its narrative role remains visible;
* the caller primarily operates with concepts appropriate to its own altitude;
* lower-level implementation structure is owned by the layer that uses it; and
* leakage was not removed merely by inlining the implementation into the caller.

---

## 5. Run the exhaustive reading audit

Return to the audit list and evaluate **every orchestration site**, not just the sites changed most recently.

Apply the same tests to each.

### Narrative test

Does the visible code communicate the meaningful operation this site is responsible for?

### Repetition test

If the site performs repeated or delegated work, is the once-per-unit operation apparent?

### Altitude test

Do its major statements mostly speak at one semantic altitude?

### Collapse test

If implementations below this level are hidden, does this level still explain itself?

### Expand test

If one meaningful operation is opened, does it reveal one coherent next level of understanding?

### Call-site test

Does invoking a meaningful boundary preserve the abstraction, rather than expose unnecessary lower-level structure?

### Preservation test

Did any local simplification make a useful higher-level narrative step disappear?

For every site in the audit, reach one of two explicit conclusions:

* **passes**; or
* **intentionally unchanged because the existing structure is already clearer than the available refactoring**.

If a site fails a test, continue restructuring at that site.

### Completion criterion

Every orchestration site in scope has been explicitly accounted for and passes the reading audit or has a concrete reason to remain unchanged.

Do not infer completion from having improved several representative locations.

---

# Stop condition

Stop when:

1. the core narrative is directly visible in the code;
2. the normal successful workflow can be followed from the highest relevant orchestration level;
3. progressive disclosure remains coherent as the reader moves downward;
4. every orchestration site in scope has been audited;
5. meaningful repeated units expose what happens once per unit;
6. meaningful boundaries are preserved and unnecessary leakage is contained;
7. introduced abstractions provide real semantic or ownership value; and
8. further restructuring would mostly rename, relocate, bundle, shorten, or subdivide code without revealing additional meaning.

The target is:

> **The minimum hierarchy that makes the core logic obvious, applied consistently across the full orchestration surface.**

# Verification

Preserve observable behavior while restructuring.

Run the most relevant existing tests, checks, type checks, linters, builds, or executable validations available for the changed code.

Fix unintended behavioral changes introduced by restructuring.

Finish by briefly reporting:

* the core narrative identified;
* the orchestration sites audited;
* the main structural changes used to reveal the narrative;
* meaningful boundaries preserved or repaired;
* any audited sites intentionally left unchanged and why;
* the checks used to verify behavior.

