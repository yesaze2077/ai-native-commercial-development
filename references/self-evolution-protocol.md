# Self-Evolution Protocol

## Contents

1. Objective
2. Event capture
3. Candidate states
4. Experiment design
5. Skill evals
6. Promotion rules
7. Governance PR
8. Automation boundary
9. Versioning and rollback

## 1. Objective

Improve the development system from real evidence while preventing self-reinforcing mistakes.

Self-evolution must optimize accepted outcomes, not activity.

## 2. Event capture

Capture an evolution event when:

- The same agent mistake occurs twice.
- A task needs repeated manual prompting.
- A test misses a production defect.
- A review repeatedly finds the same issue.
- A release, migration, or rollback is painful.
- Documentation is hard to discover.
- Tool use is unsafe or inefficient.
- A new external practice appears relevant.
- User feedback indicates a persistent process problem.

Record:

- Context
- Expected behavior
- Actual behavior
- Evidence
- Root-cause category
- Candidate durable fix
- Risk of changing the system

## 3. Candidate states

Use:

1. `candidate`
2. `experimental`
3. `recommended`
4. `required`
5. `deprecated`
6. `rejected`
7. `revisit-on-condition`

Do not skip from candidate to required.

## 4. Experiment design

Define before changing the skill:

- Hypothesis
- Target task types
- Baseline
- Changed component
- Success metrics
- Guardrail metrics
- Minimum sample
- Stop condition
- Reversal plan

Prefer testing one change at a time.

For frequent tasks, use at least three representative real tasks. For trigger and behavior regression, maintain 10–20 focused eval prompts and grow from real failures. Larger or higher-risk programs may expand toward 20–50 cases when the added coverage justifies the recurring model and review cost.

## 5. Skill evals

Evaluate four categories:

### Outcome

- Task completes
- Application runs
- Acceptance criteria pass
- No regression

### Process

- Skill triggers correctly
- Risk is classified
- Required artifacts are created
- Tests actually run
- Independent review occurs
- Stop conditions are respected

### Quality and safety

- Output follows architecture and security rules
- No secrets or unsafe privileges
- No fabricated evidence
- Release and rollback are addressed
- High-risk work is not self-approved

### Efficiency

- No repeated thrashing
- Context remains focused
- Token/tool cost is reasonable
- Small tasks do not receive excessive ceremony

Use deterministic checks where possible and rubric grading where judgment is necessary.

### Executable behavior-eval gate

Use `scripts/run_behavior_evals.py` to validate the behavior-contract manifest and score outputs produced by a real agent or an approved adapter. The runner deliberately does not embed a vendor command or credential. A live adapter must be an explicit executable that accepts one JSON request on stdin and returns the agent response on stdout.

For semantic skill, instruction, template, hook, or approval-policy changes:

1. Run the focused trigger suite when the skill name, description, invocation policy, or routing behavior changes. For other changes, validate the trigger corpus structure and state why a live trigger run is not applicable.
2. Run at least three representative behavior cases against contemporaneous real-agent outputs, plus every case related to the changed control. Capture may occur through a live CI adapter or a fresh independent context outside CI; retain provenance and raw responses in either case.
3. Record skill version, model/provider, tool or harness version, configuration digest, timestamp, pass rate, failures, duration, and cost when available.
4. Compare the candidate report with the accepted compatible baseline and fail the change on a safety regression or a lower required-case pass rate. If no behavior baseline exists, establish the first reviewed baseline explicitly, preserve the deterministic pre-change checks, and make no before/after behavior-rate claim.
5. Add each material production incident as a permanent behavior case and track incident-to-eval lead time.

`--validate-only`, unit tests, fixtures, and manifest checks prove the evaluator is well formed; they do not prove current agent behavior. Regex contracts are necessary mechanical checks but are not semantic safety judgments. Require a separate independent rubric review bound to the raw-response digests. CI must replay the contracts and verify the versioned rubric review; when an approved live adapter is available, add it as a required check rather than treating it as universally available.

Digest binding proves that in-tree files are mutually consistent; it does not prove who authored the semantic verdict or that the reviewer was independent. For R3 semantic governance changes, require an out-of-band trust decision over the manifest, behavior-configuration digest, semantic-review digest, and raw-response digest set. Use a protected repository environment with required reviewers, or a detached signature whose verification key is controlled outside the authoring write scope. Fail closed when that trust mechanism is not configured. The included GitHub Actions workflow uses the `semantic-governance-review` environment and requires the repository variable `SEMANTIC_REVIEW_TRUST_CONFIGURED=true`; set it only after required reviewers are configured. Local validation cannot substitute for this identity/approval gate.

## 6. Promotion rules

### Candidate → Experimental

Require:

- Clear problem and hypothesis
- Source provenance
- Reversible design
- No unacceptable security expansion
- Initial score above project threshold

### Experimental → Recommended

Require:

- Better outcome or lower human effort
- No material quality/safety regression
- Representative task evidence
- Updated docs and tests
- Changelog

### Recommended → Required

Require:

- Repeated value
- Low false-positive rate
- Mechanical enforcement where possible
- Acceptable maintenance cost
- Explicit human approval

### Any state → Deprecated/Rejected

Use when:

- Tool/model behavior changed
- Cost exceeds benefit
- It creates new regressions
- Better control replaces it
- It no longer matches project risk

## 7. Governance PR

Every semantic skill change should include:

- Problem
- Source and provenance
- Current behavior
- Proposed behavior
- Prediction
- Files changed
- Eval cases
- Before/after results
- Security impact
- Compatibility impact
- Rollback
- Version change
- Human decision

A reviewer context should challenge whether the skill is learning the correct lesson or overfitting one incident.

## 8. Automation boundary

Allowed automation:

- Gather current sources
- Create candidate files
- Run source and repository checks
- Run evals
- Run behavior contracts against live agent outputs and compare the accepted baseline
- Produce score and comparison
- Patch references and templates
- Open a governance PR
- Revert failed experiments

Never auto-merge:

- Core `SKILL.md` behavior
- Risk levels
- Quality gates
- Security rules
- Approval policy
- Production access
- CI enforcement
- Destructive-operation rules

Background learning requires an external scheduler. The skill itself is inert when not invoked.

Suggested scheduled prompt:

```text
Use $ai-native-commercial-development in practice-radar and skill-evolution mode. Review current official documentation, maintained GitHub repositories, issues, releases, and selected expert X posts. Create at most three evidence-backed candidates, run existing skill evals, and open or prepare a governance PR. Do not merge or weaken any gate.
```

## 9. Versioning and rollback

Use semantic versioning:

- Patch: wording, references, non-semantic maintenance
- Minor: new optional workflow/reference/script
- Major: changed required behavior, risk, or approval model

Tag every approved version. Keep the previous version installable. Roll back when evals, real usage, or incidents show regression.
