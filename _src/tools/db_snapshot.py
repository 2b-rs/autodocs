#!/usr/bin/env python3
"""Deterministic database rebuild / migration / version-snapshot writers (0037-26.04).

Snapshots are exclusive-create directory trees. Semantic identity is derived
only from schema/migration/tool/config commits plus the ordered input artifact
set. Wall-clock and staging paths never enter the identity. Promotion is a
single directory rename from a `.partial-*` staging tree; a crash before that
rename leaves no live snapshot.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Sequence

SCHEMA = "database-snapshot@v1"
SCHEMA_VERSION = "1.0"
OPERATIONS = frozenset({"rebuild", "migrate", "snapshot"})
RECORD_OPS = frozenset({"added", "changed", "deleted"})
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
TRIGGER_KINDS = frozenset({"issue", "finding", "campaign", "run"})
EVIDENCE_KINDS = frozenset({"artifact", "artifact-set", "record-version", "evidence"})


class SnapshotError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def tree_digest(files: Mapping[str, bytes]) -> str:
    lines = []
    for path in sorted(files):
        lines.append(f"{path}:{sha256_bytes(files[path])}:{len(files[path])}")
    return sha256_bytes("\n".join(lines).encode("utf-8"))


def _require_commit(value: Any, field: str) -> str:
    if not isinstance(value, str) or not COMMIT_RE.fullmatch(value):
        raise SnapshotError("SNAP-COMMIT", f"{field} must be a 40-hex Git commit")
    return value


def _require_digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise SnapshotError("SNAP-DIGEST", f"{field} must be sha256:<hex>")
    return value


def _ordered_inputs(inputs: Sequence[Mapping[str, Any]]) -> list:
    ordered = []
    seen = set()
    for item in inputs:
        if not isinstance(item, Mapping):
            raise SnapshotError("SNAP-INPUT", "each input must be an object")
        path = item.get("path")
        digest = item.get("digest")
        size = item.get("size_bytes")
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in Path(path).parts:
            raise SnapshotError("SNAP-INPUT", f"invalid input path {path!r}")
        if path in seen:
            raise SnapshotError("SNAP-INPUT", f"duplicate input path {path}")
        seen.add(path)
        _require_digest(digest, f"input {path} digest")
        if not isinstance(size, int) or size < 0:
            raise SnapshotError("SNAP-INPUT", f"input {path} size_bytes must be >= 0")
        ordered.append({"path": path, "digest": digest, "size_bytes": size})
    return ordered


def _record_changes(changes: Sequence[Mapping[str, Any]]) -> list:
    out = []
    seen = set()
    for item in changes:
        if not isinstance(item, Mapping):
            raise SnapshotError("SNAP-RECORD", "each record change must be an object")
        rec_id = item.get("record_id")
        op = item.get("op")
        if not isinstance(rec_id, str) or not rec_id:
            raise SnapshotError("SNAP-RECORD", "record_id required")
        if op not in RECORD_OPS:
            raise SnapshotError("SNAP-RECORD", f"invalid record op {op!r}")
        key = (rec_id, op, item.get("from_version"), item.get("to_version"))
        if key in seen:
            raise SnapshotError("SNAP-RECORD", f"duplicate record change {rec_id}")
        seen.add(key)
        evidence = item.get("evidence")
        trigger = item.get("trigger")
        if not isinstance(evidence, Mapping) or evidence.get("kind") not in EVIDENCE_KINDS:
            raise SnapshotError("SNAP-TRACE", f"{rec_id} evidence kind missing or invalid")
        if not isinstance(evidence.get("uri"), str) or not evidence["uri"].startswith(
            evidence["kind"] + ":"
        ):
            raise SnapshotError("SNAP-TRACE", f"{rec_id} evidence URI does not match kind")
        _require_digest(evidence.get("digest"), f"{rec_id} evidence digest")
        if not isinstance(trigger, Mapping) or trigger.get("kind") not in TRIGGER_KINDS:
            raise SnapshotError("SNAP-TRACE", f"{rec_id} trigger kind missing or invalid")
        if not isinstance(trigger.get("uri"), str) or not trigger["uri"].startswith(
            trigger["kind"] + ":"
        ):
            raise SnapshotError("SNAP-TRACE", f"{rec_id} trigger URI does not match kind")
        from_v = item.get("from_version")
        to_v = item.get("to_version")
        if op == "added" and from_v is not None:
            raise SnapshotError("SNAP-RECORD", f"{rec_id} added must not set from_version")
        if op == "deleted" and to_v is not None:
            raise SnapshotError("SNAP-RECORD", f"{rec_id} deleted must not set to_version")
        if op == "changed" and (not from_v or not to_v or from_v == to_v):
            raise SnapshotError("SNAP-RECORD", f"{rec_id} changed requires distinct versions")
        out.append(
            {
                "record_id": rec_id,
                "op": op,
                "from_version": from_v,
                "to_version": to_v,
                "evidence": {
                    "kind": evidence["kind"],
                    "uri": evidence["uri"],
                    "digest": evidence["digest"],
                },
                "trigger": {"kind": trigger["kind"], "uri": trigger["uri"]},
            }
        )
    out.sort(
        key=lambda row: (
            row["record_id"],
            row["op"],
            str(row["from_version"]),
            str(row["to_version"]),
        )
    )
    return out


def identity_material(payload: Mapping[str, Any]) -> dict:
    return {
        "schema": SCHEMA,
        "operation": payload["operation"],
        "schema_commit": payload["schema_commit"],
        "migration_commit": payload["migration_commit"],
        "tool_commit": payload["tool_commit"],
        "config_commit": payload["config_commit"],
        "schema_digest": payload["schema_digest"],
        "config_digest": payload["config_digest"],
        "tool_digest": payload["tool_digest"],
        "inputs": payload["inputs"],
        "records": payload["records"],
        "trigger": payload["trigger"],
        "rebuilds": payload.get("rebuilds"),
        "rollback_of": payload.get("rollback_of"),
    }


def semantic_identity(payload: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_bytes(identity_material(payload)))


def detect_drift(
    *,
    inputs: Sequence[Mapping[str, Any]],
    source_files: Mapping[str, bytes],
    schema_bytes: bytes,
    config_bytes: bytes,
    tool_bytes: bytes,
    schema_digest: str,
    config_digest: str,
    tool_digest: str,
) -> list:
    findings = []
    for item in inputs:
        path = item["path"]
        if path not in source_files:
            findings.append({"code": "SNAP-DRIFT-INPUT", "path": path, "reason": "missing"})
            continue
        actual = sha256_bytes(source_files[path])
        if actual != item["digest"] or len(source_files[path]) != item["size_bytes"]:
            findings.append(
                {
                    "code": "SNAP-DRIFT-INPUT",
                    "path": path,
                    "reason": "digest-or-size",
                    "expected": item["digest"],
                    "actual": actual,
                }
            )
    extra = sorted(set(source_files) - {item["path"] for item in inputs})
    for path in extra:
        findings.append({"code": "SNAP-DRIFT-INPUT", "path": path, "reason": "undeclared"})
    actual_schema = sha256_bytes(schema_bytes)
    if actual_schema != schema_digest:
        findings.append(
            {
                "code": "SNAP-DRIFT-SCHEMA",
                "reason": "digest",
                "expected": schema_digest,
                "actual": actual_schema,
            }
        )
    actual_config = sha256_bytes(config_bytes)
    if actual_config != config_digest:
        findings.append(
            {
                "code": "SNAP-DRIFT-CONFIG",
                "reason": "digest",
                "expected": config_digest,
                "actual": actual_config,
            }
        )
    actual_tool = sha256_bytes(tool_bytes)
    if actual_tool != tool_digest:
        findings.append(
            {
                "code": "SNAP-DRIFT-TOOL",
                "reason": "digest",
                "expected": tool_digest,
                "actual": actual_tool,
            }
        )
    return findings


def normalize_envelope(payload: Mapping[str, Any]) -> dict:
    operation = payload.get("operation")
    if operation not in OPERATIONS:
        raise SnapshotError("SNAP-OP", f"operation must be one of {sorted(OPERATIONS)}")
    records = _record_changes(payload.get("records") or [])
    inputs = _ordered_inputs(payload.get("inputs") or [])
    trigger = payload.get("trigger")
    if not isinstance(trigger, Mapping):
        raise SnapshotError("SNAP-TRIGGER", "trigger object required")
    kinds_present = []
    for kind in ("issue", "finding", "campaign", "run"):
        uri = trigger.get(kind)
        if uri is None:
            continue
        if not isinstance(uri, str) or not uri.startswith(kind + ":"):
            raise SnapshotError("SNAP-TRIGGER", f"trigger.{kind} URI mismatch")
        kinds_present.append(kind)
    if not kinds_present:
        raise SnapshotError("SNAP-TRIGGER", "trigger requires issue, finding, campaign, or run")
    envelope = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "operation": operation,
        "schema_commit": _require_commit(payload.get("schema_commit"), "schema_commit"),
        "migration_commit": _require_commit(payload.get("migration_commit"), "migration_commit"),
        "tool_commit": _require_commit(payload.get("tool_commit"), "tool_commit"),
        "config_commit": _require_commit(payload.get("config_commit"), "config_commit"),
        "schema_digest": _require_digest(payload.get("schema_digest"), "schema_digest"),
        "config_digest": _require_digest(payload.get("config_digest"), "config_digest"),
        "tool_digest": _require_digest(payload.get("tool_digest"), "tool_digest"),
        "inputs": inputs,
        "records": records,
        "trigger": {k: trigger[k] for k in ("issue", "finding", "campaign", "run") if k in trigger},
        "environment": payload.get("environment") or "development-test",
    }
    if envelope["environment"] == "production":
        raise SnapshotError("SNAP-ENV", "fixture/synthetic snapshots must not be labeled production")
    for key in ("rebuilds", "rollback_of"):
        if key in payload and payload[key] is not None:
            envelope[key] = _require_digest(payload[key], key)
    envelope["semantic_identity"] = semantic_identity(envelope)
    return envelope


def _write_tree(directory: Path, files: Mapping[str, bytes]) -> None:
    directory.mkdir(parents=True, exist_ok=False)
    for rel, data in files.items():
        dest = directory / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name("." + dest.name + ".tmp-" + secrets.token_hex(4))
        tmp.write_bytes(data)
        os.replace(tmp, dest)


class DatabaseSnapshotStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.live = self.root / "snapshots"
        self.staging = self.root / "staging"
        self.live.mkdir(parents=True, exist_ok=True)
        self.staging.mkdir(parents=True, exist_ok=True)

    def live_path(self, identity_hex: str) -> Path:
        return self.live / identity_hex

    def promote(
        self,
        payload: Mapping[str, Any],
        *,
        source_files: Mapping[str, bytes],
        schema_bytes: bytes,
        config_bytes: bytes,
        tool_bytes: bytes,
        record_blobs: Optional[Mapping[str, bytes]] = None,
        inject_before_promote: Optional[Callable[[Path], None]] = None,
    ) -> dict:
        envelope = normalize_envelope(payload)
        drift = detect_drift(
            inputs=envelope["inputs"],
            source_files=source_files,
            schema_bytes=schema_bytes,
            config_bytes=config_bytes,
            tool_bytes=tool_bytes,
            schema_digest=envelope["schema_digest"],
            config_digest=envelope["config_digest"],
            tool_digest=envelope["tool_digest"],
        )
        if drift:
            raise SnapshotError("SNAP-DRIFT", json.dumps(drift, sort_keys=True))
        identity_hex = envelope["semantic_identity"].split(":", 1)[1]
        dest = self.live_path(identity_hex)
        files = dict(record_blobs or {})
        for item in envelope["inputs"]:
            files[f"inputs/{item['path']}"] = source_files[item["path"]]
        files["schema.bin"] = schema_bytes
        files["config.bin"] = config_bytes
        files["tool.bin"] = tool_bytes
        envelope["output_tree_digest"] = tree_digest(files)
        files["envelope.json"] = canonical_bytes(envelope) + b"\n"
        if dest.exists():
            existing = json.loads((dest / "envelope.json").read_text(encoding="utf-8"))
            if existing.get("semantic_identity") == envelope["semantic_identity"] and existing.get(
                "output_tree_digest"
            ) == envelope["output_tree_digest"]:
                return existing
            raise SnapshotError("SNAP-COLLISION", f"snapshot {identity_hex} already exists with different payload")
        token = secrets.token_hex(8)
        partial = self.staging / f".partial-{identity_hex}-{token}"
        try:
            _write_tree(partial, files)
            if inject_before_promote is not None:
                inject_before_promote(partial)
            os.rename(partial, dest)
        except Exception:
            if partial.exists():
                # leave staging debris; never rename a half-written tree into live
                pass
            if dest.exists() and not (dest / "envelope.json").is_file():
                raise SnapshotError("SNAP-PARTIAL", "live snapshot missing envelope after failed promote")
            raise
        if not (dest / "envelope.json").is_file():
            raise SnapshotError("SNAP-PARTIAL", "promoted snapshot missing envelope")
        return json.loads((dest / "envelope.json").read_text(encoding="utf-8"))

    def list_live(self) -> Iterable[Path]:
        if not self.live.is_dir():
            return []
        return sorted(p for p in self.live.iterdir() if p.is_dir() and not p.name.startswith("."))


def reverse_trace(envelope: Mapping[str, Any], record_id: str) -> dict:
    matches = [row for row in envelope.get("records") or [] if row.get("record_id") == record_id]
    if not matches:
        raise SnapshotError("SNAP-TRACE", f"no record {record_id} in snapshot")
    return {
        "record_id": record_id,
        "changes": matches,
        "trigger": envelope.get("trigger"),
        "semantic_identity": envelope.get("semantic_identity"),
        "inputs": envelope.get("inputs"),
    }
