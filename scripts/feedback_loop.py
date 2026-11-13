#!/usr/bin/env python3
"""Record redacted usage feedback and suggest review; never change or approve rules."""
from __future__ import annotations

import argparse
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import time

KIND = "commercial-skill-feedback"
MAX_BYTES = 2 * 1024 * 1024
MAX_RECORDS = 2000
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,119}$")
PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
SEVERITIES = {"low": 0, "medium": 1, "high": 2, "critical": 3}
CAUSES = {"unknown", "product-defect", "requirements-gap", "project-config",
          "tool-environment", "workflow-rule", "user-preference"}
PROJECT_CAUSES = {"product-defect", "requirements-gap", "project-config", "tool-environment"}
SENSITIVE = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|\bAKIA[0-9A-Z]{16}\b|"
    r"\bgh[pousr]_[A-Za-z0-9]{20,}\b|\bsk-[A-Za-z0-9_-]{20,}\b|"
    r"\bxox[baprs]-[A-Za-z0-9-]{15,}\b|\bBearer\s+[A-Za-z0-9._-]{20,}|"
    r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b|"
    r"\b(?:api[_-]?key|token|password|secret)\s*[=:]\s*[^\s\"']{8,}", re.I)


class FeedbackError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def material_digest(record):
    return digest({key: value for key, value in record.items() if key != "id"})


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise FeedbackError("Duplicate JSON keys are not allowed.")
        result[key] = value
    return result


def text(value, name, limit=1000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise FeedbackError("Invalid text field: " + name)
    if any(ord(c) < 32 and c not in "\n\t" for c in value):
        raise FeedbackError("Control characters are not allowed.")
    if SENSITIVE.search(value):
        raise FeedbackError("Possible sensitive data rejected; redact the input before retrying.")
    return value


def fields(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or not set(required) <= set(value):
        raise FeedbackError("Missing or unsupported record fields.")
    if type(value.get("schema_version")) is not int or value.get("schema_version") != 1 or value.get("redacted") is not True:
        raise FeedbackError("Records require schema_version 1 and redacted true.")


def event(value):
    required = {"schema_version", "redacted", "id", "occurrence_id", "project", "pattern_key",
                "category", "severity", "root_cause", "scope", "summary", "expected", "actual",
                "evidence", "skill_version"}
    fields(value, required, {"outcome"})
    for key in required - {"schema_version", "redacted", "evidence"}:
        text(value[key], key)
    for key in ("id", "occurrence_id", "project"):
        if not ID.fullmatch(value[key]):
            raise FeedbackError("Use a short non-sensitive alias for identifiers.")
    if not PATTERN.fullmatch(value["pattern_key"]):
        raise FeedbackError("pattern_key must be a lowercase slug.")
    if value["category"] not in {"boundary", "feature", "correction", "efficiency", "incident", "outcome"}:
        raise FeedbackError("Invalid category.")
    if value["severity"] not in SEVERITIES or value["root_cause"] not in CAUSES or value["scope"] not in {"project", "global", "unknown"}:
        raise FeedbackError("Invalid severity, cause or scope.")
    if not re.fullmatch(r"\d+\.\d+\.\d+", value["skill_version"]):
        raise FeedbackError("Invalid skill version.")
    if value["category"] == "outcome":
        if not isinstance(value.get("outcome"), str) or value["outcome"] not in {"improved", "regressed", "unknown"}:
            raise FeedbackError("Outcome observations require improved, regressed or unknown.")
    elif "outcome" in value:
        raise FeedbackError("outcome is only valid for outcome observations.")
    if not isinstance(value["evidence"], list) or not 1 <= len(value["evidence"]) <= 10:
        raise FeedbackError("Provide one to ten redacted evidence references.")
    for item in value["evidence"]:
        if not isinstance(item, dict) or set(item) != {"kind", "ref"} or not isinstance(item["kind"], str) or item["kind"] not in {"observed", "reported"}:
            raise FeedbackError("Invalid evidence reference.")
        text(item["ref"], "evidence.ref", 300)
    return value


def decision(value, events):
    fields(value, {"schema_version", "redacted", "pattern_key", "reviewed_event_ids", "disposition",
                   "reason", "user_ref", "proposal_ref"})
    for key in ("pattern_key", "disposition", "reason", "user_ref", "proposal_ref"):
        text(value[key], key)
    if not PATTERN.fullmatch(value["pattern_key"]) or value["disposition"] not in {"deferred", "rejected", "applied"}:
        raise FeedbackError("Invalid decision pattern or disposition.")
    ids = value["reviewed_event_ids"]
    if not isinstance(ids, list) or not ids or not all(isinstance(i, str) for i in ids) or len(set(ids)) != len(ids):
        raise FeedbackError("reviewed_event_ids must be a nonempty unique list.")
    known = {e["id"] for e in events if e["pattern_key"] == value["pattern_key"]}
    if not set(ids) <= known:
        raise FeedbackError("Decision references missing or unrelated events.")
    return value


def safe_path(path):
    if not path.is_absolute() or path != Path(os.path.abspath(path)) or path.suffix != ".json":
        raise FeedbackError("Store must be a canonical absolute .json path.")
    skill = Path(__file__).resolve().parents[1]
    if skill == path or skill in path.parents or ".git" in path.parts:
        raise FeedbackError("Keep feedback state outside the skill package and Git metadata.")
    for part in [*reversed(path.parents), path]:
        if part.is_symlink():
            raise FeedbackError("Symlink store paths are not allowed.")
    if any((p / ".git").exists() for p in path.parents):
        raise FeedbackError("Keep feedback state outside application Git repositories.")


def read_json(path, private=False):
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise FeedbackError("Unable to open a regular JSON input.") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES or info.st_nlink != 1:
            raise FeedbackError("JSON input must be a bounded regular file without hard links.")
        if private and (info.st_uid != os.getuid() or info.st_mode & 0o077):
            raise FeedbackError("Feedback state must be private and owned by the current user.")
        with os.fdopen(fd, "rb") as stream:
            fd = -1
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise FeedbackError("JSON input exceeds the size limit.")
        return json.loads(raw, object_pairs_hook=pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FeedbackError("Invalid JSON input; contents were not displayed.") from exc
    finally:
        if fd >= 0:
            os.close(fd)


def empty():
    return {"schema_version": 1, "store_kind": KIND, "events": [], "decisions": []}


def load(path):
    safe_path(path)
    if not path.exists():
        return empty()
    parent_info = path.parent.stat()
    if parent_info.st_uid != os.getuid() or parent_info.st_mode & 0o077:
        raise FeedbackError("Use a private feedback directory owned by the current user.")
    data = read_json(path, private=True)
    if not isinstance(data, dict) or set(data) != {"schema_version", "store_kind", "events", "decisions"} or data["schema_version"] != 1 or data["store_kind"] != KIND:
        raise FeedbackError("Unrecognized feedback store; refusing to overwrite it.")
    ids = set()
    for key in ("events", "decisions"):
        rows = data[key]
        if not isinstance(rows, list) or len(rows) > MAX_RECORDS:
            raise FeedbackError("Invalid or oversized feedback store.")
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"record", "recorded_at", "sha256"}:
                raise FeedbackError("Invalid feedback envelope.")
            text(row["recorded_at"], "recorded_at", 80)
            record = event(row["record"]) if key == "events" else decision(row["record"], [r["record"] for r in data["events"]])
            if row["sha256"] != digest(record):
                raise FeedbackError("Feedback record digest mismatch.")
            if key == "events":
                if record["id"] in ids:
                    raise FeedbackError("Duplicate stored event identifier.")
                ids.add(record["id"])
    return data


@contextmanager
def write_lock(path):
    safe_path(path)
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    safe_path(path)
    info = path.parent.stat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise FeedbackError("Use a private feedback directory owned by the current user.")
    lock = path.with_name("." + path.name + ".lock")
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0), 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise FeedbackError("Invalid feedback lock file.")
        deadline = time.monotonic() + 3
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise FeedbackError("Feedback store is busy; retry after the other writer completes.")
                time.sleep(0.02)
        yield
    finally:
        os.close(fd)


def append(path, record, key):
    with write_lock(path):
        data = load(path)
        prior_digest = digest(data)
        if key == "events":
            event(record)
            existing = next((r for r in data[key] if r["record"]["id"] == record["id"]), None)
            if existing:
                if existing["record"] != record:
                    raise FeedbackError("Conflicting event identifier; retain the original and use a new evidence identifier.")
                return {"status": "duplicate", "record_id": existing["record"]["id"],
                        "record_sha256": existing["sha256"], "rules_changed": False}
            repeated = next((r for r in data[key] if material_digest(r["record"]) == material_digest(record)), None)
            if repeated:
                return {"status": "duplicate", "record_id": repeated["record"]["id"],
                        "record_sha256": repeated["sha256"], "rules_changed": False}
        else:
            decision(record, [r["record"] for r in data["events"]])
            if data[key] and data[key][-1]["record"] == record:
                return {"status": "duplicate", "record_sha256": digest(record), "rules_changed": False}
        if len(data[key]) >= MAX_RECORDS:
            raise FeedbackError("Feedback store record limit reached; archive reviewed state first.")
        data[key].append({"record": record, "recorded_at": datetime.now(timezone.utc).isoformat(), "sha256": digest(record)})
        encoded = json.dumps(data, ensure_ascii=False, indent=2).encode() + b"\n"
        if len(encoded) > MAX_BYTES:
            raise FeedbackError("Feedback store size limit reached.")
        fd, temp = tempfile.mkstemp(prefix=".feedback-", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            safe_path(path)
            if digest(load(path)) != prior_digest:
                raise FeedbackError("Feedback state changed outside the lock; no overwrite was performed.")
            os.replace(temp, path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
        return {"status": "recorded", "record_sha256": digest(record), "rules_changed": False,
                "decision_is_authenticated_approval": False}


def assess(data):
    groups = defaultdict(list)
    for envelope in data["events"]:
        groups[envelope["record"]["pattern_key"]].append(envelope)
    decisions = {r["record"]["pattern_key"]: r for r in data["decisions"]}
    results = []
    for pattern, envelopes in sorted(groups.items()):
        all_events = [e["record"] for e in envelopes]
        adverse = [e for e in all_events if e["category"] != "outcome" or e["outcome"] == "regressed"]
        observed = [e for e in adverse if any(r["kind"] == "observed" for r in e["evidence"])]
        by_occurrence = defaultdict(list)
        for e in adverse:
            by_occurrence[e["occurrence_id"]].append(e)
        conflicting_projects = any(len({e["project"] for e in events}) > 1 for events in by_occurrence.values())
        known = {e["root_cause"] for e in adverse} - {"unknown"}
        occurrences = {e["occurrence_id"] for e in adverse}
        observed_global_projects = {e["project"] for e in observed if e["scope"] == "global"}
        observed_global_occurrences = {e["occurrence_id"] for e in observed if e["scope"] == "global"}
        severe_observed = any(SEVERITIES[e["severity"]] >= 2 for e in observed)
        # A later observed event can corroborate the same occurrence's report. Lower-
        # severity observations do not silently verify a more serious reported claim.
        severe_reported = any(
            SEVERITIES[e["severity"]] >= 2 and e not in observed and
            not any(o["occurrence_id"] == e["occurrence_id"] and
                    SEVERITIES[o["severity"]] >= SEVERITIES[e["severity"]] for o in observed)
            for e in adverse)
        urgent = severe_observed or severe_reported
        reasons = []
        if not adverse:
            recommendation = "monitor"
            reasons.append("Outcome observations do not count as repeated failures or prove causality.")
        elif conflicting_projects:
            recommendation = "investigate"
            reasons.append("One occurrence has conflicting project aliases; reconcile ownership before counting independent support.")
        elif len(known) != 1:
            recommendation = "investigate"
            reasons.append("Root cause is unknown or conflicting; do not generalize a rule yet.")
        elif next(iter(known)) in PROJECT_CAUSES:
            recommendation = "project_fix"
            reasons.append("The supplied diagnosis points to a project, requirement or environment issue.")
        elif severe_reported:
            recommendation = "investigate"
            reasons.append("A serious report needs immediate verification; reported evidence is not an observed failure.")
        elif known == {"user-preference"}:
            recommendation = "skill_candidate" if any(e["scope"] == "global" for e in adverse) else "project_trial"
            reasons.append("An explicit preference can justify a scoped proposal, never automatic approval.")
        elif severe_observed or len(occurrences) >= 2:
            recommendation = "skill_candidate" if len(observed_global_projects) >= 2 and len(observed_global_occurrences) >= 2 else "project_trial"
            reasons.append("Distinct recurrence or an observed serious issue justifies a reviewable scoped experiment.")
        else:
            recommendation = "observe"
            reasons.append("One ordinary occurrence is insufficient to add a universal workflow rule.")
        decision_envelope = decisions.get(pattern)
        latest = decision_envelope["record"] if decision_envelope else None
        reviewed_materials = {material_digest(e) for e in all_events if latest and e["id"] in latest["reviewed_event_ids"]}
        new_ids = sorted(e["id"] for e in adverse if material_digest(e) not in reviewed_materials)
        after_decision = sorted(e["record"]["id"] for e in envelopes if latest and e["record"]["id"] in new_ids
                                and e.get("recorded_at", "") > decision_envelope.get("recorded_at", ""))
        preexisting = sorted(set(new_ids) - set(after_decision)) if latest else []
        suppressed = bool(latest and latest["disposition"] in {"deferred", "rejected"} and not new_ids)
        reopened = bool(latest and new_ids)
        if suppressed:
            reasons.append("No new adverse evidence since the recorded defer/reject decision; do not repeat the proposal.")
        if latest and latest["disposition"] == "applied":
            if new_ids:
                urgent = True
                reasons.append("Unreviewed adverse material exists alongside a recorded update. Check occurrence timing and effectiveness before considering rollback; recording order alone does not establish a regression or causality.")
            else:
                recommendation = "monitor"
                reasons.append("A recorded update needs subsequent observation, not another identical proposal.")
        results.append({"pattern_key": pattern, "recommendation": recommendation, "urgent": urgent,
                        "distinct_occurrences": len(occurrences), "distinct_projects": len({e["project"] for e in adverse}),
                        "observed_occurrences": len({e["occurrence_id"] for e in observed}), "reasons": reasons,
                        "event_ids": [e["id"] for e in all_events], "event_digests": {e["record"]["id"]: e["sha256"] for e in envelopes},
                        "skill_versions": sorted({e["skill_version"] for e in all_events}),
                        "suppressed": suppressed, "reopened": reopened, "new_adverse_event_ids": new_ids,
                        "recorded_after_decision_event_ids": after_decision, "preexisting_unreviewed_event_ids": preexisting,
                        "needs_proposal": not suppressed and recommendation in {"project_trial", "skill_candidate"},
                        "requires_user_confirmation_for_rule_update": True})
    return {"schema_version": 1, "store_digest": digest(data), "assessments": results,
            "rules_changed": False, "may_update_rules": False, "rule_update_authorized": False,
            "decision_is_authenticated_approval": False,
            "approval_scope": "Rule updates only; existing task authorization is unchanged.",
            "limitations": "Heuristics use supplied classifications and evidence labels, not semantic verification. Common secret checks are incomplete; redact before recording. Decision notes are history, not authenticated authorization."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", required=True, type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("record").add_argument("--event", required=True, type=Path)
    commands.add_parser("decision").add_argument("--decision", required=True, type=Path)
    commands.add_parser("assess")
    args = parser.parse_args()
    try:
        if args.command == "assess":
            result = assess(load(args.store))
        else:
            path = args.event if args.command == "record" else args.decision
            record = read_json(path)
            if args.command == "record":
                event(record)
            result = append(args.store, record, "events" if args.command == "record" else "decisions")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (FeedbackError, OSError) as exc:
        message = str(exc) if isinstance(exc, FeedbackError) else "Feedback filesystem operation failed; no input contents were displayed."
        print(json.dumps({"error": message, "rules_changed": False}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
