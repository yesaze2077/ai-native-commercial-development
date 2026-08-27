# Review Policy

- Owner:
- Applies to:
- Effective version:
- Last reviewed:

## Required inputs

- Accepted intent or equivalent request
- Approved specification
- Approved plan when required
- Diff and changed artifact list
- Test, security, migration, and release evidence
- Artifact-lineage record

## Reviewer separation

Use a reviewer context that did not author the change. The reviewer may recommend a verdict but cannot approve its own high-risk change or release.

## Review passes

1. **Correctness:** acceptance criteria, business rules, regressions, edge cases, failure behavior.
2. **Security and operations:** authorization, data exposure, injection, secrets, dependencies, retries, concurrency, monitoring, migration, rollback.
3. **Traceability and design:** intent/spec/plan alignment, architecture boundaries, unexplained scope, artifact lineage, documentation and evidence truthfulness.

## Severity

- **Blocker:** cannot merge or release.
- **High:** material user, security, data, reliability, or compliance risk; resolve before release.
- **Medium:** real risk with an explicit owner and accepted disposition.
- **Low:** bounded improvement that does not obscure higher risks.
- **Nit:** non-blocking polish.

## Noise controls

- Report at most five Nits; summarize additional polish as a count.
- Do not repeat formatter, linter, generated-file, or other deterministic findings unless the control failed or the result is suspect.
- Do not manufacture findings to fill every pass.

## Required output

| Finding ID | Pass | Severity | File/artifact | Evidence | Impact | Required action | Owner/status |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

## Verdict

SHIP / CONDITIONAL / NO-SHIP / BLOCKED

## Feedback loop

Repeated findings become a test, deterministic guardrail, project instruction, or behavior-eval case. Review policy changes are versioned and reviewed like code.
