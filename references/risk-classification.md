# Risk Classification

## Contents

1. Scoring dimensions
2. Risk levels
3. Escalation rules
4. Required controls

## 1. Scoring dimensions

Score each dimension from 0 to 3:

| Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| User impact | Invisible | Minor | Core journey | Safety/financial/large-scale |
| Data sensitivity | None | Internal | Personal/confidential | Regulated/secret |
| Reversibility | Immediate | Easy | Difficult | Irreversible |
| Privilege | Read-only | Normal user | Admin/service write | Root/prod/security control |
| Blast radius | Isolated | One module | Many users/services | Whole system/external world |
| Novelty | Known pattern | Small variation | New integration | New architecture/agent autonomy |
| Operational risk | None | Recoverable | Downtime/data risk | Severe outage/loss |
| AI autonomy | None | Generate only | Tool-assisted action | Privileged/destructive autonomy |

Use judgment, not only arithmetic. Any dimension at 3 generally requires R3 review.

## 2. Risk levels

### R0 — Low

Examples:

- Copy and documentation
- Styling with no behavior change
- Test-only improvement
- Internal comments
- Nonfunctional refactor proven equivalent

Required:

- Diff review
- Relevant quick check
- Visual evidence if UI
- No unrelated changes

### R1 — Standard

Examples:

- Ordinary CRUD
- Search/filter/display
- Non-sensitive API integration
- Back-office workflow without privileged consequences

Required:

- Written acceptance criteria
- Branch/PR
- Unit or integration coverage
- Relevant regression tests
- Independent review
- Release note and rollback path

### R2 — High

Examples:

- Authentication or authorization
- Personal or confidential data
- Payments, refunds, credits, pricing
- File upload or external content
- Messaging and notifications
- Maps, location, background tracking
- AI-generated decisions or tool calls
- Core schema migrations
- High-volume external APIs
- Critical user journey changes

Required:

- Full spec and ExecPlan
- Threat model update
- Negative and adversarial tests
- End-to-end journey
- Security and dependency scans
- Migration rehearsal
- Feature flag or staged rollout
- Monitoring and rollback evidence
- Explicit human ship decision

### R3 — Critical

Examples:

- Destructive production operations
- Identity, key, permission, or tenant-isolation foundations
- Large irreversible migration
- Financial ledger correctness
- SOS, safety, medical, or legal action
- Autonomous deletion, purchase, payout, publication, or privilege change
- Compliance-critical data processing

Required:

- Everything in R2
- Specialist external review where expertise is material
- Two-person or equivalent independent approval when available
- Restore or disaster-recovery rehearsal
- Strong staged rollout and kill switch
- Documented residual-risk acceptance
- No unattended autonomous release

## 3. Escalation rules

Escalate one level when:

- Requirements are uncertain.
- Existing tests are weak.
- The system is poorly observed.
- The change touches legacy code with unknown ownership.
- The dependency is unmaintained or security-sensitive.
- Production data must be transformed.
- A model can act on untrusted external content.
- The rollback cannot restore data state.
- A failure is hard to detect quickly.

## 4. Required controls matrix

| Control | R0 | R1 | R2 | R3 |
|---|---:|---:|---:|---:|
| Written spec | Optional | Yes | Yes | Yes |
| ExecPlan | No | As needed | Yes | Yes |
| Independent review | Lightweight | Yes | Yes | Yes + specialist |
| Unit/integration | Targeted | Yes | Yes | Yes |
| Critical E2E | As applicable | Core | Yes | Yes |
| Threat model | No | As applicable | Yes | Yes |
| Migration rehearsal | No | As applicable | Yes | Yes |
| Feature flag/staging | Optional | Recommended | Required | Required |
| Restore rehearsal | No | No | As applicable | Required |
| Human ship verdict | Implied | Yes | Explicit | Explicit + recorded |
