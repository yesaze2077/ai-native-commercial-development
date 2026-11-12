# AI-Native Commercial Development

A task-sized commercial-development workflow for solo/OPC developers using AI coding agents.

## Incremental verification (6.0.0)

Use the project's native affected/cache tools when available, or configure the optional explicit component/check map described in `references/incremental-verification.md`. The bundled planner defaults to read-only. Authorized execution selects checks by dependency impact, separates quick feedback from batch integration and full fresh release checks, and reuses only explicitly cacheable successful results with matching declared inputs. Unknown/global changes widen scope and disable reuse.

Project paths, dependency edges and commands must be reviewed for that project. The skill does not automatically discover a sound graph, install a CI system or modify existing protected gates. See `governance/6.0.0-change-evidence.md` for actual tests, limits and rollback.

## Commercial product lifecycle (5.0.0)

The skill connects product/problem decisions, requirements, interaction and visual design, architecture and technology choices, delivery management, application acceptance, commercial launch and product feedback. New products follow applicable handoffs; existing-product changes enter only affected stages. Existing approved artifacts remain authoritative. Specialist tools are optional and must actually be available; the built-in guides remain usable without them.

`references/acceptance-and-evidence.md` explains the optional local evidence checker and its limits. The 5.0.0 evidence package distinguishes scenario answers, actual local synthetic-repository exercises and production/market evidence. No production or commercial-outcome guarantee follows from local evaluation. See `governance/5.0.0-change-evidence.md`.

## Development efficiency (4.0.0)

Start from the affected task rather than scanning the entire repository. Reuse accepted requirements and check evidence only when its inputs and environment still apply. Small changes use a short path; complex and sensitive changes retain the risk-based gates. Local implementation, independent review and release have separate completion states. The main entrypoint loads detailed references only when relevant.

These changes reduce instruction duplication and avoidable process; actual delivery-time and cost improvements require real task measurements. Local validation is not hosted governance promotion. See `governance/4.0.0-change-evidence.md` for results, limits and the complete 3.0.0 rollback package.

## What it does

This skill turns AI-assisted development into an auditable workflow:

- Specification before implementation
- Optional intent capture with artifact authority and lineage
- Risk-based gates
- Independent review
- Deterministic guardrail contracts and review policy
- Controlled parallel execution with worktree isolation
- Automated verification
- Security and least privilege
- Release evidence and rollback
- Observability and incident learning
- Eval-gated, reversible self-evolution
- Disabled-by-default, tiered operational control bands

## Install

### Repository-scoped

Copy this folder into:

```text
<repo>/.codex/skills/ai-native-commercial-development/
```

### User-scoped

Copy this folder into:

```text
~/.codex/skills/ai-native-commercial-development/
```

Restart the coding agent after installation if it does not discover the skill immediately.

Other compatible agent systems can load the same `SKILL.md` and references from their own skill directory, or link the skill from repository-level instructions.

## Invoke

```text
Use $ai-native-commercial-development to bootstrap this project for commercial development.
```

```text
Use $ai-native-commercial-development to implement this feature through specification, risk classification, verification, independent review, and release evidence.
```

```text
Use $ai-native-commercial-development to audit whether this application is ready for production.
```

```text
Use $ai-native-commercial-development to run the practice radar, evaluate candidate improvements, and prepare a governance PR for this skill.
```

## Bootstrap a project

```bash
python scripts/bootstrap_governance.py --target /path/to/repository --dry-run
python scripts/bootstrap_governance.py --target /path/to/repository
```

Run the dry run first and review every planned path and conflict. The script refuses to overwrite existing files unless `--force` is provided.

Writes fail closed unless the runtime provides POSIX directory-descriptor and no-follow primitives. Within the selected target root, files are written to synced temporary inodes and published atomically so symlink races and hard-linked peers are not followed or truncated.

## Validate the skill

```bash
python scripts/validate_skill.py .
python scripts/run_behavior_evals.py --validate-only
```

## Behavior evals

`evals/behavior_contracts.json` contains the executable regression subset. Score auditable responses produced by a real agent:

```bash
python scripts/run_behavior_evals.py \
  --responses-dir /path/to/responses \
  --baseline /path/to/accepted-report.json \
  --semantic-review /path/to/semantic-review.json \
  --require-semantic-review \
  --report /path/to/candidate-report.json
```

For a live run, provide an explicit executable adapter. It receives one JSON request on stdin and returns the agent response on stdout. The harness passes only a minimal environment unless a variable is explicitly allowlisted with `--pass-env`.

```bash
python scripts/run_behavior_evals.py \
  --runner /path/to/approved-adapter \
  --save-responses-dir /path/to/raw-responses \
  --metadata model=<model> \
  --metadata tool_version=<version> \
  --max-output-bytes 1048576 \
  --report /path/to/candidate-report.json
```

The harness computes `configuration_digest` itself from `SKILL.md`, agent metadata, references, project templates, eval definitions, and deterministic scripts. It cannot be supplied by the adapter or caller.

The live adapter is a trusted launcher, not an OS sandbox. The harness uses a temporary working directory, a minimal inherited environment, an output-size limit, no shell, fail-closed evidence creation, and heuristic secret-pattern checks; the adapter still inherits whatever filesystem, network, process, and credential access the host grants it. Run the adapter in an external sandbox or isolated CI job when containment is required, and review/redact raw outputs before publication.

Manifest validation, fixtures, deterministic regex replay, and secret heuristics prove only their specific mechanical contracts. They do not prove semantic correctness or a new live model run. Semantic governance changes require representative real-agent responses plus a separate rubric review bound to every raw-response digest. `scripts/validate_skill.py` recomputes the contracts and verifies the semantic-review digest instead of trusting stored `passed` fields.

Those local checks prove consistency, not reviewer identity or independence. For an R3 semantic release, configure the GitHub environment `semantic-governance-review` with required reviewers, then set the repository variable `SEMANTIC_REVIEW_TRUST_CONFIGURED=true`. The separate CI job fails closed while that out-of-band trust declaration is absent. A protected-environment approval or an externally controlled detached signature must cover the manifest, current behavior-configuration digest, semantic-review digest, and raw-response digest set. Do not describe a mutable in-tree digest alone as reviewer attestation.

## Artifact authority

The repository is the durable execution and audit record. Each intent, specification, plan, change, review, release, and incident declares one authoritative system. External systems remain compatible through stable record IDs plus immutable snapshots, digests, or version-pinned references. Mirror a commit SHA back only when that external write is authorized and supported; otherwise record a pending backlink locally. Independently editable duplicate truths are prohibited.

## Self-evolution boundary

The skill can research practices, capture feedback, score candidates, run evals, and prepare changes. It must not silently auto-merge semantic governance changes. Safe self-evolution means automated evidence generation plus explicit approval at the accountability boundary.

A `SKILL.md` file cannot monitor the internet or update itself while idle. Continuous learning requires an external scheduler or a recurring invocation in the coding environment.

The operational control-band template starts disabled. Automatic production mutation, deployment, and rollback remain false unless an R3 process explicitly approves and verifies a rehearsed runbook, scoped identity, audit path, restore evidence, and kill switch.

The distributable includes the previous coherent package at `governance/rollback/ai-native-commercial-development-2.0.0.zip` and its SHA-256 file. The validator checks the digest, archive integrity, and embedded version before 3.0.0 can pass.


## Parallel execution

Parallel agents are used only for independent, bounded work. Read-heavy exploration and verification are the default parallel cases. Concurrent writers require frozen contracts, separate worktrees/branches, explicit resource namespaces, one integration coordinator, and a full combined-state regression gate.

For a solo developer, category ceilings are three read-only workers, two write workers, and one independent reviewer. These are not additive entitlements: start with the smallest useful set, obey stricter host limits, and count the coordinator when it consumes an agent slot. Adjust concurrency using lead-time, conflict, defect, cost, and owner-attention data.
