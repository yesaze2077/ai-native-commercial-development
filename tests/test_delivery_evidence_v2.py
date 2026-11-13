from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_delivery_evidence.py"
REVISION = "a" * 40
OLD_REVISION = "b" * 40
TIMESTAMP = "2026-11-13T08:30:00Z"


class DeliveryEvidenceV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = self.root / "manifest.json"
        self.artifact = self.make_artifact("result.txt", "Synthetic fixture only; no product run occurred.")
        self.data = {
            "schema_version": 2, "revision": REVISION,
            "requirements": [{"id": "R1", "description": "Fixture requirement", "check_ids": ["C1"]}],
            "checks": [{"id": "C1", "category": "unit", "status": "passed",
                        "required_for": ["local", "release", "observation"],
                        "applies_to_revision": REVISION, "run_revision": REVISION,
                        "fresh_required": True, "origin": "executed", "run_id": "fixture-run",
                        "executed_at": TIMESTAMP, "artifact": self.artifact}],
        }

    def make_artifact(self, name: str, content: str) -> dict:
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def scoped_out(self) -> dict:
        return {"reason": "Fixture accepted scope excludes an ongoing service",
                "scope_or_policy_ref": "fixture-scope@pinned-revision#service-boundary",
                "decision_artifact": self.make_artifact("scope.txt", "Synthetic scope decision")}

    def release(self, deployed: bool = False) -> None:
        self.data["review"] = {"status": "passed", "revision": REVISION,
                               "reviewer": "fixture-reviewer", "artifact": self.artifact}
        self.data["release"] = {
            "status": "deployed" if deployed else "planned", "revision": REVISION,
            "environment": "fixture-staging", "approval": {"by": "fixture-owner",
                                                           "artifact": self.artifact},
        }
        self.data["business_acceptance"] = {
            "status": "accepted", "revision": REVISION, "responsible_owner": "fixture-owner",
            "method": "owner_acceptance", "requirement_ids": ["R1"],
            "artifact": self.make_artifact("acceptance.txt", "Synthetic owner criteria and acceptance"),
        }
        self.data["operations_handoff"] = {
            "applicable": False, "revision": REVISION, **self.scoped_out(),
        }
        if deployed:
            self.data["release"].update(deployment_id="fixture-deployment",
                                       url="https://example.invalid/", smoke_check_ids=["SMOKE"])
            self.data["checks"].append({
                **self.data["checks"][0], "id": "SMOKE", "category": "deployment_smoke",
                "environment": "fixture-staging", "deployment_id": "fixture-deployment",
                "run_id": "fixture-smoke-run",
            })

    def observation(self) -> None:
        self.release(deployed=True)
        self.data["observations"] = [{"metric": "fixture errors", "expected": 0, "actual": 0,
                                      "period": "fixture interval", "owner": "fixture-owner",
                                      "decision": "Fixture only", "artifact": self.artifact}]

    def run_cli(self, stage: str = "local", require_v2: bool = True,
                raw: str | None = None) -> tuple[int, dict]:
        self.manifest.write_text(json.dumps(self.data) if raw is None else raw, encoding="utf-8")
        command = [sys.executable, str(SCRIPT), str(self.manifest), "--root", str(self.root),
                   "--revision", REVISION, "--stage", stage]
        if require_v2:
            command.append("--require-v2")
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.stderr, "", result.stderr)
        payload = json.loads(result.stdout)
        self.assertIs(payload["consistency_only"], True)
        self.assertNotIn("SHIP", result.stdout)
        self.assertIn("authenticity", " ".join(payload["limitations"]))
        return result.returncode, payload

    def assert_invalid(self, field: str, stage: str = "local") -> dict:
        code, payload = self.run_cli(stage)
        self.assertEqual(code, 1, payload)
        self.assertTrue(any(field in error for error in payload["errors"]), payload)
        return payload

    def assert_previously_accepted(self, field: str, stage: str = "local") -> None:
        self.assert_invalid(field, stage)
        self.data["schema_version"] = 1
        code, payload = self.run_cli(stage, require_v2=False)
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["contract_level"], "legacy_consistency")

    def test_valid_local_requires_no_release_prerequisites_and_never_runs_commands(self) -> None:
        marker = self.root / "must-not-exist"
        self.data["command"] = f"touch {marker}"
        self.data["checks"][0]["command"] = f"touch {marker}"
        code, payload = self.run_cli()
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["contract_level"], "v2_release_evidence")
        self.assertEqual(payload["schema_version"], 2)
        self.assertFalse(marker.exists())

    def test_all_na_cannot_satisfy_an_in_scope_requirement(self) -> None:
        self.data["checks"][0].update(status="not_applicable", reason="Fixture boundary",
                                      scope_or_policy_ref="fixture-scope@pinned#no-unit")
        self.assert_previously_accepted("all N/A is insufficient")

    def test_old_pass_cannot_satisfy_a_current_fresh_check(self) -> None:
        self.data["checks"][0].update(run_revision=OLD_REVISION, origin="reused",
                                      reuse_reason="Fixture claims unchanged inputs")
        self.assert_previously_accepted("fresh required check")

    def test_same_revision_unit_pass_cannot_masquerade_as_target_smoke(self) -> None:
        self.release(deployed=True)
        self.data["release"]["smoke_check_ids"] = ["C1"]
        self.assert_previously_accepted("category deployment_smoke", "release")

    def test_fresh_fields_have_strict_types_and_explicit_current_execution(self) -> None:
        baseline = copy.deepcopy(self.data)
        for key, value in (("fresh_required", "true"), ("fresh_required", 1),
                           ("fresh_required", None), ("origin", "reused"),
                           ("origin", True), ("run_revision", OLD_REVISION),
                           ("run_revision", None), ("run_id", ""),
                           ("executed_at", "2026-11-13"), ("executed_at", TIMESTAMP[:-1]),
                           ("executed_at", "2026-02-30T08:30:00Z")):
            with self.subTest(key=key, value=value):
                self.data = copy.deepcopy(baseline)
                self.data["checks"][0][key] = value
                self.assert_invalid(key)

    def test_intentionally_reused_document_is_allowed_with_explicit_reason(self) -> None:
        check = self.data["checks"][0]
        check.update(category="document_review", fresh_required=False, origin="reused",
                     run_revision=OLD_REVISION, reuse_reason="Pinned document inputs unchanged; fixture only")
        check.pop("run_id")
        check.pop("executed_at")
        self.assertEqual(self.run_cli()[0], 0)
        check.pop("reuse_reason")
        self.assert_invalid("reuse_reason")

    def test_future_fresh_check_does_not_block_local(self) -> None:
        self.data["checks"].append({"id": "FUTURE", "category": "deployment_smoke",
                                    "status": "not_run", "required_for": ["release"],
                                    "applies_to_revision": REVISION, "fresh_required": True})
        self.assertEqual(self.run_cli()[0], 0)

    def test_na_check_needs_scope_reference_even_when_another_check_passes(self) -> None:
        self.data["checks"].append({**self.data["checks"][0], "id": "NA",
                                    "status": "not_applicable", "reason": "Fixture scope boundary"})
        self.data["requirements"][0]["check_ids"].append("NA")
        self.assert_invalid("checks[1].scope_or_policy_ref")
        self.data["checks"][1]["scope_or_policy_ref"] = "fixture-scope@pinned#boundary"
        self.assertEqual(self.run_cli()[0], 0)

    def test_removed_and_na_requirements_need_digest_bound_scope_decisions(self) -> None:
        baseline = copy.deepcopy(self.data)
        for disposition in ("removed", "not_applicable"):
            with self.subTest(disposition=disposition):
                self.data = copy.deepcopy(baseline)
                requirement = {"id": "R2", "description": "Fixture excluded requirement",
                               "disposition": disposition, "reason": "Reason text alone"}
                self.data["requirements"].append(requirement)
                self.assert_invalid("requirements[1].scope_or_policy_ref")
                requirement.update(self.scoped_out())
                self.assertEqual(self.run_cli()[0], 0)
                requirement["decision_artifact"]["sha256"] = "0" * 64
                self.assert_invalid("SHA256 mismatch")

    def test_deployed_smoke_binds_category_target_and_current_executed_run(self) -> None:
        self.release(deployed=True)
        self.assertEqual(self.run_cli("release")[0], 0)
        baseline = copy.deepcopy(self.data)
        for key, value in (("environment", "another-environment"), ("deployment_id", "another-id"),
                           ("origin", "reused"), ("run_revision", OLD_REVISION),
                           ("run_id", None), ("executed_at", None),
                           ("required_for", ["local"])):
            with self.subTest(key=key):
                self.data = copy.deepcopy(baseline)
                self.data["checks"][1].update({key: value}, fresh_required=False,
                                             reuse_reason="Fixture historical evidence")
                self.assert_invalid("smoke_check_ids", "release")

    def test_business_acceptance_is_separate_and_current(self) -> None:
        self.release()
        baseline = copy.deepcopy(self.data)
        for key, value in (("status", "pending"), ("status", True),
                           ("responsible_owner", ""), ("method", "agent_self_approval"),
                           ("revision", OLD_REVISION), ("artifact", None)):
            with self.subTest(key=key):
                self.data = copy.deepcopy(baseline)
                self.data["business_acceptance"][key] = value
                self.assert_invalid("business_acceptance", "release")
        self.data = baseline
        self.data.pop("business_acceptance")
        self.assert_invalid("business_acceptance", "release")

    def test_business_acceptance_covers_known_unique_in_scope_requirements(self) -> None:
        self.release()
        self.data["requirements"].append({"id": "R2", "description": "Second fixture requirement",
                                          "check_ids": ["C1"]})
        for refs in (["R1"], ["R1", "R2", "unknown"], ["R1", "R2", "R2"], ["R1", {}]):
            with self.subTest(refs=refs):
                self.data["business_acceptance"]["requirement_ids"] = refs
                self.assert_invalid("requirement_ids", "release")
        self.data["business_acceptance"]["requirement_ids"] = ["R1", "R2"]
        self.assertEqual(self.run_cli("release")[0], 0)

    def test_delegated_acceptance_requires_explicit_authority_and_evidence(self) -> None:
        self.release()
        acceptance = self.data["business_acceptance"]
        acceptance["method"] = "delegated"
        self.assert_invalid("authority_ref", "release")
        acceptance["authority_ref"] = "fixture-owner-policy@pinned#delegation"
        self.assert_invalid("authority_artifact", "release")
        acceptance["authority_artifact"] = self.make_artifact("delegation.txt", "Synthetic delegated criteria")
        self.assertEqual(self.run_cli("release")[0], 0)
        acceptance["authority_artifact"]["sha256"] = "0" * 64
        self.assert_invalid("SHA256 mismatch", "release")

    def test_scoped_business_acceptance_na_requires_decision_evidence(self) -> None:
        self.release()
        self.data["business_acceptance"] = {"status": "not_applicable", "revision": REVISION,
                                             "reason": "Fixture exemption"}
        self.assert_invalid("scope_or_policy_ref", "release")
        self.data["business_acceptance"].update(self.scoped_out())
        self.assertEqual(self.run_cli("release")[0], 0)

    def test_operations_handoff_requires_accepted_owner_access_and_followup(self) -> None:
        self.release()
        self.data["operations_handoff"] = {
            "applicable": True, "revision": REVISION, "status": "accepted", "owner": "fixture-oncall",
            "access_confirmed": True, "observation_window": "Fixture 24-hour window",
            "next_check_at": "2026-11-14T08:30:00+00:00", "escalation": "Fixture owner escalation",
            "artifact": self.make_artifact("handoff.txt", "Synthetic accepted access and handoff"),
        }
        self.assertEqual(self.run_cli("release")[0], 0)
        baseline = copy.deepcopy(self.data)
        for key, value in (("status", "pending"), ("owner", ""), ("access_confirmed", "true"),
                           ("access_confirmed", 1), ("observation_window", ""),
                           ("next_check_at", "next week"), ("escalation", ""),
                           ("revision", OLD_REVISION), ("artifact", None), ("applicable", "true")):
            with self.subTest(key=key, value=value):
                self.data = copy.deepcopy(baseline)
                self.data["operations_handoff"][key] = value
                self.assert_invalid("operations_handoff", "release")

    def test_operations_na_is_scoped_and_digest_bound(self) -> None:
        self.release()
        operations = self.data["operations_handoff"]
        operations.pop("scope_or_policy_ref")
        self.assert_invalid("scope_or_policy_ref", "release")
        operations.update(self.scoped_out())
        operations["decision_artifact"]["sha256"] = "0" * 64
        self.assert_invalid("SHA256 mismatch", "release")

    def test_valid_scoped_non_ui_simple_release_and_observation(self) -> None:
        self.observation()
        self.data["checks"][0]["category"] = "document_review"
        self.data["requirements"].append({"id": "UI", "description": "No UI in fixture scope",
                                          "disposition": "not_applicable", **self.scoped_out()})
        for stage in ("release", "observation"):
            with self.subTest(stage=stage):
                self.assertEqual(self.run_cli(stage)[0], 0)
        self.data["business_acceptance"]["status"] = "pending"
        self.assert_invalid("business_acceptance.status", "observation")

    def test_scope_decision_artifacts_retain_symlink_and_path_safety(self) -> None:
        self.release()
        alias = self.root / "alias.txt"
        alias.symlink_to(self.root / self.artifact["path"])
        artifact = self.data["operations_handoff"]["decision_artifact"]
        for path in ("../outside", str(self.root / "result.txt"), "alias.txt"):
            with self.subTest(path=path):
                artifact["path"] = path
                self.assert_invalid("decision_artifact", "release")

    def test_legacy_is_explicitly_not_v2_and_flag_rejects_it(self) -> None:
        self.data["schema_version"] = 1
        code, payload = self.run_cli(require_v2=False)
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["contract_level"], "legacy_consistency")
        code, payload = self.run_cli(require_v2=True)
        self.assertEqual(code, 1, payload)
        self.assertEqual(payload["contract_level"], "legacy_consistency")
        self.assertIn("legacy is not v2", " ".join(payload["errors"]))

    def test_example_is_unexecuted_and_cannot_pass_as_evidence(self) -> None:
        example = SCRIPT.parents[1] / "assets" / "delivery-evidence.v2.example.json"
        code, payload = self.run_cli("release", raw=example.read_text(encoding="utf-8"))
        self.assertEqual(code, 1, payload)
        self.assertIn("not_run", example.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
