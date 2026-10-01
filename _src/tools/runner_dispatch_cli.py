#!/usr/bin/env python3
"""runner_dispatch_cli.py — CLI queue consumer and runner for runner_dispatch.py.

Usage:
    python3 _src/tools/runner_dispatch_cli.py [--root DIR] [--once] [--worker-id ID] [--capability CLASS]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict

import runner_dispatch as rd


def get_current_base_commit(repo_root: Path) -> str:
    try:
        res = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return res.stdout.strip()
    except Exception:
        return ""


def get_current_refs(repo_root: Path) -> Dict[str, str]:
    refs = {}
    try:
        res = subprocess.run(
            ["git", "-C", str(repo_root), "show-ref"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for line in res.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) == 2:
                commit, ref_name = parts
                refs[ref_name] = commit
    except Exception:
        pass
    return refs


def main() -> int:
    parser = argparse.ArgumentParser(description="Consume and execute requests from .runner/requests/")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root path")
    parser.add_argument("--once", action="store_true", help="Process ready requests once and exit")
    parser.add_argument("--worker-id", type=str, default="host-worker-1", help="Worker identifier")
    parser.add_argument("--capability", type=str, default="sandboxed-grunt", help="Capability class")
    parser.add_argument("--epoch", type=str, default="legacy-writable", help="Current authority epoch")
    args = parser.parse_args()

    repo_root = args.root.resolve()
    runner_root_path = repo_root / ".runner"
    runner_root = rd.RunnerRoot(runner_root_path)
    runner_root.ensure_layout()
    registry = rd.ActionRegistry()
    dispatcher = rd.Dispatcher(runner_root, registry, repo_root=repo_root)

    print(f"=== Runner Dispatch Consumer started (root={repo_root}, epoch={args.epoch}) ===")
    processed_any = False
    all_succeeded = True

    while True:
        # Reclaim any stale leases
        reclaimed = runner_root.reclaim_stale_leases()
        if reclaimed:
            print(f"Reclaimed {len(reclaimed)} stale leases: {reclaimed}")

        ready = runner_root.list_ready_requests()
        # Filter out requests that already have a terminal result
        unresolved = [req_id for req_id in ready if runner_root.read_result(req_id) is None]

        if unresolved:
            for req_id in unresolved:
                base_commit = get_current_base_commit(repo_root)
                refs = get_current_refs(repo_root)
                ctx = rd.PreflightContext(
                    base_commit=base_commit,
                    authority_epoch=args.epoch,
                    capability_class=args.capability,
                    ref_state=refs,
                )
                print(f"Processing request: {req_id} (base={base_commit[:9] if base_commit else 'unknown'})...")
                result = dispatcher.claim_and_execute(req_id, args.worker_id, ctx)
                status = result.get("status")
                findings = result.get("findings", [])
                print(f"Request {req_id} finished with status: {status} (findings={findings})")
                processed_any = True
                if status != "succeeded":
                    all_succeeded = False
        else:
            if args.once:
                if not processed_any:
                    print("No pending unresolved requests in .runner/requests/.")
                break
            time.sleep(1)

        if args.once:
            break

    print("=== Runner Dispatch Consumer completed ===")
    return 0 if all_succeeded else 1


if __name__ == "__main__":
    sys.exit(main())
