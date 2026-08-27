# Operating Model

## Contents

1. Accountability model
2. Operating modes
3. Phase artifacts
4. Agent role separation
5. Context and memory
6. Change-size discipline
7. Comprehension control
8. Controlled parallelism

## 1. Accountability model

Use a three-layer model:

| Layer | Owner | Responsibility |
|---|---|---|
| Outer loop | Human owner | Product intent, risk acceptance, resource tradeoffs, final ship/block decision |
| Inner loop | Coding agents | Investigate, specify, plan, implement, test, review, document, report |
| Mechanical controls | CI/CD and scripts | Build, lint, typecheck, tests, scans, provenance, deployment checks |

Do not delegate accountability merely because an agent can execute the work.

## 2. Operating modes

### Bootstrap

Use for a new repository or an existing prototype moving toward commercial use.

Required outputs:

- Product summary
- Intent template and artifact-lineage registry
- Repository map
- Architecture baseline
- Risk register
- Definition of Done
- CI plan
- Security baseline
- Release and rollback plan
- Initial critical journeys

### Feature/change

Use intent when needed → specification → plan → tasks → implementation → verification → review → release evidence. A narrow R0 or R1 change may use its issue or request as the intent when it already states the problem, outcome, constraints, owner, and approval.

### Bug/incident

Use reproduce → failing evidence → root cause → red/green test → minimal fix → regression → incident learning.

### Review/audit

Do not edit first. Build an evidence inventory, identify gaps, rank by risk, and propose the smallest controlled remediation plan.

### Release/migration

Freeze scope. Verify release evidence, backup, migration, monitoring, rollout, rollback, and approvals.

### Practice radar

Research current practices, create candidates, and do not change required policy directly.

### Skill evolution

Run candidate evaluation, skill evals, regression comparison, and a governance PR.

## 3. Phase artifacts

| Phase | Minimum artifact |
|---|---|
| Capture | Accepted intent or equivalent authoritative request |
| Orient | Repository map and baseline |
| Specify | Approved spec |
| Plan | ExecPlan for complex work |
| Implement | Focused commits and updated docs |
| Verify | Machine-readable and human-readable evidence |
| Review | Findings with severity |
| Release | Release evidence and verdict |
| Observe | Dashboard/alerts and post-release note |
| Learn | Test, rule, tool, or candidate |

## 4. Agent role separation

For solo development, emulate separation with contexts rather than headcount.

Recommended minimum:

1. **Primary agent:** investigates and implements.
2. **Reviewer context:** starts fresh with spec, diff, and evidence.
3. **Human owner:** validates user behavior and decides release.

Add specialist agents only when they reduce risk or preserve context:

- Security reviewer
- Test-impact reviewer
- Migration reviewer
- UI/browser verifier
- AI-eval reviewer

Do not create a multi-agent ceremony for a trivial R0 task.

## 5. Context and memory

Keep durable state on disk:

- Intents and authoritative source references
- Artifact-lineage registry
- Specs
- Plans
- Decisions
- Progress log
- Tests
- Release evidence
- Incident reviews
- Practice candidates

Use fresh contexts for independent judgment. Recover state from repository artifacts, not from a huge inherited conversation.

Prefer just-in-time context:

1. Read the repository map.
2. Search for relevant symbols and decisions.
3. Load only files needed for the task.
4. Summarize findings into the active plan.

### Artifact authority and lineage

The repository is always the durable execution and audit record, but a repository file does not have to be the business system of record for every artifact. For each intent, specification, plan, decision, change, review, release, and incident:

1. Name exactly one authoritative system and stable record ID.
2. Link each derived artifact to its parent artifact.
3. If the authority is external, store an immutable snapshot, digest, or version-pinned reference in the repository when policy permits. Write the relevant commit SHA back only when that external action is authorized and the system supports it; otherwise register the pending backlink locally for an authorized owner.
4. If the repository is authoritative, external tools contain links or read-only mirrors rather than independently edited copies.
5. Reconcile conflicting copies before implementation or release; do not choose the more convenient version silently or expand a local coding task into an unauthorized external write.

Use `assets/project-template/docs/governance/ARTIFACT_LINEAGE.md` as the registry.

## 6. Change-size discipline

A good change:

- Has one business purpose.
- Can be reviewed without reconstructing unrelated history.
- Has a measurable acceptance condition.
- Leaves the repository runnable.
- Can be reverted or forward-fixed.

Split changes when they mix schema migration, framework upgrade, new feature, broad refactor, and deployment changes.

## 7. Comprehension control

Guard against comprehension debt:

- Require architecture and data-flow explanations for R2–R3.
- Prefer named invariants over accumulated defensive branches.
- Reject abstractions without at least two real uses or a clear boundary value.
- Remove dead experiments and generated clutter.
- Maintain an explicit “why” through ADRs and code comments only where non-obvious.
- Schedule periodic architecture and documentation garbage collection.


## 8. Controlled parallelism

After specification and dependency analysis, delegate independent work only when task contracts and write isolation are explicit. Prefer read-only fan-out. Use separate worktrees for concurrent writers and a single coordinator for integration. Read `parallel-execution.md`.
