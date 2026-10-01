#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test.py — Unified test runner for autodocs.

Unifies integration, documentation, architecture, tools, and review-request test suites.
Implements task 0033-14 test execution.

Usage:
    ./test.py [--layer {all,review-request,integration,tools}] [-v] [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "_src"
TESTS_DIR = SRC_DIR / "tests"
TOOLS_DIR = SRC_DIR / "tools"

# Ensure root and src are on sys.path
for p in (str(ROOT_DIR), str(SRC_DIR), str(TOOLS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Ensure NODE_PATH has node_modules for browser tests
candidate_node_paths = [
    str(ROOT_DIR / "output" / "npm-prefix" / "node_modules"),
    "/tmp/autodocs/output/npm-prefix/node_modules",
    "/Users/tobias.anton/devel/autodocs/output/npm-prefix/node_modules",
    "/Users/tobias.anton/devel/autodocs/node_modules",
    str(ROOT_DIR / "node_modules"),
]
valid_node_paths = [p for p in candidate_node_paths if os.path.isdir(p)]
if valid_node_paths:
    os.environ["NODE_PATH"] = os.pathsep.join(valid_node_paths) + os.pathsep + os.environ.get("NODE_PATH", "")


def get_test_modules(layer: str = "all") -> list[str]:
    """Return matching test files / modules based on layer."""
    modules = []
    
    if layer in ("all", "review-request"):
        modules.extend([
            "_src/tests/test_review_request_package.py",
            "_src/tests/test_review_request_package_v2_contract.py",
            "_src/tests/test_review_request_ingest.py",
            "_src/tests/test_review_request_retention.py",
            "_src/tests/test_review_request_abuse_control.py",
            "_src/tests/test_review_request_browser.py",
            "_src/tests/test_review_request_browser_builder.py",
            "_src/tests/test_review_request_rendering.py",
            "_src/tests/test_review_request_ux_contract.py",
        ])
        
    if layer in ("all", "tools"):
        for f in sorted(TOOLS_DIR.glob("test_*.py")):
            rel = f.relative_to(ROOT_DIR)
            if str(rel) not in modules:
                modules.append(str(rel))

    if layer in ("all", "integration"):
        for f in sorted(TESTS_DIR.glob("test_*.py")):
            rel = f.relative_to(ROOT_DIR)
            if str(rel) not in modules:
                modules.append(str(rel))
                
    return modules


def run_tests(layer: str = "all", verbose: int = 1) -> unittest.TestResult:
    """Load and run tests for the selected layer."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    modules = get_test_modules(layer)
    for mod_path in modules:
        full_path = ROOT_DIR / mod_path
        if not full_path.exists():
            continue
        module_name = mod_path.replace("/", ".").replace(".py", "")
        try:
            mod_suite = loader.loadTestsFromName(module_name)
            suite.addTest(mod_suite)
        except Exception as e:
            print(f"Warning: failed to load test module {module_name}: {e}", file=sys.stderr)
            
    runner = unittest.TextTestRunner(verbosity=verbose)
    start_time = time.time()
    result = runner.run(suite)
    duration = time.time() - start_time
    
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified test runner for autodocs")
    parser.add_argument(
        "--layer",
        choices=["all", "review-request", "integration", "tools"],
        default="review-request",
        help="Test layer to execute (default: review-request)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=1,
        help="Increase verbosity level",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON summary",
    )
    
    args = parser.parse_args()
    
    result = run_tests(layer=args.layer, verbose=args.verbose)
    
    if args.json:
        summary = {
            "layer": args.layer,
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "was_successful": result.wasSuccessful(),
        }
        print(json.dumps(summary, indent=2))
        
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
