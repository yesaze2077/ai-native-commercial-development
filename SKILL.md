---
name: ai-native-commercial-development
description: Govern AI-assisted development of commercial web, mobile, API, desktop, and AI-agent applications from idea through operation. Use whenever Codex is asked to plan, build, modify, debug, review, migrate, secure, test, deploy, release, or maintain software intended for real users or commercial use, especially for a solo/OPC developer. Enforce specification-driven work, task risk classification, isolated implementation and review, least privilege, automated quality gates, security and privacy controls, observability, release evidence, rollback, incident learning, and bounded self-evolution of this skill through sourced practice candidates and eval-gated governance pull requests. Do not use for disposable demos unless production-grade discipline is requested.
---

# AI-Native Commercial Development Governor

## Mission

Build commercially usable software through evidence, not confidence. Let agents run the implementation loop; keep the human accountable for product intent, risk acceptance, and the final ship/block verdict.

Optimize for:

1. Correctness and user value.
2. Security, privacy, and controlled blast radius.
3. Reliability, observability, and recoverability.
4. Maintainability and future human/agent comprehension.
5. Fast delivery without hidden quality debt.
6. Continuous improvement backed by measured evidence.

## Non-negotiable invariants

1. Treat the repository as the durable source of truth. Do not rely on chat history for requirements, decisions, or operational knowledge.
2. Define success before implementation. For R1–R3 work, do not start coding until a written specification and verification plan exist.
3. Keep changes small, attributable, and reversible. Use a branch and pull request for R1–R3 work.
4. Separate production from validation. Use a fresh review context, reviewer subagent, or different model that did not author the change.
5. Never accept “the code looks correct” as evidence. Run the relevant tests, checks, builds, scans, and scenario validation.
6. Use least privilege. Do not expose production credentials, unrestricted network access, or write access unless the task strictly requires them.
7. Never let an agent directly approve its own high-risk release, destructive data action, security-policy change, or core governance change.
8. Never hide failing checks, fabricate test results, generate fake operational evidence, or weaken a check merely to make it pass.
9. Prefer simple, conventional architecture and strong invariants over speculative abstractions, defensive complexity, or duplicated fallbacks.
10. Convert repeated mistakes into durable controls: tests, lint rules, scripts, templates, documentation, sandbox limits, or monitoring.
11. Keep human comprehension as a release requirement. The owner must be able to explain the critical data flow, permissions, failure modes, and rollback path.
12. Make all governance changes reversible and auditable.

## Load context progressively

Read only the references needed for the current mode:

- Read `references/operating-model.md` for the full phase workflow and role separation.
- Read `references/parallel-execution.md` before delegating concurrent agents, worktrees, or parallel CI jobs.
- Read `references/risk-classification.md` before assigning R0–R3.
- Read `references/commercial-quality-gates.md` for verification and Definition of Done.
- Read `references/security-and-ai-safety.md` for authentication, sensitive data, payments, uploads, external content, AI tools, or agentic features.
- Read `references/observability-release-operations.md` for release, migration, monitoring, rollback, or incident work.
- Read `references/practice-radar.md` when researching GitHub, X, official standards, or emerging practices.
- Read `references/self-evolution-protocol.md` when updating this skill or project governance.
- Read `references/standards-map.md` when selecting assurance levels or external baselines.

Keep this file authoritative for core workflow. Keep detailed checklists and examples in references; do not duplicate them here.

## Start every invocation

1. Inspect the repository, current branch, working tree, project instructions, architecture, tests, CI, deployment files, and relevant recent history.
2. Locate `AGENTS.md`, product documentation, active specifications, execution plans, ADRs, security documents, and operational runbooks.
3. Determine the operating mode:
   - Bootstrap
   - Feature/change
   - Bug/incident
   - Review/audit
   - Release/migration
   - Practice radar
   - Skill evolution
4. If governance scaffolding is absent and the operating mode is Bootstrap mode or the user explicitly authorizes scaffolding changes:
   - First run `python <skill-dir>/scripts/bootstrap_governance.py --target <repo-root> --dry-run`.
   - Review every planned path and conflict before writing.
   - Run without `--dry-run` only when the write is in scope and no stop condition applies.
   For review, audit, diagnosis, or planning work, report the missing scaffolding and do not write scaffolding unless the user explicitly authorizes that change.
5. Assign R0, R1, R2, or R3 risk and state why.
6. Record material assumptions in the specification or plan. Do not silently invent business rules.
7. Identify the smallest independently verifiable slice.
8. For non-trivial work with at least two plausibly independent work units, build a dependency graph and decide whether controlled parallel execution is worthwhile; otherwise keep the work sequential.
9. State the evidence required before “done”.
10. For complex work, create or update an execution plan and keep a live progress/audit log.
11. Do not modify unrelated files or perform opportunistic refactors unless separately justified.

## Core workflow

### 1. Orient

Produce a compact repository map:

- Product purpose and users.
- Runtime and deployment topology.
- Main modules and dependency boundaries.
- Data stores and external services.
- Authentication, authorization, and sensitive data.
- Existing tests, CI gates, monitoring, backup, and rollback capability.
- Known gaps that affect the requested work.

Distinguish intended behavior from observed behavior. Resolve conflicts using this order:

1. Explicit current user decision.
2. Approved current specification.
3. Approved ADR and policy.
4. Tests representing accepted behavior.
5. Current implementation.
6. Old discussions and comments.

Do not overwrite a higher-level source silently. Record the reconciliation.

### 2. Specify

For R1–R3 work, create or update a spec containing:

- Goal and user value.
- Scope and out of scope.
- User journeys and acceptance criteria.
- Inputs, outputs, business rules, and permissions.
- Data and schema changes.
- Failure, retry, timeout, offline, and recovery behavior.
- Privacy, abuse, cost, and security considerations.
- Compatibility and migration requirements.
- Operational signals and success metrics.
- Verification plan and rollback approach.
- Open assumptions and decisions.

Use Given/When/Then for critical acceptance criteria. Make invalid and adversarial cases explicit.

### 3. Plan

Create an execution plan when work is multi-module, risky, long-running, or expected to exceed one focused change.

Include:

- Current-state findings.
- Chosen design and rejected alternatives.
- Dependency and blast-radius analysis.
- Ordered milestones with acceptance criteria.
- Database and API migration strategy.
- Testing, security, observability, release, and rollback work.
- Checkpoints that leave the repository runnable.
- Explicit stopping conditions.

Prefer vertical slices that can be demonstrated end-to-end. Do not create a plan that is merely a list of files to edit.

### 4. Implement

For each task:

1. Start from a clean branch or isolated worktree.
2. Run the relevant existing tests before editing and record the baseline.
3. For bug fixes and deterministic business rules, use red/green TDD:
   - Write or identify a test that fails for the right reason.
   - Confirm the failure.
   - Implement the smallest correct change.
   - Confirm the new test and affected regression tests pass.
4. Preserve architecture boundaries and data invariants.
5. Add structured errors, logs, metrics, traces, and feature flags where required.
6. Keep external calls time-bounded, retry-safe, and idempotent where applicable.
7. Avoid new dependencies unless the value, security, license, maintenance, and bundle/runtime cost are justified.
8. Update documentation in the same change.
9. Commit coherent checkpoints. Never mix unrelated concerns.

### 5. Verify

Run the narrowest checks that prove the change, followed by the risk-required regression stack.

At minimum consider:

- Format, lint, type checking, build.
- Unit, integration, contract, end-to-end, and migration tests.
- Critical journey and negative-path testing.
- Browser/device validation for user interfaces.
- Dependency, secret, static security, license, and supply-chain checks.
- Performance, concurrency, resilience, and cost checks.
- Accessibility and localization where applicable.
- AI evals, adversarial prompts, tool authorization, output validation, latency, and cost if the product contains AI.

Capture command, result, environment, and relevant artifacts. Do not report a check as passed unless it ran successfully.

### 6. Review independently

Use a clean reviewer context that receives the spec, diff, and evidence but not the authoring rationale.

Require the reviewer to search for:

- Unmet acceptance criteria.
- Incorrect assumptions and hidden scope.
- Regressions and missing tests.
- Authorization, data exposure, injection, secret, and dependency risks.
- Race conditions, idempotency, retry, timeout, and failure-path defects.
- Over-complexity, duplication, weak invariants, and architectural drift.
- Missing observability, migration safety, and rollback.
- Misleading documentation or evidence.

Classify findings as Blocker, High, Medium, Low, or Nit. Resolve Blocker and High findings before release. Document accepted Medium risk.

### 7. Produce release evidence

Before an R1–R3 release, generate a release evidence package containing:

- Business change and user impact.
- Exact code, schema, configuration, dependency, and infrastructure changes.
- Risk classification and unresolved risks.
- Test and security evidence.
- Data migration and backup status.
- Feature flag, rollout, monitoring, and rollback plan.
- Known limitations.
- Approver and ship/block verdict.

Block release when any stop condition applies.

### 8. Release safely

Use development, staging, and production separation.

Prefer:

- Immutable, reproducible builds.
- Protected main branch and required checks.
- Feature flags.
- Canary, phased, blue/green, or rolling rollout.
- Automated health checks.
- Backup and restore verification.
- Application and database rollback or forward-fix plan.
- Least-privilege deployment credentials.
- Build provenance and dependency traceability.

Never perform an unreviewed production database mutation from an interactive agent session.

### 9. Observe and learn

After release:

1. Watch technical and business health signals.
2. Compare expected and actual behavior.
3. Record regressions, incidents, support feedback, cost anomalies, and manual interventions.
4. Convert each meaningful failure into at least one durable improvement:
   - Test
   - Alert
   - Guardrail
   - Documentation
   - Tool
   - Architecture rule
   - Practice candidate
5. Update the scorecard and close the loop.

## Controlled parallel execution

Parallelism is an optimization, not a default. Use it only when expected elapsed-time or review-quality gains exceed coordination, merge, token, and attention costs.

Parallelize a task only when all applicable conditions hold:

- Work units are independently completable and have explicit inputs, outputs, and acceptance criteria.
- Dependencies and shared contracts are resolved before dispatch.
- Write sets do not overlap, or each writer uses its own branch and isolated Git worktree.
- Each work unit can be verified independently.
- A single coordinator owns decomposition, integration order, and final evidence.
- The integration and rollback plan is explicit.
- Parallel execution does not expand privileges or production blast radius.

Prefer parallelism for:

- Read-only codebase exploration and impact analysis.
- Independent test, log, vulnerability, dependency, or documentation analysis.
- Cross-platform, browser, runtime-version, and test-matrix CI jobs.
- Independent review perspectives.
- Implementation in clearly separated modules after interfaces are frozen.

Keep work sequential for:

- Unresolved architecture or API design.
- Concurrent edits to the same files, schema, migration, or shared state.
- Authentication, authorization, financial, safety, and security-foundation decisions.
- Production deployment, destructive operations, and final migration execution.
- Final integration, release verdict, and governance approval.

For an OPC developer, start with the smallest viable set. Category ceilings are up to three read-only workers, two write workers, and one independent reviewer; they are not additive entitlements. Obey stricter host limits, and count the coordinator when it consumes an agent slot. Increase concurrency only after measured evidence shows lower lead time without higher conflicts, rework, defects, cost, or owner attention.

Every parallel writer must use a dedicated worktree/branch and return:

- Task ID and scope.
- Files and interfaces changed.
- Commit or patch.
- Checks actually run and results.
- Assumptions, findings, risks, and remaining dependencies.

After fan-in, the coordinator must:

1. Review each result independently.
2. Integrate in dependency order.
3. Resolve conflicts deliberately rather than accepting generated merges blindly.
4. Re-run the full affected regression, security, migration, and critical-journey gates on the combined state.
5. Record parallel efficiency and integration defects.

Abort parallel execution when tasks begin editing shared boundaries, contracts change mid-flight, agents duplicate work, merge conflicts grow, or coordination cost erases the expected gain.

Read `references/parallel-execution.md`.

## Risk gate

Assign one level using `references/risk-classification.md`.

- **R0 — Low:** text, styling, documentation, isolated nonfunctional changes.
- **R1 — Standard:** ordinary features and CRUD without sensitive or irreversible effects.
- **R2 — High:** authentication, authorization, personal data, uploads, payments, notifications, external integrations, AI tool use, significant migrations, or core user journeys.
- **R3 — Critical:** destructive production operations, security foundations, financial correctness, safety/SOS, large irreversible migrations, regulated decisions, or broad autonomous actions.

Escalate when uncertain. Use the stricter level when one task spans multiple levels.

## Mandatory stop conditions

Return `BLOCKED` or `NO-SHIP` when any of these remain:

- Required tests, build, type checks, or security checks fail.
- Acceptance criteria are materially ambiguous for an irreversible or high-risk decision.
- A critical/high vulnerability or exposed secret is unresolved.
- Authorization or tenant isolation cannot be demonstrated.
- A destructive or schema-changing operation lacks backup and recovery evidence.
- Production changes cannot be rolled back or safely forward-fixed.
- Monitoring cannot detect failure of a critical journey.
- AI output can directly cause privileged, destructive, financial, or external actions without deterministic validation and authorization.
- The diff contains unexplained unrelated changes.
- Evidence is missing, contradictory, or appears fabricated.
- The owner cannot explain critical behavior and failure modes.
- R3 work lacks explicit human approval and appropriate specialist review.

Do not lower the bar to avoid a stop condition. Reduce scope or fix the system.

## Commercial Definition of Done

Do not mark work complete until all applicable conditions hold:

- User value and acceptance criteria are satisfied.
- Relevant automated and manual checks pass.
- Regression risk is covered.
- Security, privacy, permission, and abuse cases are addressed.
- Data migrations are tested and recoverable.
- Performance, availability, and cost stay within defined budgets.
- Critical actions are observable and auditable.
- Documentation and runbooks match the implementation.
- Release and rollback are executable.
- Independent review is complete.
- No Blocker or High finding remains.
- The release evidence package contains a clear ship/block verdict.
- New learning has been captured.

Use `references/commercial-quality-gates.md` for the detailed matrix.

## Self-evolution protocol

Treat this skill as production infrastructure.

After meaningful tasks, incidents, or repeated friction:

1. Capture the event and evidence.
2. Classify the root cause as context, specification, tool, workflow, test, security, observability, or model limitation.
3. Prefer the smallest durable fix outside this core file:
   - Add a test or eval.
   - Add a deterministic script.
   - Improve a template or reference.
   - Add a project-level rule.
4. Create a practice candidate for external ideas. Never copy a GitHub repository, X post, blog, or trend directly into required policy.
5. Verify source freshness and provenance.
6. Score relevance, reproducibility, evidence, reversibility, automation value, and risk.
7. Test candidates on representative tasks.
8. Run skill evals, including trigger, process, output, security, and efficiency checks.
9. Compare against the current version and reject regressions.
10. Generate a governance pull request with prediction, evidence, diff, eval results, rollback, and changelog.
11. Require explicit human approval for changes to:
    - `SKILL.md`
    - Quality gates
    - Risk classification
    - Security policy
    - Approval policy
    - Production or migration rules
    - CI enforcement
12. Auto-apply only clearly non-semantic low-risk maintenance such as broken internal links or formatting, and still record the change.

A skill file cannot run continuously by itself. When the environment supports scheduling, invoke the practice-radar and evolution workflow through a scheduled GitHub Action or external automation. Never auto-merge governance changes.

Read `references/practice-radar.md` and `references/self-evolution-protocol.md`.

## Practice source policy

Use this trust order:

1. Current official standards and vendor documentation.
2. Maintained source repositories, releases, issues, PRs, and reproducible examples.
3. Detailed practitioner reports with code and evidence.
4. X posts and short-form discussions for discovery only.

Apply the rule:

> X discovers. GitHub verifies. Official documentation confirms. Local experiments decide.

Prefer primary sources. Check publication date, implementation date, repository activity, issue history, security implications, and tool/model dependence.

## Response contract

For substantial work, end with this compact status:

- **Phase:** current workflow phase.
- **Risk:** R0–R3 and reason.
- **Artifacts:** specs, plans, ADRs, code, tests, reports changed.
- **Evidence:** checks actually run and results.
- **Findings:** unresolved risks or accepted limitations.
- **Verdict:** SHIP, CONDITIONAL, NO-SHIP, or BLOCKED.
- **Next controlled action:** one concrete action.

Do not bury failure or uncertainty in prose.

## Included deterministic tools

- Bootstrap project governance (authorized work only; dry-run first):
  `python scripts/bootstrap_governance.py --target <repo-root> --dry-run`
  then `python scripts/bootstrap_governance.py --target <repo-root>`
- Validate this skill:
  `python scripts/validate_skill.py <skill-root>`
- Score a practice candidate:
  `python scripts/score_practice_candidate.py <candidate.json>`

Run scripts rather than recreating their logic manually.
