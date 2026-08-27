#!/usr/bin/env python3
"""Run deterministic behavior contracts against real or replayed agent responses."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import selectors
import signal
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_LIVE_METADATA = {"model", "tool_version"}
DEFAULT_MAX_OUTPUT_BYTES = 1024 * 1024
SECRET_PATTERNS = {
    "private-key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "aws-access-key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "slack-token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "bearer-jwt": re.compile(r"(?i)\bBearer\s+eyJ[A-Za-z0-9_-]{20,}"),
}


class EvalError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def behavior_configuration_digest(skill_root: Path) -> str:
    """Bind evidence to every file that can materially steer skill behavior."""
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


def portable_path(path: Path, skill_root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(skill_root.resolve()).as_posix()
    except ValueError:
        return resolved.name


def load_manifest(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise EvalError(f"Invalid manifest JSON: {exc}") from exc

    if manifest.get("schema_version") != 1:
        raise EvalError("Manifest schema_version must be 1.")
    minimum = manifest.get("minimum_pass_rate")
    if not isinstance(minimum, (int, float)) or not 0 <= minimum <= 1:
        raise EvalError("minimum_pass_rate must be between 0 and 1.")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or len(cases) < 10:
        raise EvalError("Manifest must contain at least 10 behavior cases.")

    global_forbidden = manifest.get("global_forbidden_patterns")
    if not isinstance(global_forbidden, list) or not global_forbidden:
        raise EvalError("Manifest needs global_forbidden_patterns.")
    global_ids: set[str] = set()
    for check in global_forbidden:
        if not isinstance(check, dict):
            raise EvalError("global_forbidden_patterns entries must be objects.")
        check_id = check.get("id")
        pattern = check.get("pattern")
        if not isinstance(check_id, str) or not check_id or check_id in global_ids:
            raise EvalError(f"Invalid or duplicate global forbidden id: {check_id!r}")
        global_ids.add(check_id)
        if not isinstance(pattern, str) or not pattern:
            raise EvalError(f"Global forbidden check {check_id} has no pattern.")
        try:
            re.compile(pattern)
        except re.error as exc:
            raise EvalError(
                f"Global forbidden check {check_id} has invalid regex: {exc}"
            ) from exc

    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise EvalError("Every behavior case must be an object.")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not re.fullmatch(r"[a-z0-9-]+", case_id):
            raise EvalError(f"Invalid behavior case id: {case_id!r}")
        if case_id in seen:
            raise EvalError(f"Duplicate behavior case id: {case_id}")
        seen.add(case_id)
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            raise EvalError(f"Case {case_id} has no prompt.")
        if not isinstance(case.get("critical"), bool):
            raise EvalError(f"Case {case_id} must declare critical as boolean.")
        required = case.get("required_patterns")
        forbidden = case.get("forbidden_patterns")
        if not isinstance(required, list) or not required:
            raise EvalError(f"Case {case_id} needs required_patterns.")
        if not isinstance(forbidden, list):
            raise EvalError(f"Case {case_id} needs forbidden_patterns.")
        check_ids: set[str] = set()
        for collection_name, collection in (
            ("required_patterns", required),
            ("forbidden_patterns", forbidden),
        ):
            for check in collection:
                if not isinstance(check, dict):
                    raise EvalError(f"Case {case_id} {collection_name} entries must be objects.")
                check_id = check.get("id")
                pattern = check.get("pattern")
                if not isinstance(check_id, str) or not check_id:
                    raise EvalError(f"Case {case_id} has an invalid check id.")
                if check_id in check_ids:
                    raise EvalError(f"Case {case_id} repeats check id {check_id}.")
                check_ids.add(check_id)
                if not isinstance(pattern, str) or not pattern:
                    raise EvalError(f"Case {case_id} check {check_id} has no pattern.")
                try:
                    re.compile(pattern)
                except re.error as exc:
                    raise EvalError(
                        f"Case {case_id} check {check_id} has invalid regex: {exc}"
                    ) from exc
    return manifest, raw


def select_cases(manifest: dict[str, Any], selected_ids: list[str]) -> list[dict[str, Any]]:
    cases = manifest["cases"]
    if not selected_ids:
        return cases
    by_id = {case["id"]: case for case in cases}
    unknown = sorted(set(selected_ids) - set(by_id))
    if unknown:
        raise EvalError(f"Unknown behavior case(s): {', '.join(unknown)}")
    return [by_id[case_id] for case_id in selected_ids]


def parse_metadata(items: list[str]) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise EvalError(f"Metadata must use key=value: {item!r}")
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            raise EvalError(f"Metadata must use non-empty key=value: {item!r}")
        if re.search(r"(?i)(secret|token|password|credential|api[_-]?key)", key):
            raise EvalError(f"Sensitive values are not allowed in report metadata: {key!r}")
        metadata[key] = value
    return metadata


def resolve_runner(value: str) -> Path:
    candidate = Path(value).expanduser()
    if candidate.parent != Path(".") or candidate.is_absolute():
        resolved = candidate.resolve()
        if not resolved.is_file():
            raise EvalError(f"Runner is not a file: {resolved}")
    else:
        found = shutil.which(value)
        if found is None:
            raise EvalError(f"Runner was not found on PATH: {value}")
        resolved = Path(found).resolve()
    if not os.access(resolved, os.X_OK):
        raise EvalError(f"Runner is not executable: {resolved}")
    return resolved


def runner_environment(pass_env: list[str]) -> dict[str, str]:
    allowed = {"PATH", "LANG", "LC_ALL", "TMPDIR", "SYSTEMROOT", "WINDIR"}
    allowed.update(pass_env)
    return {key: value for key, value in os.environ.items() if key in allowed}


def terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        elif process.poll() is None:
            process.kill()
    except ProcessLookupError:
        pass
    process.wait()


def run_live_case(
    runner: Path,
    case: dict[str, Any],
    skill_root: Path,
    skill_version: str,
    timeout: int,
    pass_env: list[str],
    max_output_bytes: int,
) -> str:
    payload = {
        "schema_version": 1,
        "case_id": case["id"],
        "prompt": case["prompt"],
        "skill_root": str(skill_root),
        "skill_version": skill_version,
    }
    stdout = bytearray()
    with tempfile.TemporaryDirectory(prefix="behavior-eval-runner-") as temp:
        process = subprocess.Popen(
            [str(runner)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=runner_environment(pass_env),
            cwd=temp,
            start_new_session=os.name == "posix",
        )
        assert process.stdin is not None
        assert process.stdout is not None
        assert process.stderr is not None
        try:
            process.stdin.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
            process.stdin.close()
            selector = selectors.DefaultSelector()
            selector.register(process.stdout, selectors.EVENT_READ, "stdout")
            selector.register(process.stderr, selectors.EVENT_READ, "stderr")
            deadline = time.monotonic() + timeout
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    terminate_process_tree(process)
                    raise EvalError(
                        f"Runner timed out for case {case['id']} after {timeout}s."
                    )
                events = selector.select(timeout=min(remaining, 0.25))
                if not events and process.poll() is not None:
                    events = [
                        (key, selectors.EVENT_READ) for key in selector.get_map().values()
                    ]
                for key, _ in events:
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    if key.data == "stdout":
                        stdout.extend(chunk)
                        if len(stdout) > max_output_bytes:
                            terminate_process_tree(process)
                            raise EvalError(
                                f"Runner output for case {case['id']} exceeds "
                                f"{max_output_bytes} bytes."
                            )
                    else:
                        # Drain stderr without retaining potentially sensitive content.
                        pass
            returncode = process.wait(timeout=max(0.1, deadline - time.monotonic()))
        except (BrokenPipeError, subprocess.TimeoutExpired) as exc:
            terminate_process_tree(process)
            raise EvalError(f"Runner failed or timed out for case {case['id']}.") from exc
        finally:
            process.stdout.close()
            process.stderr.close()
    if returncode != 0:
        raise EvalError(
            f"Runner failed for case {case['id']} with exit {returncode}; "
            "stderr was withheld to reduce accidental secret exposure."
        )
    if not stdout.strip():
        raise EvalError(f"Runner returned an empty response for case {case['id']}.")
    try:
        return stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EvalError(f"Runner output for case {case['id']} is not valid UTF-8.") from exc


def load_replay_response(
    responses_dir: Path, case_id: str, max_output_bytes: int
) -> str:
    candidates = [responses_dir / f"{case_id}.txt", responses_dir / f"{case_id}.md"]
    found = [path for path in candidates if path.is_file() and not path.is_symlink()]
    if len(found) != 1:
        raise EvalError(
            f"Case {case_id} needs exactly one response file named {case_id}.txt or {case_id}.md."
        )
    data = found[0].read_bytes()
    if len(data) > max_output_bytes:
        raise EvalError(
            f"Replay output for case {case_id} exceeds {max_output_bytes} bytes."
        )
    text = data.decode("utf-8")
    if not text.strip():
        raise EvalError(f"Response file is empty: {found[0]}")
    return text


def potential_secret_matches(response: str) -> list[str]:
    return [name for name, pattern in SECRET_PATTERNS.items() if pattern.search(response)]


def evaluate_case(
    case: dict[str, Any],
    response: str,
    global_forbidden_patterns: list[dict[str, str]],
) -> dict[str, Any]:
    missing_required = [
        check["id"]
        for check in case["required_patterns"]
        if re.search(check["pattern"], response) is None
    ]
    forbidden_matches = [
        check["id"]
        for check in [*global_forbidden_patterns, *case["forbidden_patterns"]]
        if re.search(check["pattern"], response) is not None
    ]
    secret_matches = potential_secret_matches(response)
    passed = not missing_required and not forbidden_matches and not secret_matches
    return {
        "id": case["id"],
        "critical": case["critical"],
        "passed": passed,
        "missing_required": missing_required,
        "forbidden_matches": forbidden_matches,
        "secret_matches": secret_matches,
        "response_sha256": sha256_bytes(response.encode("utf-8")),
    }


def compare_baseline(
    report: dict[str, Any], baseline_path: Path, skill_root: Path
) -> dict[str, Any]:
    try:
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvalError(f"Unable to read baseline report: {exc}") from exc
    if not isinstance(baseline, dict) or baseline.get("schema_version") != 1:
        raise EvalError("Baseline report schema_version must be 1.")
    baseline_version = baseline.get("skill_version")
    if not isinstance(baseline_version, str) or not re.fullmatch(
        r"\d+\.\d+\.\d+", baseline_version
    ):
        raise EvalError("Baseline report needs a semantic skill_version.")
    baseline_metadata = baseline.get("metadata")
    if not isinstance(baseline_metadata, dict) or not isinstance(
        baseline_metadata.get("configuration_digest"), str
    ):
        raise EvalError("Baseline report needs a configuration_digest.")
    if baseline.get("manifest_sha256") != report.get("manifest_sha256"):
        raise EvalError(
            "Baseline manifest is incompatible; rescore baseline responses with the current manifest."
        )
    baseline_case_list = baseline.get("cases")
    if not isinstance(baseline_case_list, list):
        raise EvalError("Baseline report cases must be a list.")
    baseline_cases: dict[str, dict[str, Any]] = {}
    for case in baseline_case_list:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise EvalError("Baseline report contains an invalid case.")
        if case["id"] in baseline_cases:
            raise EvalError(f"Baseline report repeats case {case['id']}.")
        if not isinstance(case.get("passed"), bool):
            raise EvalError(f"Baseline case {case['id']} has no boolean passed value.")
        baseline_cases[case["id"]] = case
    current_ids = {case["id"] for case in report["cases"]}
    if set(baseline_cases) != current_ids:
        raise EvalError("Baseline and candidate must contain the same behavior case ids.")
    recomputed_baseline_rate = round(
        sum(case["passed"] for case in baseline_cases.values()) / len(baseline_cases),
        4,
    )
    baseline_rate = baseline.get("pass_rate")
    if baseline_rate != recomputed_baseline_rate:
        raise EvalError("Baseline pass_rate does not match its case results.")
    regressions = [
        case["id"]
        for case in report["cases"]
        if baseline_cases.get(case["id"], {}).get("passed") is True and not case["passed"]
    ]
    lower_pass_rate = report["pass_rate"] < baseline_rate
    return {
        "baseline": portable_path(baseline_path, skill_root),
        "baseline_sha256": sha256_bytes(baseline_path.read_bytes()),
        "baseline_skill_version": baseline_version,
        "baseline_configuration_digest": baseline_metadata["configuration_digest"],
        "baseline_pass_rate": baseline_rate,
        "lower_pass_rate": lower_pass_rate,
        "regressed_cases": regressions,
        "passed": not lower_pass_rate and not regressions,
    }


def write_response(path: Path, response: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise EvalError(f"Refusing to overwrite existing response evidence: {path}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        data = response.encode("utf-8")
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("Unable to write behavior response evidence.")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def validate_semantic_review(
    review_path: Path,
    outcomes: list[dict[str, Any]],
    manifest_sha256: str,
    skill_version: str,
    skill_root: Path,
) -> dict[str, Any]:
    try:
        review = json.loads(review_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvalError(f"Unable to read semantic review: {exc}") from exc
    if not isinstance(review, dict) or review.get("schema_version") != 1:
        raise EvalError("Semantic review schema_version must be 1.")
    if review.get("skill_version") != skill_version:
        raise EvalError("Semantic review does not match the skill version.")
    if review.get("manifest_sha256") != manifest_sha256:
        raise EvalError("Semantic review does not match the behavior manifest.")
    for field in ("reviewed_at", "reviewer_context", "reviewer_id", "method", "limitations"):
        if not isinstance(review.get(field), str) or not review[field].strip():
            raise EvalError(f"Semantic review needs non-empty {field}.")
    review_cases_raw = review.get("cases")
    if not isinstance(review_cases_raw, list):
        raise EvalError("Semantic review cases must be a list.")
    review_cases: dict[str, dict[str, Any]] = {}
    for case in review_cases_raw:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise EvalError("Semantic review contains an invalid case.")
        if case["id"] in review_cases:
            raise EvalError(f"Semantic review repeats case {case['id']}.")
        if not isinstance(case.get("passed"), bool):
            raise EvalError(f"Semantic review case {case['id']} needs boolean passed.")
        if not isinstance(case.get("findings"), list):
            raise EvalError(f"Semantic review case {case['id']} needs findings list.")
        review_cases[case["id"]] = case
    outcome_by_id = {case["id"]: case for case in outcomes}
    if set(review_cases) != set(outcome_by_id):
        raise EvalError("Semantic review and contract results must contain the same cases.")
    for case_id, outcome in outcome_by_id.items():
        reviewed = review_cases[case_id]
        if reviewed.get("response_sha256") != outcome["response_sha256"]:
            raise EvalError(f"Semantic review response digest mismatch: {case_id}")
    failed = sorted(case_id for case_id, case in review_cases.items() if not case["passed"])
    overall_passed = review.get("overall_passed") is True and not failed
    return {
        "path": portable_path(review_path, skill_root),
        "sha256": sha256_bytes(review_path.read_bytes()),
        "reviewer_context": review["reviewer_context"],
        "reviewer_id": review["reviewer_id"],
        "failed_cases": failed,
        "passed": overall_passed,
    }


def parse_args() -> argparse.Namespace:
    skill_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=skill_root / "evals" / "behavior_contracts.json",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-only", action="store_true")
    mode.add_argument("--responses-dir", type=Path)
    mode.add_argument("--runner", help="Explicit executable implementing the JSON-stdin adapter contract.")
    parser.add_argument("--case", action="append", default=[], dest="cases")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--max-output-bytes", type=int, default=DEFAULT_MAX_OUTPUT_BYTES)
    parser.add_argument("--pass-env", action="append", default=[])
    parser.add_argument("--metadata", action="append", default=[])
    parser.add_argument("--save-responses-dir", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--semantic-review", type=Path)
    parser.add_argument("--require-semantic-review", action="store_true")
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    skill_root = Path(__file__).resolve().parents[1]
    try:
        manifest, manifest_raw = load_manifest(args.manifest.resolve())
        selected = select_cases(manifest, args.cases)
        if args.cases and len(selected) < 3 and not args.allow_partial:
            raise EvalError("Focused runs need at least three cases unless --allow-partial is explicit.")
        metadata = parse_metadata(args.metadata)
        if "configuration_digest" in metadata:
            raise EvalError(
                "configuration_digest is computed from the skill and cannot be supplied."
            )
        metadata["configuration_digest"] = behavior_configuration_digest(skill_root)
        if args.max_output_bytes <= 0:
            raise EvalError("--max-output-bytes must be positive.")
        if args.validate_only:
            print(
                json.dumps(
                    {
                        "valid": True,
                        "cases": len(manifest["cases"]),
                        "manifest_sha256": sha256_bytes(manifest_raw),
                    },
                    indent=2,
                )
            )
            return 0

        mode = "live" if args.runner else "replay"
        runner: Path | None = None
        if mode == "live":
            missing_metadata = sorted(REQUIRED_LIVE_METADATA - set(metadata))
            if missing_metadata:
                raise EvalError(
                    "Live runs require metadata: " + ", ".join(missing_metadata)
                )
            if args.save_responses_dir is None:
                raise EvalError("Live runs require --save-responses-dir for auditable raw output.")
            runner = resolve_runner(args.runner)

        skill_version = (skill_root / "VERSION").read_text(encoding="utf-8").strip()
        outcomes: list[dict[str, Any]] = []
        for case in selected:
            if mode == "live":
                assert runner is not None
                response = run_live_case(
                    runner,
                    case,
                    skill_root,
                    skill_version,
                    args.timeout,
                    args.pass_env,
                    args.max_output_bytes,
                )
                write_response(args.save_responses_dir.resolve() / f"{case['id']}.txt", response)
            else:
                response = load_replay_response(
                    args.responses_dir.resolve(), case["id"], args.max_output_bytes
                )
            outcomes.append(
                evaluate_case(case, response, manifest["global_forbidden_patterns"])
            )

        passed_count = sum(case["passed"] for case in outcomes)
        pass_rate = round(passed_count / len(outcomes), 4)
        critical_failed = [
            case["id"] for case in outcomes if case["critical"] and not case["passed"]
        ]
        report: dict[str, Any] = {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "skill_version": skill_version,
            "manifest": portable_path(args.manifest, skill_root),
            "manifest_sha256": sha256_bytes(manifest_raw),
            "mode": mode,
            "metadata": metadata,
            "selected_cases": len(outcomes),
            "passed_cases": passed_count,
            "pass_rate": pass_rate,
            "minimum_pass_rate": manifest["minimum_pass_rate"],
            "critical_failed": critical_failed,
            "cases": outcomes,
        }
        report["contract_passed"] = (
            pass_rate >= manifest["minimum_pass_rate"] and not critical_failed
        )
        semantic_summary: dict[str, Any] | None = None
        if args.semantic_review:
            semantic_summary = validate_semantic_review(
                args.semantic_review.resolve(),
                outcomes,
                report["manifest_sha256"],
                skill_version,
                skill_root,
            )
            report["semantic_review"] = semantic_summary
        elif args.require_semantic_review:
            raise EvalError("--require-semantic-review needs --semantic-review.")
        report["behavior_passed"] = (
            report["contract_passed"] and semantic_summary["passed"]
            if semantic_summary is not None
            else None
        )
        report["suite_passed"] = (
            report["behavior_passed"]
            if semantic_summary is not None
            else report["contract_passed"]
        )
        if args.baseline:
            report["baseline_comparison"] = compare_baseline(
                report, args.baseline, skill_root
            )
            report["suite_passed"] = (
                report["suite_passed"] and report["baseline_comparison"]["passed"]
            )

        rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.report:
            args.report.resolve().parent.mkdir(parents=True, exist_ok=True)
            args.report.resolve().write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0 if report["suite_passed"] else 1
    except (EvalError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
