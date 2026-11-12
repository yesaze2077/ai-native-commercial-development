# Architecture and Stack Decisions

## Mode and applicable inputs

Use when a new system needs a deployable shape, a boundary changes, or feasibility is uncertain. Start from accepted journeys, data/trust needs, deployment constraints, budget and maintenance ownership. Inspect the existing runtime, dependencies, conventions and operations before proposing a stack. An increment should preserve the current stack unless a demonstrated constraint justifies change. Architecture review is read-only unless implementation is authorized.

This guide does not authorize cloud resources, paid services, external writes or production connections. Security, migration, release and approval requirements remain in the existing references.

## Working method

1. **Turn requirements into decision constraints.** Identify where it can run, who operates it, required integrations, expected load and latency, data locality/retention, transactional invariants, identity/permission boundaries, availability/recovery needs and cost ceiling. Mark unknown volume and cost as estimates with assumptions. Verify supported versions and material service limits from current primary sources when selecting dependencies.
2. **Compare only credible candidates.** For an existing system, compare staying with it against the smallest viable extension; include replacement only if evidence warrants it. For a new product, compare a small shortlist, usually two or three. Use deployment fit, data consistency, authorization support, integration fit, scale/cost and maintenance burden as decision columns. Include migration/exit effort and ownership, not feature counts or popularity. Do not select a vendor or introduce infrastructure merely because it appears in a reference workflow.
3. **Fix the choice and its rationale.** Write a short [ADR](../assets/project-template/docs/decisions/ADR_TEMPLATE.md), or extend the existing decision, with constraints, selected option, rejected alternatives, tradeoffs, evidence and a revisit trigger. Identify unresolved decisions that block only their dependent work. A proposed choice is not an approved purchase or deployment.
4. **Define contracts before broad implementation.** A compact diagram plus the following affected contracts is sufficient; update existing architecture/specification material rather than generating a document set.

| Contract | Record what implementers and reviewers need |
|---|---|
| System/data flow | Clients, services, stores, external systems, trust boundaries and sensitive/side-effecting paths. |
| Domain/data | Terms, entity identifiers/relationships, tenant or owner boundary, lifecycle/retention and invariants; transaction/concurrency expectations. |
| API/integration | Request/response/schema, validation/errors, authentication/authorization, timeouts, retries, idempotency and compatibility rules where applicable. |
| Roles | Actor × permitted operation/resource, enforcement point and negative verification case. |
| Failure/recovery | Dependency loss, partial completion, duplicate/replayed work, detection, retry/reconciliation and restore/rollback responsibilities. |

5. **Probe the riskiest boundary when needed.** Set a time/cost cap and one falsifiable technical question. Build the smallest runnable vertical path through the relevant interface, domain rule, persistence and integration boundary, using fixtures or an authorized sandbox. Include the failure or denied-access case that threatens the design. A dependency ping is insufficient if the uncertainty concerns a complete transaction. Do not build the full feature or connect production to settle a local feasibility question.
6. **Evaluate and close the probe.** Record commands, runtime/dependency versions, environment, observed behavior, costs measured versus estimated, limitations and the decision. Keep reusable code only after normal review and checks; label temporary scaffolding and remove it when it has no continuing value. If the cap expires, report the unresolved question and choose a smaller fallback or a bounded next investigation.

## Outputs and exit basis

The result is a justified stack/boundary decision, current diagram, affected data/API/role/recovery contracts and probe evidence when required. These can live in the existing ADR, SPEC and repository map. Assign responsibility for operation and unresolved dependencies.

Proceed when the selected slice can run in the authorized environment, critical invariants and trust boundaries are understandable, and major feasibility uncertainty has evidence or an explicit bounded fallback. Stop dependent implementation when a critical contract is contradictory or unproven. A successful local probe establishes only the conditions exercised; it does not establish capacity, security, production readiness or release authorization.

Mechanism sources: [BMAD architecture](https://github.com/bmad-code-org/BMAD-METHOD/blob/a867e1604b365d48ea03cbd109da1066ba0c84bc/skills/bmad-architecture/SKILL.md), [Matt Pocock domain modeling](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/domain-modeling/SKILL.md), [bounded UI prototypes](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/prototype/UI.md). Borrow decision and boundary-testing mechanisms, not their stack assumptions.
