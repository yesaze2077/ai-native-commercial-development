# Lifecycle handoffs and implementation readiness

Use for new products, material features or an affected handoff that has become uncertain. Read-only reviews still produce findings only. Keep the record in the authoritative issue/spec/plan; a clear narrow fix needs no new lifecycle dossier. Reuse accepted decisions that still cover this change.

## Choose the actual product mechanism

After requirements confirmation, settle material decisions about how the product creates the intended outcome: core user path, what is automatic versus reviewed, ownership/permissions, completion/failure behavior and the meaningful alternatives or tradeoffs. Name the chosen mechanism and why it fits the accepted constraints. A spec already settling these choices supplies this handoff; a separate solution document is optional. Do not let an implementation or page layout silently decide an unresolved product mechanism.

The user or authorized product/design owner chooses material product and experience commitments, or explicitly delegates them within named constraints. Routine reversible details may be resolved under existing authorization. Record the actual decision/delegation and version, without inventing a meeting or approval. A single explicit instruction may settle several named handoffs. Independent engineering review handles ordinary technical choices within accepted scope; changes to business promises, cost/access authority or recovery obligations go back to the relevant owner.

## Gate dependent work proportionately

For new/material implementation, use a compact row per affected handoff:

| Handoff | Minimum basis for dependent work |
|---|---|
| Requirements | Accepted users/problem/outcome, scope and rules, constraints and testable acceptance. |
| Product solution | Material mechanism/path/tradeoffs chosen or explicitly delegated; unresolved outcome-affecting decisions block their dependent work. |
| Interaction and visual | Critical journeys and states, representative key-screen/flow baseline and needed visual tokens selected by the responsible owner or scoped delegate. No-UI work records a real N/A basis. |
| Technical | Affected API/data/role/failure/recovery contracts are coherent, reviewed and aligned with the same accepted product/design version; probe evidence where needed. |
| Implementation | Focused slices preserve the accepted contracts; combined-state integration and meaningful negative/critical-journey checks support delivered behavior. |
| Business/experience acceptance | Responsible owner, accepted method or explicit delegation, covered requirements, candidate revision, actual observations/conclusion and unresolved differences. Engineering verification and code review are separate evidence. |
| Release readiness/authorization | Required pre-deployment fresh checks, applicable business acceptance, authorization for the exact candidate/scope and recovery/monitoring/operating readiness. |
| Deployment verification | After authorized deployment, its actual receipt and fresh target-environment critical smoke; until then report planned/authorized/deploying rather than completed launch. |
| Operations | Where ongoing support/monitoring applies, a named owner acknowledges handoff and has required diagnostic/recovery capability, window/next check, escalation and evidence. |

Record `handoff → ready / reused / not_applicable / blocked → baseline/version + evidence/decision → responsible owner/delegation → material gaps`. These are handoff states, separate from check-result statuses. Reuse requires an applicability explanation against the actual change, not just an old checkbox. N/A cites scope or policy; withdrawing an accepted requirement needs its scope-change decision. Low risk, a one-line diff, existing stack or existing component alone does not exempt a changed journey, API contract, permission rule or substantial visual redesign.

Block only dependent work. Read-only investigation and explicitly authorized bounded prototypes/probes may resolve uncertainty; they do not become approved production scope. Product, design and technical work may iterate or run concurrently after shared boundaries are frozen. If feasibility forces a different workflow, permission rule, cost or visual contract, reopen the affected owner decision before implementing that difference. Unchanged independent slices continue.

For a clear small change, the accepted issue/request, existing design/architecture and targeted checks can supply the whole applicable path. Do not generate a PRD, new design system, stage table or extra approval round solely to populate templates. Preserve the project-required review and release controls.

## Separate completion and acceptance

Engineering completion establishes what was implemented and actually verified, including integration and rendered behavior where relevant. Independent code review challenges correctness/security/regression. Business/experience acceptance establishes whether the accepted user outcome and experience are met through the method approved by the responsible owner. Release authorization decides whether this exact candidate may go to its target environment. None automatically impersonates another.

Use an owner walkthrough, review of version-bound artifacts, or explicitly approved delegated/automated acceptance appropriate to the requirement. A delegate reports the actual method, covered scope and observations under its authority; it cannot silently approve itself. Real-user research is not universally required. Material unresolved differences retain a pending/failed conclusion; a limited authorized pilot is not full commercial acceptance. Reuse earlier acceptance only for unchanged covered commitments, while the current candidate still meets mandatory verification.

## Close release and operations at the verified stage

Keep planned release, authorized deployment, target-environment smoke and operational observation distinct. Fresh machine checks cannot use a historical result-cache hit to satisfy a required fresh run. Non-executable unchanged design/approval records may retain valid reuse. A local unit test cannot stand in for a deployed critical journey solely because both name the same source SHA.

Pre-deployment authorization needs the applicable pre-deployment commitments; the future deployment receipt and target smoke close the later verification stage after that authorized action. Do not create a circular prerequisite requiring a future smoke result before deployment itself, and do not treat planned evidence as completed launch. Preserve required prechecks and bounded rollout/abort controls. Express the actual phase in the check set and validate deployed evidence again after execution; a consistency pass never supplies deployment permission.

Before a release needing ongoing support/monitoring, confirm the operational owner is aware and has the appropriate least-privilege access or authorized recovery route, monitoring/observation window and next check, escalation and runbook/rollback responsibilities. A solo owner can acknowledge their own responsibility; do not invent a team. A static/no-operations delivery may record an evidence-backed N/A. Naming an unaware person is not takeover. Missing handoff blocks that promised completion/affected launch, while independent local preparation can continue.

Use the existing acceptance and release records. The optional v2 delivery checker adds consistency constraints for N/A/scope decisions, fresh checks, business acceptance, deployment smoke and operations evidence. It never observes reality, chooses all applicable checks, proves a person's identity, or grants authority. Read its explicit limitations and keep project CI, independent review and actual authorized verification.
