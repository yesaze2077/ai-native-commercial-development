# Practice Candidate: Anthropic AI-Native SDLC Core Governance

- State: Recommended, pending 3.0.0 R3 release approval
- Source: https://claude.com/blog/the-ai-native-sdlc-playbook
- Published: 2026-08-21
- Retrieved: 2026-08-27
- Source tier: S, official vendor guidance
- Source content evidence: `anthropic-ai-native-sdlc-source-content.json`
- HTTP body SHA-256: `2a8450b3c847c602251fd0e46a8172f2f2186023aa9f6c8583b439130395f12a` over 602,036 response bytes; two consecutive fetches matched
- Normalized claim summary: `anthropic-ai-native-sdlc-source-claims.txt`
- Claim-summary SHA-256: `07a1520e978abf2bbba0071eb61134e55df1d1e27da1cd45edc8de0e9b650d50`
- Evidence class: Practice guidance and worked examples, not a comparative benchmark or causal proof. The response body was fingerprinted in memory but not retained or redistributed.

## Problem

The 2.0.0 skill had strong lifecycle rules but no explicit intent-to-release lineage, no artifact-by-artifact external authority contract, no executable behavior-evidence gate, and no project templates for review policy or deterministic guardrails.

## Proposed practice

Adopt intent capture for material or ambiguous work, per-artifact authority and immutable lineage, deterministic enforcement for mandatory policy, structured independent review, and versioned behavior evidence with semantic rubric review.

## Hypothesis

These controls will reduce requirement drift, duplicate truth, unsafe prompt-only policy, low-signal review, and silent instruction regressions without adding heavy ceremony to narrow R0/R1 work.

## Applicability and dependencies

Applicable to commercial applications and governance changes. It assumes a durable repository, stable external record identifiers when another system is authoritative, a testable validation harness, and a human approval boundary.

## Counterevidence and limits

- The source is vendor guidance, not an independent comparative study.
- The article does not prove causal improvements for this exact skill or for solo developers.
- Intent artifacts can add overhead; narrow, unambiguous R0/R1 work therefore has an explicit skip path.
- Regex behavior contracts cannot establish semantic safety; independent rubric review remains required.

## Experiment and metrics

- Run all executable behavior cases on fresh agent responses.
- Replay deterministic contracts and independently grade semantic correctness.
- Require zero Blocker/High findings, no critical-case regression, and no unsafe production default.
- Track later requirement-reconciliation defects, repeated review findings, and incident-to-eval lead time.

## Security and privacy

The change does not grant new credentials or production permissions. Evidence capture uses a minimal environment and heuristic secret scanning, but adapters still inherit host filesystem/network permissions unless externally sandboxed.

## Reversal plan

Restore `governance/rollback/ai-native-commercial-development-2.0.0.zip`, verify its recorded SHA-256, then run the 2.0.0 validator and tests as one coherent unit.

## Score and decision

- Score: 79.1
- Triage recommendation: `ELIGIBLE_FOR_CONTROLLED_EXPERIMENT`
- Decision: Adopt only through the reviewed 3.0.0 R3 governance release. The score does not authorize adoption.
