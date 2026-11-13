# Local issue queue — delivery contract v1

## Intent and boundary

Authority: `BRIEF.md`, accepted synthetic request in fixture commit `7da710e`; API/UI selectors derive from the supplied `application_cases/cases.json`. This file holds derived design/architecture decisions, not a second requirement authority.

One fictional internal operator captures a request, sees its status, and closes it when done. The intended value is avoiding forgotten requests; frequency, time saved, willingness to adopt/pay and business results are unmeasured assumptions. Existing alternatives are a text list or spreadsheet; they remain credible for real use. This exercise chooses a tiny local queue to verify delivery and persistence, not to establish that a new product is commercially preferable. No customer contact or discovery experiment is authorized.

Risk: **R1** ordinary local CRUD with synthetic non-sensitive data. Reversibility is a local code revert; no existing application data or production is touched. Runtime is loopback only. No accounts, tenancy, payment, notifications, external tools, cloud, packages or release are in scope. Operator owns the local database and any future product decision.

Continue locally when the accepted create → list/filter → close → restart journey and invalid-input checks pass. Change the implementation if the checks fail. Stop before production or real data: independent review, actual user evidence, security/operational design and separate authorization would be required. A polished UI or passing synthetic test is not market validation.

## Requirements and verification plan (before implementation)

| ID | Accepted behavior / contract | Planned check |
| --- | --- | --- |
| IQ-01 | Create trimmed, nonblank title of 1–120 Unicode characters; persist open ticket | HTTP create, boundaries; browser form reaches real API |
| IQ-02 | List all/open/closed; invalid status is 400 | HTTP filters plus browser empty/no-results transition |
| IQ-03 | Close existing ticket; closed stays closed; unknown ID is 404 | HTTP state/idempotency; browser visible closed state |
| IQ-04 | Reload and stop/restart retain tickets and state | Browser reload and HTTP process restart with same DB |
| IQ-05 | Reject invalid JSON, wrong title type/length, unsupported filters without writes | Negative HTTP tests; UI inline validation/recovery |
| IQ-06 | Labelled keyboard inputs, visible focus, useful empty/loading/error feedback, narrow layout | Browser walkthrough/screenshots at 1100/360px; rendered comparison |
| IQ-07 | `app.create_server(host, port, data_path)` returns stoppable HTTPServer; CLI prints loopback URL with `--port 0` | Supplied real-HTTP verifier; CLI subprocess and clean stop |

Baseline: repository contains only BRIEF and ignore rules; there is no application to run. Runtime inventory: Python 3.9.6, Node v22.17.0. No pre-existing behavior to preserve and no dependency selection uncertainty. This new slice does not need red/green bug reproduction; tests will verify externally visible invariants.

## Experience reference v1

Journey: open localhost → enter title → submit → see new open row → optionally filter → close row → closed label appears → reload/restart retains state. Single screen, no navigation. Capture form precedes queue; filter sits beside queue heading. Each row exposes title, readable status and one close action while open. No reopen, edit, delete, bulk actions, search or counters.

Visual choice: quiet warm canvas, dark ink, forest-green primary action, restrained orange eyebrow; serif heading and system sans controls. Chosen by implementation agent for the synthetic task; there is no brand asset, user design approval or usability study. The executable screen is the key-screen reference, versioned with the code.

Tokens: canvas `#f6f4ed`, surface `#ffffff`, ink `#202c28`, muted `#5c6b64`, primary `#245742`, border `#d6ddd5`; body system sans, heading Georgia; spacing 8/12/16/24/32/48px; max content 1000px; corners 12px; focus 3px dark green outline with offset. Responsive layout is one column below 640px, 44px minimum action/input height. No animation.

States: initial loading; first-use empty; no results for open/closed; per-form required/length validation; submitting with disabled submit; fetch failure with explicit retry and retained input; per-row closing with disabled button; mutation failure leaves row intact and retry possible; closed has text plus status styling. Errors are associated with the form and announced via live region. No permission/login state is fabricated because identity is out of scope.

Comparison: actual rendered desktop/mobile captures must be inspected against these hierarchy/spacing/focus/state commitments. Automated focus and labels are only partial accessibility evidence; no screen-reader audit or representative-user study is claimed.

## Architecture decision ADR-01

Fixed constraints select Python stdlib `http.server` + SQLite (`sqlite3`) + semantic HTML/CSS/JS. No vendor/version choice, install or network research is needed. SQLite transactions beat a hand-written JSON file here for atomic updates and simultaneous HTTP requests; in-memory storage fails accepted persistence. A framework/database service would violate the fixed no-package/no-cloud boundary.

Flow: browser (untrusted input) → same-origin loopback HTTP → server validation → parameterized SQLite transaction → JSON → safe `textContent` rendering. `app.py` holds HTTP/storage/CLI, `web/` holds explicit static assets, `test_app.py` adds focused contract checks. Static files use a fixed allowlist; arbitrary filesystem paths are never served. API JSON is size-capped; stack traces and ticket titles are not logged. The single operator has all local operations; there is no authentication/tenant boundary. This is unsuitable for LAN/public serving or confidential data.

Data: `tickets(id integer primary key, title text, status open|closed, created_at text, closed_at nullable text)`. IDs never change. Title is trimmed before validation, 1–120 Unicode code points; browser also uses code points to match Python. No uniqueness promise: separate create actions may create duplicate titles. Close is idempotent; original closed timestamp is retained. List is newest ID first, stable for ties. A connection per operation avoids cross-thread SQLite sharing; transactions serialize writes. Initial table creation only, no existing-schema migration.

API: `GET /api/tickets?status=all|open|closed` returns JSON array; `POST /api/tickets {title}` returns created object/201; `POST /api/tickets/{positive id}/close` returns closed object/200; `GET /health` runs a database query and returns health/200. Missing record/path 404, invalid JSON/title/filter 400, wrong media type 415, body >8192 bytes 413, unsupported mutation method 405. Safe JSON errors have `error`. Host/origin controls reject foreign origins/host headers for localhost protection; no permissive CORS.

Recovery: transaction failure returns safe 500 and rolls back. UI retains recoverable input and offers retry; no automatic POST retry because create is not deduplicated. SQLite commit persistence is tested across restart, not a backup guarantee. Stop with Ctrl+C, copy DB only while stopped before any future code change, restart same `--data`; schema-compatible code rollback can retain DB. No destructive migration, external side-effect reconciliation or production rollback applies. Unknown data/schema must fail safely rather than reset.

## Local handoff / review boundary

Run instructions are in `README.md`; actual commands, revision/digests, pass/fail output and screenshots go in ignored `evidence/execution.md`. Requirement → state/API → implementation → check → evidence is this table plus the execution record. Commit code and decisions, not DB/cache/evidence.

This local task ends after applicable HTTP, meaningful negative/restart, CLI and browser checks with screenshots. No hosted PR, independent fresh review, CI, user acceptance or launch is claimed. A later release requires independent review of this revision/spec/diff/evidence and authorized human decision. The single implementation agent's self-review is not independent. The next useful product step, if separately authorized, is a task walkthrough with actual intended users; no threshold or commercial claim is invented now.
