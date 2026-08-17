#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit link-verification evidence without mutating sources, claims, or Git.

This helper deliberately does not clean scratch paths, repair page models,
generate tracked output, stage files, or create commits.  It reports those
states and returns nonzero when a required validation stage fails.
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


ROOT = Path(__file__).resolve().parents[2]
_EPHEMERAL_DIRS = (
    "_review_request_bisect_tmp",
    "_review_request_four_url_probe",
)


def find_ephemeral_paths(root: Path = ROOT) -> List[str]:
    """Return scratch paths that an operator may review; never delete them."""
    found = []
    for relative in _EPHEMERAL_DIRS:
        if (root / relative).exists():
            found.append(relative)
    for candidate in sorted(root.glob(".perplexity-cpu-loop-recovery*")):
        found.append(candidate.relative_to(root).as_posix())
    return sorted(set(found))


def page_model_paths(root: Path = ROOT) -> List[Path]:
    """Return all current source page-model JSON files."""
    return sorted((root / "_src" / "sources" / "pages").glob("*.json"))


def validate_page_models(paths: Optional[Iterable[Path]] = None) -> List[Dict[str, object]]:
    """Read and validate page-model JSON, returning findings without repair."""
    findings = []
    for path in paths if paths is not None else page_model_paths():
        try:
            with path.open("r", encoding="utf-8") as handle:
                value = json.load(handle)
            if not isinstance(value, dict):
                raise ValueError("top-level JSON value must be an object")
        except (OSError, UnicodeError, ValueError) as exc:
            findings.append(
                {
                    "path": str(path),
                    "category": "invalid-page-model",
                    "message": str(exc),
                }
            )
    return findings


def _bounded_lines(value: str, limit: int = 20) -> str:
    lines = value.splitlines()
    return "\n".join(lines[-limit:])


def run_required(argv: Sequence[str], label: str, root: Path = ROOT) -> int:
    """Run one required read-only/checking command and report its exact result."""
    try:
        result = subprocess.run(
            list(argv),
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except OSError as exc:
        print("ERROR %s: %s" % (label, exc))
        return 1
    if result.returncode != 0:
        print("ERROR %s: exit %d" % (label, result.returncode))
        detail = _bounded_lines(result.stderr or result.stdout)
        if detail:
            print(detail)
        return result.returncode or 1
    print("OK %s" % label)
    return 0


def git_status(root: Path = ROOT) -> Dict[str, Any]:
    """Return read-only Git status with an explicit command outcome."""
    try:
        result = subprocess.run(
            ["git", "--no-optional-locks", "status", "--short"],
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except OSError as exc:
        return {"exit_code": 1, "error": str(exc), "paths": []}
    return {
        "exit_code": result.returncode,
        "error": _bounded_lines(result.stderr) if result.returncode else "",
        "paths": result.stdout.splitlines(),
    }


def main() -> int:
    scratch = find_ephemeral_paths()
    if scratch:
        print("Scratch paths retained for owner review: %s" % ", ".join(scratch))
    else:
        print("No known scratch paths found.")

    model_findings = validate_page_models()
    if model_findings:
        for finding in model_findings:
            print("ERROR page model %s: %s" % (finding["path"], finding["message"]))
        return 1
    print("OK page-model JSON (%d files)" % len(page_model_paths()))

    stages = (
        ([sys.executable, "_src/generate.py", "--check"], "generation check"),
        ([sys.executable, "_src/validate.py"], "project validation"),
    )
    for argv, label in stages:
        returncode = run_required(argv, label)
        if returncode != 0:
            return returncode

    status = git_status()
    if status["exit_code"] != 0:
        print("ERROR git status: %s" % status["error"])
        return int(status["exit_code"])
    print("Git status paths observed (read-only): %d" % len(status["paths"]))
    print("OK link-verification evidence audit completed without source or Git mutation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
