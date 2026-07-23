from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "bootstrap_governance.py"


def run_bootstrap(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
    )


class BootstrapGovernanceTests(unittest.TestCase):
    def test_dry_run_does_not_create_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "new-project"

            result = run_bootstrap("--target", str(target), "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(target.exists())

    def test_copies_template_into_a_new_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "new-project"

            result = run_bootstrap("--target", str(target))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertIn("14 file(s) copied.", result.stdout)

    def test_refuses_to_overwrite_an_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "project"
            target.mkdir()
            sentinel = target / "AGENTS.md"
            sentinel.write_text("keep me", encoding="utf-8")

            result = run_bootstrap("--target", str(target))

            self.assertEqual(result.returncode, 1)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep me")
            self.assertIn("Refusing to overwrite existing files", result.stderr)

    def test_refuses_symlinked_parent_even_with_force(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "project"
            outside = root / "outside"
            target.mkdir()
            outside.mkdir()
            (target / "docs").symlink_to(outside, target_is_directory=True)

            result = run_bootstrap("--target", str(target), "--force")

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((outside / "product" / "PRODUCT.md").exists())
            self.assertIn("symbolic link", result.stderr)

    def test_refuses_dangling_destination_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "project"
            outside = root / "outside"
            destination_parent = target / "docs" / "product"
            destination_parent.mkdir(parents=True)
            outside.mkdir()
            destination = destination_parent / "PRODUCT.md"
            destination.symlink_to(outside / "missing.md")

            result = run_bootstrap("--target", str(target))

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((outside / "missing.md").exists())
            self.assertIn("symbolic link", result.stderr)


if __name__ == "__main__":
    unittest.main()
