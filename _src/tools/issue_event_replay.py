#!/usr/bin/env python3
"""Exactly-once authorized event replay over a fresh shadow candidate (Task 0037-15.03).

Reads independently authored events, validates base/source/item compatibility and
authority, then writes provenance-event@v1 records into a standing provenance
store. Never mutates shadow item files. Collisions, stale bases, deleted
targets, concurrent claims, unauthorized events, and imported-text mutations
become stable blocking findings with an explicit disposition.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

TOOL_REL = "_src/tools/issue_event_replay.py"
UUID7 = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_HEX = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")

FINDING_UNAUTHORIZED = "event-unauthorized"
FINDING_STALE_BASE = "upgrade-stale-base"
FINDING_TARGET_DELETED = "upgrade-target-deleted"
FINDING_OVERWRITE = "upgrade-overwrite-conflict"
FINDING_DUPLICATE = "event-replay-duplicate"
FINDING_CHANGED = "event-item-changed"
FINDING_CLAIM = "event-concurrent-claim"
FINDING_IDENTITY = "event-identity-incompatible"

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PS = _load("provenance_store", ROOT / "_src/tools/provenance_store.py")


class ReplayError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def finding_id(rule: str, item: str, field: str, locator: str) -> str:
    payload = "|".join((rule, item, field, locator)).encode("utf-8")
    return "RPL-" + hashlib.sha256(payload).hexdigest()[:16]


def uuid7() -> str:
    if hasattr(uuid, "uuid7"):
        return str(uuid.uuid7())
    ts_ms = int(time.time() * 1000)
    rand = os.urandom(10)
    b = bytearray(16)
    b[0] = (ts_ms >> 40) & 0xFF
    b[1] = (ts_ms >> 32) & 0xFF
    b[2] = (ts_ms >> 24) & 0xFF
    b[3] = (ts_ms >> 16) & 0xFF
    b[4] = (ts_ms >> 8) & 0xFF
    b[5] = ts_ms & 0xFF
    b[6] = 0x70 | (rand[0] & 0x0F)
    b[7] = rand[1]
    b[8] = 0x80 | (rand[2] & 0x3F)
    b[9:] = rand[3:]
    hx = bytes(b).hex()
    return f"{hx[0:8]}-{hx[8:12]}-{hx[12:16]}-{hx[16:20]}-{hx[20:32]}"


def _ref(kind: str, ident: str, **extra: Any) -> dict:
    value = {
        "schema_version": "1.0",
        "kind": kind,
        "uri": f"{kind}:{ident}",
        "classification": extra.pop("classification", "internal"),
    }
    value.update(extra)
    return value


def item_digest(body: bytes) -> str:
    return "sha256:" + _sha256_hex(body)


def load_candidate(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ReplayError("RPL-CANDIDATE", "candidate must be a JSON object")
    latest = raw.get("latest_source") or raw.get("source_commit")
    source = raw.get("source_commit") or latest
    if not isinstance(latest, str) or not COMMIT_RE.fullmatch(latest):
        raise ReplayError("RPL-CANDIDATE", "latest_source must be a 40-hex commit")
    if not isinstance(source, str) or not COMMIT_RE.fullmatch(source):
        raise ReplayError("RPL-CANDIDATE", "source_commit must be a 40-hex commit")
    items = raw.get("items") or {}
    if not isinstance(items, dict):
        raise ReplayError("RPL-CANDIDATE", "items must be an object")
    return {
        "source_commit": source,
        "latest_source": latest,
        "schema": raw.get("schema") or "issue-item@v1",
        "items": items,
        "issues_root": raw.get("issues_root"),
        "run_id": raw.get("run_id"),
    }


def load_events(path: Path) -> List[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "events" in raw:
        raw = raw["events"]
    if not isinstance(raw, list):
        raise ReplayError("RPL-EVENTS", "events must be a JSON array")
    return [dict(e) for e in raw]


def _item_record(candidate: Mapping[str, Any], item_id: str) -> Optional[dict]:
    rec = candidate["items"].get(item_id)
    if rec is None:
        return None
    if not isinstance(rec, dict):
        return {"id": item_id, "deleted": True}
    return rec


def _item_body_bytes(candidate: Mapping[str, Any], item: Mapping[str, Any]) -> Optional[bytes]:
    if "body" in item:
        body = item["body"]
        if isinstance(body, bytes):
            return body
        return str(body).encode("utf-8")
    rel = item.get("path")
    root = candidate.get("issues_root")
    if rel and root:
        path = Path(root) / rel
        if path.is_file():
            return path.read_bytes()
    return None


def _current_digest(candidate: Mapping[str, Any], item: Mapping[str, Any]) -> Optional[str]:
    declared = item.get("digest")
    if isinstance(declared, str) and SHA256_HEX.fullmatch(declared):
        return declared if declared.startswith("sha256:") else "sha256:" + declared
    body = _item_body_bytes(candidate, item)
    if body is None:
        return None
    return item_digest(body)


def _blocking(code: str, event_id: str, item_id: str, message: str, disposition: str) -> dict:
    fid = finding_id(code, item_id or "-", "event", event_id or "-")
    return {
        "id": fid,
        "code": code,
        "severity": "blocking",
        "disposition": disposition,
        "event_id": event_id,
        "item_id": item_id,
        "message": message,
    }


def _event_payload(event: Mapping[str, Any]) -> dict:
    payload = {
        "schema_version": event.get("schema_version") or "1.0",
        "event_id": event["event_id"],
        "occurred_at": event["occurred_at"],
        "relation": event["relation"],
        "source": event["source"],
        "target": event["target"],
        "environment": event.get("environment") or "assessment",
        "classification": event.get("classification") or "internal",
    }
    if "run" in event:
        payload["run"] = event["run"]
    if payload["environment"] == "synthetic":
        payload["synthetic_reason"] = event.get("synthetic_reason") or "shadow-candidate-replay"
    return payload


def find_event_by_id(store: Any, event_id: str) -> Optional[dict]:
    events_root = store.provenance / "events"
    if not events_root.is_dir():
        return None
    matches = list(events_root.glob(f"*/*/{event_id}.json"))
    if not matches:
        return None
    return store.read_json(matches[0])


def _ensure_run(store: Any, run_id: str, commit: str, issue_id: str) -> None:
    path = store.run_path(run_id)
    if path.is_file():
        return
    store.create_run(
        {
            "schema_version": "1.0",
            "run_id": run_id,
            "started_at": "2026-08-16T08:00:00Z",
            "ended_at": "2026-08-16T08:01:00Z",
            "environment": "assessment",
            "classification": "internal",
            "status": "succeeded",
            "producer": _ref("commit", commit),
            "inputs": [
                _ref("commit", commit),
                _ref("issue", issue_id),
            ],
            "outputs": [],
        }
    )


def _record_finding(
    store: Any,
    *,
    finding: Mapping[str, Any],
    run_id: str,
    detected_at: str,
) -> None:
    fid = finding["id"]
    # Map RPL- hex into a UUIDv7-shaped finding_id for the store.
    hexpart = hashlib.sha256(fid.encode("utf-8")).hexdigest()
    uuid_id = f"{hexpart[0:8]}-{hexpart[8:12]}-7{hexpart[13:16]}-8{hexpart[17:20]}-{hexpart[20:32]}"
    payload = {
        "schema_version": "1.0",
        "finding_id": uuid_id,
        "detected_at": detected_at,
        "state": "open",
        "classification": "internal",
        "environment": "assessment",
        "subject": _ref("issue", finding.get("item_id") or "0037-15.03"),
        "detected_during": _ref("run", run_id),
    }
    try:
        store.create_finding(payload)
    except PS.ProvenanceError:
        pass


def replay_events(
    *,
    candidate: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    store_root: Path,
    replay_run_id: Optional[str] = None,
    record_findings: bool = True,
) -> dict:
    """Replay events against a fresh candidate. Never writes under issues/."""
    store = PS.ProvenanceStore(store_root)
    run_id = replay_run_id or uuid7()
    source_commit = candidate["source_commit"]
    latest = candidate["latest_source"]
    findings: List[dict] = []
    results: List[dict] = []
    replayed = 0
    skipped = 0

    context_issue = "0037-15.03"
    if candidate["items"]:
        context_issue = sorted(candidate["items"])[0]
    _ensure_run(store, run_id, source_commit if COMMIT_RE.fullmatch(source_commit) else "a" * 40, context_issue)

    seen_ids: Dict[str, dict] = {}

    for event in events:
        event_id = event.get("event_id")
        item_id = str(event.get("item_id") or "")
        if not isinstance(event_id, str) or not UUID7.fullmatch(event_id):
            findings.append(
                _blocking(
                    FINDING_IDENTITY,
                    str(event_id or ""),
                    item_id,
                    "event_id is not an immutable UUIDv7",
                    "reject-invalid-id",
                )
            )
            skipped += 1
            continue

        auth = event.get("reconciliation_authorized_by")
        if not isinstance(auth, str) or not auth.strip():
            findings.append(
                _blocking(
                    FINDING_UNAUTHORIZED,
                    event_id,
                    item_id,
                    "event lacks reconciliation_authorized_by",
                    "reject-unauthorized",
                )
            )
            skipped += 1
            continue

        base = event.get("base_source") or event.get("source_commit")
        if source_commit != latest:
            findings.append(
                _blocking(
                    FINDING_STALE_BASE,
                    event_id,
                    item_id,
                    "candidate source_commit is stale relative to latest_source",
                    "reject-stale-base",
                )
            )
            skipped += 1
            continue
        if isinstance(base, str) and COMMIT_RE.fullmatch(base) and base != latest:
            findings.append(
                _blocking(
                    FINDING_STALE_BASE,
                    event_id,
                    item_id,
                    "event base_source is stale relative to latest_source",
                    "reject-stale-base",
                )
            )
            skipped += 1
            continue

        item = _item_record(candidate, item_id) if item_id else None
        if item_id:
            if item is None or item.get("deleted"):
                findings.append(
                    _blocking(
                        FINDING_TARGET_DELETED,
                        event_id,
                        item_id,
                        "event target item is absent or deleted on the fresh candidate",
                        "reject-deleted-target",
                    )
                )
                skipped += 1
                continue
            claims = list(item.get("active_claims") or item.get("claims") or [])
            event_claim = event.get("claim_token")
            foreign = [c for c in claims if event_claim is None or c != event_claim]
            if foreign:
                findings.append(
                    _blocking(
                        FINDING_CLAIM,
                        event_id,
                        item_id,
                        "concurrent claim on target item; replay refused",
                        "reject-concurrent-claim",
                    )
                )
                skipped += 1
                continue
            current = _current_digest(candidate, item)
            expected = event.get("item_digest")
            if isinstance(expected, str) and SHA256_HEX.fullmatch(expected):
                exp = expected if expected.startswith("sha256:") else "sha256:" + expected
                if current is not None and current != exp:
                    findings.append(
                        _blocking(
                            FINDING_CHANGED,
                            event_id,
                            item_id,
                            "imported item digest changed; event must not rewrite imported text",
                            "reject-changed-item",
                        )
                    )
                    skipped += 1
                    continue
            if event.get("mutates_item") or event.get("mutates_imported_text"):
                findings.append(
                    _blocking(
                        FINDING_OVERWRITE,
                        event_id,
                        item_id,
                        "event would mutate imported text/state; last-writer-wins is forbidden",
                        "reject-overwrite",
                    )
                )
                skipped += 1
                continue

        # Identity compatibility: typed refs must name kinds valid under the store table.
        try:
            payload = _event_payload(event)
            if "run" not in payload:
                payload["run"] = _ref("run", run_id)
            PS.validate_typed_ref(payload["source"], "source")
            PS.validate_typed_ref(payload["target"], "target")
        except (PS.ProvenanceError, KeyError) as exc:
            findings.append(
                _blocking(
                    FINDING_IDENTITY,
                    event_id,
                    item_id,
                    f"identity incompatible with target schema: {exc}",
                    "reject-incompatible-identity",
                )
            )
            skipped += 1
            continue

        # Collision among the batch (same ID, different payload) before store write.
        prior = seen_ids.get(event_id)
        if prior is not None:
            prior_bytes = _canonical_json(_event_payload(prior)).encode("utf-8")
            now_bytes = _canonical_json(payload).encode("utf-8")
            if prior_bytes != now_bytes:
                findings.append(
                    _blocking(
                        FINDING_DUPLICATE,
                        event_id,
                        item_id,
                        "same event_id replayed with a different payload",
                        "reject-collision",
                    )
                )
                skipped += 1
                continue
            results.append({"event_id": event_id, "status": "replay", "item_id": item_id})
            replayed += 1
            continue

        existing = find_event_by_id(store, event_id)
        if existing is not None:
            existing_cmp = {k: existing[k] for k in (
                "schema_version", "event_id", "occurred_at", "relation",
                "source", "target", "environment", "classification",
            ) if k in existing}
            if existing.get("run"):
                existing_cmp["run"] = existing["run"]
            now_bytes = _canonical_json(payload).encode("utf-8")
            old_bytes = _canonical_json(existing_cmp).encode("utf-8")
            if now_bytes != old_bytes:
                findings.append(
                    _blocking(
                        FINDING_DUPLICATE,
                        event_id,
                        item_id,
                        "same event_id already stored with a different payload",
                        "reject-collision",
                    )
                )
                skipped += 1
                continue
            seen_ids[event_id] = event
            results.append({"event_id": event_id, "status": "replay", "item_id": item_id})
            replayed += 1
            continue

        try:
            outcome = store.create_event(payload)
        except PS.ProvenanceError as exc:
            code = getattr(exc, "code", "")
            if code == "PV-COLLISION":
                findings.append(
                    _blocking(
                        FINDING_DUPLICATE,
                        event_id,
                        item_id,
                        str(exc),
                        "reject-collision",
                    )
                )
                skipped += 1
                continue
            findings.append(
                _blocking(
                    FINDING_IDENTITY,
                    event_id,
                    item_id,
                    str(exc),
                    "reject-store",
                )
            )
            skipped += 1
            continue

        seen_ids[event_id] = event
        status = outcome.get("status") or "created"
        results.append({"event_id": event_id, "status": status, "item_id": item_id})
        replayed += 1

    detected_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if record_findings:
        for finding in findings:
            _record_finding(store, finding=finding, run_id=run_id, detected_at=detected_at)

    blocking = [f for f in findings if f.get("severity") == "blocking"]
    report = {
        "schema": "event-replay-report@v1",
        "run_id": run_id,
        "source_commit": source_commit,
        "latest_source": latest,
        "replayed": replayed,
        "skipped": skipped,
        "findings": findings,
        "results": results,
        "promotable": not blocking,
        "candidate_items_mutated": False,
    }
    return report


def dump_report(path: Path, report: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(report), encoding="utf-8")
    os.replace(tmp, path)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Replay authorized events over a shadow candidate.")
    parser.add_argument("--candidate", required=True, help="JSON candidate index (fresh shadow)")
    parser.add_argument("--events", required=True, help="JSON array of independently authored events")
    parser.add_argument("--store-root", required=True, help="standing provenance host root")
    parser.add_argument("--report", help="write event-replay-report@v1 JSON")
    args = parser.parse_args(argv)

    candidate = load_candidate(Path(args.candidate))
    events = load_events(Path(args.events))
    store_root = Path(args.store_root)
    store_root.mkdir(parents=True, exist_ok=True)
    report = replay_events(candidate=candidate, events=events, store_root=store_root)
    if args.report:
        dump_report(Path(args.report), report)
    sys.stdout.write(_canonical_json({"promotable": report["promotable"], "replayed": report["replayed"], "skipped": report["skipped"], "findings": len(report["findings"])}))
    return 0 if report["promotable"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
