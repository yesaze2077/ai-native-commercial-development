#!/usr/bin/env python3
"""Validate the structure and core invariants of this skill without external dependencies."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
LINK_RE = re.compile(r"\]\(([^)]+)\)")
ANTHROPIC_SOURCE_URL = "https://claude.com/blog/the-ai-native-sdlc-playbook"
ANTHROPIC_SOURCE_BODY_SHA256 = (
    "2a8450b3c847c602251fd0e46a8172f2f2186023aa9f6c8583b439130395f12a"
)
SECRET_PATTERNS = {
    "private-key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "aws-access-key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "slack-token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "bearer-jwt": re.compile(r"(?i)\bBearer\s+eyJ[A-Za-z0-9_-]{20,}"),
}


def behavior_configuration_digest(skill_root: Path) -> str:
    candidates = [skill_root / "SKILL.md", skill_root / "agents" / "openai.yaml"]
    for pattern in (
        "references/**/*.md",
        "assets/project-template/**/*",
        "evals/behavior_cases.md",
        "evals/behavior_contracts.json",
        "evals/rubric.md",
        "evals/trigger_cases.csv",
        ".github/workflows/*.yml",
        ".github/workflows/*.yaml",
        "scripts/*.py",
    ):
        candidates.extend(skill_root.glob(pattern))
    files = sorted({path.resolve() for path in candidates if path.is_file()})
    digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(skill_root.resolve()).as_posix().encode("utf-8")
        data = path.read_bytes()
        digest.update(relative)
        digest.update(b"\0")
        digest.update(str(len(data)).encode("ascii"))
        digest.update(b"\0")
        digest.update(data)
        digest.update(b"\0")
    return digest.hexdigest()


def reject_duplicate_object_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def evaluate_contract(
    case: dict[str, object],
    response: str,
    global_forbidden: list[dict[str, object]],
) -> dict[str, object]:
    required = case.get("required_patterns", [])
    forbidden = case.get("forbidden_patterns", [])
    missing_required = [
        str(check.get("id"))
        for check in required
        if isinstance(check, dict)
        and re.search(str(check.get("pattern", "")), response) is None
    ]
    forbidden_matches = [
        str(check.get("id"))
        for check in [*global_forbidden, *forbidden]
        if isinstance(check, dict)
        and re.search(str(check.get("pattern", "")), response) is not None
    ]
    secret_matches = [
        name for name, pattern in SECRET_PATTERNS.items() if pattern.search(response)
    ]
    return {
        "passed": not missing_required and not forbidden_matches and not secret_matches,
        "missing_required": missing_required,
        "forbidden_matches": forbidden_matches,
        "secret_matches": secret_matches,
    }


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
        "evals/behavior_contracts.json",
        "evals/rubric.md",
        "governance/3.0.0-change-evidence.md",
        "governance/practice-candidates/anthropic-ai-native-sdlc-source-claims.txt",
        "governance/practice-candidates/anthropic-ai-native-sdlc-source-content.json",
        "governance/practice-candidates/anthropic-ai-native-sdlc-core.json",
        "governance/practice-candidates/anthropic-ai-native-sdlc-core.md",
        "governance/practice-candidates/anthropic-ai-native-sdlc-control-bands.json",
        "governance/practice-candidates/anthropic-ai-native-sdlc-control-bands.md",
        "governance/rollback/ai-native-commercial-development-2.0.0.zip",
        "governance/rollback/ai-native-commercial-development-2.0.0.sha256",
        ".github/workflows/validate-skill.yml",
        "assets/project-template/docs/intents/INTENT_TEMPLATE.md",
        "assets/project-template/docs/governance/ARTIFACT_LINEAGE.md",
        "assets/project-template/docs/governance/REVIEW_POLICY.md",
        "assets/project-template/docs/governance/GUARDRAIL_CONTRACT.md",
        "assets/project-template/docs/operations/AUTONOMY_BANDS.yaml",
        "assets/project-template/docs/plans/PARALLEL_EXECUTION_BOARD.md",
        "scripts/bootstrap_governance.py",
        "scripts/run_behavior_evals.py",
        "scripts/score_practice_candidate.py",
        "tests/test_bootstrap_governance.py",
        "tests/test_behavior_evals.py",
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
                "one authoritative system for each artifact",
                "run_behavior_evals.py",
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

    workflow_path = root / ".github" / "workflows" / "validate-skill.yml"
    if workflow_path.is_file():
        workflow_text = workflow_path.read_text(encoding="utf-8")
        for required_control in (
            "environment: semantic-governance-review",
            "SEMANTIC_REVIEW_TRUST_CONFIGURED",
            "Require out-of-band semantic-review trust",
            "--require-semantic-review",
        ):
            if required_control not in workflow_text:
                errors.append(
                    f"CI workflow missing semantic trust control: {required_control}"
                )

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
            "## Case 15 — External system is authoritative",
            "## Case 16 — Mandatory policy needs a hard guardrail",
            "## Case 17 — Semantic skill change",
            "## Case 18 — Production control band",
        ):
            if heading not in behavior_text:
                errors.append(f"behavior_cases.md missing required heading: {heading}")

    behavior_contracts_path = root / "evals" / "behavior_contracts.json"
    behavior_contracts: dict[str, object] = {"cases": []}
    if behavior_contracts_path.is_file():
        try:
            behavior_contracts = json.loads(
                behavior_contracts_path.read_text(encoding="utf-8")
            )
            cases = behavior_contracts.get("cases", [])
            global_forbidden = behavior_contracts.get("global_forbidden_patterns", [])
            if behavior_contracts.get("schema_version") != 1:
                errors.append("behavior_contracts.json schema_version must be 1.")
            if not isinstance(global_forbidden, list) or not global_forbidden:
                errors.append("behavior_contracts.json needs global_forbidden_patterns.")
            if len(cases) < 10:
                errors.append("Maintain at least 10 executable behavior contracts.")
            case_ids = [case.get("id") for case in cases if isinstance(case, dict)]
            if len(case_ids) != len(set(case_ids)):
                errors.append("behavior_contracts.json case ids must be unique.")
            for required_case in (
                "external-authority-lineage",
                "mandatory-policy-guardrail",
                "control-band-safe-default",
                "semantic-skill-change-evals",
            ):
                if required_case not in case_ids:
                    errors.append(
                        f"behavior_contracts.json missing required case: {required_case}"
                    )
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Invalid behavior_contracts.json: {exc}")

    claims_path = (
        root
        / "governance"
        / "practice-candidates"
        / "anthropic-ai-native-sdlc-source-claims.txt"
    )
    expected_claims_digest = (
        hashlib.sha256(claims_path.read_bytes()).hexdigest()
        if claims_path.is_file()
        else None
    )
    source_content_path = (
        root
        / "governance"
        / "practice-candidates"
        / "anthropic-ai-native-sdlc-source-content.json"
    )
    source_content: dict[str, object] = {}
    if source_content_path.is_file():
        try:
            source_content = json.loads(source_content_path.read_text(encoding="utf-8"))
            if source_content.get("schema_version") != 1:
                errors.append("Source content evidence schema_version must be 1.")
            if source_content.get("source_url") != ANTHROPIC_SOURCE_URL:
                errors.append("Source content evidence has an unexpected source_url.")
            if source_content.get("final_url") != ANTHROPIC_SOURCE_URL:
                errors.append("Source content evidence has an unexpected final_url.")
            if source_content.get("http_status") != 200:
                errors.append("Source content evidence HTTP status is not 200.")
            if source_content.get("body_sha256") != ANTHROPIC_SOURCE_BODY_SHA256:
                errors.append("Source body digest does not match captured release evidence.")
            if not isinstance(source_content.get("body_bytes"), int) or source_content["body_bytes"] < 100000:
                errors.append("Source content evidence body_bytes is implausible.")
            if source_content.get("repeated_fetches", 0) < 2:
                errors.append("Source content evidence needs at least two fetches.")
            if source_content.get("identical_repeated_fetches") is not True:
                errors.append("Repeated source content fetches did not match.")
            if source_content.get("raw_body_retained") is not False:
                errors.append("Source content evidence must declare raw_body_retained false.")
            if source_content.get("claims_sha256") != expected_claims_digest:
                errors.append("Source content evidence claim digest does not match.")
            for field in (
                "captured_at",
                "capture_method",
                "content_type",
                "last_modified",
                "retention_reason",
                "verification",
            ):
                if not isinstance(source_content.get(field), str) or not source_content[field].strip():
                    errors.append(f"Source content evidence needs non-empty {field}.")
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            errors.append(f"Invalid source content evidence: {exc}")
    for candidate_name in (
        "anthropic-ai-native-sdlc-core.json",
        "anthropic-ai-native-sdlc-control-bands.json",
    ):
        candidate_path = root / "governance" / "practice-candidates" / candidate_name
        if not candidate_path.is_file():
            continue
        try:
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            if candidate.get("source_url") != ANTHROPIC_SOURCE_URL:
                errors.append(f"{candidate_name} has an unexpected source_url.")
            if candidate.get("source_tier") != "S":
                errors.append(f"{candidate_name} source_tier must be S.")
            if candidate.get("source_claims_sha256") != expected_claims_digest:
                errors.append(f"{candidate_name} source claim digest does not match.")
            if candidate.get("source_content_evidence_path") != (
                "governance/practice-candidates/"
                "anthropic-ai-native-sdlc-source-content.json"
            ):
                errors.append(f"{candidate_name} source content evidence path does not match.")
            if candidate.get("source_body_sha256") != source_content.get("body_sha256"):
                errors.append(f"{candidate_name} source content digest does not match.")
            if candidate.get("source_body_bytes") != source_content.get("body_bytes"):
                errors.append(f"{candidate_name} source content byte count does not match.")
            if candidate.get("source_last_modified") != source_content.get("last_modified"):
                errors.append(f"{candidate_name} source last-modified value does not match.")
            if candidate_name.endswith("control-bands.json"):
                if candidate.get("state") != "experimental" or candidate.get("risk") != 3:
                    errors.append(
                        "Production control-band candidate must remain experimental and R3."
                    )
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Invalid practice candidate {candidate_name}: {exc}")

    rollback_archive = (
        root / "governance" / "rollback" / "ai-native-commercial-development-2.0.0.zip"
    )
    rollback_digest_path = (
        root / "governance" / "rollback" / "ai-native-commercial-development-2.0.0.sha256"
    )
    if rollback_archive.is_file() and rollback_digest_path.is_file():
        try:
            digest_parts = rollback_digest_path.read_text(encoding="utf-8").split()
            if len(digest_parts) != 2 or digest_parts[1] != rollback_archive.name:
                raise ValueError("rollback checksum file has an invalid format")
            actual_rollback_digest = hashlib.sha256(rollback_archive.read_bytes()).hexdigest()
            if digest_parts[0] != actual_rollback_digest:
                errors.append("Bundled rollback archive checksum does not match.")
            with zipfile.ZipFile(rollback_archive) as archive:
                corrupt = archive.testzip()
                if corrupt is not None:
                    errors.append(f"Bundled rollback archive has a corrupt member: {corrupt}")
                version_members = [
                    name
                    for name in archive.namelist()
                    if name.endswith("/VERSION") and not name.startswith("__MACOSX/")
                ]
                if len(version_members) != 1:
                    errors.append("Bundled rollback archive must contain exactly one VERSION file.")
                elif archive.read(version_members[0]).decode("utf-8").strip() != "2.0.0":
                    errors.append("Bundled rollback archive is not version 2.0.0.")
        except (OSError, ValueError, UnicodeDecodeError, zipfile.BadZipFile) as exc:
            errors.append(f"Invalid bundled rollback archive: {exc}")

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

    template_requirements = {
        "assets/project-template/docs/intents/INTENT_TEMPLATE.md": (
            "Artifact ID",
            "Authoritative system",
            "Authoritative record ID",
            "Stable version-pinned source reference",
            "Approval evidence",
            "Problem in the originator's words",
        ),
        "assets/project-template/docs/governance/ARTIFACT_LINEAGE.md": (
            "Parent artifact",
            "Authoritative system",
            "Stable record ID or path",
            "Snapshot/digest/commit",
            "Approval evidence",
            "Reconciliation log",
        ),
        "assets/project-template/docs/governance/REVIEW_POLICY.md": (
            "Reviewer separation",
            "Correctness",
            "Security and operations",
            "Traceability and design",
            "Report at most five Nits",
            "Verdict",
        ),
        "assets/project-template/docs/governance/GUARDRAIL_CONTRACT.md": (
            "Deterministic mechanism",
            "Enforcement point",
            "Denied action or fail mode",
            "Evidence event/artifact",
            "Break-glass approval",
            "Fail-open behavior",
        ),
    }
    for relative, fields in template_requirements.items():
        path = root / relative
        if not path.is_file():
            continue
        template_text = path.read_text(encoding="utf-8")
        for field in fields:
            if field not in template_text:
                errors.append(f"{relative} missing required field: {field}")

    bands_path = root / "assets" / "project-template" / "docs" / "operations" / "AUTONOMY_BANDS.yaml"
    if bands_path.is_file():
        try:
            bands_config = json.loads(
                bands_path.read_text(encoding="utf-8"),
                object_pairs_hook=reject_duplicate_object_pairs,
            )
            if bands_config.get("schema_version") != 1:
                errors.append("AUTONOMY_BANDS.yaml schema_version must be 1.")
            if bands_config.get("status") != "disabled":
                errors.append("AUTONOMY_BANDS.yaml must start with status disabled.")
            if bands_config.get("active_tier") != "disabled":
                errors.append("AUTONOMY_BANDS.yaml must start with active_tier disabled.")
            detector = bands_config.get("detector", {})
            if not isinstance(detector, dict) or detector.get("deterministic") is not True:
                errors.append("AUTONOMY_BANDS.yaml detector must be deterministic.")
            bands = bands_config.get("bands", {})
            if not isinstance(bands, dict) or set(bands) != {
                "observe",
                "diagnose",
                "propose",
                "runbook",
            }:
                errors.append("AUTONOMY_BANDS.yaml must define the four controlled tiers.")
            elif any(
                not isinstance(config, dict) or config.get("enabled") is not False
                for config in bands.values()
            ):
                errors.append("AUTONOMY_BANDS.yaml tiers must all start disabled.")
            production = bands_config.get("production", {})
            expected_production = {
                "direct_mutation": False,
                "automatic_deploy": False,
                "automatic_rollback": False,
                "require_human_approval": True,
            }
            if not isinstance(production, dict) or any(
                production.get(key) is not value
                for key, value in expected_production.items()
            ):
                errors.append("AUTONOMY_BANDS.yaml production defaults are unsafe.")
            if not isinstance(bands_config.get("transition"), dict):
                errors.append("AUTONOMY_BANDS.yaml must define transition evidence.")
            if not isinstance(bands_config.get("kill_switch"), dict):
                errors.append("AUTONOMY_BANDS.yaml must define a kill switch.")
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append(f"Invalid JSON-compatible AUTONOMY_BANDS.yaml: {exc}")

    version_path = root / "VERSION"
    changelog_path = root / "CHANGELOG.md"
    if version_path.is_file() and changelog_path.is_file():
        version = version_path.read_text(encoding="utf-8").strip()
        if not re.fullmatch(r"\d+\.\d+\.\d+", version):
            errors.append(f"VERSION must use semantic versioning: {version!r}")
        changelog_text = changelog_path.read_text(encoding="utf-8")
        if not re.search(rf"^## {re.escape(version)}(?:\s|$)", changelog_text, re.MULTILINE):
            errors.append(f"CHANGELOG.md missing current version heading: {version}")

        evidence_root = root / "evals" / "evidence" / version
        evidence_report_path = evidence_root / "report.json"
        semantic_review_path = evidence_root / "semantic-review.json"
        responses_root = evidence_root / "responses"
        if not evidence_report_path.is_file():
            errors.append(
                f"Missing versioned behavior evidence report: evals/evidence/{version}/report.json"
            )
        elif not responses_root.is_dir():
            errors.append(
                f"Missing versioned behavior responses: evals/evidence/{version}/responses"
            )
        elif not skill_path.is_file() or not behavior_contracts_path.is_file():
            pass
        else:
            try:
                evidence_report = json.loads(
                    evidence_report_path.read_text(encoding="utf-8")
                )
                if evidence_report.get("skill_version") != version:
                    errors.append("Behavior evidence report does not match VERSION.")
                if evidence_report.get("contract_passed") is not True:
                    errors.append("Behavior evidence contract gate is not passing.")
                if evidence_report.get("behavior_passed") is not True:
                    errors.append("Behavior evidence semantic gate is not passing.")
                if evidence_report.get("suite_passed") is not True:
                    errors.append("Behavior evidence report is not passing.")

                expected_skill_digest = behavior_configuration_digest(root)
                evidence_metadata = evidence_report.get("metadata", {})
                if not isinstance(evidence_metadata, dict):
                    raise ValueError("Behavior evidence metadata must be an object.")
                recorded_skill_digest = evidence_metadata.get("configuration_digest")
                if recorded_skill_digest != expected_skill_digest:
                    errors.append(
                        "Behavior evidence configuration_digest does not match behavior-steering files."
                    )

                expected_manifest_digest = hashlib.sha256(
                    behavior_contracts_path.read_bytes()
                ).hexdigest()
                if evidence_report.get("manifest_sha256") != expected_manifest_digest:
                    errors.append(
                        "Behavior evidence manifest_sha256 does not match behavior_contracts.json."
                    )

                evidence_cases = evidence_report.get("cases", [])
                if not isinstance(evidence_cases, list):
                    raise ValueError("Behavior evidence cases must be a list.")
                report_cases = {
                    case.get("id"): case
                    for case in evidence_cases
                    if isinstance(case, dict)
                }
                if len(report_cases) != len(evidence_cases):
                    errors.append(
                        "Behavior evidence report contains invalid or duplicate case ids."
                    )
                manifest_cases = behavior_contracts.get("cases", [])
                if not isinstance(manifest_cases, list):
                    raise ValueError("Behavior contract cases must be a list.")
                manifest_case_ids = {
                    case.get("id") for case in manifest_cases if isinstance(case, dict)
                }
                if set(report_cases) != manifest_case_ids:
                    errors.append(
                        "Behavior evidence report and manifest case ids do not match exactly."
                    )
                global_forbidden = behavior_contracts.get(
                    "global_forbidden_patterns", []
                )
                if not isinstance(global_forbidden, list):
                    raise ValueError("Global forbidden patterns must be a list.")
                for case in manifest_cases:
                    case_id = case.get("id")
                    candidates = [
                        responses_root / f"{case_id}.txt",
                        responses_root / f"{case_id}.md",
                    ]
                    response_files = [
                        path for path in candidates if path.is_file() and not path.is_symlink()
                    ]
                    if len(response_files) != 1:
                        errors.append(
                            f"Behavior evidence case {case_id} needs exactly one raw response."
                        )
                        continue
                    response_bytes = response_files[0].read_bytes()
                    actual_digest = hashlib.sha256(response_bytes).hexdigest()
                    recorded_digest = report_cases.get(case_id, {}).get(
                        "response_sha256"
                    )
                    if actual_digest != recorded_digest:
                        errors.append(
                            f"Behavior evidence response digest mismatch: {case_id}"
                        )
                    response = response_bytes.decode("utf-8")
                    recomputed = evaluate_contract(case, response, global_forbidden)
                    recorded_case = report_cases.get(case_id, {})
                    for field in (
                        "passed",
                        "missing_required",
                        "forbidden_matches",
                        "secret_matches",
                    ):
                        if recorded_case.get(field) != recomputed[field]:
                            errors.append(
                                f"Behavior evidence recorded {field} does not match recomputation: {case_id}"
                            )
                    if recomputed["passed"] is not True:
                        errors.append(
                            f"Behavior evidence case fails recomputation: {case_id}"
                        )

                if not semantic_review_path.is_file():
                    errors.append(
                        f"Missing semantic review: evals/evidence/{version}/semantic-review.json"
                    )
                else:
                    semantic_review = json.loads(
                        semantic_review_path.read_text(encoding="utf-8")
                    )
                    if semantic_review.get("schema_version") != 1:
                        errors.append("Semantic review schema_version must be 1.")
                    if semantic_review.get("skill_version") != version:
                        errors.append("Semantic review does not match VERSION.")
                    if semantic_review.get("manifest_sha256") != expected_manifest_digest:
                        errors.append("Semantic review manifest digest does not match.")
                    for field in (
                        "reviewed_at",
                        "reviewer_context",
                        "reviewer_id",
                        "method",
                        "limitations",
                    ):
                        if not isinstance(semantic_review.get(field), str) or not semantic_review[field].strip():
                            errors.append(f"Semantic review needs non-empty {field}.")
                    semantic_cases_raw = semantic_review.get("cases", [])
                    if not isinstance(semantic_cases_raw, list):
                        raise ValueError("Semantic review cases must be a list.")
                    semantic_cases = {
                        case.get("id"): case
                        for case in semantic_cases_raw
                        if isinstance(case, dict)
                    }
                    if len(semantic_cases) != len(semantic_cases_raw):
                        errors.append(
                            "Semantic review contains invalid or duplicate case ids."
                        )
                    if set(semantic_cases) != manifest_case_ids:
                        errors.append(
                            "Semantic review and manifest case ids do not match exactly."
                        )
                    for case_id in manifest_case_ids:
                        semantic_case = semantic_cases.get(case_id, {})
                        if semantic_case.get("response_sha256") != report_cases.get(
                            case_id, {}
                        ).get("response_sha256"):
                            errors.append(
                                f"Semantic review response digest mismatch: {case_id}"
                            )
                        if semantic_case.get("passed") is not True:
                            errors.append(f"Semantic review case is not passing: {case_id}")
                        if not isinstance(semantic_case.get("findings"), list):
                            errors.append(
                                f"Semantic review case needs findings list: {case_id}"
                            )
                        elif not all(
                            isinstance(finding, str)
                            for finding in semantic_case["findings"]
                        ):
                            errors.append(
                                f"Semantic review findings must be strings: {case_id}"
                            )
                    if semantic_review.get("overall_passed") is not True:
                        errors.append("Semantic review overall_passed is not true.")
                    semantic_summary = evidence_report.get("semantic_review", {})
                    if not isinstance(semantic_summary, dict):
                        errors.append("Behavior report semantic_review must be an object.")
                    else:
                        semantic_digest = hashlib.sha256(
                            semantic_review_path.read_bytes()
                        ).hexdigest()
                        if semantic_summary.get("sha256") != semantic_digest:
                            errors.append(
                                "Behavior report semantic review digest does not match."
                            )
            except (OSError, json.JSONDecodeError, TypeError, ValueError, re.error) as exc:
                errors.append(f"Invalid versioned behavior evidence: {exc}")

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
