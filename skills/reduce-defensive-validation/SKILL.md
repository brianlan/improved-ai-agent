---
name: reduce-defensive-validation
description: Review and surgically refactor a specified code scope to remove low-value defensive validation while preserving behavior, interfaces, and regression tests.
disable-model-invocation: true
---

# Reduce Defensive Validation

Surgically simplify defensive control flow that obscures the code's real logic.

The goal is **not fewer checks**. The goal is a higher signal-to-noise ratio:

> Preserve guards that prevent silent semantic corruption. Remove guards that merely duplicate natural failures, re-prove already-established invariants, or enforce properties the code does not actually depend on.

Use these anchors throughout the review:

> **Validate semantics, not mechanics.**

> **Validate what you consume, not everything you encounter.**

The user's invocation arguments define the review scope. The scope may be a file, directory, function, class, diff, PR, or other explicitly named code region.

Modify only that scope. Read adjacent code when necessary to understand contracts and data flow, but do not expand the refactor outside the requested scope unless a minimal adjacent change is strictly required to preserve behavior.

## Preservation contract

This is a behavior-preserving refactor.

Preserve:

* normal-path behavior and outputs
* public function and class interfaces
* CLI arguments and exit behavior
* return types and externally visible data structures
* serialized formats, filenames, directory layouts, and protocols
* externally visible side effects
* documented or tested error contracts
* semantic invariants required for correctness
* cleanup, rollback, recovery, and transaction behavior
* existing regression coverage

All relevant regression tests must continue to pass.

Tests are verification, not the sole justification for keeping or removing a guard. An invariant may still protect against silent corruption even when no test covers it.

Do not weaken, delete, skip, or rewrite tests merely to make the refactor pass.

For private/internal code, an incidental exception type or message produced only by a redundant pre-check is not automatically a stable contract. Treat it as a contract when callers, documentation, or tests rely on it.

## Step 1 — Establish scope, happy path, and baseline

Read the requested scope and only the surrounding code necessary to understand:

* what the code is actually trying to accomplish
* the primary happy-path data flow
* inputs it consumes
* outputs and side effects it produces
* callers and downstream consumers
* trust boundaries
* externally visible contracts
* relevant tests

Identify the smallest set of input properties that the code actually relies on to produce correct output.

Distinguish those required properties from incidental properties merely present in the same file, object, archive, directory, message, or data structure.

Run relevant existing tests before editing when practical.

Do not perform unrelated:

* style cleanup
* architecture redesign
* typing migrations
* schema redesign
* exception redesign
* performance work
* dead-code cleanup
* general refactoring

**Complete when:** the exact review scope, happy path, consumed data, required semantic invariants, externally visible contracts, and relevant tests are understood.

## Step 2 — Find trust boundaries

Trace where untrusted or weakly trusted data becomes trusted.

A **trust boundary** is a point where raw data is parsed, normalized, validated, or otherwise given guarantees that downstream code may legitimately rely on.

Examples include:

* parsing external files
* configuration loading
* schema validation
* protocol decoding
* construction of a validated domain object
* a trajectory loader that establishes shape and semantic guarantees
* an API boundary with explicit preconditions

For each important invariant, determine:

1. where it is first established
2. whether downstream code is entitled to rely on it
3. whether anything can invalidate it before use

Once an invariant is established at a trustworthy boundary and cannot change, downstream internal code should normally rely on it rather than repeatedly re-validating it.

Prefer existing trust boundaries.

Do not introduce new classes, schemas, validation frameworks, exception hierarchies, or architectural layers merely to create a cleaner-looking trust boundary.

**Complete when:** each repeated validation under review can be related to an existing trust boundary, or identified as lacking one.

## Step 3 — Identify what the code actually consumes

Before evaluating individual guards, determine which data and properties affect the reviewed code's behavior or output.

For each file, mapping, object, archive, directory, record, or message the code reads, distinguish:

### Consumed state

Data directly or indirectly used to:

* compute output
* select behavior
* control ordering
* identify related data
* preserve alignment
* determine units, frames, conventions, or semantics
* serialize results
* perform externally visible side effects

### Incidental state

Data that happens to coexist with consumed state but does not affect the reviewed code's output or behavior.

Examples:

* unused arrays in an NPZ archive
* unrelated metadata fields
* extra files that are never selected
* extra records outside the requested range
* optional upstream artifacts ignored by this converter
* naming conventions on files the code never consumes

A converter, reader, or processing stage should not become a general validator for its entire upstream artifact unless that validation is itself part of its documented responsibility.

**Complete when:** the properties required by the reviewed code are separated from unrelated upstream state.

## Step 4 — Audit defensive control flow

Inspect defensive constructs inside the scope, including where relevant:

* explicit precondition checks
* `raise`
* `assert`
* `try` / `except`
* exception translation and wrapping
* existence checks
* `None` checks
* `isinstance` checks
* shape checks
* dtype checks
* finite-value checks
* range checks
* length checks
* ordering and duplicate checks
* fallback/default behavior
* schema checks
* repeated validation
* rejection of unused or extra data

Do not treat ordinary business branching as defensive validation.

For every defensive guard that materially affects readability, answer this counterfactual:

> **If this guard is removed, its assumption is violated, and execution continues from here, what exactly happens?**

Trace the real downstream path far enough to establish the answer.

Do not justify a guard with vague statements such as:

* "this is safer"
* "this catches bad input"
* "this gives a better error"
* "defensive programming is good"
* "the schema says this should not happen"

The question is whether this specific code needs the guard.

Classify each guard into exactly one of the following categories.

## SEMANTIC GUARD — keep

Without the guard, invalid data can still flow through the code and produce plausible but incorrect behavior or output.

Typical examples include:

* wrong units
* wrong coordinate frame
* wrong camera or projection model
* incorrect scale
* incorrect convention
* mismatched IDs or episodes
* RGB/depth/frame misalignment
* incorrect timestamp ordering when downstream code accepts it
* unintended broadcasting
* silent dtype conversion that changes semantics
* NaN or Inf values that downstream computation can propagate
* structurally valid data carrying the wrong meaning
* values that satisfy the programming-language type contract but violate the domain contract

These guards protect against **silent corruption** and are high-value.

Keep them.

## LOCALIZATION GUARD — keep only when materially valuable

Without the guard, the program will eventually fail, but the natural failure occurs sufficiently far from the root cause or is sufficiently misleading that diagnosis becomes materially harder.

Do not keep a guard merely because its custom message is nicer.

A localization guard earns its complexity only when it substantially improves one or more of:

* distance from cause to failure
* ability to identify the offending input
* ability to identify the violated semantic contract
* operational diagnosis in production or batch processing

Prefer the natural failure when it is already:

* immediate
* local
* specific
* easy to associate with the offending operation

For internal scripts and data pipelines, a normal Python, NumPy, filesystem, or library exception is often adequate.

## MECHANICAL DUPLICATE — remove candidate

The next operation, or an immediately adjacent operation, already rejects the same invalid state clearly and locally.

Examples:

```python
if not path.is_file():
    raise ValueError("file is missing")

data = np.load(path)
```

```python
if "pose_world" not in archive:
    raise ValueError("pose_world missing")

pose = archive["pose_world"]
```

```python
if not directory.is_dir():
    raise ValueError("directory missing")

for path in directory.iterdir():
    ...
```

Other common cases include:

* checking file existence immediately before opening it
* checking a mapping key immediately before required indexing
* checking tuple/list unpacking length immediately before direct unpacking
* validating a mechanical type immediately before an API that clearly rejects it
* catching a clear low-level exception only to rephrase the same failure

Remove these unless a real public error contract requires the custom behavior.

## REPEATED INVARIANT — remove or consolidate candidate

The invariant was already established at a trustworthy boundary, nothing can invalidate it before this point, and downstream code checks it again.

Examples:

```text
load trajectory
    ↓
validate finite pose and velocity
    ↓
pass trusted trajectory internally
    ↓
check the same values are finite again
```

or:

```text
validate camera profile
    ↓
derive calibration
    ↓
helper validates the same model/resolution again
```

Keep the authoritative check at the strongest useful trust boundary.

Let trusted internal code rely on established invariants.

Do not repeatedly re-prove the same fact simply because the data crosses helper-function boundaries.

## IRRELEVANT INVARIANT — remove candidate

The guard enforces a property that the reviewed code does not depend on for correct behavior or output.

Violating the property does not affect the subset of data actually consumed by the code.

Examples:

### Unused archive contents

The converter consumes:

```text
time_s
pose_world
velocity_world_mps
yaw_rate_radps
```

but validates the dimensions of every other array stored in the same archive.

Those unrelated arrays are not this converter's responsibility.

### Harmless extra files

The code requires frame files:

```text
0, 1, 2, 3
```

and all four are present.

An additional file:

```text
episode_000001_backup.jpg
```

does not participate in selection, indexing, or output.

Rejecting the episode merely because that unrelated file exists is unnecessary unless directory exclusivity is part of the converter's actual contract.

### Harmless extra records

The code consumes records for a known set of IDs but rejects unrelated extra records that cannot influence the selected data.

### Unused metadata

The code validates metadata fields that are never read and cannot affect interpretation of fields that are read.

Apply this test:

> **If this property changes while every value actually consumed by this code remains unchanged, can this code's behavior or output change?**

If the answer is no, the invariant is probably irrelevant to this scope.

Remove the guard unless this component is explicitly responsible for validating the complete upstream artifact.

This category is especially important in converters and pipeline stages: avoid unnecessary coupling to upstream implementation details.

## UNCERTAIN — preserve

If static reasoning cannot establish the consequence of removal with sufficient confidence, preserve the guard.

Investigate callers, tests, schemas, and downstream usage when that can resolve the uncertainty cheaply.

Do not delete a guard merely because it looks verbose.

Uncertainty is not evidence of redundancy.

**Complete when:** every defensive construct that materially obscures the happy path has been classified, every removal candidate has a concrete justification, and irrelevant upstream properties have been explicitly considered.

## Step 5 — Perform the surgical refactor

Modify guards classified as:

* `MECHANICAL DUPLICATE`
* `REPEATED INVARIANT`
* `IRRELEVANT INVARIANT`

Preserve:

* `SEMANTIC GUARD`
* justified `LOCALIZATION GUARD`
* `UNCERTAIN`

Prefer deletion over replacement.

Prefer direct code over new abstractions.

When removing a mechanical duplicate:

```text
pre-check
↓
operation
```

prefer:

```text
operation
```

when the operation already provides a clear local failure.

When removing repeated validation:

```text
validate at trust boundary
↓
trusted internal data
↓
validate again
```

prefer:

```text
validate at trust boundary
↓
trusted internal data
↓
use directly
```

When removing irrelevant validation:

```text
load artifact
↓
validate consumed fields
↓
validate unrelated fields
↓
use consumed fields
```

prefer:

```text
load artifact
↓
validate only semantic requirements of consumed fields
↓
use them
```

## Extra-data principle

Be especially careful with checks for:

* extra files
* extra keys
* extra arrays
* extra records
* extra frames
* extra metadata

Distinguish **missing required data** from **harmless additional data**.

For example:

```text
expected frames = {0, 1, 2, 3}
actual frames   = {0, 1, 2}
```

is normally a correctness problem because required consumed data is missing.

But:

```text
expected frames = {0, 1, 2, 3}
actual frames   = {0, 1, 2, 3, 4}
```

is not automatically a correctness problem.

If frame `4` is ignored and cannot affect selection, alignment, ordering, or output, rejecting it may be unnecessary over-validation.

Require exact equality only when exact exclusivity itself is a semantic contract.

## Exception-handling principle

Review `try` / `except` according to behavior, not syntax.

Preserve handlers that provide functional behavior such as:

* cleanup
* rollback
* resource release
* retry
* recovery
* transaction semantics
* required public-boundary error translation
* attaching materially useful context unavailable from the underlying exception

A handler is a simplification candidate when it only:

* catches an already clear exception
* changes its type without contractual need
* restates the same failure
* adds generic context such as "processing failed" while preserving no useful recovery behavior

Do not remove `try` / `finally` or equivalent structures that protect resource or transactional correctness merely to reduce visual complexity.

## Do not optimize validation counts

Do not use any of these as success metrics:

* number of `raise` statements
* number of `if` statements
* number of `assert` statements
* number of `try` blocks
* total lines removed
* percentage of validation deleted

A file with many genuine semantic boundaries may legitimately contain many guards.

A file with five guards may still be over-defensive if all five enforce irrelevant state.

Optimize for:

> **maximum semantic protection with minimum interference in the happy path.**

The remaining checks should be meaningful enough that a reader can assume:

> "If this code stops here, continuing would risk semantic correctness, not merely violate an upstream preference."

## Step 6 — Inspect the resulting happy path

After editing, read the modified functions again as normal program logic rather than as a validation audit.

Check whether the primary behavior is now visually apparent.

A reader should be able to understand:

```text
input
↓
transform
↓
compute
↓
write
```

without repeatedly crossing low-value defensive branches.

Do not remove meaningful guards merely to make the function aesthetically linear.

The objective is for exceptional code to remain proportional to the exceptional risks this component actually owns.

**Complete when:** the code's main functional story is easier to follow and every remaining prominent guard protects a meaningful responsibility of this component.

## Step 7 — Verify behavior preservation

Run the relevant regression tests after the refactor.

Also inspect the final diff and verify:

1. valid inputs follow the same functional behavior
2. valid inputs produce the same externally observable outputs
3. public interfaces have not changed
4. CLI behavior has not changed
5. serialized formats and filesystem layouts have not changed
6. no semantic guard against silent corruption was removed
7. no cleanup, rollback, recovery, or transaction behavior was removed
8. no trusted invariant can be invalidated between its remaining validation point and use
9. removed irrelevant checks truly governed data the code does not consume
10. tests were not weakened to accommodate the changes
11. no unrelated refactoring entered the diff
12. changes remain inside the requested scope except for strictly necessary preservation edits

When removing a guard changes invalid-input behavior, determine whether the previous behavior was:

* a documented/tested contract
* relied upon by callers
* or merely incidental defensive behavior

Restore the guard if contractual behavior changed.

Do not restore it merely because a natural underlying exception now replaces a redundant custom exception in internal code.

**Complete when:** relevant regression tests pass and every edited guard satisfies the preservation contract.

## Step 8 — Report concisely

Report:

* scope reviewed
* important semantic guards retained
* mechanical duplicates removed
* repeated invariants consolidated
* irrelevant invariants removed
* uncertain checks deliberately preserved
* tests or verification performed

Call out any intentionally preserved defensive code that may superficially look redundant but protects against silent corruption.

Do not enumerate every untouched `if` or `raise`.

## Decision model

Use this decision path for each significant guard:

```text
What property does this guard enforce?
        |
        v
Does this code actually depend on that property?
        |
        +-- No
        |    -> IRRELEVANT INVARIANT
        |
        +-- Yes
             |
             v
If the guard is removed and the property is violated,
what happens next?
             |
             +-- Execution continues with plausible wrong result
             |       -> SEMANTIC GUARD
             |
             +-- Failure occurs much later or misleadingly
             |       -> LOCALIZATION GUARD
             |
             +-- Immediate clear local failure
             |       -> MECHANICAL DUPLICATE
             |
             +-- Property is already guaranteed by a trust boundary
             |       -> REPEATED INVARIANT
             |
             +-- Consequence cannot be established confidently
                     -> UNCERTAIN
```

For extra data, apply one additional question:

```text
If the extra data disappeared or changed,
while all consumed data stayed identical,
could this code's output change?
        |
        +-- No  -> probably irrelevant
        |
        +-- Yes -> determine the semantic dependency
```

## Review heuristics

Use these heuristics as prompts for investigation, not automatic rewrite rules.

### High-value guards often protect

* units
* coordinate systems
* geometric conventions
* semantic modes
* scale
* alignment
* ordering
* identity relationships
* assumptions NumPy/PyTorch may silently broadcast
* NaN/Inf propagation
* schema ambiguity that downstream code cannot distinguish
* irreversible output corruption

### Low-value guards often protect

* missing files immediately before opening them
* missing keys immediately before required indexing
* types immediately rejected by the called API
* lengths immediately enforced by unpacking
* repeated finite/shape checks on immutable trusted data
* every field in an upstream artifact when only a subset is consumed
* harmless extra files or records
* formatting preferences irrelevant to selected data
* generic exception rewording

These lists are evidence hints only. Always trace the actual code path.

## Non-goals

This skill is not:

* a general refactoring skill
* a style cleanup pass
* a request to minimize validation count
* a type-system migration
* a schema redesign
* an exception-hierarchy redesign
* a validation-framework migration
* an architecture cleanup
* a broad API redesign
* a performance optimization task
* a test simplification task
* an opportunity for speculative abstraction

Prefer a small diff that removes only proven low-value defensive code over a broader redesign that happens to look cleaner.

## Completion standard

The refactor is successful when:

* the happy path is materially easier to read
* required semantic invariants remain protected
* silent corruption risks are not weakened
* mechanical duplicate checks are reduced
* repeated invariants are trusted after their boundary
* unrelated upstream state is no longer unnecessarily policed
* interfaces and valid-input behavior remain unchanged
* relevant regression tests pass

The target state is not validation-free code.

The target state is code where each remaining defensive branch earns its place.
