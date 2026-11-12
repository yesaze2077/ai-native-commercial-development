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
from pathlib import Path, PureWindowsPath

STAGES = ("local", "release", "observation")
STATUSES = ("passed", "failed", "not_run", "not_applicable")
LIMITATIONS = [
    "Consistency only: this does not prove execution, outcomes, or commercial readiness.",
    "Local digests do not prove reviewer identity, independence, or approval authenticity.",
    "The expected revision is caller-supplied; Git state and remote systems are not verified.",
    "Historical reuse reasons do not prove continued applicability of previous results.",
    "N/A reasons do not prove applicability or project acceptance of an exemption; "
    "unimplemented requirements must not be waived as not_applicable.",
    "Artifacts must be non-sensitive; no network access, credential lookup, or command execution occurs.",
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
    def __init__(self, root: Path, revision: str, stage: str):
        self.root, self.revision, self.stage = root, revision, stage
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
        self.need(type(data.get("schema_version")) is int and data["schema_version"] == 1,
                  "schema_version", "must be integer 1")
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
            if self.stage in required:
                self.need(status not in ("failed", "not_run"), f"{field}.status",
                          f"required {self.stage} check has not passed or been explicitly waived")

        requirement_ids = set()
        for index, item in enumerate(self.items(data.get("requirements"), "requirements")):
            field = f"requirements[{index}]"
            requirement = self.obj(item, field)
            ident = requirement.get("id")
            if self.text(ident, f"{field}.id"):
                self.need(ident not in requirement_ids, f"{field}.id", "duplicate requirement ID")
                requirement_ids.add(ident)
            self.text(requirement.get("description"), f"{field}.description")
            refs = self.items(requirement.get("check_ids"), f"{field}.check_ids")
            coverage = False
            for ref in refs:
                if not self.text(ref, f"{field}.check_ids"):
                    continue
                self.need(ref in checks, f"{field}.check_ids", "unknown check reference")
                required = checks.get(ref, {}).get("required_for", [])
                coverage |= isinstance(required, list) and self.stage in required
            self.need(coverage, field, f"has no check applicable to {self.stage}")

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
    args = parser.parse_args()
    validator = Validator(args.root, args.revision, args.stage)
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
    print(json.dumps({"schema_version": 1, "stage": args.stage, "revision": args.revision,
                      "consistency_only": True,
                      "readiness": "evidence_consistent" if not validator.errors else "evidence_inconsistent",
                      "errors": validator.errors, "limitations": LIMITATIONS}, indent=2))
    return 1 if validator.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
