#!/usr/bin/env python3
"""Task Bookkeeping and Closure Automation Helper.

This tool automates the two-commit task closure workflow for project backlogs.
It safely transitions task status in `TODO.md` from in-progress (`[p]`) to
completed (`[x]`), attaches the substantive commit SHA reference (`REF: <hash>`),
appends a timestamped closure entry to the task's Definition of Done block, and
updates the corresponding task claim file (`TODO-<agent>-<task>-<request>.md`)
with complete closure evidence.

Typical Usage Workflow:
    1. Land the substantive code/documentation commit and capture its commit SHA:
       $ SUBSTANTIVE=$(git rev-parse HEAD)

    2. Execute this script to update `TODO.md` and the active claim file:
       $ python3 _src/tools/task_bookkeeping_closure.py \\
           --task-id 0037-04.01 \\
           --claim TODO-perplexity-0037-04.01-qdZL46kZ6UpFGNpFn6qZmA.md \\
           --substantive "$SUBSTANTIVE" \\
           --request-id "req-12345-closure" \\
           --closure-text "Completed schemas, fixtures, and contract documentation." \\
           --point "JSON syntax and Draft-7 schema validation passed." \\
           --point "Isolated invalid fixtures verified for all rules."

    3. Stage and commit only the bookkeeping artifacts:
       $ git add TODO.md TODO-perplexity-0037-04.01-qdZL46kZ6UpFGNpFn6qZmA.md
       $ git commit -m "chore(todo): close 0037-04.01"
"""

import argparse
import os
import re
from pathlib import Path


def update_todo(
    todo_path: Path,
    task_id: str,
    substantive_commit: str,
    request_id: str,
    closure_details: str,
) -> None:
    """Update task status from [p] to [x] and record closure details in TODO.md.

    Args:
        todo_path: File path to the authoritative TODO.md backlog.
        task_id: Unique task identifier (e.g., '0037-04.01').
        substantive_commit: Full or short SHA-1 hash of the substantive commit.
        request_id: Unique runner request or validation identifier.
        closure_details: Narrative description of work delivered for the task.

    Raises:
        ValueError: If the in-progress task header or Definition of Done section
            cannot be located in the specified TODO.md file.
    """
    text = todo_path.read_text()

    # Update task marker and append reference commit
    header_pattern = rf"(- \[p\] \*\*{re.escape(task_id)}\*\*[^\n]+)"
    match = re.search(header_pattern, text)
    if not match:
        raise ValueError(
            f"Active task header for {task_id} marked [p] not found in {todo_path}"
        )

    old_header = match.group(1)
    new_header = old_header.replace("- [p] ", "- [x] ")
    if "Claim:" in new_header:
        # Strip trailing Claim note if present, replace with REF
        new_header = re.sub(r"\s*Claim:\s*`[^`]+`\.?", "", new_header)
    new_header = f"{new_header.rstrip('.')} REF: {substantive_commit}"
    text = text.replace(old_header, new_header, 1)

    # Locate Definition of Done block for this task to append Closure note
    dod_pattern = (
        rf"(\*\*{re.escape(task_id)}\*\*[\s\S]*?-\s+\*\*Definition of Done:\*\*[^\n]+)"
    )
    dod_match = re.search(dod_pattern, text)
    if not dod_match:
        raise ValueError(
            f"Definition of Done section for {task_id} not found in {todo_path}"
        )

    dod_block = dod_match.group(1)
    closure_entry = (
        f"\n  - **Closure ({os.popen('date +%Y-%m-%d').read().strip()}):** "
        f"{closure_details} Validation passed in request `{request_id}`. "
        f"REF: `{substantive_commit}`."
    )
    text = text.replace(dod_block, dod_block + closure_entry, 1)
    todo_path.write_text(text)


def update_claim(
    claim_path: Path,
    substantive_commit: str,
    request_id: str,
    summary_points: list[str],
) -> None:
    """Transition claim state to [x] and replace pending steps with closure logs.

    Args:
        claim_path: Path to the active markdown claim file.
        substantive_commit: Commit SHA associated with the substantive change.
        request_id: Identifier of the runner execution that validated the task.
        summary_points: Bullet-point statements summarizing verification and scope.
    """
    text = claim_path.read_text()
    if "- `state`: [p]" in text:
        text = text.replace("- `state`: [p]", "- `state`: [x]", 1)

    points_formatted = "\n".join(f"- {p}" for p in summary_points)
    closure_section = (
        f"\n## Closure\n\n"
        f"- Substantive commit: `{substantive_commit}`.\n"
        f"- Request ID: `{request_id}`.\n"
        f"{points_formatted}\n"
    )

    if "## Next step" in text:
        text = re.sub(r"## Next step[\s\S]*$", closure_section.lstrip(), text)
    else:
        text += closure_section

    claim_path.write_text(text)


def main() -> None:
    """Parse command-line arguments and execute backlog/claim closure."""
    parser = argparse.ArgumentParser(
        description="Safely record task completion in TODO.md and active claim files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python3 _src/tools/task_bookkeeping_closure.py \\
    --task-id "0037-04.01" \\
    --claim "TODO-perplexity-0037-04.01-qdZL46kZ6UpFGNpFn6qZmA.md" \\
    --substantive "9aae0b7a295800478bc8eb0d0df795283b28c2a5" \\
    --request-id "qdZL46kZ6UpFGNpFn6qZmA-bookkeeping03" \\
    --closure-text "Completed schemas, relation constraints, and invalid fixture suite." \\
    --point "Draft-7 JSON schemas and coverage checks passed." \\
    --point "Unrelated workspace files preserved."
""",
    )
    parser.add_argument(
        "--todo",
        type=Path,
        default=Path("TODO.md"),
        help="Path to the authoritative backlog file (default: TODO.md).",
    )
    parser.add_argument(
        "--claim",
        type=Path,
        required=True,
        help="Path to the specific task coordination claim file to close.",
    )
    parser.add_argument(
        "--task-id",
        required=True,
        help="Exact task identifier to transition, e.g. '0037-04.01'.",
    )
    parser.add_argument(
        "--substantive",
        required=True,
        help="Git commit SHA containing the substantive code/doc deliverables.",
    )
    parser.add_argument(
        "--request-id",
        required=True,
        help="Unique identifier of the runner request that validated the task.",
    )
    parser.add_argument(
        "--closure-text",
        required=True,
        help="Narrative summary for the Definition of Done closure note.",
    )
    parser.add_argument(
        "--point",
        action="append",
        default=[],
        help="Bullet point to record in the claim's ## Closure section (repeatable).",
    )

    args = parser.parse_args()
    update_todo(
        args.todo,
        args.task_id,
        args.substantive,
        args.request_id,
        args.closure_text,
    )
    update_claim(args.claim, args.substantive, args.request_id, args.point)
    print(f"Successfully closed task {args.task_id} in {args.todo} and {args.claim}")


if __name__ == "__main__":
    main()
