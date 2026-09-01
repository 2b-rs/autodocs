#!/usr/bin/env python3
"""Digest-bound structural editor for the authoritative legacy Task database.

Planning is pure: an explicit closed operation is checked against exact source
bytes, rendered with byte-preserving splices, reparsed, and written only to a
candidate directory.  Promotion is a separate invocation and supports only one
non-destructive file replacement/creation; multi-file or deletion plans require
the durable transaction coordinator.
"""
from __future__ import annotations

import argparse
import difflib
import errno
import hashlib
import json
import os
import re
import stat
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple


OPERATION_SCHEMA = "legacy-task-editor-operation@v1"
CANDIDATE_SCHEMA = "legacy-task-editor-candidate@v1"
RESULT_SCHEMA = "legacy-task-editor-result@v1"
KINDS = {
    "pickup",
    "progress",
    "closure",
    "wontfix",
    "parent-aggregation",
    "ref-injection",
    "claim-handoff",
    "claim-finalization",
    "append-correction",
}
TASK_ID_RE = re.compile(r"^[0-9]{4}-[0-9]{2}(?:\.[0-9]{2})?$")
FEATURE_ID_RE = re.compile(r"^[0-9]{4}$")
FULL_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{5,127}$")
OPERATION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{5,127}$")
TIMESTAMP_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
OWNER_TOKEN_RE = re.compile(
    r"^agent:(?P<agent>[A-Za-z0-9._-]+):"
    r"(?P<task>[0-9]{4}-[0-9]{2}(?:\.[0-9]{2})?):"
    r"(?P<request>[A-Za-z0-9][A-Za-z0-9._-]{5,127})$"
)
FEATURE_HEADER_RE = re.compile(r"^## Feature: (?P<id>[0-9]{4}) — (?P<title>.+)$")
TASK_HEADER_RE = re.compile(
    r"^- \[(?P<marker> |u|p|\?|w|x)\] "
    r"\*\*(?P<id>[0-9]{4}-[0-9]{2}(?:\.[0-9]{2})?)\*\*"
    r"(?P<tail>.*)$"
)
FIELD_PLAIN_RE = re.compile(r"^(?P<key>[a-z][a-z0-9_]*):\s*(?P<value>.+?)\s*$")
FIELD_LEGACY_RE = re.compile(
    r"^\s*-\s*(?:`(?P<backtick>[a-z][a-z0-9_]*)`|(?P<plain>[a-z][a-z0-9_]*))"
    r":\s*(?P<value>.+?)\s*$"
)
CLAIM_POINTER_RE = re.compile(
    r"^  - \*\*Claim(?: \([^)]*\))?:\*\*.*?via `(?P<path>(?:TODO|DONE)-[^`]+\.md)`, "
    r"`owner_token: (?P<owner>agent:[A-Za-z0-9:._-]+)`.*?"
    r"(?:base|base_commit) `(?P<base>[0-9a-f]{40}|pending-discovery)`.*$"
)
AUTHORITATIVE_REF_RE = re.compile(r"\bREF:\s*(?P<ref>[0-9a-f]{40})\b")
CHECKPOINT_BULLET_RE = re.compile(r"^\s*-\s*\*\*integration review\b", re.IGNORECASE)
RATIONALE_ARCHITECT_RE = re.compile(r"rationale\s*\(architect\)", re.IGNORECASE)
JUSTIFICATION_ARCHITECT_RE = re.compile(r"no-checkpoint justification\s*\(architect\)", re.IGNORECASE)
RATIONALE_LABEL_RE = re.compile(r"\brationale\b", re.IGNORECASE)
JUSTIFICATION_LABEL_RE = re.compile(r"no-checkpoint justification", re.IGNORECASE)
ARCHITECT_AUTHORITY_KEYS = {"role", "rationale"}
MAX_SOURCE_BYTES = 12 * 1024 * 1024
MAX_DIFF_BYTES = 2 * 1024 * 1024
EXIT_OPERATION = 10
EXIT_INPUT = 20
EXIT_RENDER = 30
EXIT_CANDIDATE = 40
EXIT_PROMOTE = 50
EXIT_INTERNAL = 90

TOP_KEYS = {
    "schema",
    "operation_id",
    "kind",
    "recorded_at",
    "subject",
    "actor",
    "backlog",
    "claim",
    "payload",
    "architect_authority",
}
SUBJECT_KEYS = {"feature_id", "task_id"}
ACTOR_KEYS = {"request_id", "owner_token"}
BACKLOG_KEYS = {
    "path",
    "expected_document_sha256",
    "expected_feature_sha256",
    "expected_task_sha256",
    "expected_marker",
}
CLAIM_KEYS = {
    "path",
    "expected_document_sha256",
    "expected_task_id",
    "expected_request_id",
    "expected_owner_token",
    "expected_state",
}
PAYLOAD_FIELDS = {
    "pickup": (
        {"claim_path", "base_commit", "capability_class", "scope", "next_step"},
        {"summary"},
    ),
    "progress": ({"target", "message"}, {"next_step"}),
    "closure": ({"substantive_ref", "summary"}, set()),
    "wontfix": ({"disposition_ref", "reason"}, set()),
    "parent-aggregation": ({"children", "summary"}, set()),
    "ref-injection": ({"new_ref", "reason"}, {"expected_old_ref"}),
    "claim-handoff": (
        {
            "destination_claim_path",
            "new_request_id",
            "new_owner_token",
            "new_capability_class",
            "new_base_commit",
            "scope",
            "next_step",
            "authorization",
            "archive_path",
        },
        set(),
    ),
    "claim-finalization": ({"archive_path"}, set()),
    "append-correction": ({"target", "correction_id", "message"}, set()),
}


class DuplicateKeyError(ValueError):
    pass


class EditorError(RuntimeError):
    def __init__(
        self,
        rule: str,
        message: str,
        phase: str,
        exit_code: int,
        path: str = "",
        subject: str = "",
    ) -> None:
        super().__init__(message)
        self.rule = rule
        self.message = message
        self.phase = phase
        self.exit_code = exit_code
        self.path = path
        self.subject = subject

    def finding(self) -> Dict[str, object]:
        return {
            "rule": self.rule,
            "phase": self.phase,
            "path": self.path,
            "subject": self.subject,
            "message": self.message,
        }


@dataclass(frozen=True)
class Span:
    start: int
    end: int


@dataclass(frozen=True)
class FeatureNode:
    id: str
    line: int
    span: Span


@dataclass(frozen=True)
class TaskNode:
    id: str
    feature_id: str
    marker: str
    line: int
    header: Span
    span: Span
    content_end: int
    sections: Mapping[str, Tuple[Span, ...]]


@dataclass(frozen=True)
class BacklogDocument:
    path: str
    raw: bytes
    text: str
    features: Tuple[FeatureNode, ...]
    tasks: Tuple[TaskNode, ...]


@dataclass(frozen=True)
class ClaimDocument:
    path: str
    raw: bytes
    text: str
    task_id: Optional[str]
    request_id: Optional[str]
    owner_token: Optional[str]
    base_commit: Optional[str]
    capability_class: Optional[str]
    state: Optional[str]


@dataclass(frozen=True)
class Operation:
    data: Mapping[str, object]
    raw_sha256: str
    contract_sha256: str


@dataclass(frozen=True)
class Change:
    path: str
    action: str
    before: Optional[bytes]
    after: Optional[bytes]
    declared_span: Optional[Span]

    def to_manifest(self, candidate_dir: Path) -> Dict[str, object]:
        before_sha = _sha256(self.before) if self.before is not None else None
        after_sha = _sha256(self.after) if self.after is not None else None
        return {
            "path": self.path,
            "action": self.action,
            "before_sha256": before_sha,
            "after_sha256": after_sha,
            "bytes_before": len(self.before) if self.before is not None else 0,
            "bytes_after": len(self.after) if self.after is not None else 0,
            "before_blob": f"blobs/{before_sha}.before" if before_sha else None,
            "after_blob": f"blobs/{after_sha}.after" if after_sha else None,
            "declared_span": (
                {"start": self.declared_span.start, "end": self.declared_span.end}
                if self.declared_span
                else None
            ),
        }


@dataclass(frozen=True)
class EditPlan:
    operation: Operation
    subject: Mapping[str, str]
    changes: Tuple[Change, ...]
    read_set: Mapping[str, str]
    absent_paths: Tuple[str, ...]
    summary: Tuple[str, ...]


@dataclass(frozen=True)
class CandidateReceipt:
    manifest_path: str
    manifest_sha256: str
    diff_path: str
    diff_sha256: str
    changes: int


@dataclass(frozen=True)
class EditorResult:
    verdict: str
    phase: str
    operation_id: str
    kind: str
    changes: Tuple[Mapping[str, object], ...]
    candidate: Optional[Mapping[str, object]]
    promotion: Mapping[str, object]
    findings: Tuple[Mapping[str, object], ...]
    summary: Tuple[str, ...]

    def to_dict(self) -> Dict[str, object]:
        return {
            "schema": RESULT_SCHEMA,
            "verdict": self.verdict,
            "phase": self.phase,
            "operation": {"id": self.operation_id, "kind": self.kind},
            "changes": list(self.changes),
            "candidate": self.candidate,
            "promotion": dict(self.promotion),
            "findings": list(self.findings),
            "summary": list(self.summary),
        }


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _load_json_unique(raw: bytes) -> object:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EditorError("LTE-OP-JSON", "operation is not UTF-8", "operation", EXIT_OPERATION) from exc

    def pairs_hook(pairs: Sequence[Tuple[str, object]]) -> Dict[str, object]:
        result: Dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise DuplicateKeyError(key)
            result[key] = value
        return result

    try:
        return json.loads(text, object_pairs_hook=pairs_hook)
    except DuplicateKeyError as exc:
        raise EditorError("LTE-OP-JSON", f"duplicate JSON key: {exc}", "operation", EXIT_OPERATION) from exc
    except json.JSONDecodeError as exc:
        raise EditorError("LTE-OP-JSON", f"invalid JSON at line {exc.lineno}: {exc.msg}", "operation", EXIT_OPERATION) from exc


def _closed_object(value: object, allowed: Set[str], required: Set[str], location: str) -> Dict[str, object]:
    if not isinstance(value, dict):
        raise EditorError("LTE-OP-SCHEMA", f"{location} must be an object", "operation", EXIT_OPERATION)
    unknown = sorted(set(value) - allowed)
    missing = sorted(required - set(value))
    if unknown:
        raise EditorError("LTE-OP-UNKNOWN-FIELD", f"{location} has unknown fields: {', '.join(unknown)}", "operation", EXIT_OPERATION)
    if missing:
        raise EditorError("LTE-OP-SCHEMA", f"{location} lacks required fields: {', '.join(missing)}", "operation", EXIT_OPERATION)
    return dict(value)


def _single_line(value: object, location: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str):
        raise EditorError("LTE-OP-UNSAFE-VALUE", f"{location} must be a string", "operation", EXIT_OPERATION)
    if (
        any(ord(character) < 32 or ord(character) == 127 for character in value)
        or len(value.splitlines()) != 1
        or "\n" in value
        or "\r" in value
        or "\u2028" in value
        or "\u2029" in value
        or "<!--" in value
        or "-->" in value
        or "```" in value
        or "~~~" in value
        or "<" in value
        or ">" in value
    ):
        raise EditorError("LTE-OP-UNSAFE-VALUE", f"{location} must be one non-structural printable line", "operation", EXIT_OPERATION)
    if nonempty and not value.strip():
        raise EditorError("LTE-OP-UNSAFE-VALUE", f"{location} must not be empty", "operation", EXIT_OPERATION)
    return value.strip()


def _safe_path(value: object, location: str) -> str:
    path = _single_line(value, location)
    pure = PurePosixPath(path)
    if (
        pure.is_absolute()
        or ".." in pure.parts
        or not pure.parts
        or pure.parts[0] == ".git"
        or path == "run.sh"
        or "\\" in path
        or any(character in path for character in "*?[")
    ):
        raise EditorError("LTE-PATH-UNSAFE", f"{location} is not an exact safe repository path: {path}", "operation", EXIT_OPERATION, path=path)
    return pure.as_posix()


def _digest(value: object, location: str) -> str:
    text = _single_line(value, location)
    if not SHA256_RE.fullmatch(text):
        raise EditorError("LTE-OP-SCHEMA", f"{location} must be 64 lowercase hex characters", "operation", EXIT_OPERATION)
    return text


def _full_ref(value: object, location: str) -> str:
    text = _single_line(value, location)
    if not FULL_COMMIT_RE.fullmatch(text):
        raise EditorError("LTE-OP-UNSAFE-VALUE", f"{location} must be a full lowercase 40-hex commit", "operation", EXIT_OPERATION)
    return text


def _owner(value: object, location: str, task_id: str, request_id: str) -> str:
    text = _single_line(value, location)
    match = OWNER_TOKEN_RE.fullmatch(text)
    if not match or match.group("task") != task_id or match.group("request") != request_id:
        raise EditorError("LTE-CLAIM-IDENTITY", f"{location} must bind the exact Task and request", "operation", EXIT_OPERATION)
    return text


def load_operation(raw: bytes) -> Operation:
    value = _load_json_unique(raw)
    top = _closed_object(value, TOP_KEYS, TOP_KEYS - {"claim", "architect_authority"}, "$")
    if top.get("schema") != OPERATION_SCHEMA:
        raise EditorError("LTE-OP-SCHEMA", f"$.schema must be {OPERATION_SCHEMA}", "operation", EXIT_OPERATION)
    operation_id = _single_line(top.get("operation_id"), "$.operation_id")
    if not OPERATION_ID_RE.fullmatch(operation_id):
        raise EditorError("LTE-OP-UNSAFE-VALUE", "$.operation_id has invalid syntax", "operation", EXIT_OPERATION)
    kind = _single_line(top.get("kind"), "$.kind")
    if kind not in KINDS:
        raise EditorError("LTE-OP-SCHEMA", f"unsupported operation kind: {kind}", "operation", EXIT_OPERATION)
    recorded_at = _single_line(top.get("recorded_at"), "$.recorded_at")
    if not TIMESTAMP_RE.fullmatch(recorded_at):
        raise EditorError("LTE-OP-UNSAFE-VALUE", "$.recorded_at must be an explicit UTC second timestamp", "operation", EXIT_OPERATION)

    subject = _closed_object(top.get("subject"), SUBJECT_KEYS, SUBJECT_KEYS, "$.subject")
    feature_id = _single_line(subject.get("feature_id"), "$.subject.feature_id")
    task_id = _single_line(subject.get("task_id"), "$.subject.task_id")
    if not FEATURE_ID_RE.fullmatch(feature_id) or not TASK_ID_RE.fullmatch(task_id) or not task_id.startswith(feature_id + "-"):
        raise EditorError("LTE-OP-UNSAFE-VALUE", "subject Feature/Task identity is invalid", "operation", EXIT_OPERATION)

    actor = _closed_object(top.get("actor"), ACTOR_KEYS, ACTOR_KEYS, "$.actor")
    request_id = _single_line(actor.get("request_id"), "$.actor.request_id")
    if not REQUEST_ID_RE.fullmatch(request_id):
        raise EditorError("LTE-OP-UNSAFE-VALUE", "$.actor.request_id has invalid syntax", "operation", EXIT_OPERATION)
    _owner(actor.get("owner_token"), "$.actor.owner_token", task_id, request_id)

    backlog = _closed_object(top.get("backlog"), BACKLOG_KEYS, BACKLOG_KEYS, "$.backlog")
    backlog["path"] = _safe_path(backlog.get("path"), "$.backlog.path")
    for key in ("expected_document_sha256", "expected_feature_sha256", "expected_task_sha256"):
        backlog[key] = _digest(backlog.get(key), f"$.backlog.{key}")
    marker_value = backlog.get("expected_marker")
    if not isinstance(marker_value, str) or marker_value not in {" ", "u", "p", "?", "w", "x"}:
        raise EditorError("LTE-OP-SCHEMA", "$.backlog.expected_marker is invalid", "operation", EXIT_OPERATION)
    backlog["expected_marker"] = marker_value

    claim_value = top.get("claim")
    claim: Optional[Dict[str, object]] = None
    if claim_value is not None:
        claim = _closed_object(claim_value, CLAIM_KEYS, CLAIM_KEYS, "$.claim")
        claim["path"] = _safe_path(claim.get("path"), "$.claim.path")
        claim["expected_document_sha256"] = _digest(claim.get("expected_document_sha256"), "$.claim.expected_document_sha256")
        claim_task = _single_line(claim.get("expected_task_id"), "$.claim.expected_task_id")
        claim_request = _single_line(claim.get("expected_request_id"), "$.claim.expected_request_id")
        if claim_task != task_id or not REQUEST_ID_RE.fullmatch(claim_request):
            raise EditorError("LTE-CLAIM-IDENTITY", "claim Task/request does not match subject", "operation", EXIT_OPERATION)
        claim["expected_owner_token"] = _owner(claim.get("expected_owner_token"), "$.claim.expected_owner_token", task_id, claim_request)
        state = _single_line(claim.get("expected_state"), "$.claim.expected_state", nonempty=False)
        if state not in {" ", "u", "p", "?", "w", "x"}:
            raise EditorError("LTE-CLAIM-IDENTITY", "claim expected state is invalid", "operation", EXIT_OPERATION)
        claim["expected_state"] = state
        if (
            actor["request_id"] != claim["expected_request_id"]
            or actor["owner_token"] != claim["expected_owner_token"]
        ):
            raise EditorError(
                "LTE-CLAIM-IDENTITY",
                "operation actor must be the exact current claim owner/request",
                "operation",
                EXIT_OPERATION,
                path=str(claim["path"]),
                subject=task_id,
            )

    authority_value = top.get("architect_authority")
    architect_authority: Optional[Dict[str, object]] = None
    if authority_value is not None:
        architect_authority = _closed_object(authority_value, ARCHITECT_AUTHORITY_KEYS, ARCHITECT_AUTHORITY_KEYS, "$.architect_authority")
        role = _single_line(architect_authority.get("role"), "$.architect_authority.role")
        if role != "architect":
            raise EditorError(
                "LTE-CHECKPOINT-AUTHORITY-REQUIRED",
                "$.architect_authority.role must be exactly 'architect'",
                "operation",
                EXIT_OPERATION,
            )
        architect_authority["role"] = role
        architect_authority["rationale"] = _single_line(
            architect_authority.get("rationale"), "$.architect_authority.rationale"
        )

    required_payload, optional_payload = PAYLOAD_FIELDS[kind]
    payload = _closed_object(top.get("payload"), required_payload | optional_payload, required_payload, "$.payload")
    _validate_payload(kind, payload, task_id)
    if kind in {"closure", "wontfix", "claim-handoff", "claim-finalization"} and claim is None:
        raise EditorError("LTE-OP-SCHEMA", f"{kind} requires an exact claim input", "operation", EXIT_OPERATION)
    if kind == "progress" and payload.get("target") == "claim" and claim is None:
        raise EditorError("LTE-OP-SCHEMA", "claim progress requires an exact claim input", "operation", EXIT_OPERATION)
    if kind == "append-correction" and payload.get("target") == "claim" and claim is None:
        raise EditorError("LTE-OP-SCHEMA", "claim correction requires an exact claim input", "operation", EXIT_OPERATION)

    role_paths = [str(backlog["path"])]
    if claim is not None:
        role_paths.append(str(claim["path"]))
    if kind == "pickup":
        role_paths.append(str(payload["claim_path"]))
    elif kind == "claim-handoff":
        role_paths.extend(
            [
                str(payload["destination_claim_path"]),
                str(payload["archive_path"]),
            ]
        )
    elif kind == "claim-finalization":
        role_paths.append(str(payload["archive_path"]))
    if len(role_paths) != len(set(role_paths)):
        raise EditorError(
            "LTE-PATH-UNSAFE",
            "operation path roles must be pairwise disjoint",
            "operation",
            EXIT_OPERATION,
        )

    normalized = dict(top)
    normalized["subject"] = subject
    normalized["actor"] = actor
    normalized["backlog"] = backlog
    normalized["payload"] = payload
    if claim is not None:
        normalized["claim"] = claim
    else:
        normalized.pop("claim", None)
    if architect_authority is not None:
        normalized["architect_authority"] = architect_authority
    else:
        normalized.pop("architect_authority", None)
    contract = _json_bytes(normalized)
    return Operation(normalized, _sha256(raw), _sha256(contract))


def _validate_payload(kind: str, payload: Dict[str, object], task_id: str) -> None:
    narrative_fields = {
        "summary",
        "message",
        "next_step",
        "reason",
        "correction_id",
        "authorization",
    }
    for key in narrative_fields & set(payload):
        payload[key] = _single_line(payload[key], f"$.payload.{key}")
    for key in ("substantive_ref", "disposition_ref", "new_ref", "expected_old_ref"):
        if key in payload and payload[key] is not None:
            payload[key] = _full_ref(payload[key], f"$.payload.{key}")
    for key in ("base_commit", "new_base_commit"):
        if key in payload:
            value = _single_line(payload[key], f"$.payload.{key}")
            if value != "pending-discovery" and not FULL_COMMIT_RE.fullmatch(value):
                raise EditorError("LTE-OP-UNSAFE-VALUE", f"$.payload.{key} must be pending-discovery or a full commit", "operation", EXIT_OPERATION)
            payload[key] = value
    for key in ("claim_path", "destination_claim_path", "archive_path"):
        if key in payload:
            payload[key] = _safe_path(payload[key], f"$.payload.{key}")
    if "scope" in payload:
        scope = payload["scope"]
        if not isinstance(scope, list) or not scope:
            raise EditorError("LTE-OP-SCHEMA", "$.payload.scope must be a nonempty path array", "operation", EXIT_OPERATION)
        payload["scope"] = [_safe_path(value, "$.payload.scope[]") for value in scope]
        if len(set(payload["scope"])) != len(payload["scope"]):
            raise EditorError("LTE-OP-SCHEMA", "$.payload.scope contains duplicates", "operation", EXIT_OPERATION)
    if "capability_class" in payload and payload["capability_class"] not in {"sandboxed/grunt", "sandboxed-grunt", "privileged"}:
        raise EditorError("LTE-OP-SCHEMA", "unsupported claim capability class", "operation", EXIT_OPERATION)
    if "new_capability_class" in payload and payload["new_capability_class"] not in {"sandboxed/grunt", "sandboxed-grunt", "privileged"}:
        raise EditorError("LTE-OP-SCHEMA", "unsupported destination capability class", "operation", EXIT_OPERATION)
    if kind == "progress" and payload.get("target") not in {"backlog", "claim"}:
        raise EditorError("LTE-OP-SCHEMA", "progress target must be backlog or claim", "operation", EXIT_OPERATION)
    if kind == "append-correction" and payload.get("target") not in {"backlog", "claim"}:
        raise EditorError("LTE-OP-SCHEMA", "append-correction target must be backlog or claim", "operation", EXIT_OPERATION)
    if kind == "claim-handoff":
        new_request = _single_line(payload.get("new_request_id"), "$.payload.new_request_id")
        if not REQUEST_ID_RE.fullmatch(new_request):
            raise EditorError("LTE-CLAIM-IDENTITY", "new request ID is invalid", "operation", EXIT_OPERATION)
        payload["new_owner_token"] = _owner(payload.get("new_owner_token"), "$.payload.new_owner_token", task_id, new_request)
    if kind == "parent-aggregation":
        children = payload.get("children")
        if not isinstance(children, list) or not children:
            raise EditorError("LTE-PARENT-CHILD-SET", "children must be a nonempty array", "operation", EXIT_OPERATION)
        normalized_children = []
        for index, child_value in enumerate(children):
            child = _closed_object(
                child_value,
                {"task_id", "marker", "ref", "expected_task_sha256"},
                {"task_id", "marker", "ref", "expected_task_sha256"},
                f"$.payload.children[{index}]",
            )
            child_id = _single_line(child.get("task_id"), "child.task_id")
            if not TASK_ID_RE.fullmatch(child_id) or not child_id.startswith(task_id + "."):
                raise EditorError("LTE-PARENT-CHILD-SET", f"invalid direct child ID: {child_id}", "operation", EXIT_OPERATION)
            child_marker = _single_line(child.get("marker"), "child.marker")
            if child_marker not in {"x", "w"}:
                raise EditorError("LTE-PARENT-CHILD-NONTERMINAL", f"child {child_id} is not terminal", "operation", EXIT_OPERATION)
            child["task_id"] = child_id
            child["marker"] = child_marker
            child["ref"] = _full_ref(child.get("ref"), "child.ref")
            child["expected_task_sha256"] = _digest(child.get("expected_task_sha256"), "child.expected_task_sha256")
            normalized_children.append(child)
        payload["children"] = normalized_children


def _line_table(text: str) -> List[Tuple[int, int, str]]:
    result = []
    position = 0
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        result.append((position, position + len(content), content))
        position += len(line)
    if not text or (text and text[-1] not in "\r\n" and (not result or result[-1][1] != len(text))):
        result.append((position, len(text), text[position:]))
    return result


def _structural_visibility(lines: Sequence[Tuple[int, int, str]]) -> List[bool]:
    visible: List[bool] = []
    fence_character: Optional[str] = None
    fence_length = 0
    in_comment = False
    for _start, _end, line in lines:
        line_visible = fence_character is None and not in_comment
        visible.append(line_visible)

        fence = re.match(
            r"^(?P<indent> {0,3})(?P<fence>`{3,}|~{3,})(?P<rest>.*)$",
            line,
        )
        if fence_character is not None:
            if (
                fence
                and fence.group("fence")[0] == fence_character
                and len(fence.group("fence")) >= fence_length
                and not fence.group("rest").strip()
            ):
                fence_character = None
                fence_length = 0
            continue
        if in_comment:
            end = line.find("-->")
            if end >= 0:
                in_comment = False
            continue
        if fence:
            fence_character = fence.group("fence")[0]
            fence_length = len(fence.group("fence"))
            continue

        position = 0
        while position < len(line):
            start = line.find("<!--", position)
            if start < 0:
                break
            end = line.find("-->", start + 4)
            if end < 0:
                in_comment = True
                break
            position = end + 3
    return visible


def parse_backlog(path: str, raw: bytes) -> BacklogDocument:
    if len(raw) > MAX_SOURCE_BYTES:
        raise EditorError("LTE-INPUT-NONREGULAR", "backlog exceeds input limit", "input", EXIT_INPUT, path=path)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EditorError("LTE-INPUT-NONREGULAR", "backlog is not UTF-8", "input", EXIT_INPUT, path=path) from exc
    lines = _line_table(text)
    visible = _structural_visibility(lines)
    feature_starts: List[Tuple[int, int, re.Match[str]]] = []
    task_starts: List[Tuple[int, int, re.Match[str]]] = []
    for index, (start, _end, line) in enumerate(lines):
        if not visible[index]:
            continue
        feature = FEATURE_HEADER_RE.fullmatch(line)
        if feature:
            feature_starts.append((index, start, feature))
        task = TASK_HEADER_RE.fullmatch(line)
        if task:
            task_starts.append((index, start, task))
    features: List[FeatureNode] = []
    for offset, (line_index, start, match) in enumerate(feature_starts):
        end = feature_starts[offset + 1][1] if offset + 1 < len(feature_starts) else len(text)
        features.append(FeatureNode(match.group("id"), line_index + 1, Span(start, end)))
    tasks: List[TaskNode] = []
    for line_index, start, match in task_starts:
        feature = next((item for item in reversed(features) if item.span.start <= start < item.span.end), None)
        if feature is None:
            raise EditorError("LTE-TASK-BOUNDARY", f"Task {match.group('id')} is outside a canonical Feature", "parse", EXIT_INPUT, path=path, subject=match.group("id"))
        end = feature.span.end
        for next_index in range(line_index + 1, len(lines)):
            next_start, _next_end, next_line = lines[next_index]
            if not visible[next_index] or not next_line:
                continue
            if not next_line.startswith((" ", "\t")):
                end = next_start
                break
        block_lines = text[start:end].splitlines(keepends=True)
        while block_lines and not block_lines[-1].strip():
            block_lines.pop()
        content_end = start + sum(len(line) for line in block_lines)
        header_end = lines[line_index][1]
        sections: Dict[str, List[Span]] = {"Acceptance criteria": [], "Definition of Done": []}
        for section_index in range(line_index + 1, len(lines)):
            section_start, section_end, section_line = lines[section_index]
            if section_start >= end:
                break
            if not visible[section_index]:
                continue
            for name in sections:
                if section_line.startswith(f"  - **{name}:**"):
                    sections[name].append(Span(section_start, section_end))
        tasks.append(
            TaskNode(
                id=match.group("id"),
                feature_id=feature.id,
                marker=match.group("marker"),
                line=line_index + 1,
                header=Span(start, header_end),
                span=Span(start, end),
                content_end=content_end,
                sections={key: tuple(value) for key, value in sections.items()},
            )
        )
    return BacklogDocument(path, raw, text, tuple(features), tuple(tasks))


def parse_claim(path: str, raw: bytes) -> ClaimDocument:
    if len(raw) > MAX_SOURCE_BYTES:
        raise EditorError("LTE-INPUT-NONREGULAR", "claim exceeds input limit", "input", EXIT_INPUT, path=path)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EditorError("LTE-INPUT-NONREGULAR", "claim is not UTF-8", "input", EXIT_INPUT, path=path) from exc
    line_table = _line_table(text)
    lines = [line for _start, _end, line in line_table]
    visible = _structural_visibility(line_table)
    identity = next(
        (
            index
            for index, line in enumerate(lines)
            if visible[index]
            and re.fullmatch(r"##\s+Claim identity\s*", line, re.IGNORECASE)
        ),
        None,
    )
    start = identity + 1 if identity is not None else 0
    end = len(lines)
    for index in range(start, len(lines)):
        if visible[index] and lines[index].startswith("## "):
            end = index
            break
    fields: Dict[str, List[str]] = {}
    for index in range(start, end):
        if not visible[index]:
            continue
        line = lines[index]
        match = FIELD_PLAIN_RE.fullmatch(line)
        if not match:
            match = FIELD_LEGACY_RE.fullmatch(line)
            if match:
                key = match.group("backtick") or match.group("plain")
                value = match.group("value")
            else:
                continue
        else:
            key = match.group("key")
            value = match.group("value")
        value = value.strip().strip("`")
        fields.setdefault(key, []).append(value)
    for key in ("task_id", "request_id", "owner_token", "base_commit", "capability_class", "state"):
        if len(fields.get(key, [])) > 1:
            raise EditorError("LTE-CLAIM-IDENTITY", f"claim field {key} is duplicated", "parse", EXIT_INPUT, path=path)
    owner_token = fields.get("owner_token", [None])[0]
    owner_match = OWNER_TOKEN_RE.fullmatch(owner_token or "")
    task_id = fields.get("task_id", [None])[0]
    request_id = fields.get("request_id", [None])[0]
    if owner_match:
        task_id = task_id or owner_match.group("task")
        request_id = request_id or owner_match.group("request")
        if task_id != owner_match.group("task") or request_id != owner_match.group("request"):
            raise EditorError("LTE-CLAIM-IDENTITY", "claim fields disagree with owner token", "parse", EXIT_INPUT, path=path)
    state = fields.get("state", [None])[0]
    if state and state.startswith("[") and state.endswith("]"):
        state = state[1:-1]
    return ClaimDocument(
        path,
        raw,
        text,
        task_id,
        request_id,
        owner_token,
        fields.get("base_commit", [None])[0],
        fields.get("capability_class", [None])[0],
        state,
    )


def _unique_task(document: BacklogDocument, feature_id: str, task_id: str) -> Tuple[FeatureNode, TaskNode]:
    features = [feature for feature in document.features if feature.id == feature_id]
    if len(features) != 1:
        raise EditorError("LTE-FEATURE-NOT-UNIQUE", f"expected one Feature {feature_id}, found {len(features)}", "parse", EXIT_INPUT, path=document.path, subject=feature_id)
    tasks = [task for task in document.tasks if task.id == task_id]
    if len(tasks) != 1:
        raise EditorError("LTE-TASK-NOT-UNIQUE", f"expected one Task {task_id}, found {len(tasks)}", "parse", EXIT_INPUT, path=document.path, subject=task_id)
    if tasks[0].feature_id != feature_id:
        raise EditorError("LTE-TASK-BOUNDARY", f"Task {task_id} is not inside Feature {feature_id}", "parse", EXIT_INPUT, path=document.path, subject=task_id)
    return features[0], tasks[0]


def _verify_backlog(operation: Operation, sources: Mapping[str, bytes]) -> Tuple[BacklogDocument, FeatureNode, TaskNode]:
    data = operation.data
    backlog = data["backlog"]
    assert isinstance(backlog, dict)
    path = str(backlog["path"])
    raw = sources.get(path)
    if raw is None:
        raise EditorError("LTE-INPUT-MISSING", "backlog input is absent", "input", EXIT_INPUT, path=path)
    if _sha256(raw) != backlog["expected_document_sha256"]:
        raise EditorError("LTE-DOCUMENT-DRIFT", "backlog document digest differs", "input", EXIT_INPUT, path=path)
    document = parse_backlog(path, raw)
    subject = data["subject"]
    assert isinstance(subject, dict)
    feature, task = _unique_task(document, str(subject["feature_id"]), str(subject["task_id"]))
    feature_bytes = document.text[feature.span.start:feature.span.end].encode("utf-8")
    task_bytes = document.text[task.span.start:task.span.end].encode("utf-8")
    if _sha256(feature_bytes) != backlog["expected_feature_sha256"]:
        raise EditorError("LTE-BLOCK-DRIFT", "Feature block digest differs", "input", EXIT_INPUT, path=path, subject=feature.id)
    if _sha256(task_bytes) != backlog["expected_task_sha256"]:
        raise EditorError("LTE-BLOCK-DRIFT", "Task block digest differs", "input", EXIT_INPUT, path=path, subject=task.id)
    if task.marker != backlog["expected_marker"]:
        raise EditorError("LTE-STATE-TRANSITION", f"expected marker [{backlog['expected_marker']}], observed [{task.marker}]", "precondition", EXIT_INPUT, path=path, subject=task.id)
    return document, feature, task


def _verify_claim(operation: Operation, sources: Mapping[str, bytes]) -> Optional[ClaimDocument]:
    claim_spec = operation.data.get("claim")
    if claim_spec is None:
        return None
    assert isinstance(claim_spec, dict)
    path = str(claim_spec["path"])
    raw = sources.get(path)
    if raw is None:
        raise EditorError("LTE-INPUT-MISSING", "claim input is absent", "input", EXIT_INPUT, path=path)
    if _sha256(raw) != claim_spec["expected_document_sha256"]:
        raise EditorError("LTE-CLAIM-FINALIZE-MISMATCH", "claim digest differs", "input", EXIT_INPUT, path=path)
    claim = parse_claim(path, raw)
    expected = {
        "task_id": claim_spec["expected_task_id"],
        "request_id": claim_spec["expected_request_id"],
        "owner_token": claim_spec["expected_owner_token"],
        "state": claim_spec["expected_state"],
    }
    observed = {
        "task_id": claim.task_id,
        "request_id": claim.request_id,
        "owner_token": claim.owner_token,
        "state": claim.state,
    }
    if observed != expected:
        raise EditorError("LTE-CLAIM-IDENTITY", f"claim identity differs: expected {expected}, observed {observed}", "precondition", EXIT_INPUT, path=path, subject=str(expected["task_id"]))
    owner_match = OWNER_TOKEN_RE.fullmatch(claim.owner_token or "")
    if owner_match is None:
        raise EditorError("LTE-CLAIM-IDENTITY", "claim owner token is malformed", "precondition", EXIT_INPUT, path=path, subject=claim.task_id or "")
    expected_filename = (
        f"TODO-{owner_match.group('agent')}-{owner_match.group('task')}-"
        f"{owner_match.group('request')}.md"
    )
    if path != expected_filename:
        raise EditorError("LTE-CLAIM-IDENTITY", f"claim path must match immutable identity: {expected_filename}", "precondition", EXIT_INPUT, path=path, subject=claim.task_id or "")
    return claim


def _task_text(document: BacklogDocument, task: TaskNode) -> str:
    return document.text[task.span.start:task.span.end]


def _header_text(document: BacklogDocument, task: TaskNode) -> str:
    return document.text[task.header.start:task.header.end]


def _visible_ref_matches(header: str) -> List[re.Match[str]]:
    hidden: List[Tuple[int, int]] = []
    position = 0
    while position < len(header):
        start = header.find("<!--", position)
        if start < 0:
            break
        end = header.find("-->", start + 4)
        if end < 0:
            hidden.append((start, len(header)))
            break
        hidden.append((start, end + 3))
        position = end + 3
    return [
        match
        for match in AUTHORITATIVE_REF_RE.finditer(header)
        if not any(start <= match.start() < end for start, end in hidden)
    ]


def _visible_task_lines(block: str) -> List[str]:
    lines = _line_table(block)
    visible = _structural_visibility(lines)
    return [line for index, (_start, _end, line) in enumerate(lines) if visible[index]]


def _insert_at_content_end(block: str, task: TaskNode, text: str) -> str:
    relative = task.content_end - task.span.start
    prefix = block[:relative]
    suffix = block[relative:]
    if prefix and not prefix.endswith(("\n", "\r")):
        prefix += "\n"
    return prefix + text + suffix


def _replace_header(block: str, task: TaskNode, header: str) -> str:
    relative_end = task.header.end - task.span.start
    return header + block[relative_end:]


def _newline(document: BacklogDocument) -> str:
    return "\r\n" if "\r\n" in document.text and document.text.count("\r\n") >= document.text.count("\n") / 2 else "\n"


def _claim_pointer(task_block: str) -> Optional[re.Match[str]]:
    matches = [match for line in _visible_task_lines(task_block) if (match := CLAIM_POINTER_RE.fullmatch(line))]
    if len(matches) > 1:
        raise EditorError("LTE-CLAIM-POINTER", "Task has multiple claim pointers", "precondition", EXIT_INPUT)
    return matches[0] if matches else None


def _assert_pointer(task_block: str, claim: ClaimDocument) -> re.Match[str]:
    pointer = _claim_pointer(task_block)
    if pointer is None:
        raise EditorError("LTE-CLAIM-POINTER", "Task has no exact claim pointer", "precondition", EXIT_INPUT, path=claim.path, subject=claim.task_id or "")
    if (
        pointer.group("path") != claim.path
        or pointer.group("owner") != claim.owner_token
        or pointer.group("base") != claim.base_commit
    ):
        raise EditorError("LTE-CLAIM-POINTER", "Task pointer does not name the exact claim path/token/base", "precondition", EXIT_INPUT, path=claim.path, subject=claim.task_id or "")
    return pointer


def _checkpoint_attribute_line(line: str) -> Optional[Dict[str, object]]:
    """Parse a structural ``- **Integration review: ...`` attribute bullet.

    Mirrors ``legacy_task_doctor._checkpoint_attribute_line`` exactly (kept as
    an independent copy so each ``_src/tools/`` script stays a standalone,
    dependency-free file per project convention). Returns ``None`` when the
    line is not the attribute bullet itself; prose that merely quotes or
    discusses the attribute does not count. Otherwise returns the parsed
    polarity (``True``/``False``/``None`` for mandatory/not-mandatory/
    unrecognized) plus whether an ``(architect)``-tagged Rationale/
    No-checkpoint justification label is present on the same line.
    """

    if not CHECKPOINT_BULLET_RE.match(line):
        return None
    stripped = re.sub(r"[*`]", "", line)
    match = re.search(r"integration review:?\s*(?P<rest>.+)", stripped, re.IGNORECASE)
    if not match:
        return {
            "mandatory": None,
            "has_rationale_label": False,
            "has_justification_label": False,
            "architect_tagged": False,
        }
    first_clause = match.group("rest").split(".")[0]
    starts_with_mandatory = bool(re.match(r"\s*mandatory\b", first_clause, re.IGNORECASE))
    starts_with_not_mandatory = bool(re.match(r"\s*not\s+mandatory\b", first_clause, re.IGNORECASE))
    has_not = bool(re.search(r"\bnot\b", first_clause, re.IGNORECASE))
    mandatory: Optional[bool]
    if starts_with_mandatory:
        mandatory = not has_not
    elif starts_with_not_mandatory:
        mandatory = False
    else:
        mandatory = None
    return {
        "mandatory": mandatory,
        "has_rationale_label": bool(RATIONALE_LABEL_RE.search(stripped)),
        "has_justification_label": bool(JUSTIFICATION_LABEL_RE.search(stripped)),
        "architect_tagged": bool(
            RATIONALE_ARCHITECT_RE.search(stripped) or JUSTIFICATION_ARCHITECT_RE.search(stripped)
        ),
    }


def _checkpoint_lines(text: str) -> List[str]:
    return [line for line in text.splitlines() if CHECKPOINT_BULLET_RE.match(line)]


def _enforce_checkpoint_authority(operation: Operation, before: str, after: str, task_id: str, path: str) -> None:
    """Refuse any rendered change to an ``Integration review:`` attribute
    bullet unless the operation carries an explicit ``architect_authority``
    assertion, and unless the resulting bullet(s) are themselves well-formed
    (Task ``0038-23``; ``AGENTS.md`` — "Sandboxed/grunt implementers never
    set, clear, or move the attribute").

    Comparing the exact set of attribute bullets before/after means ordinary
    operations that never touch the attribute (the overwhelming majority)
    pay no cost and are never asked for authority they have no reason to
    carry; only a render that actually adds, removes, or edits a checkpoint
    bullet is gated. Architect authority is a self-declared role assertion
    carried in the operation, not a capability-class fact: `_
    docs/pipeline/process-roles.md` fixes the architect's minimum capability
    class at `sandboxed/grunt`, so capability class cannot stand in for it.
    """

    before_lines = _checkpoint_lines(before)
    after_lines = _checkpoint_lines(after)
    if before_lines == after_lines:
        return
    authority = operation.data.get("architect_authority")
    if not isinstance(authority, dict) or authority.get("role") != "architect" or not authority.get("rationale"):
        raise EditorError(
            "LTE-CHECKPOINT-AUTHORITY-REQUIRED",
            "change sets, clears, or moves an Integration review attribute without an architect_authority assertion",
            "precondition",
            EXIT_INPUT,
            path=path,
            subject=task_id,
        )
    for line in after_lines:
        parsed = _checkpoint_attribute_line(line)
        if (
            parsed is None
            or parsed["mandatory"] is None
            or not parsed["architect_tagged"]
            or not (parsed["has_rationale_label"] or parsed["has_justification_label"])
        ):
            raise EditorError(
                "LTE-CHECKPOINT-MALFORMED",
                "rendered Integration review attribute lacks a recognized polarity or an (architect)-tagged rationale/justification",
                "render",
                EXIT_RENDER,
                path=path,
                subject=task_id,
            )


def _render_task_change(operation: Operation, document: BacklogDocument, task: TaskNode, claim: Optional[ClaimDocument], sources: Mapping[str, bytes]) -> Tuple[Change, ...]:
    data = operation.data
    kind = str(data["kind"])
    payload = data["payload"]
    subject = data["subject"]
    actor = data["actor"]
    backlog = data["backlog"]
    assert isinstance(payload, dict) and isinstance(subject, dict) and isinstance(actor, dict) and isinstance(backlog, dict)
    task_id = str(subject["task_id"])
    date = str(data["recorded_at"])[:10]
    nl = _newline(document)
    block = _task_text(document, task)
    header = _header_text(document, task)
    new_block = block
    changes: List[Change] = []

    if kind == "pickup":
        if task.marker not in {" ", "?"}:
            raise EditorError("LTE-STATE-TRANSITION", "pickup requires [ ] or [?]", "precondition", EXIT_INPUT, path=document.path, subject=task_id)
        existing = [parse_claim(path, raw) for path, raw in sources.items() if path.startswith("TODO-") and path.endswith(".md")]
        if any(item.task_id == task_id and item.state == "p" for item in existing):
            raise EditorError("LTE-CLAIM-CONFLICT", "another active claim resolves to the Task", "precondition", EXIT_INPUT, path=document.path, subject=task_id)
        claim_path = str(payload["claim_path"])
        if claim_path in sources:
            raise EditorError("LTE-CLAIM-CONFLICT", "destination claim already exists", "precondition", EXIT_INPUT, path=claim_path, subject=task_id)
        owner = str(actor["owner_token"])
        request = str(actor["request_id"])
        owner_match = OWNER_TOKEN_RE.fullmatch(owner)
        assert owner_match is not None
        expected_filename = f"TODO-{owner_match.group('agent')}-{task_id}-{request}.md"
        if claim_path != expected_filename:
            raise EditorError("LTE-CLAIM-IDENTITY", f"claim path must be {expected_filename}", "precondition", EXIT_INPUT, path=claim_path, subject=task_id)
        new_header = header.replace(f"- [{task.marker}]", "- [p]", 1)
        pointer = (
            f"  - **Claim ({date}):** Claimed via `{claim_path}`, "
            f"`owner_token: {owner}`, base `{payload['base_commit']}`."
        )
        relative_header_end = task.header.end - task.span.start
        new_block = new_header + nl + pointer + block[relative_header_end:]
        claim_lines = [
            f"# {claim_path} — active claim",
            "",
            "## Claim identity",
            "",
            f"task_id: {task_id}",
            f"feature_id: {subject['feature_id']}",
            f"capability_class: {payload['capability_class']}",
            f"request_id: {request}",
            f"owner_token: {owner}",
            f"base_commit: {payload['base_commit']}",
            "state: [p]",
            "",
            "## Intended write scope",
            "",
        ]
        claim_lines.extend(f"- `{path}`" for path in payload["scope"])
        claim_lines.extend(["", "## Next step", "", str(payload["next_step"]), ""])
        changes.append(Change(claim_path, "create", None, nl.join(claim_lines).encode("utf-8"), None))

    elif kind == "progress":
        if task.marker != "p":
            raise EditorError("LTE-STATE-TRANSITION", "progress requires an active [p] Task", "precondition", EXIT_INPUT, path=document.path, subject=task_id)
        message = f"  - **Progress ({date}, {data['operation_id']}):** {payload['message']}{nl}"
        if payload["target"] == "backlog":
            new_block = _insert_at_content_end(block, task, message)
        else:
            assert claim is not None
            if claim.state != "p":
                raise EditorError("LTE-STATE-TRANSITION", "claim progress requires an active [p] claim", "precondition", EXIT_INPUT, path=claim.path, subject=task_id)
            _assert_pointer(block, claim)
            claim_text = claim.text
            if claim_text and not claim_text.endswith(("\n", "\r")):
                claim_text += nl
            addition = f"{nl}## Progress {data['operation_id']}{nl}{nl}- {payload['message']}{nl}"
            if payload.get("next_step"):
                addition += f"{nl}## Next step{nl}{nl}{payload['next_step']}{nl}"
            claim_after = (claim_text + addition).encode("utf-8")
            changes.append(Change(claim.path, "replace", claim.raw, claim_after, Span(len(claim.text), len(claim.text))))

    elif kind == "closure":
        if task.marker != "p" or claim is None or claim.state != "p":
            raise EditorError("LTE-STATE-TRANSITION", "closure requires an active [p] Task and [p] claim", "precondition", EXIT_INPUT, path=document.path, subject=task_id)
        if len(task.sections["Definition of Done"]) != 1:
            raise EditorError("LTE-SECTION-NOT-UNIQUE", "closure requires exactly one Definition of Done", "precondition", EXIT_INPUT, path=document.path, subject=task_id)
        _assert_pointer(block, claim)
        if _visible_ref_matches(header):
            raise EditorError("LTE-REF-AMBIGUOUS", "active Task already has a visible authoritative REF", "precondition", EXIT_INPUT, path=document.path, subject=task_id)
        new_header = header.replace("- [p]", "- [x]", 1).rstrip() + f" REF: {payload['substantive_ref']}"
        dod = task.sections["Definition of Done"][0]
        insert = dod.end - task.span.start
        closure = f"{nl}  - **Closure ({date}, {data['operation_id']}):** {payload['summary']}"
        new_block = block[:insert] + closure + block[insert:]
        new_block = _replace_header(new_block, task, new_header)

    elif kind == "wontfix":
        if task.marker != "p" or claim is None or claim.state != "p":
            raise EditorError("LTE-STATE-TRANSITION", "wontfix requires an active [p] Task and [p] claim", "precondition", EXIT_INPUT, path=document.path, subject=task_id)
        _assert_pointer(block, claim)
        if _visible_ref_matches(header):
            raise EditorError("LTE-REF-AMBIGUOUS", "nonterminal Task already has a visible authoritative REF", "precondition", EXIT_INPUT, path=document.path, subject=task_id)
        new_header = header.replace(f"- [{task.marker}]", "- [w]", 1).rstrip() + f" REF: {payload['disposition_ref']}"
        relative_header_end = task.header.end - task.span.start
        reason = f"{nl}  - **Reason ({date}, {data['operation_id']}):** {payload['reason']}"
        new_block = new_header + reason + block[relative_header_end:]

    elif kind == "parent-aggregation":
        if task.marker != "p":
            raise EditorError("LTE-STATE-TRANSITION", "parent aggregation requires an active [p] parent", "precondition", EXIT_INPUT, path=document.path, subject=task_id)
        if len(task.sections["Definition of Done"]) != 1:
            raise EditorError("LTE-SECTION-NOT-UNIQUE", "parent aggregation requires exactly one Definition of Done", "precondition", EXIT_INPUT, path=document.path, subject=task_id)
        actual = [
            item
            for item in document.tasks
            if item.feature_id == task.feature_id
            and item.id.startswith(task_id + ".")
            and item.id.count(".") == task_id.count(".") + 1
        ]
        if len({item.id for item in actual}) != len(actual):
            raise EditorError("LTE-PARENT-CHILD-SET", "direct child IDs are duplicated", "precondition", EXIT_INPUT, path=document.path, subject=task_id)
        declared = payload["children"]
        assert isinstance(declared, list)
        declared_ids = {str(item["task_id"]) for item in declared}
        if declared_ids != {item.id for item in actual}:
            raise EditorError("LTE-PARENT-CHILD-SET", f"declared children {sorted(declared_ids)} differ from actual children {sorted(item.id for item in actual)}", "precondition", EXIT_INPUT, path=document.path, subject=task_id)
        child_by_id = {item.id: item for item in actual}
        for child_spec in declared:
            child = child_by_id[str(child_spec["task_id"])]
            child_bytes = document.text[child.span.start:child.span.end].encode("utf-8")
            child_header = _header_text(document, child)
            if (
                child.marker != child_spec["marker"]
                or _sha256(child_bytes) != child_spec["expected_task_sha256"]
                or [match.group("ref") for match in _visible_ref_matches(child_header)]
                != [str(child_spec["ref"])]
            ):
                raise EditorError("LTE-PARENT-CHILD-NONTERMINAL", f"child {child.id} state/digest/REF differs", "precondition", EXIT_INPUT, path=document.path, subject=child.id)
        ids = ", ".join(f"`{item['task_id']}`" for item in declared)
        note = f"  - **Aggregation ({date}, {data['operation_id']}):** Direct children {ids} are terminal at their recorded REFs; {payload['summary']}{nl}"
        new_block = _insert_at_content_end(block, task, note)

    elif kind == "ref-injection":
        if task.marker not in {"x", "w"}:
            raise EditorError("LTE-STATE-TRANSITION", "REF injection/correction requires a terminal Task", "precondition", EXIT_INPUT, path=document.path, subject=task_id)
        new_ref = str(payload["new_ref"])
        refs = _visible_ref_matches(header)
        expected_old = payload.get("expected_old_ref")
        if expected_old is None:
            if refs:
                raise EditorError("LTE-REF-AMBIGUOUS", "REF insertion expected no existing authoritative REF", "precondition", EXIT_INPUT, path=document.path, subject=task_id)
            new_header = header.rstrip() + f" REF: {new_ref}"
            new_block = _replace_header(block, task, new_header)
        else:
            if len(refs) != 1 or refs[0].group("ref") != expected_old:
                raise EditorError("LTE-REF-AMBIGUOUS", "expected old REF is absent or ambiguous", "precondition", EXIT_INPUT, path=document.path, subject=task_id)
            new_header = header[: refs[0].start("ref")] + new_ref + header[refs[0].end("ref") :]
            correction = (
                f"  - **REF correction ({date}, {data['operation_id']}):** Header REF corrected from "
                f"`{expected_old}` to `{new_ref}`; {payload['reason']}{nl}"
            )
            new_block = _insert_at_content_end(block, task, correction)
            new_block = _replace_header(new_block, task, new_header)

    elif kind == "append-correction":
        marker = str(payload["correction_id"])
        if marker in block or (claim and marker in claim.text):
            raise EditorError("LTE-NOOP", "correction ID already exists", "precondition", EXIT_INPUT, subject=task_id)
        correction = f"  - **Correction {marker} ({date}):** {payload['message']}{nl}"
        if payload["target"] == "backlog":
            new_block = _insert_at_content_end(block, task, correction)
        else:
            assert claim is not None
            if task.marker != "p" or claim.state != "p":
                raise EditorError("LTE-STATE-TRANSITION", "claim correction requires an active [p] Task and claim", "precondition", EXIT_INPUT, path=claim.path, subject=task_id)
            _assert_pointer(block, claim)
            claim_text = claim.text
            if claim_text and not claim_text.endswith(("\n", "\r")):
                claim_text += nl
            claim_after = (claim_text + f"{nl}## Correction {marker}{nl}{nl}- {payload['message']}{nl}").encode("utf-8")
            changes.append(Change(claim.path, "replace", claim.raw, claim_after, Span(len(claim.text), len(claim.text))))

    elif kind == "claim-handoff":
        assert claim is not None
        if task.marker != "p" or claim.state != "p":
            raise EditorError("LTE-STATE-TRANSITION", "handoff requires an active [p] Task and claim", "precondition", EXIT_INPUT, path=claim.path, subject=task_id)
        pointer = _assert_pointer(block, claim)
        if payload["authorization"] != "explicit-owner-release-or-authorized-decision":
            raise EditorError("LTE-CLAIM-IDENTITY", "handoff lacks exact authorization token", "precondition", EXIT_INPUT, path=claim.path, subject=task_id)
        destination = str(payload["destination_claim_path"])
        if destination in sources:
            raise EditorError("LTE-CLAIM-CONFLICT", "destination claim already exists", "precondition", EXIT_INPUT, path=destination, subject=task_id)
        new_owner = str(payload["new_owner_token"])
        new_request = str(payload["new_request_id"])
        owner_match = OWNER_TOKEN_RE.fullmatch(new_owner)
        assert owner_match is not None
        expected_destination = f"TODO-{owner_match.group('agent')}-{task_id}-{new_request}.md"
        if destination != expected_destination:
            raise EditorError("LTE-CLAIM-IDENTITY", f"destination claim path must be {expected_destination}", "precondition", EXIT_INPUT, path=destination, subject=task_id)
        old_pointer = pointer.group(0)
        new_pointer = (
            f"  - **Claim ({date}):** Claimed via `{destination}`, `owner_token: {new_owner}`, "
            f"base `{payload['new_base_commit']}`. Handoff from `{claim.path}`."
        )
        new_block = block.replace(old_pointer, new_pointer, 1)
        claim_lines = [
            f"# {destination} — active claim",
            "",
            "## Claim identity",
            "",
            f"task_id: {task_id}",
            f"feature_id: {subject['feature_id']}",
            f"capability_class: {payload['new_capability_class']}",
            f"request_id: {new_request}",
            f"owner_token: {new_owner}",
            f"base_commit: {payload['new_base_commit']}",
            "state: [p]",
            "",
            "## Handoff",
            "",
            f"- predecessor_path: `{claim.path}`",
            f"- predecessor_owner_token: `{claim.owner_token}`",
            f"- predecessor_sha256: `{_sha256(claim.raw)}`",
            "",
            "## Intended write scope",
            "",
        ]
        claim_lines.extend(f"- `{path}`" for path in payload["scope"])
        claim_lines.extend(["", "## Next step", "", str(payload["next_step"]), ""])
        changes.extend(
            [
                Change(destination, "create", None, nl.join(claim_lines).encode("utf-8"), None),
                Change(str(payload["archive_path"]), "create", None, claim.raw, None),
                Change(claim.path, "delete", claim.raw, None, None),
            ]
        )

    elif kind == "claim-finalization":
        assert claim is not None
        if claim.state != "p":
            raise EditorError("LTE-CLAIM-FINALIZE-MISMATCH", "claim finalization requires the exact active [p] claim", "precondition", EXIT_INPUT, path=claim.path, subject=task_id)
        pointer = _assert_pointer(block, claim)
        del pointer
        if task.marker not in {"x", "w"} or len(_visible_ref_matches(header)) != 1:
            raise EditorError("LTE-CLAIM-FINALIZE-MISMATCH", "claim finalization requires a terminal Task with one visible full REF", "precondition", EXIT_INPUT, path=document.path, subject=task_id)
        pointer_line = next(line for line in _visible_task_lines(block) if CLAIM_POINTER_RE.fullmatch(line))
        finalized = f"  - **Claim finalized ({date}, {data['operation_id']}):** `{claim.path}` archived after terminal verification."
        new_block = block.replace(pointer_line, finalized, 1)
        changes.extend(
            [
                Change(str(payload["archive_path"]), "create", None, claim.raw, None),
                Change(claim.path, "delete", claim.raw, None, None),
            ]
        )

    if new_block != block:
        _enforce_checkpoint_authority(operation, block, new_block, task_id, document.path)
        after_text = document.text[: task.span.start] + new_block + document.text[task.span.end :]
        if not after_text.startswith(document.text[: task.span.start]) or not after_text.endswith(document.text[task.span.end :]):
            raise EditorError("LTE-UNRELATED-BYTES", "render changed bytes outside the Task span", "render", EXIT_RENDER, path=document.path, subject=task_id)
        changes.insert(0, Change(document.path, "replace", document.raw, after_text.encode("utf-8"), task.span))
    if not changes:
        raise EditorError("LTE-NOOP", "operation produced no byte change", "render", EXIT_RENDER, subject=task_id)
    return tuple(changes)


def _postconditions(operation: Operation, changes: Sequence[Change]) -> None:
    backlog_change = next((change for change in changes if change.path == operation.data["backlog"]["path"]), None)  # type: ignore[index]
    if backlog_change and backlog_change.after:
        if backlog_change.before is None:
            raise EditorError("LTE-CANDIDATE-POSTCONDITION", "backlog replacement lacks a preimage", "render", EXIT_RENDER, path=backlog_change.path)
        before_document = parse_backlog(backlog_change.path, backlog_change.before)
        candidate = parse_backlog(backlog_change.path, backlog_change.after)
        def inventory(document: BacklogDocument) -> Tuple[object, object]:
            return (
                [feature.id for feature in document.features],
                [
                    (
                        item.id,
                        item.feature_id,
                        tuple(
                            (name, len(spans))
                            for name, spans in sorted(item.sections.items())
                        ),
                    )
                    for item in document.tasks
                ],
            )

        if inventory(before_document) != inventory(candidate):
            raise EditorError("LTE-UNRELATED-BYTES", "candidate changes the visible Feature/Task/section inventory", "render", EXIT_RENDER, path=backlog_change.path)
        subject = operation.data["subject"]
        assert isinstance(subject, dict)
        _feature, task = _unique_task(candidate, str(subject["feature_id"]), str(subject["task_id"]))
        _before_feature, before_task = _unique_task(
            before_document,
            str(subject["feature_id"]),
            str(subject["task_id"]),
        )
        kind = str(operation.data["kind"])
        before_pointer_count = len(
            [
                line
                for line in _visible_task_lines(_task_text(before_document, before_task))
                if CLAIM_POINTER_RE.fullmatch(line)
            ]
        )
        after_pointer_count = len(
            [
                line
                for line in _visible_task_lines(_task_text(candidate, task))
                if CLAIM_POINTER_RE.fullmatch(line)
            ]
        )
        expected_pointer_count = {
            "pickup": 1,
            "claim-finalization": 0,
        }.get(kind, before_pointer_count)
        if after_pointer_count != expected_pointer_count:
            raise EditorError("LTE-CANDIDATE-POSTCONDITION", "candidate claim-pointer inventory differs", "render", EXIT_RENDER, path=backlog_change.path, subject=task.id)
        expected_marker = {
            "pickup": "p",
            "closure": "x",
            "wontfix": "w",
        }.get(kind)
        if expected_marker and task.marker != expected_marker:
            raise EditorError("LTE-CANDIDATE-POSTCONDITION", f"candidate marker is [{task.marker}], expected [{expected_marker}]", "render", EXIT_RENDER, path=backlog_change.path, subject=task.id)
        if kind in {"closure", "wontfix", "ref-injection"} and len(_visible_ref_matches(_header_text(candidate, task))) != 1:
            raise EditorError("LTE-CANDIDATE-POSTCONDITION", "candidate does not carry exactly one visible authoritative header REF", "render", EXIT_RENDER, path=backlog_change.path, subject=task.id)


def plan_operation(operation: Operation, sources: Mapping[str, bytes]) -> EditPlan:
    document, _feature, task = _verify_backlog(operation, sources)
    claim = _verify_claim(operation, sources)
    changes = _render_task_change(operation, document, task, claim, sources)
    _postconditions(operation, changes)
    summaries = (
        f"legacy-task-editor planned {operation.data['kind']} for {operation.data['subject']['task_id']}",  # type: ignore[index]
        f"changes={len(changes)} candidate-required=true promotion-performed=false",
    )
    read_set = {path: _sha256(raw) for path, raw in sorted(sources.items())}
    absent_paths = tuple(
        sorted(
            change.path
            for change in changes
            if change.action == "create" and change.path not in sources
        )
    )
    return EditPlan(
        operation,
        operation.data["subject"],  # type: ignore[arg-type]
        changes,
        read_set,
        absent_paths,
        summaries,
    )


def _diff_for_changes(changes: Sequence[Change]) -> bytes:
    parts: List[str] = []
    for change in sorted(changes, key=lambda item: item.path):
        before = change.before.decode("utf-8").splitlines(keepends=True) if change.before is not None else []
        after = change.after.decode("utf-8").splitlines(keepends=True) if change.after is not None else []
        fromfile = f"a/{change.path}" if change.before is not None else "/dev/null"
        tofile = f"b/{change.path}" if change.after is not None else "/dev/null"
        parts.extend(difflib.unified_diff(before, after, fromfile=fromfile, tofile=tofile, lineterm="\n"))
    encoded = "".join(parts).encode("utf-8")
    if len(encoded) > MAX_DIFF_BYTES:
        raise EditorError("LTE-CANDIDATE-POSTCONDITION", "candidate diff exceeds review budget", "candidate", EXIT_CANDIDATE)
    return encoded


def _path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _open_dir_nofollow(path: Path, *, create: bool = False) -> int:
    """Open an existing directory without traversing escaping symlinks.

    Leading OS aliases (macOS ``/var`` -> ``/private/var``) are followed because
    the resolved target remains under the current physical prefix.  A directory
    symlink whose target leaves that prefix is never followed: the original
    ``O_NOFOLLOW`` failure is re-raised, so symlink-escape attempts are still
    rejected.  This mirrors the fix already carried by
    ``runner_transaction._open_directory_nofollow`` (Task ``0038-10``).
    """
    absolute = path.absolute()
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    nofollow_flags = directory_flags | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(os.sep, directory_flags)
    current_physical = Path(os.path.realpath(os.sep))
    try:
        for part in absolute.parts[1:]:
            if create:
                try:
                    os.mkdir(part, 0o755, dir_fd=descriptor)
                except FileExistsError:
                    pass
            try:
                next_descriptor = os.open(part, nofollow_flags, dir_fd=descriptor)
            except OSError as exc:
                if exc.errno not in (errno.ENOTDIR, errno.ELOOP):
                    raise
                try:
                    link_stat = os.lstat(part, dir_fd=descriptor)
                except OSError:
                    raise exc
                if not stat.S_ISLNK(link_stat.st_mode):
                    raise
                raw_target = Path(os.readlink(part, dir_fd=descriptor))
                if raw_target.is_absolute():
                    resolved_target = Path(os.path.realpath(raw_target))
                else:
                    resolved_target = Path(os.path.realpath(current_physical / raw_target))
                if not _path_is_relative_to(resolved_target, current_physical):
                    raise
                next_descriptor = os.open(part, directory_flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
            current_physical = Path(os.path.realpath(current_physical / part))
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _atomic_write(
    path: Path,
    data: bytes,
    mode: int = 0o644,
    *,
    exclusive: bool = False,
) -> None:
    directory_fd = _open_dir_nofollow(path.parent, create=True)
    temporary = f".{path.name}.lte-{_sha256(data)[:12]}"
    descriptor: Optional[int] = None
    try:
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=directory_fd,
        )
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
            os.fchmod(handle.fileno(), stat.S_IMODE(mode))
        if exclusive:
            try:
                os.link(
                    temporary,
                    path.name,
                    src_dir_fd=directory_fd,
                    dst_dir_fd=directory_fd,
                    follow_symlinks=False,
                )
            except FileExistsError as exc:
                raise EditorError(
                    "LTE-PROMOTE-DRIFT",
                    "exclusive create target appeared during promotion",
                    "promote",
                    EXIT_PROMOTE,
                    path=path.name,
                ) from exc
            os.unlink(temporary, dir_fd=directory_fd)
        else:
            os.replace(temporary, path.name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
        os.fsync(directory_fd)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            os.unlink(temporary, dir_fd=directory_fd)
        except FileNotFoundError:
            pass
        os.close(directory_fd)



def write_candidate(plan: EditPlan, candidate_dir: Path) -> CandidateReceipt:
    if candidate_dir.exists() or candidate_dir.is_symlink():
        raise EditorError("LTE-CANDIDATE-TAMPERED", "candidate directory already exists", "candidate", EXIT_CANDIDATE, path=candidate_dir.name)
    candidate_dir.mkdir(parents=True, exist_ok=False)
    blobs_dir = candidate_dir / "blobs"
    blobs_dir.mkdir()
    manifests = []
    for change in sorted(plan.changes, key=lambda item: item.path):
        item = change.to_manifest(candidate_dir)
        manifests.append(item)
        if change.before is not None:
            _atomic_write(candidate_dir / str(item["before_blob"]), change.before)
        if change.after is not None:
            _atomic_write(candidate_dir / str(item["after_blob"]), change.after)
    diff_bytes = _diff_for_changes(plan.changes)
    diff_path = candidate_dir / "diff.patch"
    _atomic_write(diff_path, diff_bytes)
    manifest = {
        "schema": CANDIDATE_SCHEMA,
        "operation": {
            "id": plan.operation.data["operation_id"],
            "kind": plan.operation.data["kind"],
            "raw_sha256": plan.operation.raw_sha256,
            "contract_sha256": plan.operation.contract_sha256,
            "contract": plan.operation.data,
            "subject": plan.subject,
        },
        "changes": manifests,
        "read_set": [
            {"path": path, "sha256": digest}
            for path, digest in sorted(plan.read_set.items())
        ],
        "absent_paths": list(plan.absent_paths),
        "diff": {"path": "diff.patch", "sha256": _sha256(diff_bytes), "bytes": len(diff_bytes)},
        "promotion": {"standalone_allowed": False},
    }
    manifest_bytes = _json_bytes(manifest)
    manifest_path = candidate_dir / "candidate.json"
    _atomic_write(manifest_path, manifest_bytes)
    return CandidateReceipt(
        manifest_path="candidate.json",
        manifest_sha256=_sha256(manifest_bytes),
        diff_path="diff.patch",
        diff_sha256=_sha256(diff_bytes),
        changes=len(manifests),
    )


def _read_regular_nofollow(path: Path) -> bytes:
    directory_fd = _open_dir_nofollow(path.parent)
    descriptor: Optional[int] = None
    try:
        descriptor = os.open(
            path.name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=directory_fd,
        )
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise EditorError("LTE-INPUT-NONREGULAR", "path is not a regular non-symlink file", "input", EXIT_INPUT, path=path.name)
        chunks: List[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    except OSError as exc:
        raise EditorError("LTE-INPUT-NONREGULAR", f"cannot read exact path: {exc.strerror or exc.__class__.__name__}", "input", EXIT_INPUT, path=path.name) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(directory_fd)


def _safe_target(root: Path, relative: str, *, allow_absent_final: bool = False) -> Path:
    _safe_path(relative, "candidate change path")
    current = root
    parts = PurePosixPath(relative).parts
    for index, part in enumerate(parts):
        current = current / part
        final = index == len(parts) - 1
        try:
            info = current.lstat()
        except FileNotFoundError:
            if final and allow_absent_final:
                return current
            if not final:
                raise EditorError("LTE-PATH-UNSAFE", "target parent is missing", "promote", EXIT_PROMOTE, path=relative)
            raise
        if stat.S_ISLNK(info.st_mode):
            raise EditorError("LTE-PATH-UNSAFE", "target traverses a symlink", "promote", EXIT_PROMOTE, path=relative)
        if not final and not stat.S_ISDIR(info.st_mode):
            raise EditorError("LTE-PATH-UNSAFE", "target parent is not a directory", "promote", EXIT_PROMOTE, path=relative)
    return current


def _candidate_error(message: str, path: str = "") -> EditorError:
    return EditorError(
        "LTE-CANDIDATE-TAMPERED",
        message,
        "candidate",
        EXIT_CANDIDATE,
        path=path,
    )


def _candidate_object(
    value: object,
    allowed: Set[str],
    required: Set[str],
    location: str,
) -> Dict[str, object]:
    if not isinstance(value, dict):
        raise _candidate_error(f"{location} must be an object")
    unknown = sorted(set(value) - allowed)
    missing = sorted(required - set(value))
    if unknown or missing:
        raise _candidate_error(
            f"{location} field mismatch: unknown={unknown} missing={missing}"
        )
    return dict(value)


def _validate_candidate_manifest(value: object) -> Dict[str, object]:
    top_keys = {
        "schema",
        "operation",
        "changes",
        "read_set",
        "absent_paths",
        "diff",
        "promotion",
    }
    manifest = _candidate_object(value, top_keys, top_keys, "candidate")
    if manifest["schema"] != CANDIDATE_SCHEMA:
        raise _candidate_error("unsupported candidate schema")
    operation = _candidate_object(
        manifest["operation"],
        {"id", "kind", "raw_sha256", "contract_sha256", "contract", "subject"},
        {"id", "kind", "raw_sha256", "contract_sha256", "contract", "subject"},
        "candidate.operation",
    )
    if (
        not OPERATION_ID_RE.fullmatch(str(operation["id"]))
        or operation["kind"] not in KINDS
        or not SHA256_RE.fullmatch(str(operation["raw_sha256"]))
        or not SHA256_RE.fullmatch(str(operation["contract_sha256"]))
    ):
        raise _candidate_error("candidate operation identity is invalid")
    contract_operation = load_operation(_json_bytes(operation["contract"]))
    if contract_operation.contract_sha256 != operation["contract_sha256"]:
        raise _candidate_error("candidate operation contract digest differs")
    if (
        contract_operation.data["operation_id"] != operation["id"]
        or contract_operation.data["kind"] != operation["kind"]
    ):
        raise _candidate_error("candidate operation summary differs from contract")
    operation["contract"] = contract_operation.data
    subject = _candidate_object(
        operation["subject"],
        SUBJECT_KEYS,
        SUBJECT_KEYS,
        "candidate.operation.subject",
    )
    if (
        not FEATURE_ID_RE.fullmatch(str(subject["feature_id"]))
        or not TASK_ID_RE.fullmatch(str(subject["task_id"]))
        or subject != contract_operation.data["subject"]
    ):
        raise _candidate_error("candidate subject identity is invalid or differs from contract")
    operation["subject"] = subject
    manifest["operation"] = operation

    changes_value = manifest["changes"]
    if not isinstance(changes_value, list) or not changes_value:
        raise _candidate_error("candidate changes must be a nonempty array")
    change_keys = {
        "path",
        "action",
        "before_sha256",
        "after_sha256",
        "bytes_before",
        "bytes_after",
        "before_blob",
        "after_blob",
        "declared_span",
    }
    changes: List[Dict[str, object]] = []
    seen_paths: Set[str] = set()
    for index, item in enumerate(changes_value):
        change = _candidate_object(
            item,
            change_keys,
            change_keys,
            f"candidate.changes[{index}]",
        )
        path = _safe_path(change["path"], "candidate change path")
        if path in seen_paths:
            raise _candidate_error(f"duplicate candidate change path: {path}")
        seen_paths.add(path)
        action = change["action"]
        if action not in {"replace", "create", "delete"}:
            raise _candidate_error(f"invalid candidate action: {action}", path)
        before_sha = change["before_sha256"]
        after_sha = change["after_sha256"]
        if before_sha is not None and not SHA256_RE.fullmatch(str(before_sha)):
            raise _candidate_error("invalid before digest", path)
        if after_sha is not None and not SHA256_RE.fullmatch(str(after_sha)):
            raise _candidate_error("invalid after digest", path)
        if action == "replace" and (before_sha is None or after_sha is None):
            raise _candidate_error("replace requires before and after digests", path)
        if action == "create" and (before_sha is not None or after_sha is None):
            raise _candidate_error("create digest shape is invalid", path)
        if action == "delete" and (before_sha is None or after_sha is not None):
            raise _candidate_error("delete digest shape is invalid", path)
        expected_before_blob = f"blobs/{before_sha}.before" if before_sha else None
        expected_after_blob = f"blobs/{after_sha}.after" if after_sha else None
        if change["before_blob"] != expected_before_blob or change["after_blob"] != expected_after_blob:
            raise _candidate_error("candidate blob path is not content-addressed", path)
        if not isinstance(change["bytes_before"], int) or not isinstance(change["bytes_after"], int):
            raise _candidate_error("candidate byte counts must be integers", path)
        span = change["declared_span"]
        if span is not None:
            span_obj = _candidate_object(
                span,
                {"start", "end"},
                {"start", "end"},
                "candidate declared_span",
            )
            if not all(isinstance(span_obj[key], int) for key in ("start", "end")):
                raise _candidate_error("candidate span must use integer offsets", path)
            change["declared_span"] = span_obj
        change["path"] = path
        changes.append(change)
    manifest["changes"] = changes

    read_value = manifest["read_set"]
    if not isinstance(read_value, list) or not read_value:
        raise _candidate_error("candidate read_set must be nonempty")
    read_set: List[Dict[str, object]] = []
    read_paths: Set[str] = set()
    for index, item in enumerate(read_value):
        entry = _candidate_object(
            item,
            {"path", "sha256"},
            {"path", "sha256"},
            f"candidate.read_set[{index}]",
        )
        path = _safe_path(entry["path"], "candidate read path")
        digest = str(entry["sha256"])
        if path in read_paths or not SHA256_RE.fullmatch(digest):
            raise _candidate_error("candidate read_set has duplicate/invalid entry", path)
        read_paths.add(path)
        read_set.append({"path": path, "sha256": digest})
    manifest["read_set"] = read_set

    absent_value = manifest["absent_paths"]
    if not isinstance(absent_value, list):
        raise _candidate_error("candidate absent_paths must be an array")
    absent = [_safe_path(item, "candidate absent path") for item in absent_value]
    if len(set(absent)) != len(absent):
        raise _candidate_error("candidate absent_paths contains duplicates")
    manifest["absent_paths"] = absent

    read_map = {str(entry["path"]): str(entry["sha256"]) for entry in read_set}
    create_paths = {str(change["path"]) for change in changes if change["action"] == "create"}
    if set(absent) != create_paths:
        raise _candidate_error("candidate absent_paths must exactly equal create paths")
    if set(absent) & set(read_map):
        raise _candidate_error("candidate read_set and absent_paths overlap")
    for change in changes:
        path = str(change["path"])
        if change["action"] in {"replace", "delete"} and read_map.get(path) != change["before_sha256"]:
            raise _candidate_error("changed preimage is absent from read_set or has a different digest", path)
    contract = contract_operation.data
    contract_backlog = contract["backlog"]
    assert isinstance(contract_backlog, dict)
    if read_map.get(str(contract_backlog["path"])) != contract_backlog["expected_document_sha256"]:
        raise _candidate_error("contract backlog preimage is missing from read_set")
    contract_claim = contract.get("claim")
    if isinstance(contract_claim, dict):
        if read_map.get(str(contract_claim["path"])) != contract_claim["expected_document_sha256"]:
            raise _candidate_error("contract claim preimage is missing from read_set")

    diff = _candidate_object(
        manifest["diff"],
        {"path", "sha256", "bytes"},
        {"path", "sha256", "bytes"},
        "candidate.diff",
    )
    if diff["path"] != "diff.patch" or not SHA256_RE.fullmatch(str(diff["sha256"])) or not isinstance(diff["bytes"], int):
        raise _candidate_error("candidate diff entry is invalid")
    manifest["diff"] = diff
    promotion = _candidate_object(
        manifest["promotion"],
        {"standalone_allowed"},
        {"standalone_allowed"},
        "candidate.promotion",
    )
    expected_standalone = False
    if promotion["standalone_allowed"] is not expected_standalone:
        raise _candidate_error("candidate standalone promotion flag is inconsistent")
    manifest["promotion"] = promotion
    return manifest


def _candidate_member(candidate_root: Path, relative: str) -> bytes:
    _safe_path(relative, "candidate member path")
    try:
        root_info = candidate_root.lstat()
    except OSError as exc:
        raise _candidate_error("candidate root is missing") from exc
    if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
        raise _candidate_error("candidate root is not a regular directory")
    current = candidate_root
    for index, part in enumerate(PurePosixPath(relative).parts):
        current = current / part
        try:
            info = current.lstat()
        except OSError as exc:
            raise _candidate_error("candidate member is missing", relative) from exc
        if stat.S_ISLNK(info.st_mode):
            raise _candidate_error("candidate member traverses a symlink", relative)
        final = index == len(PurePosixPath(relative).parts) - 1
        if not final and not stat.S_ISDIR(info.st_mode):
            raise _candidate_error("candidate member parent is not a directory", relative)
        if final and not stat.S_ISREG(info.st_mode):
            raise _candidate_error("candidate member is not a regular file", relative)
    return _read_regular_nofollow(current)


def _verify_absent_path(root: Path, relative: str) -> None:
    _safe_path(relative, "candidate absent path")
    current = root
    parts = PurePosixPath(relative).parts
    for index, part in enumerate(parts):
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            return
        if stat.S_ISLNK(info.st_mode):
            raise EditorError("LTE-PATH-UNSAFE", "absent path traverses a symlink", "promote", EXIT_PROMOTE, path=relative)
        final = index == len(parts) - 1
        if not final and not stat.S_ISDIR(info.st_mode):
            raise EditorError("LTE-PATH-UNSAFE", "absent path parent is not a directory", "promote", EXIT_PROMOTE, path=relative)
        if final:
            raise EditorError("LTE-PROMOTE-DRIFT", "planning absent path now exists", "promote", EXIT_PROMOTE, path=relative)


def _verify_manifest_read_set(root: Path, manifest: Mapping[str, object]) -> None:
    for entry in manifest["read_set"]:  # type: ignore[index]
        assert isinstance(entry, dict)
        path = str(entry["path"])
        try:
            target = _safe_target(root, path)
            current = _read_regular_nofollow(target)
        except (FileNotFoundError, EditorError) as exc:
            raise EditorError("LTE-PROMOTE-DRIFT", "planning read-set path is missing or unsafe", "promote", EXIT_PROMOTE, path=path) from exc
        if _sha256(current) != entry["sha256"]:
            raise EditorError("LTE-PROMOTE-DRIFT", "planning read-set path changed", "promote", EXIT_PROMOTE, path=path)
    for relative in manifest["absent_paths"]:  # type: ignore[index]
        _verify_absent_path(root, str(relative))


def verify_candidate_for_promotion(
    root: Path,
    manifest_path: Path,
    expected_manifest_sha256: str,
) -> Mapping[str, object]:
    """Validate every candidate member and current planning preimage without mutation."""
    manifest_bytes = _read_regular_nofollow(manifest_path)
    if _sha256(manifest_bytes) != expected_manifest_sha256:
        raise _candidate_error("candidate manifest digest differs", manifest_path.name)
    manifest = _validate_candidate_manifest(_load_json_unique(manifest_bytes))
    changes = manifest["changes"]
    assert isinstance(changes, list)
    candidate_changes: List[Change] = []
    for change in changes:
        assert isinstance(change, dict)
        before = None
        after = None
        if change["before_blob"] is not None:
            before = _candidate_member(manifest_path.parent, str(change["before_blob"]))
            if _sha256(before) != change["before_sha256"] or len(before) != change["bytes_before"]:
                raise _candidate_error("before blob digest/size differs", str(change["path"]))
        if change["after_blob"] is not None:
            after = _candidate_member(manifest_path.parent, str(change["after_blob"]))
            if _sha256(after) != change["after_sha256"] or len(after) != change["bytes_after"]:
                raise _candidate_error("after blob digest/size differs", str(change["path"]))
        span_value = change["declared_span"]
        span = Span(int(span_value["start"]), int(span_value["end"])) if isinstance(span_value, dict) else None
        candidate_changes.append(
            Change(str(change["path"]), str(change["action"]), before, after, span)
        )
    diff = manifest["diff"]
    assert isinstance(diff, dict)
    diff_bytes = _candidate_member(manifest_path.parent, str(diff["path"]))
    if (
        _sha256(diff_bytes) != diff["sha256"]
        or len(diff_bytes) != diff["bytes"]
        or _diff_for_changes(candidate_changes) != diff_bytes
    ):
        raise _candidate_error("candidate diff does not match verified blobs")
    root = root.resolve()
    _verify_manifest_read_set(root, manifest)
    operation_entry = manifest["operation"]
    assert isinstance(operation_entry, dict)
    embedded_operation = load_operation(_json_bytes(operation_entry["contract"]))
    fresh_sources = _load_sources(root, embedded_operation)
    replanned = plan_operation(embedded_operation, fresh_sources)
    expected_read_set = {path: digest for path, digest in replanned.read_set.items()}
    observed_read_set = {
        str(entry["path"]): str(entry["sha256"])
        for entry in manifest["read_set"]
    }
    if expected_read_set != observed_read_set:
        raise _candidate_error("candidate read_set differs from fresh operation planning")
    if tuple(sorted(replanned.absent_paths)) != tuple(sorted(str(path) for path in manifest["absent_paths"])):
        raise _candidate_error("candidate absent_paths differ from fresh operation planning")
    expected_changes = sorted(replanned.changes, key=lambda item: item.path)
    observed_changes = sorted(candidate_changes, key=lambda item: item.path)
    if expected_changes != observed_changes:
        raise _candidate_error("candidate changes differ from fresh operation rendering")
    if _diff_for_changes(expected_changes) != diff_bytes:
        raise _candidate_error("candidate diff differs from fresh operation rendering")
    return manifest


def promote_candidate(root: Path, manifest_path: Path, expected_manifest_sha256: str) -> EditorResult:
    manifest = verify_candidate_for_promotion(
        root,
        manifest_path,
        expected_manifest_sha256,
    )
    operation = manifest["operation"]
    assert isinstance(operation, dict)
    subject = operation["subject"]
    assert isinstance(subject, dict)
    diff = manifest["diff"]
    assert isinstance(diff, dict)
    finding = {
        "rule": "LTE-PROMOTE-COORDINATOR-REQUIRED",
        "phase": "promote",
        "path": "",
        "subject": str(subject["task_id"]),
        "message": (
            "candidate and all current preimages verified; authoritative "
            "publication belongs to Task 0038-05.02 durable coordinator integration"
        ),
    }
    candidate_evidence = {
        "manifest_path": manifest_path.name,
        "manifest_sha256": expected_manifest_sha256,
        "preflight_verified": True,
        "diff": dict(diff),
        "read_set": list(manifest["read_set"]),
        "absent_paths": list(manifest["absent_paths"]),
    }
    return EditorResult(
        "verified-coordinator-required",
        "promote-preflight",
        str(operation["id"]),
        str(operation["kind"]),
        tuple(dict(change) for change in manifest["changes"]),
        candidate_evidence,
        {
            "requested": True,
            "performed": False,
            "atomicity": "coordinator-required",
            "promoted_paths": [],
        },
        (finding,),
        (
            f"legacy-task-editor verified {operation['kind']} for {subject['task_id']}",
            "authoritative publication requires Task 0038-05.02 coordinator",
        ),
    )


def _load_sources(root: Path, operation: Operation) -> Dict[str, bytes]:
    paths: Set[str] = {str(operation.data["backlog"]["path"])}  # type: ignore[index]
    claim = operation.data.get("claim")
    if isinstance(claim, dict):
        paths.add(str(claim["path"]))
    for candidate in root.glob("TODO-*.md"):
        paths.add(candidate.name)
    sources: Dict[str, bytes] = {}
    for relative in sorted(paths):
        path = _safe_target(root, relative, allow_absent_final=True)
        if not path.exists():
            continue
        sources[relative] = _read_regular_nofollow(path)
    return sources


def _error_result(error: EditorError, operation_id: str = "unknown", kind: str = "unknown") -> Dict[str, object]:
    return EditorResult(
        "rejected",
        error.phase,
        operation_id,
        kind,
        (),
        None,
        {"requested": False, "performed": False, "atomicity": "none", "promoted_paths": []},
        (error.finding(),),
        (f"legacy-task-editor rejected {error.rule}: {error.message}",),
    ).to_dict()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan_parser = subparsers.add_parser("plan", help="validate and write a review candidate")
    plan_parser.add_argument("--operation", type=Path, required=True)
    plan_parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    plan_parser.add_argument("--candidate-dir", type=Path, required=True)
    plan_parser.add_argument("--json", action="store_true")
    promote_parser = subparsers.add_parser("promote", help="verify promotion preflight and return coordinator handoff evidence")
    promote_parser.add_argument("--candidate-manifest", type=Path, required=True)
    promote_parser.add_argument("--expect-candidate-sha256", required=True)
    promote_parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    promote_parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    operation_id = "unknown"
    kind = "unknown"
    try:
        if args.command == "plan":
            raw = _read_regular_nofollow(args.operation)
            operation = load_operation(raw)
            operation_id = str(operation.data["operation_id"])
            kind = str(operation.data["kind"])
            root = args.root.resolve()
            sources = _load_sources(root, operation)
            before = {path: _sha256(value) for path, value in sources.items()}
            plan = plan_operation(operation, sources)
            after_sources = _load_sources(root, operation)
            after = {path: _sha256(value) for path, value in after_sources.items()}
            if before != after:
                raise EditorError("LTE-INPUT-CHANGED", "source set changed during planning", "input", EXIT_INPUT)
            receipt = write_candidate(plan, args.candidate_dir)
            result = EditorResult(
                "planned",
                "candidate",
                operation_id,
                kind,
                tuple(change.to_manifest(args.candidate_dir) for change in plan.changes),
                asdict(receipt),
                {"requested": False, "performed": False, "atomicity": "none", "promoted_paths": []},
                (),
                plan.summary,
            ).to_dict()
        else:
            if not SHA256_RE.fullmatch(args.expect_candidate_sha256):
                raise EditorError("LTE-CANDIDATE-TAMPERED", "expected candidate digest is invalid", "candidate", EXIT_CANDIDATE)
            result = promote_candidate(args.root.resolve(), args.candidate_manifest, args.expect_candidate_sha256).to_dict()
        if args.json:
            sys.stdout.buffer.write(_json_bytes(result))
        else:
            for line in result["summary"]:
                print(line)
        return (
            EXIT_PROMOTE
            if result["verdict"] == "verified-coordinator-required"
            else 0
        )
    except EditorError as exc:
        result = _error_result(exc, operation_id, kind)
        if getattr(args, "json", False):
            sys.stdout.buffer.write(_json_bytes(result))
        else:
            for line in result["summary"]:
                print(line)
        return exc.exit_code
    except Exception as exc:
        error = EditorError("LTE-INTERNAL", f"{exc.__class__.__name__}: {' '.join(str(exc).split())}", "internal", EXIT_INTERNAL)
        result = _error_result(error, operation_id, kind)
        if getattr(args, "json", False):
            sys.stdout.buffer.write(_json_bytes(result))
        else:
            for line in result["summary"]:
                print(line)
        return EXIT_INTERNAL


if __name__ == "__main__":
    raise SystemExit(main())
