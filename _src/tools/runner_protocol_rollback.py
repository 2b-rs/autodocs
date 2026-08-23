#!/usr/bin/env python3
"""Automatic singleton+epoch rollback for 0037-46.02 (pre-switch proof).

The helper snapshots the legacy selector/service pair, injects a controlled
post-switch failure, and restores the exact prior bytes.  The three named
failure stores model the distinct points at which activation must fail closed:
health after switching, post-switch verification, and exclusive-mutation
validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

SINGLETON_PROTOCOL = "runner-request@v1"
PRIOR_EPOCH = "legacy-writable"
SELECTOR_NAME = "agent-workflow.json"
SERVICE_NAME = "issues/_policy/runner-service.json"
INJECTED_PROTOCOL = "runner-queue@v1"
INJECTED_EPOCH = "issue-store-writable"

HEALTH_AFTER_SWITCH = "health_after_switch"
POST_SWITCH_VERIFICATION = "post_switch_verification"
EXCLUSIVE_MUTATION = "exclusive_mutation"
FAILURE_STORES = (
    HEALTH_AFTER_SWITCH,
    POST_SWITCH_VERIFICATION,
    EXCLUSIVE_MUTATION,
)


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def atomic_write(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".rollback-tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def git_rev_parse(repo: Path) -> str:
    head = repo / ".git"
    if head.is_file():
        text = head.read_text(encoding="utf-8").strip()
        gitdir = Path(text.split(":", 1)[1].strip()) if text.startswith("gitdir:") else head
    else:
        gitdir = head
    return (gitdir / "HEAD").read_text(encoding="utf-8").strip()


def snapshot_file(repo: Path, rel: str) -> dict[str, Any]:
    path = repo / rel
    data = read_bytes(path)
    return {"path": rel, "digest": sha256_bytes(data), "bytes": len(data), "payload": data}


def selector_fields(data: bytes) -> dict[str, str]:
    obj = json.loads(data.decode("utf-8"))
    return {
        "runner_protocol": str(obj.get("runner_protocol", "")),
        "authority_epoch": str(obj.get("authority_epoch", "")),
        "write_phase": str(obj.get("write_phase", "")),
    }


def capture(repo: Path) -> dict[str, Any]:
    selector = snapshot_file(repo, SELECTOR_NAME)
    service = snapshot_file(repo, SERVICE_NAME)
    return {
        "head_ref": git_rev_parse(repo),
        "selector": {key: selector[key] for key in ("path", "digest", "bytes")},
        "service": {key: service[key] for key in ("path", "digest", "bytes")},
        "fields": selector_fields(selector["payload"]),
        "_selector_payload": selector["payload"],
        "_service_payload": service["payload"],
    }


def restore(repo: Path, snap: dict[str, Any]) -> None:
    """Restore both protected files exactly, atomically per file."""
    atomic_write(repo / SELECTOR_NAME, snap["_selector_payload"])
    atomic_write(repo / SERVICE_NAME, snap["_service_payload"])


def inject_failed_activation(repo: Path, failure_store: str | None = None) -> dict[str, str]:
    """Inject a queue selector state representing a controlled failed switch.

    ``failure_store`` selects a required fail-closed gate.  The selector carries
    the store only while injected; ``restore`` returns it byte-for-byte to its
    legacy singleton state.
    """
    if failure_store is not None and failure_store not in FAILURE_STORES:
        raise ValueError(f"unknown failure store: {failure_store}")
    path = repo / SELECTOR_NAME
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["runner_protocol"] = INJECTED_PROTOCOL
    obj["authority_epoch"] = INJECTED_EPOCH
    obj["write_phase"] = INJECTED_EPOCH
    if failure_store is not None:
        obj["activation_failure_store"] = failure_store
    atomic_write(path, (json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8"))
    return selector_fields(path.read_bytes())


def verify_restored(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if after["fields"]["runner_protocol"] != SINGLETON_PROTOCOL:
        errors.append("protocol-not-singleton")
    if after["fields"]["authority_epoch"] != PRIOR_EPOCH:
        errors.append("epoch-not-prior")
    if after["selector"]["digest"] != before["selector"]["digest"]:
        errors.append("selector-digest-mismatch")
    if after["service"]["digest"] != before["service"]["digest"]:
        errors.append("service-digest-mismatch")
    if after["head_ref"] != before["head_ref"]:
        errors.append("head-ref-changed")
    return errors


def prove(repo: Path, failure_store: str | None = None) -> dict[str, Any]:
    """Prove one named failure store rolls back selector and service bytes."""
    before = capture(repo)
    injected: dict[str, str] | None = None
    after: dict[str, Any] | None = None
    errors: list[str] = []
    try:
        if before["fields"]["runner_protocol"] != SINGLETON_PROTOCOL:
            raise RuntimeError("precondition: singleton protocol not active")
        if before["fields"]["authority_epoch"] != PRIOR_EPOCH:
            raise RuntimeError("precondition: prior epoch not active")
        injected = inject_failed_activation(repo, failure_store)
        mid = capture(repo)
        if mid["fields"]["runner_protocol"] == SINGLETON_PROTOCOL:
            raise RuntimeError("injection did not change protocol")
        if mid["fields"]["authority_epoch"] == PRIOR_EPOCH:
            raise RuntimeError("injection did not change epoch")
        restore(repo, before)
        after = capture(repo)
        errors = verify_restored(before, after)
    except Exception:
        restore(repo, before)
        raise
    public_before = {key: before[key] for key in ("head_ref", "selector", "service", "fields")}
    public_after = {key: after[key] for key in ("head_ref", "selector", "service", "fields")}
    return {
        "ok": not errors,
        "failure_store": failure_store,
        "errors": errors,
        "before": public_before,
        "injected": injected,
        "after": public_after,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prove", action="store_true")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--failure-store", choices=FAILURE_STORES)
    args = parser.parse_args()
    if not args.prove:
        parser.error("only --prove is supported")
    result = prove(Path(args.repo).resolve(), args.failure_store)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
