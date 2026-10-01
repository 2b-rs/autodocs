#!/usr/bin/env python3
"""Retired compatibility surface for legacy free-form Task closure edits.

Authoritative backlog/claim changes require a digest-bound operation, reviewed
candidate, and separate promotion through `_src/tools/legacy_task_editor.py`.
The former helper accepted free-form arguments and independently rewrote shared
files, so it now fails closed without reading or writing repository state.
"""
import argparse
from pathlib import Path
from typing import List, Optional


RETIREMENT_MESSAGE = (
    "task_bookkeeping_closure.py is retired; create a "
    "legacy-task-editor-operation@v1 manifest and run "
    "_src/tools/legacy_task_editor.py plan before any promotion"
)


class RetiredBookkeepingHelper(RuntimeError):
    pass


def update_todo(
    todo_path: Path,
    task_id: str,
    substantive_commit: str,
    request_id: str,
    closure_details: str,
) -> None:
    del todo_path, task_id, substantive_commit, request_id, closure_details
    raise RetiredBookkeepingHelper(RETIREMENT_MESSAGE)


def update_claim(
    claim_path: Path,
    substantive_commit: str,
    request_id: str,
    summary_points: List[str],
) -> None:
    del claim_path, substantive_commit, request_id, summary_points
    raise RetiredBookkeepingHelper(RETIREMENT_MESSAGE)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--todo")
    parser.add_argument("--claim")
    parser.add_argument("--task-id")
    parser.add_argument("--substantive")
    parser.add_argument("--request-id")
    parser.add_argument("--closure-text")
    parser.add_argument("--point", action="append")
    parser.parse_args(argv)
    print(RETIREMENT_MESSAGE)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
