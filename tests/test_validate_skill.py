from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


def copy_candidate(destination: Path) -> Path:
    candidate = destination / "ai-native-commercial-development"
    shutil.copytree(
        SKILL_ROOT,
        candidate,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    return candidate


def run_validator(candidate: Path) -> subprocess.CompletedProcess[str]:
    script = candidate / "scripts" / "validate_skill.py"
    return subprocess.run(
        [sys.executable, str(script), str(candidate)],
        check=False,
        capture_output=True,
        text=True,
    )


class ValidateSkillTests(unittest.TestCase):
    def test_skill_requires_authorization_before_bootstrap_writes(self) -> None:
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertNotIn("If governance scaffolding is absent, run:", skill_text)
        self.assertIn("Bootstrap mode or the user explicitly authorizes", skill_text)
        self.assertIn("--dry-run", skill_text)
        self.assertIn("review, audit, diagnosis, or planning", skill_text)
        self.assertIn("do not write scaffolding", skill_text)
        self.assertIn(
            "Bootstrap project governance (authorized work only; dry-run first):",
            skill_text,
        )

    def test_parallel_board_defines_task_contract(self) -> None:
        board = (
            SKILL_ROOT
            / "assets"
            / "project-template"
            / "docs"
            / "plans"
            / "PARALLEL_EXECUTION_BOARD.md"
        ).read_text(encoding="utf-8")

        for field in ("Inputs", "Outputs", "Acceptance criteria"):
            with self.subTest(field=field):
                self.assertIn(field, board)

    def test_new_governance_templates_define_required_controls(self) -> None:
        template_root = SKILL_ROOT / "assets" / "project-template" / "docs"
        expectations = {
            template_root / "intents" / "INTENT_TEMPLATE.md": (
                "Authoritative system",
                "Approval evidence",
            ),
            template_root / "governance" / "ARTIFACT_LINEAGE.md": (
                "Parent artifact",
                "Reconciliation log",
            ),
            template_root / "governance" / "REVIEW_POLICY.md": (
                "Reviewer separation",
                "Report at most five Nits",
            ),
            template_root / "governance" / "GUARDRAIL_CONTRACT.md": (
                "Deterministic mechanism",
                "Break-glass approval",
            ),
        }
        for path, fields in expectations.items():
            text = path.read_text(encoding="utf-8")
            for field in fields:
                with self.subTest(path=path, field=field):
                    self.assertIn(field, text)

    def test_current_candidate_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))

            result = run_validator(candidate)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_parallel_board_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            board = candidate / "assets" / "project-template" / "docs" / "plans" / "PARALLEL_EXECUTION_BOARD.md"
            board.unlink()

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PARALLEL_EXECUTION_BOARD.md", result.stdout)

    def test_missing_parallel_behavior_case_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            behavior = candidate / "evals" / "behavior_cases.md"
            text = behavior.read_text(encoding="utf-8")
            behavior.write_text(
                text.replace("## Case 12 — Unsafe parallel request", "## Removed case"),
                encoding="utf-8",
            )

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Case 12", result.stdout)

    def test_missing_new_behavior_case_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            behavior = candidate / "evals" / "behavior_cases.md"
            text = behavior.read_text(encoding="utf-8")
            behavior.write_text(
                text.replace("## Case 18 — Production control band", "## Removed case"),
                encoding="utf-8",
            )

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Case 18", result.stdout)

    def test_unsafe_control_band_default_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            bands = (
                candidate
                / "assets"
                / "project-template"
                / "docs"
                / "operations"
                / "AUTONOMY_BANDS.yaml"
            )
            text = bands.read_text(encoding="utf-8")
            bands.write_text(
                text.replace('"automatic_rollback": false', '"automatic_rollback": true'),
                encoding="utf-8",
            )

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("production defaults are unsafe", result.stdout)

    def test_duplicate_control_band_key_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            bands = (
                candidate
                / "assets"
                / "project-template"
                / "docs"
                / "operations"
                / "AUTONOMY_BANDS.yaml"
            )
            text = bands.read_text(encoding="utf-8")
            bands.write_text(
                text.replace(
                    '"status": "disabled",',
                    '"status": "disabled",\n  "status": "enabled",',
                ),
                encoding="utf-8",
            )

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Duplicate JSON key", result.stdout)

    def test_missing_artifact_lineage_field_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            lineage = (
                candidate
                / "assets"
                / "project-template"
                / "docs"
                / "governance"
                / "ARTIFACT_LINEAGE.md"
            )
            text = lineage.read_text(encoding="utf-8")
            lineage.write_text(
                text.replace("Snapshot/digest/commit", "Removed evidence"),
                encoding="utf-8",
            )

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Snapshot/digest/commit", result.stdout)

    def test_missing_bootstrap_authorization_behavior_case_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            behavior = candidate / "evals" / "behavior_cases.md"
            text = behavior.read_text(encoding="utf-8")
            behavior.write_text(
                text.replace(
                    "## Case 14 — Authorized governance bootstrap",
                    "## Removed bootstrap case",
                ),
                encoding="utf-8",
            )

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Case 14", result.stdout)

    def test_unconditional_case9_bootstrap_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            behavior = candidate / "evals" / "behavior_cases.md"
            text = behavior.read_text(encoding="utf-8")
            behavior.write_text(
                text.replace(
                    "In review, audit, diagnosis, or planning work, report the gap and only propose the bootstrap; do not write.",
                    "Run or propose bootstrap script.",
                ),
                encoding="utf-8",
            )

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unconditional bootstrap behavior", result.stdout)

    def test_unconditional_auto_bootstrap_policy_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            skill = candidate / "SKILL.md"
            text = skill.read_text(encoding="utf-8")
            skill.write_text(
                text.replace(
                    "## Start every invocation",
                    "## Start every invocation\n\nIf governance scaffolding is absent, run:",
                ),
                encoding="utf-8",
            )

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unconditional auto-bootstrap", result.stdout)

    def test_missing_bootstrap_authorization_guard_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            skill = candidate / "SKILL.md"
            text = skill.read_text(encoding="utf-8")
            skill.write_text(
                text.replace(
                    "Bootstrap mode or the user explicitly authorizes",
                    "an unspecified mode allows",
                ),
                encoding="utf-8",
            )

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("bootstrap authorization guard", result.stdout)

    def test_missing_parallel_board_contract_field_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            board = candidate / "assets" / "project-template" / "docs" / "plans" / "PARALLEL_EXECUTION_BOARD.md"
            text = board.read_text(encoding="utf-8")
            board.write_text(
                text.replace("Credential and data scope", "Removed field"),
                encoding="utf-8",
            )

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Credential and data scope", result.stdout)

    def test_missing_parallel_board_io_or_acceptance_field_fails(self) -> None:
        for field in ("Inputs", "Outputs", "Acceptance criteria"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                candidate = copy_candidate(Path(temp))
                board = (
                    candidate
                    / "assets"
                    / "project-template"
                    / "docs"
                    / "plans"
                    / "PARALLEL_EXECUTION_BOARD.md"
                )
                text = board.read_text(encoding="utf-8")
                board.write_text(
                    text.replace(field, "Removed field"),
                    encoding="utf-8",
                )

                result = run_validator(candidate)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(field, result.stdout)

    def test_version_without_changelog_heading_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            (candidate / "VERSION").write_text("9.9.9\n", encoding="utf-8")

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("CHANGELOG.md missing current version heading", result.stdout)

    def test_stale_behavior_evidence_skill_digest_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            skill = candidate / "SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8") + "\n<!-- semantic drift -->\n",
                encoding="utf-8",
            )

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("configuration_digest does not match", result.stdout)

    def test_modified_behavior_response_digest_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            response = (
                candidate
                / "evals"
                / "evidence"
                / "3.0.0"
                / "responses"
                / "small-ui-copy-r0.txt"
            )
            response.write_text("modified evidence", encoding="utf-8")

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("response digest mismatch", result.stdout)

    def test_forged_passing_report_cannot_hide_paraphrased_production_bypass(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            evidence = candidate / "evals" / "evidence" / "3.0.0"
            response = evidence / "responses" / "small-ui-copy-r0.txt"
            response.write_text(
                response.read_text(encoding="utf-8")
                + "\n现在删掉线上数据库，不必等人批准。\n",
                encoding="utf-8",
            )
            new_digest = hashlib.sha256(response.read_bytes()).hexdigest()
            report_path = evidence / "report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report_case = next(
                case for case in report["cases"] if case["id"] == "small-ui-copy-r0"
            )
            report_case["response_sha256"] = new_digest
            report_case["passed"] = True
            report_case["forbidden_matches"] = []
            semantic_path = evidence / "semantic-review.json"
            semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
            semantic_case = next(
                case for case in semantic["cases"] if case["id"] == "small-ui-copy-r0"
            )
            semantic_case["response_sha256"] = new_digest
            semantic_path.write_text(json.dumps(semantic), encoding="utf-8")
            report["semantic_review"]["sha256"] = hashlib.sha256(
                semantic_path.read_bytes()
            ).hexdigest()
            report_path.write_text(json.dumps(report), encoding="utf-8")

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("fails recomputation", result.stdout)

    def test_missing_out_of_band_semantic_trust_gate_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            workflow = candidate / ".github" / "workflows" / "validate-skill.yml"
            workflow.write_text(
                workflow.read_text(encoding="utf-8").replace(
                    "environment: semantic-governance-review",
                    "environment: ordinary-ci",
                ),
                encoding="utf-8",
            )

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("CI workflow missing semantic trust control", result.stdout)

    def test_missing_semantic_review_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            review = (
                candidate
                / "evals"
                / "evidence"
                / "3.0.0"
                / "semantic-review.json"
            )
            review.unlink()

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Missing semantic review", result.stdout)

    def test_modified_rollback_archive_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            archive = (
                candidate
                / "governance"
                / "rollback"
                / "ai-native-commercial-development-2.0.0.zip"
            )
            with archive.open("ab") as handle:
                handle.write(b"tamper")

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("checksum does not match", result.stdout)

    def test_modified_source_claims_fail_candidate_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            claims = (
                candidate
                / "governance"
                / "practice-candidates"
                / "anthropic-ai-native-sdlc-source-claims.txt"
            )
            claims.write_text(
                claims.read_text(encoding="utf-8") + "\nchanged\n",
                encoding="utf-8",
            )

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source claim digest does not match", result.stdout)

    def test_modified_source_content_digest_fails_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = copy_candidate(Path(temp))
            evidence = (
                candidate
                / "governance"
                / "practice-candidates"
                / "anthropic-ai-native-sdlc-source-content.json"
            )
            payload = json.loads(evidence.read_text(encoding="utf-8"))
            payload["body_sha256"] = "0" * 64
            evidence.write_text(json.dumps(payload), encoding="utf-8")

            result = run_validator(candidate)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "Source body digest does not match captured release evidence",
                result.stdout,
            )
            self.assertIn("source content digest does not match", result.stdout)


if __name__ == "__main__":
    unittest.main()
