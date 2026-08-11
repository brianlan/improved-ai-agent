---
name: reduce-defensive-validation
description: Review and surgically refactor a specified code scope to remove low-value defensive validation while preserving behavior, interfaces, and regression tests.
disable-model-invocation: true
---

# Reduce Defensive Validation

Surgically simplify defensive control flow that obscures the code's real logic.

The goal is **not fewer checks**. The goal is a higher signal-to-noise ratio:

> Preserve guards against **silent semantic corruption**. Remove guards that merely duplicate clear, immediate failures already provided by the underlying operation.

**Validate semantics, not mechanics.**

Treat the user's invocation arguments as the review scope. The scope may be a file, directory, function, class, diff, PR, or other explicitly named code region.

Modify only that scope. If the requested refactor genuinely requires changes outside it, report that constraint instead of expanding the refactor.

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
* existing regression coverage

Keep all relevant regression tests passing.

Use existing tests as verification, not as the sole justification for removing a guard: an untested invariant may still prevent silent corruption.

Do not weaken, delete, or rewrite tests merely to make the refactor pass.

For private/internal code, an incidental exception message or exception type produced solely by a redundant pre-check is not automatically a stable contract. Treat it as a contract when documentation, callers, or tests rely on it.

## Step 1 — Establish the scope and baseline

Read the requested scope and the smallest amount of surrounding code needed to understand its callers, inputs, outputs, and invariants.

Identify:

* the main happy-path behavior
* inputs entering from external or weakly trusted sources
* existing schemas, parsers, validators, types, and tests
* public or tested error behavior
* relevant regression-test commands

Run the relevant existing tests before editing when practical.

Do not perform unrelated style cleanup, architecture redesign, typing migrations, exception redesign, or general refactoring.

**Complete when:** the exact review scope, happy path, externally visible contracts, and relevant tests are known.

## Step 2 — Find trust boundaries

Trace where data becomes trusted.

A **trust boundary** is a point where raw or externally supplied data is parsed, normalized, validated, or otherwise given invariants that downstream code is entitled to rely on.

Examples include:

* file or network parsing
* configuration loading
* schema validation
* construction of a validated domain object
* a loader that guarantees array shape and semantics
* an API boundary with documented preconditions

For each important invariant, determine where it is first established and whether anything can invalidate it before later use.

Prefer existing trust boundaries. Do not introduce new classes, schemas, exception hierarchies, or validation frameworks merely to justify deleting checks.

**Complete when:** every repeated validation under review can be related to an established trust boundary, or identified as having no such guarantee.

## Step 3 — Audit defensive control flow

Inspect defensive constructs inside the scope, including where relevant:

* explicit precondition checks
* `raise`
* `assert`
* `try` / `except`
* exception translation and wrapping
* existence checks
* `None` checks
* `isinstance` checks
* shape, dtype, range, finite-value, and length checks
* duplicate and ordering checks
* fallback/default behavior
* repeated validation of previously validated data

Do not treat ordinary business branching as defensive validation.

For every candidate guard, answer this counterfactual:

> **If this guard is removed and its assumption is violated, what exactly happens next?**

Trace the actual downstream path far enough to determine the outcome. Do not assume that "something will probably fail."

Classify each guard into one of the following categories.

### SEMANTIC GUARD — keep

Without the guard, invalid data can still be accepted and produce plausible but incorrect behavior or output.

Typical examples:

* wrong units
* wrong coordinate frame
* wrong camera or projection model
* mismatched IDs or episodes
* RGB/depth/frame misalignment
* incorrect scale or convention
* timestamp or ordering errors that downstream code accepts
* unintended broadcasting
* silent dtype conversion with changed semantics
* NaN/Inf values that downstream computation can propagate
* structurally valid data carrying the wrong meaning

These guards protect against **silent corruption** and are high-value.

### LOCALIZATION GUARD — usually keep

The underlying code would eventually fail, but only much later or with an error substantially disconnected from the real cause.

Keep such a guard when it materially shortens the distance between cause and failure or turns an opaque failure into an actionable one.

A different error message by itself is not enough; the diagnostic improvement must be meaningful.

### MECHANICAL DUPLICATE — remove candidate

The immediately following operation already rejects the same invalid state clearly and locally.

Example:

```python
if not path.is_file():
    raise ValueError("file is missing")

data = np.load(path)
```

If `np.load(path)` already produces an immediate, useful missing-file error and no public error contract requires the wrapper, the pre-check adds little value.

Other common cases:

* checking a mapping key immediately before required indexing
* checking file readability immediately before an operation that opens it
* checking a mechanical type constraint immediately before an API that clearly rejects it
* wrapping a clear low-level exception only to restate the same failure

### REPEATED INVARIANT — remove or consolidate candidate

The same invariant was already established at a trust boundary, nothing can invalidate it, and downstream code validates it again merely because it receives the data.

Keep the authoritative boundary check and let trusted internal code rely on it.

Do not repeatedly re-prove the same invariant across internal helper functions.

### UNCERTAIN — preserve

If static reasoning cannot establish the consequence of removal with sufficient confidence, keep the guard.

Uncertainty is not evidence that a check is redundant.

**Complete when:** every defensive construct that materially affects readability has been classified, and every removal candidate has a concrete downstream-failure analysis.

## Step 4 — Perform the surgical refactor

Refactor only guards classified as `MECHANICAL DUPLICATE` or `REPEATED INVARIANT`.

Prefer deletion and simplification over replacement abstractions.

When a repeated invariant exists:

* retain the check at the strongest existing trust boundary
* remove redundant downstream checks
* keep downstream code direct and readable

When a mechanical pre-check merely duplicates an immediate underlying failure:

* call the underlying operation directly
* preserve public/tested error contracts where required

When reviewing `try` / `except`, distinguish pure defensive wrapping from functional exception handling.

Preserve handlers that provide real behavior such as:

* cleanup
* rollback
* resource release
* retry
* recovery
* transaction semantics
* required error translation at a public boundary

A handler that only catches a clear exception and rephrases it without adding useful context is a simplification candidate.

Keep `SEMANTIC GUARD`, justified `LOCALIZATION GUARD`, and `UNCERTAIN` checks intact.

Do not use counts of `raise`, `if`, `assert`, or `try` as optimization targets. A scope containing many meaningful semantic guards may require many checks.

Keep the happy path visually dominant wherever possible.

**Complete when:** every edit has a specific classified justification and the diff contains no unrelated refactoring.

## Step 5 — Verify behavior preservation

Run the relevant regression tests after the refactor.

Also inspect the final diff and verify:

1. valid inputs follow the same functional path and produce the same externally observable results
2. public interfaces have not changed
3. serialized and filesystem outputs have not changed
4. no semantic guard against silent corruption was removed
5. no cleanup, rollback, or recovery behavior was accidentally removed
6. no trusted invariant can be invalidated between its remaining validation point and its use
7. tests were not weakened to accommodate the changes
8. the diff is limited to the requested scope and this refactoring objective

If a removed guard causes a regression, restore it unless the regression itself proves that an existing test encodes non-contractual incidental behavior and the user explicitly permits changing that behavior.

**Complete when:** relevant regression tests pass and every changed defensive construct still satisfies the preservation contract.

## Step 6 — Report concisely

Report:

* scope reviewed
* important semantic guards intentionally retained
* redundant validation removed or consolidated
* any uncertain checks deliberately left unchanged
* tests or verification performed

Focus the report on decisions that matter. Do not enumerate every untouched check.

## Decision shorthand

Use this mental model throughout the review:

```text
Guard
  |
  v
If removed, assumption is violated
  |
  +--> Immediate, clear, local failure
  |       -> MECHANICAL DUPLICATE
  |
  +--> Same invariant already guaranteed and still valid
  |       -> REPEATED INVARIANT
  |
  +--> Delayed or misleading failure
  |       -> LOCALIZATION GUARD
  |
  +--> Execution continues with plausible wrong result
  |       -> SEMANTIC GUARD
  |
  +--> Consequence cannot be established confidently
          -> UNCERTAIN
```

The preferred end state is code in which defensive checks are sparse enough that the happy-path logic is easy to read, while the remaining checks visibly protect real semantic boundaries.

## Non-goals

This skill is not a general cleanup pass.

Its success criterion is **meaningful validation density**, not minimal validation count.

Leave unrelated concerns alone, including:

* broad architecture changes
* stylistic rewrites
* type-system migrations
* schema redesign
* new validation frameworks
* exception-hierarchy redesign
* speculative abstractions
* opportunistic performance work
* unrelated dead-code cleanup

A small diff that removes only proven low-value defensive code is preferable to a larger "cleaner" redesign.

