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

## Optional deterministic consistency check

`scripts/validate_delivery_evidence.py` validates an explicit local manifest. Copy/adapt `assets/delivery-evidence.example.json` only when useful; its placeholders are intentionally not passing evidence. The schema links requirements to check IDs; checks carry applicability, status, current revision and digest-bound local artifacts. A historical run needs an explicit reuse reason. Release adds review/approval receipts; deployed status adds a deployment identifier and fresh passed smoke checks. Observation additionally records expected/actual outcomes, window, owner, evidence and product decision.

```bash
python <skill-dir>/scripts/validate_delivery_evidence.py delivery-evidence.json \
  --root <artifact-root> --revision <expected-git-sha> --stage local
```

Use `--stage release` or `--stage observation` only for those stages. The checker reads local files; it never executes manifest commands, accesses the deployment URL or grants authority. It rejects unknown statuses, uncovered requirements, stale revision bindings, missing/tampered artifacts and required unrun/failed checks. A release URL alone is insufficient.

A successful result means evidence is internally consistent. It does **not** prove that a command ran, all applicable policies were selected, N/A/reuse is justified, a person approved, a reviewer was independent, the real environment matches, or the product is commercially ready. Apply the risk matrix, project CI, review, security and release controls separately. Never use the helper to replace them.

## Validate the workflow itself

For a material skill change, retain response/trigger evaluations but also test actual repository work in isolated contexts: a new vertical slice, an existing-system change and failure/recovery. Bind artifacts to exact code and record commands, final outcomes, errors, rework and available duration/cost. Synthetic local repositories are execution evidence, not market demand or production evidence. Use equivalent tasks/configuration for version comparisons; do not infer improvement from response wording or incompatible task sets.

Mechanism references: [Spec Kit convergence](https://github.com/github/spec-kit/blob/979b0a3c1277283371c9901ad0eed04b64a99997/templates/commands/converge.md), [GSD verifier](https://github.com/open-gsd/gsd-core/blob/4226711512fb4035fcbb7d17ae64ac5419d8396a/agents/gsd-verifier.md), [Compound shipping receipts](https://github.com/EveryInc/compound-engineering-plugin/blob/3cdf53d5a8625c97b0cdd5f5aa102213d86c3a52/skills/ce-work/references/shipping-workflow.md). These supply candidate mechanisms, not commercial assurance.
