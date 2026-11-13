#!/usr/bin/env python3
"""Check local delivery-evidence consistency; never execute manifest commands."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
from datetime import datetime
from pathlib import Path, PureWindowsPath

STAGES = ("local", "release", "observation")
STATUSES = ("passed", "failed", "not_run", "not_applicable")
LIMITATIONS = [
    "Consistency only: this does not prove execution, outcomes, or commercial readiness.",
    "Local digests do not prove reviewer identity, independence, or approval authenticity.",
    "The expected revision is caller-supplied; Git state and remote systems are not verified.",
    "Historical reuse reasons do not prove continued applicability of previous results.",
    "Run IDs and timestamps are declarations; their presence does not prove a run occurred or was fresh.",
    "N/A reasons do not prove applicability or project acceptance of an exemption; "
    "unimplemented requirements must not be waived as not_applicable.",
    "Artifacts must be non-sensitive; no network access, credential lookup, or command execution occurs.",
    "A v2 result checks only this evidence contract, not full lifecycle readiness or authority legitimacy.",
]


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise ValueError("non-finite JSON number")


def finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("overflowed JSON number")
    return number


class Validator:
    def __init__(self, root: Path, revision: str, stage: str, require_v2: bool = False):
        self.root, self.revision, self.stage = root, revision, stage
        self.require_v2 = require_v2
        self.schema_version: int | None = None
        self.errors: list[str] = []

    def need(self, condition: bool, field: str, message: str) -> bool:
        if not condition:
            self.errors.append(f"{field}: {message}")
        return condition

    def text(self, value: object, field: str) -> bool:
        return self.need(isinstance(value, str) and bool(value.strip()), field,
                         "must be a non-empty string")

    def obj(self, value: object, field: str) -> dict:
        return value if self.need(isinstance(value, dict), field, "must be an object") else {}

    def items(self, value: object, field: str) -> list:
        valid = isinstance(value, list) and bool(value)
        return value if self.need(valid, field, "must be a non-empty array") else []

    def revision_is_current(self, value: object, field: str) -> None:
        self.need(value == self.revision, field, "must match --revision")

    def timestamp(self, value: object, field: str) -> None:
        valid = False
        if isinstance(value, str) and "T" in value:
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                valid = parsed.tzinfo is not None and parsed.utcoffset() is not None
            except ValueError:
                pass
        self.need(valid, field, "must be an ISO 8601 timestamp with a timezone")

    def scope_decision(self, record: dict, field: str) -> None:
        self.text(record.get("reason"), f"{field}.reason")
        self.text(record.get("scope_or_policy_ref"), f"{field}.scope_or_policy_ref")
        self.artifact(record.get("decision_artifact"), f"{field}.decision_artifact")

    def v2_check(self, check: dict, field: str, relevant: bool) -> None:
        fresh = check.get("fresh_required")
        self.need(type(fresh) is bool, f"{field}.fresh_required", "must be a boolean")
        if check.get("status") == "not_applicable":
            self.text(check.get("scope_or_policy_ref"), f"{field}.scope_or_policy_ref")
        if check.get("status") != "passed":
            return
        origin = check.get("origin")
        self.need(origin in ("executed", "reused"), f"{field}.origin",
                  "must be executed or reused for a passed check")
        self.need(isinstance(check.get("run_revision"), str)
                  and bool(re.fullmatch(r"[0-9a-fA-F]{40}", check["run_revision"])),
                  f"{field}.run_revision", "passed v2 checks require an explicit 40-hex Git SHA")
        if origin == "executed":
            self.text(check.get("run_id"), f"{field}.run_id")
            self.timestamp(check.get("executed_at"), f"{field}.executed_at")
        if origin == "reused":
            self.text(check.get("reuse_reason"), f"{field}.reuse_reason")
        if fresh is True and relevant:
            self.revision_is_current(check.get("run_revision"), f"{field}.run_revision")
            self.need(origin == "executed", f"{field}.origin",
                      "a fresh required check must declare a current executed run")

    def v2_release(self, data: dict, release: dict, checks: dict,
                   requirement_ids: set, in_scope_ids: set) -> None:
        if release.get("status") == "deployed":
            refs = release.get("smoke_check_ids")
            for ref in refs if isinstance(refs, list) else []:
                if not isinstance(ref, str):
                    continue  # The base contract reports malformed references.
                check = checks.get(ref, {})
                field = f"release.smoke_check_ids[{ref}]"
                self.need(check.get("category") == "deployment_smoke", field,
                          "must reference category deployment_smoke")
                self.need(isinstance(check.get("required_for"), list)
                          and self.stage in check["required_for"], field,
                          "smoke must be required for the selected stage")
                self.need(check.get("origin") == "executed", field,
                          "smoke must declare an executed run, never reused evidence")
                self.text(check.get("run_id"), f"{field}.run_id")
                self.timestamp(check.get("executed_at"), f"{field}.executed_at")
                for key in ("environment", "deployment_id"):
                    self.text(check.get(key), f"{field}.{key}")
                    self.need(check.get(key) == release.get(key), f"{field}.{key}",
                              f"must match release.{key}")

        acceptance = self.obj(data.get("business_acceptance"), "business_acceptance")
        self.revision_is_current(acceptance.get("revision"), "business_acceptance.revision")
        if acceptance.get("status") == "not_applicable":
            self.scope_decision(acceptance, "business_acceptance")
        else:
            self.need(acceptance.get("status") == "accepted", "business_acceptance.status",
                      "must be accepted or scoped not_applicable")
            self.text(acceptance.get("responsible_owner"), "business_acceptance.responsible_owner")
            self.need(acceptance.get("method") in ("owner_acceptance", "delegated"),
                      "business_acceptance.method", "must be owner_acceptance or delegated")
            refs = self.items(acceptance.get("requirement_ids"), "business_acceptance.requirement_ids")
            accepted_ids = set()
            for ref in refs:
                if self.text(ref, "business_acceptance.requirement_ids"):
                    self.need(ref not in accepted_ids, "business_acceptance.requirement_ids",
                              "requirement IDs must be unique")
                    self.need(ref in requirement_ids, "business_acceptance.requirement_ids",
                              "unknown requirement reference")
                    accepted_ids.add(ref)
            self.need(in_scope_ids <= accepted_ids, "business_acceptance.requirement_ids",
                      "must cover every in-scope requirement")
            self.artifact(acceptance.get("artifact"), "business_acceptance.artifact")
            if acceptance.get("method") == "delegated":
                self.text(acceptance.get("authority_ref"), "business_acceptance.authority_ref")
                self.artifact(acceptance.get("authority_artifact"),
                              "business_acceptance.authority_artifact")

        operations = self.obj(data.get("operations_handoff"), "operations_handoff")
        self.revision_is_current(operations.get("revision"), "operations_handoff.revision")
        applicable = operations.get("applicable")
        self.need(type(applicable) is bool, "operations_handoff.applicable", "must be a boolean")
        if applicable is False:
            self.scope_decision(operations, "operations_handoff")
        elif applicable is True:
            self.need(operations.get("status") == "accepted", "operations_handoff.status",
                      "must be accepted")
            for key in ("owner", "observation_window", "escalation"):
                self.text(operations.get(key), f"operations_handoff.{key}")
            self.need(operations.get("access_confirmed") is True,
                      "operations_handoff.access_confirmed", "must be boolean true")
            self.timestamp(operations.get("next_check_at"), "operations_handoff.next_check_at")
            self.artifact(operations.get("artifact"), "operations_handoff.artifact")

    def artifact(self, value: object, field: str) -> None:
        artifact = self.obj(value, field)
        path, expected = artifact.get("path"), artifact.get("sha256")
        path_ok = self.text(path, f"{field}.path")
        hash_ok = isinstance(expected, str) and re.fullmatch(r"[0-9a-fA-F]{64}", expected)
        self.need(bool(hash_ok), f"{field}.sha256", "must be a 64-hex SHA256")
        if not path_ok:
            return
        parts = path.split("/")
        safe = (not Path(path).is_absolute() and not PureWindowsPath(path).anchor
                and "\\" not in path and all(p not in ("", ".", "..") for p in parts))
        if not self.need(safe, f"{field}.path", "must be a relative path inside --root"):
            return
        # Descriptor-relative opens refuse symlinks in every artifact component, even
        # if a directory is replaced between validation and reading. Never run commands.
        descriptors = []
        try:
            flags = os.O_RDONLY | os.O_NOFOLLOW
            descriptors.append(os.open(self.root, flags | os.O_DIRECTORY))
            for part in parts[:-1]:
                descriptors.append(os.open(part, flags | os.O_DIRECTORY,
                                           dir_fd=descriptors[-1]))
            fd = os.open(parts[-1], flags | os.O_NONBLOCK, dir_fd=descriptors[-1])
            descriptors.append(fd)
            if not self.need(stat.S_ISREG(os.fstat(fd).st_mode), field,
                             "must reference a regular file without symlinks"):
                return
            digest = hashlib.sha256()
            while chunk := os.read(fd, 1024 * 1024):
                digest.update(chunk)
            if hash_ok:
                self.need(digest.hexdigest() == expected.lower(), field, "SHA256 mismatch")
        except (OSError, ValueError, AttributeError, NotImplementedError):
            self.need(False, field, "cannot read regular artifact without symlinks")
        finally:
            for descriptor in reversed(descriptors):
                os.close(descriptor)

    def validate(self, value: object) -> None:
        data = self.obj(value, "manifest")
        version = data.get("schema_version")
        if self.need(type(version) is int and version in (1, 2),
                     "schema_version", "must be integer 1 or 2"):
            self.schema_version = version
        v2 = self.schema_version == 2
        if self.require_v2:
            self.need(v2, "schema_version", "--require-v2 requires schema_version 2; legacy is not v2")
        self.revision_is_current(data.get("revision"), "revision")
        checks = {}
        for index, item in enumerate(self.items(data.get("checks"), "checks")):
            field = f"checks[{index}]"
            check = self.obj(item, field)
            ident = check.get("id")
            if self.text(ident, f"{field}.id"):
                self.need(ident not in checks, f"{field}.id", "duplicate check ID")
                checks.setdefault(ident, check)
            self.text(check.get("category"), f"{field}.category")
            status = check.get("status")
            self.need(isinstance(status, str) and status in STATUSES, f"{field}.status",
                      "must be passed, failed, not_run, or not_applicable")
            required = self.items(check.get("required_for"), f"{field}.required_for")
            self.need(all(isinstance(s, str) and s in STAGES for s in required),
                      f"{field}.required_for", "contains an unknown stage")
            self.need(len(required) == len({s for s in required if isinstance(s, str)}),
                      f"{field}.required_for", "stages must be unique strings")
            self.revision_is_current(check.get("applies_to_revision"),
                                     f"{field}.applies_to_revision")
            run_revision = check.get("run_revision", self.revision)
            self.need(isinstance(run_revision, str)
                      and bool(re.fullmatch(r"[0-9a-fA-F]{40}", run_revision)),
                      f"{field}.run_revision", "must be a 40-hex Git SHA")
            if run_revision != self.revision:
                self.text(check.get("reuse_reason"), f"{field}.reuse_reason")
            if status == "not_applicable":
                self.text(check.get("reason"), f"{field}.reason")
            if status == "passed" or "artifact" in check:
                self.artifact(check.get("artifact"), f"{field}.artifact")
            if v2:
                self.v2_check(check, field, self.stage in required)
            if self.stage in required:
                self.need(status not in ("failed", "not_run"), f"{field}.status",
                          f"required {self.stage} check has not passed or been explicitly waived")

        requirement_ids = set()
        in_scope_ids = set()
        for index, item in enumerate(self.items(data.get("requirements"), "requirements")):
            field = f"requirements[{index}]"
            requirement = self.obj(item, field)
            ident = requirement.get("id")
            if self.text(ident, f"{field}.id"):
                self.need(ident not in requirement_ids, f"{field}.id", "duplicate requirement ID")
                requirement_ids.add(ident)
            self.text(requirement.get("description"), f"{field}.description")
            disposition = requirement.get("disposition", "in_scope") if v2 else "in_scope"
            self.need(disposition in ("in_scope", "removed", "not_applicable"),
                      f"{field}.disposition", "must be in_scope, removed, or not_applicable")
            scoped_out = v2 and disposition in ("removed", "not_applicable")
            if disposition == "in_scope" and isinstance(ident, str) and ident.strip():
                in_scope_ids.add(ident)
            if scoped_out:
                self.scope_decision(requirement, field)
                refs = requirement.get("check_ids", [])
                if not self.need(isinstance(refs, list), f"{field}.check_ids", "must be an array"):
                    refs = []
            else:
                refs = self.items(requirement.get("check_ids"), f"{field}.check_ids")
            coverage = False
            passed_coverage = False
            for ref in refs:
                if not self.text(ref, f"{field}.check_ids"):
                    continue
                self.need(ref in checks, f"{field}.check_ids", "unknown check reference")
                required = checks.get(ref, {}).get("required_for", [])
                coverage |= isinstance(required, list) and self.stage in required
                passed_coverage |= (isinstance(required, list) and self.stage in required
                                    and checks.get(ref, {}).get("status") == "passed")
            if not scoped_out:
                self.need(coverage, field, f"has no check applicable to {self.stage}")
                if v2:
                    self.need(passed_coverage, field,
                              f"in-scope requirement needs a passed {self.stage} check; all N/A is insufficient")

        if self.stage in ("release", "observation"):
            review = self.obj(data.get("review"), "review")
            self.need(review.get("status") == "passed", "review.status", "must be passed")
            self.revision_is_current(review.get("revision"), "review.revision")
            self.text(review.get("reviewer"), "review.reviewer")
            self.artifact(review.get("artifact"), "review.artifact")
            release = self.obj(data.get("release"), "release")
            self.need(release.get("status") in ("planned", "deployed"), "release.status",
                      "must be planned or deployed")
            self.revision_is_current(release.get("revision"), "release.revision")
            self.text(release.get("environment"), "release.environment")
            approval = self.obj(release.get("approval"), "release.approval")
            self.text(approval.get("by"), "release.approval.by")
            self.artifact(approval.get("artifact"), "release.approval.artifact")
            if release.get("status") == "deployed":
                self.text(release.get("deployment_id"), "release.deployment_id")
                self.text(release.get("url"), "release.url")
                refs = self.items(release.get("smoke_check_ids"), "release.smoke_check_ids")
                for ref in refs:
                    if not self.text(ref, "release.smoke_check_ids"):
                        continue
                    check = checks.get(ref, {})
                    self.need(check.get("status") == "passed"
                              and check.get("applies_to_revision") == self.revision
                              and check.get("run_revision", self.revision) == self.revision,
                              "release.smoke_check_ids", "must reference a current-run passed check")
            if v2:
                self.v2_release(data, release, checks, requirement_ids, in_scope_ids)
            if self.stage == "observation":
                self.need(release.get("status") == "deployed", "release.status",
                          "observation requires deployed evidence")
                observations = self.items(data.get("observations"), "observations")
                for index, item in enumerate(observations):
                    field = f"observations[{index}]"
                    observation = self.obj(item, field)
                    for key in ("metric", "period", "owner", "decision"):
                        self.text(observation.get(key), f"{field}.{key}")
                    for key in ("expected", "actual"):
                        value = observation.get(key)
                        present = value is not None and value not in ("", [], {})
                        if isinstance(value, str):
                            present = bool(value.strip())
                        self.need(present, f"{field}.{key}", "must not be missing or empty (0 is valid)")
                    self.artifact(observation.get("artifact"), f"{field}.artifact")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", required=True, type=Path, help="root of non-sensitive local artifacts")
    parser.add_argument("--revision", required=True, help="expected 40-hex Git SHA supplied by caller")
    parser.add_argument("--stage", required=True, choices=STAGES)
    parser.add_argument("--require-v2", action="store_true", help="reject legacy schema 1 evidence")
    args = parser.parse_args()
    validator = Validator(args.root, args.revision, args.stage, args.require_v2)
    validator.need(bool(re.fullmatch(r"[0-9a-fA-F]{40}", args.revision)),
                   "--revision", "must be a 40-hex Git SHA")
    validator.need(args.root.is_dir(), "--root", "must be an existing directory")
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"),
                          object_pairs_hook=unique_object, parse_constant=reject_constant,
                          parse_float=finite_float)
        validator.validate(data)
    except (OSError, ValueError, RecursionError):
        validator.need(False, "manifest", "cannot read valid, unambiguous JSON")
    level = ("v2_release_evidence" if validator.schema_version == 2 else
             "legacy_consistency" if validator.schema_version == 1 else "unrecognized")
    print(json.dumps({"schema_version": validator.schema_version,
                      "contract_level": level, "stage": args.stage, "revision": args.revision,
                      "consistency_only": True,
                      "readiness": "evidence_consistent" if not validator.errors else "evidence_inconsistent",
                      "errors": validator.errors, "limitations": LIMITATIONS}, indent=2))
    return 1 if validator.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
