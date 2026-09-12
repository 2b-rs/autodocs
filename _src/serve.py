#!/usr/bin/env python3
"""Canonical local preview server for the HTML tree and issue store.

Usage:
    _src/serve.sh
    python3 _src/serve.py
    python3 _src/serve.py --port 8100
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent / "tools" / "issue_preview.py"
SPEC = importlib.util.spec_from_file_location("issue_preview", TOOLS)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="_src/serve.sh",
        description="Canonical local preview server for the HTML tree and issue store.",
    )
    parser.add_argument("--repo", default=str(MODULE.ROOT), help="repository root")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8100)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    MODULE.serve(Path(args.repo).resolve(), args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
