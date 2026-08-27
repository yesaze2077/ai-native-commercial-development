# Practice Candidate: Production Control Bands

- State: Experimental template only; all tiers disabled
- Source: https://claude.com/blog/the-ai-native-sdlc-playbook
- Published: 2026-08-21
- Retrieved: 2026-08-27
- Source tier: S, official vendor guidance
- Source content evidence: `anthropic-ai-native-sdlc-source-content.json`
- HTTP body SHA-256: `2a8450b3c847c602251fd0e46a8172f2f2186023aa9f6c8583b439130395f12a` over 602,036 response bytes; two consecutive fetches matched
- Normalized claim summary: `anthropic-ai-native-sdlc-source-claims.txt`
- Claim-summary SHA-256: `07a1520e978abf2bbba0071eb61134e55df1d1e27da1cd45edc8de0e9b650d50`
- Evidence class: Practice guidance; the response body was fingerprinted in memory but not retained or redistributed; no production-autonomy benchmark for this skill

## Problem and proposed practice

Operations need a vocabulary for moving from observation to diagnosis and proposals without silently granting an agent production authority. Add a machine-validated template with observe, diagnose, propose, and runbook tiers, but ship every tier disabled.

## Hypothesis

A typed, disabled-by-default contract will make future autonomy proposals reviewable and reject unsafe defaults earlier than prose-only guidance.

## Counterevidence and limits

- No evidence currently justifies activating any production tier for this skill.
- A local template does not create OS, network, identity, or deployment isolation.
- Statistical anomaly detection cannot itself authorize mutation, deployment, or rollback.
- Activation could expand blast radius and therefore requires its own R3 decision, scoped identity, rehearsal, audit path, and kill switch.

## Experiment, stop condition, and reversal

The 3.0.0 experiment is template validation only: duplicate keys, non-boolean controls, enabled defaults, and automatic production action must fail validation. Stop on any ambiguous active tier or unapproved production capability. Reversal is removal of this optional template or restoration of the bundled 2.0.0 package.

## Score and decision

- Score: 55.5
- Triage recommendation: `KEEP_AS_CANDIDATE`
- Decision: Keep as disabled experimental scaffolding. Do not activate through 3.0.0.
