#!/usr/bin/env python3
"""Copy the bundled commercial-governance template into a repository."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="Repository root.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without writing.")
    return parser.parse_args()


def validate_destination(target_root: Path, destination: Path) -> None:
    """Reject destinations that escape the target or traverse symbolic links."""
    try:
        relative = destination.relative_to(target_root)
    except ValueError as exc:
        raise ValueError(f"Destination escapes target root: {destination}") from exc

    current = target_root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"Destination contains a symbolic link: {current}")

    resolved_parent = destination.parent.resolve(strict=False)
    try:
        resolved_parent.relative_to(target_root)
    except ValueError as exc:
        raise ValueError(f"Destination parent escapes target root: {destination}") from exc


def copy_file_safely(src: Path, dst: Path, overwrite: bool) -> None:
    """Copy one file while refusing to follow a final-component symlink."""
    flags = os.O_WRONLY | os.O_CREAT
    flags |= os.O_TRUNC if overwrite else os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    mode = stat.S_IMODE(src.stat().st_mode)
    descriptor = os.open(dst, flags, mode)
    try:
        with src.open("rb") as source, os.fdopen(descriptor, "wb") as destination:
            descriptor = -1
            shutil.copyfileobj(source, destination)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    shutil.copystat(src, dst, follow_symlinks=False)


def main() -> int:
    args = parse_args()
    skill_root = Path(__file__).resolve().parents[1]
    template_root = skill_root / "assets" / "project-template"
    target_root = Path(args.target).expanduser().resolve()

    if not template_root.is_dir():
        print(f"Template directory missing: {template_root}", file=sys.stderr)
        return 2

    conflicts: list[Path] = []
    actions: list[tuple[Path, Path]] = []

    for src in sorted(template_root.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(template_root)
        dst = target_root / rel
        try:
            validate_destination(target_root, dst)
        except ValueError as exc:
            print(f"Unsafe destination: {exc}", file=sys.stderr)
            return 2
        if dst.exists() and not args.force:
            conflicts.append(dst)
        else:
            actions.append((src, dst))

    if conflicts:
        print("Refusing to overwrite existing files:", file=sys.stderr)
        for path in conflicts:
            print(f"  - {path}", file=sys.stderr)
        print("Re-run with --force only after reviewing the files.", file=sys.stderr)
        return 1

    if not args.dry_run:
        target_root.mkdir(parents=True, exist_ok=True)

    for src, dst in actions:
        print(f"{'WOULD COPY' if args.dry_run else 'COPY'} {src.relative_to(template_root)}")
        if not args.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                validate_destination(target_root, dst)
                copy_file_safely(src, dst, overwrite=args.force)
            except (FileExistsError, OSError, ValueError) as exc:
                print(f"Refusing unsafe write to {dst}: {exc}", file=sys.stderr)
                return 2

    print(f"{len(actions)} file(s) {'planned' if args.dry_run else 'copied'}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
