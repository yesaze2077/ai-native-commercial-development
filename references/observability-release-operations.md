# Observability, Release, and Operations

## Contents

1. Observability baseline
2. Service objectives
3. Release design
4. Migration safety
5. Rollback and restore
6. Incident response
7. Deterministic control bands
8. Post-release learning

## 1. Observability baseline

Instrument critical systems with:

- **Traces:** request and workflow path
- **Metrics:** runtime measurements and business outcomes
- **Logs:** structured event records
- **Profiles:** resource use where useful
- **Context propagation:** correlation across boundaries

For every critical journey, define:

- Start and success event
- Failure event and reason
- Latency
- Volume
- Dependency status
- User/business impact
- Cost where material
- Version/feature flag

Do not log secrets, raw credentials, unnecessary personal data, or unrestricted model prompts.

## 2. Service objectives

Define measurable objectives for:

- Availability
- Success rate
- Latency
- Data durability
- Notification delivery
- AI task success
- Recovery time
- Cost per transaction or user

Alert on user impact, not only CPU.

## 3. Release design

Every release should identify:

- Exact artifact and commit
- Reproducible build method
- Environment differences
- Configuration changes
- Dependency changes
- Feature flags
- Rollout stages
- Health checks
- Monitoring window
- Abort conditions
- Rollback target

Prefer small, frequent, reversible releases.

## 4. Migration safety

For data/schema changes:

1. Back up and verify backup usability.
2. Test on production-like data volume.
3. Prefer backward-compatible expand/migrate/contract.
4. Make steps idempotent.
5. Record checkpoints and counts.
6. Validate before and after invariants.
7. Avoid long exclusive locks.
8. Define rollback or forward-fix.
9. Monitor errors, duration, and data discrepancies.
10. Keep old code compatible until migration stabilizes.

## 5. Rollback and restore

Code rollback is not data rollback.

Document separately:

- Application rollback
- Configuration rollback
- Infrastructure rollback
- Database rollback
- Data restore
- Queue/event recovery
- Third-party side-effect reconciliation

Test restore procedures periodically. A backup without a successful restore drill is unproven.

## 6. Incident response

During an incident:

1. Protect users and data.
2. Stop or contain the harmful path.
3. Preserve evidence.
4. Restore service safely.
5. Communicate facts and uncertainty.
6. Identify direct and systemic causes.
7. Add regression tests, alerts, runbooks, or architecture controls.
8. Track corrective actions to completion.

Do not let an agent make broad production edits while diagnosis is uncertain.

## 7. Deterministic control bands

Use control bands only after a metric has a stable definition, sufficient baseline, named owner, tested detector, and low-noise escalation path. Detection must remain deterministic; the model may interpret evidence only after the detector fires.

Start disabled and promote one tier at a time:

1. **Observe:** record the breach and evidence.
2. **Diagnose:** invoke a read-only agent that cannot mutate code, infrastructure, data, or external systems.
3. **Propose:** allow the agent to create an intent, issue, or pull request through normal review gates.
4. **Runbook:** permit only a named, pre-approved, rehearsed, idempotent runbook with scoped identity, complete audit logging, bounded retries, and a kill switch.

The configuration is JSON-compatible YAML so deterministic tooling can reject duplicate keys and inspect typed booleans without an optional YAML parser. `active_tier` names exactly one tier, and only that tier may have `enabled: true`. A transition records its previous tier, approver, approval evidence, verification evidence, and activation time. Setting global status to enabled without a valid single active tier is invalid.

Automatic production mutation, deployment, or rollback is disabled by default. Enabling it is R3 and requires explicit human approval, restore evidence, an independent specialist review where material, and a deterministic authorization mechanism outside the model. A statistical threshold alone never authorizes production action.

Use `assets/project-template/docs/operations/AUTONOMY_BANDS.yaml`. Record false positives, dismissals, time from breach to diagnosis, findings accepted into work, repeated incidents, and incident-to-eval time. Disable or step down the system when noise, model drift, or operational risk exceeds the documented guardrails.

## 8. Post-release learning

Within the monitoring window, record:

- Expected versus actual metrics
- Errors and support signals
- Rollback or hotfix
- Cost change
- Manual intervention
- Missing telemetry
- New practice candidate
- Governance friction

Feed this record into the skill evolution process.
