# Artifact Authority and Lineage

The repository is the durable execution and audit record. Each artifact has exactly one authoritative system. A mirror is never edited as an independent source of truth.

When an external system is authoritative, record its stable ID and an immutable snapshot, digest, or version-pinned reference here. Write the relevant commit SHA back only when the external action is authorized and supported; otherwise register a pending backlink for an authorized owner. Resolve conflicts before implementation or release.

| Artifact ID | Type | Status | Parent artifact | Authoritative system | Stable record ID or path | Snapshot/digest/commit | Owner | Approval evidence | Supersedes |
|---|---|---|---|---|---|---|---|---|---|
| | Intent / Spec / Plan / ADR / Change / Review / Release / Incident | | | | | | | | |

## Reconciliation log

| Date | Artifact ID | Conflict | Authority applied | Resolution | Owner |
|---|---|---|---|---|---|
| | | | | | |

## Rules

- Do not use chat history as the only durable requirement or decision record.
- Do not maintain two independently editable authoritative copies.
- Do not turn local implementation authority into external write authority.
- Derived artifacts must link to their immediate parent.
- Approval evidence must identify the approver and stable record.
- A superseded artifact remains discoverable and points to its replacement.
