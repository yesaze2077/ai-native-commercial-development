from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "bootstrap_governance.py"
MODULE_SPEC = importlib.util.spec_from_file_location("bootstrap_governance", SCRIPT)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
BOOTSTRAP_MODULE = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(BOOTSTRAP_MODULE)


def run_bootstrap(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
    )


class BootstrapGovernanceTests(unittest.TestCase):
    def test_fails_closed_without_secure_directory_primitives(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "new-project"
            stderr = io.StringIO()
            with (
                mock.patch.object(
                    BOOTSTRAP_MODULE,
                    "secure_dir_fd_supported",
                    return_value=False,
                ),
                mock.patch.object(
                    sys,
                    "argv",
                    [str(SCRIPT), "--target", str(target)],
                ),
                contextlib.redirect_stderr(stderr),
            ):
                result = BOOTSTRAP_MODULE.main()

            self.assertEqual(result, 2)
            self.assertFalse(target.exists())
            self.assertIn("Secure bootstrap writes require", stderr.getvalue())

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
            template_root = SKILL_ROOT / "assets" / "project-template"
            expected_count = sum(path.is_file() for path in template_root.rglob("*"))
            self.assertIn(f"{expected_count} file(s) copied.", result.stdout)

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

    def test_force_replaces_hardlink_without_modifying_peer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "project"
            target.mkdir()
            peer = root / "outside-AGENTS.md"
            peer.write_text("keep peer", encoding="utf-8")
            destination = target / "AGENTS.md"
            os.link(peer, destination)
            shared_inode = destination.stat().st_ino

            result = run_bootstrap("--target", str(target), "--force")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(peer.read_text(encoding="utf-8"), "keep peer")
            self.assertNotEqual(destination.stat().st_ino, shared_inode)
            expected = (SKILL_ROOT / "assets" / "project-template" / "AGENTS.md").read_text(encoding="utf-8")
            self.assertEqual(destination.read_text(encoding="utf-8"), expected)
            self.assertEqual(list(target.glob(".bootstrap-governance-*")), [])

    def test_failed_atomic_replace_removes_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "project"
            (target / "AGENTS.md").mkdir(parents=True)

            result = run_bootstrap("--target", str(target), "--force")

            self.assertNotEqual(result.returncode, 0)
            self.assertTrue((target / "AGENTS.md").is_dir())
            self.assertEqual(
                list(target.rglob(".bootstrap-governance-*")),
                [],
            )


if __name__ == "__main__":
    unittest.main()
