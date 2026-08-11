---
name: reduce-defensive-validation
description: Review and surgically refactor a specified code scope to remove low-value defensive validation while preserving behavior, interfaces, and regression tests.
disable-model-invocation: true
---

# Reduce Defensive Validation

Simplify defensive control flow that obscures the code's real logic.

The goal is **not fewer checks**. The goal is:

> Preserve checks that prevent silent semantic errors. Remove checks that duplicate natural failures, re-prove trusted invariants, or validate state this code does not depend on.

Use these anchors throughout the review:

> **Validate semantics, not mechanics.**

> **Validate what you consume, not everything you encounter.**

> **Capability is not contract.**

The user's invocation arguments define the review scope. Read adjacent code as needed to understand data flow and contracts, but keep modifications inside the requested scope unless a minimal adjacent change is strictly necessary.

## Preservation contract

This is a behavior-preserving refactor.

Preserve:

* valid-input behavior and outputs
* accepted-input contracts and schema restrictions
* public interfaces and return types
* CLI behavior
* serialized formats and filesystem layouts
* externally visible side effects
* documented or tested error contracts
* semantic invariants required for correctness
* cleanup, rollback, recovery, and transaction behavior
* existing regression coverage

Relevant regression tests must continue to pass.

Do not weaken or rewrite tests to accommodate the refactor.

For private/internal code, a custom exception type or message produced only by a redundant pre-check is not automatically part of the contract unless callers, documentation, or tests rely on it.

## 1. Understand the responsibility

Read the requested scope and enough surrounding code to establish:

* the happy-path behavior
* what inputs are actually consumed
* what outputs and side effects are produced
* which input properties are required for correct output
* which input forms are intentionally accepted or rejected
* where untrusted data becomes trusted
* relevant callers and tests

Separate **consumed state** from incidental upstream state.

Consumed state affects computation, selection, alignment, identity, semantics, serialization, or externally visible behavior.

Incidental state merely coexists with consumed data, such as unused archive arrays, unrelated metadata, or harmless files that are never selected.

A converter or processing stage should not become a validator for an entire upstream artifact unless complete validation is explicitly part of its responsibility.

### Capability is not contract

Do not remove an explicit schema or accepted-input restriction merely because downstream code could technically process the rejected form.

For example, if one caller intentionally requires:

```python
episodes: list
```

while another accepts:

```python
episodes: list | dict
```

the fact that both can eventually be iterated does not make the distinction redundant.

Treat deliberate differences in:

* accepted types
* schema forms
* required fields
* modes
* versions
* input layouts

as contracts unless analysis shows they are accidental and irrelevant.

**Complete when:** you can state what this code depends on, what it intentionally accepts or rejects, and what upstream state is irrelevant.

## 2. Find trust boundaries

A **trust boundary** is where raw or weakly trusted data receives guarantees that downstream code may rely on: parsing, normalization, schema validation, construction of a validated object, or an equivalent boundary.

For each important invariant, determine:

1. where it is established
2. whether anything can invalidate it before use

Once an invariant has been established at a trustworthy boundary and remains valid, internal downstream code should normally rely on it rather than validate it again.

Use existing boundaries. Do not introduce new schemas, classes, validation frameworks, or architecture merely to eliminate checks.

**Complete when:** repeated checks can be related to an established trust boundary or identified as lacking one.

## 3. Audit defensive control flow

Review meaningful defensive constructs such as:

* precondition checks
* `raise` and `assert`
* `try` / `except`
* existence and type checks
* shape, dtype, range, finite-value, length, ordering, and duplicate checks
* fallback behavior
* schema checks
* rejection of extra files, fields, records, or arrays

Do not treat ordinary business branching or deliberate input-contract enforcement as redundant validation.

For each significant guard, first ask:

> **Does this code actually depend on the property being checked?**

If yes, ask:

> **If this guard is removed and the property is violated, what exactly happens next?**

Trace the real downstream path. Do not assume that something will eventually fail.

Classify the guard using the following categories.

### SEMANTIC GUARD — keep

Without the guard, execution may continue and produce plausible but incorrect results.

Common examples:

* wrong units, coordinate frames, scale, or conventions
* mismatched IDs, frames, images, or trajectories
* wrong semantic mode or camera model
* ordering or alignment errors
* unintended broadcasting
* semantic dtype conversion
* NaN/Inf propagation
* structurally valid data carrying the wrong meaning

These protect against **silent corruption**.

### CONTRACT GUARD — keep

The guard intentionally defines which inputs this component accepts, even if downstream operations could technically handle additional forms.

Examples include:

* one metadata source must use a list while another may use a mapping
* only specific schema versions are accepted
* a mode intentionally requires a particular representation
* a public or internal API explicitly rejects otherwise-processable input

Do not infer redundancy from implementation capability.

Remove a contract guard only when surrounding code, documentation, callers, and tests establish that the restriction is accidental rather than intentional.

### LOCALIZATION GUARD — keep only when it materially helps

The program would naturally fail, but much later or with an error substantially disconnected from the real cause.

Keep the guard only when it meaningfully improves diagnosis.

A nicer custom error message alone is not enough.

If the natural Python, filesystem, NumPy, or library exception is already immediate, local, and understandable, prefer the natural failure.

### MECHANICAL DUPLICATE — remove

The following operation already rejects the same invalid state clearly and locally.

Examples:

```python
if not path.is_file():
    raise ValueError("file missing")
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

This also includes redundant type or length checks immediately enforced by indexing, unpacking, or the called API.

### REPEATED INVARIANT — remove or consolidate

The same property was already established at a trust boundary, cannot have changed, and is checked again downstream.

Keep the authoritative check. Let trusted internal code use the established invariant directly.

Example:

```text
trajectory loader
    ↓
validates pose/velocity are finite
    ↓
trusted trajectory
    ↓
derive ego pose using finite arithmetic
    ↓
validate ego pose is finite again
```

The downstream check is normally redundant unless an intervening operation can independently introduce invalid values.

### IRRELEVANT INVARIANT — remove

The guard validates a property this code does not depend on.

Apply this test:

> **If this property changed while every value actually consumed by this code remained identical, could this code's behavior or output change?**

If not, the property is normally outside this component's responsibility.

Typical examples:

* validating unused arrays in an archive
* validating unused metadata
* rejecting unrelated files that are never selected
* enforcing upstream formatting that cannot affect consumed data

Be careful with apparently extra data. Extra state is irrelevant only when it cannot indicate a semantic mismatch.

An unrelated backup file may be harmless, while an unexpected additional numbered frame may indicate stale or mismatched rendered data.

### UNCERTAIN — preserve

If the consequence of removal cannot be established confidently, preserve the guard.

Inspect nearby callers, tests, schemas, and downstream usage when they can resolve the uncertainty cheaply.

**Complete when:** every defensive construct that materially obscures the happy path has a concrete classification and every removal candidate has a traced justification.

## 4. Sweep downstream from trust boundaries

After the local guard-by-guard audit, make one dedicated pass from each trust boundary through its downstream uses.

For every invariant established at the boundary, ask:

> **Where is this same fact checked again before anything could have invalidated it?**

Look specifically for repeated:

* shape checks
* finite-value checks
* type checks
* range checks
* schema checks
* identity/alignment checks
* normalized-value checks

Do not require textual duplication. A downstream check may re-prove the same invariant indirectly after transformations that preserve it.

Remove the downstream check when:

1. the source invariant was already established,
2. intervening operations preserve it, and
3. no new failure mode is introduced.

Preserve checks after operations that can independently violate the invariant.

**Complete when:** each trusted invariant has been followed downstream far enough to identify redundant re-validation.

## 5. Refactor surgically

Modify only:

* `MECHANICAL DUPLICATE`
* `REPEATED INVARIANT`
* `IRRELEVANT INVARIANT`

Preserve:

* `SEMANTIC GUARD`
* `CONTRACT GUARD`
* justified `LOCALIZATION GUARD`
* `UNCERTAIN`

Prefer deletion and direct code over replacement abstractions.

Prefer:

```text
validate at trust boundary
        ↓
trusted internal data
        ↓
use directly
```

over:

```text
validate
↓
pass to helper
↓
validate again
↓
pass to helper
↓
validate again
```

Prefer loading and validating only consumed state when possible:

```python
required = ("time_s", "pose_world", "velocity_world_mps", "yaw_rate_radps")
arrays = {key: np.asarray(archive[key]) for key in required}
```

rather than loading an entire artifact and policing unrelated contents.

### Exception handling

Preserve `try` / `except` that provides real behavior:

* cleanup
* rollback
* retry
* recovery
* resource release
* transaction semantics
* required error translation
* materially useful diagnostic context

Simplify handlers that merely catch an already-clear exception and restate the same failure.

### Extra data

Distinguish **missing required data** from **additional data**.

Missing consumed data is normally an error.

Additional data is an error only when:

* exclusivity itself is part of the contract, or
* the extra data is evidence of inconsistency, misalignment, stale artifacts, or incorrect provenance.

Do not enforce exact equality merely because an upstream format happens to be exact.

## 6. Review the happy path

After editing, reread the modified functions as program logic rather than as a validation audit.

The main behavior should be visually easy to follow:

```text
read
  ↓
transform
  ↓
compute
  ↓
write
```

Defensive branches should remain where continuing would risk semantic correctness, violate an intentional contract, or where a materially better failure boundary is justified.

Do not remove meaningful checks merely to make the code look linear.

**Complete when:** the functional story is easier to read and every prominent remaining guard earns its place.

## 7. Verify

Run the relevant regression tests.

Inspect the final diff and verify:

1. valid-input behavior and outputs are unchanged
2. accepted-input contracts have not been unintentionally broadened or narrowed
3. public interfaces are unchanged
4. serialized and filesystem outputs are unchanged
5. no silent-corruption guard was removed
6. cleanup, rollback, recovery, and transaction behavior remain intact
7. trusted invariants cannot become invalid between validation and use
8. removed irrelevant checks truly governed state this code does not consume
9. tests were not weakened
10. no unrelated refactoring entered the diff
11. changes remain within scope

Pay particular attention to deleted checks that previously rejected an input.

Ask:

> **Did this change only how invalid input fails, or did it make previously rejected input proceed successfully?**

The first may be acceptable for a redundant private pre-check.

The second changes the accepted-input domain and requires evidence that the old restriction was not contractual.

Restore the guard when that evidence is absent.

**Complete when:** relevant regression tests pass and the preservation contract holds.

## Report

Report concisely:

* scope reviewed
* semantic and contract guards retained
* redundant or repeated validation removed
* irrelevant validation removed
* uncertain guards deliberately preserved
* tests or verification performed

Do not enumerate every untouched check.

## Decision model

```text
What property does this guard enforce?
        |
        v
Is it an intentional accepted-input contract?
        |
        +-- Yes -> CONTRACT GUARD
        |
        +-- No / not established
                |
                v
Does this code depend on the property?
        |
        +-- No
        |    -> IRRELEVANT INVARIANT
        |
        +-- Yes
             |
             v
What happens without the guard?
             |
             +-- Plausible wrong result
             |       -> SEMANTIC GUARD
             |
             +-- Much later / misleading failure
             |       -> LOCALIZATION GUARD
             |
             +-- Immediate clear local failure
             |       -> MECHANICAL DUPLICATE
             |
             +-- Already guaranteed and unchanged
             |       -> REPEATED INVARIANT
             |
             +-- Cannot determine confidently
                     -> UNCERTAIN
```

## Success criterion

Do not optimize:

* number of `raise` statements
* number of `if` statements
* number of `try` blocks
* lines removed
* percentage of validation deleted

Optimize for:

> **Maximum semantic and contractual protection with minimum interference in the happy path.**

The target is not validation-free code.

The target is code where each remaining defensive branch earns its place.

