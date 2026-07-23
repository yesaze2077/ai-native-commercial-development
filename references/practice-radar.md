# Practice Radar

## Contents

1. Purpose
2. Source hierarchy
3. Discovery queries
4. Candidate intake
5. Validation
6. Cadence
7. Anti-hype rules

## 1. Purpose

Continuously discover useful AI-native development practices without turning the project into a trend-driven experiment.

The radar produces candidates, not instant policy.

## 2. Source hierarchy

### S — Standards and official primary sources

Examples:

- OpenAI Codex and Agent Skills documentation
- Anthropic engineering and Claude Code documentation
- GitHub documentation and official repositories
- NIST SSDF
- OWASP ASVS and GenAI/Agentic Security
- SLSA
- OpenTelemetry
- DORA research
- Framework, cloud, database, and language official documentation

### A — Reproducible repositories and engineering evidence

Evaluate:

- Maintainer identity
- Recent releases and commits
- Issue and PR quality
- Tests and CI
- Security posture
- License
- Adoption and real use
- Reproducibility
- Pinning and rollback

### B — Detailed practitioner reports

Track experienced builders who publish code, examples, failures, and limits. Useful seed areas include:

- Outer-loop accountability
- Loop and harness engineering
- Context engineering
- Red/green TDD
- Git/worktree isolation
- Subagents and reviewer separation
- Comprehension debt
- Long-horizon state on disk

### C — X and short-form discussion

Use only to discover:

- New terms
- New repositories
- New failure modes
- New experiments
- Links to primary material

Do not make a post a required rule merely because the author is influential or the post is popular.

## 3. Discovery queries

When web and GitHub tools are available, search current material using queries such as:

### Official

- `site:developers.openai.com codex best practices AGENTS.md skills evals`
- `site:anthropic.com/engineering Claude Code best practices sandbox context evals`
- `site:docs.github.com Copilot instructions code review security branch protection`
- `site:github.com/github/spec-kit releases constitution converge`
- `site:nist.gov SSDF software AI secure development`
- `site:owasp.org ASVS agentic applications`
- `site:slsa.dev specification`
- `site:opentelemetry.io observability`
- `site:dora.dev AI assisted software development`

### GitHub

- `path:SKILL.md agentic coding`
- `filename:AGENTS.md testing security`
- `topic:agentic-coding`
- `topic:spec-driven-development`
- Repository releases, issues, discussions, and merged PRs for tools already used

### X

Search named experts and terms, then follow links to original material:

- `agentic engineering`
- `outer loop`
- `loop engineering`
- `harness engineering`
- `red green TDD`
- `coding agent regression`
- `AGENTS.md`
- `Ralph loop`
- `comprehension debt`
- `agent sandbox`
- `skill evals`

Always compare publication date with event date and current tool versions.

## 4. Candidate intake

Create one candidate per practice:

- Practice name
- Source and date
- Source tier
- Problem addressed
- Proposed project/skill change
- Hypothesis
- Applicability
- Dependencies and lock-in
- Security and privacy impact
- Experiment
- Metrics
- Reversal plan
- Decision

Use `assets/project-template/docs/practice-radar/CANDIDATE_TEMPLATE.md`.

## 5. Validation

Before experimentation:

1. Read the original source.
2. Confirm current versions and behavior.
3. Inspect repository code and issues.
4. Search for failures and counterexamples.
5. Identify whether evidence is benchmark, anecdote, or production.
6. Check whether the practice depends on a specific model, tool, language, or team scale.
7. Define measurable success and possible harm.
8. Score with `scripts/score_practice_candidate.py`.
9. Start with a reversible, narrow experiment.

## 6. Cadence

Recommended for an OPC developer:

- Continuous: capture friction after tasks.
- Weekly: review up to 10 high-signal items.
- Monthly: test at most 1–2 candidates.
- Quarterly: prune deprecated rules and audit the full governance system.
- After incidents: run an immediate focused radar search for the failure class.

Avoid spending more time collecting practices than shipping and measuring product value.

## 7. Anti-hype rules

Reject or defer when:

- The practice has no clear problem.
- Evidence is only screenshots or claims.
- It requires excessive autonomy without verification.
- It expands permissions or blast radius.
- It creates more ceremony than risk reduction.
- It optimizes generated-code volume instead of accepted outcomes.
- It hides vendor lock-in or cost.
- It removes human comprehension.
- It cannot be reverted.
