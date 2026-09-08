#!/usr/bin/env python3
"""Manifest-compatible issue HTML generation entry point.

This wrapper intentionally owns no rendering logic.  It delegates the declared
``--issues`` operation to the corresponding ``issuectl render --html`` stage.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_issuectl():
    path = Path(__file__).resolve().with_name("issuectl.py")
    spec = importlib.util.spec_from_file_location("issuectl_generate_entrypoint", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


issuectl = _load_issuectl()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issues", action="store_true", help="render the declared issue HTML outputs")
    parser.add_argument("--repo", default=os.environ.get("ISSUECTL_REPO", str(ROOT)))
    parser.add_argument("--output-root")
    parser.add_argument("--dag")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", dest="write", action="store_const", const=True)
    mode.add_argument("--check", "--dry-run", dest="write", action="store_const", const=False)
    parser.set_defaults(write=None)
    parser.add_argument("--format", choices=("json", "human"), default="json")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not args.issues:
        parser.error("--issues is required")

    delegated = ["render", "--html", "--repo", args.repo, "--format", args.format]
    if args.output_root:
        delegated.extend(("--output-root", args.output_root))
    if args.dag:
        delegated.extend(("--dag", args.dag))
    if args.write is True:
        delegated.append("--write")
    elif args.write is False:
        delegated.append("--check")
    return issuectl.main(delegated)


if __name__ == "__main__":
    raise SystemExit(main())
