from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
