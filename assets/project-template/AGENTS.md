# Project Agent Guide

Keep this file concise. Link to durable project documents rather than duplicating them.

## Product

Read `docs/product/PRODUCT.md`.

## Repository map

Document the main modules and boundaries here after bootstrap.

## Standard commands

```text
install:
dev:
format:
lint:
typecheck:
test:
test:integration:
test:e2e:
build:
security:
```

Do not claim a command passed unless it ran successfully.

## Workflow

For R1–R3 work:

1. Create/update a spec.
2. Assign risk.
3. Create an ExecPlan when complex.
4. Implement the smallest vertical slice.
5. Verify.
6. Run independent review.
7. Produce release evidence.
8. Record learning.

## Always

- Preserve user data and permission boundaries.
- Keep changes focused and reversible.
- Update tests and documentation with behavior.
- Use least privilege.
- Record assumptions.

## Ask/approve before

- Production deploy
- Destructive data action
- Schema migration with transformation
- Auth/permission change
- Payment logic
- New privileged dependency
- Weakening a quality/security gate

## Never

- Commit secrets
- Edit production directly
- Fabricate evidence
- Disable checks to force green
- Auto-approve R2/R3 release
- Modify unrelated code without justification

## Definition of Done

Read `docs/quality/DEFINITION_OF_DONE.md`.
