# Commercial Launch and Product Feedback

## Mode and applicable inputs

Use for commercial readiness, an authorized release, or post-release product evaluation. Read [commercial-quality-gates.md](commercial-quality-gates.md) and [observability-release-operations.md](observability-release-operations.md) first; their checks, human ship decision, production authorization, monitoring and recovery controls remain authoritative. A readiness review produces a recommendation and gaps. It does not deploy. For an increment, review only changed business promises and affected operational dependencies, plus mandatory release controls.

## Working method

1. **Check the promise users will encounter.** Trace the advertised outcome through onboarding, the critical journey, completion and support/recovery. Compare actual capability with product copy, plan/role entitlements and any limits. Apply the following commercial checks only when the business model or change triggers them; a free internal tool does not need a billing system.

| Trigger | Evidence needed before the affected launch |
|---|---|
| Payment, subscription or trial | Price/terms and entitlement behavior agree; payment failure, cancellation/refund and reconciliation paths have appropriate verified coverage. Use authorized test mode; live financial actions need their existing authorization. |
| Plans, metering or costly resources | Defined unit and quota, usage visibility, limit behavior, abuse/cost guardrails and owner. Unknown provider/model costs remain estimates. |
| Users need help or manual intervention | Discoverable help/contact path, support owner, handoff/escalation and usable diagnostic information without exposing private data. |
| New onboarding or changed workflow | Entry instructions, necessary help and recovery guidance match the released behavior. |
| A product-outcome claim will be evaluated | Event/metric contract, permitted collection, baseline and validation of critical instrumentation. |

2. **Define measurement before rollout.** For each primary outcome and guardrail, record population/exposure, numerator/denominator, event timing, identity/deduplication, source, baseline, expected value/range, observation window and owner. Include activation/completion, repeated use, revenue/value or service outcomes only as relevant. Add reliability, support burden and cost guardrails. Separate targets, estimates and observed results. Missing joins, consent constraints or incomplete telemetry limit interpretation; they are not zero outcomes.
3. **Bind release evidence to the real environment.** Record exact revision/build artifact, target environment, relevant configuration/feature flags, schema and dependency versions, approvals, rollout/abort conditions and recovery target. After an authorized deployment, preserve its actual receipt: deployment/job ID, timestamp, artifact/version and environment, result and health evidence. A prepared command or CI build is not a deployment receipt.
4. **Run a real smoke journey.** Verify the deployed version at its target entry point with an appropriate scoped account, critical action, persisted/result state and relevant permission/failure behavior. Use authorized test data and account for side effects. If a real action is outside scope or credentials are missing, mark that check pending and complete independent checks. A reachable URL, open page or merged PR alone does not establish a working released product.
5. **Observe within owned windows.** Keep the existing operational monitoring/abort window, then evaluate product outcomes over a window suitable for the behavior, such as a full activation or renewal cycle. Name who checks each window and when. Compare expected versus actual metrics, sample/exposure, errors, support signals, cost and manual intervention. State missing telemetry, seasonality, selection effects and concurrent changes; uncontrolled before/after differences do not establish causality.
6. **Return learning to a product decision.** Record continue, improve, change direction, stop or insufficient evidence, with the supporting observations and owner. Turn accepted findings into an existing intent/specification/backlog item, linked to release/version and evidence. Re-enter discovery for a failed value assumption, experience design for journey friction, architecture for a demonstrated technical constraint, or incident response for harm. Engineering retrospectives and governance improvements can accompany this decision; they do not replace it.

## Outputs and exit basis

Extend existing release evidence and the post-release note with commercial readiness, deployment receipt, actual smoke results, measurement windows and the resulting product decision. No extra launch dossier is required. Report local verification, review, deployment, operational observation and product evidence separately.

Close the requested release work only to its verified stage. If commercial outcomes need more time, state “deployed; product outcome pending,” with owner, evaluation date and evidence gap. Do not invent success or run an unrequested background monitor. A commercial feedback cycle closes when observed evidence supports a recorded product decision and accepted follow-up; a URL, PR or engineering retrospective cannot close that cycle by itself.

Mechanism source: [gstack land-and-deploy](https://github.com/garrytan/gstack/blob/b9bbc31c5c9b36ff4fe8e85493fd86491602b846/land-and-deploy/SKILL.md). Use receipt and real-environment verification ideas under this skill's existing authorization and recovery rules.
