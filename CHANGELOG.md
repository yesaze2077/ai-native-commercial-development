# Changelog

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
