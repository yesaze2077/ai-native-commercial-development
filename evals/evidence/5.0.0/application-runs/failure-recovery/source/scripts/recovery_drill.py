#!/usr/bin/env python3
"""Bounded localhost recovery drill using the supplied, unchanged application."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import selectors
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, Request, build_opener


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
OPENER = build_opener(ProxyHandler({}))


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(report, action, **values):
    event = {"at": utc_now(), "action": action, **values}
    report["events"].append(event)
    return event


@contextmanager
def instance(report, name, data_path, fail_health=False):
    command = [sys.executable, "-B", str(APP), "--data", str(data_path), "--port", "0"]
    if fail_health:
        command.append("--fail-health")
    child = subprocess.Popen(
        command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            if not selector.select(timeout=5):
                raise RuntimeError(f"{name}: startup URL timed out")
            url = child.stdout.readline().strip()
        parsed = urlsplit(url)
        if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1"
                or not parsed.port or parsed.path or parsed.query or parsed.fragment
                or parsed.username or parsed.password):
            raise RuntimeError(f"{name}: unexpected startup URL {url!r}")
        record(report, "instance_started", instance=name, pid=child.pid,
               url=url, command=command, data_path=str(data_path))
        yield {"name": name, "url": url, "pid": child.pid}
    finally:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=3)
        output = child.stdout.read()
        child.stdout.close()
        record(report, "instance_stopped", instance=name, pid=child.pid,
               returncode=child.returncode, trailing_output=output)


def http(report, active, path, expected_status, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(active["url"] + path, data=data,
                      headers={"Content-Type": "application/json"} if data else {})
    try:
        response = OPENER.open(request, timeout=3)
    except HTTPError as error:
        response = error
    with response:
        status = response.code
        body = json.loads(response.read().decode("utf-8"))
    record(report, "http", instance=active["name"], pid=active["pid"],
           url=request.full_url, method=request.get_method(), input=payload,
           status=status, body=body, expected_status=expected_status)
    if status != expected_status:
        raise AssertionError(f"{active['name']} {path}: {status} != {expected_status}")
    return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/recovery.json")
    args = parser.parse_args()
    report = {
        "status": "running", "started_at": utc_now(), "scope": "synthetic_localhost",
        "git_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "git_status_before_run": subprocess.check_output(
            ["git", "status", "--short"], cwd=ROOT, text=True).splitlines(),
        "environment": {"python": sys.version, "executable": sys.executable,
                        "platform": platform.platform(), "cwd": str(ROOT)},
        "source_sha256": {"app.py": digest(APP), "index.html": digest(ROOT / "index.html"),
                          "scripts/recovery_drill.py": digest(Path(__file__))},
        "events": [],
        "limits": ["Fault is injected health failure, not process crash or disk loss.",
                   "Recovery reuses a SQLite file; no backup restore was exercised.",
                   "No production, deployment, human approval or independent review.",
                   "No browser/UI, capacity, security or commercial outcome validation."],
    }
    started = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="synthetic-recovery-") as temporary:
            data_path = Path(temporary) / "requests.sqlite3"
            with instance(report, "baseline", data_path) as active:
                if http(report, active, "/health", 200) != {"status": "ok"}:
                    raise AssertionError("baseline health body differs")
                created = http(report, active, "/api/tickets", 201,
                               {"title": "Synthetic recovery request"})
                if (not isinstance(created.get("id"), int)
                        or created.get("title") != "Synthetic recovery request"
                        or created.get("status") != "open"):
                    raise AssertionError("created record differs")
                if created not in http(report, active, "/api/tickets?status=all", 200):
                    raise AssertionError("baseline record was not persisted")
                report["created_record"] = created
            with instance(report, "fault", data_path, fail_health=True) as active:
                if http(report, active, "/health", 503) != {"status": "unhealthy"}:
                    raise AssertionError("fault health body differs")
            recovery_started = time.monotonic()
            with instance(report, "recovered", data_path) as active:
                if http(report, active, "/health", 200) != {"status": "ok"}:
                    raise AssertionError("recovery health body differs")
                report["local_recovery_to_health_seconds"] = round(
                    time.monotonic() - recovery_started, 6)
                records = http(report, active, "/api/tickets?status=all", 200)
                if created not in records:
                    raise AssertionError("original record absent or changed after recovery")
                report["recovered_records"] = records
                record(report, "persistence_verified", record=created,
                       source="actual HTTP GET after third process startup")
            if not data_path.exists():
                raise AssertionError("shared data file missing before cleanup")
        report["temporary_database_cleaned"] = not data_path.exists()
        report["status"] = "passed"
    except BaseException as error:
        report["status"] = "failed"
        report["error"] = {"type": type(error).__name__, "message": str(error)}
        raise
    finally:
        report["finished_at"] = utc_now()
        report["duration_seconds"] = round(time.monotonic() - started, 6)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "evidence": str(args.output),
                          "duration_seconds": report["duration_seconds"]}))


if __name__ == "__main__":
    main()
