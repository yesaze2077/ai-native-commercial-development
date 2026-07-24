#!/usr/bin/env python3
"""Validate the structure and core invariants of this skill without external dependencies."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
LINK_RE = re.compile(r"\]\(([^)]+)\)")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter.")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration as exc:
        raise ValueError("SKILL.md frontmatter is not closed.") from exc

    data: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"Invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data, "\n".join(lines[end + 1 :])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_root", nargs="?", default=".")
    args = parser.parse_args()

    root = Path(args.skill_root).resolve()
    errors: list[str] = []
    warnings: list[str] = []

    required = [
        "SKILL.md",
        "README.md",
        "VERSION",
        "CHANGELOG.md",
        "agents/openai.yaml",
        "references/operating-model.md",
        "references/parallel-execution.md",
        "references/risk-classification.md",
        "references/commercial-quality-gates.md",
        "references/security-and-ai-safety.md",
        "references/observability-release-operations.md",
        "references/practice-radar.md",
        "references/self-evolution-protocol.md",
        "references/standards-map.md",
        "evals/trigger_cases.csv",
        "evals/behavior_cases.md",
        "evals/rubric.md",
        "assets/project-template/docs/plans/PARALLEL_EXECUTION_BOARD.md",
        "scripts/bootstrap_governance.py",
        "scripts/score_practice_candidate.py",
        "tests/test_bootstrap_governance.py",
        "tests/test_validate_skill.py",
    ]
    for rel in required:
        if not (root / rel).is_file():
            errors.append(f"Missing required file: {rel}")

    skill_path = root / "SKILL.md"
    if skill_path.is_file():
        text = skill_path.read_text(encoding="utf-8")
        try:
            frontmatter, body = parse_frontmatter(text)
            if set(frontmatter) != {"name", "description"}:
                errors.append("Frontmatter must contain only name and description.")
            name = frontmatter.get("name", "")
            desc = frontmatter.get("description", "")
            if not NAME_RE.fullmatch(name):
                errors.append(f"Invalid skill name: {name!r}")
            if root.name != name:
                errors.append(f"Folder name {root.name!r} must equal skill name {name!r}.")
            if len(desc) < 80:
                warnings.append("Description may be too short to trigger reliably.")
            body_lines = len(body.splitlines())
            if body_lines > 500:
                errors.append(f"SKILL.md body has {body_lines} lines; keep it at or below 500.")
            if "If governance scaffolding is absent, run:" in body:
                errors.append("SKILL.md contains an unconditional auto-bootstrap policy.")
            for guard in (
                "Bootstrap mode or the user explicitly authorizes",
                "--dry-run",
                "do not write scaffolding",
            ):
                if guard not in body:
                    errors.append(f"SKILL.md missing bootstrap authorization guard: {guard}")

            for link in LINK_RE.findall(body):
                if "://" in link or link.startswith("#"):
                    continue
                target = (root / link.split("#", 1)[0]).resolve()
                if not target.exists():
                    errors.append(f"Broken local link in SKILL.md: {link}")
        except ValueError as exc:
            errors.append(str(exc))

    yaml_path = root / "agents" / "openai.yaml"
    if yaml_path.is_file() and skill_path.is_file():
        yaml_text = yaml_path.read_text(encoding="utf-8")
        try:
            name = parse_frontmatter(skill_path.read_text(encoding="utf-8"))[0]["name"]
            if f"${name}" not in yaml_text:
                errors.append("agents/openai.yaml default_prompt must mention the skill by $name.")
        except Exception:
            pass
        for key in ("display_name:", "short_description:", "default_prompt:"):
            if key not in yaml_text:
                errors.append(f"agents/openai.yaml missing {key}")

    csv_path = root / "evals" / "trigger_cases.csv"
    if csv_path.is_file():
        with csv_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) < 10:
            errors.append("Maintain at least 10 focused trigger eval cases.")
        required_cols = {"id", "should_trigger", "prompt"}
        if rows and not required_cols.issubset(rows[0]):
            errors.append("trigger_cases.csv must include id, should_trigger, and prompt.")

    behavior_path = root / "evals" / "behavior_cases.md"
    if behavior_path.is_file():
        behavior_text = behavior_path.read_text(encoding="utf-8")
        if "Run or propose bootstrap script." in behavior_text:
            errors.append("behavior_cases.md contains unconditional bootstrap behavior.")
        for heading in (
            "## Case 11 — Parallelizable feature",
            "## Case 12 — Unsafe parallel request",
            "## Case 13 — Read-only work without governance scaffolding",
            "## Case 14 — Authorized governance bootstrap",
        ):
            if heading not in behavior_text:
                errors.append(f"behavior_cases.md missing required heading: {heading}")

    board_path = root / "assets" / "project-template" / "docs" / "plans" / "PARALLEL_EXECUTION_BOARD.md"
    if board_path.is_file():
        board_text = board_path.read_text(encoding="utf-8")
        for field in (
            "Inputs",
            "Outputs",
            "Acceptance criteria",
            "Forbidden scope",
            "Required checks",
            "Environment namespace",
            "Stop conditions",
            "Allowed tools and external actions",
            "Credential and data scope",
            "Approval owner",
        ):
            if field not in board_text:
                errors.append(f"Parallel execution board missing required field: {field}")

    version_path = root / "VERSION"
    changelog_path = root / "CHANGELOG.md"
    if version_path.is_file() and changelog_path.is_file():
        version = version_path.read_text(encoding="utf-8").strip()
        if not re.fullmatch(r"\d+\.\d+\.\d+", version):
            errors.append(f"VERSION must use semantic versioning: {version!r}")
        changelog_text = changelog_path.read_text(encoding="utf-8")
        if not re.search(rf"^## {re.escape(version)}(?:\s|$)", changelog_text, re.MULTILINE):
            errors.append(f"CHANGELOG.md missing current version heading: {version}")

    if errors:
        print("Skill validation FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        for warning in warnings:
            print(f"WARNING: {warning}")
        return 1

    print("Skill validation PASSED")
    for warning in warnings:
        print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
