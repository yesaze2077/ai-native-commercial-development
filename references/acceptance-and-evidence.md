# Application Acceptance and Delivery Evidence

## When to use

Use for application-level acceptance, release preparation or an audit of delivered behavior. A narrow copy change keeps its existing quick path. Reuse the project's issues, tests, CI and release records; this guide does not require a new reporting system.

## Connect commitments to observed behavior

For each material requirement, retain its stable ID and link the accepted journey or non-UI contract, relevant screen/state or API/data/permission decision, delivery task, behavior check and evidence revision. Include negative, empty, permission and recovery paths where relevant. Traceability must survive a requirement change, deletion or rename; inspect the previous accepted behavior and reopen genuine gaps even when tasks were checked off.

Choose proof at the actual boundary: a UI action reaching the intended API, correct persistence and retrieval, appropriate role enforcement and the visible result. File existence, mocked agreement, a rendered placeholder or an isolated HTTP 200 does not establish the whole outcome. Verify the combined state, not just separate frontend/backend passes. Use synthetic data and isolated test identities; do not access real customer data for convenience.

For experience and visual commitments, compare the rendered implementation with the versioned key-screen/flow contract at relevant viewport sizes and states. Record actual screenshots or walkthrough observations when available. Distinguish automated accessibility checks from keyboard/use-flow inspection and visual judgment. If a browser, design tool or reviewer is unavailable, preserve that limitation; do not invent screenshots, approval or usability research.

## Keep evidence honest

Use explicit `passed`, `failed`, `not_run` and `not_applicable` statuses. Inapplicability requires a real scope/policy reason; it cannot hide an unimplemented requirement. A passed result identifies the command or action, revision, environment, input, observed result and artifact. Reuse historical results only under the unchanged-coverage criteria in SKILL.md. Deployment smoke results must belong to the actual deployed revision and environment, not be copied from a prior deployment.

Independent review records the reviewed revision, reviewer context, spec/design/architecture references, findings and resolution. A receipt or digest preserves consistency; it cannot authenticate reviewer independence. Keep local implementation completion, release prerequisites, actual deployment and post-release observations distinct.

## Engineering, business acceptance and release authority

Record these as separate conclusions in the existing issue/release record. Engineering verification and independent code review show what was implemented and checked. Business/experience acceptance names the responsible owner, approved acceptance method or explicit delegate authority, covered requirements and baseline, candidate revision, actual observations, conclusion and remaining differences. A user walkthrough, review of version-bound artifacts or an explicitly approved automated/delegated method can be appropriate; real-user research is not mandatory for every task. An agent's self-test or CI green cannot silently stand in for the owner's acceptance. Release authorization binds the permitted candidate, environment and scope; one clear instruction may cover several named decisions without repeated permission requests.

Apply [lifecycle-handoffs.md](lifecycle-handoffs.md). Material gaps remain pending/failed for their dependent stage. Reuse existing approved acceptance for unchanged commitments only; verify the affected behavior and preserve required fresh release/target-environment checks. Waiving an inapplicable policy is distinct from removing an accepted requirement, which needs its scope-change decision and trace.

## Incremental execution handoff

Use [incremental-verification.md](incremental-verification.md) when choosing or reusing checks. Carry selected/executed/reused status, source fingerprint, original run and remaining gates into delivery evidence. A quick or integration subset does not establish full requirement coverage. Deployment smoke remains specific to the real deployed revision and environment and is never satisfied from the local result cache.

## Optional deterministic consistency check

`scripts/validate_delivery_evidence.py` validates an explicit local manifest. For new LIFE-001 evidence records, copy/adapt `assets/delivery-evidence.v2.example.json` only when useful and use `--require-v2`; placeholders intentionally cannot pass. Schema 1 and `assets/delivery-evidence.example.json` remain legacy consistency, not evidence that the new handoff constraints were checked. V2 requirements, fresh execution, scoped business acceptance and operational handoff are described below. Neither version selects all project obligations or proves actual execution/authority.

```bash
python <skill-dir>/scripts/validate_delivery_evidence.py delivery-evidence.json \
  --root <artifact-root> --revision <expected-git-sha> --stage local --require-v2
```

Use `--stage release` or `--stage observation` only for those stages. The checker reads local files; it never executes manifest commands, accesses the deployment URL or grants authority. It rejects unknown statuses, uncovered requirements, stale revision bindings, missing/tampered artifacts and required unrun/failed checks. A release URL alone is insufficient.

V2 keeps in-scope requirement coverage distinct from evidence-backed scope removal/policy N/A. Checks declare `fresh_required`; passed execution records origin, run revision and run ID/time. A required fresh run must be executed for the candidate; valid non-executable historical records may be reused with their basis. Deployed smoke must be `deployment_smoke`, executed for the current candidate and bound to the release environment/deployment ID. Release additionally separates `business_acceptance` and `operations_handoff`: accepted business scope identifies covered requirement IDs, responsible owner and owner/delegated method plus evidence; delegated acceptance includes its authority. Necessary operations need accepted ownership, access confirmation, observation/next-check and escalation evidence, or a justified scope/policy N/A. These fields are inspectable claims, not authentication or live observation.

A successful result means evidence is internally consistent. It does **not** prove that a command ran, all applicable policies were selected, N/A/reuse is justified, a person approved, a reviewer was independent, the real environment matches, or the product is commercially ready. Apply the risk matrix, project CI, review, security and release controls separately. Never use the helper to replace them.

## Validate the workflow itself

For a material skill change, retain response/trigger evaluations but also test actual repository work in isolated contexts: a new vertical slice, an existing-system change and failure/recovery. Bind artifacts to exact code and record commands, final outcomes, errors, rework and available duration/cost. Synthetic local repositories are execution evidence, not market demand or production evidence. Use equivalent tasks/configuration for version comparisons; do not infer improvement from response wording or incompatible task sets.

Mechanism references: [Spec Kit convergence](https://github.com/github/spec-kit/blob/979b0a3c1277283371c9901ad0eed04b64a99997/templates/commands/converge.md), [GSD verifier](https://github.com/open-gsd/gsd-core/blob/4226711512fb4035fcbb7d17ae64ac5419d8396a/agents/gsd-verifier.md), [Compound shipping receipts](https://github.com/EveryInc/compound-engineering-plugin/blob/3cdf53d5a8625c97b0cdd5f5aa102213d86c3a52/skills/ce-work/references/shipping-workflow.md). These supply candidate mechanisms, not commercial assurance.
