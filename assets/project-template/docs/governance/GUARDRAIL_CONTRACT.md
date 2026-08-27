# Guardrail Contract

Instructions and skills are advisory. Every policy that must always hold needs a deterministic enforcement point and verifiable evidence.

| Policy ID | Control objective | Scope and risk | Advisory instruction | Deterministic mechanism | Enforcement point | Denied action or fail mode | Evidence event/artifact | Owner | Break-glass approval | Test and cadence | Version |
|---|---|---|---|---|---|---|---|---|---|---|---|
| | | | | CI / sandbox / branch rule / typed authorization / hook | | Fail closed / fail safe | | | | | |

## Control requirements

- The deterministic mechanism must not depend on model judgment for authorization.
- Fail-open behavior must be justified, time-bounded, observable, and approved at the task's risk level.
- Break-glass access uses a named owner, short lifetime, complete audit record, and post-use review.
- Tests prove both allowed and denied paths.
- A control without current evidence is advisory only and cannot support a SHIP verdict for a mandatory policy.

## Change record

| Date | Policy ID | Change | Reason | Evidence | Approved by | Rollback |
|---|---|---|---|---|---|---|
| | | | | | | |
