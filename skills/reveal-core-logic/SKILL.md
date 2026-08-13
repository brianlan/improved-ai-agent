---
name: reveal-core-logic
description: Refactor existing code so its core workflow is directly visible and unfolds through coherent levels of abstraction.
disable-model-invocation: true
---

# Reveal Core Logic

Refactor the target code so a reader can understand its **core narrative before its implementation details**.

Preserve observable behavior, public interfaces, data formats, and correctness constraints.

Spend restructuring effort first on the normal successful workflow. Keep supporting concerns stable unless moving them is necessary to expose that workflow.

Use `$ARGUMENTS` to determine the requested scope. If the scope is not explicit, focus on the code currently being worked on rather than expanding into unrelated parts of the repository.

## Leading concepts

Use these concepts consistently while working:

* **Core narrative** — the smallest sequence of meaningful operations that explains what the code does from input to output.
* **Happy path** — the normal successful workflow that should dominate the top-level reading experience.
* **Semantic altitude** — the conceptual level at which a statement operates. High-altitude statements describe workflow or domain operations; lower-altitude statements describe the mechanics used to implement them.
* **Progressive disclosure** — organize code so the reader understands the workflow first, then expands one operation at a time to reveal increasingly detailed implementation.
* **Semantic compression** — a helper boundary earns its existence when its name communicates the meaning of several implementation details at once.

## Process

### 1. Reconstruct the core narrative

Read enough surrounding code to understand the actual successful workflow before restructuring it.

Identify:

* the main entry point or orchestration path;
* the primary entity or data moving through the workflow;
* the major stages or transformations;
* the important outputs or side effects.

Express the workflow as a short sequence of meaningful operations.

For example:

```text
select scenes
→ load one scene
→ convert eligible episodes
→ write each converted scene
→ report results
```

Prefer domain and workflow language.

Representation details such as filenames, dictionary keys, indexing, serialization, temporary variables, array manipulation, path construction, and bookkeeping belong in the narrative only when they are themselves central to the program's purpose.

**Completion criterion:** you can state the main successful workflow as a short sequence of meaningful operations without relying on unrelated implementation mechanics.

### 2. Align the narrative with the code structure

Compare the reconstructed core narrative with the actual orchestration structure.

For every major operation in the narrative, locate where that operation appears in the code.

A major narrative operation should normally be visible as one of:

* a clearly named function call;
* a clearly named method call;
* a short and already self-explanatory inline operation.

When an important narrative verb is implemented only as a long mixture of representation details, path construction, bookkeeping, condition handling, or lower-level mechanics, the operation is still hidden.

For example, if the narrative contains:

```text
convert episode
```

but the orchestration code contains only:

```python
episode = int(record["episode_index"])
filename = f"episode_{episode:06d}.npz"
path = root / filename
trajectory = load_trajectory(path, ...)
frame_ids = ...
cameras = ...
write_episode(...)
```

then `convert episode` has not yet become visible in the structure.

Create a meaningful boundary when doing so makes that missing narrative operation explicit.

Prefer the smallest boundary that exposes the missing meaning.

**Completion criterion:** every major operation in the core narrative has a recognizable counterpart in the orchestration structure, and no major narrative step remains hidden inside a long collection of lower-level statements.

### 3. Expose the happy path

Restructure orchestration functions so the normal successful workflow is visually dominant.

A reader should be able to start at the entry point and follow the main path through a small number of meaningful operations.

For example:

```python
def convert_scene(...):
    source = load_scene(...)
    episodes = select_convertible_episodes(source)

    for episode in episodes:
        convert_episode(source, episode, ...)
```

The orchestration layer should primarily answer:

> What happens next?

Implementation helpers should answer:

> How does this step work?

Move implementation detail behind a named operation when the new boundary performs semantic compression.

Keep locally readable detail inline when extracting it would merely replace obvious code with another name the reader must chase.

**Completion criterion:** reading only the orchestration path is sufficient to explain the normal successful workflow and its major stages.

### 4. Keep orchestration at a coherent semantic altitude

Review every orchestration function changed during the refactoring.

Its major statements should operate at approximately the semantic altitude implied by that function's purpose.

A workflow-level function might read:

```python
source = load_source(...)
items = select_items(source)

for item in items:
    convert_item(source, item)
```

A mixed-altitude version might read:

```python
source = load_source(...)

for record in source.records:
    item_id = int(record["item_index"])
    filename = f"item_{item_id:06d}.npz"
    path = root / filename
    convert_item(source, item_id)
```

The second version repeatedly drops from workflow meaning into representation mechanics and then climbs back up.

When a lower-altitude block interrupts a higher-altitude narrative, move that block one level down behind a meaningful operation.

When a helper adds indirection without revealing meaning, keep or return the detail to the level where it is easiest to understand.

**Completion criterion:** the major statements in every changed orchestration function operate at a coherent semantic altitude, and transitions to lower-level detail happen through meaningful named operations.

### 5. Inspect every major loop

Major loops often contain the real workflow even when the enclosing function looks clean.

For each significant loop in an orchestration function, read the loop body as its own narrative.

Ask:

> What meaningful operation is performed once per iteration?

The body should either:

* directly read as a short workflow at one semantic altitude; or
* delegate the iteration's main responsibility to a meaningful operation.

For example:

```python
for scene in scenes:
    convert_scene(scene)
```

or:

```python
for frame in frames:
    observations = prepare_observations(frame)
    ego_state = compute_ego_state(frame)
    write_frame(frame, observations, ego_state)
```

A major loop remains structurally dense when one iteration mixes the entity lifecycle with filenames, paths, serialization, indexing, bookkeeping, and unrelated supporting mechanics.

Do not extract a loop body merely because it is long. Extract it when the iteration itself represents a meaningful operation or lifecycle that should be visible in the surrounding narrative.

**Completion criterion:** every major orchestration loop makes the meaning of one iteration immediately clear, and its body does not conceal a major narrative operation inside mixed-altitude mechanics.

### 6. Check progressive disclosure recursively

Read the result as if navigating the code by expanding one function at a time.

The intended reading order is:

```text
program purpose
    ↓
major workflow stages
    ↓
one stage's sub-operations
    ↓
implementation of one sub-operation
    ↓
low-level mechanics
```

Apply the **collapse test** at every orchestration level:

> If the implementations called from this function are collapsed, does the visible function still explain its level of the workflow?

Then expand one operation:

> Does the expanded function reveal one coherent next level of detail?

Continue this check through the important path rather than applying it only to the entry point.

A clean top-level function does not compensate for a dense second-level orchestration function.

Keep closely related implementation details together so following one operation does not require unnecessary jumping across unrelated parts of the codebase.

**Completion criterion:** every important orchestration layer forms a readable narrative of its own, and expanding a meaningful operation reveals one coherent additional level of detail.

## Stop condition

Stop restructuring when all of these are true:

1. The core narrative is short, explicit, and easy to state.
2. Every major narrative operation has a recognizable counterpart in the code structure.
3. The happy path is visually dominant in the orchestration layer.
4. Every major orchestration function reads at a coherent semantic altitude.
5. Every major loop makes the meaning of one iteration clear.
6. Collapsing helper implementations still leaves an understandable workflow at each important orchestration level.
7. Expanding one operation reveals one coherent next level of detail.
8. Helper boundaries provide semantic compression rather than merely shortening functions.
9. Further extraction would mainly rearrange code or add indirection rather than expose additional meaning.

The goal is not maximal decomposition.

The goal is the **minimum hierarchy of meaningful operations required for the core logic to reveal itself progressively**.

## Verification

Preserve observable behavior while restructuring.

Run the most relevant existing tests, checks, or executable validation available for the changed code.

Then perform a structural reread from the entry point.

Do not judge success from the helper functions you just created. Follow the program as a new reader would:

1. read the entry point;
2. follow the happy path;
3. inspect each major loop;
4. expand the major operations one level at a time;
5. stop when implementation mechanics become the appropriate subject.

Before finishing, verify that every major operation identified in the original core narrative is now visible in that reading path.

Report briefly:

* the core narrative;
* the major narrative operations that were made explicit;
* the main structural changes used to expose them;
* the checks used to verify preserved behavior.

