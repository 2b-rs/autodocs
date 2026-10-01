#!/usr/bin/env python3
"""Verify workflow-queue validation and its integration with ``validate.py``.

This script is the reusable counterpart of the project-root ``run.sh`` runner.
It compiles the changed modules, executes focused regression tests, validates
all real queue payloads, and finally runs the complete project validator.
"""
from __future__ import annotations

import argparse
import os
import py_compile
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "_src"
TMP_ROOT = Path("/tmp")
HEARTBEAT_SECONDS = 5

COMPILE_TARGETS = (
    SRC / "validate.py",
    SRC / "tools" / "curation_item.py",
    SRC / "tools" / "validate_workflow_validator.py",
    SRC / "tests" / "test_validate_workflow_lifecycle.py",
)
TEST_MODULES = (
    "_src.tests.test_curation_item_lifecycle",
    "_src.tests.test_curation_item_versioning",
    "_src.tests.test_validate_workflow_lifecycle",
    "_src.tests.test_curation_inventory",
)


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["TMPDIR"] = str(TMP_ROOT)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _run(command: list[str], *, heartbeat: str | None = None) -> None:
    process = subprocess.Popen(command, cwd=PROJECT_ROOT, env=_environment())
    if heartbeat is None:
        return_code = process.wait()
    else:
        while True:
            try:
                return_code = process.wait(timeout=HEARTBEAT_SECONDS)
                break
            except subprocess.TimeoutExpired:
                print(heartbeat, flush=True)
    if return_code:
        raise subprocess.CalledProcessError(return_code, command)


def compile_targets() -> None:
    print("[1/4] Compiling validator files into /tmp...", flush=True)
    for index, source in enumerate(COMPILE_TARGETS):
        destination = TMP_ROOT / f"autodocs-workflow-validator-{index}.pyc"
        py_compile.compile(str(source), cfile=str(destination), doraise=True)
    print(f"Compilation passed for {len(COMPILE_TARGETS)} files.", flush=True)


def run_focused_tests() -> None:
    print("[2/4] Running focused curation and workflow regression tests...", flush=True)
    _run([sys.executable, "-m", "unittest", "-v", *TEST_MODULES])


def validate_real_queues() -> None:
    print("[3/4] Validating real review and curation queues...", flush=True)
    src_text = str(SRC)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)

    import validate  # noqa: PLC0415

    validate.problems.clear()
    validate.structured_findings.clear()
    validate.checks_performed.clear()

    roots = dict(validate._workflow_queue_roots())
    counts = {
        name: len(list(Path(root).glob("**/*.json")))
        for name, root in roots.items()
    }
    missing_roots = [name for name, root in roots.items() if not Path(root).is_dir()]
    if missing_roots:
        raise RuntimeError(f"Missing workflow queue roots: {', '.join(missing_roots)}")
    empty_roots = [name for name, count in counts.items() if count == 0]
    if empty_roots:
        raise RuntimeError(f"Workflow queue roots unexpectedly empty: {', '.join(empty_roots)}")

    validate.check_workflow_lifecycle()
    print(f"Queue roots: {roots}", flush=True)
    print(f"Queue JSON counts: {counts}", flush=True)
    print(f"Workflow findings: {len(validate.structured_findings)}", flush=True)
    if validate.problems:
        details = "\n".join(validate.problems[:50])
        raise RuntimeError(f"Workflow validation errors:\n{details}")
    print("Real workflow queue validation passed.", flush=True)


def run_complete_validator() -> None:
    print("[4/4] Running complete project validator...", flush=True)
    _run(
        [sys.executable, str(SRC / "validate.py")],
        heartbeat="Full validator still running...",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-full-validator",
        action="store_true",
        help="run compilation, focused tests, and real queue validation only",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    compile_targets()
    run_focused_tests()
    validate_real_queues()
    if not args.skip_full_validator:
        run_complete_validator()
    print("Workflow validator verification passed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
