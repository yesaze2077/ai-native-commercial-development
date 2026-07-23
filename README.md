# AI-Native Commercial Development

A production-governance skill for solo/OPC developers using AI coding agents to build commercial applications.

## What it does

This skill turns AI-assisted development into an auditable workflow:

- Specification before implementation
- Risk-based gates
- Independent review
- Automated verification
- Security and least privilege
- Release evidence and rollback
- Observability and incident learning
- Eval-gated, reversible self-evolution

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
python scripts/bootstrap_governance.py --target /path/to/repository
```

The script refuses to overwrite existing files unless `--force` is provided.

## Validate the skill

```bash
python scripts/validate_skill.py .
```

## Self-evolution boundary

The skill can research practices, capture feedback, score candidates, run evals, and prepare changes. It must not silently auto-merge semantic governance changes. Safe self-evolution means automated evidence generation plus explicit approval at the accountability boundary.

A `SKILL.md` file cannot monitor the internet or update itself while idle. Continuous learning requires an external scheduler or a recurring invocation in the coding environment.
