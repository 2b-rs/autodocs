#!/usr/bin/env python3
"""Fail-closed scope validation for the 0019 handoff-scope correction."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
BASE = "b4af9f88834f2872801aa60158158b59317ac500"
CANDIDATE = "0b884cd7c96ae7edfd19be4d5a0d83cd9d6d1d07"
SCOPE_MANIFEST = OUT / "candidate-scope.tsv"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def expected_scope(path: Path = SCOPE_MANIFEST) -> list[str]:
    lines = path.read_text().splitlines()
    if len(lines) < 2 or not lines[0].startswith("# Exact declared candidate delta") or lines[1] != "git_name_status":
        fail("candidate-scope manifest is malformed")
    return lines[2:]


def validate_scope(observed: Iterable[str], expected: Iterable[str]) -> None:
    observed_list = list(observed)
    expected_list = list(expected)
    if observed_list != expected_list:
        unexpected = [entry for entry in observed_list if entry not in expected_list]
        missing = [entry for entry in expected_list if entry not in observed_list]
        detail = unexpected[0] if unexpected else ("missing " + missing[0] if missing else "ordering differs")
        fail(f"candidate scope differs from its exact manifest: {detail}")


def verify_sums() -> None:
    for line in (OUT / "SHA256SUMS.txt").read_text().splitlines():
        digest, relative = line.split(maxsplit=1)
        target = ROOT / relative.lstrip("*")
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            fail(f"package digest mismatch: {relative}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope-file", type=Path, help="test-only name-status fixture; default is the pinned Git delta")
    args = parser.parse_args()
    git("cat-file", "-e", CANDIDATE + "^{commit}")
    git("merge-base", "--is-ancestor", BASE, CANDIDATE)
    observed = args.scope_file.read_text().splitlines() if args.scope_file else git("diff", "--name-status", "-M", BASE + ".." + CANDIDATE).splitlines()
    validate_scope(observed, expected_scope())
    verify_sums()
    print("PASS: exact 0019 candidate scope, including the merged 0019-11 corrective claim, matches the digest-bound manifest.")


if __name__ == "__main__":
    main()
