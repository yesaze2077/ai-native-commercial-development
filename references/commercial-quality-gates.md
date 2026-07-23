# Commercial Quality Gates

## Contents

1. Quality dimensions
2. Verification stack
3. Definition of Done
4. Evidence rules
5. Quality scorecard
6. No-ship rules

## 1. Quality dimensions

Evaluate every commercial release across:

1. Product correctness
2. Data integrity
3. Security and privacy
4. Reliability and resilience
5. Performance and capacity
6. Accessibility and usability
7. Observability and supportability
8. Maintainability and architecture
9. Supply-chain integrity
10. Cost control
11. AI quality and safety when applicable
12. Release and recovery

## 2. Verification stack

### Static

- Formatting
- Lint
- Type checking
- Compile/build
- Architecture/dependency rules
- Secret detection
- Static security analysis
- Dependency vulnerability and license review

### Automated behavior

- Unit tests for rules and transformations
- Integration tests using real component boundaries where practical
- API/schema contract tests
- End-to-end critical journeys
- Migration tests
- Retry, timeout, idempotency, concurrency, and failure injection
- Accessibility tests
- AI evals and adversarial cases

### Human or agentic scenario verification

- Browser/device walkthrough
- Screenshots or recordings for UI changes
- Role and permission walkthrough
- Support/admin workflow
- Rollback drill
- Restore drill for critical data
- Explanation of critical data flow

Avoid over-mocking. A test that only proves mocks agree with mocks is weak evidence.

## 3. Definition of Done

Use all applicable checks:

### Product

- [ ] Goal and user value are clear.
- [ ] Acceptance criteria are met.
- [ ] Out-of-scope behavior did not leak into the change.
- [ ] Error and empty states are usable.

### Engineering

- [ ] Existing baseline was run before change.
- [ ] New tests fail before the fix when red/green TDD applies.
- [ ] Relevant checks pass.
- [ ] No unrelated diff remains.
- [ ] Architecture boundaries are preserved.
- [ ] New dependency decisions are documented.

### Security and privacy

- [ ] Authentication and authorization are tested.
- [ ] Sensitive data handling is documented.
- [ ] Inputs, files, webhooks, and external content are validated.
- [ ] Secrets are not present in code, logs, artifacts, or prompts.
- [ ] Abuse and rate-limit cases are addressed.
- [ ] Required scans pass.

### Operations

- [ ] Structured logs exist for critical actions.
- [ ] Metrics and traces cover critical journeys.
- [ ] Alerts have owners and thresholds.
- [ ] Migration, backup, rollout, and rollback are executable.
- [ ] Runbooks are updated.

### Governance

- [ ] Risk level is recorded.
- [ ] Independent review is complete.
- [ ] Blocker/High findings are resolved.
- [ ] Release evidence is complete.
- [ ] Human ship/block decision is recorded.
- [ ] Learning is captured.

## 4. Evidence rules

Every evidence item should identify:

- What ran
- Where it ran
- Version/commit
- Relevant configuration
- Result
- Timestamp when useful
- Artifact location
- Limitations

Forbidden:

- “Should pass”
- “Likely safe”
- Invented command output
- Screenshots from a different version
- A reviewer summary without the underlying checks
- Silently skipped tests

## 5. Quality scorecard

Track trends, not vanity output:

| Metric | Desired direction |
|---|---|
| First-pass acceptance rate | Up |
| Average rework cycles | Down |
| Escaped defects | Down |
| Change failure rate | Down |
| Recovery time | Down |
| Critical journey pass rate | At 100% |
| High-risk debt | Toward zero |
| Manual intervention per shipped change | Down |
| AI cost per accepted change | Controlled |
| Skill/governance regression rate | Toward zero |
| Documentation freshness | Up |
| Restore drill success | At 100% |

Do not use lines of code or agent task count as a quality metric.

## 6. No-ship rules

Do not ship with:

- Failing required checks
- Missing authorization evidence
- Unresolved critical/high security issue
- Unbounded data loss risk
- No detection path for critical failure
- No rollback or forward-fix path
- Unreviewed dependency or supply-chain change
- Unexplained user-impacting behavior
- AI tool actions that bypass deterministic policy
