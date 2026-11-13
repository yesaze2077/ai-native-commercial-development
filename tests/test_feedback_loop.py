from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "feedback_loop.py"
SPEC = importlib.util.spec_from_file_location("feedback_loop_under_test", SCRIPT)
feedback = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(feedback)


def example(**changes):
    value = {"schema_version": 1, "redacted": True, "id": "event-1", "occurrence_id": "task-1",
             "project": "project-a", "pattern_key": "repeated-checks", "category": "efficiency",
             "severity": "medium", "root_cause": "workflow-rule", "scope": "project",
             "summary": "Repeated unaffected checks", "expected": "Keep valid evidence",
             "actual": "Ran unaffected checks again", "evidence": [{"kind": "observed", "ref": "local-report-1"}],
             "skill_version": "7.0.0"}
    value.update(changes)
    return value


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.store = self.root / "private-state" / "feedback.json"

    def tearDown(self):
        self.temp.cleanup()

    def record(self, **changes):
        return feedback.append(self.store, example(**changes), "events")

    def result(self):
        return feedback.assess(feedback.load(self.store))["assessments"][0]

    def decision(self, disposition="deferred", reviewed=None):
        return {"schema_version": 1, "redacted": True, "pattern_key": "repeated-checks",
                "reviewed_event_ids": reviewed or ["event-1"], "disposition": disposition,
                "reason": "User decision recorded for this proposal", "user_ref": "current-chat-decision-1",
                "proposal_ref": "proposal-1-digest-reference"}

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), "--store", str(self.store), *args],
                              capture_output=True, text=True)

    def test_absent_assessment_does_not_create_state(self):
        result = self.cli("assess")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["assessments"], [])
        self.assertFalse(self.store.parent.exists())

    def test_record_private_and_round_trip(self):
        self.record()
        self.assertEqual(stat.S_IMODE(self.store.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.store.parent.stat().st_mode), 0o700)
        self.assertEqual(feedback.load(self.store)["events"][0]["record"], example())
        self.assertEqual(self.result()["recommendation"], "observe")

    def test_assessment_does_not_mutate_existing_state(self):
        self.record()
        before = self.store.read_bytes(), self.store.stat().st_mtime_ns
        feedback.assess(feedback.load(self.store))
        self.assertEqual((self.store.read_bytes(), self.store.stat().st_mtime_ns), before)

    def test_duplicate_is_idempotent_and_conflict_rejected(self):
        self.record()
        before = self.store.read_bytes()
        self.assertEqual(self.record()["status"], "duplicate")
        self.assertEqual(self.store.read_bytes(), before)
        with self.assertRaises(feedback.FeedbackError):
            self.record(actual="Different report under the same immutable id")
        self.assertEqual(self.store.read_bytes(), before)

    def test_same_occurrence_does_not_inflate_recurrence(self):
        self.record()
        self.record(id="event-2")
        self.assertEqual(self.result()["distinct_occurrences"], 1)
        self.assertEqual(self.result()["recommendation"], "observe")

    def test_distinct_occurrences_support_project_trial(self):
        self.record()
        self.record(id="event-2", occurrence_id="task-2")
        result = self.result()
        self.assertEqual(result["recommendation"], "project_trial")
        self.assertTrue(result["needs_proposal"])
        self.assertTrue(result["requires_user_confirmation_for_rule_update"])

    def test_cross_project_observed_global_evidence_supports_candidate(self):
        self.record(scope="global")
        self.record(id="event-2", occurrence_id="task-2", project="project-b", scope="global")
        self.assertEqual(self.result()["recommendation"], "skill_candidate")

    def test_cross_project_reported_only_does_not_establish_global(self):
        report = [{"kind": "reported", "ref": "user-feedback"}]
        self.record(scope="global", evidence=report)
        self.record(id="event-2", occurrence_id="task-2", project="project-b", scope="global", evidence=report)
        self.assertEqual(self.result()["recommendation"], "project_trial")

    def test_observed_serious_single_issue_gets_scoped_review(self):
        self.record(severity="critical", category="incident", scope="global")
        result = self.result()
        self.assertEqual(result["recommendation"], "project_trial")
        self.assertTrue(result["urgent"])

    def test_reported_serious_issue_requires_verification(self):
        self.record(severity="critical", evidence=[{"kind": "reported", "ref": "unverified-feedback"}])
        result = self.result()
        self.assertEqual(result["recommendation"], "investigate")
        self.assertTrue(result["urgent"])

    def test_specific_project_causes_do_not_become_skill_rules(self):
        for cause in feedback.PROJECT_CAUSES:
            with self.subTest(cause=cause):
                data = feedback.empty()
                e = example(root_cause=cause)
                data["events"] = [{"record": e, "sha256": feedback.digest(e)}]
                self.assertEqual(feedback.assess(data)["assessments"][0]["recommendation"], "project_fix")

    def test_unknown_cause_and_conflicting_known_causes_investigate(self):
        self.record(root_cause="unknown")
        self.assertEqual(self.result()["recommendation"], "investigate")
        self.record(id="event-2", root_cause="workflow-rule")
        self.assertEqual(self.result()["recommendation"], "observe")
        self.record(id="event-3", root_cause="product-defect")
        self.assertEqual(self.result()["recommendation"], "investigate")

    def test_explicit_preference_only_proposes_and_never_approves(self):
        self.record(root_cause="user-preference", scope="global")
        report = feedback.assess(feedback.load(self.store))
        self.assertEqual(report["assessments"][0]["recommendation"], "skill_candidate")
        self.assertFalse(report["may_update_rules"])
        self.assertFalse(report["decision_is_authenticated_approval"])

    def test_defer_suppresses_until_new_adverse_evidence(self):
        self.record(root_cause="user-preference")
        feedback.append(self.store, self.decision(), "decisions")
        self.assertTrue(self.result()["suppressed"])
        self.record(id="event-2", root_cause="user-preference", evidence=[{"kind": "observed", "ref": "new-evidence-2"}])
        result = self.result()
        self.assertFalse(result["suppressed"])
        self.assertTrue(result["reopened"])
        self.assertEqual(result["distinct_occurrences"], 1)

    def test_verified_serious_report_can_progress_without_erasing_history(self):
        self.record(severity="critical", evidence=[{"kind": "reported", "ref": "initial-report"}])
        self.assertEqual(self.result()["recommendation"], "investigate")
        self.record(id="event-2", severity="critical", evidence=[{"kind": "observed", "ref": "direct-reproduction"}])
        self.assertEqual(self.result()["recommendation"], "project_trial")
        self.assertEqual(self.result()["distinct_occurrences"], 1)
        self.assertEqual(len(feedback.load(self.store)["events"]), 2)
        self.record(id="event-3", occurrence_id="task-2", severity="critical",
                    evidence=[{"kind": "reported", "ref": "unverified-independent-report"}])
        self.assertEqual(self.result()["recommendation"], "investigate")

    def test_lower_severity_observation_does_not_verify_critical_claim(self):
        self.record(severity="critical", evidence=[{"kind": "reported", "ref": "initial-report"}])
        self.record(id="event-2", severity="low", evidence=[{"kind": "observed", "ref": "limited-observation"}])
        self.assertEqual(self.result()["recommendation"], "investigate")

    def test_one_occurrence_cannot_invent_cross_project_support(self):
        self.record(severity="critical", scope="global")
        self.record(id="event-2", severity="critical", scope="global", project="project-b")
        result = self.result()
        self.assertEqual(result["distinct_occurrences"], 1)
        self.assertEqual(result["recommendation"], "investigate")
        self.assertFalse(result["needs_proposal"])

    def test_renaming_identical_material_does_not_reopen_deferred_proposal(self):
        self.record(root_cause="user-preference", scope="global")
        feedback.append(self.store, self.decision(), "decisions")
        before = self.store.read_bytes()
        result = self.record(id="new-id-only", root_cause="user-preference", scope="global")
        self.assertEqual(result["status"], "duplicate")
        self.assertEqual(result["record_id"], "event-1")
        self.assertEqual(self.store.read_bytes(), before)
        self.assertTrue(self.result()["suppressed"])
        self.assertFalse(self.result()["reopened"])
        self.assertFalse(self.result()["needs_proposal"])

    def test_preexisting_unreviewed_material_is_not_called_update_regression(self):
        self.record()
        self.record(id="event-2", occurrence_id="task-2")
        feedback.append(self.store, self.decision("applied"), "decisions")
        result = self.result()
        self.assertEqual(result["preexisting_unreviewed_event_ids"], ["event-2"])
        self.assertEqual(result["recorded_after_decision_event_ids"], [])
        self.assertIn("recording order alone does not establish", " ".join(result["reasons"]))

    def test_rejection_and_invalid_decision_references(self):
        self.record()
        feedback.append(self.store, self.decision("rejected"), "decisions")
        self.assertTrue(self.result()["suppressed"])
        with self.assertRaises(feedback.FeedbackError):
            feedback.append(self.store, self.decision(reviewed=["missing"]), "decisions")

    def test_applied_update_is_monitor_only_until_regression(self):
        self.record()
        feedback.append(self.store, self.decision("applied"), "decisions")
        self.assertEqual(self.result()["recommendation"], "monitor")
        self.record(id="outcome-1", occurrence_id="follow-up-1", category="outcome", outcome="improved")
        self.assertEqual(self.result()["distinct_occurrences"], 1)
        self.assertEqual(self.result()["recommendation"], "monitor")
        self.assertFalse(self.result()["reopened"])
        self.record(id="outcome-2", occurrence_id="follow-up-2", category="outcome", outcome="regressed")
        result = self.result()
        self.assertTrue(result["reopened"])
        self.assertTrue(result["urgent"])
        self.assertIn("outcome-2", result["new_adverse_event_ids"])
        self.assertFalse(feedback.assess(feedback.load(self.store))["may_update_rules"])

    def test_outcome_without_issue_is_monitor_not_repeat_failure(self):
        self.record(category="outcome", outcome="improved")
        self.assertEqual(self.result()["recommendation"], "monitor")
        self.assertEqual(self.result()["distinct_occurrences"], 0)
        with self.assertRaises(feedback.FeedbackError):
            self.record(id="event-2", outcome="improved")

    def test_input_requires_redaction_and_rejects_obvious_sensitive_data(self):
        for changes in ({"redacted": False}, {"summary": "contact@example.test"},
                        {"actual": "password=unredacted-example-value"}, {"extra": "unsupported"}):
            with self.subTest(changes=changes), self.assertRaises(feedback.FeedbackError):
                feedback.event(example(**changes))
        self.assertFalse(self.store.exists())

    def test_corrupt_unrecognized_and_digest_tampered_store_not_overwritten(self):
        self.store.parent.mkdir(mode=0o700)
        self.store.write_text('{"unrelated":"keep"}')
        self.store.chmod(0o600)
        before = self.store.read_bytes()
        with self.assertRaises(feedback.FeedbackError):
            self.record()
        self.assertEqual(self.store.read_bytes(), before)
        self.store.unlink()
        self.record()
        data = json.loads(self.store.read_text())
        data["events"][0]["record"]["summary"] = "Tampered summary"
        self.store.write_text(json.dumps(data))
        with self.assertRaises(feedback.FeedbackError):
            feedback.load(self.store)

    def test_duplicate_json_keys_and_oversized_input_rejected(self):
        p = self.root / "input.json"
        p.write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaises(feedback.FeedbackError):
            feedback.read_json(p)
        p.write_bytes(b" " * (feedback.MAX_BYTES + 1))
        with self.assertRaises(feedback.FeedbackError):
            feedback.read_json(p)

    def test_symlink_store_and_parent_rejected(self):
        self.root.joinpath("other.json").write_text("{}")
        self.root.joinpath("linked.json").symlink_to(self.root / "other.json")
        with self.assertRaises(feedback.FeedbackError):
            feedback.load(self.root / "linked.json")
        (self.root / "link").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(feedback.FeedbackError):
            feedback.load(self.root / "link" / "missing.json")

    def test_nonregular_store_and_nonprivate_directory_rejected(self):
        self.store.parent.mkdir(mode=0o700)
        os.mkfifo(self.store, 0o600)
        with self.assertRaises(feedback.FeedbackError):
            feedback.load(self.store)
        self.store.unlink()
        self.store.parent.chmod(0o755)
        with self.assertRaises(feedback.FeedbackError):
            self.record()
        self.assertEqual(stat.S_IMODE(self.store.parent.stat().st_mode), 0o755)

    def test_store_private_mode_and_package_or_git_location(self):
        self.record()
        self.store.chmod(0o644)
        with self.assertRaises(feedback.FeedbackError):
            feedback.load(self.store)
        with self.assertRaises(feedback.FeedbackError):
            feedback.safe_path(SCRIPT.parent / "state.json")
        (self.root / ".git").mkdir()
        with self.assertRaises(feedback.FeedbackError):
            feedback.safe_path(self.root / "other.json")

    def test_parallel_cli_writers_do_not_lose_events(self):
        processes = []
        for number in range(6):
            p = self.root / ("event-%d.json" % number)
            p.write_text(json.dumps(example(id="event-%d" % number, occurrence_id="task-%d" % number)))
            processes.append(subprocess.Popen([sys.executable, str(SCRIPT), "--store", str(self.store),
                                               "record", "--event", str(p)], stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE, text=True))
        for process in processes:
            stdout, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertFalse(json.loads(stdout)["rules_changed"])
        records = feedback.load(self.store)["events"]
        self.assertEqual(len(records), 6)
        self.assertEqual(len({r["record"]["id"] for r in records}), 6)

    def test_malformed_enum_types_fail_cleanly(self):
        for changes in ({"schema_version": True}, {"category": "outcome", "outcome": []},
                        {"evidence": [{"kind": [], "ref": "local-report"}]}):
            with self.subTest(changes=changes), self.assertRaises(feedback.FeedbackError):
                feedback.event(example(**changes))
        self.record()
        decision = self.decision()
        decision["disposition"] = []
        with self.assertRaises(feedback.FeedbackError):
            feedback.append(self.store, decision, "decisions")

    def test_external_noncooperating_change_is_not_overwritten(self):
        self.record()
        real_fsync = os.fsync
        def modify_after_temporary_write(fd):
            real_fsync(fd)
            self.store.write_text('{"unrelated":"preserve-external-change"}')
        with mock.patch.object(feedback.os, "fsync", side_effect=modify_after_temporary_write):
            with self.assertRaises(feedback.FeedbackError):
                self.record(id="event-2", occurrence_id="task-2")
        self.assertEqual(json.loads(self.store.read_text()), {"unrelated": "preserve-external-change"})
        self.assertFalse(list(self.store.parent.glob(".feedback-*")))

    def test_symlink_lock_and_hardlinked_store_are_rejected(self):
        self.store.parent.mkdir(mode=0o700)
        other = self.root / "unrelated.json"
        other.write_text('{"unrelated":"preserve"}')
        lock = self.store.with_name("." + self.store.name + ".lock")
        lock.symlink_to(other)
        result = self.root / "input.json"
        result.write_text(json.dumps(example()))
        completed = self.cli("record", "--event", str(result))
        self.assertEqual(completed.returncode, 2)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertEqual(json.loads(other.read_text()), {"unrelated": "preserve"})
        lock.unlink()
        self.record()
        os.link(self.store, self.root / "linked-copy.json")
        with self.assertRaises(feedback.FeedbackError):
            feedback.load(self.store)


if __name__ == "__main__":
    unittest.main()
