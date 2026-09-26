#!/usr/bin/env python3
"""Alert on nbgitpuller commits that are new to main's history.

The push-triggered guard (check_no_solutions.py) inspects only the range of a
single push. This scans the whole branch, so it also catches commits that
arrive by a route a push range would miss -- a force-push, a rewritten branch,
or anything that landed while CI was skipped.

Seven nbgitpuller commits are already in history; they are listed in
.github/nbgitpuller-baseline.txt and ignored. Anything else exits 1.
"""
import pathlib
import subprocess
import sys

BASELINE = pathlib.Path(".github/nbgitpuller-baseline.txt")
BRANCH = sys.argv[1] if len(sys.argv) > 1 else "origin/main"


def baseline():
    if not BASELINE.exists():
        return set()
    out = set()
    for line in BASELINE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.add(line.split()[0])
    return out


def main():
    known = baseline()
    log = subprocess.run(
        ["git", "log", BRANCH, "--author=nbgitpuller", "--format=%H%x1f%ad%x1f%an%x1f%s",
         "--date=short"],
        capture_output=True, text=True,
    )
    if log.returncode != 0:
        print(f"could not read {BRANCH}:\n{log.stderr}")
        return 2

    found, new = 0, []
    for line in log.stdout.splitlines():
        parts = line.split("\x1f")
        if len(parts) != 4:
            continue
        found += 1
        if parts[0] not in known:
            new.append(parts)

    print(f"branch            : {BRANCH}")
    print(f"baselined commits : {len(known)}")
    print(f"nbgitpuller found : {found}")

    if not new:
        print("\nOK -- no new nbgitpuller commits.")
        return 0

    print(f"\nALERT: {len(new)} new nbgitpuller commit(s) on {BRANCH}\n")
    for sha, date, name, subj in new:
        print(f"  {sha[:10]}  {date}  {name}  {subj}")
    print(
        "\nSomeone pushed from a directory reached through an nbgitpuller link.\n"
        "Check the student notebooks under proj/ and disc/ for leaked solutions,\n"
        "then see scripts/README.md."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
