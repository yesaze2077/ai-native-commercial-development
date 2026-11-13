# Independent public-CLI feedback lifecycle

This bounded synthetic exercise used the public CLI/schema and sample only. The runner implementation, its tests, behavior contracts, rubric, existing responses/reports and author conclusions were not inspected. All 17 assigned scenario responses were captured before this exercise and remain unchanged. The source was frozen by the parent before execution.

## Actual execution

- 16 real CLI subprocess calls, all exit 0, in one canonical private temporary non-Git workspace.
- External subprocess wall total: 0.506194s. This is a small synthetic execution measurement, not evidence of real-project productivity improvement.
- First absent-store assess returned no assessments and created no directories/files. Every later assess preserved the exact file list, content digests, modes and mtimes in the ledger directory.
- First and second workflow events were distinct tasks. A third record described the first occurrence again; the result was 3 records but 2 distinct occurrences and a project_trial suggestion. Exact duplicate input was recognized as duplicate.
- A deferred history note suppressed the unchanged proposal. Additional evidence recorded against the same first occurrence reopened review while the distinct count remained 2.
- An improved outcome did not become a new failure occurrence; count remained 2. It also did not erase the already-open unreviewed adverse evidence.
- An applied history note covering all then-known records resulted in monitor/no new proposal. A later input labeled regressed reopened urgent review, with count 3. The output explicitly cautioned that recording order alone cannot establish regression timing or causality.
- Every output stated rules_changed:false; assess outputs also stated rule_update_authorized:false and decision_is_authenticated_approval:false. No active rule was updated, authenticated or rolled back.
- Active installed package aggregate digest remained unchanged across all 394 source/evidence files (Git metadata and Python bytecode excluded). The candidate runner SHA-256 remained `4525c3d0c4a1cb4c6a6adadbb54097d4a7270ed2f838eaedea5587c11e48eb84` before/after.

| Assess checkpoint | Adverse occurrences | Recommendation | Suppressed | Reopened | Proposal |
|---|---:|---|---|---|---|
| Absent store | 0 | none | n/a | n/a | no |
| Two tasks plus repeated report | 2 | project_trial | false | false | yes |
| After defer | 2 | project_trial | true | false | no |
| New evidence, same occurrence | 2 | project_trial | false | true | yes |
| Improved outcome added | 2 | project_trial | false | true | yes, from prior unreviewed adverse evidence |
| Applied history, no new adverse input | 2 | monitor | false | false | no |
| Regressed input after applied history | 3 | project_trial, urgent | false | true | yes |

## Artifacts and limits

`command-ledger.json` retains exact argv/cwd/exit codes/timing and before/after file snapshots; per-call stdout/stderr, JSON and store snapshots plus synthetic inputs are retained. `receipt.json` binds runtime, runner and unchanged installed-package digests. `consistency-checks.json` independently checks observed public outputs against this fixture's occurrence identities and chronology. Temporary runtime files were removed after capture; versioned raw evidence remains.

The events, observed/reported evidence labels, user-decision references and applied note are synthetic test inputs. They are not verified application facts, a real user approval or a real installed rule change. No customer data, token, network, package installation, real local feedback store or production system was accessed. This bounded exercise does not cover every malformed/private/concurrent input condition or replace independent source tests/review. No semantic score was produced here.
