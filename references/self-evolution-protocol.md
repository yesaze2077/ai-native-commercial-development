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

For frequent tasks, use at least three representative real tasks. For trigger and behavior regression, maintain 10–20 focused eval prompts and grow from real failures.

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
