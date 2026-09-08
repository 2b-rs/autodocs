#!/usr/bin/env python3
"""Atomic exclusive-create provenance writers and readers (Task `0037-17.01`).

One JSON object per file at the approved `provenance/` paths. Create is
exclusive (temp file + link); existing identities never overwrite. Identical
canonical payloads replay; a different payload with the same identity is a
collision. Artifact-set files are content-addressed by SHA-256 of canonical
JSON with `set_digest` omitted, then filled in.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

SCHEMA_VERSION = "1.0"
UUIDV7_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
CLASSIFICATIONS = frozenset({"public", "internal", "restricted"})
ENVIRONMENTS = frozenset({"synthetic", "development-test", "production", "assessment"})
EVIDENCE_CLASSES = frozenset(ENVIRONMENTS)
FINDING_STATES = frozenset(
    {"open", "accepted", "rejected", "remediated", "invalidated", "superseded"}
)
RUN_STATUSES = frozenset({"running", "succeeded", "failed", "cancelled", "superseded"})
ENDPOINT_KINDS = (
    "issue",
    "criterion",
    "commit",
    "run",
    "campaign",
    "finding",
    "decision",
    "artifact",
    "artifact-set",
    "record-version",
    "evidence",
    "curation-item",
)
RELATIONS: Dict[str, Tuple[frozenset, frozenset]] = {
    "detected-during": (frozenset({"finding"}), frozenset({"run", "campaign"})),
    "reported-by": (frozenset({"finding"}), frozenset({"issue", "curation-item"})),
    "remediates": (frozenset({"commit", "issue"}), frozenset({"finding", "issue"})),
    "implements": (
        frozenset({"commit", "artifact", "record-version"}),
        frozenset({"issue", "criterion", "decision"}),
    ),
    "verifies": (
        frozenset({"run", "evidence"}),
        frozenset({"criterion", "issue", "artifact", "record-version"}),
    ),
    "triggered": (
        frozenset({"issue", "finding", "decision"}),
        frozenset({"run", "campaign"}),
    ),
    "produced-by": (
        frozenset({"artifact", "artifact-set", "record-version", "evidence"}),
        frozenset({"run", "campaign"}),
    ),
    "derived-from": (
        frozenset({"artifact", "artifact-set", "record-version", "evidence"}),
        frozenset({"artifact", "artifact-set", "record-version", "evidence"}),
    ),
    "invalidated-by": (
        frozenset({"artifact", "artifact-set", "record-version", "evidence", "finding"}),
        frozenset({"finding", "decision", "run"}),
    ),
    "regenerated-by": (
        frozenset({"artifact", "artifact-set", "record-version"}),
        frozenset({"run", "campaign"}),
    ),
    "supersedes": (
        frozenset(
            {
                "issue",
                "finding",
                "decision",
                "artifact",
                "artifact-set",
                "record-version",
                "evidence",
            }
        ),
        frozenset(
            {
                "issue",
                "finding",
                "decision",
                "artifact",
                "artifact-set",
                "record-version",
                "evidence",
            }
        ),
    ),
    "published-as": (
        frozenset({"artifact", "artifact-set", "record-version"}),
        frozenset({"artifact", "evidence"}),
    ),
    "decides": (frozenset({"decision"}), frozenset({"issue", "finding", "criterion"})),
    "blocks": (
        frozenset({"issue", "finding", "decision"}),
        frozenset({"issue", "criterion", "run", "campaign"}),
    ),
}

LEGACY_CONFIDENCE = "legacy"
UNKNOWN_CONFIDENCE = "unknown"

_STORE_LOCK = threading.Lock()


class ProvenanceError(Exception):
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


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def tree_digest(members: list) -> str:
    lines = []
    for member in sorted(members, key=lambda item: item["path"]):
        lines.append(f"{member['path']}:{member['digest']}:{member['size_bytes']}")
    return sha256_bytes("\n".join(lines).encode("utf-8"))


def adapt_legacy_confidence(record: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Map absent or pre-store confidence without inventing numeric scores."""
    if not record:
        return {"confidence": UNKNOWN_CONFIDENCE, "adapter": "legacy-confidence@v1"}
    if "confidence" in record:
        value = record["confidence"]
        if isinstance(value, (int, float)) and 0.0 <= float(value) <= 1.0:
            return {"confidence": float(value), "adapter": "legacy-confidence@v1"}
        if value in (LEGACY_CONFIDENCE, UNKNOWN_CONFIDENCE):
            return {"confidence": value, "adapter": "legacy-confidence@v1"}
        raise ProvenanceError("PV-CONFIDENCE", "invented or out-of-range confidence is rejected")
    if record.get("legacy") or record.get("source") == "legacy":
        return {"confidence": LEGACY_CONFIDENCE, "adapter": "legacy-confidence@v1"}
    return {"confidence": UNKNOWN_CONFIDENCE, "adapter": "legacy-confidence@v1"}


def _parse_dt(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProvenanceError("PV-DATETIME", f"invalid {field}: {value}") from exc
    if parsed.tzinfo is None:
        raise ProvenanceError("PV-DATETIME", f"{field} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _year_month(stamp: str, field: str) -> Tuple[str, str]:
    parsed = _parse_dt(stamp, field)
    return f"{parsed.year:04d}", f"{parsed.month:02d}"


def _require_mapping(value: Any, what: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ProvenanceError("PV-SCHEMA", f"{what} must be a JSON object")
    return value


def _require_uuid(value: Any, field: str) -> str:
    if not isinstance(value, str) or not UUIDV7_RE.match(value):
        raise ProvenanceError("PV-UUID", f"{field} must be a UUIDv7")
    return value


def validate_typed_ref(ref: Any, field: str = "reference") -> Dict[str, Any]:
    obj = _require_mapping(ref, field)
    extra = set(obj) - {
        "schema_version",
        "kind",
        "uri",
        "classification",
        "digest",
        "environment",
        "redacted",
    }
    if extra:
        raise ProvenanceError("PV-SCHEMA", f"{field} has unknown fields: {sorted(extra)}")
    for key in ("schema_version", "kind", "uri", "classification"):
        if key not in obj:
            raise ProvenanceError("PV-SCHEMA", f"{field} missing {key}")
    if obj["schema_version"] != SCHEMA_VERSION:
        raise ProvenanceError("PV-SCHEMA", f"{field} schema_version must be {SCHEMA_VERSION}")
    kind = obj["kind"]
    if kind not in ENDPOINT_KINDS:
        raise ProvenanceError("PV-ENDPOINT", f"{field} unknown kind {kind}")
    uri = obj["uri"]
    if not isinstance(uri, str) or not uri.startswith(kind + ":"):
        raise ProvenanceError("PV-ENDPOINT", f"{field} URI does not match kind {kind}")
    if obj["classification"] not in CLASSIFICATIONS:
        raise ProvenanceError("PV-PRIVACY", f"{field} invalid classification")
    if obj["classification"] == "restricted" and "redacted" not in obj:
        raise ProvenanceError("PV-REDACTION", f"{field} restricted reference requires redacted")
    if "digest" in obj and not SHA256_RE.match(str(obj["digest"])):
        raise ProvenanceError("PV-DIGEST", f"{field} digest must be sha256:<hex>")
    if "environment" in obj and obj["environment"] not in ENVIRONMENTS:
        raise ProvenanceError("PV-ENV", f"{field} invalid environment")
    return obj


def _context_kinds(payload: Mapping[str, Any]) -> set:
    kinds = set()
    for key in ("source", "target", "run", "producer", "subject", "detected_during"):
        if key in payload and isinstance(payload[key], dict):
            kinds.add(payload[key].get("kind"))
    for key in ("inputs", "outputs", "evidence"):
        for item in payload.get(key) or []:
            if isinstance(item, dict):
                kinds.add(item.get("kind"))
    return kinds


class ProvenanceStore:
    def __init__(self, root: Path, *, file_bytes: Optional[Callable[[str], bytes]] = None) -> None:
        self.root = Path(root)
        self.provenance = self.root / "provenance"
        self._file_bytes = file_bytes
        self._inject_before_link: Optional[Callable[[Path, Path], None]] = None

    def event_path(self, event_id: str, occurred_at: str) -> Path:
        year, month = _year_month(occurred_at, "occurred_at")
        return self.provenance / "events" / year / month / f"{event_id}.json"

    def run_path(self, run_id: str) -> Path:
        return self.provenance / "runs" / f"{run_id}.json"

    def finding_path(self, finding_id: str, detected_at: str) -> Path:
        year, month = _year_month(detected_at, "detected_at")
        return self.provenance / "findings" / year / month / f"{finding_id}.json"

    def artifact_set_path(self, digest_hex: str) -> Path:
        return self.provenance / "artifact-sets" / f"{digest_hex}.json"

    def create_run(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        record = self._normalize_run(payload)
        path = self.run_path(record["run_id"])
        return self._exclusive_put(path, record, identity=("run", record["run_id"]))

    def create_finding(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        record = self._normalize_finding(payload)
        path = self.finding_path(record["finding_id"], record["detected_at"])
        return self._exclusive_put(path, record, identity=("finding", record["finding_id"]))

    def create_artifact_set(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        record = self._normalize_artifact_set(payload)
        digest_hex = record["set_digest"].split(":", 1)[1]
        path = self.artifact_set_path(digest_hex)
        self._assert_set_id_unique(record["set_id"], digest_hex)
        return self._exclusive_put(path, record, identity=("artifact-set", record["set_id"]))

    def create_event(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        record = self._normalize_event(payload)
        path = self.event_path(record["event_id"], record["occurred_at"])
        return self._exclusive_put(path, record, identity=("event", record["event_id"]))

    def read_json(self, path: Path) -> Dict[str, Any]:
        if not path.is_file():
            raise ProvenanceError("PV-MISSING", f"no record at {path}")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise ProvenanceError("PV-CORRUPT", f"invalid JSON at {path}") from exc
        if not isinstance(value, dict):
            raise ProvenanceError("PV-CORRUPT", f"non-object JSON at {path}")
        return value

    def read_run(self, run_id: str) -> Dict[str, Any]:
        return self.read_json(self.run_path(run_id))

    def read_finding(self, finding_id: str, detected_at: str) -> Dict[str, Any]:
        return self.read_json(self.finding_path(finding_id, detected_at))

    def read_event(self, event_id: str, occurred_at: str) -> Dict[str, Any]:
        return self.read_json(self.event_path(event_id, occurred_at))

    def read_artifact_set(self, set_digest: str) -> Dict[str, Any]:
        hex_part = set_digest.split(":")[-1]
        return self.read_json(self.artifact_set_path(hex_part))

    def _normalize_run(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        record = dict(payload)
        extra = set(record) - {
            "schema_version",
            "run_id",
            "started_at",
            "ended_at",
            "environment",
            "classification",
            "status",
            "producer",
            "inputs",
            "outputs",
        }
        if extra:
            raise ProvenanceError("PV-SCHEMA", f"run unknown fields: {sorted(extra)}")
        for key in (
            "schema_version",
            "run_id",
            "started_at",
            "ended_at" if record.get("status") != "running" else "run_id",
            "environment",
            "classification",
            "status",
            "producer",
        ):
            if key not in record:
                raise ProvenanceError("PV-SCHEMA", f"run missing {key}")
        if record["schema_version"] != SCHEMA_VERSION:
            raise ProvenanceError("PV-SCHEMA", "run schema_version must be 1.0")
        _require_uuid(record["run_id"], "run_id")
        _parse_dt(record["started_at"], "started_at")
        if "ended_at" in record:
            _parse_dt(record["ended_at"], "ended_at")
        if record["environment"] not in ENVIRONMENTS:
            raise ProvenanceError("PV-ENV", "invalid run environment")
        if record["classification"] not in CLASSIFICATIONS:
            raise ProvenanceError("PV-PRIVACY", "invalid run classification")
        if record["status"] not in RUN_STATUSES:
            raise ProvenanceError("PV-SCHEMA", "invalid run status")
        validate_typed_ref(record["producer"], "producer")
        for name in ("inputs", "outputs"):
            items = record.get(name, [])
            if not isinstance(items, list):
                raise ProvenanceError("PV-SCHEMA", f"run {name} must be an array")
            seen = set()
            for item in items:
                validated = validate_typed_ref(item, name)
                key = canonical_bytes(validated)
                if key in seen:
                    raise ProvenanceError("PV-SCHEMA", f"duplicate {name} reference")
                seen.add(key)
        kinds = _context_kinds(record)
        if not {"issue", "criterion", "campaign"} & kinds and not any(
            item.get("kind") in {"issue", "criterion", "campaign"}
            for item in record.get("inputs") or []
        ):
            raise ProvenanceError(
                "PV-CONTEXT",
                "run requires issue, criterion, or campaign context",
            )
        commit_kinds = [
            item
            for item in (record.get("inputs") or [])
            if isinstance(item, dict) and item.get("kind") == "commit"
        ]
        if len(commit_kinds) < 1:
            raise ProvenanceError("PV-COMMIT", "run requires source/tool/config commit input")
        return record

    def _normalize_finding(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        record = dict(payload)
        extra = set(record) - {
            "schema_version",
            "finding_id",
            "detected_at",
            "state",
            "classification",
            "environment",
            "subject",
            "detected_during",
            "evidence",
            "redaction_reason",
        }
        if extra:
            raise ProvenanceError("PV-SCHEMA", f"finding unknown fields: {sorted(extra)}")
        for key in (
            "schema_version",
            "finding_id",
            "detected_at",
            "state",
            "classification",
            "environment",
            "subject",
        ):
            if key not in record:
                raise ProvenanceError("PV-SCHEMA", f"finding missing {key}")
        if record["schema_version"] != SCHEMA_VERSION:
            raise ProvenanceError("PV-SCHEMA", "finding schema_version must be 1.0")
        _require_uuid(record["finding_id"], "finding_id")
        _parse_dt(record["detected_at"], "detected_at")
        if record["state"] not in FINDING_STATES:
            raise ProvenanceError("PV-SCHEMA", "invalid finding state")
        if record["classification"] not in CLASSIFICATIONS:
            raise ProvenanceError("PV-PRIVACY", "invalid finding classification")
        if record["environment"] not in EVIDENCE_CLASSES:
            raise ProvenanceError("PV-ENV", "invalid finding environment/evidence class")
        if record["classification"] == "restricted":
            if not record.get("redaction_reason"):
                raise ProvenanceError("PV-REDACTION", "restricted finding requires redaction_reason")
        validate_typed_ref(record["subject"], "subject")
        if "detected_during" in record:
            validate_typed_ref(record["detected_during"], "detected_during")
        evidence = record.get("evidence")
        if evidence is not None:
            if not isinstance(evidence, list) or not evidence:
                raise ProvenanceError("PV-SCHEMA", "evidence must be a non-empty array")
            for item in evidence:
                validate_typed_ref(item, "evidence")
        kinds = _context_kinds(record)
        if not {"issue", "criterion", "run", "campaign"} & kinds:
            raise ProvenanceError("PV-CONTEXT", "finding requires typed run/campaign/issue/criterion context")
        return record

    def _normalize_artifact_set(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        record = dict(payload)
        extra = set(record) - {
            "schema_version",
            "set_id",
            "created_at",
            "classification",
            "environment",
            "set_digest",
            "members",
            "producer",
        }
        if extra:
            raise ProvenanceError("PV-SCHEMA", f"artifact-set unknown fields: {sorted(extra)}")
        for key in (
            "schema_version",
            "set_id",
            "created_at",
            "classification",
            "environment",
            "members",
        ):
            if key not in record:
                raise ProvenanceError("PV-SCHEMA", f"artifact-set missing {key}")
        if record["schema_version"] != SCHEMA_VERSION:
            raise ProvenanceError("PV-SCHEMA", "artifact-set schema_version must be 1.0")
        _require_uuid(record["set_id"], "set_id")
        _parse_dt(record["created_at"], "created_at")
        if record["classification"] not in CLASSIFICATIONS:
            raise ProvenanceError("PV-PRIVACY", "invalid artifact-set classification")
        if record["environment"] not in ENVIRONMENTS:
            raise ProvenanceError("PV-ENV", "invalid artifact-set environment")
        if "producer" in record:
            validate_typed_ref(record["producer"], "producer")
        members = record.get("members")
        if not isinstance(members, list) or not members:
            raise ProvenanceError("PV-SCHEMA", "artifact-set members required")
        normalized = []
        paths = set()
        for member in members:
            obj = _require_mapping(member, "member")
            for key in ("path", "digest", "size_bytes", "media_type", "source_commit"):
                if key not in obj:
                    raise ProvenanceError("PV-MEMBER", f"member missing {key}")
            path = obj["path"]
            if path in paths or ".." in Path(path).parts or path.startswith("/"):
                raise ProvenanceError("PV-MEMBER", f"invalid or colliding member path {path}")
            paths.add(path)
            if not SHA256_RE.match(str(obj["digest"])):
                raise ProvenanceError("PV-DIGEST", f"invalid member digest for {path}")
            if not isinstance(obj["size_bytes"], int) or obj["size_bytes"] < 0:
                raise ProvenanceError("PV-MEMBER", f"invalid size_bytes for {path}")
            if not COMMIT_RE.match(str(obj["source_commit"])):
                raise ProvenanceError("PV-COMMIT", f"member {path} source_commit must be a 40-hex commit")
            if obj.get("classification") and obj["classification"] not in CLASSIFICATIONS:
                raise ProvenanceError("PV-PRIVACY", f"invalid member classification for {path}")
            if obj.get("classification") == "restricted" and "redacted" not in obj:
                raise ProvenanceError("PV-REDACTION", f"restricted member {path} requires redacted")
            raw = self._member_bytes(path)
            if raw is not None:
                actual = sha256_bytes(raw)
                if actual != obj["digest"]:
                    raise ProvenanceError(
                        "PV-DIGEST-CHANGE",
                        f"file digest changed for {path}: {obj['digest']} != {actual}",
                    )
                if len(raw) != obj["size_bytes"]:
                    raise ProvenanceError("PV-DIGEST-CHANGE", f"size changed for {path}")
            normalized.append(obj)
        normalized.sort(key=lambda item: item["path"])
        record["members"] = normalized
        body = {key: value for key, value in record.items() if key != "set_digest"}
        digest = sha256_bytes(canonical_bytes(body))
        if "set_digest" in payload and payload["set_digest"] != digest:
            raise ProvenanceError("PV-DIGEST-CHANGE", "artifact-set digest does not match canonical members")
        expected_tree = tree_digest(normalized)
        record["_tree_digest"] = expected_tree
        # `_tree_digest` is computed for tests; it is not persisted (schema forbids extras).
        record.pop("_tree_digest", None)
        record["set_digest"] = digest
        if record.get("classification") == "restricted":
            for member in normalized:
                if member.get("classification") == "restricted" and not member.get("redacted"):
                    raise ProvenanceError("PV-REDACTION", "restricted member must set redacted")
        return record

    def _normalize_event(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        record = dict(payload)
        extra = set(record) - {
            "schema_version",
            "event_id",
            "occurred_at",
            "relation",
            "source",
            "target",
            "environment",
            "classification",
            "run",
            "synthetic_reason",
        }
        if extra:
            raise ProvenanceError("PV-SCHEMA", f"event unknown fields: {sorted(extra)}")
        for key in (
            "schema_version",
            "event_id",
            "occurred_at",
            "relation",
            "source",
            "target",
            "environment",
            "classification",
        ):
            if key not in record:
                raise ProvenanceError("PV-SCHEMA", f"event missing {key}")
        if record["schema_version"] != SCHEMA_VERSION:
            raise ProvenanceError("PV-SCHEMA", "event schema_version must be 1.0")
        _require_uuid(record["event_id"], "event_id")
        _parse_dt(record["occurred_at"], "occurred_at")
        relation = record["relation"]
        if relation not in RELATIONS:
            raise ProvenanceError("PV-RELATION", f"unknown relation {relation}")
        source = validate_typed_ref(record["source"], "source")
        target = validate_typed_ref(record["target"], "target")
        allowed_src, allowed_tgt = RELATIONS[relation]
        if source["kind"] not in allowed_src or target["kind"] not in allowed_tgt:
            raise ProvenanceError("PV-ENDPOINT", f"relation {relation} incompatible with endpoint kinds")
        if source["uri"] == target["uri"] and not (
            relation == "derived-from" and source["kind"] == "record-version"
        ):
            raise ProvenanceError("PV-ENDPOINT", "self-edges are rejected")
        if record["environment"] not in ENVIRONMENTS:
            raise ProvenanceError("PV-ENV", "invalid event environment")
        if record["environment"] == "synthetic" and not record.get("synthetic_reason"):
            raise ProvenanceError("PV-ENV", "synthetic events require synthetic_reason")
        if record["classification"] not in CLASSIFICATIONS:
            raise ProvenanceError("PV-PRIVACY", "invalid event classification")
        if "run" in record:
            validate_typed_ref(record["run"], "run")
        kinds = _context_kinds(record)
        if not {"issue", "criterion", "run", "campaign"} & kinds:
            raise ProvenanceError("PV-CONTEXT", "event requires run/campaign/issue/criterion context")
        self._reject_dangling_and_fabricated(record)
        return record

    def _reject_dangling_and_fabricated(self, record: Mapping[str, Any]) -> None:
        for ref in (record["source"], record["target"], record.get("run")):
            if not ref:
                continue
            kind = ref["kind"]
            ident = ref["uri"].split(":", 1)[1]
            if kind == "run" and UUIDV7_RE.match(ident):
                path = self.run_path(ident)
                if not path.is_file():
                    raise ProvenanceError("PV-DANGLING", f"dangling run {ident}")
            if kind == "finding" and UUIDV7_RE.match(ident):
                matches = list((self.provenance / "findings").glob(f"*/*/{ident}.json"))
                if not matches:
                    raise ProvenanceError("PV-DANGLING", f"dangling finding {ident}")
            if kind == "artifact-set" and SHA256_RE.match("sha256:" + ident if len(ident) == 64 else ident):
                hex_part = ident.split(":")[-1]
                if len(hex_part) == 64 and not self.artifact_set_path(hex_part).is_file():
                    raise ProvenanceError("PV-DANGLING", f"dangling artifact-set {ident}")
        occurred = _parse_dt(record["occurred_at"], "occurred_at")
        run_ref = record.get("run") or (
            record["source"] if record["source"]["kind"] == "run" else None
        ) or (record["target"] if record["target"]["kind"] == "run" else None)
        if run_ref:
            ident = run_ref["uri"].split(":", 1)[1]
            if UUIDV7_RE.match(ident) and self.run_path(ident).is_file():
                run = self.read_json(self.run_path(ident))
                started = _parse_dt(run["started_at"], "started_at")
                if occurred < started:
                    raise ProvenanceError(
                        "PV-FABRICATED",
                        "event occurred_at precedes referenced run start",
                    )

    def _assert_set_id_unique(self, set_id: str, digest_hex: str) -> None:
        directory = self.provenance / "artifact-sets"
        if not directory.is_dir():
            return
        for path in directory.glob("*.json"):
            if path.name.startswith("."):
                continue
            existing = self.read_json(path)
            if existing.get("set_id") == set_id and path.stem != digest_hex:
                raise ProvenanceError("PV-COLLISION", f"artifact-set id {set_id} already bound to another digest")

    def _member_bytes(self, relative: str) -> Optional[bytes]:
        if self._file_bytes is not None:
            try:
                return self._file_bytes(relative)
            except FileNotFoundError:
                return None
        path = self.root / relative
        if path.is_file():
            return path.read_bytes()
        return None

    def _exclusive_put(
        self, path: Path, record: Mapping[str, Any], *, identity: Tuple[str, str]
    ) -> Dict[str, Any]:
        payload = canonical_bytes(record) + b"\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        with _STORE_LOCK:
            if path.exists():
                existing = path.read_bytes()
                if existing == payload:
                    return {"status": "replay", "path": str(path), "record": json.loads(existing)}
                raise ProvenanceError(
                    "PV-COLLISION",
                    f"{identity[0]} {identity[1]} already exists with a different payload",
                )
            self._atomic_create(path, payload)
        return {"status": "created", "path": str(path), "record": json.loads(payload)}

    def _atomic_create(self, path: Path, data: bytes) -> None:
        directory = path.parent
        temporary_name = f".{path.name}.{secrets.token_hex(8)}.tmp"
        tmp_path = directory / temporary_name
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(str(tmp_path), flags, 0o600)
        try:
            os.write(fd, data)
            os.fsync(fd)
            os.fchmod(fd, stat.S_IMODE(0o644))
        finally:
            os.close(fd)
        if self._inject_before_link is not None:
            self._inject_before_link(tmp_path, path)
        try:
            os.link(str(tmp_path), str(path))
        except FileExistsError as exc:
            os.unlink(str(tmp_path))
            raise ProvenanceError("PV-OVERWRITE", f"exclusive create lost the race at {path}") from exc
        os.unlink(str(tmp_path))
        dir_fd = os.open(str(directory), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
