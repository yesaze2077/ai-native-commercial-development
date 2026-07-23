# Security and AI Safety

## Contents

1. Secure development baseline
2. Agent execution containment
3. Application controls
4. AI-feature controls
5. External content and MCP
6. Secrets and production access
7. High-risk approvals

## 1. Secure development baseline

Use secure-development practices throughout the lifecycle, not only before launch.

Baseline:

- Protect source, CI, build, signing, and deployment environments.
- Define security requirements in the spec.
- Threat-model R2–R3 changes.
- Review third-party components and licenses.
- Scan source, dependencies, containers, infrastructure, and secrets.
- Verify authentication, authorization, session, input, output, file, API, logging, and data-protection controls.
- Track vulnerabilities to closure and prevent recurrence.
- Preserve build provenance and dependency traceability.

Use OWASP ASVS Level 2 as a practical default for most commercial web/API applications. Consider Level 3 for high-value or safety-critical systems.

## 2. Agent execution containment

Control what the agent can do, not only what it is told to do.

Prefer:

- Workspace-limited filesystem access
- Network denied by default
- Allowlisted egress when needed
- Ephemeral or isolated devcontainers
- Read-only production data
- Short-lived, narrowly scoped credentials
- Separate deploy identity
- No secrets in agent context
- Command logging
- Approval for destructive actions

Avoid approval fatigue. A stream of low-value prompts encourages blind approval. Use hard environmental boundaries and reserve human approval for consequential actions.

## 3. Application controls

Verify:

- Server-side authorization for every protected action
- Tenant isolation
- Input validation and output encoding
- CSRF, XSS, injection, SSRF, and request-smuggling protections as applicable
- Secure upload type, size, storage, scanning, and serving
- Rate limits and abuse controls
- Idempotency for financial or repeatable actions
- Secure session and token lifecycle
- Encryption in transit and at rest
- Data minimization and retention
- Audit logging without sensitive leakage
- Safe error messages
- Backup confidentiality and access control

## 4. AI-feature controls

Treat model output as untrusted data.

Require:

- Typed/structured output validation
- Deterministic authorization outside the model
- Tool allowlists and scoped arguments
- Confirmation for privileged, destructive, financial, or external actions
- Prompt-injection and indirect-injection tests
- Retrieval provenance and trust labels
- Sensitive-data filters
- Output safety and policy checks
- Cost, rate, token, and recursion limits
- Timeouts and bounded loops
- Human escalation path
- Versioned prompts, models, tools, and eval datasets
- Fallback behavior that fails safely

Evaluate:

- Task success
- False actions and omissions
- Robustness to ambiguous and malicious input
- Tool-choice correctness
- Permission compliance
- Data leakage
- Latency and cost
- Model/provider changes
- Drift after prompt, retrieval, or tool updates

## 5. External content and MCP

Assume any fetched repository, webpage, issue, email, document, plugin output, or MCP response may contain hostile instructions.

Never combine all three without strong isolation:

1. Untrusted external content
2. Access to private data
3. Ability to communicate or act externally

For third-party tools:

- Review source and permissions.
- Pin versions or commits.
- Limit data and tool scope.
- Separate read and write capabilities.
- Validate tool output.
- Log consequential calls.
- Revoke unused credentials.
- Test failure and compromise scenarios.

## 6. Secrets and production access

Never:

- Commit `.env` files or keys.
- Paste production secrets into prompts.
- Let an agent search broad home directories for credentials.
- Grant permanent admin credentials to CI.
- Use production as a test environment.
- Allow an agent to delete or rewrite production data without an approved runbook.

If exposure occurs:

1. Stop use.
2. Rotate/revoke.
3. Remove from history and artifacts.
4. Determine access and impact.
5. Add detection and prevention.
6. Record the incident.

## 7. High-risk approvals

Require explicit approval before:

- Production deploy
- Schema migration with data transformation
- Permission or authentication policy change
- Payment/refund/payout logic change
- User-data deletion
- Public communication or publication
- External message sending at scale
- Installing a privileged third-party agent/plugin
- Weakening a security or quality gate
- Modifying this skill’s core governance
