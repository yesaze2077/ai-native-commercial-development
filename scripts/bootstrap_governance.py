#!/usr/bin/env python3
"""Copy the bundled commercial-governance template into a repository."""

from __future__ import annotations

import argparse
import os
import secrets
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


def secure_dir_fd_supported() -> bool:
    required = (os.open, os.mkdir, os.unlink, os.link, os.rename)
    return (
        os.name == "posix"
        and hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
        and all(function in os.supports_dir_fd for function in required)
    )


def open_directory_chain(root_fd: int, parts: tuple[str, ...]) -> int:
    """Open or create a relative directory chain without following symlinks."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    current_fd = os.dup(root_fd)
    try:
        for part in parts:
            if part in ("", ".", ".."):
                raise ValueError(f"Unsafe destination component: {part!r}")
            try:
                next_fd = os.open(part, flags, dir_fd=current_fd)
            except FileNotFoundError:
                try:
                    os.mkdir(part, mode=0o755, dir_fd=current_fd)
                except FileExistsError:
                    pass
                next_fd = os.open(part, flags, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except Exception:
        os.close(current_fd)
        raise


def write_all(descriptor: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise OSError("Unable to make progress writing temporary file.")
        view = view[written:]


def copy_file_atomically(src: Path, parent_fd: int, destination_name: str, overwrite: bool) -> None:
    """Publish a complete new inode through a verified destination directory."""
    source_stat = os.stat(src, follow_symlinks=False)
    mode = stat.S_IMODE(source_stat.st_mode)
    temp_name: str | None = None
    temp_fd = -1

    try:
        for _ in range(128):
            candidate = f".bootstrap-governance-{secrets.token_hex(12)}"
            try:
                temp_fd = os.open(
                    candidate,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    mode,
                    dir_fd=parent_fd,
                )
                temp_name = candidate
                break
            except FileExistsError:
                continue
        if temp_name is None:
            raise FileExistsError("Unable to allocate a unique temporary file.")

        with src.open("rb") as source:
            while chunk := source.read(1024 * 1024):
                write_all(temp_fd, chunk)
        os.fchmod(temp_fd, mode)
        os.utime(temp_fd, ns=(source_stat.st_atime_ns, source_stat.st_mtime_ns))
        os.fsync(temp_fd)

        if overwrite:
            os.rename(
                temp_name,
                destination_name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
        else:
            os.link(
                temp_name,
                destination_name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
                follow_symlinks=False,
            )
            os.unlink(temp_name, dir_fd=parent_fd)
        temp_name = None
        os.fsync(parent_fd)
    finally:
        if temp_fd >= 0:
            os.close(temp_fd)
        if temp_name is not None:
            try:
                os.unlink(temp_name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass


def copy_relative_safely(root_fd: int, src: Path, relative: Path, overwrite: bool) -> None:
    if relative.is_absolute() or ".." in relative.parts or relative.name in ("", ".", ".."):
        raise ValueError(f"Unsafe relative destination: {relative}")
    if src.is_symlink():
        raise ValueError(f"Template source is a symbolic link: {src}")

    parent_parts = () if relative.parent == Path(".") else relative.parent.parts
    parent_fd = open_directory_chain(root_fd, parent_parts)
    try:
        copy_file_atomically(src, parent_fd, relative.name, overwrite)
    finally:
        os.close(parent_fd)


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

    root_fd = -1
    if not args.dry_run:
        if not secure_dir_fd_supported():
            print(
                "Secure bootstrap writes require POSIX directory-descriptor and no-follow support.",
                file=sys.stderr,
            )
            return 2
        try:
            target_root.mkdir(parents=True, exist_ok=True)
            root_fd = os.open(
                target_root,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            )
        except OSError as exc:
            print(f"Unable to open target root safely: {exc}", file=sys.stderr)
            return 2

    try:
        for src, dst in actions:
            relative = src.relative_to(template_root)
            print(f"{'WOULD COPY' if args.dry_run else 'COPY'} {relative}")
            if not args.dry_run:
                try:
                    copy_relative_safely(root_fd, src, relative, overwrite=args.force)
                except (FileExistsError, OSError, ValueError) as exc:
                    print(f"Refusing unsafe write to {dst}: {exc}", file=sys.stderr)
                    return 2
    finally:
        if root_fd >= 0:
            os.close(root_fd)

    print(f"{len(actions)} file(s) {'planned' if args.dry_run else 'copied'}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
