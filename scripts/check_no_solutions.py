#!/usr/bin/env python3
"""Block instructor solutions from reaching the student materials repo.

Two incidents, fa25 and fa26, had the same shape: nbgitpuller auto-commits
whatever sits in someone's pulled DataHub directory, and that directory gets
pushed to origin, replacing a released blank notebook with a solved one.

Checks, chosen so that they fire on both incidents and on nothing currently in
the repo:

  1. otter solution markers in any notebook under proj/ or disc/
  2. commits authored by nbgitpuller that carry local changes into proj/ or
     disc/ (nbgitpuller commits that only touch lec/ are instructor edits
     and are allowed)

Stdlib only. Exit 0 clean, 1 on a violation.
"""
import json
import pathlib
import re
import subprocess
import sys

MARKERS = ("BEGIN SOLUTION", "END SOLUTION", "SOLUTION NO PROMPT", "BEGIN PROMPT")
WATCHED = ("proj", "disc")


def notebooks():
    for top in WATCHED:
        for p in pathlib.Path(top).rglob("*.ipynb"):
            if ".ipynb_checkpoints" not in p.parts:
                yield p


def check_markers():
    bad = []
    for p in notebooks():
        try:
            nb = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:                      # noqa: BLE001
            print(f"  ! could not parse {p}: {e}")
            continue
        for i, cell in enumerate(nb.get("cells", [])):
            src = "".join(cell.get("source", []))
            hit = [m for m in MARKERS if m in src]
            if hit:
                bad.append((p, i, hit))
    return bad


def watched_changes(sha):
    """Student-material files this commit brought in from a local copy.

    An nbgitpuller merge has the local work as parent 1 and origin as parent 2,
    so what leaked is the merge result relative to origin.
    """
    parents = subprocess.run(
        ["git", "rev-list", "--parents", "-n", "1", sha],
        capture_output=True, text=True,
    ).stdout.split()[1:]
    base = parents[1] if len(parents) > 1 else (parents[0] if parents else None)
    cmd = ["git", "diff", "--name-only", base, sha] if base else \
          ["git", "show", "--name-only", "--format=", sha]
    out = subprocess.run(cmd + ["--", *WATCHED], capture_output=True, text=True).stdout
    return [f for f in out.splitlines() if f]


def check_authors(rev_range):
    if not rev_range:
        return []
    out = subprocess.run(
        ["git", "log", "--format=%H%x1f%an%x1f%ae%x1f%s", rev_range],
        capture_output=True, text=True,
    ).stdout
    bad = []
    for line in out.splitlines():
        parts = line.split("\x1f")
        if len(parts) != 4:
            continue
        sha, name, email, subj = parts
        if "nbgitpuller" in name.lower() or "nbgitpuller" in email.lower():
            files = watched_changes(sha)
            if files:
                bad.append((sha[:10], name, subj, files))
    return bad


def blank_count(path):
    """Cells still awaiting a student answer -- reported, never fatal."""
    try:
        nb = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001
        return None
    n = 0
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        if re.search(r"\.\.\.|YOUR CODE|YOUR ANSWER", src, re.I):
            n += 1
    return n


def main():
    rev_range = sys.argv[1] if len(sys.argv) > 1 else ""
    failed = False

    markers = check_markers()
    if markers:
        failed = True
        print("BLOCKED: otter solution markers found in student materials\n")
        for p, i, hit in markers:
            print(f"  {p}  cell {i}  -> {', '.join(hit)}")
        print("\n  This is the instructor master, not the student notebook.")

    authors = check_authors(rev_range)
    if authors:
        failed = True
        print("\nBLOCKED: nbgitpuller commits touching student materials\n")
        for sha, name, subj, files in authors:
            print(f"  {sha}  {name}  {subj}")
            for f in files:
                print(f"      {f}")
        print(
            "\n  nbgitpuller auto-commits your working copy when it pulls, so\n"
            "  these carry whatever was in your DataHub directory. Never push\n"
            "  from a directory you reached through an nbgitpuller link --\n"
            "  keep a separate clean clone for releases."
        )

    for p in sorted(pathlib.Path("proj").rglob("*.ipynb")) if pathlib.Path("proj").exists() else []:
        if ".ipynb_checkpoints" in p.parts:
            continue
        n = blank_count(p)
        if n == 0:
            print(f"\nWARNING: {p} has no cells awaiting an answer -- is it solved?")

    if failed:
        print("\nNothing was pushed. See scripts/README.md.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
