#!/usr/bin/env python3
"""Derive the deterministic 20-Task measurement population for 0039-01.

Population rule (from the Task contract): exactly the first 20 Task-level items
(`XXXX-YY`; Features `XXXX` and Subtasks `XXXX-YY.ZZ` excluded) whose authoritative
implementation disposition FIRST becomes `[x]` or `[w]` after the recorded
authority-activation reference for the 0040-05 TK-2 rule. Order by the authoritative
terminal-transition event sequence; stable Task ID as deterministic tie-breaker.

Activation: DEC-0040-007, 2026-08-20T08:02:27Z (Management ratification; CON-01).

Read-only: walks main's history of TODO.md and DONE.md via git; mutates nothing.
"""
import re, subprocess, json, sys, os
from datetime import datetime, timezone

GITDIR = os.environ.get("TK2_GITDIR", "/Users/tobias.anton/devel/autodocs/.git")
# Overridable so the tool can be exercised against a hermetic fixture repository
# instead of the live one (the fixture rule this repository learned the hard way).
ACTIVATION = (datetime.fromisoformat(os.environ["TK2_ACTIVATION"])
              if os.environ.get("TK2_ACTIVATION")
              else datetime(2026, 8, 20, 8, 2, 27, tzinfo=timezone.utc))
FILES = ["TODO.md", "DONE.md"]
# Task-level marker line: "- [x] **0038-14**" ; excludes Feature (**0038**) and Subtask (**0038-14.01**)
MARKER = re.compile(r'^- \[([ pxwdu])\] \*\*(\d{4}-\d{2})\*\*(?!\.)', re.M)

def git(*args):
    return subprocess.run(["/usr/bin/git", "--git-dir", GITDIR, *args],
                          capture_output=True, text=True, errors="replace").stdout

def commits():
    """main's commits touching the bookkeeping files, oldest->newest, after activation."""
    out = git("log", "--reverse", "--format=%H|%cI", "main", "--", *FILES)
    res = []
    for line in out.strip().splitlines():
        if "|" not in line:
            continue
        sha, iso = line.split("|", 1)
        # `git log --format=%cI` emits `Z` when the committer TZ is UTC; Python's
        # fromisoformat rejects it before 3.11. The live repository commits with a
        # numeric offset, so this path stayed green until a UTC fixture exercised it
        # (the environment-qualifier defect class, found by the hermetic suite).
        ts = datetime.fromisoformat(iso.strip().replace("Z", "+00:00"))
        res.append((sha.strip(), ts.astimezone(timezone.utc)))
    return res

def markers_at(sha):
    """Task-level markers at a commit, merged over both files (DONE wins if terminal)."""
    state = {}
    for f in FILES:
        blob = git("show", f"{sha}:{f}")
        for m, tid in MARKER.findall(blob):
            # a terminal state anywhere is terminal; otherwise first seen
            if tid not in state or m in "xw":
                state[tid] = m
    return state

def main():
    hist = commits()
    if not hist:
        print("no history", file=sys.stderr); return 2
    # baseline = last commit at or before activation
    baseline_sha = None
    for sha, ts in hist:
        if ts <= ACTIVATION:
            baseline_sha = sha
        else:
            break
    prev = markers_at(baseline_sha) if baseline_sha else {}
    terminal_before = {t for t, m in prev.items() if m in "xw"}
    print(f"baseline commit at/before activation: {baseline_sha}  "
          f"({len(prev)} task-level items, {len(terminal_before)} already terminal)")

    population, seen = [], set(terminal_before)
    for sha, ts in hist:
        if ts <= ACTIVATION:
            continue
        cur = markers_at(sha)
        newly = sorted(t for t, m in cur.items() if m in "xw" and t not in seen)
        for tid in newly:  # stable Task ID tie-breaker within one event
            seen.add(tid)
            population.append({"rank": len(population) + 1, "task": tid,
                               "marker": cur[tid], "event_commit": sha,
                               "event_time": ts.isoformat().replace("+00:00", "Z")})
            if len(population) == 20:
                break
        if len(population) == 20:
            break

    print(f"\npopulation size: {len(population)} (target 20)\n")
    for r in population:
        print(f"{r['rank']:2d}. {r['task']}  [{r['marker']}]  {r['event_time']}  {r['event_commit'][:9]}")
    if len(population) < 20:
        print("\nRESULT: fewer than 20 qualifying Tasks -> conclusion `not-yet-mature`")
    json.dump({"activation": {"decision": "DEC-0040-007",
                              "recorded_at": ACTIVATION.isoformat().replace("+00:00", "Z"),
                              "authority_reference": "docs/dossiers/0040-management-closure-provenance.md#dec-0040-007"},
               "baseline_commit": baseline_sha,
               "population": population},
              open("/tmp/seven-0039-01-population.json", "w"), indent=2)
    print("\nwrote /tmp/seven-0039-01-population.json")
    return 0

if __name__ == "__main__":
    sys.exit(main())
