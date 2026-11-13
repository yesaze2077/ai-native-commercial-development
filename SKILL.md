---
name: ai-native-commercial-development
description: Guide commercial and real-user software from product and requirements decisions through interaction/UI/visual design, frontend/backend architecture and stack, implementation management, acceptance, launch and operating feedback. Use for a new commercial application or changes, audits and releases within that lifecycle. Also use for AI-agent/tool security, requirement-to-Git traceability, and practice-radar, evaluation or improvement of software-development governance. Apply only affected stages, reuse accepted artifacts and enforce risk-based evidence. Exclude stand-alone business advice, unrelated design tasks and disposable demos unless a commercial delivery workflow is requested.
---

# AI-Native Commercial Development

Carry the user’s product intent through a verifiable commercial delivery lifecycle. Deliver the requested user value with the smallest sufficient process and truthful evidence. Optimize time to an accepted, verified change, including rework and owner attention. More generated code or more agents alone does not prove faster delivery.

## Start with the task

1. Identify the outcome and action boundary: planning, read-only review, local implementation, release, incident, bootstrap, practice research or skill evolution. Follow current authorization and project instructions. Ask only for missing decisions that materially affect correctness, scope or risk; continue independent authorized work.
2. Read applicable `AGENTS.md`, branch/working-tree state, the relevant accepted request/specification, and directly affected code/checks. Search before broad reading. Expand to architecture, dependencies, CI, deployment or history only when affected or uncertain. Preserve existing edits; do not reset them for a clean workspace.
3. Assign R0–R3 below. For R1–R3, read [risk-classification.md](references/risk-classification.md); also read it when R0 consequences are uncertain. Risk depends on environment, privilege and reversibility, not task size alone.
4. Identify the smallest independently verifiable slice. For R1–R3, record acceptance criteria and a verification plan before coding. Reuse an issue, approved spec or authoritative request already containing them; fill gaps in place instead of duplicating documents.
5. Select the lifecycle entry point below, then execute the short loop. On continuation, inspect changes and evidence validity instead of repeating orientation. Load only references needed for this task.

## Requirements readiness

For a new product, a materially new feature or an ambiguous change, establish an accepted requirements baseline before solution design, interaction/UI design, stack selection or product implementation. Start by reusing authoritative context, separating facts from assumptions and identifying missing decisions that could change the user outcome, scope, business rules, permissions/data handling or acceptance. A brief background starts clarification; it does not establish accepted scope. Ask the smallest useful set of questions first and explain which decision each answer affects.

Return a concise requirements confirmation draft covering the target users/problem, intended outcome and success criteria, core journey and business rules, scope/non-goals/priorities, material constraints/dependencies and testable acceptance. Identify remaining critical decisions and their owners. Keep this in the existing authoritative brief or issue when available. Do not invent interviews, user confirmation or business rules.

Unresolved material decisions block dependent design and implementation. Relevant read-only investigation and explicitly authorized, bounded concept/feasibility probes may continue to resolve those decisions; label their assumptions and disposable boundaries. Do not treat those probes as accepted product scope or production implementation.

Proceed when the user confirms the requirements baseline, or existing approved requirements already cover the change and the current action is authorized. Reuse accepted decisions and clarify only affected gaps. Clear bug fixes, copy/style edits and other narrow changes keep their proportionate short path.

| Risk | Typical work | Development path |
|---|---|---|
| R0 | Small nonfunctional text, styling or documentation changes | Focused diff and quick/visual check; no separate spec, plan or new test suite by default. |
| R1 | Ordinary feature, CRUD, search or display | Written acceptance and verification plan, affected checks, branch/PR and independent review before release. A short existing issue can be the spec. |
| R2 | Auth, personal data, payments, uploads, notifications, AI tools, core journeys or significant migration | Full applicable spec and execution plan; security, negative-path, critical-journey and operational evidence under the risk matrix. |
| R3 | Security foundations, destructive production, financial correctness or broad privileged autonomy | R2 controls, explicit recorded human decision and appropriate independent/specialist review; no unattended release. |

Never downgrade a sensitive change to obtain the short path. Reviewing a high-risk system remains read-only unless implementation is authorized.

## Route the product lifecycle

For a new commercial product, connect the applicable stages in order. For an existing product, enter at the changed boundary and reuse accepted upstream decisions; bug fixes and narrow R0/R1 work keep their short path. Planning or audit produces its requested artifact only. Do not turn a request for research, design or a prototype into implementation or publication authorization.

| Stage | Read when applicable | Handoff and exit evidence |
|---|---|---|
| Problem and product decision | [product-discovery.md](references/product-discovery.md) for a new direction or material uncertainty | Users, observed problem, alternatives, facts/assumptions, value model, smallest scope and continue/change/stop criteria. Unvalidated demand stays an assumption. |
| Requirements | Existing spec plus [operating-model.md](references/operating-model.md) for material work | Journeys, domain terms, business rules, permissions and testable acceptance tied to stable requirement IDs. |
| Product solution | [lifecycle-handoffs.md](references/lifecycle-handoffs.md) when a mechanism or material tradeoff remains undecided | Selected mechanism, core path, alternatives/constraints and the user's or authorized owner's choice. Reuse an approved spec that already settles them. |
| Interaction and visual design | [experience-design.md](references/experience-design.md) for a new or materially changed interface | Flows, information architecture, relevant states, key-screen prototype, visual tokens and versioned implementation comparison. Reuse approved brand/components. |
| Architecture and stack | [architecture-and-stack.md](references/architecture-and-stack.md) for a new app or changed technical boundary | Justified stack, system/data/API/authorization contracts, environment and cost constraints, plus a runnable vertical probe where uncertainty warrants it. |
| Implementation readiness | [lifecycle-handoffs.md](references/lifecycle-handoffs.md) before new/material feature implementation | Applicable product, experience and technical baselines are ready or validly reused; N/A has a scope/policy basis. Material blockers stop dependent work. |
| Delivery management | Short loop and existing ExecPlan; parallel reference only if needed | Vertical slices with dependencies, explicit input/output/acceptance, isolated changes, runnable checkpoints and recoverable progress. |
| Acceptance | [acceptance-and-evidence.md](references/acceptance-and-evidence.md) for application-level verification or release | Engineering verification, independent review and business/experience acceptance are distinct. Record the responsible owner, method/delegation, scope, revision, conclusion and gaps. |
| Commercial launch and learning | [commercial-launch-feedback.md](references/commercial-launch-feedback.md) when preparing launch or reviewing operation | Deployment/version/environment receipt, real smoke checks, applicable business readiness, operational and product observations, owner and next product decision. |
| Operations handoff | [lifecycle-handoffs.md](references/lifecycle-handoffs.md) when continuing support/monitoring is needed | Before the affected launch, owner acknowledges takeover, required diagnostic/recovery access, observation window/next check and escalation. Pending handoff remains pending. |

Reuse existing project artifacts; filenames are examples, not required duplicates. Link experience, architecture, acceptance and observations into the existing lineage registry. A stage is complete when its commitments are supported, not when a template is filled or a task box checked. Reconcile changed requirements with affected design, contracts, tests and release evidence; reopen material gaps, preserving accepted history.

For new products and material features, record applicable handoffs in the existing issue/spec as ready, reused with its version and applicability, not applicable with a real scope/policy basis, or blocked. Requirement confirmation starts the next applicable decisions; it does not complete product, experience or technical design. Material product/interaction/visual choices need the user or an explicitly authorized responsible owner to choose the baseline or delegate the decision. Listing a critical open question cannot close its dependent stage. Stage applicability follows the actual workflow/interface/contract changes independently of risk labels: a major visual redesign still needs its design baseline even with low data/security risk.

Use [lifecycle-handoffs.md](references/lifecycle-handoffs.md) for these transitions. Design and technical work may iterate or run in parallel once their shared boundaries are stable. Preserve small-change paths, existing approved designs, scoped delegations and independent work. One explicit approval may cover several clearly named commitments at the same baseline; do not repeatedly ask permission for unchanged authorized scope. Code review/CI success does not supply business acceptance or release authorization.

Use available specialized design, product or engineering skills when they fit the task. Inspect their actual availability and tool/permission requirements before routing. If absent, use these self-contained guides and local artifacts; never invent a tool call, design file or review. One coordinator owns the shared requirements and handoffs. Specialist outputs cannot override current user choices, project stack or authorization. Do not create a fixed agent team or ask for approval again at every stage of already-authorized work.

## Short development loop

### Orient and implement

- Reuse accepted decisions and current docs. Create/update a compact repository or data-flow map only when the boundary is unknown or changing. Capture intent for material new directions or ambiguous cross-system changes using [operating-model.md](references/operating-model.md).
- Keep one authoritative system for each artifact. External authority needs its stable record ID and an immutable snapshot, digest or version-pinned reference where permitted. Write commit-SHA backlinks only when authorized; otherwise record a pending backlink locally. Reconcile conflicts rather than maintaining two editable truths.
- R1–R3 use a branch and PR before merge/release. Use a worktree when another task is active or isolation requires it; a single writer on a suitable branch needs no extra worktree. Prepare local review material when remote actions are outside scope.
- Establish the affected baseline through a targeted check or valid reusable evidence. For bugs and deterministic business rules, reproduce the failure, make the smallest fix and verify regression coverage. Add tests protecting behavior, not tests mirroring wording or implementation.
- Preserve interfaces, permissions and data invariants. Add timeouts, retries, idempotency, errors and observability where the boundary needs them. Justify dependencies; avoid speculative infrastructure and unrelated refactors. Update existing artifacts. Use an ExecPlan for complex, long-running or R2–R3 work, not every narrow change.
- Batch independent searches and read-only checks. Delegate only when permitted and worthwhile; use the smallest useful team. Before concurrent agents/writers, read [parallel-execution.md](references/parallel-execution.md), freeze contracts, isolate write sets/worktrees and assign one integration owner. Shared-state changes and integration remain sequential.

### Verify and stop repeating

When repeat verification is costly, read [incremental-verification.md](references/incremental-verification.md). Prefer the project's existing affected/cache tooling. Otherwise use a reviewed change-to-component-to-check map and the optional bundled planner: quick feedback during edits, affected integration after a coherent batch, and all required release checks freshly on the exact candidate. Compare the whole change since the appropriate validated baseline; never move an integration baseline merely because quick checks passed. Unknown/global/lock/profile changes widen verification and disable result reuse. A plan, selected-check pass or cache hit is not complete acceptance.

For routine R0 work, the table above and known project checks suffice. Otherwise use [commercial-quality-gates.md](references/commercial-quality-gates.md) and the risk matrix to select applicable checks. Run the narrowest useful check first, then required regression, build, type, security and critical-journey gates. UI changes need relevant rendered/visual validation. Missing tools or credentials are verification limits, not passes.

Reuse an actual passing result only when its covered sources and transitive dependencies, inputs, configuration, environment and tool versions remain relevant and unchanged. Record the original run and why it applies; never present reused evidence as a new run. If unsure, rerun. A lockfile, runtime, shared-contract, migration or relevant configuration change invalidates affected evidence.

Verify the combined state after integration; isolated worker passes do not establish interaction correctness. Reuse only unaffected evidence. Required CI/protected checks still run on the exact revision under project policy. After applicable checks pass, stop repeating them unless new changes, failures or unresolved concerns justify another run. Never weaken a check to save time.

### Review and report the actual stage

Before R1–R3 release, obtain an independent fresh review of the spec, diff and evidence. Follow project review policy, resolve Blocker/High findings and record accepted Medium risk. Prioritize correctness, security, regressions and failure paths; avoid duplicating trustworthy automated checks or cycling on stylistic Nits.

Report local implementation, verification, review and deployment separately. Local work can be complete while review or release remains pending. A missing production approval blocks production action, not independent reversible preparation. A gap affecting design, authorization or safe verification still blocks its dependent work.

Use **SHIP / CONDITIONAL / NO-SHIP** only for release recommendations; these are not deployment authorization. Use **BLOCKED** for a requested step that cannot proceed, identifying the dependency. For small tasks, state result, actual verification and material limitation briefly. For substantial work add risk, artifacts and the next required action. Do not generate a release package or fixed multi-field status for a task ending at local development.

## Load details when applicable

| Situation | Reference |
|---|---|
| Complex specification, intent, artifact authority | [operating-model.md](references/operating-model.md) |
| Checks, independent review, readiness | [commercial-quality-gates.md](references/commercial-quality-gates.md) |
| Auth, sensitive data, payment, uploads, external content, AI/agent tools | [security-and-ai-safety.md](references/security-and-ai-safety.md) |
| Release, migration, monitoring, rollback, restore, incident | [observability-release-operations.md](references/observability-release-operations.md) |
| Multiple agents, worktrees, parallel CI | [parallel-execution.md](references/parallel-execution.md) |
| External practice research | [practice-radar.md](references/practice-radar.md) |
| Skill/governance changes | [self-evolution-protocol.md](references/self-evolution-protocol.md) |
| Requested standards/assurance baseline | [standards-map.md](references/standards-map.md) |

Do not load all references by default. Mark irrelevant domains, such as migration when no data changes, as inapplicable with a reason; do not invent work. Explicit project requirements still apply.

## Bootstrap boundary

Enter Bootstrap mode or the user explicitly authorizes scaffolding changes before generating governance files. First run `python <skill-dir>/scripts/bootstrap_governance.py --target <repo-root> --dry-run`; inspect paths/conflicts before authorized writes. For review, audit, diagnosis, or planning, do not write scaffolding without authorization. Missing template filenames alone do not justify stopping development or creating a duplicate governance system.

## Release controls

Before release, read the quality and operations references above. Record user impact, exact revision/configuration/schema, risk, checks, applicable migration/backup evidence, rollout, monitoring, recovery, limitations and the human ship/block decision. Keep development, validation and production separate. Protect secrets and private data; use least privilege and deterministic authorization/output validation for AI actions. Instructions are advisory; mandatory policies need enforceable controls and evidence.

Return **NO-SHIP** for failed required checks, unresolved critical/high vulnerabilities, unproven authorization/tenant isolation, unsafe data changes or missing recovery evidence, no viable rollback/forward-fix, undetectable critical failure, unbounded AI actions, unexplained unrelated changes, fabricated/contradictory evidence, or high-risk acceptance ambiguity. R3 requires explicit human approval and appropriate specialist review. Never perform an unreviewed production database mutation from an interactive session. The owner must understand critical data flow, permissions, failure modes and recovery. Production mutation, deployment and automatic rollback remain disabled unless separately authorized under required controls.

Apply stop conditions at the affected step; never label local completion a released commercial product.

## Skill evolution

Read [self-evolution-protocol.md](references/self-evolution-protocol.md), plus the practice reference for external ideas. Prefer a targeted test, tool, template or project fix over universal rules. External practices start as sourced candidates; verify current primary sources before adoption.

Semantic changes require contemporaneous real-agent responses, `scripts/run_behavior_evals.py` replay, independent rubric review bound to raw-response digests, and comparison with an accepted compatible baseline when available. Preserve pre-change checks. For expanded suites, compare the compatible subset separately and label new coverage honestly; do not compare incompatible rates.

Prepare a reversible versioned governance change with prediction, evidence, limitations and rollback. Explicit human approval is required for core instructions, risk, quality/security/approval policy, production/migration rules and CI enforcement. Do not auto-merge. Retain required protected hosted approval or an externally controlled signature; local hashes prove consistency, not reviewer identity. Local preparation/installation does not establish hosted promotion.

During actual use, apply the event-driven [usage-feedback-loop.md](references/usage-feedback-loop.md): capture material boundary problems, feature feedback and corrections in a separate local ledger, assess whether a project fix or reusable rule change is warranted, and present a concrete proposal only when evidence warrants it. Reuse pending decisions; do not repeat rejected/deferred advice without new evidence. User confirmation of the specific proposal is required before updating active skill rules. This request to build the mechanism does not preapprove future proposals. Continue already-authorized product work independently of optional rule improvements.

Do not add schedulers or background learning unless requested. This loop runs only while the skill is invoked; it cannot monitor other chats or future activity in the background. Routine success needs no report. Measure lead time, rework, defects, cost and owner intervention when data exists. Fewer words alone do not prove productivity gain.

## Deterministic tools

Run from the skill directory. Use project commands for application checks.

- Bootstrap project governance (authorized work only; dry-run first): `python scripts/bootstrap_governance.py --target <repo-root> --dry-run`
- Skill validation: `python scripts/validate_skill.py <skill-root>`
- Manifest validation: `python scripts/run_behavior_evals.py --validate-only`
- Behavior replay: `python scripts/run_behavior_evals.py --responses-dir <responses> --semantic-review <review.json> --require-semantic-review --report <report.json>`
- Incremental verification plan (read-only by default): `python scripts/incremental_verify.py --root <repo> --profile <map.json> --base <validated-ref> --stage quick`; add `--execute` only for authorized checks, and use `--stage release` for fresh full declared verification.
- Delivery-evidence consistency: `python scripts/validate_delivery_evidence.py <manifest.json> --root <artifact-root> --revision <expected-git-sha> --stage local --require-v2` (or `release` / `observation`); see [acceptance-and-evidence.md](references/acceptance-and-evidence.md). Schema 1 remains legacy consistency only. Neither version executes checks, authenticates approval or authorizes release.
- Practice scoring: `python scripts/score_practice_candidate.py <candidate.json>`
- Usage-feedback assessment (read-only; explicit local state path): `python scripts/feedback_loop.py --store <feedback.json> assess`; recording and decision notes are described in [usage-feedback-loop.md](references/usage-feedback-loop.md). The tool never applies rule changes or authenticates approval.

Distinguish static validation, replay, scenario responses and actual application execution in every evidence claim.
