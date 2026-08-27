#!/usr/bin/env python3
"""Build the retained source/target migration cutover report (Task 0037-16).

The report is deliberately independent of the importer.  It reads the frozen
legacy inventory and the source Git blobs, parses the disposable candidate,
and records both semantic and preserved-byte comparisons.  A report passes
only when every error is resolved and every warning has an explicit
disposition.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

SCHEMA = "issue-migration-report@v1"
SCHEMA_VERSION = "1.0"
TOOL_VERSION = "1.0"
PRODUCING_ISSUE = "0037-16"
TOOL_REL = "_src/tools/issue_migration_report.py"
SCHEMA_REL = "provenance/_schema/issue-migration-report-v1.schema.json"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
REF_RE = re.compile(r"(?<![0-9a-f])(?:[0-9a-f]{7,40}|local-[a-zA-Z0-9._-]+)(?![0-9a-f])")
AC_SPLIT_RE = re.compile(r";\s+")
MARKER_STATE = {
    " ": "open",
    "p": "in_progress",
    "?": "open",
    "u": "blocked",
    "w": "closed",
    "x": "closed",
    "d": "open",
}


class MigrationReportError(RuntimeError):
    """Fail-closed input, identity, or output error."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha256_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def finding_id(rule: str, item: str, field: str, source_locator: str) -> str:
    """Stable ID whose input never includes an observed value."""
    material = "|".join((rule, item, field, source_locator)).encode("utf-8")
    return "MIG-" + hashlib.sha256(material).hexdigest()[:16]


def _git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, check=False
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise MigrationReportError("MIG-GIT", detail or "Git object lookup failed")
    return result.stdout


def _commit_exists(repo: Path, commit: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{commit}^{{commit}}"],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _read_json(path: Path, code: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MigrationReportError(code, f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MigrationReportError(code, f"{path} must contain a JSON object")
    return value


def _under(path: Path, root: Path, code: str = "MIG-PATH-ESCAPE") -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise MigrationReportError(code, f"{path} escapes {root}") from exc
    return resolved


def _atomic_write(path: Path, raw: bytes, root: Path) -> None:
    _under(path.parent, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}-{time.time_ns()}")
    _under(tmp, root)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(tmp, flags, 0o644)
    try:
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise MigrationReportError("MIG-WRITE", f"short write for {path}")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    try:
        os.replace(tmp, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if tmp.exists():
            tmp.unlink()


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _lf_bytes(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _json_scalar(text: str) -> Any:
    text = text.strip()
    if not text:
        return None
    if text in {"true", "false"}:
        return text == "true"
    if text == "[]":
        return []
    if text.startswith('"'):
        return json.loads(text)
    return text


def parse_candidate_markdown(raw: bytes) -> dict:
    """Parse the strict subset emitted by issue_import_legacy."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MigrationReportError("MIG-CANDIDATE-UTF8", str(exc)) from exc
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise MigrationReportError("MIG-CANDIDATE-FRONTMATTER", "missing opening ---")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise MigrationReportError("MIG-CANDIDATE-FRONTMATTER", "missing closing ---") from exc
    front: Dict[str, Any] = {}
    current: Optional[str] = None
    for line in lines[1:end]:
        if not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            current = key
            front[key] = _json_scalar(value)
            if front[key] is None:
                front[key] = [] if key in {"prerequisites", "labels", "criteria"} else {}
            continue
        if current is None:
            continue
        stripped = line.strip()
        if line.startswith("  - "):
            if not isinstance(front[current], list):
                front[current] = []
            payload = stripped[2:]
            if ":" in payload and current == "criteria":
                key, value = payload.split(":", 1)
                front[current].append({key: _json_scalar(value)})
            else:
                front[current].append(_json_scalar(payload))
        elif line.startswith("    ") and isinstance(front[current], list) and front[current]:
            key, value = stripped.split(":", 1)
            if isinstance(front[current][-1], dict):
                front[current][-1][key] = _json_scalar(value)
        elif line.startswith("  ") and isinstance(front[current], dict):
            key, value = stripped.split(":", 1)
            front[current][key] = _json_scalar(value)

    sections: Dict[str, str] = {}
    heading: Optional[str] = None
    body: List[str] = []
    for line in lines[end + 1 :]:
        if line.startswith("## "):
            if heading is not None:
                sections[heading] = "\n".join(body).strip()
            heading = line[3:].strip().lower()
            body = []
        elif heading is not None:
            body.append(line)
    if heading is not None:
        sections[heading] = "\n".join(body).strip()
    criteria_text = []
    for line in sections.get("acceptance criteria", "").splitlines():
        match = re.match(r"^- \*\*(AC-[0-9]{3})\*\*\s*(.*)$", line.strip())
        if match:
            criteria_text.append({"id": match.group(1), "text": _nfc(match.group(2).strip())})
    return {"front": front, "sections": sections, "criteria_text": criteria_text, "text": text}


def _legacy_block(blob: str, line_number: int) -> str:
    lines = blob.splitlines()
    start = max(line_number - 1, 0)
    chunk: List[str] = []
    for index in range(start, len(lines)):
        row = lines[index]
        if index > start and row.startswith("- [") and "**" in row:
            break
        if index > start and row.startswith("## "):
            break
        chunk.append(row)
    return "\n".join(chunk)


def _extract_source_semantics(item: Mapping[str, Any], blob: str) -> dict:
    item_id = str(item["id"])
    kind = str(item.get("kind") or "")
    locator = f"{item.get('path')}:{item.get('line')}"
    if kind == "feature":
        state = "closed" if item.get("path") == "DONE.md" or item_id == "0021" else "open"
        return {
            "id": item_id,
            "level": "feature",
            "parent": None,
            "state": state,
            "prerequisites": [],
            "labels": ["archived-not-accepted"] if item_id == "0021" else [],
            "authority": "shadow",
            "goal": _nfc(str(item.get("title") or item_id)),
            "scope": "Imported Feature body is retained via source locators; child Tasks are separate items.",
            "criteria": ["Preserve Feature identity and archive classification from the legacy source."],
            "definition_of_done": "Feature identity, archive class, and locators match the source blobs.",
            "refs": sorted(set(REF_RE.findall(_legacy_block(blob, int(item.get("line") or 1))))),
            "locator": locator,
        }
    block = _legacy_block(blob, int(item.get("line") or 1))
    title = str(item.get("title_tail") or "").strip()
    goal = title or "Imported from legacy backlog."
    acceptance = ""
    dod = ""
    rest: List[str] = []
    collecting = False
    for raw in block.splitlines():
        stripped = raw.strip()
        lower = stripped.lower()
        if lower.startswith("- **acceptance criteria:**") or lower.startswith("**acceptance criteria:**"):
            acceptance = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
            collecting = True
            continue
        if collecting:
            if stripped.startswith("- **") or stripped.startswith("## ") or (
                stripped.startswith("- [") and "**" in stripped
            ):
                collecting = False
            elif stripped:
                acceptance = (acceptance + " " + stripped).strip()
                continue
        if lower.startswith("- **definition of done:**") or lower.startswith("**definition of done:**"):
            dod = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
            collecting = False
        elif stripped.startswith("- [") and "**" in stripped:
            continue
        else:
            rest.append(raw)
    acceptance = acceptance.strip().lstrip("*").strip()
    dod = dod.strip().lstrip("*").strip()
    criteria = [part.strip().rstrip(".") for part in AC_SPLIT_RE.split(acceptance) if part.strip()]
    if not criteria:
        criteria = ["Preserve imported acceptance text from the legacy source."]
    if not dod:
        dod = "Imported item is represented under the disposable candidate root."
    prereqs = sorted(
        {
            str(edge.get("to"))
            for edge in (item.get("prerequisites") or [])
            if isinstance(edge, dict) and edge.get("to")
        }
    )
    marker = str(item.get("marker", " "))
    level = "subtask" if "." in item_id else "task"
    parent = item_id.rsplit(".", 1)[0] if level == "subtask" else item_id.split("-", 1)[0]
    return {
        "id": item_id,
        "level": level,
        "parent": parent,
        "state": MARKER_STATE.get(marker),
        "prerequisites": prereqs,
        "labels": ["archived-not-accepted"] if item_id.startswith("0021-") else [],
        "authority": "shadow",
        "goal": _nfc(goal),
        "scope": _nfc("\n".join(rest).strip() or "Imported legacy text retained under source locators."),
        "criteria": [_nfc(value) for value in criteria],
        "definition_of_done": _nfc(dod),
        "refs": sorted(set(REF_RE.findall(block))),
        "locator": locator,
    }


def _candidate_semantics(parsed: Mapping[str, Any]) -> dict:
    front = parsed["front"]
    criteria = [entry["text"] for entry in parsed.get("criteria_text") or []]
    return {
        "id": front.get("id"),
        "level": front.get("level"),
        "parent": front.get("parent"),
        "state": front.get("state"),
        "prerequisites": sorted(front.get("prerequisites") or []),
        "labels": sorted(front.get("labels") or []),
        "authority": front.get("authority"),
        "goal": _nfc(parsed.get("sections", {}).get("goal", "")),
        "scope": _nfc(parsed.get("sections", {}).get("scope", "")),
        "criteria": criteria,
        "definition_of_done": _nfc(parsed.get("sections", {}).get("definition of done", "")),
        "refs": sorted(set(REF_RE.findall(parsed.get("text", "")))),
    }


def _group_digest(records: Iterable[Tuple[str, str]]) -> str:
    material = b"".join(
        key.encode("utf-8") + b"\0" + digest.encode("ascii") + b"\0"
        for key, digest in sorted(records)
    )
    return sha256_bytes(material)


def _summary(items: Mapping[str, Mapping[str, Any]], raw_digests: Mapping[str, str]) -> dict:
    by_type = Counter(str(value.get("level")) for value in items.values())
    by_state = Counter(str(value.get("state")) for value in items.values())
    type_hashes = {
        key: _group_digest((item_id, raw_digests[item_id]) for item_id, value in items.items() if value.get("level") == key)
        for key in sorted(by_type)
    }
    state_hashes = {
        key: _group_digest((item_id, raw_digests[item_id]) for item_id, value in items.items() if value.get("state") == key)
        for key in sorted(by_state)
    }
    return {
        "total_items": len(items),
        "counts_by_type": dict(sorted(by_type.items())),
        "counts_by_state": dict(sorted(by_state.items())),
        "hashes_by_item": dict(sorted(raw_digests.items())),
        "hashes_by_type": type_hashes,
        "hashes_by_state": state_hashes,
    }


def _artifact_identity(path: Optional[Path], members: Sequence[Mapping[str, Any]], kind: str) -> dict:
    normalized = [
        {"path": str(member["path"]), "digest": str(member["digest"]), "size_bytes": int(member["size_bytes"])}
        for member in members
    ]
    normalized.sort(key=lambda value: value["path"])
    payload = canonical_json(normalized).encode("utf-8")
    return {
        "kind": kind,
        "path": str(path) if path else None,
        "digest": sha256_file(path) if path else sha256_bytes(payload),
        "members_digest": sha256_bytes(payload),
        "member_count": len(normalized),
    }


def _integrity_payload(report: Mapping[str, Any]) -> bytes:
    clone = copy.deepcopy(report)
    clone.setdefault("integrity", {}).pop("payload_digest", None)
    return canonical_json(clone).encode("utf-8")


def verify_report(path: Path) -> Tuple[bool, str]:
    try:
        report = _read_json(path, "MIG-REPORT-READ")
    except MigrationReportError as exc:
        return False, str(exc)
    expected = report.get("integrity", {}).get("payload_digest")
    observed = sha256_bytes(_integrity_payload(report))
    if expected != observed:
        return False, f"MIG-REPORT-TAMPERED: expected {expected}, observed {observed}"
    return True, observed


def _render_markdown(report: Mapping[str, Any]) -> str:
    findings = report.get("findings") or []
    lines = [
        f"# Issue migration report — {report['run_id']}",
        "",
        f"- Decision: **{str(report['decision']['pass']).lower()}**",
        f"- Source commit: `{report['identity']['source_commit']}`",
        f"- Candidate commit: `{report['identity']['candidate_commit']}`",
        f"- Source items: {report['summaries']['source']['total_items']}",
        f"- Candidate items: {report['summaries']['candidate']['total_items']}",
        f"- Findings: {len(findings)}",
        "",
        "## Reconciliation",
        "",
    ]
    for key in ("ids", "states", "edges", "criteria", "definition_of_done", "refs", "claims", "archives", "preserved_text", "provenance", "generated_views"):
        record = report["comparisons"][key]
        lines.append(f"- {key}: `{record['status']}` ({record.get('mismatch_count', 0)} mismatch(es))")
    lines.extend(["", "## Findings", ""])
    if not findings:
        lines.append("No findings.")
    else:
        for finding in findings:
            disposition_record = finding.get("disposition")
            disposition = (
                f"{disposition_record['value']} (authority: {disposition_record['authority']})"
                if disposition_record
                else "unresolved"
            )
            lines.append(
                f"- `{finding['id']}` {finding['severity']} `{finding['rule']}` "
                f"({finding['item']} / {finding['field']}): {finding['message']} — {disposition}"
            )
    lines.extend(["", "## Rerun delta", ""])
    previous = report["previous_run"]
    lines.append(f"- Previous report: `{previous.get('run_id') or 'none'}`")
    lines.append(f"- Added findings: {len(previous['added_finding_ids'])}")
    lines.append(f"- Retained findings: {len(previous['retained_finding_ids'])}")
    lines.append(f"- Resolved findings: {len(previous['resolved_finding_ids'])}")
    return "\n".join(lines) + "\n"


def generate_report(
    *,
    repo: Path,
    source_inventory_path: Path,
    candidate_root: Path,
    output_parent: Path,
    run_id: str,
    candidate_commit: str,
    source_artifact_set_path: Optional[Path] = None,
    candidate_artifact_set_path: Optional[Path] = None,
    migration_state_path: Optional[Path] = None,
    generated_view_manifest_path: Optional[Path] = None,
    previous_report_path: Optional[Path] = None,
    produced_at: Optional[str] = None,
) -> dict:
    repo = repo.resolve()
    candidate_root = candidate_root.resolve()
    output_parent = output_parent.resolve()
    if not RUN_ID_RE.fullmatch(run_id):
        raise MigrationReportError("MIG-RUN-ID", f"unsafe run id {run_id!r}")
    inventory = _read_json(source_inventory_path, "MIG-INVENTORY")
    manifest_path = candidate_root / "import-manifest.json"
    manifest = _read_json(manifest_path, "MIG-CANDIDATE-MANIFEST")
    source_commit = str(inventory.get("source_commit") or "")
    if not COMMIT_RE.fullmatch(source_commit) or not _commit_exists(repo, source_commit):
        raise MigrationReportError("MIG-SOURCE-COMMIT", "inventory source commit is absent or invalid")
    if not COMMIT_RE.fullmatch(candidate_commit):
        raise MigrationReportError("MIG-CANDIDATE-COMMIT", "candidate commit must be full 40-hex")

    findings: List[dict] = []
    raw_dispositions = [
        value for value in (inventory.get("dispositions") or []) if isinstance(value, dict)
    ]
    dispositions = {
        (str(value.get("item") or "*"), str(value.get("rule") or "*")): {
            "value": str(value["disposition"]),
            "authority": str(value["authority"]),
            "evidence_credit": value.get("evidence_credit"),
            "source": f"inventory:dispositions[{index}]",
        }
        for index, value in enumerate(raw_dispositions)
        if str(value.get("disposition") or "").strip()
        and str(value.get("authority") or "").strip()
    }

    def add(
        rule: str,
        item: str,
        field: str,
        locator: str,
        severity: str,
        message: str,
        disposition: Optional[Mapping[str, Any]] = None,
    ) -> None:
        disp = disposition or dispositions.get((item, rule)) or dispositions.get((item, "*")) or dispositions.get(("*", rule))
        findings.append(
            {
                "id": finding_id(rule, item, field, locator),
                "rule": rule,
                "severity": severity,
                "item": item,
                "field": field,
                "source_locator": locator,
                "message": message,
                "disposition": disp,
            }
        )

    for index, value in enumerate(raw_dispositions):
        if str(value.get("disposition") or "").strip() and not str(
            value.get("authority") or ""
        ).strip():
            add(
                "MIG-DISPOSITION-AUTHORITY",
                str(value.get("item") or "migration"),
                "disposition",
                f"inventory:dispositions[{index}]",
                "error",
                "disposition lacks an authority reference",
            )

    state = _read_json(migration_state_path, "MIG-STATE") if migration_state_path else {}
    candidate_source = str(manifest.get("source_commit") or "")
    baseline = str((state.get("watermarks") or {}).get("baseline") or source_commit)
    latest = str((state.get("watermarks") or {}).get("latest_source") or candidate_source)
    candidate_watermark = str((state.get("watermarks") or {}).get("candidate") or candidate_source)
    if candidate_source != source_commit or latest != source_commit or candidate_watermark != source_commit:
        add("MIG-STALE-CANDIDATE", "migration", "watermark", "inventory:source_commit", "error", "candidate is not based on the frozen source commit")
    if candidate_commit == source_commit or baseline == candidate_commit:
        add("MIG-SELF-BASELINED", "migration", "candidate_commit", "candidate:commit", "error", "candidate identity aliases its source/baseline")
    if not _commit_exists(repo, candidate_commit):
        add("MIG-CANDIDATE-COMMIT-MISSING", "migration", "candidate_commit", "candidate:commit", "error", "candidate commit is not present in the repository")

    source_blobs: Dict[str, str] = {}
    source_items: Dict[str, dict] = {}
    source_raw_digests: Dict[str, str] = {}
    for item in inventory.get("items") or []:
        if not isinstance(item, dict) or item.get("kind") == "malformed_task" or not item.get("id"):
            continue
        path = str(item.get("path") or "")
        if path not in source_blobs:
            source_blobs[path] = _git(repo, "show", f"{source_commit}:{path}").decode("utf-8")
        semantic = _extract_source_semantics(item, source_blobs[path])
        item_id = semantic["id"]
        if item_id in source_items:
            add("MIG-DUPLICATE-SOURCE-ID", item_id, "id", semantic["locator"], "error", "source inventory contains a duplicate canonical ID")
            continue
        source_items[item_id] = semantic
        source_raw_digests[item_id] = str(item.get("text_sha256") or sha256_bytes(_legacy_block(source_blobs[path], int(item.get("line") or 1)).encode("utf-8")))

    candidate_items: Dict[str, dict] = {}
    candidate_raw_digests: Dict[str, str] = {}
    candidate_paths: Dict[str, Path] = {}
    member_rows: List[dict] = []
    for record in manifest.get("items") or []:
        if not isinstance(record, dict) or not record.get("id") or not record.get("path"):
            add("MIG-CANDIDATE-MANIFEST-INVALID", "migration", "items", "candidate:import-manifest.json", "error", "candidate manifest has an invalid item record")
            continue
        item_id = str(record["id"])
        if item_id in candidate_items:
            add(
                "MIG-DUPLICATE-CANDIDATE-ID",
                item_id,
                "id",
                "candidate:import-manifest.json",
                "error",
                "candidate manifest repeats a canonical ID",
            )
            continue
        candidate_path = _under(candidate_root / str(record["path"]), candidate_root)
        if not candidate_path.is_file():
            add("MIG-SOURCE-OMISSION", item_id, "item", source_items.get(item_id, {}).get("locator", str(record["path"])), "error", "candidate item file is missing")
            continue
        raw = candidate_path.read_bytes()
        parsed = parse_candidate_markdown(raw)
        candidate_semantics = _candidate_semantics(parsed)
        if candidate_semantics.get("id") != item_id:
            add(
                "MIG-CANDIDATE-ID-MISMATCH",
                item_id,
                "id",
                "candidate:" + str(record["path"]),
                "error",
                "candidate frontmatter ID differs from its manifest identity",
            )
        if record.get("state") and candidate_semantics.get("state") != record.get("state"):
            add(
                "MIG-CANDIDATE-MANIFEST-DRIFT",
                item_id,
                "state",
                "candidate:import-manifest.json",
                "error",
                "candidate frontmatter state differs from its manifest record",
            )
        candidate_items[item_id] = candidate_semantics
        candidate_raw_digests[item_id] = sha256_bytes(raw)
        candidate_paths[item_id] = candidate_path
        member_rows.append({"path": str(record["path"]), "digest": sha256_bytes(raw), "size_bytes": len(raw)})

    source_ids = set(source_items)
    candidate_ids = set(candidate_items)
    for item_id in sorted(source_ids - candidate_ids):
        add("MIG-SOURCE-OMISSION", item_id, "id", source_items[item_id]["locator"], "error", "source item is absent from candidate")
    for item_id in sorted(candidate_ids - source_ids):
        add("MIG-ID-INFLATION", item_id, "id", "candidate:" + str(candidate_paths[item_id].relative_to(candidate_root)), "error", "candidate item has no source identity")

    field_rules = {
        "state": "MIG-STATE-DRIFT",
        "level": "MIG-TYPE-DRIFT",
        "parent": "MIG-EDGE-DRIFT",
        "prerequisites": "MIG-EDGE-DRIFT",
        "criteria": "MIG-CRITERIA-DRIFT",
        "definition_of_done": "MIG-DOD-DRIFT",
        "goal": "MIG-SEMANTIC-DRIFT",
        "scope": "MIG-SEMANTIC-DRIFT",
        "labels": "MIG-ARCHIVE-DRIFT",
    }
    for item_id in sorted(source_ids & candidate_ids):
        source = source_items[item_id]
        candidate = candidate_items[item_id]
        for field, rule in field_rules.items():
            if source.get(field) != candidate.get(field):
                add(rule, item_id, field, source["locator"], "error", f"candidate {field} differs from normalized source semantics")
        if candidate.get("authority") != "shadow":
            add("MIG-AUTHORITY-INFLATION", item_id, "authority", source["locator"], "error", "candidate asserts authority instead of shadow status")
        source_refs = set(source.get("refs") or [])
        candidate_refs = set(candidate.get("refs") or [])
        fabricated = candidate_refs - source_refs
        missing_refs = source_refs - candidate_refs
        if fabricated:
            add("MIG-FABRICATED-REF", item_id, "refs", source["locator"], "error", "candidate contains a reference absent from the source item")
        if missing_refs:
            add("MIG-REF-OMISSION", item_id, "refs", source["locator"], "error", "candidate omits a source reference")
        text = candidate_paths[item_id].read_text(encoding="utf-8")
        if re.search(r"(?m)^(?:acceptance|approval|closure|evidence):", text):
            add("MIG-EVIDENCE-INFLATION", item_id, "evidence", source["locator"], "error", "candidate fabricates acceptance, approval, closure, or evidence fields")

    claim_mismatches = 0
    for claim in inventory.get("claims") or []:
        if not isinstance(claim, dict) or not claim.get("path"):
            continue
        source_path = str(claim["path"])
        item = str(claim.get("item") or source_path)
        locator = source_path
        candidate_path = _under(candidate_root / "legacy-claims" / source_path, candidate_root)
        try:
            source_raw = _git(repo, "show", f"{source_commit}:{source_path}")
        except MigrationReportError:
            add("MIG-PROVENANCE-INCOMPLETE", item, "claim", locator, "error", "inventoried claim blob is absent from the source commit")
            claim_mismatches += 1
            continue
        if not candidate_path.is_file():
            add("MIG-CLAIM-OMISSION", item, "claim", locator, "error", "preserved claim blob is absent")
            claim_mismatches += 1
            continue
        candidate_raw = candidate_path.read_bytes()
        member_rows.append({"path": str(candidate_path.relative_to(candidate_root)), "digest": sha256_bytes(candidate_raw), "size_bytes": len(candidate_raw)})
        if _lf_bytes(source_raw) != _lf_bytes(candidate_raw):
            add("MIG-BYTE-DRIFT", item, "claim", locator, "error", "LF-normalized preserved claim bytes differ")
            claim_mismatches += 1

    for inventory_finding in inventory.get("findings") or []:
        if not isinstance(inventory_finding, dict):
            continue
        severity = str(inventory_finding.get("severity") or "warning")
        severity = "error" if severity == "blocking" else severity
        rule = str(inventory_finding.get("rule") or "MIG-SOURCE-ANOMALY")
        if not rule.startswith("MIG-"):
            rule = "MIG-SOURCE-" + rule
        add(
            rule,
            str(inventory_finding.get("item") or "migration"),
            str(inventory_finding.get("field") or "source"),
            str(inventory_finding.get("locator") or "inventory"),
            severity,
            str(inventory_finding.get("message") or "source inventory anomaly"),
        )
    for candidate_finding in manifest.get("findings") or []:
        if not isinstance(candidate_finding, dict):
            continue
        severity = str(candidate_finding.get("severity") or "warning")
        severity = "error" if severity == "blocking" else severity
        if severity == "info":
            continue
        rule = "MIG-IMPORT-" + str(candidate_finding.get("rule") or candidate_finding.get("code") or "ANOMALY")
        add(rule, str(candidate_finding.get("item") or "migration"), "import", str(candidate_finding.get("locator") or "candidate:import-manifest.json"), severity, str(candidate_finding.get("message") or "import anomaly"))

    source_members = []
    for member in inventory.get("source_artifacts") or []:
        if isinstance(member, dict) and member.get("path") and member.get("digest"):
            source_members.append({"path": member["path"], "digest": member["digest"], "size_bytes": member.get("size_bytes", 0)})
            try:
                observed = sha256_bytes(_git(repo, "show", f"{source_commit}:{member['path']}"))
                if observed != member["digest"]:
                    add("MIG-SOURCE-ARTIFACT-TAMPER", "migration", "source_artifact", str(member["path"]), "error", "source artifact digest differs from frozen inventory")
            except MigrationReportError:
                add("MIG-PROVENANCE-INCOMPLETE", "migration", "source_artifact", str(member["path"]), "error", "source artifact is absent from source commit")
    if not source_members:
        add("MIG-PROVENANCE-INCOMPLETE", "migration", "source_artifacts", "inventory:source_artifacts", "error", "source artifact set is empty")

    generated = {"status": "not-supplied", "mismatch_count": 0, "checked": [], "disposition": "not-applicable-to-disposable-shadow-candidate"}
    if generated_view_manifest_path:
        view_manifest = _read_json(generated_view_manifest_path, "MIG-GENERATED-VIEWS")
        checked = []
        mismatch = 0
        for entry in view_manifest.get("views") or []:
            if (
                not isinstance(entry, dict)
                or not entry.get("path")
                or not re.fullmatch(r"sha256:[0-9a-f]{64}", str(entry.get("digest") or ""))
            ):
                add("MIG-GENERATED-VIEW-MANIFEST", "migration", "generated_views", str(generated_view_manifest_path), "error", "generated-view manifest entry is invalid")
                mismatch += 1
                continue
            view_path = _under(candidate_root / str(entry["path"]), candidate_root)
            observed = sha256_file(view_path) if view_path.is_file() else None
            match = observed == entry["digest"]
            checked.append({"path": entry["path"], "expected_digest": entry["digest"], "observed_digest": observed, "match": match})
            if not match:
                add("MIG-GENERATED-VIEW-DRIFT", "migration", "generated_views", str(entry["path"]), "error", "generated view is missing or stale")
                mismatch += 1
        generated = {"status": "match" if mismatch == 0 else "mismatch", "mismatch_count": mismatch, "checked": checked, "disposition": None}

    comparisons = {}
    rules_by_comparison = {
        "ids": {
            "MIG-SOURCE-OMISSION",
            "MIG-ID-INFLATION",
            "MIG-DUPLICATE-SOURCE-ID",
            "MIG-DUPLICATE-CANDIDATE-ID",
            "MIG-CANDIDATE-ID-MISMATCH",
            "MIG-CANDIDATE-MANIFEST-DRIFT",
        },
        "states": {"MIG-STATE-DRIFT"},
        "edges": {"MIG-EDGE-DRIFT"},
        "criteria": {"MIG-CRITERIA-DRIFT"},
        "definition_of_done": {"MIG-DOD-DRIFT"},
        "refs": {"MIG-FABRICATED-REF", "MIG-REF-OMISSION"},
        "claims": {"MIG-CLAIM-OMISSION"},
        "archives": {"MIG-ARCHIVE-DRIFT"},
        "preserved_text": {"MIG-BYTE-DRIFT"},
        "provenance": {"MIG-PROVENANCE-INCOMPLETE", "MIG-SOURCE-ARTIFACT-TAMPER", "MIG-STALE-CANDIDATE", "MIG-SELF-BASELINED", "MIG-CANDIDATE-COMMIT-MISSING"},
    }
    for name, rules in rules_by_comparison.items():
        count = sum(1 for finding in findings if finding["rule"] in rules)
        comparisons[name] = {"status": "match" if count == 0 else "mismatch", "mismatch_count": count}
    comparisons["generated_views"] = generated

    if source_artifact_set_path and not source_artifact_set_path.is_file():
        raise MigrationReportError("MIG-SOURCE-ARTIFACT-SET", "source artifact-set path is not a file")
    if candidate_artifact_set_path and not candidate_artifact_set_path.is_file():
        raise MigrationReportError("MIG-CANDIDATE-ARTIFACT-SET", "candidate artifact-set path is not a file")
    source_identity = _artifact_identity(source_artifact_set_path, source_members, "source")
    candidate_identity = _artifact_identity(candidate_artifact_set_path, member_rows, "candidate")

    previous_ids: set[str] = set()
    previous_run_id: Optional[str] = None
    previous_digest: Optional[str] = None
    if previous_report_path:
        valid, detail = verify_report(previous_report_path)
        if not valid:
            raise MigrationReportError("MIG-PREVIOUS-REPORT-TAMPERED", detail)
        previous = _read_json(previous_report_path, "MIG-PREVIOUS-REPORT")
        previous_ids = {str(value.get("id")) for value in previous.get("findings") or [] if isinstance(value, dict)}
        previous_run_id = str(previous.get("run_id"))
        previous_digest = detail
    findings.sort(key=lambda value: (value["id"], value["rule"], value["source_locator"]))
    current_ids = {value["id"] for value in findings}
    unresolved_errors = [value["id"] for value in findings if value["severity"] == "error" and not value.get("disposition")]
    unresolved_warnings = [value["id"] for value in findings if value["severity"] == "warning" and not value.get("disposition")]

    root = Path(__file__).resolve().parents[2]
    tool_path = root / TOOL_REL
    schema_path = root / SCHEMA_REL
    report: dict = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "produced_at": produced_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "identity": {
            "producing_issue": PRODUCING_ISSUE,
            "source_commit": source_commit,
            "candidate_commit": candidate_commit,
            "source_artifact_set": source_identity,
            "candidate_artifact_set": candidate_identity,
            "tool": {"path": TOOL_REL, "version": TOOL_VERSION, "digest": sha256_file(tool_path)},
            "report_schema": {"path": SCHEMA_REL, "version": SCHEMA_VERSION, "digest": sha256_file(schema_path)},
            "report_json": {"path": f"provenance/migrations/issue-store/{run_id}/report.json"},
            "report_markdown": {"path": f"provenance/migrations/issue-store/{run_id}/report.md", "digest": ""},
        },
        "watermarks": {
            "baseline_commit": baseline,
            "latest_source_commit": latest,
            "candidate_source_commit": candidate_watermark,
            "stale": any(value["rule"] == "MIG-STALE-CANDIDATE" for value in findings),
            "self_baselined": any(value["rule"] == "MIG-SELF-BASELINED" for value in findings),
        },
        "summaries": {
            "source": _summary(source_items, source_raw_digests),
            "candidate": _summary(candidate_items, candidate_raw_digests),
        },
        "comparisons": comparisons,
        "findings": findings,
        "previous_run": {
            "run_id": previous_run_id,
            "report_digest": previous_digest,
            "added_finding_ids": sorted(current_ids - previous_ids),
            "retained_finding_ids": sorted(current_ids & previous_ids),
            "resolved_finding_ids": sorted(previous_ids - current_ids),
        },
        "decision": {
            "pass": not unresolved_errors and not unresolved_warnings,
            "unresolved_error_ids": sorted(unresolved_errors),
            "unresolved_warning_ids": sorted(unresolved_warnings),
            "cutover_blocked": bool(unresolved_errors or unresolved_warnings),
        },
        "integrity": {"algorithm": "sha256", "payload_digest": ""},
    }
    markdown = _render_markdown(report)
    report["identity"]["report_markdown"]["digest"] = sha256_bytes(markdown.encode("utf-8"))
    report["integrity"]["payload_digest"] = sha256_bytes(_integrity_payload(report))
    # Render again only to include the final decision/findings; markdown intentionally
    # excludes its own digest and the JSON payload digest, avoiding circular hashes.
    markdown = _render_markdown(report)

    run_root = _under(output_parent / run_id, output_parent)
    existing = run_root / "report.json"
    if existing.exists():
        valid, detail = verify_report(existing)
        if not valid:
            raise MigrationReportError("MIG-EXISTING-REPORT-TAMPERED", detail)
        existing_markdown = run_root / "report.md"
        retained_report = _read_json(existing, "MIG-EXISTING-REPORT")
        if not existing_markdown.is_file():
            recovered_markdown = _render_markdown(retained_report).encode("utf-8")
            expected_recovery_digest = str(
                retained_report.get("identity", {})
                .get("report_markdown", {})
                .get("digest")
            )
            if sha256_bytes(recovered_markdown) != expected_recovery_digest:
                raise MigrationReportError(
                    "MIG-EXISTING-REPORT-TAMPERED",
                    "retained report.md is missing and cannot be reconstructed from report.json",
                )
            _atomic_write(existing_markdown, recovered_markdown, output_parent)
        observed_markdown_digest = sha256_file(existing_markdown)
        expected_markdown_digest = str(
            retained_report.get("identity", {}).get("report_markdown", {}).get("digest")
        )
        if observed_markdown_digest != expected_markdown_digest:
            raise MigrationReportError(
                "MIG-EXISTING-REPORT-TAMPERED",
                f"report.md expected {expected_markdown_digest}, observed {observed_markdown_digest}",
            )
        if existing.read_bytes() != canonical_json(report).encode("utf-8"):
            raise MigrationReportError(
                "MIG-RUN-ID-COLLISION",
                "retained run id already names a different valid report",
            )
        return report
    _atomic_write(run_root / "report.md", markdown.encode("utf-8"), output_parent)
    # JSON is the commit marker for the retained pair.  Writing it last leaves
    # an interrupted markdown-only attempt safely retryable under the same ID.
    _atomic_write(existing, canonical_json(report).encode("utf-8"), output_parent)
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-report")
    parser.add_argument("--repo")
    parser.add_argument("--source-inventory")
    parser.add_argument("--candidate-root")
    parser.add_argument("--output-parent")
    parser.add_argument("--run-id")
    parser.add_argument("--candidate-commit")
    parser.add_argument("--source-artifact-set")
    parser.add_argument("--candidate-artifact-set")
    parser.add_argument("--migration-state")
    parser.add_argument("--generated-view-manifest")
    parser.add_argument("--previous-report")
    parser.add_argument("--produced-at")
    args = parser.parse_args(argv)
    if args.verify_report:
        valid, detail = verify_report(Path(args.verify_report))
        sys.stdout.write(canonical_json({"valid": valid, "detail": detail}))
        return 0 if valid else 2
    required = ("repo", "source_inventory", "candidate_root", "output_parent", "run_id", "candidate_commit")
    missing = [name for name in required if not getattr(args, name)]
    if missing:
        parser.error("missing required generation arguments: " + ", ".join(missing))
    try:
        report = generate_report(
            repo=Path(args.repo),
            source_inventory_path=Path(args.source_inventory),
            candidate_root=Path(args.candidate_root),
            output_parent=Path(args.output_parent),
            run_id=args.run_id,
            candidate_commit=args.candidate_commit,
            source_artifact_set_path=Path(args.source_artifact_set) if args.source_artifact_set else None,
            candidate_artifact_set_path=Path(args.candidate_artifact_set) if args.candidate_artifact_set else None,
            migration_state_path=Path(args.migration_state) if args.migration_state else None,
            generated_view_manifest_path=Path(args.generated_view_manifest) if args.generated_view_manifest else None,
            previous_report_path=Path(args.previous_report) if args.previous_report else None,
            produced_at=args.produced_at,
        )
        sys.stdout.write(canonical_json({"run_id": report["run_id"], "pass": report["decision"]["pass"], "report_digest": report["integrity"]["payload_digest"]}))
        return 0 if report["decision"]["pass"] else 2
    except MigrationReportError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
