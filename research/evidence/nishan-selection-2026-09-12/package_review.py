"""Create non-Git review artifacts from this plan's preserved tar snapshot."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import tarfile
from pathlib import Path


def included(name: str, prefixes: list[str]) -> bool:
    parts = Path(name).parts
    return (
        any(name.startswith(prefix.rstrip("/") + "/") for prefix in prefixes)
        and "archive" not in parts
        and "__pycache__" not in parts
        and not any(part.endswith(".egg-info") for part in parts)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prefix", action="append", required=True)
    args = parser.parse_args()
    old: dict[str, bytes] = {}
    with tarfile.open(args.before, "r:gz") as archive:
        for member in archive.getmembers():
            if member.isfile() and included(member.name, args.prefix):
                handle = archive.extractfile(member)
                assert handle is not None
                old[member.name] = handle.read()
    current = {
        path.as_posix(): path.read_bytes()
        for prefix in args.prefix
        for path in Path(prefix).rglob("*")
        if path.is_file() and included(path.as_posix(), args.prefix)
    }
    changes = [name for name in sorted(old.keys() | current.keys()) if old.get(name) != current.get(name)]
    lines = [f"# Review package: {args.before} -> working files\n", "No Git repository; complete net snapshot diff, 10 lines of context.\n", "## Changed files\n"]
    for name in changes:
        before = old.get(name, b"")
        after = current.get(name, b"")
        lines.append(f"{name}: {len(before)} -> {len(after)} bytes; SHA256 {hashlib.sha256(before).hexdigest()} -> {hashlib.sha256(after).hexdigest()}\n")
    lines.append("\n## Diff\n")
    for name in changes:
        before = old.get(name, b"")
        after = current.get(name, b"")
        try:
            left, right = before.decode("utf-8"), after.decode("utf-8")
            if "\0" in left or "\0" in right:
                raise UnicodeError("binary")
        except UnicodeError:
            lines.append(f"\nBinary artifact changed: {name} (hashes above).\n")
            continue
        lines.extend(difflib.unified_diff(left.splitlines(keepends=True), right.splitlines(keepends=True), fromfile="before/" + name, tofile="current/" + name, n=10))
    args.output.write_text("".join(lines))
    print(f"Wrote {args.output}: {len(changes)} changed files, {args.output.stat().st_size} bytes")


if __name__ == "__main__":
    main()
