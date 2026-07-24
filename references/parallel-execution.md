# Controlled Parallel Execution

## 1. Principle

Use parallel agents to shorten independent work or improve review breadth. Do not use them to avoid decomposition or unresolved design decisions.

```text
Specify and freeze contracts
        ↓
Build dependency graph
        ↓
Fan out independent work
        ↓
Independent verification
        ↓
Fan in through one coordinator
        ↓
Combined regression and release gate
```

Parallel execution increases throughput only when the coordination tax is smaller than the saved elapsed time.

## 2. Eligibility test

A work unit qualifies only when:

- It has a bounded goal, explicit inputs/outputs, and acceptance criteria.
- It can finish without waiting for another worker.
- Shared interfaces and contracts are stable.
- Write sets do not overlap, or writers are isolated by worktree and branch.
- Ports, test databases, caches, queues, credentials, and temporary resources are namespaced.
- It can be verified independently.
- Merge order and rollback are known.
- One coordinator owns integration.

If any condition is unclear, keep the work sequential until the boundary is clarified.

## 3. Preferred patterns

### Read-only fan-out

Use as the default parallel pattern for codebase mapping, impact analysis, logs, security review, dependency review, documentation, and independent test analysis.

### Parallel verification

Run independent checks concurrently: unit/integration/E2E suites, browser/device/runtime matrices, static analysis, security scans, performance, and accessibility.

### Isolated implementation

Use only after module and interface boundaries are frozen. Give each writer one worktree, branch, task packet, allowed scope, required checks, and output contract.

### Independent review quorum

Use read-only reviewers with distinct lenses: correctness, security, migration/reliability, and product acceptance.

## 4. Worktree and resource isolation

Every concurrent writer uses a separate Git worktree and branch.

A worktree isolates files, not all shared resources. Isolate:

- Environment files
- Ports
- Databases/schemas
- Object-storage prefixes
- Queues/topics
- Browser profiles
- Containers
- Test users
- Temporary directories

Never let two agents write to the same checkout or merge their own work to main.

## 5. Parallel task packet

Use the generated `docs/plans/PARALLEL_EXECUTION_BOARD.md` to track dependency, resource, task-control, integration, and combined-verification state for a parallel batch.

```markdown
# Parallel Task: <ID>

## Goal
## Risk and approval owner
## Dependencies
## Frozen contracts
## Allowed files/modules
## Forbidden files/modules
## Allowed tools and external actions
## Credential and data scope
## Acceptance criteria
## Required checks
## Environment namespace
## Expected commit/patch and evidence
## Stop conditions
```

Workers must stop instead of silently changing a frozen contract.

## 6. Fan-in integration

One coordinator must:

1. Confirm the expected base commit.
2. Inspect each scope and diff.
3. Reject unrelated edits.
4. Merge in dependency order.
5. Re-run local checks after each merge when useful.
6. Run the complete affected verification stack on the combined state.
7. Run an independent combined-diff review.
8. Produce one release evidence package.

Individually green branches do not prove the combined system is green.

## 7. CI and deployment concurrency

Safe CI candidates include test suites, static analysis, builds, browser/device matrices, and scans. Set explicit maximum parallelism.

Serialize with concurrency groups or environment locks:

- Shared staging deploys
- Production deploys
- Database migrations
- Shared integration environments
- Release tags
- Artifact signing
- Infrastructure mutations

Queue production releases; do not run them concurrently.

## 8. OPC starting budget

```text
Read-only workers: up to 3
Write workers: up to 2
Independent reviewer: 1
Production writers: 0
```

These are category ceilings, not additive entitlements. Start with the smallest useful set, obey stricter host/runtime limits, and count the coordinator when it consumes an agent slot. Raise a category ceiling only after evidence shows lower lead time without increased conflicts, defects, cost, or owner attention.

## 9. Metrics

Track:

- Estimated sequential time
- Actual elapsed time
- Integration time
- Token/infrastructure cost
- Merge conflicts
- Duplicate work
- Integration defects
- Rework cycles
- Owner review time
- First-pass integration rate

A fast parallel batch that increases defects or owner attention is not successful.
