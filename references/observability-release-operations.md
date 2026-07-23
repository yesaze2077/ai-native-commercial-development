# Observability, Release, and Operations

## Contents

1. Observability baseline
2. Service objectives
3. Release design
4. Migration safety
5. Rollback and restore
6. Incident response
7. Post-release learning

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

## 7. Post-release learning

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
