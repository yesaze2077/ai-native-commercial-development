from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_delivery_evidence.py"
REVISION = "a" * 40
OLD_REVISION = "b" * 40


class DeliveryEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "artifacts"
        self.root.mkdir()
        self.manifest = self.base / "manifest.json"
        self.artifact = self.make_artifact("checks/result.txt", "fixture result, not a product run\n")
        self.data = {
            "schema_version": 1,
            "revision": REVISION,
            "requirements": [{"id": "R1", "description": "Accepted fixture requirement",
                              "check_ids": ["C1"]}],
            "checks": [{"id": "C1", "category": "acceptance", "status": "passed",
                        "required_for": ["local", "release", "observation"],
                        "applies_to_revision": REVISION, "artifact": self.artifact}],
        }

    def make_artifact(self, relative: str, content: str) -> dict:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def release(self, deployed: bool = False) -> None:
        self.data["review"] = {"status": "passed", "revision": REVISION,
                               "reviewer": "fixture-reviewer",
                               "artifact": self.make_artifact("review.txt", "fixture review")}
        self.data["release"] = {
            "status": "deployed" if deployed else "planned", "revision": REVISION,
            "environment": "fixture-environment",
            "approval": {"by": "fixture-owner",
                         "artifact": self.make_artifact("approval.txt", "fixture approval")},
        }
        if deployed:
            self.data["release"].update(deployment_id="fixture-deployment",
                                       url="https://example.invalid/", smoke_check_ids=["C1"])

    def observation(self) -> None:
        self.release(deployed=True)
        self.data["observations"] = [{"metric": "fixture error count", "expected": 0, "actual": 0,
                                      "period": "fixture interval", "owner": "fixture-owner",
                                      "decision": "Continue fixture observation",
                                      "artifact": self.make_artifact("metric.txt", "count=0")}]

    def run_validator(self, stage: str = "local", raw: str | None = None,
                      revision: str = REVISION) -> tuple[int, dict]:
        self.manifest.write_text(json.dumps(self.data) if raw is None else raw, encoding="utf-8")
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.manifest),
                                 "--root", str(self.root), "--revision", revision, "--stage", stage],
                                check=False, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.stderr, "", result.stderr)
        payload = json.loads(result.stdout)
        self.assertIs(payload["consistency_only"], True)
        self.assertTrue(payload["limitations"])
        self.assertNotIn("SHIP", result.stdout)
        self.assertEqual(payload["readiness"],
                         "evidence_consistent" if result.returncode == 0 else "evidence_inconsistent")
        return result.returncode, payload

    def assert_invalid(self, field: str, stage: str = "local", **kwargs) -> dict:
        code, payload = self.run_validator(stage, **kwargs)
        self.assertEqual(code, 1, payload)
        self.assertTrue(any(field in error for error in payload["errors"]), payload)
        return payload

    def test_valid_local_has_explicit_consistency_limitations(self) -> None:
        code, payload = self.run_validator()
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["errors"], [])
        self.assertIn("identity", " ".join(payload["limitations"]))
        self.assertIn("N/A", " ".join(payload["limitations"]))

    def test_requirement_coverage_and_reference_are_required(self) -> None:
        self.data["checks"][0]["required_for"] = ["release"]
        self.assert_invalid("no check applicable to local")
        self.data["requirements"][0]["check_ids"] = ["missing"]
        self.assert_invalid("unknown check reference")

    def test_required_failed_and_not_run_are_failures(self) -> None:
        for status in ("failed", "not_run"):
            with self.subTest(status=status):
                self.data["checks"][0]["status"] = status
                self.assert_invalid("required local check")

    def test_unknown_and_boolean_statuses_are_rejected(self) -> None:
        for status in (True, False, "skipped", "PASS", None, {}):
            with self.subTest(status=status):
                self.data["checks"][0]["status"] = status
                self.assert_invalid("checks[0].status")

    def test_not_applicable_requires_explicit_reason(self) -> None:
        self.data["checks"][0].update(status="not_applicable")
        self.data["checks"][0].pop("artifact")
        self.assert_invalid("checks[0].reason")
        self.data["checks"][0]["reason"] = "No database boundary in the accepted fixture scope"
        self.assertEqual(self.run_validator()[0], 0)

    def test_revision_and_reuse_binding(self) -> None:
        self.data["revision"] = OLD_REVISION
        self.assert_invalid("revision: must match")
        self.data["revision"] = REVISION
        self.data["checks"][0]["applies_to_revision"] = OLD_REVISION
        self.assert_invalid("applies_to_revision")
        self.data["checks"][0]["applies_to_revision"] = REVISION
        self.data["checks"][0]["run_revision"] = OLD_REVISION
        self.assert_invalid("reuse_reason")
        self.data["checks"][0]["reuse_reason"] = "Fixture declares unchanged inputs; not proven here"
        self.assertEqual(self.run_validator()[0], 0)

    def test_passed_requires_artifact_and_valid_digest(self) -> None:
        for artifact in (None, {"path": "missing.txt", "sha256": "0" * 64},
                         {"path": self.artifact["path"], "sha256": "not-a-digest"}):
            with self.subTest(artifact=artifact):
                self.data["checks"][0]["artifact"] = artifact
                self.assert_invalid("artifact")
        self.data["checks"][0]["artifact"] = self.artifact
        (self.root / self.artifact["path"]).write_text("tampered", encoding="utf-8")
        self.assert_invalid("SHA256 mismatch")

    def test_absolute_parent_and_windows_paths_are_rejected(self) -> None:
        for path in (str(self.root / "checks/result.txt"), "../outside.txt",
                     "checks/../checks/result.txt", "C:\\private\\result.txt", "C:result.txt"):
            with self.subTest(path=path):
                self.data["checks"][0]["artifact"] = {**self.artifact, "path": path}
                self.assert_invalid("relative path inside")

    def test_symlink_file_and_symlink_directory_are_rejected(self) -> None:
        (self.root / "alias.txt").symlink_to(self.root / self.artifact["path"])
        (self.root / "linked").symlink_to(self.root / "checks", target_is_directory=True)
        for path in ("alias.txt", "linked/result.txt"):
            with self.subTest(path=path):
                self.data["checks"][0]["artifact"] = {**self.artifact, "path": path}
                self.assert_invalid("without symlinks")

    def test_non_regular_files_are_rejected_without_blocking(self) -> None:
        self.data["checks"][0]["artifact"] = {**self.artifact, "path": "checks"}
        self.assert_invalid("regular file")
        if hasattr(os, "mkfifo"):
            os.mkfifo(self.root / "fifo")
            self.data["checks"][0]["artifact"] = {**self.artifact, "path": "fifo"}
            self.assert_invalid("regular file")

    def test_structure_and_duplicate_ids_are_rejected(self) -> None:
        baseline = copy.deepcopy(self.data)
        for field in ("requirements", "checks"):
            self.data = copy.deepcopy(baseline)
            self.data[field].append(copy.deepcopy(self.data[field][0]))
            self.assert_invalid("duplicate")
        for field, value in (("schema_version", True), ("requirements", []), ("checks", {})):
            self.data = {**baseline, field: value}
            self.assert_invalid(field)

    def test_malformed_json_and_duplicate_keys_are_rejected(self) -> None:
        for raw in ('{"schema_version": 1, "schema_version": 1}', '[]', '{', '{"x": NaN}'):
            with self.subTest(raw=raw):
                self.assert_invalid("manifest", raw=raw)
        self.assert_invalid("--revision", revision="not-a-git-sha")

    def test_release_url_alone_is_insufficient(self) -> None:
        self.data["release"] = {"status": "deployed", "url": "https://example.invalid/"}
        payload = self.assert_invalid("review", stage="release")
        for field in ("approval", "deployment_id", "smoke_check_ids"):
            self.assertTrue(any(field in error for error in payload["errors"]), payload)

    def test_valid_planned_and_deployed_release(self) -> None:
        for deployed in (False, True):
            with self.subTest(deployed=deployed):
                self.release(deployed)
                self.assertEqual(self.run_validator("release")[0], 0)

    def test_review_and_approval_artifacts_and_revision_are_bound(self) -> None:
        self.release()
        self.data["review"]["revision"] = OLD_REVISION
        self.data["release"]["revision"] = OLD_REVISION
        self.assert_invalid("revision", stage="release")
        self.release()
        self.data["review"]["artifact"]["sha256"] = "0" * 64
        self.data["release"]["approval"]["artifact"]["path"] = "absent.txt"
        payload = self.assert_invalid("review.artifact", stage="release")
        self.assertTrue(any("release.approval.artifact" in error for error in payload["errors"]))

    def test_smoke_requires_current_actual_pass_even_when_reuse_has_reason(self) -> None:
        self.release(deployed=True)
        self.data["checks"][0].update(run_revision=OLD_REVISION, reuse_reason="Unchanged fixture")
        self.assert_invalid("current-run passed check", stage="release")
        self.data["checks"][0]["run_revision"] = REVISION
        self.data["release"]["smoke_check_ids"] = ["missing"]
        self.assert_invalid("current-run passed check", stage="release")
        self.data["release"]["smoke_check_ids"] = ["C1"]
        self.data["checks"][0].update(status="not_applicable", reason="Fixture exception")
        self.assert_invalid("current-run passed check", stage="release")

    def test_observation_requires_deployment_and_nonempty_observations(self) -> None:
        self.release()
        self.assert_invalid("observation requires deployed", stage="observation")
        self.release(deployed=True)
        self.assert_invalid("observations", stage="observation")
        self.data["observations"] = []
        self.assert_invalid("observations", stage="observation")

    def test_observation_zero_is_valid_and_values_must_not_be_empty(self) -> None:
        self.observation()
        self.assertEqual(self.run_validator("observation")[0], 0)
        baseline = copy.deepcopy(self.data)
        for key in ("expected", "actual"):
            for value in (None, "", "  ", [], {}):
                with self.subTest(key=key, value=value):
                    self.data = copy.deepcopy(baseline)
                    self.data["observations"][0][key] = value
                    self.assert_invalid(key, stage="observation")
            self.data = copy.deepcopy(baseline)
            self.data["observations"][0].pop(key)
            self.assert_invalid(key, stage="observation")
        self.data = baseline
        self.data["observations"][0]["artifact"]["sha256"] = "0" * 64
        self.assert_invalid("observations[0].artifact", stage="observation")

    def test_other_stage_failure_does_not_block_local_and_commands_are_never_run(self) -> None:
        self.data["checks"].append({"id": "future", "category": "operations", "status": "not_run",
                                    "required_for": ["release"], "applies_to_revision": REVISION})
        marker = self.base / "must-not-exist"
        self.data["command"] = f"touch {marker}"
        self.data["checks"][0]["command"] = f"touch {marker}"
        self.assertEqual(self.run_validator()[0], 0)
        self.assertFalse(marker.exists())

    def test_demonstration_example_cannot_pass_as_actual_evidence(self) -> None:
        example = SCRIPT.parents[1] / "assets" / "delivery-evidence.example.json"
        self.assert_invalid("revision", raw=example.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
