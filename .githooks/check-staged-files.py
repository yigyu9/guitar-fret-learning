#!/usr/bin/env python3
"""Inspect staged blobs, including LFS pointers; never change the index/files."""
import os
from pathlib import PurePosixPath
import subprocess
import sys

from storage_policy import is_external_link_target

MIB = 1024 * 1024
ALLOWED = {"data", "docs", "guitar_learning", "isaacgym", "paper", "tab2fingermapping", ".githooks"}

def git(*args, **kwargs):
    return subprocess.check_output(["git", *args], **kwargs)

def main():
    root = git("rev-parse", "--show-toplevel").decode().strip()
    os.chdir(root)
    changed = set(git("diff", "--cached", "--name-only", "--diff-filter=ACMRT", "-z").split(b"\0")) - {b""}
    if not changed:
        return 0
    entries = []
    ignored = subprocess.run(["git", "check-ignore", "--no-index", "-z", "--stdin"],
        input=b"\0".join(sorted(changed))+b"\0", capture_output=True)
    if ignored.returncode not in (0, 1):
        raise RuntimeError(ignored.stderr.decode(errors="replace"))
    errors = ["Ignored local-only path: "+os.fsdecode(p)
              for p in ignored.stdout.split(b"\0") if p]
    for entry in git("ls-files", "--stage", "-z").split(b"\0"):
        if not entry:
            continue
        meta, path = entry.split(b"\t", 1)
        if path not in changed:
            continue
        mode, oid, stage = meta.split()
        if stage != b"0":
            continue
        name = os.fsdecode(path)
        parts = PurePosixPath(name).parts
        if len(parts) > 1 and parts[0] not in ALLOWED:
            errors.append(f"Outside GitHub scope: {name}")
        if any("archive" in part.lower() for part in parts[:-1]):
            errors.append(f"Archive directory: {name}")
        if mode == b"120000":
            target = os.fsdecode(git("cat-file", "blob", oid.decode()))
            if is_external_link_target(root, name, target):
                errors.append(f"External-storage link: {name}; keep locally and refresh local exclusions")
        if mode == b"160000":
            errors.append(f"Embedded repository: {name}; add its files or configure a submodule explicitly")
        else:
            entries.append((name, oid))
    if entries:
        sizes = git("cat-file", "--batch-check=%(objectsize)", input=b"".join(oid+b"\n" for _, oid in entries)).splitlines()
        for (name, oid), raw_size in zip(entries, sizes):
            size = int(raw_size)
            lower = name.lower()
            generated_text = lower.endswith((".log", ".out", ".jsonl", ".jsonl.gz", ".json.gz")) or (lower.startswith("docs/") and lower.endswith((".json", ".csv", ".txt")))
            if generated_text and size > 10 * MIB:
                errors.append(f"Generated log/report exceeds 10 MiB: {name} ({size/MIB:.1f} MiB); keep locally and commit a summary/manifest")
            elif size > 50 * MIB:
                errors.append(f"Regular Git blob exceeds 50 MiB: {name} ({size/MIB:.1f} MiB); use LFS for required inputs or ignore generated output")
    if errors:
        print("Commit blocked by repository file policy:", file=sys.stderr)
        print("\n".join("- "+error for error in errors), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
