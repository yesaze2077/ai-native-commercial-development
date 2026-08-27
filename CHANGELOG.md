# Changelog

## 3.0.0 — 2026-08-26

- Reframed the repository as the durable execution and audit record while requiring one declared authoritative system per artifact, stable cross-system references, immutable snapshots or digests, authorized-only commit-SHA backlinks, and explicit conflict reconciliation.
- Added optional intent capture plus artifact-lineage fields across specifications, plans, pull requests, releases, and incidents.
- Added a provider-neutral executable behavior-eval harness with manifest validation, replay and live-adapter modes, fail-closed raw-output retention, metadata requirements, minimal environment inheritance, output limits, secret heuristics, global contradiction guards, critical-case gates, compatible-baseline checks, and raw-digest-bound semantic review.
- Added CI replay of versioned behavior evidence and semantic-review verification without mislabeling structural checks or replay as a new live-agent run.
- Added project templates for review policy and deterministic guardrail contracts.
- Added a disabled-by-default autonomy-band template with deterministic detection, read-only diagnosis, proposal-only escalation, bounded execution, audit, and a kill switch; production mutation, deployment, and rollback remain disabled by default.
- Added regression tests for the new templates, safe autonomy defaults, bounded behavior-eval runner, known contradiction/paraphrase recomputation, in-tree evidence consistency, source provenance, rollback integrity, source-authority rules, and semantic skill-evolution controls.
- Added a fail-closed protected-environment CI gate for out-of-band semantic-review trust; local digests are explicitly treated as consistency evidence, not reviewer identity or independence.
- Persisted two scored source candidates for Anthropic, “The AI-Native SDLC playbook,” 2026-08-21: core governance is eligible for controlled adoption; production control bands remain experimental and disabled. The source is treated as official practice guidance rather than causal outcome evidence, and both candidates are bound to a repeated-fetch HTTP response-body fingerprint plus the normalized-claims digest without redistributing the full vendor page.
- Bundled the coherent 2.0.0 archive plus SHA-256 and made archive integrity/version validation a 3.0.0 gate.

## 2.0.0 — 2026-07-24

- Changed governance bootstrap from an unconditional start-of-invocation write to an explicitly authorized Bootstrap workflow with mandatory dry-run review.
- Reworked bootstrap writes to traverse target subdirectories through no-follow directory descriptors and fail closed when secure primitives are unavailable.
- Replaced truncating writes with synced temporary files and atomic publication, preserving hard-linked peers and cleaning incomplete temporary files.
- Added governance authorization behavior cases and deterministic regression gates.

## 1.1.0 — 2026-07-24

- Added controlled parallel execution as a risk-aware optimization.
- Added dependency checks, worktree isolation, OPC concurrency limits, fan-in integration gates, CI/deployment concurrency rules, metrics, templates, and eval cases.
- Added deterministic validation for the parallel board, required behavior cases, tests, and version/changelog alignment.
- Clarified that parallel planning is conditional, concurrency ceilings are not additive, and task packets must define tool, credential, data, and approval scope.

## 1.0.0 — 2026-07-23

- Established a commercial-grade, risk-based AI-assisted development workflow.
- Added repository bootstrap templates for specifications, plans, ADRs, quality, security, releases, rollback, incidents, and practice candidates.
- Added deterministic skill validation and practice-candidate scoring.
- Added bootstrap path-containment and symlink protections with regression tests.
- Added source governance for official documentation, GitHub, expert long-form material, and X discovery.
- Added bounded self-evolution through eval-gated governance pull requests.
- Pinned GitHub Actions to immutable commits.
