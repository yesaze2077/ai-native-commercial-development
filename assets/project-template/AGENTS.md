# Project Agent Guide

Keep this file concise. Link to durable project documents rather than duplicating them.

## Product

Read `docs/product/PRODUCT.md`.

For material or ambiguous work, read the accepted intent under `docs/intents/` and the authority/parent relationships in `docs/governance/ARTIFACT_LINEAGE.md`. Use one authoritative system per artifact; do not edit mirrors as independent sources of truth.

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
2. Link it to an accepted intent or equivalent authoritative request.
3. Assign risk.
4. Create an ExecPlan when complex.
5. Implement the smallest vertical slice.
6. Verify.
7. Run independent review using `docs/governance/REVIEW_POLICY.md`.
8. Produce release evidence.
9. Record learning.

## Always

- Preserve user data and permission boundaries.
- Keep changes focused and reversible.
- Update tests and documentation with behavior.
- Use least privilege.
- Record assumptions.
- Register mandatory policies in `docs/governance/GUARDRAIL_CONTRACT.md` with deterministic enforcement evidence.

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
