#!/usr/bin/env python3
"""Read-only diagnostics for the authoritative legacy Task/claim bootstrap.

The legacy lists remain authoritative until Feature 0037 performs its reviewed
cutover.  This tool normalizes their current worktree bytes, reports drift with
stable rule IDs, and emits advisory exact-path reconciliation plans.  It never
edits a file, stages work, changes a ref, takes over a claim, or inspects the
root runner request slot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple


REPORT_SCHEMA = "legacy-task-doctor-report@v1"
VALID_MARKERS = {" ", "u", "p", "?", "w", "x"}
TERMINAL_MARKERS = {"w", "x"}
TASK_ID_RE = re.compile(r"^[0-9]{4}-[0-9]{2}(?:\.[0-9]{2})?$")
FEATURE_ID_RE = re.compile(r"^[0-9]{4}$")
FULL_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHORT_COMMIT_RE = re.compile(r"^[0-9a-f]{7,39}$")
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{5,127}$")
OWNER_TOKEN_RE = re.compile(
    r"^agent:(?P<agent>[A-Za-z0-9._-]+):"
    r"(?P<task>[0-9]{4}-[0-9]{2}(?:\.[0-9]{2})?):"
    r"(?P<claim>[A-Za-z0-9][A-Za-z0-9._-]{5,127})$"
)
TASK_HEADER_RE = re.compile(
    r"^- \[(?P<marker>[^]]*)\] \*\*(?P<id>[0-9]{4}-[0-9]{2}(?:\.[0-9]{2})?)\*\*(?P<tail>.*)$"
)
LEGACY_TASK_RE = re.compile(r"^- \[(?P<marker>[^]]*)\](?P<tail>.*)$")
FEATURE_HEADER_RE = re.compile(
    r"^## Feature:\s*(?:(?P<id>[0-9]{4})\s+[—-]\s+)?(?P<title>.+?)\s*$"
)
PREREQ_PAIR_RE = re.compile(
    r"(?P<left>[0-9]{4}(?:-[0-9]{2}(?:\.[0-9]{2})?)?):"
    r"(?P<right>[0-9]{4}(?:-[0-9]{2}(?:\.[0-9]{2})?)?)"
)
REF_RE = re.compile(
    r"\bREF:\s*(?:`(?P<quoted>[^`\n]+)`|(?P<pending>pending\s+commit)|(?P<plain>[^\s<]+))?",
    re.IGNORECASE,
)
PLAIN_FIELD_RE = re.compile(r"^(?P<key>[a-z][a-z0-9_]*):\s*(?P<value>.+?)\s*$")
LEGACY_FIELD_RE = re.compile(
    r"^\s*-\s*(?:`(?P<backtick>[a-z][a-z0-9_]*)`|(?P<plain>[a-z][a-z0-9_]*))"
    r":\s*(?P<value>.+?)\s*$"
)
MARKDOWN_LINK_RE = re.compile(r"\[[^]]*\]\((?P<target>[^)]+)\)")
BACKTICK_MD_RE = re.compile(r"`(?P<target>(?:\.\./|[A-Za-z0-9_])[A-Za-z0-9_./-]*\.md)`")
PATH_TOKEN_RE = re.compile(r"`(?P<path>[^`\n]+)`")
SEVERITY_RANK = {"error": 0, "warning": 1, "info": 2}
MAX_INPUT_BYTES = 12 * 1024 * 1024
REQUIRED_WORKFLOW_KEYS = {
    "schema",
    "workflow_version",
    "authority_epoch",
    "authority_profile",
    "write_phase",
    "required_capability",
    "runner_protocol",
    "selector_digest",
    "instruction_bundle",
}
WORKFLOW_ENUMS = {
    "authority_epoch": {
        "legacy-writable",
        "legacy-frozen",
        "issue-store-writable",
        "issue-store-write-frozen",
        "legacy-restored",
    },
    "authority_profile": {"legacy-lists", "issue-store"},
    "write_phase": {
        "legacy-writable",
        "frozen",
        "issue-store-writable",
        "write-frozen",
        "legacy-restored",
    },
    "required_capability": {"sandboxed-grunt", "privileged"},
}
RULE_SEVERITY = {
    "LTD-INPUT-CHANGED": "error",
    "LTD-INPUT-MISSING": "error",
    "LTD-INPUT-NONREGULAR": "error",
    "LTD-MARKER-UNDEFINED": "error",
    "LTD-ID-DUPLICATE": "error",
    "LTD-TASK-HEADER-MALFORMED": "error",
    "LTD-FEATURE-HEADER-MALFORMED": "error",
    "LTD-REF-HIDDEN": "error",
    "LTD-REF-MALFORMED": "error",
    "LTD-REF-PLACEHOLDER": "error",
    "LTD-REF-MISSING": "error",
    "LTD-REF-DUPLICATE": "warning",
    "LTD-REF-UNREACHABLE": "error",
    "LTD-REF-STATE-DIVERGED": "error",
    "LTD-CLAIM-FIELDS-MISSING": "error",
    "LTD-CLAIM-EXECUTION-AUTHORITY-INVALID": "error",
    "LTD-CLAIM-STARTUP-REVIEW-INVALID": "error",
    "LTD-CLAIM-FIELD-DUPLICATE": "error",
    "LTD-CLAIM-FIELD-NONCANONICAL": "warning",
    "LTD-CLAIM-STATE-DIVERGED": "error",
    "LTD-CLAIM-TASK-MISSING": "error",
    "LTD-CLAIM-TERMINAL-RETAINED": "error",
    "LTD-CLAIM-IDENTITY-MISMATCH": "error",
    "LTD-CLAIM-BASE-ABBREVIATED": "warning",
    "LTD-CLAIM-BASE-INVALID": "error",
    "LTD-CLAIM-BASE-UNREACHABLE": "error",
    "LTD-CLAIM-SCOPE-MISSING": "error",
    "LTD-CLAIM-SCOPE-MISMATCH": "error",
    "LTD-CLAIM-SCOPE-INVALID": "error",
    "LTD-CLAIM-NEXT-STEP-MISSING": "error",
    "LTD-TASK-CLAIM-MISSING": "error",
    "LTD-TASK-CLAIM-DUPLICATE": "error",
    "LTD-TASK-CLAIM-POINTER-MISMATCH": "error",
    "LTD-PREREQ-MALFORMED": "error",
    "LTD-PREREQ-LHS": "error",
    "LTD-PREREQ-ENDPOINT-MISSING": "error",
    "LTD-PREREQ-DUPLICATE": "warning",
    "LTD-PREREQ-SELF": "error",
    "LTD-PREREQ-CYCLE": "error",
    "LTD-TERMINAL-UNSATISFIED-PREREQ": "error",
    "LTD-PARENT-CLOSURE-ELIGIBLE": "warning",
    "LTD-FEATURE-CLOSURE-ELIGIBLE": "warning",
    "LTD-BOOT-INVALID": "error",
    "LTD-BOOT-UNKNOWN-FIELD": "error",
    "LTD-BOOT-CROSS-FIELD": "error",
    "LTD-BOOT-DIGEST-PLACEHOLDER": "warning",
    "LTD-BOOT-BUNDLE-MISSING": "error",
    "LTD-BOOT-COMMAND-MISSING": "error",
    "LTD-INSTRUCTION-LINK-MISSING": "error",
    "LTD-INSTRUCTION-NEAR-NAME": "error",
    "LTD-POLICY-CONTRADICTION": "error",
    "LTD-GIT-PROBE": "error",
}


class DoctorInputError(RuntimeError):
    """An input could not be read safely or consistently."""

    def __init__(self, rule: str, path: str, message: str) -> None:
        super().__init__(message)
        self.rule = rule
        self.path = path
        self.message = message


@dataclass(frozen=True)
class InputBlob:
    path: str
    raw: bytes
    text: str
    lines: Tuple[str, ...]
    sha256: str
    size: int

    def inventory(self) -> Dict[str, object]:
        return {"path": self.path, "bytes": self.size, "sha256": self.sha256}


@dataclass(frozen=True)
class FeatureRecord:
    id: Optional[str]
    title: str
    path: str
    line: int
    end_line: int
    archived_not_accepted: bool
    prerequisites: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RefRecord:
    path: str
    line: int
    column: int
    subject_kind: str
    subject_id: str
    value: str
    visibility: str
    role: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PrerequisiteEdge:
    dependent: str
    prerequisite: str
    path: str
    line: int

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TaskRecord:
    id: str
    marker: str
    feature_id: Optional[str]
    path: str
    line: int
    end_line: int
    title: str
    archived_not_accepted: bool
    prerequisites: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class LegacyEntry:
    marker: str
    feature_id: Optional[str]
    path: str
    line: int
    text: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FieldOccurrence:
    key: str
    value: str
    line: int
    canonical: bool


@dataclass(frozen=True)
class ClaimRecord:
    path: str
    sha256: str
    task_id: Optional[str]
    request_id: Optional[str]
    owner_token: Optional[str]
    base_commit: Optional[str]
    capability_class: Optional[str]
    execution_authority: Optional[str]
    startup_review: Optional[str]
    state: Optional[str]
    scopes: Tuple[str, ...]
    next_step_present: bool
    field_lines: Mapping[str, Tuple[int, ...]]

    def to_dict(self) -> Dict[str, object]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "task_id": self.task_id,
            "request_id": self.request_id,
            "owner_token": self.owner_token,
            "base_commit": self.base_commit,
            "capability_class": self.capability_class,
            "execution_authority": self.execution_authority,
            "startup_review": self.startup_review,
            "state": self.state,
            "scopes": list(self.scopes),
            "next_step_present": self.next_step_present,
            "field_lines": {key: list(value) for key, value in sorted(self.field_lines.items())},
        }


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    category: str
    path: str
    line: int
    subject: str
    message: str
    evidence: str
    evidence_sha256: str
    related_paths: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, object]:
        value = asdict(self)
        value["related_paths"] = list(self.related_paths)
        return value


@dataclass(frozen=True)
class ReconciliationPlan:
    rule: str
    path: str
    line: int
    subject: str
    action: str
    required_actor: str
    target_paths: Tuple[str, ...]
    expected_document_sha256: Optional[str]
    automatic: bool = False
    destructive: bool = False

    def to_dict(self) -> Dict[str, object]:
        value = asdict(self)
        value["target_paths"] = list(self.target_paths)
        return value


@dataclass
class ParsedRepository:
    features: List[FeatureRecord] = field(default_factory=list)
    tasks: List[TaskRecord] = field(default_factory=list)
    legacy_entries: List[LegacyEntry] = field(default_factory=list)
    refs: List[RefRecord] = field(default_factory=list)
    edges: List[PrerequisiteEdge] = field(default_factory=list)
    claims: List[ClaimRecord] = field(default_factory=list)
    workflow: Dict[str, object] = field(default_factory=dict)
    findings: List[Finding] = field(default_factory=list)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_json(value: Mapping[str, object]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


class DuplicateJsonKeyError(ValueError):
    pass


def _json_loads_unique(text: str) -> object:
    def pairs_hook(pairs: Sequence[Tuple[str, object]]) -> Dict[str, object]:
        result: Dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise DuplicateJsonKeyError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(text, object_pairs_hook=pairs_hook)


def _exception_detail(exc: BaseException) -> str:
    if isinstance(exc, OSError):
        return exc.strerror or exc.__class__.__name__
    if isinstance(exc, UnicodeError):
        return exc.__class__.__name__
    return " ".join(str(exc).split()) or exc.__class__.__name__


def _safe_relative_path(value: str) -> bool:
    if not value or "\\" in value or "\x00" in value:
        return False
    pure = PurePosixPath(value)
    return not pure.is_absolute() and ".." not in pure.parts


def _read_blob(root: Path, relative: str) -> InputBlob:
    if not _safe_relative_path(relative):
        raise DoctorInputError("LTD-INPUT-NONREGULAR", relative, "input path is not a safe repository-relative path")
    path = root / relative
    try:
        info = path.lstat()
    except OSError as exc:
        raise DoctorInputError(
            "LTD-INPUT-MISSING",
            relative,
            f"cannot stat required input: {_exception_detail(exc)}",
        ) from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise DoctorInputError("LTD-INPUT-NONREGULAR", relative, "input must be a regular non-symlink file")
    if info.st_size > MAX_INPUT_BYTES:
        raise DoctorInputError("LTD-INPUT-NONREGULAR", relative, f"input exceeds {MAX_INPUT_BYTES} bytes")
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise DoctorInputError(
            "LTD-INPUT-NONREGULAR",
            relative,
            f"cannot read UTF-8 input: {_exception_detail(exc)}",
        ) from exc
    return InputBlob(
        path=relative,
        raw=raw,
        text=text,
        lines=tuple(text.splitlines()),
        sha256=_sha256(raw),
        size=len(raw),
    )


def _claim_names(root: Path) -> List[str]:
    try:
        names = [
            entry.name
            for entry in os.scandir(root)
            if entry.name.startswith("TODO-") and entry.name.endswith(".md")
        ]
    except OSError as exc:
        raise DoctorInputError(
            "LTD-INPUT-MISSING",
            ".",
            f"cannot enumerate top-level claims: {_exception_detail(exc)}",
        ) from exc
    return sorted(names)


def _discover_inputs(root: Path) -> Tuple[Dict[str, InputBlob], List[str]]:
    required = ["TODO.md", "DONE.md", "agent-workflow.json", "AGENTS.md", "SANDBOX.md", "PRIVILEGED.md"]
    claim_names = _claim_names(root)
    blobs: Dict[str, InputBlob] = {}
    for relative in required + claim_names:
        blobs[relative] = _read_blob(root, relative)

    workflow_bundle: Optional[str] = None
    try:
        decoded = _json_loads_unique(blobs["agent-workflow.json"].text)
        if isinstance(decoded, dict):
            candidate = decoded.get("instruction_bundle")
            if isinstance(candidate, str) and _safe_relative_path(candidate):
                workflow_bundle = candidate
    except (json.JSONDecodeError, DuplicateJsonKeyError):
        pass
    if workflow_bundle and re.fullmatch(
        r"docs/pipeline/agent-instructions/(legacy|current|future)/index\.md",
        workflow_bundle,
    ) and workflow_bundle not in blobs:
        bundle_path = root / workflow_bundle
        try:
            bundle_path.lstat()
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise DoctorInputError(
                "LTD-INPUT-NONREGULAR",
                workflow_bundle,
                f"cannot stat selected instruction bundle: {_exception_detail(exc)}",
            ) from exc
        else:
            blobs[workflow_bundle] = _read_blob(root, workflow_bundle)

    sentinel = root / "SENTINEL.md"
    try:
        sentinel_info = sentinel.lstat()
    except FileNotFoundError:
        sentinel_info = None
    except OSError as exc:
        raise DoctorInputError(
            "LTD-INPUT-NONREGULAR",
            "SENTINEL.md",
            f"cannot stat policy file: {_exception_detail(exc)}",
        ) from exc
    if sentinel_info is not None:
        blobs["SENTINEL.md"] = _read_blob(root, "SENTINEL.md")
    return blobs, claim_names


def _verify_inputs(root: Path, blobs: Mapping[str, InputBlob], claim_names: Sequence[str]) -> List[str]:
    changed: List[str] = []
    try:
        if _claim_names(root) != list(claim_names):
            changed.append("TODO-*.md")
    except DoctorInputError:
        changed.append("TODO-*.md")
    for relative, before in sorted(blobs.items()):
        try:
            after = _read_blob(root, relative)
        except DoctorInputError:
            changed.append(relative)
            continue
        if (after.sha256, after.size) != (before.sha256, before.size):
            changed.append(relative)
    return sorted(set(changed))


def _line_evidence(blob: Optional[InputBlob], line: int, fallback: str = "") -> Tuple[str, str]:
    if blob is not None and 1 <= line <= len(blob.lines):
        evidence = blob.lines[line - 1]
    else:
        evidence = fallback
    return evidence, _sha256(evidence.encode("utf-8"))


def _make_finding(
    rule: str,
    category: str,
    path: str,
    line: int,
    subject: str,
    message: str,
    blobs: Mapping[str, InputBlob],
    *,
    evidence: Optional[str] = None,
    related_paths: Iterable[str] = (),
    severity: Optional[str] = None,
) -> Finding:
    source, digest = _line_evidence(blobs.get(path), line, evidence or "")
    if evidence is not None:
        source = evidence
        digest = _sha256(evidence.encode("utf-8"))
    return Finding(
        rule=rule,
        severity=severity or RULE_SEVERITY[rule],
        category=category,
        path=path,
        line=max(1, line),
        subject=subject,
        message=message,
        evidence=source,
        evidence_sha256=digest,
        related_paths=tuple(sorted(set(related_paths))),
    )


def _strip_ref_value(value: str) -> str:
    return value.strip().rstrip(".,;:)")


def _html_comment_spans(blob: InputBlob) -> Dict[int, Tuple[Tuple[int, int], ...]]:
    spans_by_line: Dict[int, Tuple[Tuple[int, int], ...]] = {}
    in_comment = False
    for line_number, line in enumerate(blob.lines, 1):
        spans: List[Tuple[int, int]] = []
        position = 0
        while position <= len(line):
            if in_comment:
                end = line.find("-->", position)
                if end < 0:
                    spans.append((position, len(line)))
                    break
                spans.append((position, end + 3))
                in_comment = False
                position = end + 3
                continue
            start = line.find("<!--", position)
            if start < 0:
                break
            end = line.find("-->", start + 4)
            if end < 0:
                spans.append((start, len(line)))
                in_comment = True
                break
            spans.append((start, end + 3))
            position = end + 3
        spans_by_line[line_number] = tuple(spans)
    return spans_by_line


def _refs_in_line(
    blob: InputBlob,
    line_number: int,
    subject_kind: str,
    subject_id: str,
    role: str,
    hidden_spans: Sequence[Tuple[int, int]],
) -> List[RefRecord]:
    line = blob.lines[line_number - 1]
    refs: List[RefRecord] = []
    for match in REF_RE.finditer(line):
        raw_value = match.group("quoted") or match.group("pending") or match.group("plain") or ""
        visibility = (
            "hidden"
            if any(start <= match.start() < end for start, end in hidden_spans)
            else "visible"
        )
        refs.append(
            RefRecord(
                path=blob.path,
                line=line_number,
                column=match.start() + 1,
                subject_kind=subject_kind,
                subject_id=subject_id,
                value=_strip_ref_value(raw_value),
                visibility=visibility,
                role=role,
            )
        )
    return refs


def _parse_prerequisite_declaration(
    line: str,
    *,
    allow_trailing_text: bool,
) -> Tuple[List[Tuple[str, str]], List[str]]:
    if "PREREQ:" not in line:
        return [], []
    segment = line.split("PREREQ:", 1)[1].lstrip()
    if segment.startswith("**"):
        segment = segment[2:].lstrip()
    position = 0
    pairs: List[Tuple[str, str]] = []
    errors: List[str] = []

    def skip_space(index: int) -> int:
        while index < len(segment) and segment[index].isspace():
            index += 1
        return index

    position = skip_space(position)
    while True:
        match = PREREQ_PAIR_RE.match(segment, position)
        if match is None:
            if not pairs:
                errors.append("PREREQ marker has no complete dependent:prerequisite relation")
            else:
                errors.append("comma-separated prerequisite list has malformed trailing content")
            break
        pairs.append((match.group("left"), match.group("right")))
        position = skip_space(match.end())
        if position >= len(segment):
            break
        if segment[position] == ",":
            position = skip_space(position + 1)
            if position >= len(segment) or PREREQ_PAIR_RE.match(segment, position) is None:
                errors.append("comma-separated prerequisite list has malformed trailing content")
                break
            continue
        if allow_trailing_text:
            if PREREQ_PAIR_RE.match(segment, position) is not None:
                errors.append("adjacent prerequisite relations must be comma-separated")
                continue
            break
        errors.append("Feature prerequisite line contains trailing non-relation text")
        break
    return pairs, errors


def _feature_ranges(blob: InputBlob) -> List[Tuple[int, int, re.Match[str]]]:
    starts: List[Tuple[int, re.Match[str]]] = []
    for index, line in enumerate(blob.lines, 1):
        match = FEATURE_HEADER_RE.match(line)
        if match:
            starts.append((index, match))
    ranges: List[Tuple[int, int, re.Match[str]]] = []
    for offset, (start, match) in enumerate(starts):
        end = starts[offset + 1][0] - 1 if offset + 1 < len(starts) else len(blob.lines)
        ranges.append((start, end, match))
    return ranges


def _parse_backlog(blob: InputBlob) -> Tuple[List[FeatureRecord], List[TaskRecord], List[LegacyEntry], List[RefRecord], List[PrerequisiteEdge]]:
    features: List[FeatureRecord] = []
    tasks: List[TaskRecord] = []
    legacy_entries: List[LegacyEntry] = []
    refs: List[RefRecord] = []
    edges: List[PrerequisiteEdge] = []
    comment_spans = _html_comment_spans(blob)

    ranges = _feature_ranges(blob)
    feature_for_line: Dict[int, FeatureRecord] = {}
    for start, end, match in ranges:
        feature_id = match.group("id")
        preceding = "\n".join(blob.lines[max(0, start - 5): start - 1])
        archived = (
            "ARCHIVED — NOT ACCEPTED" in preceding
            or "historical implementation archive" in match.group("title").lower()
        )
        prereqs: List[str] = []
        for line_number in range(start, end + 1):
            line = blob.lines[line_number - 1]
            if line_number > start and FEATURE_HEADER_RE.match(line):
                break
            if line.startswith("- ["):
                break
            if "PREREQ:" not in line:
                continue
            pairs, _errors = _parse_prerequisite_declaration(
                line,
                allow_trailing_text=False,
            )
            for left, right in pairs:
                if feature_id and left == feature_id:
                    prereqs.append(right)
                edges.append(PrerequisiteEdge(left, right, blob.path, line_number))
        record = FeatureRecord(
            id=feature_id,
            title=match.group("title"),
            path=blob.path,
            line=start,
            end_line=end,
            archived_not_accepted=archived,
            prerequisites=tuple(prereqs),
        )
        features.append(record)
        for line_number in range(start, end + 1):
            feature_for_line[line_number] = record
        for line_number in range(start, end + 1):
            line = blob.lines[line_number - 1]
            if line.startswith("Completed:") and "REF:" in line:
                subject = feature_id or f"legacy-feature@{start}"
                refs.extend(
                    _refs_in_line(
                        blob,
                        line_number,
                        "feature",
                        subject,
                        "authoritative-feature",
                        comment_spans.get(line_number, ()),
                    )
                )

    task_starts: List[Tuple[int, re.Match[str]]] = []
    for line_number, line in enumerate(blob.lines, 1):
        task_match = TASK_HEADER_RE.match(line)
        if task_match:
            task_starts.append((line_number, task_match))
        elif LEGACY_TASK_RE.match(line):
            legacy_match = LEGACY_TASK_RE.match(line)
            assert legacy_match is not None
            feature = feature_for_line.get(line_number)
            legacy_entries.append(
                LegacyEntry(
                    marker=legacy_match.group("marker"),
                    feature_id=feature.id if feature else None,
                    path=blob.path,
                    line=line_number,
                    text=legacy_match.group("tail").strip(),
                )
            )

    for offset, (start, match) in enumerate(task_starts):
        next_task = task_starts[offset + 1][0] if offset + 1 < len(task_starts) else len(blob.lines) + 1
        feature = feature_for_line.get(start)
        feature_end = feature.end_line + 1 if feature else len(blob.lines) + 1
        end = min(next_task, feature_end) - 1
        task_id = match.group("id")
        marker = match.group("marker")
        title = match.group("tail").strip()
        prereqs: List[str] = []
        if "PREREQ:" in title:
            pairs, _errors = _parse_prerequisite_declaration(
                title,
                allow_trailing_text=True,
            )
            for left, right in pairs:
                if left == task_id:
                    prereqs.append(right)
                edges.append(PrerequisiteEdge(left, right, blob.path, start))
        task = TaskRecord(
            id=task_id,
            marker=marker,
            feature_id=feature.id if feature else None,
            path=blob.path,
            line=start,
            end_line=end,
            title=title,
            archived_not_accepted=feature.archived_not_accepted if feature else False,
            prerequisites=tuple(prereqs),
        )
        tasks.append(task)
        for line_number in range(start, end + 1):
            line = blob.lines[line_number - 1]
            role = "narrative"
            if line_number == start or re.match(r"^\s{2}-\s+REF:\s*", line):
                role = "authoritative-task"
            refs.extend(
                _refs_in_line(
                    blob,
                    line_number,
                    "task",
                    task_id,
                    role,
                    comment_spans.get(line_number, ()),
                )
            )

    task_lines = {
        line_number
        for task in tasks
        for line_number in range(task.line, task.end_line + 1)
    }
    for feature in features:
        subject = feature.id or f"legacy-feature@{feature.line}"
        for line_number in range(feature.line, feature.end_line + 1):
            if line_number in task_lines:
                continue
            line = blob.lines[line_number - 1]
            if "REF:" not in line or line.startswith("Completed:"):
                continue
            refs.extend(
                _refs_in_line(
                    blob,
                    line_number,
                    "feature",
                    subject,
                    "narrative",
                    comment_spans.get(line_number, ()),
                )
            )

    return features, tasks, legacy_entries, refs, edges


def _normalize_field_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        return value[1:-1]
    return value


def _claim_occurrences(blob: InputBlob) -> List[FieldOccurrence]:
    identity_heading = next(
        (
            index
            for index, line in enumerate(blob.lines)
            if re.fullmatch(r"##\s+Claim identity\s*", line, re.IGNORECASE)
        ),
        None,
    )
    start = identity_heading + 1 if identity_heading is not None else 0
    end = len(blob.lines)
    for index in range(start, len(blob.lines)):
        if blob.lines[index].startswith("## "):
            end = index
            break

    result: List[FieldOccurrence] = []
    for index in range(start, end):
        line_number = index + 1
        line = blob.lines[index]
        match = PLAIN_FIELD_RE.match(line)
        if match:
            result.append(FieldOccurrence(match.group("key"), _normalize_field_value(match.group("value")), line_number, True))
            continue
        match = LEGACY_FIELD_RE.match(line)
        if match:
            key = match.group("backtick") or match.group("plain")
            result.append(FieldOccurrence(key, _normalize_field_value(match.group("value")), line_number, False))
    return result


def _claim_scopes(blob: InputBlob) -> Tuple[str, ...]:
    in_scope = False
    values: Set[str] = set()
    for line in blob.lines:
        if line.startswith("## "):
            heading = line.lower()
            in_scope = (
                "write scope" in heading
                or "intended scope" in heading
                or "task scope" in heading
            ) and "runner scope" not in heading and "execution scope" not in heading
            continue
        if "intended write scope" in line.lower() or "write scope" in line.lower():
            in_scope = True
        if not in_scope:
            continue
        for match in PATH_TOKEN_RE.finditer(line):
            token = match.group("path").strip()
            if "/" in token or token.endswith((".md", ".py", ".json", ".sh")) or token.startswith("TODO"):
                values.add(token)
    return tuple(sorted(values))


def _valid_claim_scope(value: str) -> bool:
    if not _safe_relative_path(value):
        return False
    if any(character in value for character in "*?["):
        return False
    parts = PurePosixPath(value).parts
    return bool(parts) and parts[0] != ".git" and value != "run.sh"


def _claim_next_step(blob: InputBlob) -> bool:
    headings = [
        index
        for index, line in enumerate(blob.lines)
        if re.match(r"^#{2,6}\s+", line)
    ]
    starts = [
        index
        for index, line in enumerate(blob.lines)
        if re.match(r"^##\s+Next step\b", line, re.IGNORECASE)
    ]
    if not starts or (headings and starts[-1] != headings[-1]):
        return False
    content = [line.strip() for line in blob.lines[starts[-1] + 1:]]
    meaningful = [
        re.sub(r"^[-*+]\s+", "", line).strip()
        for line in content
        if line
        and not line.startswith(("<!--", "-->", "```", "~~~"))
    ]
    placeholders = {"tbd", "todo", "pending", "none", "n/a", "unknown", "not set"}
    return any(line.lower().rstrip(".") not in placeholders for line in meaningful)


def _parse_claim(blob: InputBlob) -> Tuple[ClaimRecord, List[FieldOccurrence]]:
    occurrences = _claim_occurrences(blob)
    grouped: Dict[str, List[FieldOccurrence]] = {}
    for occurrence in occurrences:
        grouped.setdefault(occurrence.key, []).append(occurrence)

    def one(key: str) -> Optional[str]:
        values = grouped.get(key, [])
        return values[0].value if values else None

    owner = one("owner_token")
    owner_match = OWNER_TOKEN_RE.fullmatch(owner or "")
    task_id = one("task_id")
    if task_id is None and owner_match:
        task_id = owner_match.group("task")
    state = one("state")
    if state and state.startswith("[") and state.endswith("]"):
        state = state[1:-1]
    return (
        ClaimRecord(
            path=blob.path,
            sha256=blob.sha256,
            task_id=task_id,
            request_id=one("request_id"),
            owner_token=owner,
            base_commit=one("base_commit"),
            capability_class=one("capability_class"),
            execution_authority=one("execution_authority"),
            startup_review=one("startup_review"),
            state=state,
            scopes=_claim_scopes(blob),
            next_step_present=_claim_next_step(blob),
            field_lines={key: tuple(item.line for item in value) for key, value in grouped.items()},
        ),
        occurrences,
    )


def _parse_workflow(blob: InputBlob, blobs: Mapping[str, InputBlob]) -> Tuple[Dict[str, object], List[Finding]]:
    findings: List[Finding] = []
    try:
        value = _json_loads_unique(blob.text)
    except json.JSONDecodeError as exc:
        findings.append(
            _make_finding("LTD-BOOT-INVALID", "bootstrap", blob.path, exc.lineno, "agent-workflow", f"invalid JSON: {exc.msg}", blobs)
        )
        return {}, findings
    except DuplicateJsonKeyError as exc:
        findings.append(
            _make_finding("LTD-BOOT-INVALID", "bootstrap", blob.path, 1, "agent-workflow", str(exc), blobs)
        )
        return {}, findings
    if not isinstance(value, dict):
        findings.append(_make_finding("LTD-BOOT-INVALID", "bootstrap", blob.path, 1, "agent-workflow", "selector must be a JSON object", blobs))
        return {}, findings

    unknown = sorted(set(value) - REQUIRED_WORKFLOW_KEYS)
    missing = sorted(REQUIRED_WORKFLOW_KEYS - set(value))
    if missing:
        findings.append(
            _make_finding("LTD-BOOT-INVALID", "bootstrap", blob.path, 1, "agent-workflow", f"missing required fields: {', '.join(missing)}", blobs)
        )
    if unknown:
        findings.append(
            _make_finding("LTD-BOOT-UNKNOWN-FIELD", "bootstrap", blob.path, 1, "agent-workflow", f"unknown fields: {', '.join(unknown)}", blobs)
        )
    exact = {"schema": "agent-workflow-bootstrap@v1", "runner_protocol": "runner-request@v1"}
    for key, expected in exact.items():
        if value.get(key) != expected:
            findings.append(
                _make_finding("LTD-BOOT-INVALID", "bootstrap", blob.path, 1, key, f"{key} must equal {expected!r}", blobs)
            )
    workflow_version = value.get("workflow_version")
    if not isinstance(workflow_version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", workflow_version):
        findings.append(_make_finding("LTD-BOOT-INVALID", "bootstrap", blob.path, 1, "workflow_version", "workflow_version must be semantic numeric version", blobs))
    for key, allowed in WORKFLOW_ENUMS.items():
        if value.get(key) not in allowed:
            findings.append(_make_finding("LTD-BOOT-INVALID", "bootstrap", blob.path, 1, key, f"unsupported {key}: {value.get(key)!r}", blobs))
    digest = value.get("selector_digest")
    if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        findings.append(_make_finding("LTD-BOOT-INVALID", "bootstrap", blob.path, 1, "selector_digest", "selector_digest must be sha256 plus 64 lowercase hex characters", blobs))
    elif len(set(digest.split(":", 1)[1])) == 1:
        findings.append(_make_finding("LTD-BOOT-DIGEST-PLACEHOLDER", "bootstrap", blob.path, 1, "selector_digest", "selector digest is an obvious repeated-character placeholder; the digest preimage remains contract-owned", blobs))
    bundle = value.get("instruction_bundle")
    if not isinstance(bundle, str) or not re.fullmatch(r"docs/pipeline/agent-instructions/(legacy|current|future)/index\.md", bundle):
        findings.append(_make_finding("LTD-BOOT-INVALID", "bootstrap", blob.path, 1, "instruction_bundle", "instruction_bundle is outside the versioned bundle paths", blobs))
    elif bundle not in blobs:
        findings.append(_make_finding("LTD-BOOT-BUNDLE-MISSING", "bootstrap", blob.path, 1, "instruction_bundle", f"selected instruction bundle is missing: {bundle}", blobs, related_paths=(bundle,)))

    profile = value.get("authority_profile")
    epoch = value.get("authority_epoch")
    phase = value.get("write_phase")
    profile_epochs = {
        "legacy-lists": {"legacy-writable", "legacy-frozen", "legacy-restored"},
        "issue-store": {"issue-store-writable", "issue-store-write-frozen"},
    }
    if isinstance(profile, str) and profile in profile_epochs and epoch not in profile_epochs[profile]:
        findings.append(_make_finding("LTD-BOOT-CROSS-FIELD", "bootstrap", blob.path, 1, "authority", f"authority profile {profile!r} is incompatible with epoch {epoch!r}", blobs))
    expected_phase = {
        "legacy-writable": "legacy-writable",
        "legacy-frozen": "frozen",
        "legacy-restored": "legacy-restored",
        "issue-store-writable": "issue-store-writable",
        "issue-store-write-frozen": "write-frozen",
    }.get(epoch) if isinstance(epoch, str) else None
    if expected_phase and phase != expected_phase:
        findings.append(_make_finding("LTD-BOOT-CROSS-FIELD", "bootstrap", blob.path, 1, "write_phase", f"epoch {epoch!r} requires write_phase {expected_phase!r}, observed {phase!r}", blobs))
    return dict(value), findings


def _dedupe_findings(findings: Iterable[Finding]) -> List[Finding]:
    unique: Dict[Tuple[object, ...], Finding] = {}
    for item in findings:
        key = (item.rule, item.path, item.line, item.subject, item.message, item.evidence_sha256)
        unique[key] = item
    return sorted(
        unique.values(),
        key=lambda item: (
            SEVERITY_RANK.get(item.severity, 99),
            item.rule,
            item.path,
            item.line,
            item.subject,
            item.evidence_sha256,
        ),
    )


def _authoritative_refs(refs: Iterable[RefRecord]) -> List[RefRecord]:
    return [item for item in refs if item.visibility == "visible" and item.role.startswith("authoritative")]


def _ref_findings(parsed: ParsedRepository, blobs: Mapping[str, InputBlob], reachable: Set[str]) -> List[Finding]:
    findings: List[Finding] = []
    refs_by_subject: Dict[Tuple[str, str], List[RefRecord]] = {}
    for ref in parsed.refs:
        refs_by_subject.setdefault((ref.subject_kind, ref.subject_id), []).append(ref)
        if ref.visibility == "hidden":
            findings.append(_make_finding("LTD-REF-HIDDEN", "reference", ref.path, ref.line, ref.subject_id, "REF is hidden in an HTML comment and is not authoritative closure evidence", blobs))
            continue
        if not ref.role.startswith("authoritative"):
            continue
        lower = ref.value.lower()
        if not ref.value or lower == "verified" or lower == "pending commit" or lower.startswith("local-"):
            severity = "info" if any(task.id == ref.subject_id and task.archived_not_accepted for task in parsed.tasks) else None
            findings.append(_make_finding("LTD-REF-PLACEHOLDER", "reference", ref.path, ref.line, ref.subject_id, f"authoritative REF is a non-Git placeholder: {ref.value or '<empty>'}", blobs, severity=severity))
        elif not FULL_COMMIT_RE.fullmatch(ref.value):
            findings.append(_make_finding("LTD-REF-MALFORMED", "reference", ref.path, ref.line, ref.subject_id, f"authoritative REF must be a full lowercase 40-hex commit: {ref.value}", blobs))
        elif ref.value not in reachable:
            findings.append(_make_finding("LTD-REF-UNREACHABLE", "reference", ref.path, ref.line, ref.subject_id, f"full commit REF is not reachable from any local ref: {ref.value}", blobs))

    task_by_id = {task.id: task for task in parsed.tasks}
    feature_by_id = {feature.id: feature for feature in parsed.features if feature.id}
    for subject, subject_refs in sorted(refs_by_subject.items()):
        authoritative = _authoritative_refs(subject_refs)
        if len(authoritative) > 1:
            first = authoritative[0]
            findings.append(_make_finding("LTD-REF-DUPLICATE", "reference", first.path, first.line, subject[1], f"item has {len(authoritative)} visible authoritative REF occurrences", blobs))
        task = task_by_id.get(subject[1]) if subject[0] == "task" else None
        if task and task.marker not in TERMINAL_MARKERS and authoritative:
            first = authoritative[0]
            findings.append(_make_finding("LTD-REF-STATE-DIVERGED", "reference", first.path, first.line, task.id, f"nonterminal Task [{task.marker}] carries authoritative closure REF", blobs))

    for task in parsed.tasks:
        if task.marker in TERMINAL_MARKERS and not task.archived_not_accepted:
            visible = _authoritative_refs(refs_by_subject.get(("task", task.id), []))
            if not visible:
                findings.append(_make_finding("LTD-REF-MISSING", "reference", task.path, task.line, task.id, f"terminal Task [{task.marker}] has no visible authoritative REF", blobs))
    for feature_id, feature in sorted(feature_by_id.items()):
        if feature.path == "DONE.md" and not feature.archived_not_accepted:
            visible = _authoritative_refs(refs_by_subject.get(("feature", feature_id), []))
            if not visible:
                findings.append(_make_finding("LTD-REF-MISSING", "reference", feature.path, feature.line, feature_id, "completed Feature has no visible authoritative REF", blobs))
    return findings


def _task_claim_pointer(blob: InputBlob, task: TaskRecord) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    block = "\n".join(blob.lines[task.line - 1:task.end_line])
    path_match = re.search(r"via\s+`(?P<path>TODO-[^`]+\.md)`", block)
    token_match = re.search(r"owner_token:\s*(?P<value>agent:[A-Za-z0-9:._-]+)", block)
    base_match = re.search(r"(?:base|base_commit)\s+`?(?P<value>[0-9a-f]{7,40}|pending-discovery)`?", block)
    return (
        path_match.group("path") if path_match else None,
        token_match.group("value") if token_match else None,
        base_match.group("value") if base_match else None,
    )


def _claim_findings(parsed: ParsedRepository, blobs: Mapping[str, InputBlob], occurrences: Mapping[str, Sequence[FieldOccurrence]], reachable: Set[str]) -> List[Finding]:
    findings: List[Finding] = []
    tasks_by_id: Dict[str, List[TaskRecord]] = {}
    for task in parsed.tasks:
        tasks_by_id.setdefault(task.id, []).append(task)
    claims_by_task: Dict[str, List[ClaimRecord]] = {}
    for claim in parsed.claims:
        if claim.task_id:
            claims_by_task.setdefault(claim.task_id, []).append(claim)
        items = list(occurrences.get(claim.path, ()))
        grouped: Dict[str, List[FieldOccurrence]] = {}
        for item in items:
            grouped.setdefault(item.key, []).append(item)
        required = {"request_id", "owner_token", "base_commit", "capability_class", "state"}
        if claim.state == "p":
            required.update({"execution_authority", "startup_review"})
        if claim.task_id:
            required.add("task_id")
        missing = sorted(key for key in required if key not in grouped)
        if missing:
            findings.append(_make_finding("LTD-CLAIM-FIELDS-MISSING", "claim", claim.path, 1, claim.task_id or claim.path, f"claim lacks canonical identity fields: {', '.join(missing)}", blobs))
        for key, values in sorted(grouped.items()):
            if len(values) > 1 and key in required | {"feature_id"}:
                findings.append(_make_finding("LTD-CLAIM-FIELD-DUPLICATE", "claim", claim.path, values[1].line, claim.task_id or claim.path, f"claim field {key} occurs {len(values)} times", blobs))
            if key in required and any(not value.canonical for value in values):
                first = next(value for value in values if not value.canonical)
                findings.append(_make_finding("LTD-CLAIM-FIELD-NONCANONICAL", "claim", claim.path, first.line, claim.task_id or claim.path, f"identity field {key} uses legacy bullet/backtick syntax instead of plain key: value", blobs))

        owner_match = OWNER_TOKEN_RE.fullmatch(claim.owner_token or "")
        mismatches: List[str] = []
        if claim.task_id and not TASK_ID_RE.fullmatch(claim.task_id):
            mismatches.append(f"invalid task_id {claim.task_id!r}")
        if claim.request_id and not REQUEST_ID_RE.fullmatch(claim.request_id):
            mismatches.append(f"invalid request_id {claim.request_id!r}")
        if claim.owner_token and not owner_match:
            mismatches.append("owner_token does not match agent:<agent>:<task>:<claim-id>")
        if owner_match:
            if claim.task_id and owner_match.group("task") != claim.task_id:
                mismatches.append("owner_token Task differs from task_id")
            if claim.request_id and owner_match.group("claim") != claim.request_id:
                mismatches.append("request_id differs from immutable owner-token claim ID")
            expected_filename = (
                f"TODO-{owner_match.group('agent')}-"
                f"{owner_match.group('task')}-"
                f"{owner_match.group('claim')}.md"
            )
            if claim.path != expected_filename:
                mismatches.append(
                    f"filename must exactly match immutable identity {expected_filename}"
                )
        if claim.capability_class and claim.capability_class not in {
            "sandboxed/grunt",
            "sandboxed-grunt",
            "privileged",
        }:
            mismatches.append(f"unsupported capability_class {claim.capability_class!r}")
        if mismatches:
            line = claim.field_lines.get("owner_token", (1,))[0]
            findings.append(_make_finding("LTD-CLAIM-IDENTITY-MISMATCH", "claim", claim.path, line, claim.task_id or claim.path, "; ".join(mismatches), blobs))

        if claim.state == "p" and claim.capability_class:
            expected_authority = "runner-only" if claim.capability_class in {"sandboxed/grunt", "sandboxed-grunt"} else "direct" if claim.capability_class == "privileged" else None
            if expected_authority and claim.execution_authority != expected_authority:
                findings.append(_make_finding("LTD-CLAIM-EXECUTION-AUTHORITY-INVALID", "claim", claim.path, claim.field_lines.get("execution_authority", (1,))[0], claim.task_id or claim.path, f"{claim.capability_class} claims require execution_authority {expected_authority!r}, observed {claim.execution_authority!r}", blobs))
            review = (claim.startup_review or "").lower()
            missing_reviews = [name for name in ("SANDBOX.md", "AGENTS.md") if name.lower() not in review]
            if missing_reviews:
                findings.append(_make_finding("LTD-CLAIM-STARTUP-REVIEW-INVALID", "claim", claim.path, claim.field_lines.get("startup_review", (1,))[0], claim.task_id or claim.path, "startup_review must record review of SANDBOX.md and AGENTS.md; missing " + ", ".join(missing_reviews), blobs))

        base = claim.base_commit
        if base:
            base_line = claim.field_lines.get("base_commit", (1,))[0]
            if base == "pending-discovery":
                pass
            elif SHORT_COMMIT_RE.fullmatch(base):
                findings.append(_make_finding("LTD-CLAIM-BASE-ABBREVIATED", "claim", claim.path, base_line, claim.task_id or claim.path, f"claim base is abbreviated rather than an exact commit: {base}", blobs))
            elif not FULL_COMMIT_RE.fullmatch(base):
                findings.append(_make_finding("LTD-CLAIM-BASE-INVALID", "claim", claim.path, base_line, claim.task_id or claim.path, f"claim base is neither pending-discovery nor a full commit: {base}", blobs))
            elif base not in reachable:
                findings.append(_make_finding("LTD-CLAIM-BASE-UNREACHABLE", "claim", claim.path, base_line, claim.task_id or claim.path, f"claim base is not reachable from any local ref: {base}", blobs))
        if claim.state is not None and claim.state not in VALID_MARKERS:
            line = claim.field_lines.get("state", (1,))[0]
            findings.append(_make_finding("LTD-MARKER-UNDEFINED", "claim", claim.path, line, claim.task_id or claim.path, f"claim uses undefined state [{claim.state}]", blobs))
        if claim.task_id and claim.task_id not in tasks_by_id:
            findings.append(
                _make_finding(
                    "LTD-CLAIM-TASK-MISSING",
                    "claim",
                    claim.path,
                    claim.field_lines.get("task_id", (1,))[0],
                    claim.task_id,
                    "claim declares a Task ID absent from TODO.md and DONE.md",
                    blobs,
                )
            )
        scope_fields = grouped.get("write_scope", []) + grouped.get("write_scopes", [])
        if scope_fields:
            declared_scopes: Set[str] = set()
            for scope_field in scope_fields:
                raw_scope = scope_field.value.strip()
                try:
                    decoded_scope = json.loads(raw_scope)
                except json.JSONDecodeError:
                    decoded_scope = None
                if isinstance(decoded_scope, list) and all(isinstance(item, str) for item in decoded_scope):
                    declared_scopes.update(decoded_scope)
                else:
                    declared_scopes.update(item.strip() for item in raw_scope.split(",") if item.strip())
            if declared_scopes != set(claim.scopes):
                findings.append(
                    _make_finding(
                        "LTD-CLAIM-SCOPE-MISMATCH",
                        "claim",
                        claim.path,
                        scope_fields[0].line,
                        claim.task_id or claim.path,
                        "machine write_scope field disagrees with the path-bearing Intended write scope section",
                        blobs,
                    )
                )
        scope_candidates = set(claim.scopes)
        if scope_fields:
            scope_candidates.update(declared_scopes)
        invalid_scopes = sorted(
            scope for scope in scope_candidates if not _valid_claim_scope(scope)
        )
        if invalid_scopes:
            findings.append(
                _make_finding(
                    "LTD-CLAIM-SCOPE-INVALID",
                    "claim",
                    claim.path,
                    scope_fields[0].line if scope_fields else 1,
                    claim.task_id or claim.path,
                    "claim scope must contain only exact, in-root, non-glob paths: "
                    + ", ".join(invalid_scopes),
                    blobs,
                )
            )
        if claim.state == "p" and not claim.scopes:
            findings.append(_make_finding("LTD-CLAIM-SCOPE-MISSING", "claim", claim.path, 1, claim.task_id or claim.path, "active claim has no exact path-bearing write-scope declaration", blobs))
        if claim.state == "p" and not claim.next_step_present:
            findings.append(_make_finding("LTD-CLAIM-NEXT-STEP-MISSING", "claim", claim.path, 1, claim.task_id or claim.path, "active claim has no nonempty final Next step section", blobs))

        if claim.task_id and claim.task_id in tasks_by_id:
            task = sorted(tasks_by_id[claim.task_id], key=lambda value: (value.path, value.line))[0]
            if claim.state is not None and claim.state != task.marker:
                line = claim.field_lines.get("state", (1,))[0]
                findings.append(_make_finding("LTD-CLAIM-STATE-DIVERGED", "claim", claim.path, line, claim.task_id, f"claim state [{claim.state}] disagrees with authoritative Task state [{task.marker}]", blobs, related_paths=(task.path,)))
            if task.marker in TERMINAL_MARKERS:
                findings.append(_make_finding("LTD-CLAIM-TERMINAL-RETAINED", "claim", claim.path, 1, claim.task_id, f"claim file remains after authoritative Task reached [{task.marker}]", blobs, related_paths=(task.path,)))

    for task_id, task_records in sorted(tasks_by_id.items()):
        task = sorted(task_records, key=lambda value: (value.path, value.line))[0]
        active = [claim for claim in claims_by_task.get(task_id, []) if claim.state == "p"]
        if task.marker == "p" and not active:
            findings.append(_make_finding("LTD-TASK-CLAIM-MISSING", "claim", task.path, task.line, task.id, "Task is [p] but no exact active claim resolves to it", blobs))
        if len(active) > 1:
            findings.append(_make_finding("LTD-TASK-CLAIM-DUPLICATE", "claim", task.path, task.line, task.id, f"Task has {len(active)} active claim files", blobs, related_paths=(claim.path for claim in active)))
        if task.marker == "p" and active:
            task_blob = blobs[task.path]
            pointer_path, pointer_token, pointer_base = _task_claim_pointer(task_blob, task)
            exact = active[0]
            differences: List[str] = []
            if pointer_path and pointer_path != exact.path:
                differences.append(f"Task note points to {pointer_path}, active claim is {exact.path}")
            if pointer_token and pointer_token != exact.owner_token:
                differences.append("Task note owner token differs from exact claim")
            if pointer_base and pointer_base != exact.base_commit:
                differences.append("Task note base differs from exact claim")
            if not pointer_path:
                differences.append("Task has no exact claim-path pointer")
            if differences:
                findings.append(_make_finding("LTD-TASK-CLAIM-POINTER-MISMATCH", "claim", task.path, task.line, task.id, "; ".join(differences), blobs, related_paths=(exact.path,)))
    return findings


def _terminal_id(identifier: str, task_markers: Mapping[str, str], done_features: Set[str]) -> bool:
    if "-" in identifier:
        return task_markers.get(identifier) in TERMINAL_MARKERS
    return identifier in done_features


def _canonical_cycle(nodes: Sequence[str]) -> Tuple[str, ...]:
    if not nodes:
        return ()
    body = list(nodes)
    if len(body) > 1 and body[0] == body[-1]:
        body.pop()
    minimum = min(range(len(body)), key=lambda index: body[index])
    rotated = body[minimum:] + body[:minimum]
    return tuple(rotated + [rotated[0]])


def _find_cycles(edges: Iterable[PrerequisiteEdge], known: Set[str]) -> List[Tuple[str, ...]]:
    graph: Dict[str, List[str]] = {node: [] for node in known}
    for edge in edges:
        if edge.dependent in known and edge.prerequisite in known:
            graph.setdefault(edge.dependent, []).append(edge.prerequisite)
    for node in graph:
        graph[node] = sorted(set(graph[node]))
    state: Dict[str, int] = {}
    stack: List[str] = []
    cycles: Set[Tuple[str, ...]] = set()

    def visit(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for neighbor in graph.get(node, []):
            if state.get(neighbor, 0) == 0:
                visit(neighbor)
            elif state.get(neighbor) == 1:
                start = stack.index(neighbor)
                cycles.add(_canonical_cycle(stack[start:] + [neighbor]))
        stack.pop()
        state[node] = 2

    for node in sorted(graph):
        if state.get(node, 0) == 0:
            visit(node)
    return sorted(cycles)


def _prerequisite_findings(parsed: ParsedRepository, blobs: Mapping[str, InputBlob]) -> List[Finding]:
    findings: List[Finding] = []
    tasks_by_id = {task.id: task for task in parsed.tasks}
    features_by_id = {feature.id: feature for feature in parsed.features if feature.id}
    known = set(tasks_by_id) | set(features_by_id)
    task_markers = {task.id: task.marker for task in parsed.tasks}
    done_features = {feature.id for feature in parsed.features if feature.id and feature.path == "DONE.md" and not feature.archived_not_accepted}

    for task in parsed.tasks:
        line = blobs[task.path].lines[task.line - 1]
        if "PREREQ:" in line:
            pairs, errors = _parse_prerequisite_declaration(
                line,
                allow_trailing_text=True,
            )
            for message in errors:
                findings.append(
                    _make_finding(
                        "LTD-PREREQ-MALFORMED",
                        "prerequisite",
                        task.path,
                        task.line,
                        task.id,
                        message,
                        blobs,
                    )
                )
            for left, _right in pairs:
                if left != task.id:
                    findings.append(
                        _make_finding(
                            "LTD-PREREQ-LHS",
                            "prerequisite",
                            task.path,
                            task.line,
                            task.id,
                            f"relation left side {left} does not match containing Task",
                            blobs,
                        )
                    )

    for feature in parsed.features:
        if not feature.id:
            continue
        source = blobs[feature.path]
        for line_number in range(feature.line, feature.end_line + 1):
            line = source.lines[line_number - 1]
            if line_number > feature.line and line.startswith("- ["):
                break
            if "PREREQ:" not in line:
                continue
            pairs, errors = _parse_prerequisite_declaration(
                line,
                allow_trailing_text=False,
            )
            for message in errors:
                findings.append(
                    _make_finding(
                        "LTD-PREREQ-MALFORMED",
                        "prerequisite",
                        feature.path,
                        line_number,
                        feature.id,
                        message,
                        blobs,
                    )
                )
            for left, _right in pairs:
                if left != feature.id:
                    findings.append(
                        _make_finding(
                            "LTD-PREREQ-LHS",
                            "prerequisite",
                            feature.path,
                            line_number,
                            feature.id,
                            f"relation left side {left} does not match containing Feature",
                            blobs,
                        )
                    )

    seen: Set[Tuple[str, str]] = set()
    for edge in sorted(parsed.edges, key=lambda value: (value.dependent, value.prerequisite, value.path, value.line)):
        if edge.dependent not in known:
            findings.append(_make_finding("LTD-PREREQ-ENDPOINT-MISSING", "prerequisite", edge.path, edge.line, edge.dependent, f"dependent endpoint does not exist: {edge.dependent}", blobs))
        if edge.prerequisite not in known:
            findings.append(_make_finding("LTD-PREREQ-ENDPOINT-MISSING", "prerequisite", edge.path, edge.line, edge.dependent, f"prerequisite endpoint does not exist: {edge.prerequisite}", blobs))
        if edge.dependent == edge.prerequisite:
            findings.append(_make_finding("LTD-PREREQ-SELF", "prerequisite", edge.path, edge.line, edge.dependent, "item depends on itself", blobs))
        key = (edge.dependent, edge.prerequisite)
        if key in seen:
            findings.append(_make_finding("LTD-PREREQ-DUPLICATE", "prerequisite", edge.path, edge.line, edge.dependent, f"duplicate prerequisite edge {edge.dependent}:{edge.prerequisite}", blobs))
        seen.add(key)
        if _terminal_id(edge.dependent, task_markers, done_features) and not _terminal_id(edge.prerequisite, task_markers, done_features):
            findings.append(_make_finding("LTD-TERMINAL-UNSATISFIED-PREREQ", "prerequisite", edge.path, edge.line, edge.dependent, f"terminal item depends on nonterminal prerequisite {edge.prerequisite}", blobs))

    edge_lookup: Dict[Tuple[str, str], PrerequisiteEdge] = {(edge.dependent, edge.prerequisite): edge for edge in parsed.edges}
    for cycle in _find_cycles(parsed.edges, known):
        dependent, prerequisite = cycle[0], cycle[1]
        edge = edge_lookup.get((dependent, prerequisite))
        path = edge.path if edge else "TODO.md"
        line = edge.line if edge else 1
        findings.append(_make_finding("LTD-PREREQ-CYCLE", "prerequisite", path, line, dependent, "prerequisite cycle: " + " -> ".join(cycle), blobs))

    active_claim_tasks = {
        claim.task_id
        for claim in parsed.claims
        if claim.task_id and claim.state == "p"
    }
    for parent in sorted(parsed.tasks, key=lambda value: (value.path, value.line, value.id)):
        children = [task for task in parsed.tasks if task.id.startswith(parent.id + ".") and task.id.count(".") == parent.id.count(".") + 1]
        if (
            not children
            or parent.marker != " "
            or parent.id in active_claim_tasks
            or parent.archived_not_accepted
        ):
            continue
        if all(child.marker in TERMINAL_MARKERS for child in children) and all(
            _terminal_id(prerequisite, task_markers, done_features) for prerequisite in parent.prerequisites
        ):
            findings.append(_make_finding("LTD-PARENT-CLOSURE-ELIGIBLE", "prerequisite", parent.path, parent.line, parent.id, f"parent package has {len(children)} terminal direct children and terminal start gates", blobs))

    for feature in sorted(parsed.features, key=lambda value: (value.path, value.line, value.id or "")):
        if feature.path != "TODO.md" or not feature.id or feature.archived_not_accepted:
            continue
        direct = [task for task in parsed.tasks if task.feature_id == feature.id and "." not in task.id]
        if direct and all(task.marker in TERMINAL_MARKERS for task in direct) and all(
            _terminal_id(prerequisite, task_markers, done_features) for prerequisite in feature.prerequisites
        ):
            findings.append(_make_finding("LTD-FEATURE-CLOSURE-ELIGIBLE", "prerequisite", feature.path, feature.line, feature.id, f"Feature has {len(direct)} terminal direct Tasks and is eligible for package closure", blobs))
    return findings


def _resolve_doc_target(
    source: str,
    target: str,
) -> Tuple[Optional[str], Optional[str]]:
    target = target.strip().split("#", 1)[0]
    if not target or target.startswith(("http://", "https://", "mailto:")):
        return None, None
    if target.startswith("/") or "\\" in target or "\x00" in target:
        return None, "instruction reference is not a safe repository-relative path"
    joined = PurePosixPath(source).parent / target
    parts: List[str] = []
    for part in joined.parts:
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                return None, "instruction reference escapes the repository root"
            parts.pop()
        else:
            parts.append(part)
    resolved = "/".join(parts)
    if not _safe_relative_path(resolved):
        return None, "instruction reference is not a safe repository-relative path"
    return resolved, None


def _safe_instruction_target(root: Path, target: str) -> bool:
    current = root
    parts = PurePosixPath(target).parts
    if not parts:
        return False
    for index, part in enumerate(parts):
        current = current / part
        try:
            info = current.lstat()
        except OSError:
            return False
        if stat.S_ISLNK(info.st_mode):
            return False
        final = index == len(parts) - 1
        if not final and not stat.S_ISDIR(info.st_mode):
            return False
        if final and target.endswith(".md"):
            return stat.S_ISREG(info.st_mode)
        if final:
            return stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)
    return False


def _instruction_findings(root: Path, parsed: ParsedRepository, blobs: Mapping[str, InputBlob]) -> List[Finding]:
    findings: List[Finding] = []
    instruction_paths = ["AGENTS.md", "SANDBOX.md", "PRIVILEGED.md"]
    bundle = parsed.workflow.get("instruction_bundle")
    if isinstance(bundle, str) and bundle in blobs:
        instruction_paths.append(bundle)
    for source in sorted(set(instruction_paths)):
        blob = blobs.get(source)
        if blob is None:
            continue
        targets: List[Tuple[int, str]] = []
        for line_number, line in enumerate(blob.lines, 1):
            targets.extend((line_number, match.group("target")) for match in MARKDOWN_LINK_RE.finditer(line))
            targets.extend((line_number, match.group("target")) for match in BACKTICK_MD_RE.finditer(line))
        seen: Set[Tuple[int, str]] = set()
        for line_number, raw_target in targets:
            target, target_error = _resolve_doc_target(source, raw_target)
            dedupe_target = target or raw_target
            if (line_number, dedupe_target) in seen:
                continue
            seen.add((line_number, dedupe_target))
            if target_error:
                findings.append(
                    _make_finding(
                        "LTD-INSTRUCTION-LINK-MISSING",
                        "instruction",
                        source,
                        line_number,
                        raw_target,
                        target_error,
                        blobs,
                    )
                )
                continue
            if target is None:
                continue
            if target == "run.sh":
                findings.append(
                    _make_finding(
                        "LTD-INSTRUCTION-LINK-MISSING",
                        "instruction",
                        source,
                        line_number,
                        target,
                        "root run.sh is a runtime request slot, not a stable instruction link target",
                        blobs,
                    )
                )
                continue
            if not _safe_instruction_target(root, target):
                findings.append(
                    _make_finding(
                        "LTD-INSTRUCTION-LINK-MISSING",
                        "instruction",
                        source,
                        line_number,
                        target,
                        f"instruction reference is missing or not a safe expected file type: {target}",
                        blobs,
                        related_paths=(target,),
                    )
                )

    agents = blobs.get("AGENTS.md")
    sandbox = blobs.get("SANDBOX.md")
    sentinel = blobs.get("SENTINEL.md")
    try:
        sentintel_info = (root / "SENTINTEL.md").lstat()
    except OSError:
        sentintel_exists = False
    else:
        sentintel_exists = (
            stat.S_ISREG(sentintel_info.st_mode)
            and not stat.S_ISLNK(sentintel_info.st_mode)
        )
    if agents:
        for line_number, line in enumerate(agents.lines, 1):
            if "SENTINTEL.md" in line and sentinel is not None and not sentintel_exists:
                findings.append(_make_finding("LTD-INSTRUCTION-NEAR-NAME", "instruction", "AGENTS.md", line_number, "SENTINTEL.md", "missing SENTINTEL.md reference has near-name SENTINEL.md present; policy identity is ambiguous", blobs, related_paths=("SENTINEL.md",)))
    if sandbox:
        for line_number, line in enumerate(sandbox.lines, 1):
            if "SENTINTEL.md" in line and sentinel is not None and not sentintel_exists:
                findings.append(_make_finding("LTD-INSTRUCTION-NEAR-NAME", "instruction", "SANDBOX.md", line_number, "SENTINTEL.md", "missing SENTINTEL.md reference has near-name SENTINEL.md present; policy identity is ambiguous", blobs, related_paths=("SENTINEL.md",)))
    directive_line: Optional[int] = None
    if sentinel:
        for line_number, line in enumerate(sentinel.lines, 1):
            lower = line.lower()
            directs_runner = re.search(
                r"\b(create|write|publish|place|materialize)\b.*\brun\.sh\b",
                lower,
            )
            negated = re.search(r"\b(never|must not|do not|forbid(?:s|den)?)\b", lower)
            if directs_runner and not negated:
                directive_line = line_number
                break
    if (
        directive_line is not None
        and sandbox
        and "never an escalation token" in sandbox.text
    ):
        findings.append(_make_finding("LTD-POLICY-CONTRADICTION", "instruction", "SENTINEL.md", directive_line, "runner-notification", "SENTINEL.md directs escalation through run.sh while SANDBOX.md forbids run.sh as escalation or notification", blobs, related_paths=("SANDBOX.md",)))

    if isinstance(bundle, str) and bundle in blobs and "issuectl bootstrap --refresh" in blobs[bundle].text:
        candidates = (root / "_src/tools/issuectl.py", root / "tools/issuectl.py", root / "issuectl")
        if not any(candidate.is_file() for candidate in candidates):
            line = next((index for index, value in enumerate(blobs[bundle].lines, 1) if "issuectl bootstrap --refresh" in value), 1)
            findings.append(_make_finding("LTD-BOOT-COMMAND-MISSING", "bootstrap", bundle, line, "issuectl bootstrap --refresh", "selected recovery command names an implementation that does not exist", blobs))
    return findings


def _duplicate_id_findings(parsed: ParsedRepository, blobs: Mapping[str, InputBlob]) -> List[Finding]:
    findings: List[Finding] = []
    identifiers: Dict[str, List[Tuple[str, int, str]]] = {}
    for task in parsed.tasks:
        identifiers.setdefault(task.id, []).append((task.path, task.line, "task"))
    for feature in parsed.features:
        if feature.id:
            identifiers.setdefault(feature.id, []).append((feature.path, feature.line, "feature"))
    for identifier, occurrences in sorted(identifiers.items()):
        if len(occurrences) > 1:
            path, line, kind = sorted(occurrences)[0]
            findings.append(_make_finding("LTD-ID-DUPLICATE", "backlog", path, line, identifier, f"{kind} ID occurs {len(occurrences)} times across authoritative lists", blobs, related_paths=(item[0] for item in occurrences)))
    for task in parsed.tasks:
        if task.marker not in VALID_MARKERS:
            findings.append(_make_finding("LTD-MARKER-UNDEFINED", "backlog", task.path, task.line, task.id, f"Task uses undefined marker [{task.marker}]", blobs))
    for entry in parsed.legacy_entries:
        if entry.marker not in VALID_MARKERS:
            findings.append(_make_finding("LTD-MARKER-UNDEFINED", "backlog", entry.path, entry.line, f"legacy-entry@{entry.line}", f"legacy entry uses undefined marker [{entry.marker}]", blobs))

    for path in ("TODO.md", "DONE.md"):
        blob = blobs[path]
        for line_number, line in enumerate(blob.lines, 1):
            if line.startswith("- [") and "**" in line and not TASK_HEADER_RE.match(line):
                candidate = re.search(r"\*\*(?P<id>[0-9][0-9.-]*)\*\*", line)
                if candidate:
                    findings.append(
                        _make_finding(
                            "LTD-TASK-HEADER-MALFORMED",
                            "backlog",
                            path,
                            line_number,
                            candidate.group("id"),
                            "Task-like checklist entry has a malformed canonical Task ID/header",
                            blobs,
                        )
                    )
            if not line.startswith("## Feature:"):
                continue
            match = FEATURE_HEADER_RE.match(line)
            feature_id = match.group("id") if match else None
            title = match.group("title") if match else line
            malformed = path == "TODO.md" and feature_id is None
            malformed = malformed or (
                path == "DONE.md"
                and feature_id is None
                and bool(re.match(r"[0-9]", title.strip()))
            )
            if malformed:
                findings.append(
                    _make_finding(
                        "LTD-FEATURE-HEADER-MALFORMED",
                        "backlog",
                        path,
                        line_number,
                        title.strip(),
                        "Feature header does not carry a canonical four-digit Feature ID",
                        blobs,
                    )
                )
    return findings


def _required_commit_values(parsed: ParsedRepository) -> Set[str]:
    values = {
        ref.value
        for ref in _authoritative_refs(parsed.refs)
        if FULL_COMMIT_RE.fullmatch(ref.value)
    }
    values.update(
        claim.base_commit
        for claim in parsed.claims
        if claim.base_commit and FULL_COMMIT_RE.fullmatch(claim.base_commit)
    )
    return values


def _git_reachable_commits(root: Path) -> Set[str]:
    environment = dict(os.environ)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    environment["LC_ALL"] = "C"
    try:
        completed = subprocess.run(
            ["git", "--no-optional-locks", "rev-list", "--all"],
            cwd=root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DoctorInputError(
            "LTD-GIT-PROBE",
            ".git",
            f"read-only commit reachability probe failed: {_exception_detail(exc)}",
        ) from exc
    if completed.returncode != 0:
        excerpt = " ".join(
            completed.stderr.decode("utf-8", "replace")[:512].split()
        )
        raise DoctorInputError("LTD-GIT-PROBE", ".git", f"git rev-list --all exited {completed.returncode}: {excerpt}")
    values = completed.stdout.decode("ascii", "strict").splitlines()
    if any(not FULL_COMMIT_RE.fullmatch(value) for value in values):
        raise DoctorInputError("LTD-GIT-PROBE", ".git", "git rev-list returned a malformed commit ID")
    return set(values)


def _plan_action(finding: Finding) -> Tuple[str, str]:
    if finding.category == "claim":
        return "owner-reconcile-claim", "claim-owner-or-authorized-maintainer"
    if finding.rule in {"LTD-PARENT-CLOSURE-ELIGIBLE", "LTD-FEATURE-CLOSURE-ELIGIBLE"}:
        return "claim-and-perform-package-closure", "eligible-task-agent"
    if finding.category in {"bootstrap", "instruction"}:
        return "policy-authority-reconcile", "policy-owner-or-authorized-maintainer"
    if finding.category == "reference":
        return "verify-or-reconcile-reference", "backlog-owner-or-authorized-maintainer"
    if finding.category == "prerequisite":
        return "review-and-reconcile-prerequisite", "backlog-owner-or-authorized-maintainer"
    return "review-and-reconcile-exact-entry", "backlog-owner-or-authorized-maintainer"


def _plans(findings: Sequence[Finding], blobs: Mapping[str, InputBlob]) -> List[ReconciliationPlan]:
    plans: List[ReconciliationPlan] = []
    for finding in findings:
        action, actor = _plan_action(finding)
        targets = tuple(sorted(set((finding.path,) + finding.related_paths)))
        source_blob = blobs.get(finding.path)
        plans.append(
            ReconciliationPlan(
                rule=finding.rule,
                path=finding.path,
                line=finding.line,
                subject=finding.subject,
                action=action,
                required_actor=actor,
                target_paths=targets,
                expected_document_sha256=source_blob.sha256 if source_blob is not None else None,
            )
        )
    return sorted(plans, key=lambda item: (item.rule, item.path, item.line, item.subject, item.action))


def _summary(verdict: str, findings: Sequence[Finding], parsed: ParsedRepository) -> List[str]:
    counts = {severity: sum(item.severity == severity for item in findings) for severity in ("error", "warning", "info")}
    lines = [
        f"legacy-task-doctor {verdict}: errors={counts['error']} warnings={counts['warning']} info={counts['info']} total={len(findings)}",
        f"inventory: features={len(parsed.features)} tasks={len(parsed.tasks)} claims={len(parsed.claims)} refs={len(parsed.refs)} prerequisites={len(parsed.edges)}",
    ]
    if len(findings) <= 8:
        selected = findings
        truncated = 0
    else:
        selected = findings[:7]
        truncated = len(findings) - len(selected)
    for finding in selected:
        lines.append(f"{finding.rule} {finding.path}:{finding.line} {finding.subject}: {finding.message}")
    if truncated:
        lines.append(f"... {truncated} additional findings; use --json for the complete report.")
    return lines[:10]


def _empty_report(error: DoctorInputError) -> Dict[str, object]:
    evidence = " ".join(error.message.split())
    finding = Finding(
        rule=error.rule,
        severity=RULE_SEVERITY.get(error.rule, "error"),
        category="input",
        path=error.path,
        line=1,
        subject=error.path,
        message=evidence,
        evidence=evidence,
        evidence_sha256=_sha256(evidence.encode("utf-8")),
    )
    return {
        "schema": REPORT_SCHEMA,
        "verdict": "INCOMPLETE",
        "inputs": [],
        "authority": {},
        "inventory": {"features": 0, "tasks": 0, "legacy_entries": 0, "claims": 0, "active_claims": 0, "refs": 0, "prerequisite_edges": 0},
        "normalized": {"features": [], "tasks": [], "legacy_entries": [], "claims": [], "refs": [], "prerequisites": []},
        "counts": {"error": 1, "warning": 0, "info": 0, "total": 1},
        "findings": [finding.to_dict()],
        "plans": [],
        "summary": [f"legacy-task-doctor INCOMPLETE: {error.rule} {error.path}: {evidence}"],
    }


def scan_repository(root: Path, *, reachable_commits: Optional[Set[str]] = None) -> Dict[str, object]:
    """Scan one legacy repository root without modifying it.

    ``reachable_commits`` is an injectable read-only commit set for hermetic
    fixtures.  Normal callers omit it and use the fixed local Git probe.
    """

    root = root.resolve()
    try:
        blobs, claim_names = _discover_inputs(root)
    except DoctorInputError as exc:
        return _empty_report(exc)

    parsed = ParsedRepository()
    for relative in ("TODO.md", "DONE.md"):
        features, tasks, legacy, refs, edges = _parse_backlog(blobs[relative])
        parsed.features.extend(features)
        parsed.tasks.extend(tasks)
        parsed.legacy_entries.extend(legacy)
        parsed.refs.extend(refs)
        parsed.edges.extend(edges)

    claim_occurrences: Dict[str, Sequence[FieldOccurrence]] = {}
    for relative in claim_names:
        claim, occurrences = _parse_claim(blobs[relative])
        parsed.claims.append(claim)
        claim_occurrences[relative] = occurrences

    workflow, workflow_findings = _parse_workflow(blobs["agent-workflow.json"], blobs)
    parsed.workflow = workflow
    parsed.findings.extend(workflow_findings)

    required_commits = _required_commit_values(parsed)
    reachable = set(reachable_commits) if reachable_commits is not None else set()
    if reachable_commits is None and required_commits:
        try:
            reachable = _git_reachable_commits(root)
        except DoctorInputError as exc:
            report = _empty_report(exc)
            report["inputs"] = [blob.inventory() for blob in sorted(blobs.values(), key=lambda value: value.path)]
            return report

    parsed.findings.extend(_duplicate_id_findings(parsed, blobs))
    parsed.findings.extend(_ref_findings(parsed, blobs, reachable))
    parsed.findings.extend(_claim_findings(parsed, blobs, claim_occurrences, reachable))
    parsed.findings.extend(_prerequisite_findings(parsed, blobs))
    parsed.findings.extend(_instruction_findings(root, parsed, blobs))
    findings = _dedupe_findings(parsed.findings)

    changed = _verify_inputs(root, blobs, claim_names)
    if reachable_commits is None and required_commits:
        try:
            reachable_after = _git_reachable_commits(root)
        except DoctorInputError:
            changed.append(".git/refs")
        else:
            if reachable_after != reachable:
                changed.append(".git/refs")
    changed = sorted(set(changed))
    verdict = "FINDINGS" if findings else "CLEAN"
    plans = _plans(findings, blobs)
    if changed:
        for relative in changed:
            findings.append(
                _make_finding(
                    "LTD-INPUT-CHANGED",
                    "input",
                    relative if relative in blobs else "TODO.md",
                    1,
                    relative,
                    "input set or bytes changed during the read-only scan",
                    blobs,
                    evidence=relative,
                )
            )
        findings = _dedupe_findings(findings)
        plans = []
        verdict = "INCOMPLETE"

    counts = {severity: sum(item.severity == severity for item in findings) for severity in ("error", "warning", "info")}
    counts["total"] = len(findings)
    normalized_features = sorted(parsed.features, key=lambda value: (0 if value.path == "TODO.md" else 1, value.line, value.id or ""))
    normalized_tasks = sorted(parsed.tasks, key=lambda value: (0 if value.path == "TODO.md" else 1, value.line, value.id))
    normalized_legacy = sorted(parsed.legacy_entries, key=lambda value: (0 if value.path == "TODO.md" else 1, value.line))
    normalized_claims = sorted(parsed.claims, key=lambda value: value.path)
    normalized_refs = sorted(parsed.refs, key=lambda value: (value.path, value.line, value.column, value.value))
    normalized_edges = sorted(parsed.edges, key=lambda value: (value.dependent, value.prerequisite, value.path, value.line))
    report: Dict[str, object] = {
        "schema": REPORT_SCHEMA,
        "verdict": verdict,
        "inputs": [blob.inventory() for blob in sorted(blobs.values(), key=lambda value: value.path)],
        "authority": {key: workflow.get(key) for key in sorted(REQUIRED_WORKFLOW_KEYS) if key in workflow},
        "inventory": {
            "features": len(parsed.features),
            "tasks": len(parsed.tasks),
            "legacy_entries": len(parsed.legacy_entries),
            "claims": len(parsed.claims),
            "active_claims": sum(claim.state == "p" for claim in parsed.claims),
            "refs": len(parsed.refs),
            "prerequisite_edges": len(parsed.edges),
        },
        "normalized": {
            "features": [value.to_dict() for value in normalized_features],
            "tasks": [value.to_dict() for value in normalized_tasks],
            "legacy_entries": [value.to_dict() for value in normalized_legacy],
            "claims": [value.to_dict() for value in normalized_claims],
            "refs": [value.to_dict() for value in normalized_refs],
            "prerequisites": [value.to_dict() for value in normalized_edges],
        },
        "counts": counts,
        "findings": [value.to_dict() for value in findings],
        "plans": [value.to_dict() for value in plans],
    }
    report["summary"] = _summary(verdict, findings, parsed)
    return report


def render_summary(report: Mapping[str, object]) -> Tuple[str, ...]:
    value = report.get("summary", ())
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        return ("legacy-task-doctor INCOMPLETE: malformed report summary",)
    return tuple(value[:10])


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2], help="legacy repository root")
    parser.add_argument("--json", action="store_true", help="emit canonical deterministic JSON")
    args = parser.parse_args(argv)

    report = scan_repository(args.root)
    if args.json:
        sys.stdout.write(_canonical_json(report))
    else:
        for line in render_summary(report):
            print(line)
    return {"CLEAN": 0, "FINDINGS": 1}.get(str(report.get("verdict")), 2)


if __name__ == "__main__":
    raise SystemExit(main())
