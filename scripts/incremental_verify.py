#!/usr/bin/env python3
"""Conservative, local-only incremental verification. Profiles are reviewed code.

Globs use repository-relative POSIX paths: * matches one segment, ** any depth.
Source discovery follows Git ignore rules (tracked files are always included).
Ignored file inputs require explicit check inputs/runtime_inputs or global_paths.
hermetic is a human-reviewed contract, not a sandbox or a discovery mechanism.
Caching additionally requires explicit runtime_inputs (including [] when audited).
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import math
import os
from pathlib import Path
import re
import selectors
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import time
import uuid

STAGES = {"quick": 0, "integration": 1, "release": 2}
LOG_LIMIT = 1024 * 1024
LOCKFILES = {"package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml",
             "poetry.lock", "uv.lock", "Pipfile.lock", "Cargo.lock", "Gemfile.lock",
             "composer.lock", "go.sum", "bun.lock", "bun.lockb", "requirements.txt"}
LIMITS = ["Profiles and commands are reviewed local code; this tool is not a sandbox or approval.",
          "Hermeticity is a manual contract. External services, time, randomness, flakes and side effects require cache:false.",
          "Cache records are trusted local state with integrity digests, not signed identity or provenance.",
          "Only explicitly selected checks are verified; no deployment or shipping decision is made."]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def no_symlinks(path):
    path = Path(os.path.abspath(path))
    for item in (path, *path.parents):
        if item.is_symlink():
            raise ValueError(f"Symbolic link path refused: {item}")
    return path


def read_file(path, maximum=None):
    """Read a regular file without following links, including directory links."""
    path = no_symlinks(path)
    fd = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        child = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(child, "rb") as source:
            mode = os.fstat(source.fileno()).st_mode
            if not stat.S_ISREG(mode):
                raise ValueError(f"Non-regular input refused: {path}")
            data = source.read() if maximum is None else source.read(maximum + 1)
            if maximum is not None and len(data) > maximum:
                raise ValueError("Evidence exceeds size limit")
            return data, stat.S_IMODE(mode)
    finally:
        os.close(fd)


def git(root, *args):
    executable_ = shutil.which("git", path=os.defpath)
    if not executable_:
        raise ValueError("Git not found on minimal PATH")
    result = subprocess.run([executable_, "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false",
                             "-c", "core.hooksPath=/dev/null", "-C", str(root), *args],
                            capture_output=True, env={"PATH": os.defpath, "LANG": "C", "TZ": "UTC"})
    if result.returncode:
        raise ValueError(f"Git operation failed: {' '.join(args[:2])}")
    return result.stdout


def strings(value, name, nonempty=False, unique=True):
    if not isinstance(value, list) or any(not isinstance(v, str) or not v or "\x00" in v for v in value):
        raise ValueError(f"{name} must be a list of nonempty strings")
    if nonempty and not value:
        raise ValueError(f"{name} must not be empty")
    if unique and len(set(value)) != len(value):
        raise ValueError(f"Duplicate item in {name}")
    return value


def patterns(value, name):
    for pattern in strings(value, name):
        if pattern.startswith("/") or "\\" in pattern or re.match(r"^[A-Za-z]:", pattern):
            raise ValueError(f"Absolute/non-POSIX path in {name}")
        if any(p in ("", ".", "..", ".git") for p in pattern.split("/")):
            raise ValueError(f"Unsafe path in {name}: {pattern}")
    return value


def fields(value, allowed, required, name):
    if not isinstance(value, dict) or set(value) - allowed or required - set(value):
        raise ValueError(f"Invalid fields in {name}")


def load_profile(path):
    raw, _ = read_file(path)
    profile = json.loads(raw, object_pairs_hook=no_duplicates)
    fields(profile, {"schema_version", "components", "checks", "global_paths", "always_checks"},
           {"schema_version", "components", "checks", "global_paths"}, "profile")
    if type(profile["schema_version"]) is not int or profile["schema_version"] != 1:
        raise ValueError("Unsupported schema_version")
    components = profile["components"]
    if not isinstance(components, dict):
        raise ValueError("components must be an object")
    for name, component in components.items():
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise ValueError("Invalid component id")
        fields(component, {"paths", "depends_on"}, {"paths", "depends_on"}, name)
        patterns(component["paths"], f"{name}.paths")
        strings(component["depends_on"], f"{name}.depends_on")
        if set(component["depends_on"]) - set(components):
            raise ValueError(f"Unknown dependency in {name}")
    def visit(name, visiting, done):
        if name in visiting:
            raise ValueError("Component dependency cycle")
        if name not in done:
            for dep in components[name]["depends_on"]:
                visit(dep, visiting | {name}, done)
            done.add(name)
    done = set()
    for name in components:
        visit(name, set(), done)
    if not isinstance(profile["checks"], list):
        raise ValueError("checks must be an array")
    check_ids = set()
    for check in profile["checks"]:
        fields(check, {"id", "components", "stage", "command", "inputs", "cache", "hermetic",
                       "env", "runtime_inputs", "timeout_seconds"},
               {"id", "components", "stage", "command", "inputs", "env"}, "check")
        name = check["id"]
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or name in check_ids:
            raise ValueError("Duplicate or invalid check id")
        check_ids.add(name)
        if not isinstance(check["stage"], str) or check["stage"] not in STAGES:
            raise ValueError(f"Invalid stage: {name}")
        strings(check["components"], f"{name}.components")
        if set(check["components"]) - set(components):
            raise ValueError(f"Unknown component: {name}")
        strings(check["command"], f"{name}.command", nonempty=True, unique=False)
        patterns(check["inputs"], f"{name}.inputs")
        if "runtime_inputs" in check:
            patterns(check["runtime_inputs"], f"{name}.runtime_inputs")
        for flag in ("cache", "hermetic"):
            if flag in check and type(check[flag]) is not bool:
                raise ValueError(f"{flag} must be boolean")
        for name in strings(check["env"], f"{name}.env"):
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) or name in {"TMPDIR", "TEMP", "TMP"}:
                raise ValueError("Invalid/reserved environment name")
        timeout = check.get("timeout_seconds", 120)
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout_seconds must be finite and positive")
    patterns(profile["global_paths"], "global_paths")
    if set(strings(profile.get("always_checks", []), "always_checks")) - check_ids:
        raise ValueError("Unknown always_checks reference")
    return profile, digest(raw)


def matches(path, patterns_):
    def match(parts, pattern):
        if not pattern:
            return not parts
        if pattern[0] == "**":
            return match(parts, pattern[1:]) or bool(parts and match(parts[1:], pattern))
        return bool(parts and fnmatch.fnmatchcase(parts[0], pattern[0]) and match(parts[1:], pattern[1:]))
    return any(match(path.split("/"), p.split("/")) for p in patterns_)


def may_contain_inputs(path, patterns_, descendants=False):
    def prefix(parts, pattern):
        if not parts:
            return bool(pattern) if descendants else True
        if not pattern:
            return False
        if pattern[0] == "**":
            return prefix(parts, pattern[1:]) or prefix(parts[1:], pattern)
        return fnmatch.fnmatchcase(parts[0], pattern[0]) and prefix(parts[1:], pattern[1:])
    return any(prefix(path.split("/"), p.split("/")) for p in patterns_)


def excluded(path, exclusions):
    return ".git" in path.parts or any(path == p or (is_dir and p in path.parents) for p, is_dir in exclusions)


def changes(root, base, exclusions):
    result = {}
    # Union committed, staged and unstaged changes, even if later edits cancel them.
    diff = ("diff", "--no-ext-diff", "--no-textconv", "--name-status", "-z", "--find-renames")
    for args in ((*diff, base, "HEAD", "--"), (*diff, "--cached", "--"), (*diff, "--")):
        tokens = git(root, *args).decode("utf-8", "surrogateescape").split("\0")
        index = 0
        while index < len(tokens) - 1:
            kind = tokens[index]
            count = 2 if kind.startswith(("R", "C")) else 1
            for path in tokens[index + 1:index + 1 + count]:
                if not excluded(root / path, exclusions):
                    result.setdefault(path, set()).add(kind)
            index += 1 + count
    for path in git(root, "ls-files", "--others", "--exclude-standard", "-z").decode("utf-8", "surrogateescape").split("\0"):
        if path and not excluded(root / path, exclusions):
            result.setdefault(path, set()).add("untracked")
    return [{"path": path, "kinds": sorted(kinds)} for path, kinds in sorted(result.items())]


def profile_baseline_guard(root, base, relative, current_hash):
    if relative is None:
        return "profile_not_baselined:outside_repository"
    try:
        baseline = git(root, "cat-file", "blob", f"{base}:{relative}")
    except ValueError:
        return "profile_not_baselined:missing_base_blob"
    if digest(baseline) != current_hash:
        return "profile_differs_from_base"
    return None


def select(profile, changed, stage, profile_relative, profile_guard=None):
    direct, escalation, own = set(), [profile_guard] if profile_guard else [], {}
    for entry in changed:
        path = entry["path"]
        mapped = {name for name, comp in profile["components"].items() if matches(path, comp["paths"])}
        direct |= mapped
        owners = {c["id"] for c in profile["checks"] if matches(path, c["inputs"] + c.get("runtime_inputs", []))}
        for name in owners:
            own.setdefault(name, []).append(f"check_input:{path}")
        if path == profile_relative:
            escalation.append(f"profile_changed:{path}")
        elif matches(path, profile["global_paths"]):
            escalation.append(f"global_path:{path}")
        elif Path(path).name in LOCKFILES:
            escalation.append(f"lockfile:{path}")
        elif not mapped and not owners:
            escalation.append(f"unmapped_path:{path}")
    affected = set(direct)
    while True:
        expanded = affected | {name for name, comp in profile["components"].items() if affected.intersection(comp["depends_on"])}
        if expanded == affected:
            break
        affected = expanded
    selected = {}
    for check in profile["checks"]:
        if STAGES[check["stage"]] > STAGES[stage]:
            continue
        reasons = list(own.get(check["id"], []))
        reasons += [f"affected_component:{name}" for name in sorted(affected.intersection(check["components"]))]
        if escalation:
            reasons.append("conservative_escalation")
        if check["id"] in profile.get("always_checks", []):
            reasons.append("always_check")
        if stage == "release":
            reasons.append("release_all_checks")
        if reasons:
            selected[check["id"]] = reasons
    return selected, sorted(affected), sorted(set(escalation))


def declared_files(root, pattern, exclusions):
    """Discover explicitly declared ignored inputs, pruning at the glob prefix."""
    parts = pattern.split("/")
    literal = []
    for part in parts:
        if any(char in part for char in "*?["):
            break
        literal.append(part)
    anchor = root
    for part in literal:
        anchor /= part
        if excluded(anchor, exclusions):
            return
        try:
            mode = anchor.lstat().st_mode
        except FileNotFoundError:
            return
        if stat.S_ISLNK(mode):
            yield anchor  # Fingerprinting rejects links rather than traversing them.
            return
    if len(literal) == len(parts):
        if not anchor.is_dir():
            yield anchor
        return
    if not anchor.is_dir():
        return
    pending = [anchor]
    while pending:
        directory = no_symlinks(pending.pop())
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                if excluded(path, exclusions):
                    continue
                relative = path.relative_to(root).as_posix()
                if entry.is_symlink():
                    if may_contain_inputs(relative, [pattern]):
                        yield path
                elif entry.is_dir(follow_symlinks=False):
                    if may_contain_inputs(relative, [pattern], descendants=True):
                        pending.append(path)
                elif matches(relative, [pattern]):
                    yield path


def repository_files(root, exclusions, explicit_inputs):
    # Git avoids walking ignored dependency/output trees. Tracked ignored files
    # still belong to the source set; deleted paths are represented by absence.
    names = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    candidates = {root / name for name in names.decode("utf-8", "surrogateescape").split("\0") if name}
    for pattern in explicit_inputs:
        candidates.update(declared_files(root, pattern, exclusions))
    for path in sorted(candidates):
        if not excluded(path, exclusions) and (path.exists() or path.is_symlink()):
            yield path


def environment(check, temporary):
    env = {"PATH": os.defpath, "LANG": "C.UTF-8", "TZ": "UTC", "TMPDIR": str(temporary),
           "PYTHONDONTWRITEBYTECODE": "1"}
    env.update({name: os.environ[name] for name in check["env"] if name in os.environ})
    return env


def executable(command, root, env):
    name = command[0]
    search = os.pathsep.join(str(Path(p) if os.path.isabs(p) else root / p) for p in env["PATH"].split(os.pathsep))
    found = str(root / name) if "/" in name and not os.path.isabs(name) else name
    if "/" not in found:
        found = shutil.which(found, path=search)
    if not found:
        raise ValueError("Executable not found on declared PATH")
    execution_path = os.path.abspath(found)
    path = Path(found).resolve(strict=True)
    if not os.access(path, os.X_OK):
        raise ValueError("Command is not executable")
    evidence = []
    for _ in range(4):
        data, mode = read_file(path)
        evidence.append({"path": str(path), "sha256": digest(data), "mode": mode})
        if not data.startswith(b"#!"):
            return execution_path, evidence
        words = shlex.split(data.split(b"\n", 1)[0][2:].decode())
        if not words:
            raise ValueError("Invalid command shebang")
        interpreter = words[0]
        if Path(interpreter).name == "env":
            env_path = Path(interpreter).resolve(strict=True)
            env_data, env_mode = read_file(env_path)
            evidence.append({"path": str(env_path), "sha256": digest(env_data), "mode": env_mode})
            words = words[1:]
            if words and words[0] == "-S":
                words = words[1:]
            if len(words) != 1 or words[0].startswith("-"):
                raise ValueError("Unsupported env shebang; use explicit interpreter argv")
            interpreter = shutil.which(words[0], path=search)
        if not interpreter or not os.path.isabs(interpreter):
            raise ValueError("Unresolvable command interpreter")
        path = Path(interpreter).resolve(strict=True)
    raise ValueError("Interpreter chain too deep")


def fingerprint(root, profile_path, profile, profile_hash, check, exclusions, temporary, broad=False):
    if digest(read_file(profile_path)[0]) != profile_hash:
        raise ValueError("Profile changed during verification")
    closure = set(check["components"])
    pending = list(closure)
    while pending:
        for dependency in profile["components"][pending.pop()]["depends_on"]:
            if dependency not in closure:
                closure.add(dependency)
                pending.append(dependency)
    explicit_inputs = check["inputs"] + check.get("runtime_inputs", []) + profile["global_paths"]
    globs = list(explicit_inputs)
    globs += [p for component in sorted(closure) for p in profile["components"][component]["paths"]]
    if broad:
        globs = ["**"]
    files = {}
    for path in repository_files(root, exclusions, explicit_inputs):
        relative = path.relative_to(root).as_posix()
        # A symlink directory can hide descendants; treat matching descendants as relevant.
        relevant = matches(relative, globs) or (path.is_symlink() and may_contain_inputs(relative, globs))
        if relevant:
            data, mode = read_file(path)
            files[relative] = {"sha256": digest(data), "mode": mode}
    env = environment(check, temporary)
    binary, binaries = executable(check["command"], root, env)
    identity = {"root": str(root), "check_id": check["id"], "files": files, "profile": profile, "profile_sha256": profile_hash,
                "command": check["command"], "execution_path": binary, "executable": binaries,
                "env": {name: digest(packed(os.environ.get(name))) for name in check["env"]},
                "runtime": {"system": sys.platform, "uname": list(os.uname()), "python": sys.version,
                            "python_executable": str(Path(sys.executable).resolve()),
                            "python_sha256": digest(read_file(Path(sys.executable).resolve())[0]),
                            "runner_sha256": digest(read_file(Path(__file__).resolve())[0])}}
    return digest(packed(identity)), binary


def write_json(path, value):
    no_symlinks(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    no_symlinks(path)
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    try:
        with temporary.open("xb") as output:
            output.write(packed(value) + b"\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def cached(cache, key, check_id):
    record_path = cache / "records" / (key + ".json")
    try:
        record = json.loads(read_file(record_path, 65536)[0], object_pairs_hook=no_duplicates)
        payload = record["payload"]
        if digest(packed(payload)) != record["sha256"]:
            raise ValueError("record digest mismatch")
        if payload["fingerprint"] != key or payload["check_id"] != check_id or payload["exit_code"] != 0 or payload["status"] != "passed":
            raise ValueError("record identity mismatch")
        original = payload["original_run"]
        if not all(isinstance(original[k], str) and original[k] for k in ("id", "revision", "time")):
            raise ValueError("invalid original run")
        log = Path(payload["log"])
        if log.is_absolute() or ".." in log.parts or len(log.parts) != 2 or log.parts[0] != "logs":
            raise ValueError("invalid log reference")
        data, _ = read_file(cache / log, LOG_LIMIT)
        if len(data) > LOG_LIMIT or digest(data) != payload["log_sha256"]:
            raise ValueError("log digest mismatch")
        return payload, "hit"
    except FileNotFoundError:
        return None, "miss"
    except (ValueError, KeyError, TypeError, OSError):
        return None, "invalid"


def run_command(root, check, binary, temporary, log):
    temporary.mkdir(parents=True, exist_ok=False)
    no_symlinks(temporary)
    log.parent.mkdir(parents=True, exist_ok=True)
    no_symlinks(log)
    started = time.monotonic()
    reason, exit_code = None, None
    size = 0
    with log.open("xb") as output:
        process = subprocess.Popen([binary, *check["command"][1:]], cwd=root,
                                   env=environment(check, temporary), stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        try:
            while selector.get_map() or process.poll() is None:
                if time.monotonic() - started > check.get("timeout_seconds", 120):
                    reason = "timeout"
                    break
                for key, _ in selector.select(0.05):
                    block = os.read(key.fileobj.fileno(), 65536)
                    if not block:
                        selector.unregister(key.fileobj)
                        continue
                    output.write(block[:max(0, LOG_LIMIT - size)])
                    size += len(block)
                    if size > LOG_LIMIT:
                        reason = "output_limit"
                        break
                if reason:
                    break
            if reason:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            exit_code = process.wait(timeout=5)
        finally:
            selector.close()
            process.stdout.close()
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
    return exit_code, reason, time.monotonic() - started


def execute(args):
    overall_started = time.monotonic()
    root = no_symlinks(Path(args.root).absolute()).resolve(strict=True)
    if Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() != root:
        raise ValueError("--root must equal the Git repository root")
    base = git(root, "rev-parse", "--verify", "--end-of-options", args.base + "^{commit}").decode().strip()
    head = git(root, "rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    profile_path = no_symlinks(Path(args.profile).absolute())
    profile, profile_hash = load_profile(profile_path)
    default_cache = Path(git(root, "rev-parse", "--git-path", "incremental-verify").decode().strip())
    cache = no_symlinks(Path(args.cache_dir).absolute() if args.cache_dir else (default_cache if default_cache.is_absolute() else root / default_cache))
    report_path = no_symlinks(Path(args.report).absolute()) if args.report else None
    git_dir = Path(git(root, "rev-parse", "--absolute-git-dir").decode().strip()).resolve()
    common_dir = Path(git(root, "rev-parse", "--git-common-dir").decode().strip())
    common_dir = (common_dir if common_dir.is_absolute() else root / common_dir).resolve()
    namespace = git_dir / "incremental-verify"
    if cache == root or cache in root.parents or cache == profile_path or cache in profile_path.parents:
        raise ValueError("Cache directory overlaps repository/profile root")
    if report_path and (report_path == profile_path or report_path == root or cache == report_path or cache in report_path.parents):
        raise ValueError("Report overlaps profile, root or cache")
    for control_dir in {git_dir, common_dir}:
        if cache == control_dir or cache in control_dir.parents:
            raise ValueError("Cache overlaps Git control files")
        if control_dir in cache.parents and not (cache == namespace or namespace in cache.parents):
            raise ValueError("Git-internal cache must use this worktree's incremental-verify namespace")
        if report_path and (control_dir == report_path or control_dir in report_path.parents or ".git" in report_path.parts):
            raise ValueError("Report overlaps Git control files")
    tracked = git(root, "ls-files", "-z").decode("utf-8", "surrogateescape").split("\0")
    if any(p and (root / p == report_path or root / p == cache or cache in (root / p).parents) for p in tracked):
        raise ValueError("Cache/report may not hide or overwrite tracked inputs")
    input_globs = profile["global_paths"] + [p for comp in profile["components"].values() for p in comp["paths"]]
    input_globs += [p for c in profile["checks"] for p in c["inputs"] + c.get("runtime_inputs", [])]
    if root in cache.parents and git_dir not in cache.parents:
        if may_contain_inputs(cache.relative_to(root).as_posix(), input_globs):
            raise ValueError("Cache overlaps declared inputs")
    if report_path and root in report_path.parents and matches(report_path.relative_to(root).as_posix(), input_globs):
        raise ValueError("Report overlaps declared inputs")
    owner = {"schema_version": 1, "root": str(root)}
    marker = cache / ".incremental-verify-owner.json"
    if cache.exists() and any(cache.iterdir()):
        try:
            valid_owner = json.loads(read_file(marker, 4096)[0]) == owner
        except (ValueError, OSError):
            valid_owner = False
        if not valid_owner:
            raise ValueError("Nonempty cache directory is not owned by this adapter/repository")
    if report_path and report_path.exists():
        try:
            previous_report = json.loads(read_file(report_path, 8 * LOG_LIMIT)[0])
            valid_report = previous_report.get("root") == str(root) and re.fullmatch(r"[0-9a-f]{32}", previous_report.get("run_id", ""))
        except (ValueError, OSError, AttributeError, TypeError):
            valid_report = False
        if not valid_report:
            raise ValueError("Existing report path is not a report from this adapter/repository")
    exclusions = [(cache, True)] + ([(report_path, False)] if report_path else [])
    try:
        profile_relative = profile_path.relative_to(root).as_posix()
    except ValueError:
        profile_relative = None
    profile_guard = profile_baseline_guard(root, base, profile_relative, profile_hash)
    changed = changes(root, base, exclusions)
    selected, affected, escalation = select(profile, changed, args.stage, profile_relative, profile_guard)
    if args.execute and selected:
        write_json(marker, owner)
    run_id = uuid.uuid4().hex
    report = {"schema_version": 1, "run_id": run_id, "time": dt.datetime.now(dt.timezone.utc).isoformat(),
              "root": str(root), "stage": args.stage, "base": base, "head": head,
              "changes": changed, "affected_components": affected, "escalation": escalation,
              "checks": [], "remaining_gates": [c["id"] for c in profile["checks"] if STAGES[c["stage"]] > STAGES[args.stage]],
              "limits": LIMITS, "scope": "selected_checks_only",
              "status": "plan_only" if selected else "no_checks"}
    verified = []
    for check in sorted(profile["checks"], key=lambda c: STAGES[c["stage"]]):
        name = check["id"]
        entry = {"id": name, "stage": check["stage"], "selected": name in selected,
                 "reasons": selected.get(name, []), "status": "planned" if name in selected else "not_run"}
        report["checks"].append(entry)
        if not args.execute or name not in selected:
            continue
        temporary = cache / "tmp" / (run_id + "-" + name)
        log = cache / "logs" / (run_id + "-" + name + ".log")
        key = None
        try:
            key, binary = fingerprint(root, profile_path, profile, profile_hash, check, exclusions, temporary, bool(escalation))
            entry["fingerprint"] = key
            can_cache = (check.get("cache", False) and check.get("hermetic", False)
                         and "runtime_inputs" in check and args.stage != "release" and not args.fresh and not escalation)
            entry["cache"] = "disabled" if not can_cache else "miss"
            entry["cache_eligible"] = can_cache
            if can_cache:
                previous, entry["cache"] = cached(cache, key, name)
                if previous:
                    entry.update(status="reused", original_run=previous["original_run"],
                                 duration_seconds=0, log=str(cache / previous["log"]),
                                 log_sha256=previous["log_sha256"], exit_code=0)
                    verified.append((check, entry, key, temporary))
                    continue
            # Any new attempt replaces the old success, including forced fresh runs.
            record_path = no_symlinks(cache / "records" / (key + ".json"))
            record_path.unlink(missing_ok=True)
            exit_code, reason, duration = run_command(root, check, binary, temporary, log)
            entry.update(exit_code=exit_code, duration_seconds=duration, log=str(log),
                         log_sha256=digest(read_file(log)[0]),
                         original_run={"id": run_id, "revision": head, "time": report["time"]})
            after, _ = fingerprint(root, profile_path, profile, profile_hash, check, exclusions, temporary, bool(escalation))
            if after != key:
                reason = "inputs_changed_during_run"
            entry["status"] = "passed" if exit_code == 0 and reason is None else "failed"
            if entry["status"] == "failed":
                entry["failure_reason"] = reason or "nonzero_exit"
            else:
                verified.append((check, entry, key, temporary))
                if can_cache:
                    payload = {"check_id": name, "fingerprint": key, "status": "passed", "exit_code": 0,
                               "original_run": entry["original_run"], "log": str(log.relative_to(cache)),
                               "log_sha256": entry["log_sha256"]}
                    write_json(cache / "records" / (key + ".json"), {"payload": payload, "sha256": digest(packed(payload))})
        except (ValueError, OSError, subprocess.SubprocessError) as exc:
            entry.update(status="failed", failure_reason=f"verification_error:{type(exc).__name__}", error=str(exc))
        finally:
            # Temporary files never become declared durable inputs or cache evidence.
            if temporary.exists() and not temporary.is_symlink():
                shutil.rmtree(temporary)
    if args.execute and selected:
        for check, entry, key, temporary in verified:
            try:
                current, _ = fingerprint(root, profile_path, profile, profile_hash, check, exclusions, temporary, bool(escalation))
                if current != key:
                    raise ValueError("inputs changed")
            except (ValueError, OSError):
                entry.update(status="failed", failure_reason="inputs_changed_after_verification")
                record = cache / "records" / (key + ".json")
                if not record.is_symlink():
                    record.unlink(missing_ok=True)
        final_selected, _, final_escalation = select(profile, changes(root, base, exclusions), args.stage, profile_relative, profile_guard)
        if set(final_escalation) - set(escalation):
            for _, entry, key, _ in verified:
                entry.update(status="failed", failure_reason="conservative_inputs_changed_after_verification")
                record = cache / "records" / (key + ".json")
                if not record.is_symlink():
                    record.unlink(missing_ok=True)
            report["escalation"].append("conservative_inputs_changed_during_run")
        missing = set(final_selected) - set(selected)
        if missing:
            report["remaining_gates"] += sorted(missing)
            report["escalation"].append("selection_changed_during_run")
        report["status"] = "failed" if missing or any(e["status"] == "failed" for e in report["checks"]) else "passed"
    report["remaining_gates"] += [e["id"] for e in report["checks"] if e["selected"] and e["status"] not in {"passed", "reused"}]
    report["remaining_gates"] = sorted(set(report["remaining_gates"]))
    report["elapsed_seconds"] = time.monotonic() - overall_started
    if report_path:
        write_json(report_path, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--stage", choices=STAGES, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--cache-dir")
    parser.add_argument("--report")
    parser.add_argument("--fresh", action="store_true")
    args = parser.parse_args()
    try:
        report = execute(args)
    except (ValueError, OSError, subprocess.SubprocessError, RecursionError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=True))
        return 2
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))
    return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    sys.exit(main())
