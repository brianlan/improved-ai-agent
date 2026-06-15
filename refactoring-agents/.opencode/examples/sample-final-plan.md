# Refactoring Plan

## 1. Refactoring Goal

Improve maintainability of order creation by separating validation from persistence while preserving all externally visible behavior.

## 2. Scope and Non-Goals

Scope:

- `OrderService.createOrder`
- order request validation
- tests that characterize invalid-order behavior

Non-goals:

- no database schema changes
- no authorization changes
- no public API response changes

## 3. Current Problems

- `createOrder` mixes validation, normalization, authorization checks, and persistence.
- Invalid-order behavior is difficult to test without touching persistence.

## 4. Agreed Refactoring Strategy

Lock current behavior with characterization tests, then extract validation into an order-domain helper without changing persistence or authorization.

## 5. Step-by-Step Task Breakdown

### Task 1: Add characterization tests for invalid order requests

Why:

- Existing behavior needs to be locked before moving validation logic.

Scope:

- Cover current error codes, messages, and response shape for invalid order inputs.

Files likely involved:

- `tests/order/OrderService.test.ts`

Safety constraints:

- Assertions should reflect current behavior, not preferred behavior.

Verification:

- Run the existing order service test suite.

Risk:

- Low

Dependencies:

- None.

### Task 2: Extract validation into an order-domain helper

Why:

- Separates validation from persistence and makes behavior easier to test directly.

Scope:

- Move validation logic into `src/order/validation.ts` or an existing order-domain validation module.
- Keep persistence and authorization logic unchanged.

Files likely involved:

- `src/order/OrderService.ts`
- `src/order/validation.ts`
- `tests/order/OrderService.test.ts`

Safety constraints:

- Preserve public API response shape.
- Preserve existing error codes and messages.
- Keep validation inside the order domain boundary.
- Do not change database writes or authorization checks.

Verification:

- Run characterization tests from Task 1.
- Add focused unit tests for the extracted validation helper.
- Run existing order service tests.

Risk:

- Medium

Dependencies:

- Task 1 must be complete first.

## 6. Dependencies Between Tasks

- Task 1 precedes Task 2.

## 7. Risk Summary

- Highest risk: Medium.
- Main risk: subtle changes to invalid-order error behavior.

## 8. Required Tests / Verification

- Characterization tests for current invalid-order behavior.
- Unit tests for extracted validation logic.
- Existing order service test suite.

## 9. Rollback Strategy

- Revert the extraction commit while keeping characterization tests if they accurately document existing behavior.

## 10. Open Questions

- Confirm whether any clients depend on exact validation error ordering.

## 11. Rejected or Postponed Ideas

- Move validation into a shared utility: rejected because it weakens the order domain boundary.

