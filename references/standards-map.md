# Standards Map

Use current versions at execution time. Verify freshness before relying on any version number.

| Area | Primary baseline | Practical use |
|---|---|---|
| AI coding workflow | OpenAI Codex best practices, Agent Skills, long-horizon plans, skill evals | AGENTS.md, specs, plans, reusable skills, evals |
| Agent workflow | Anthropic engineering guidance | Simple composable agents, context engineering, subagents, containment |
| Spec-driven delivery | GitHub Spec Kit | Constitution, specify, clarify, plan, tasks, analyze, implement, converge |
| Repository governance | GitHub branch/ruleset and code review documentation | Protected main, required checks, reviewer automation |
| Secure SDLC | NIST SSDF | Prepare, protect, produce, respond; integrate security throughout |
| Application security | OWASP ASVS | Security requirements and verification levels |
| AI/agent security | OWASP GenAI and Agentic Security | Prompt injection, tool abuse, excessive agency, data leakage |
| Supply chain | SLSA | Build provenance, isolation, artifact trust |
| Observability | OpenTelemetry | Traces, metrics, logs, profiles, context propagation |
| Delivery performance | DORA | Delivery speed, change failure, recovery, rework |
| Product AI quality | OpenAI/Anthropic eval guidance | Outcome, process, safety, efficiency evals |

## Default assurance profile

For a typical commercial web/mobile application:

- Risk-based workflow in this skill
- OWASP ASVS Level 2 target
- NIST SSDF practices integrated into delivery
- Automated build and provenance where feasible
- Protected branch and required CI checks
- OpenTelemetry-compatible observability
- DORA-style delivery and recovery metrics

Escalate for high-value, regulated, financial, identity, safety, or agentic systems.
