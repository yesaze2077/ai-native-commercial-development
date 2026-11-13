"""Real temporary repositories and actual subprocesses; no network or dependencies."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

RUNNER = Path(__file__).resolve().parents[1] / "scripts" / "incremental_verify.py"


class IncrementalVerifyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.outside = Path(self.temporary.name).resolve()
        self.root = self.outside / "repo"
        self.root.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Local Test")
        self.profile = {
            "schema_version": 1,
            "components": {
                "lib": {"paths": ["lib/**"], "depends_on": []},
                "app": {"paths": ["app/**"], "depends_on": ["lib"]},
                "other": {"paths": ["other/**"], "depends_on": []}},
            "checks": [self.check("lib", ["lib"]), self.check("app", ["app"]),
                       self.check("other", ["other"]), self.check("integrate", ["app"], "integration"),
                       self.check("release", ["app"], "release")],
            "global_paths": ["config/**"], "always_checks": []}
        for path in ("lib/a.txt", "app/a.txt", "other/a.txt", "tests/lib.txt", "config/settings.json"):
            self.put(path, "initial\n")
        self.save_profile()
        self.git("add", ".")
        self.git("commit", "-qm", "initial")
        self.base = self.git("rev-parse", "HEAD").strip()

    @staticmethod
    def check(name, components, stage="quick", code="print('verified')"):
        return {"id": name, "components": components, "stage": stage,
                "command": [sys.executable, "-c", code], "inputs": ["tests/lib.txt"] if name == "lib" else [],
                "cache": True, "hermetic": True, "env": [], "runtime_inputs": [], "timeout_seconds": 2}

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True, check=True)
        return result.stdout

    def put(self, path, text):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text)

    def save_profile(self, commit=False):
        self.put("profile.json", json.dumps(self.profile))
        if commit:
            self.git("add", "profile.json")
            self.git("commit", "--allow-empty", "-qm", "profile")
            self.base = self.git("rev-parse", "HEAD").strip()

    def run_tool(self, execute=False, stage="quick", expected=0, env=None, extra=()):
        command = [sys.executable, str(RUNNER), "--root", str(self.root), "--profile", str(self.root / "profile.json"),
                   "--base", self.base, "--stage", stage, *extra]
        if execute:
            command.append("--execute")
        result = subprocess.run(command, capture_output=True, text=True, env=env, timeout=20)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        self.assertFalse(result.stderr, result.stderr)
        return json.loads(result.stdout)

    @staticmethod
    def entries(report):
        return {entry["id"]: entry for entry in report["checks"]}

    def selected(self, report):
        return {name for name, entry in self.entries(report).items() if entry["selected"]}

    def test_local_change_consumer_closure_and_plan_does_not_execute(self):
        self.put("lib/a.txt", "changed")
        report = self.run_tool()
        self.assertEqual(self.selected(report), {"lib", "app"})
        self.assertEqual(report["affected_components"], ["app", "lib"])
        self.assertEqual(report["status"], "plan_only")
        self.assertGreater(report["elapsed_seconds"], 0)
        self.assertFalse((self.root / ".git/incremental-verify").exists())
        self.assertEqual(report["remaining_gates"], ["app", "integrate", "lib", "release"])

    def test_no_checks_is_not_verified(self):
        report = self.run_tool(execute=True)
        self.assertEqual(report["status"], "no_checks")
        self.assertTrue(all(c["status"] == "not_run" for c in report["checks"]))

    def test_all_commits_staged_unstaged_untracked_and_renames(self):
        self.put("lib/a.txt", "committed")
        self.git("add", ".")
        self.git("commit", "-qm", "first")
        self.git("mv", "app/a.txt", "app/renamed.txt")
        self.git("commit", "-qm", "rename")
        self.put("other/a.txt", "staged")
        self.git("add", "other/a.txt")
        # Cancel a staged edit in the working tree: the union must retain it.
        self.put("other/a.txt", "initial\n")
        self.put("lib/new.txt", "untracked")
        (self.root / "lib/a.txt").unlink()
        report = self.run_tool()
        paths = {c["path"] for c in report["changes"]}
        self.assertTrue({"lib/a.txt", "lib/new.txt", "app/a.txt", "app/renamed.txt", "other/a.txt"} <= paths)
        self.assertEqual(self.selected(report), {"lib", "app", "other"})

    def test_unknown_global_lock_and_profile_escalate_all_eligible(self):
        for path, prefix in (("unknown.txt", "unmapped_path"), ("config/new.json", "global_path"),
                             ("nested/package-lock.json", "lockfile"), ("profile.json", "profile_changed")):
            with self.subTest(path=path):
                original = (self.root / path).read_text() if (self.root / path).exists() else None
                self.put(path, original + "\n" if original is not None else "changed")
                report = self.run_tool()
                self.assertEqual(self.selected(report), {"lib", "app", "other"})
                self.assertTrue(any(x.startswith(prefix) for x in report["escalation"]))
                if original is None:
                    (self.root / path).unlink()
                else:
                    self.put(path, original)

    def test_layers_and_always_eligible_only(self):
        self.profile["always_checks"] = ["other", "release"]
        self.save_profile(commit=True)
        self.put("app/a.txt", "changed")
        self.assertEqual(self.selected(self.run_tool()), {"app", "other"})
        self.assertEqual(self.selected(self.run_tool(stage="integration")), {"app", "integrate", "other"})
        self.assertEqual(self.selected(self.run_tool(stage="release")), {"lib", "app", "other", "integrate", "release"})

    def test_invalid_references_cycle_duplicate_id_and_json_key(self):
        original = copy.deepcopy(self.profile)
        variants = []
        bad = copy.deepcopy(original)
        bad["components"]["app"]["depends_on"] = ["missing"]
        variants.append(bad)
        bad = copy.deepcopy(original)
        bad["components"]["lib"]["depends_on"] = ["app"]
        variants.append(bad)
        bad = copy.deepcopy(original)
        bad["checks"].append(copy.deepcopy(bad["checks"][0]))
        variants.append(bad)
        bad = copy.deepcopy(original)
        bad["checks"][0]["components"] = ["missing"]
        variants.append(bad)
        bad = copy.deepcopy(original)
        bad["always_checks"] = ["missing"]
        variants.append(bad)
        for bad in variants:
            self.profile = bad
            self.save_profile()
            self.assertEqual(self.run_tool(expected=2)["status"], "error")
        self.put("profile.json", '{"schema_version":1,"schema_version":1}')
        self.assertIn("Duplicate", self.run_tool(expected=2)["error"])

    def test_cache_cold_hot_unrelated_and_related_files(self):
        self.put("lib/a.txt", "first")
        first = self.run_tool(execute=True)
        self.assertEqual(self.entries(first)["lib"]["status"], "passed")
        second = self.run_tool(execute=True)
        self.assertEqual(self.entries(second)["lib"]["status"], "reused")
        self.assertGreater(second["elapsed_seconds"], 0)
        self.assertEqual(self.entries(second)["lib"]["duration_seconds"], 0)
        self.assertEqual(self.entries(second)["lib"]["original_run"]["id"], first["run_id"])
        self.assertNotEqual(first["run_id"], second["run_id"])
        self.put("other/a.txt", "independent")
        third = self.run_tool(execute=True)
        self.assertEqual(self.entries(third)["lib"]["status"], "reused")
        self.put("lib/new.txt", "new input")
        fourth = self.run_tool(execute=True)
        self.assertEqual(self.entries(fourth)["lib"]["status"], "passed")
        (self.root / "lib/new.txt").unlink()
        self.assertEqual(self.entries(self.run_tool(execute=True))["lib"]["status"], "reused")

    def test_test_definition_runtime_input_and_env_change_invalidate(self):
        self.profile["checks"][0]["env"] = ["INCREMENTAL_TEST_INPUT"]
        self.profile["checks"][0]["runtime_inputs"] = ["runtime/**"]
        self.put("runtime/settings.txt", "v1")
        self.git("add", "runtime")
        self.git("commit", "-qm", "runtime")
        self.save_profile(commit=True)
        self.put("lib/a.txt", "changed")
        env = dict(os.environ, INCREMENTAL_TEST_INPUT="redacted-a")
        first = self.run_tool(execute=True, env=env)
        self.assertEqual(self.entries(self.run_tool(execute=True, env=env))["lib"]["status"], "reused")
        self.put("tests/lib.txt", "new definition")
        second = self.run_tool(execute=True, env=env)
        self.assertNotEqual(self.entries(first)["lib"]["fingerprint"], self.entries(second)["lib"]["fingerprint"])
        self.put("runtime/settings.txt", "v2")
        self.assertEqual(self.entries(self.run_tool(execute=True, env=env))["lib"]["status"], "passed")
        env["INCREMENTAL_TEST_INPUT"] = "redacted-b"
        report = self.run_tool(execute=True, env=env)
        self.assertEqual(self.entries(report)["lib"]["status"], "passed")
        self.assertNotIn("redacted-", json.dumps(report))

    def test_dependent_key_includes_producer_and_own_input_selects(self):
        self.put("app/a.txt", "changed")
        first = self.entries(self.run_tool(execute=True))["app"]["fingerprint"]
        self.put("lib/a.txt", "producer changed")
        second = self.entries(self.run_tool(execute=True))["app"]["fingerprint"]
        self.assertNotEqual(first, second)
        self.put("app/a.txt", "initial\n")
        self.put("lib/a.txt", "initial\n")
        self.put("tests/lib.txt", "test only")
        self.assertEqual(self.selected(self.run_tool()), {"lib"})

    def test_profile_and_unknown_changes_never_reuse_local_cache(self):
        self.put("lib/a.txt", "changed")
        self.run_tool(execute=True)
        for path in ("unknown.txt", "config/settings.json", "package-lock.json"):
            with self.subTest(path=path):
                original = (self.root / path).read_text() if (self.root / path).exists() else None
                self.put(path, "escalate")
                report = self.run_tool(execute=True)
                self.assertEqual(self.entries(report)["lib"]["status"], "passed")
                self.assertEqual(self.entries(report)["lib"]["cache"], "disabled")
                if original is None:
                    (self.root / path).unlink()
                else:
                    self.put(path, original)
        self.put("profile.json", (self.root / "profile.json").read_text() + "\n")
        self.assertEqual(self.entries(self.run_tool(execute=True))["lib"]["cache"], "disabled")

    def test_release_fresh_and_missing_runtime_contract_force_new_runs(self):
        self.put("lib/a.txt", "changed")
        self.run_tool(execute=True)
        self.assertEqual(self.entries(self.run_tool(execute=True, extra=["--fresh"]))["lib"]["status"], "passed")
        report = self.run_tool(execute=True, stage="release")
        self.assertTrue(all(c["status"] == "passed" for c in report["checks"]))
        self.assertFalse(report["remaining_gates"])
        self.profile["checks"][0].pop("runtime_inputs")
        self.save_profile(commit=True)
        self.run_tool(execute=True)
        self.assertEqual(self.entries(self.run_tool(execute=True))["lib"]["status"], "passed")

    def test_failed_forced_run_invalidates_previous_success(self):
        # Intentionally violate the hermetic contract to inject an unchanged-key failure.
        flag = self.outside / "failure-flag"
        self.profile["checks"][0]["command"] = [sys.executable, "-c",
            f"from pathlib import Path; raise SystemExit(int(Path({str(flag)!r}).exists()))"]
        self.save_profile(commit=True)
        self.put("lib/a.txt", "changed")
        first = self.entries(self.run_tool(execute=True))["lib"]
        flag.write_text("fail")
        failed = self.entries(self.run_tool(execute=True, extra=["--fresh"], expected=1))["lib"]
        self.assertEqual(first["fingerprint"], failed["fingerprint"])
        self.assertEqual(failed["status"], "failed")
        again = self.entries(self.run_tool(execute=True, expected=1))["lib"]
        self.assertEqual(again["status"], "failed")
        self.assertEqual(again["cache"], "miss")

    def test_failure_never_cached(self):
        self.profile["checks"][0]["command"] = [sys.executable, "-c", "raise SystemExit(7)"]
        self.save_profile(commit=True)
        self.put("lib/a.txt", "changed")
        for _ in range(2):
            entry = self.entries(self.run_tool(execute=True, expected=1))["lib"]
            self.assertEqual(entry["exit_code"], 7)
            self.assertEqual(entry["cache"], "miss")

    def test_record_and_log_tampering_require_new_execution(self):
        self.put("lib/a.txt", "changed")
        first = self.entries(self.run_tool(execute=True))["lib"]
        cache = self.root / ".git/incremental-verify"
        record = cache / "records" / (first["fingerprint"] + ".json")
        data = json.loads(record.read_text())
        data["payload"]["original_run"]["revision"] = "tampered"
        record.write_text(json.dumps(data))
        second = self.entries(self.run_tool(execute=True))["lib"]
        self.assertEqual((second["status"], second["cache"]), ("passed", "invalid"))
        Path(second["log"]).write_text("tampered")
        third = self.entries(self.run_tool(execute=True))["lib"]
        self.assertEqual((third["status"], third["cache"]), ("passed", "invalid"))
        Path(third["log"]).unlink()
        self.assertEqual(self.entries(self.run_tool(execute=True))["lib"]["status"], "passed")

    def test_related_file_mutation_during_run_cannot_pass_or_cache(self):
        self.profile["checks"][0]["command"] = [sys.executable, "-c", "from pathlib import Path; Path('lib/a.txt').write_text('mutated')"]
        self.save_profile(commit=True)
        self.put("lib/a.txt", "changed")
        entry = self.entries(self.run_tool(execute=True, expected=1))["lib"]
        self.assertEqual(entry["failure_reason"], "inputs_changed_during_run")
        self.assertFalse((self.root / ".git/incremental-verify/records" / (entry["fingerprint"] + ".json")).exists())

    def test_later_check_mutation_invalidates_combined_success(self):
        self.profile["checks"][1]["command"] = [sys.executable, "-c", "from pathlib import Path; Path('lib/a.txt').write_text('late mutation')"]
        self.save_profile(commit=True)
        self.put("lib/a.txt", "changed")
        report = self.run_tool(execute=True, expected=1)
        self.assertEqual(self.entries(report)["lib"]["failure_reason"], "inputs_changed_after_verification")

    def test_new_required_check_during_run_invalidates_selection(self):
        self.profile["checks"][0]["command"] = [sys.executable, "-c", "from pathlib import Path; Path('other/a.txt').write_text('new selection')"]
        self.save_profile(commit=True)
        self.put("lib/a.txt", "changed")
        report = self.run_tool(execute=True, expected=1)
        self.assertIn("selection_changed_during_run", report["escalation"])
        self.assertIn("other", report["remaining_gates"])

    def test_new_unknown_input_invalidates_even_when_all_checks_selected(self):
        self.profile["checks"][0]["command"] = [sys.executable, "-c", "from pathlib import Path; Path('unknown.txt').write_text('new')"]
        self.save_profile(commit=True)
        self.put("lib/a.txt", "changed")
        self.put("other/a.txt", "changed")
        report = self.run_tool(execute=True, expected=1)
        self.assertEqual(self.selected(report), {"lib", "app", "other"})
        self.assertIn("conservative_inputs_changed_during_run", report["escalation"])
        self.assertTrue(all(c["status"] == "failed" for c in report["checks"] if c["selected"]))

    def test_unknown_input_mutation_is_monitored_during_escalated_runs(self):
        self.profile["checks"][0]["command"] = [sys.executable, "-c", "from pathlib import Path; Path('unknown.txt').write_text('mutated')"]
        self.save_profile(commit=True)
        self.put("unknown.txt", "initial")
        entry = self.entries(self.run_tool(execute=True, expected=1))["lib"]
        self.assertEqual(entry["failure_reason"], "inputs_changed_during_run")

    def test_repeated_argv_tokens_are_valid_and_fifo_input_is_rejected(self):
        self.profile["checks"][0]["command"] = [sys.executable, "-c", "import sys; assert sys.argv[1:] == ['x', 'x']", "x", "x"]
        self.profile["checks"][0]["runtime_inputs"] = ["lib/pipe"]
        self.save_profile(commit=True)
        self.put("lib/a.txt", "changed")
        self.assertEqual(self.entries(self.run_tool(execute=True))["lib"]["status"], "passed")
        os.mkfifo(self.root / "lib/pipe")
        self.assertEqual(self.entries(self.run_tool(execute=True, expected=1))["lib"]["status"], "failed")

    def test_timeout_and_output_limit(self):
        for code, timeout, reason in (("import time; time.sleep(3)", .1, "timeout"),
                                     ("import sys; sys.stdout.write('x' * 1200000)", 2, "output_limit")):
            self.profile["checks"][0]["command"] = [sys.executable, "-c", code]
            self.profile["checks"][0]["timeout_seconds"] = timeout
            self.save_profile(commit=True)
            self.put("lib/a.txt", "changed")
            entry = self.entries(self.run_tool(execute=True, expected=1))["lib"]
            self.assertEqual(entry["failure_reason"], reason)
            self.assertLessEqual(Path(entry["log"]).stat().st_size, 1024 * 1024)

    def test_minimal_environment_and_fixed_cwd(self):
        code = ("import os; from pathlib import Path; "
                "assert 'HOME' not in os.environ and 'UNDECLARED_SECRET' not in os.environ; "
                "assert os.environ['ALLOW_TEST']=='allowed'; "
                "assert Path.cwd().name=='repo'; assert Path(os.environ['TMPDIR']).is_dir(); "
                "assert os.environ['TZ']=='UTC'")
        self.profile["checks"][0]["command"] = [sys.executable, "-c", code]
        self.profile["checks"][0]["env"] = ["ALLOW_TEST"]
        self.save_profile(commit=True)
        self.put("lib/a.txt", "changed")
        env = dict(os.environ, ALLOW_TEST="allowed", UNDECLARED_SECRET="must-not-leak")
        report = self.run_tool(execute=True, env=env)
        self.assertEqual(self.entries(report)["lib"]["status"], "passed")
        self.assertNotIn("must-not-leak", json.dumps(report))

    def test_unsafe_globs_symlinks_git_root_and_invalid_base(self):
        original = copy.deepcopy(self.profile)
        for pattern in ("../outside", "/absolute", "x/../y", "C:/outside", "x\\y"):
            self.profile = copy.deepcopy(original)
            self.profile["checks"][0]["inputs"] = [pattern]
            self.save_profile()
            self.assertEqual(self.run_tool(expected=2)["status"], "error")
        self.profile = original
        self.save_profile(commit=True)
        self.put("lib/a.txt", "changed")
        (self.root / "lib/link").symlink_to(self.outside, target_is_directory=True)
        self.assertEqual(self.entries(self.run_tool(execute=True, expected=1))["lib"]["status"], "failed")
        (self.root / "lib/link").unlink()
        cache = self.outside / "linked-cache"
        cache.symlink_to(self.outside, target_is_directory=True)
        self.assertEqual(self.run_tool(expected=2, extra=["--cache-dir", str(cache)])["status"], "error")
        self.assertEqual(self.run_tool(expected=2, extra=["--root", str(self.root / "lib")])["status"], "error")
        self.assertEqual(self.run_tool(expected=2, extra=["--base", "not-a-revision"])["status"], "error")

    def test_explicit_cache_report_exclusion_and_no_tracked_overwrite(self):
        self.put("lib/a.txt", "changed")
        cache, report_path = self.root / "local-cache", self.root / "report.json"
        args = ["--cache-dir", str(cache), "--report", str(report_path)]
        first = self.run_tool(execute=True, extra=args)
        second = self.run_tool(execute=True, extra=args)
        self.assertEqual(self.entries(second)["lib"]["status"], "reused")
        self.assertEqual(first["changes"], second["changes"])
        self.assertEqual(json.loads(report_path.read_text())["run_id"], second["run_id"])
        self.assertEqual(self.run_tool(expected=2, extra=["--report", str(self.root / "lib/a.txt")])["status"], "error")
        self.put("lib/untracked.txt", "source")
        self.assertEqual(self.run_tool(expected=2, extra=["--report", str(self.root / "lib/untracked.txt")])["status"], "error")
        self.assertEqual(self.run_tool(expected=2, extra=["--cache-dir", str(self.root / "lib")])["status"], "error")
        self.put("unmapped-cache/source.txt", "source")
        self.assertEqual(self.run_tool(expected=2, extra=["--cache-dir", str(self.root / "unmapped-cache")])["status"], "error")
        self.assertEqual(self.run_tool(expected=2, extra=["--report", str(self.root / ".git/config")])["status"], "error")

    def test_release_executes_in_stage_order(self):
        self.profile["checks"] = list(reversed(self.profile["checks"]))
        self.save_profile(commit=True)
        report = self.run_tool(execute=True, stage="release")
        self.assertEqual([e["stage"] for e in report["checks"]], ["quick", "quick", "quick", "integration", "release"])

    def test_ignored_dependencies_and_generated_outputs_do_not_escalate_or_drift(self):
        self.put(".gitignore", "node_modules/\n.venv/\n.pytest_cache/\nlib/tracked-ignored.txt\n")
        self.put("lib/tracked-ignored.txt", "tracked initial")
        self.profile["checks"][0]["command"] = [sys.executable, "-c",
            "from pathlib import Path; import uuid; p=Path('.pytest_cache'); p.mkdir(exist_ok=True); (p/'state').write_text(uuid.uuid4().hex)"]
        self.git("add", ".gitignore")
        self.git("add", "-f", "lib/tracked-ignored.txt")
        self.save_profile(commit=True)
        self.put("node_modules/dependency/index.js", "ignored dependency")
        self.put(".venv/lib/dependency.py", "ignored dependency")
        self.assertEqual(self.run_tool(execute=True)["status"], "no_checks")
        self.put("lib/tracked-ignored.txt", "tracked change")
        tracked = self.run_tool()
        self.assertIn("lib/tracked-ignored.txt", {c["path"] for c in tracked["changes"]})
        self.assertEqual(self.selected(tracked), {"lib", "app"})
        self.put("lib/tracked-ignored.txt", "tracked initial")
        self.put("lib/a.txt", "source change")
        first = self.run_tool(execute=True)
        self.assertFalse(first["escalation"])
        self.assertEqual(self.entries(first)["lib"]["status"], "passed")
        self.assertEqual(self.entries(self.run_tool(execute=True))["lib"]["status"], "reused")
        # Conservative expansion still hashes Git-related files, not ignored output.
        self.put("unknown-source.txt", "must still expand")
        broad = self.run_tool(execute=True)
        self.assertTrue(any(x.startswith("unmapped_path:") for x in broad["escalation"]))
        self.assertEqual(self.entries(broad)["lib"]["status"], "passed")

    def test_unrelated_large_ignored_directory_is_never_traversed(self):
        self.put(".gitignore", "node_modules/\nruntime/\n")
        self.profile["checks"][0]["runtime_inputs"] = ["runtime/*.json"]
        self.git("add", ".gitignore")
        self.save_profile(commit=True)
        for index in range(80):
            self.put(f"node_modules/dependency-{index}/deep/index.js", "ignored")
        self.put("runtime/config.json", "declared")
        self.put("runtime/irrelevant/deep/output.bin", "not matched by single-segment glob")
        self.put("lib/a.txt", "changed")
        specification = importlib.util.spec_from_file_location("incremental_verify_under_test", RUNNER)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        original_scandir = os.scandir
        visited = []
        def guarded_scandir(path):
            current = Path(path)
            visited.append(current)
            self.assertNotIn(self.root / "node_modules", (current, *current.parents))
            self.assertNotIn(self.root / "runtime/irrelevant", (current, *current.parents))
            return original_scandir(path)
        profile_path = self.root / "profile.json"
        profile, profile_hash = module.load_profile(profile_path)
        with mock.patch.object(module.os, "scandir", side_effect=guarded_scandir):
            key, _ = module.fingerprint(self.root, profile_path, profile, profile_hash, profile["checks"][0], [], self.outside / "tmp")
        self.assertEqual(len(key), 64)
        self.assertEqual(set(visited), {self.root / "runtime", self.root / "config"})
        self.assertEqual(self.entries(self.run_tool(execute=True))["lib"]["status"], "passed")

    def test_explicit_ignored_runtime_add_modify_delete_invalidates_selected_cache(self):
        self.put(".gitignore", "runtime/\n")
        self.profile["checks"][0]["runtime_inputs"] = ["runtime/**"]
        self.git("add", ".gitignore")
        self.save_profile(commit=True)
        self.put("lib/a.txt", "changed")
        first = self.entries(self.run_tool(execute=True))["lib"]
        self.assertEqual(self.entries(self.run_tool(execute=True))["lib"]["status"], "reused")
        self.put("runtime/settings.json", "version one")
        added = self.entries(self.run_tool(execute=True))["lib"]
        self.assertNotEqual(first["fingerprint"], added["fingerprint"])
        self.assertEqual(added["status"], "passed")
        self.put("runtime/settings.json", "version two")
        modified = self.entries(self.run_tool(execute=True))["lib"]
        self.assertNotEqual(added["fingerprint"], modified["fingerprint"])
        self.assertEqual(modified["status"], "passed")
        (self.root / "runtime/settings.json").unlink()
        deleted = self.entries(self.run_tool(execute=True))["lib"]
        self.assertEqual(deleted["fingerprint"], first["fingerprint"])
        self.assertEqual(deleted["status"], "reused")

    def test_timeout_still_applies_after_both_output_streams_close(self):
        self.profile["checks"][0]["command"] = [sys.executable, "-c", "import os,time; os.close(1); os.close(2); time.sleep(.35)"]
        self.profile["checks"][0]["timeout_seconds"] = .05
        self.save_profile(commit=True)
        self.put("lib/a.txt", "changed")
        entry = self.entries(self.run_tool(execute=True, expected=1))["lib"]
        self.assertEqual(entry["failure_reason"], "timeout")
        self.assertLess(entry["duration_seconds"], .3)

    def test_virtualenv_executable_preserves_its_configured_entry_path(self):
        self.put(".gitignore", ".venv/\n")
        self.git("add", ".gitignore")
        venv = self.root / ".venv"
        subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv)], capture_output=True, check=True)
        entry = venv / "bin/python"
        self.assertTrue(entry.is_symlink())
        self.profile["checks"][0]["command"] = [str(entry), "-c", f"import sys; assert sys.prefix == {str(venv)!r}, sys.prefix"]
        self.profile["checks"][0]["runtime_inputs"] = [".venv/pyvenv.cfg"]
        self.save_profile(commit=True)
        self.put("lib/a.txt", "changed")
        self.assertEqual(self.entries(self.run_tool(execute=True))["lib"]["status"], "passed")
        self.assertEqual(self.entries(self.run_tool(execute=True))["lib"]["status"], "reused")

    def test_cache_refuses_git_metadata_in_primary_and_linked_worktrees(self):
        self.put("lib/a.txt", "changed")
        bad = self.root / ".git/refs/heads/verification-cache"
        self.assertEqual(self.run_tool(execute=True, expected=2, extra=["--cache-dir", str(bad)])["status"], "error")
        self.assertFalse(bad.exists())
        self.git("show-ref")
        main_root = self.root
        linked = self.outside / "linked-worktree"
        self.git("worktree", "add", "-qb", "linked-test", str(linked))
        self.root = linked
        self.put("lib/a.txt", "changed")
        private = Path(self.git("rev-parse", "--absolute-git-dir").strip())
        for target in (private / "refs/heads/verification-cache", main_root / ".git/refs/heads/verification-cache",
                       main_root / ".git/incremental-verify/shared"):
            report = self.run_tool(execute=True, expected=2, extra=["--cache-dir", str(target)])
            self.assertEqual(report["status"], "error")
            self.assertFalse(target.exists())
            self.git("show-ref")
        self.assertEqual(self.entries(self.run_tool(execute=True))["lib"]["status"], "passed")

    def test_external_profile_is_plannable_and_always_expands_without_cache(self):
        outside_profile = self.outside / "shared-profile.json"
        outside_profile.write_text(json.dumps(self.profile))
        self.put("lib/a.txt", "changed")
        args = ["--profile", str(outside_profile)]
        plan = self.run_tool(extra=args)
        self.assertEqual(self.selected(plan), {"lib", "app", "other"})
        self.assertIn("profile_not_baselined:outside_repository", plan["escalation"])
        self.assertFalse((self.root / ".git/incremental-verify").exists())
        self.profile["checks"][2]["command"] = [sys.executable, "-c", "raise SystemExit(9)"]
        outside_profile.write_text(json.dumps(self.profile))
        report = self.run_tool(execute=True, expected=1, extra=args)
        self.assertEqual(self.entries(report)["other"]["exit_code"], 9)
        self.assertTrue(all(e["cache"] == "disabled" for e in report["checks"] if e["selected"]))

    def test_ignored_profile_missing_from_base_expands_all_eligible_checks(self):
        self.put(".gitignore", ".local/\n")
        self.git("add", ".gitignore")
        self.git("commit", "-qm", "ignore local profile")
        self.base = self.git("rev-parse", "HEAD").strip()
        self.put(".local/profile.json", json.dumps(self.profile))
        args = ["--profile", str(self.root / ".local/profile.json")]
        plan = self.run_tool(stage="integration", extra=args)
        self.assertEqual(plan["changes"], [])
        self.assertIn("profile_not_baselined:missing_base_blob", plan["escalation"])
        self.assertEqual(self.selected(plan), {"lib", "app", "other", "integrate"})
        report = self.run_tool(execute=True, extra=args)
        self.assertEqual(self.selected(report), {"lib", "app", "other"})
        self.assertTrue(all(e["status"] == "passed" and e["cache"] == "disabled" for e in report["checks"] if e["selected"]))

    def test_untracked_and_newly_committed_profiles_require_caller_baseline(self):
        self.put("lib/a.txt", "changed")
        self.put("new-profile.json", json.dumps(self.profile))
        args = ["--profile", str(self.root / "new-profile.json")]
        untracked = self.run_tool(extra=args)
        self.assertIn("profile_not_baselined:missing_base_blob", untracked["escalation"])
        self.assertEqual(self.selected(untracked), {"lib", "app", "other"})
        self.git("add", "new-profile.json")
        self.git("commit", "-qm", "commit new profile")
        still_missing = self.run_tool(extra=args)
        self.assertIn("profile_not_baselined:missing_base_blob", still_missing["escalation"])
        self.assertEqual(still_missing["base"], self.base)
        self.base = self.git("rev-parse", "HEAD").strip()
        baselined = self.run_tool(extra=args)
        self.assertEqual(self.selected(baselined), {"lib", "app"})
        self.assertFalse(baselined["escalation"])

    def test_profile_content_is_compared_with_base_blob_before_narrowing(self):
        self.put("lib/a.txt", "changed")
        self.assertEqual(self.selected(self.run_tool()), {"lib", "app"})
        self.profile["checks"][2]["command"] = [sys.executable, "-c", "raise SystemExit(9)"]
        self.save_profile()
        changed = self.run_tool(execute=True, expected=1)
        self.assertIn("profile_differs_from_base", changed["escalation"])
        self.assertEqual(self.entries(changed)["other"]["exit_code"], 9)


if __name__ == "__main__":
    unittest.main()
