#!/usr/bin/env python3
"""Deterministic importer of committed TODO.md/DONE.md/claim blobs into a disposable root.

Task 0037-14. Writes only under the supplied root. Never writes live issues/,
provenance stores, runner queue, evidence trees, or generated views.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

TOOL_REL = "_src/tools/issue_import_legacy.py"
SCHEMA_VERSION = "1.0"
IMPORTER_SCHEMA = "issue-import-legacy@v1"

MARKER_STATE = {
    " ": "open",
    "p": "in_progress",
    "?": "open",
    "u": "blocked",
    "w": "closed",
    "x": "closed",
    "d": "open",
}

FORBIDDEN_NAMES = (
    "issues",
    "provenance",
    ".runner",
    "output",
    "_src/output",
    "issues/_views",
)

NO_CREDIT_LOCAL_REFS = frozenset(
    {
        "local-20260815-0021-06",
        "local-20260815-0021-07",
        "local-20260815-0021-08",
    }
)
ARCHIVED_FEATURE = "0021"
TASK_ID_RE = re.compile(r"^[0-9]{4}-[0-9]{2}(?:\.[0-9]{2})?$")
FEATURE_ID_RE = re.compile(r"^[0-9]{4}$")
AC_SPLIT_RE = re.compile(r";\s+")
RUN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{7,63}$")
FULL_COMMIT_RE = re.compile(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])")
PLACEHOLDER_EVIDENCE_RE = re.compile(r"(?:\bpending\b|\blocal-[A-Za-z0-9._-]+)", re.IGNORECASE)
MIGRATION_SCHEMA_REL = "issues/_schema/migration-state-v1.schema.json"
CLOSURE_SCHEMA_REL = "issues/_schema/issue-closure-v1.schema.json"
ITEM_SCHEMA_REL = "issues/_schema/issue-item-v1.schema.json"
DISPOSITION_SCHEMA_REL = "issues/_schema/migration-dispositions-v1.schema.json"
DISPOSITION_SCHEMA = "migration-dispositions@v1"
DISPOSITION_KINDS = (
    "retain-provenance-no-active-lease",
    "retain-provenance-no-evidence-credit",
    "source-repaired",
    "archive-excluded-from-active-migration",
)
DISPOSITION_MALFORMED_RULES = frozenset(
    {"IMP-FEATURE-HEADER-MALFORMED", "IMP-TASK-HEADER-MALFORMED"}
)
DISPOSITION_FIELD_RULES = frozenset(
    {"IMP-REF-PENDING", "IMP-REF-LOCAL-PLACEHOLDER", "IMP-REF-NO-EVIDENCE-CREDIT"}
)
DISPOSITION_ENTRY_REQUIRED = (
    "finding_id",
    "finding_rule",
    "source_locator",
    "item",
    "source_commit",
    "kind",
    "reason",
    "deciding_identity",
    "deciding_role",
    "authority_ref",
    "decided_at",
    "evidence_refs",
    "payload_digest",
    "signature_material",
    "signature_verified",
)
SCHEMA_IDENTITIES = {
    "issue-item": ITEM_SCHEMA_REL,
    "issue-closure": CLOSURE_SCHEMA_REL,
    "migration-state": MIGRATION_SCHEMA_REL,
    "migration-dispositions": DISPOSITION_SCHEMA_REL,
}


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _finding_id(rule: str, item: str, field: str, locator: str) -> str:
    payload = "|".join((rule, item, field, locator)).encode("utf-8")
    return "IMP-" + hashlib.sha256(payload).hexdigest()[:16]


def _load_inventory_module(repo: Path):
    path = repo / "provenance/migrations/issue-store/tools/issue_legacy_inventory.py"
    spec = importlib.util.spec_from_file_location("issue_legacy_inventory", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ImportErrorClosed(RuntimeError):
    """Fail-closed importer rejection."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def resolve_disposable_root(root: Path, repo: Path) -> Path:
    resolved = root.expanduser().resolve()
    repo_resolved = repo.resolve()
    live_roots = [
        repo_resolved / "issues",
        repo_resolved / "provenance",
        repo_resolved / ".runner",
        repo_resolved / "output",
        repo_resolved / "_src" / "output",
        repo_resolved / "issues" / "_views",
        repo_resolved / "TODO.md",
        repo_resolved / "DONE.md",
    ]
    for live in live_roots:
        try:
            resolved.relative_to(live)
            raise ImportErrorClosed(
                "IMP-LIVE-ROOT",
                f"refusing live/generated root {live}",
            )
        except ValueError:
            pass
        if resolved == live:
            raise ImportErrorClosed("IMP-LIVE-ROOT", f"refusing live/generated root {live}")
    if resolved == repo_resolved:
        raise ImportErrorClosed("IMP-LIVE-ROOT", "refusing repository root as import destination")
    if ".." in Path(root).parts:
        # still allowed if resolve stays under intended dest; confusion checked below
        pass
    return resolved


def assert_under_root(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ImportErrorClosed("IMP-PATH-ESCAPE", f"{path} is outside disposable root {root}") from exc
    return resolved


def quote_yaml_scalar(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def emit_frontmatter(fields: Mapping[str, object]) -> str:
    lines = ["---"]
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, str):
            lines.append(f"{key}: {quote_yaml_scalar(value)}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:")
                for item in value:
                    if isinstance(item, dict):
                        first = True
                        for dict_key, dict_val in item.items():
                            prefix = "  - " if first else "    "
                            lines.append(f"{prefix}{dict_key}: {quote_yaml_scalar(str(dict_val))}")
                            first = False
                    else:
                        lines.append(f"  - {quote_yaml_scalar(str(item))}")
        elif isinstance(value, dict):
            lines.append(f"{key}:")
            for inner_key, inner in value.items():
                lines.append(f"  {inner_key}: {quote_yaml_scalar(str(inner))}")
        else:
            lines.append(f"{key}: {quote_yaml_scalar(str(value))}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def extract_goal_scope_ac_dod(block: str, title: str) -> Tuple[str, str, List[str], str]:
    goal = title.strip() or "Imported from legacy backlog."
    ac_text = ""
    dod_text = ""
    rest_lines: List[str] = []
    collecting_ac = False
    for raw in block.splitlines():
        stripped = raw.strip()
        lower = stripped.lower()
        if lower.startswith("- **acceptance criteria:**") or lower.startswith("**acceptance criteria:**"):
            ac_text = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
            collecting_ac = True
            continue
        if collecting_ac:
            if stripped.startswith("- **") or stripped.startswith("## ") or (
                stripped.startswith("- [") and "**" in stripped
            ):
                collecting_ac = False
            elif stripped:
                ac_text = (ac_text + " " + stripped).strip()
                continue
        if lower.startswith("- **definition of done:**") or lower.startswith("**definition of done:**"):
            dod_text = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
            collecting_ac = False
        elif stripped.startswith("- [") and "**" in stripped:
            continue
        else:
            rest_lines.append(raw)
    scope = "\n".join(rest_lines).strip() or "Imported legacy text retained under source locators."
    criteria: List[str] = []
    ac_text = ac_text.strip().lstrip("*").strip()
    dod_text = dod_text.strip().lstrip("*").strip()
    if ac_text:
        parts = [p.strip().rstrip(".") for p in AC_SPLIT_RE.split(ac_text) if p.strip()]
        criteria.extend(parts)
    if not criteria:
        criteria = ["Preserve imported acceptance text from the legacy source."]
    if not dod_text:
        dod_text = "Imported item is represented under the disposable candidate root."
    return _nfc(goal), _nfc(scope), [_nfc(c) for c in criteria], _nfc(dod_text)


def item_path_for(item_id: str) -> Optional[str]:
    if FEATURE_ID_RE.fullmatch(item_id):
        return f"issues/{item_id}/index.md"
    if TASK_ID_RE.fullmatch(item_id) and "." in item_id:
        parent_task = item_id.rsplit(".", 1)[0]
        feature = item_id.split("-", 1)[0]
        return f"issues/{feature}/{item_id}/index.md"
    if TASK_ID_RE.fullmatch(item_id):
        feature = item_id.split("-", 1)[0]
        return f"issues/{feature}/{item_id}/index.md"
    return None


def level_parent(item_id: str) -> Tuple[str, Optional[str]]:
    if FEATURE_ID_RE.fullmatch(item_id):
        return "feature", None
    if "." in item_id:
        return "subtask", item_id.rsplit(".", 1)[0]
    return "task", item_id.split("-", 1)[0]


def render_item_markdown(
    *,
    item_id: str,
    state: str,
    source_locator: str,
    prerequisites: Sequence[str],
    goal: str,
    scope: str,
    criteria: Sequence[str],
    dod: str,
    labels: Sequence[str],
) -> str:
    level, parent = level_parent(item_id)
    fields: Dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "id": item_id,
        "level": level,
    }
    if parent:
        fields["parent"] = parent
    fields["state"] = state
    fields["visibility"] = "internal"
    if prerequisites:
        fields["prerequisites"] = list(prerequisites)
    if labels:
        fields["labels"] = list(labels)
    fields["work_type"] = "migration"
    fields["origin"] = {"kind": "migrated-from-legacy-todo", "source": source_locator}
    fields["authority"] = "shadow"
    body_criteria = []
    ac_lines = []
    for index, text in enumerate(criteria, 1):
        cid = f"AC-{index:03d}"
        body_criteria.append({"id": cid, "status": "active", "source": source_locator})
        ac_lines.append(f"- **{cid}** {text}")
    fields["criteria"] = [{"id": c["id"], "status": c["status"]} for c in body_criteria]
    front = emit_frontmatter(fields)
    parts = [
        front,
        "\n## Goal\n\n",
        goal,
        "\n\n## Scope\n\n",
        scope,
        "\n\n## Acceptance criteria\n\n",
        "\n".join(ac_lines),
        "\n\n## Definition of Done\n\n",
        dod,
        "\n",
    ]
    return "".join(parts)


def atomic_write(path: Path, data: bytes, root: Path) -> None:
    assert_under_root(path.parent, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    assert_under_root(tmp, root)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(tmp, flags, 0o644)
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("atomic write made no progress")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)
    assert_under_root(path, root)


def _source_block(blobs: Mapping[str, Tuple[bytes, str]], path: str, line: int) -> str:
    if path not in blobs:
        return ""
    lines = blobs[path][0].decode("utf-8").splitlines()
    start = max(int(line) - 1, 0)
    chunk: List[str] = []
    for index in range(start, len(lines)):
        row = lines[index]
        if index > start and row.startswith("- [") and "**" in row:
            break
        if index > start and row.startswith("## "):
            break
        chunk.append(row)
    return "\n".join(chunk)


def _normalized_legacy_field(raw: str) -> Tuple[str, str]:
    normalized = raw.strip().lstrip("-").strip().replace("**", "")
    key, separator, value = normalized.partition(":")
    if not separator:
        return "", ""
    return key.strip(), value.strip().strip("`")


def _legacy_field(block: str, name: str) -> Optional[str]:
    for raw in block.splitlines():
        key, value = _normalized_legacy_field(raw)
        if key.lower() == name.lower():
            return value
    return None


def _current_acceptance_section(block: str) -> Tuple[Optional[str], str]:
    lines = block.splitlines()
    starts = []
    for index, raw in enumerate(lines):
        key, value = _normalized_legacy_field(raw)
        if key.lower() == "acceptance":
            starts.append((index, value))
    if not starts:
        return None, ""
    index, status = starts[-1]
    return status, "\n".join(lines[index:])


POSITIVE_ACCEPTANCE_REF_FIELDS = frozenset(
    {"carrying commit", "review-decision commit", "review ref"}
)


def _positive_acceptance_ref_values(section: str) -> List[str]:
    """Return only typed refs from the current positive Acceptance record."""
    refs = []
    for raw in section.splitlines():
        key, value = _normalized_legacy_field(raw)
        if key.lower() not in POSITIVE_ACCEPTANCE_REF_FIELDS:
            continue
        match = FULL_COMMIT_RE.fullmatch(value)
        if match:
            refs.append(match.group(0))
    return sorted(set(refs))


def _criterion_evidence_values(section: str) -> Dict[str, List[str]]:
    evidence: Dict[str, List[str]] = {}
    pattern = re.compile(r"^criterion evidence (AC-[0-9]{3,})$", re.IGNORECASE)
    for raw in section.splitlines():
        key, value = _normalized_legacy_field(raw)
        match = pattern.fullmatch(key)
        if not match:
            continue
        criterion = match.group(1).upper()
        values = [part.strip().strip("`") for part in re.split(r"\s*[;,]\s*", value) if part.strip()]
        evidence.setdefault(criterion, []).extend(values)
    return {key: sorted(set(values)) for key, values in evidence.items()}


def _validated_criterion_evidence(
    *, repo: Path, source_commit: str, section: str, criteria_count: int,
    positive_refs: Sequence[str],
) -> Tuple[Optional[List[dict]], List[str]]:
    bindings = _criterion_evidence_values(section)
    criteria = []
    missing = []
    allowed_commits = set(positive_refs)
    for index in range(1, max(criteria_count, 1) + 1):
        criterion_id = f"AC-{index:03d}"
        valid = []
        for value in bindings.get(criterion_id, []):
            if value.startswith("commit:"):
                ref = value.removeprefix("commit:")
                if ref in allowed_commits:
                    valid.append(value)
            elif re.fullmatch(r"sha256:[0-9a-f]{64}", value):
                valid.append(value)
            elif value.startswith("path:"):
                rel = value.removeprefix("path:").split("#", 1)[0]
                if rel and not Path(rel).is_absolute() and ".." not in Path(rel).parts:
                    exists = subprocess.run(
                        ["git", "cat-file", "-e", f"{source_commit}:{rel}"], cwd=repo,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
                    )
                    if exists.returncode == 0:
                        valid.append(value)
        if not valid:
            missing.append(criterion_id)
        else:
            criteria.append({"id": criterion_id, "status": "checked", "evidence": sorted(set(valid))})
    return (criteria if not missing else None), missing


def _closure_finding(
    findings: List[dict], rule: str, item_id: str, locator: str, message: str
) -> None:
    findings.append(
        {
            "id": _finding_id(rule, item_id, "closure", locator),
            "code": rule.lower().replace("imp-", "").replace("_", "-"),
            "rule": rule,
            "item": item_id,
            "severity": "blocking",
            "message": message,
            "locator": locator,
        }
    )


def closure_from_legacy(
    *, repo: Path, source_commit: str, item: Mapping[str, object], block: str,
    criteria_count: int, findings: List[dict], locator: str,
) -> Optional[dict]:
    """Map an evidence-complete terminal legacy block without inventing credit."""
    item_id = str(item.get("id") or "")
    marker = str(item.get("marker") or "")
    if marker not in {"x", "w"}:
        return None
    acceptance_status, acceptance = _current_acceptance_section(block)
    if acceptance_status != "✓":
        _closure_finding(findings, "IMP-CLOSURE-ACCEPTANCE-MISSING", item_id, locator,
                         "terminal marker has no current positive legacy Acceptance record")
        return None
    if PLACEHOLDER_EVIDENCE_RE.search(acceptance):
        _closure_finding(findings, "IMP-CLOSURE-EVIDENCE-PLACEHOLDER", item_id, locator,
                         "current positive Acceptance contains pending/local placeholder evidence")
        return None
    disposition = (_legacy_field(acceptance, "Disposition") or ("completed" if marker == "x" else "wontfix")).lower()
    expected = "completed" if marker == "x" else "wontfix"
    if disposition != expected:
        _closure_finding(findings, "IMP-CLOSURE-DISPOSITION-CONFLICT", item_id, locator,
                         f"marker [{marker}] conflicts with disposition {disposition!r}")
        return None
    closed_by = _legacy_field(acceptance, "Accepted by")
    closed_at = _legacy_field(acceptance, "Accepted at")
    refs = _positive_acceptance_ref_values(acceptance)
    reachable = []
    for ref in refs:
        result = subprocess.run(["git", "merge-base", "--is-ancestor", ref, source_commit], cwd=repo,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if result.returncode == 0:
            reachable.append(ref)
    missing = []
    if not closed_by:
        missing.append("Accepted by")
    if not closed_at:
        missing.append("Accepted at")
    else:
        try:
            datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
        except ValueError:
            missing.append("valid ISO-8601 Accepted at")
    if not reachable:
        missing.append("reachable full commit evidence")
    reason = _legacy_field(acceptance, "Reason") or _legacy_field(block, "Reason")
    if disposition == "wontfix" and not reason:
        missing.append("Reason")
    if missing:
        _closure_finding(findings, "IMP-CLOSURE-EVIDENCE-MISSING", item_id, locator,
                         "terminal legacy block lacks " + ", ".join(missing))
        return None
    criteria, missing_criteria = _validated_criterion_evidence(
        repo=repo, source_commit=source_commit, section=acceptance,
        criteria_count=criteria_count, positive_refs=reachable,
    )
    if criteria is None:
        _closure_finding(
            findings, "IMP-CLOSURE-CRITERION-EVIDENCE-MISSING", item_id, locator,
            "current positive Acceptance lacks typed evidence for " + ", ".join(missing_criteria),
        )
        return None
    closure = {
        "schema_version": "1.0", "item_id": item_id, "disposition": disposition,
        "closed_at": closed_at, "closed_by": closed_by,
        "criteria": criteria,
        "commit_refs": reachable,
        "validation": [{"name": "legacy-acceptance-record", "result": "pass",
                        "evidence": f"legacy:{locator}#acceptance"}],
    }
    if reason:
        closure["reason"] = reason
    return closure


def load_blobs(inv, repo: Path, source_commit: Optional[str], source_tree: Optional[Path]):
    if source_tree is not None:
        return inv.load_tree_blobs(source_tree), None
    if not source_commit:
        raise ImportErrorClosed("IMP-SOURCE-MISSING", "source commit or --source-tree is required")
    blobs = inv.load_commit_blobs(repo, source_commit)
    return blobs, source_commit


def _blob_path_for_locator(locator: str) -> str:
    return locator.split(":", 1)[0]


def _digest_prefixed(raw: bytes) -> str:
    return "sha256:" + _sha256_bytes(raw)


def expected_finding_digests(finding: Mapping[str, object], blobs: Mapping[str, Tuple[bytes, object]]) -> Tuple[Optional[str], Optional[str]]:
    locator = str(finding["locator"])
    path = _blob_path_for_locator(locator)
    blob = blobs.get(path)
    blob_digest = _digest_prefixed(blob[0]) if blob is not None else None
    field_digest = None
    if str(finding.get("rule")) in DISPOSITION_FIELD_RULES:
        field_digest = _digest_prefixed(locator.encode("utf-8"))
    return blob_digest, field_digest


def disposition_payload_digest(entry: Mapping[str, object]) -> str:
    payload = {
        key: entry[key]
        for key in (
            "finding_id",
            "finding_rule",
            "source_locator",
            "item",
            "source_commit",
            "source_blob_digest",
            "referenced_field_digest",
            "kind",
            "reason",
            "deciding_identity",
            "deciding_role",
            "authority_ref",
            "decided_at",
            "evidence_refs",
            "archive_retention_justification",
            "parser_independent_archival_safe",
            "cannot_participate_in_active_state_reason",
        )
        if key in entry
    }
    return _digest_prefixed(_canonical_json(payload).encode("utf-8"))


def validate_disposition_document(document: Mapping[str, object]) -> None:
    if document.get("schema") != DISPOSITION_SCHEMA:
        raise ImportErrorClosed("DISP-MALFORMED", "schema must be migration-dispositions@v1")
    entries = document.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ImportErrorClosed("DISP-MALFORMED", "entries must be a non-empty array")
    extra = set(document) - {"schema", "entries"}
    if extra:
        raise ImportErrorClosed("DISP-MALFORMED", f"unknown document fields {sorted(extra)}")
    seen = set()
    for raw in entries:
        if not isinstance(raw, dict):
            raise ImportErrorClosed("DISP-MALFORMED", "entry must be an object")
        missing = [key for key in DISPOSITION_ENTRY_REQUIRED if key not in raw]
        if missing:
            raise ImportErrorClosed("DISP-MISSING", f"entry missing {missing}")
        unknown = set(raw) - set(DISPOSITION_ENTRY_REQUIRED) - {
            "source_blob_digest",
            "referenced_field_digest",
            "archive_retention_justification",
            "parser_independent_archival_safe",
            "cannot_participate_in_active_state_reason",
        }
        if unknown:
            raise ImportErrorClosed("DISP-MALFORMED", f"unknown entry fields {sorted(unknown)}")
        finding_id = raw["finding_id"]
        if finding_id in seen:
            raise ImportErrorClosed("DISP-DUPLICATE", f"duplicate finding_id {finding_id}")
        seen.add(finding_id)
        if not isinstance(finding_id, str) or not re.fullmatch(r"IMP-[0-9a-f]{16}", finding_id):
            raise ImportErrorClosed("DISP-MALFORMED", "invalid finding_id")
        if raw["kind"] not in DISPOSITION_KINDS:
            raise ImportErrorClosed("DISP-MALFORMED", f"unknown kind {raw['kind']!r}")
        if not str(raw.get("reason") or "").strip():
            raise ImportErrorClosed("DISP-MISSING", "reason is empty")
        if not isinstance(raw.get("evidence_refs"), list) or not raw["evidence_refs"]:
            raise ImportErrorClosed("DISP-MISSING", "evidence_refs must be non-empty")
        if ("source_blob_digest" in raw) == ("referenced_field_digest" in raw):
            raise ImportErrorClosed("DISP-MALFORMED", "exactly one of source_blob_digest or referenced_field_digest is required")
        identity = str(raw["deciding_identity"])
        if not re.match(r"^(agent|authority|legacy-authority):.+$", identity):
            raise ImportErrorClosed("DISP-UNVERIFIABLE", "deciding_identity is not an authority grammar")
        if raw.get("signature_verified") is not True:
            raise ImportErrorClosed("DISP-UNVERIFIABLE", "signature_verified must be true")
        if not str(raw.get("signature_material") or "").strip():
            raise ImportErrorClosed("DISP-UNVERIFIABLE", "signature_material missing")
        expected = disposition_payload_digest(raw)
        if raw["payload_digest"] != expected:
            raise ImportErrorClosed("DISP-UNVERIFIABLE", "payload_digest does not authenticate the entry")
        if raw["kind"] == "archive-excluded-from-active-migration":
            if not str(raw.get("archive_retention_justification") or "").strip():
                raise ImportErrorClosed("DISP-MALFORMED", "archive exclusion requires retention justification")
            if raw.get("parser_independent_archival_safe") is not True:
                raise ImportErrorClosed("DISP-MALFORMED", "archive exclusion requires parser-independent archival safety")
            if not str(raw.get("cannot_participate_in_active_state_reason") or "").strip():
                raise ImportErrorClosed("DISP-MALFORMED", "archive exclusion requires why the bytes cannot be active state")


def load_disposition_document(path: Path) -> dict:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ImportErrorClosed("DISP-MALFORMED", f"cannot read dispositions: {exc}") from exc
    if not isinstance(document, dict):
        raise ImportErrorClosed("DISP-MALFORMED", "dispositions document must be an object")
    validate_disposition_document(document)
    return document


def apply_dispositions(
    *,
    document: Mapping[str, object],
    findings: Sequence[Mapping[str, object]],
    blobs: Mapping[str, Tuple[bytes, object]],
    source_commit: Optional[str],
) -> dict:
    validate_disposition_document(document)
    blocking = [finding for finding in findings if finding.get("severity") == "blocking"]
    by_id = {str(finding["id"]): finding for finding in blocking}
    if len(by_id) != len(blocking):
        raise ImportErrorClosed("DISP-CONFLICT", "blocking findings are not uniquely identified")
    pairs = []
    for entry in document["entries"]:
        finding_id = entry["finding_id"]
        finding = by_id.get(finding_id)
        if finding is None:
            raise ImportErrorClosed("DISP-UNMATCHED", f"disposition does not match a blocking finding: {finding_id}")
        if entry["finding_rule"] != finding["rule"] or entry["source_locator"] != finding["locator"] or entry["item"] != finding["item"]:
            raise ImportErrorClosed("DISP-UNMATCHED", f"disposition identity diverges from finding {finding_id}")
        if source_commit and entry["source_commit"] != source_commit:
            raise ImportErrorClosed("DISP-WRONG-COMMIT", f"disposition commit is not the import source for {finding_id}")
        blob_digest, field_digest = expected_finding_digests(finding, blobs)
        if "referenced_field_digest" in entry:
            if field_digest is None or entry["referenced_field_digest"] != field_digest:
                raise ImportErrorClosed("DISP-WRONG-DIGEST", f"referenced-field digest mismatch for {finding_id}")
        else:
            if blob_digest is None or entry["source_blob_digest"] != blob_digest:
                raise ImportErrorClosed("DISP-WRONG-DIGEST", f"source-blob digest mismatch for {finding_id}")
        if entry["kind"] == "archive-excluded-from-active-migration" and finding["rule"] not in DISPOSITION_MALFORMED_RULES:
            raise ImportErrorClosed(
                "DISP-MALFORMED",
                "archive-excluded-from-active-migration is repair-first and only for malformed structural syntax",
            )
        pairs.append({
            "finding_id": finding_id,
            "rule": finding["rule"],
            "locator": finding["locator"],
            "item": finding["item"],
            "kind": entry["kind"],
            "result": "covered",
        })
    covered = {pair["finding_id"] for pair in pairs}
    if len(covered) != len(pairs):
        raise ImportErrorClosed("DISP-MANY-TO-ONE", "one disposition covered more than one finding")
    missing = sorted(set(by_id) - covered)
    if missing:
        raise ImportErrorClosed("DISP-MISSING", f"blocking findings lack dispositions: {missing}")
    pairs.sort(key=lambda pair: (pair["finding_id"], pair["rule"], pair["locator"]))
    return {
        "schema": "migration-disposition-coverage@v1",
        "disposition_manifest_digest": _digest_prefixed(_canonical_json(document).encode("utf-8")),
        "source_commit": source_commit,
        "pairs": pairs,
        "blocking_after_coverage": False,
        "closure_json_synthesized": False,
        "credit_granted": False,
    }


def classify_state(marker: str, findings: List[dict], item_id: str, locator: str) -> Optional[str]:
    if marker not in MARKER_STATE:
        findings.append(
            {
                "id": _finding_id("IMP-MARKER-UNDEFINED", item_id, "marker", locator),
                "code": "marker-undefined",
                "rule": "IMP-MARKER-UNDEFINED",
                "item": item_id,
                "severity": "blocking",
                "message": f"undefined marker [{marker}]",
                "locator": locator,
            }
        )
        return None
    state = MARKER_STATE[marker]
    if marker == "?":
        findings.append(
            {
                "id": _finding_id("IMP-INVESTIGATION-REQUIRED", item_id, "marker", locator),
                "code": "investigation-required",
                "rule": "IMP-INVESTIGATION-REQUIRED",
                "item": item_id,
                "severity": "warning",
                "message": "legacy [?] maps to open with investigation_required; no fabricated decision",
                "locator": locator,
            }
        )
    if marker == "d":
        findings.append(
            {
                "id": _finding_id("IMP-DEFERRED", item_id, "marker", locator),
                "code": "deferred-open",
                "rule": "IMP-DEFERRED",
                "item": item_id,
                "severity": "warning",
                "message": "legacy [d] maps to open without fabricating a claim",
                "locator": locator,
            }
        )
    return state


def import_legacy(
    *,
    repo: Path,
    root: Path,
    source_commit: Optional[str] = None,
    source_tree: Optional[Path] = None,
    named_files: Optional[Sequence[str]] = None,
    display_root: Optional[str] = None,
    emit_closures: bool = False,
    dispositions: Optional[Path] = None,
) -> dict:
    inv = _load_inventory_module(repo)
    dest = resolve_disposable_root(root, repo)
    dest.mkdir(parents=True, exist_ok=True)
    blobs, commit = load_blobs(inv, repo, source_commit, source_tree)
    if named_files:
        allowed = set(named_files)
        blobs = {k: v for k, v in blobs.items() if k in allowed}
        missing = [n for n in named_files if n not in blobs]
        if missing:
            raise ImportErrorClosed("IMP-SOURCE-MISSING", f"named files absent: {missing}")
    tool_bytes = (repo / TOOL_REL).read_bytes() if (repo / TOOL_REL).is_file() else Path(__file__).read_bytes()
    inventory = inv.inventory_from_blobs(
        blobs,
        source_commit=commit,
        run_id="import-legacy",
        produced_at="1970-01-01T00:00:00Z",
        tool_path=TOOL_REL,
        tool_digest="sha256:" + _sha256_bytes(tool_bytes),
    )
    findings: List[dict] = []
    written: List[str] = []
    seen_ids = set()
    items_out: List[dict] = []
    closures_written: List[str] = []

    for item in inventory["items"]:
        item_id = item.get("id")
        kind = item.get("kind")
        path = item.get("path") or ""
        line = item.get("line") or 0
        locator = f"{path}:{line}"
        if kind == "feature":
            if not item_id or not FEATURE_ID_RE.fullmatch(str(item_id)):
                findings.append(
                    {
                        "id": _finding_id("IMP-FEATURE-HEADER-MALFORMED", str(item_id), "header", locator),
                        "code": "malformed-feature",
                        "rule": "IMP-FEATURE-HEADER-MALFORMED",
                        "item": str(item_id),
                        "severity": "blocking",
                        "message": "Feature header lacks canonical four-digit ID",
                        "locator": locator,
                    }
                )
                continue
            if item_id in seen_ids:
                findings.append(
                    {
                        "id": _finding_id("IMP-ID-DUPLICATE", item_id, "id", locator),
                        "code": "duplicate-id",
                        "rule": "IMP-ID-DUPLICATE",
                        "item": item_id,
                        "severity": "blocking",
                        "message": "duplicate Feature ID; second occurrence not written",
                        "locator": locator,
                    }
                )
                continue
            seen_ids.add(item_id)
            labels = ["archived-not-accepted"] if item_id == ARCHIVED_FEATURE else []
            if item_id == ARCHIVED_FEATURE:
                findings.append(
                    {
                        "id": _finding_id("IMP-ARCHIVED-NOT-ACCEPTED", item_id, "archive", locator),
                        "code": "archived-not-accepted",
                        "rule": "IMP-ARCHIVED-NOT-ACCEPTED",
                        "item": item_id,
                        "severity": "warning",
                        "message": "Feature 0021 retained as archived-not-accepted with no evidence credit",
                        "locator": locator,
                    }
                )
            state = "closed" if path == "DONE.md" or item_id == ARCHIVED_FEATURE else "open"
            rel = item_path_for(item_id)
            md = render_item_markdown(
                item_id=item_id,
                state=state,
                source_locator=f"legacy:{locator}",
                prerequisites=[],
                goal=item.get("title") or item_id,
                scope="Imported Feature body is retained via source locators; child Tasks are separate items.",
                criteria=["Preserve Feature identity and archive classification from the legacy source."],
                dod="Feature identity, archive class, and locators match the source blobs.",
                labels=labels,
            )
            dest_path = dest / rel
            atomic_write(dest_path, md.encode("utf-8"), dest)
            written.append(rel)
            items_out.append({"id": item_id, "path": rel, "state": state, "locator": locator})
            continue

        if kind in {"task", "subtask", "malformed_task"}:
            if kind == "malformed_task" or not TASK_ID_RE.fullmatch(str(item_id)):
                findings.append(
                    {
                        "id": _finding_id("IMP-TASK-HEADER-MALFORMED", str(item_id), "header", locator),
                        "code": "malformed-task",
                        "rule": "IMP-TASK-HEADER-MALFORMED",
                        "item": str(item_id),
                        "severity": "blocking",
                        "message": "malformed Task header; no issue-item written",
                        "locator": locator,
                    }
                )
                continue
            if item_id in seen_ids:
                findings.append(
                    {
                        "id": _finding_id("IMP-ID-DUPLICATE", item_id, "id", locator),
                        "code": "duplicate-id",
                        "rule": "IMP-ID-DUPLICATE",
                        "item": item_id,
                        "severity": "blocking",
                        "message": "duplicate ID; second occurrence not written",
                        "locator": locator,
                    }
                )
                continue
            marker = item.get("marker", " ")
            state = classify_state(marker, findings, item_id, locator)
            if state is None:
                continue
            seen_ids.add(item_id)
            prereqs = []
            for edge in item.get("prerequisites") or []:
                target = edge.get("to")
                source = edge.get("from")
                if source == item_id and target and target != item_id:
                    prereqs.append(target)
            prereqs = sorted(set(prereqs))
            for ref in item.get("refs") or []:
                value = ref.get("value") or ""
                if value in NO_CREDIT_LOCAL_REFS:
                    findings.append(
                        {
                            "id": _finding_id("IMP-REF-NO-EVIDENCE-CREDIT", item_id, "ref", f"{locator}:{value}"),
                            "code": "no-evidence-credit",
                            "rule": "IMP-REF-NO-EVIDENCE-CREDIT",
                            "item": item_id,
                            "severity": "blocking",
                            "message": f"{value} receives no independent evidence credit",
                            "locator": f"{locator}:{value}",
                        }
                    )
                elif ref.get("kind") == "pending":
                    findings.append(
                        {
                            "id": _finding_id("IMP-REF-PENDING", item_id, "ref", locator),
                            "code": "unresolved-placeholder",
                            "rule": "IMP-REF-PENDING",
                            "item": item_id,
                            "severity": "blocking",
                            "message": "REF is a typed pending placeholder; explicit evidence disposition is required",
                            "locator": locator,
                        }
                    )
                elif ref.get("kind") == "local_placeholder":
                    findings.append(
                        {
                            "id": _finding_id("IMP-REF-LOCAL-PLACEHOLDER", item_id, "ref", f"{locator}:{value}"),
                            "code": "unresolved-placeholder",
                            "rule": "IMP-REF-LOCAL-PLACEHOLDER",
                            "item": item_id,
                            "severity": "blocking",
                            "message": f"{value} retained as unresolved placeholder requiring explicit disposition",
                            "locator": f"{locator}:{value}",
                        }
                    )
            # Reconstruct the item contract from inventory metadata and its exact source block.
            title = (item.get("title_tail") or "").strip()
            goal, scope, criteria, dod = extract_goal_scope_ac_dod(title + "\n", title)
            block = _source_block(blobs, path, int(line))
            if block:
                goal, scope, criteria, dod = extract_goal_scope_ac_dod(block, title)
            labels = []
            if item.get("parent_feature") == ARCHIVED_FEATURE or item_id.startswith(ARCHIVED_FEATURE + "-"):
                labels.append("archived-not-accepted")
            rel = item_path_for(item_id)
            md = render_item_markdown(
                item_id=item_id,
                state=state,
                source_locator=f"legacy:{locator}",
                prerequisites=prereqs,
                goal=goal,
                scope=scope,
                criteria=criteria,
                dod=dod,
                labels=labels,
            )
            dest_path = dest / rel
            atomic_write(dest_path, md.encode("utf-8"), dest)
            written.append(rel)
            items_out.append({"id": item_id, "path": rel, "state": state, "locator": locator})
            if emit_closures and marker in {"x", "w"}:
                if not commit:
                    _closure_finding(findings, "IMP-CLOSURE-SOURCE-NOT-COMMITTED", item_id, locator,
                                     "closure generation requires an exact committed source")
                else:
                    closure = closure_from_legacy(repo=repo, source_commit=commit, item=item,
                                                  block=block, criteria_count=len(criteria),
                                                  findings=findings, locator=locator)
                    if closure is not None:
                        closure_rel = str(Path(rel).parent / "closure.json")
                        atomic_write(dest / closure_rel, _canonical_json(closure).encode("utf-8"), dest)
                        closures_written.append(closure_rel)

    claims_written = []
    for claim in inventory.get("claims") or []:
        name = claim["path"]
        if name not in blobs:
            continue
        # Retain claim blobs as opaque copies; do not emit claim.json/closure.json.
        rel = f"legacy-claims/{name}"
        atomic_write(dest / rel, blobs[name][0], dest)
        claims_written.append(rel)
        findings.append(
            {
                "id": _finding_id("IMP-CLAIM-OPAQUE", name, "claim", name),
                "code": "claim-blob-retained",
                "rule": "IMP-CLAIM-OPAQUE",
                "item": str(claim.get("item") or name),
                "severity": "blocking",
                "message": "legacy claim blob copied opaquely; explicit disposition is required before promotion",
                "locator": name,
            }
        )

    findings.sort(key=lambda f: (f["id"], f["rule"], f["locator"]))
    items_out.sort(key=lambda i: i["id"])
    written.sort()
    closures_written.sort()
    coverage = None
    if dispositions is not None:
        document = load_disposition_document(Path(dispositions))
        coverage = apply_dispositions(
            document=document, findings=findings, blobs=blobs, source_commit=commit,
        )
    blocking = [f for f in findings if f["severity"] == "blocking"]
    if coverage is not None:
        blocking = []
    tree_digest = hashlib.sha256()
    for rel in sorted(written + claims_written + closures_written):
        payload = (dest / rel).read_bytes()
        tree_digest.update(rel.encode("utf-8"))
        tree_digest.update(b"\0")
        tree_digest.update(payload)
        tree_digest.update(b"\0")
    manifest = {
        "schema": IMPORTER_SCHEMA,
        "source_commit": commit,
        "importer_digest": _sha256_bytes(tool_bytes),
        "disposable_root": display_root if display_root is not None else str(dest),
        "items": items_out,
        "written": written + sorted(claims_written) + closures_written,
        "findings": findings,
        "blocking": bool(blocking),
        "tree_digest": tree_digest.hexdigest(),
        "claim_json_emitted": False,
        "closure_json_emitted": bool(closures_written),
        "approval_emitted": False,
        "disposition_coverage": coverage,
    }
    atomic_write(dest / "import-manifest.json", _canonical_json(manifest).encode("utf-8"), dest)
    atomic_write(dest / "import-findings.json", _canonical_json(findings).encode("utf-8"), dest)
    extras = ["import-manifest.json", "import-findings.json"]
    if coverage is not None:
        atomic_write(dest / "import-disposition-coverage.json", _canonical_json(coverage).encode("utf-8"), dest)
        history_path = dest / "import-disposition-runs.jsonl"
        history_line = _canonical_json({
            "schema": "migration-disposition-run@v1",
            "source_commit": commit,
            "disposition_manifest_digest": coverage["disposition_manifest_digest"],
            "coverage_digest": _digest_prefixed(_canonical_json(coverage).encode("utf-8")),
            "result": "covered",
        }).rstrip("\n")
        with history_path.open("a", encoding="utf-8") as stream:
            stream.write(history_line + "\n")
        extras.extend(["import-disposition-coverage.json", "import-disposition-runs.jsonl"])
    for rel in written + claims_written + closures_written + extras:
        assert_under_root(dest / rel, dest)
    return manifest


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        raise ImportErrorClosed("IMP-GIT", result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def _resolve_commit(repo: Path, revision: str) -> str:
    value = _git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}")
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ImportErrorClosed("IMP-SOURCE-MALFORMED", f"not a full commit: {revision}")
    return value


def _schema_identity(repo: Path) -> Tuple[Dict[str, str], Dict[str, str]]:
    versions, digests = {}, {}
    for name, rel in sorted(SCHEMA_IDENTITIES.items()):
        raw = (repo / rel).read_bytes()
        parsed = json.loads(raw.decode("utf-8"))
        versions[name] = str(parsed.get("title") or parsed.get("$id") or "unknown")
        digests[name] = _sha256_bytes(raw)
    return versions, digests


def _importer_identity(repo: Path) -> dict:
    path = repo / TOOL_REL
    raw = path.read_bytes() if path.is_file() else Path(__file__).read_bytes()
    commit = _git(repo, "log", "-1", "--format=%H", "--", TOOL_REL) or _git(repo, "rev-parse", "HEAD")
    versions, schema_digests = _schema_identity(repo)
    return {"commit": commit, "digest": _sha256_bytes(raw), "schema_versions": versions,
            "schema_digests": schema_digests}


def _source_identity(repo: Path, source_commit: str,
                     named_files: Optional[Sequence[str]]) -> Tuple[dict, Mapping[str, Tuple[bytes, str]]]:
    inv = _load_inventory_module(repo)
    blobs = inv.load_commit_blobs(repo, source_commit)
    if named_files:
        requested = list(dict.fromkeys(named_files))
        missing = [name for name in requested if name not in blobs]
        if missing:
            raise ImportErrorClosed("IMP-SOURCE-MISSING", f"named files absent: {missing}")
        blobs = {name: blobs[name] for name in requested}
    if not {"TODO.md", "DONE.md"}.issubset(blobs):
        raise ImportErrorClosed("IMP-SOURCE-MISSING", "TODO.md and DONE.md are required")
    digest = hashlib.sha256()
    artifacts = []
    for name, (raw, blob_digest) in sorted(blobs.items()):
        digest.update(name.encode("utf-8") + b"\0" + raw + b"\0")
        artifacts.append({"path": name, "blob": blob_digest, "sha256": _sha256_bytes(raw),
                          "size_bytes": len(raw)})
    return ({"commit": source_commit, "tree": _git(repo, "rev-parse", f"{source_commit}^{{tree}}"),
             "tree_digest": digest.hexdigest(), "files": ["TODO.md", "DONE.md", "claim-blobs"],
             "working_tree_clean": True, "artifacts": artifacts}, blobs)


def _source_pathspecs(named_files: Optional[Sequence[str]]) -> List[str]:
    if named_files:
        return sorted(set(named_files))
    return ["TODO.md", "DONE.md", ":(glob)TODO-*.md"]


def _legacy_source_clean(
    repo: Path, source_commit: str, named_files: Optional[Sequence[str]]
) -> bool:
    paths = _source_pathspecs(named_files)
    unstaged = subprocess.run(["git", "diff", "--quiet", source_commit, "--", *paths], cwd=repo, check=False)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet", source_commit, "--", *paths], cwd=repo, check=False)
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all", "--", *paths],
                            cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return unstaged.returncode == 0 and staged.returncode == 0 and status.returncode == 0 and not status.stdout


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _history_root(root: Path, repo: Path) -> Path:
    repo_resolved = repo.resolve()
    lexical = Path(os.path.abspath(os.path.expanduser(str(root))))
    resolved = root.expanduser().resolve()
    canonical = (repo_resolved / "_src/output/issue-migration").resolve()
    lexical_in_repo = _is_within(lexical, repo_resolved)
    resolved_in_repo = _is_within(resolved, repo_resolved)
    if lexical_in_repo or resolved_in_repo:
        if lexical != canonical or resolved != canonical:
            raise ImportErrorClosed(
                "IMP-LIVE-ROOT",
                "in-repository history root must be exactly _src/output/issue-migration without aliases",
            )
    return resolved


def _load_prior_states(history_root: Path) -> List[Tuple[Path, dict]]:
    states = []
    if not history_root.is_dir():
        return states
    for path in sorted(history_root.glob("*/reports/migration-state.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ImportErrorClosed("IMP-HISTORY-MALFORMED", f"cannot read prior state {path}") from exc
        if value.get("schema") != "migration-state@v1":
            raise ImportErrorClosed("IMP-HISTORY-MALFORMED", f"unexpected prior state {path}")
        states.append((path, value))
    states.sort(key=lambda entry: (int(entry[1].get("history", {}).get("sequence", 0)),
                                   str(entry[1].get("run_id", ""))))
    return states


def _candidate_digest(root: Path, paths: Sequence[str]) -> str:
    digest = hashlib.sha256()
    for rel in sorted(set(paths)):
        path = root / rel
        if not path.is_file():
            raise ImportErrorClosed("IMP-CANDIDATE-DRIFT", f"candidate path missing: {rel}")
        digest.update(rel.encode("utf-8") + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def _state_findings(findings: Sequence[Mapping[str, object]]) -> List[dict]:
    return [{"code": str(f.get("code") or f.get("rule") or "import-finding").lower().replace("_", "-"),
             "severity": str(f.get("severity") or "blocking"),
             "message": str(f.get("message") or "import finding")} for f in findings]


def _finding_summary(findings: Sequence[Mapping[str, object]]) -> dict:
    summary = {key: 0 for key in ("info", "warning", "error", "blocking")}
    for finding in findings:
        severity = str(finding.get("severity") or "blocking")
        summary[severity] = summary.get(severity, 0) + 1
    summary["total"] = len(findings)
    return summary


def run_migration(*, repo: Path, history_root: Path, run_id: str, source_revision: str,
                  source_ref: Optional[str] = None, baseline_commit: Optional[str] = None,
                  named_files: Optional[Sequence[str]] = None,
                  before_compare: Optional[Callable[[Path], None]] = None) -> dict:
    """Create one immutable production migration run under a non-authoritative history root."""
    repo = repo.resolve()
    if not RUN_ID_RE.fullmatch(run_id):
        raise ImportErrorClosed("IMP-RUN-ID", f"invalid run ID {run_id!r}")
    history = _history_root(history_root, repo)
    initial_source = _resolve_commit(repo, source_revision)
    watched_ref = source_ref or source_revision
    if _resolve_commit(repo, watched_ref) != initial_source:
        raise ImportErrorClosed(
            "IMP-SOURCE-STALE", "source revision and watched ref disagree before reservation"
        )
    baseline = _resolve_commit(repo, baseline_commit) if baseline_commit else initial_source
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", baseline, initial_source], cwd=repo,
        check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise ImportErrorClosed("IMP-BASELINE-REGRESSION", "baseline is not an ancestor of source")
    source, _ = _source_identity(repo, initial_source, named_files)
    importer_before = _importer_identity(repo)
    preparation_clean = _legacy_source_clean(repo, initial_source, named_files)

    history.mkdir(parents=True, exist_ok=True)
    final_root, lock_path = history / run_id, history / f".{run_id}.lock"
    if final_root.exists():
        raise ImportErrorClosed("IMP-RUN-EXISTS", f"run already exists: {run_id}")
    try:
        lock_fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise ImportErrorClosed("IMP-RUN-EXISTS", f"run is already reserved: {run_id}") from exc
    os.close(lock_fd)
    staging = Path(tempfile.mkdtemp(prefix=f".{run_id}.staging-", dir=history))
    promoted = False
    prior_states: List[Tuple[Path, dict]] = []
    prior = None
    findings: List[dict] = []
    manifest: Optional[dict] = None
    candidate_paths: List[str] = []
    empty_digest = _sha256_bytes(b"")
    candidate_digest = empty_digest
    observed_digest = empty_digest
    latest_source = initial_source
    source_after = source
    logical_root = f"_src/output/issue-migration/{run_id}/"

    def records(status: str, phase: str) -> Tuple[dict, dict]:
        ordered = sorted(
            findings,
            key=lambda finding: (
                str(finding.get("rule")), str(finding.get("locator")),
                str(finding.get("message")),
            ),
        )
        history_link = {
            "sequence": len(prior_states) + 1,
            "previous_run_id": prior.get("run_id") if prior else None,
            "previous_source_commit": prior.get("source", {}).get("commit") if prior else None,
            "previous_state_digest": (
                _sha256_bytes(_canonical_json(prior).encode("utf-8")) if prior else None
            ),
        }
        counts = {
            "items": len(manifest["items"]) if manifest else 0,
            "closures": sum(1 for rel in candidate_paths if rel.endswith("/closure.json")),
            "written": len(candidate_paths),
            "findings": len(ordered),
        }
        candidate_identity = _sha256_bytes(
            f"migration-candidate@v1|{run_id}|{candidate_digest}".encode("utf-8")
        )
        source_state = {
            key: source[key]
            for key in ("commit", "tree", "tree_digest", "files", "working_tree_clean")
        }
        state = {
            "schema": "migration-state@v1", "run_id": run_id, "source": source_state,
            "importer": {
                "commit": importer_before["commit"], "digest": importer_before["digest"],
                "schema_versions": importer_before["schema_versions"],
                "schema_digests": importer_before["schema_digests"],
            },
            "watermarks": {
                "baseline": baseline, "latest_source": latest_source,
                "candidate": initial_source,
            },
            "candidate": {
                "root": logical_root, "issues_root": logical_root + "issues/",
                "reports_root": logical_root + "reports/", "tree": source["tree"],
                "identity": candidate_identity, "tree_digest": candidate_digest,
                "promotable": status == "promoted",
            },
            "phase": phase, "status": status, "counts": counts,
            "finding_summary": _finding_summary(ordered), "history": history_link,
            "findings": _state_findings(ordered),
        }
        report = {
            "schema": "issue-import-legacy-report@v1", "run_id": run_id,
            "source": source, "source_compare": source_after, "importer": importer_before,
            "candidate": {
                "logical_root": logical_root, "identity": candidate_identity,
                "tree_digest": candidate_digest, "observed_tree_digest": observed_digest,
                "paths": candidate_paths,
            },
            "counts": counts, "finding_summary": state["finding_summary"],
            "findings": ordered, "history": history_link, "status": status,
        }
        return state, report

    def append_finding(finding: dict) -> None:
        identity = (finding.get("rule"), finding.get("locator"), finding.get("message"))
        if all(
            (current.get("rule"), current.get("locator"), current.get("message")) != identity
            for current in findings
        ):
            findings.append(finding)

    def compare_promotion_inputs() -> None:
        nonlocal latest_source, source_after, observed_digest
        latest_source = _resolve_commit(repo, watched_ref)
        source_after, _ = _source_identity(repo, latest_source, named_files)
        comparison_clean = _legacy_source_clean(repo, latest_source, named_files)
        source_after["working_tree_clean"] = comparison_clean
        source["working_tree_clean"] = preparation_clean and comparison_clean
        importer_after = _importer_identity(repo)
        observed_digest = _candidate_digest(staging / "issues", candidate_paths)
        comparable_keys = ("commit", "tree", "tree_digest", "artifacts")
        if any(source_after[key] != source[key] for key in comparable_keys):
            append_finding({
                "code": "stale-candidate", "rule": "IMP-STALE-CANDIDATE",
                "severity": "blocking", "message": "full source identity drifted before promotion",
                "locator": watched_ref,
            })
        if not comparison_clean:
            append_finding({
                "code": "dirty-legacy-source-drift",
                "rule": "IMP-DIRTY-LEGACY-SOURCE-DRIFT", "severity": "blocking",
                "message": "staged, unstaged, or untracked source paths drifted after preparation",
                "locator": watched_ref,
            })
        if importer_after != importer_before:
            append_finding({
                "code": "importer-identity-drift", "rule": "IMP-IMPORTER-IDENTITY-DRIFT",
                "severity": "blocking", "message": "importer or schema drifted before promotion",
                "locator": TOOL_REL,
            })
        if observed_digest != candidate_digest:
            append_finding({
                "code": "candidate-drift", "rule": "IMP-CANDIDATE-DRIFT",
                "severity": "blocking", "message": "candidate bytes drifted after preparation",
                "locator": run_id,
            })

    def retain(status: str, phase: str, *, discard_candidate: bool) -> dict:
        nonlocal promoted
        if discard_candidate:
            shutil.rmtree(staging / "issues", ignore_errors=True)
            candidate_paths.clear()
        shutil.rmtree(staging / "reports", ignore_errors=True)
        state, report = records(status, phase)
        atomic_write(staging / "reports/migration-state.json", _canonical_json(state).encode(), staging)
        atomic_write(staging / "reports/migration-report.json", _canonical_json(report).encode(), staging)
        if status == "promoted":
            compare_promotion_inputs()
            if any(finding.get("severity") == "blocking" for finding in findings):
                status = phase = "rejected"
                shutil.rmtree(staging / "reports", ignore_errors=True)
                state, report = records(status, phase)
                atomic_write(
                    staging / "reports/migration-state.json", _canonical_json(state).encode(), staging
                )
                atomic_write(
                    staging / "reports/migration-report.json", _canonical_json(report).encode(), staging
                )
        if final_root.exists():
            raise ImportErrorClosed("IMP-RUN-EXISTS", f"run appeared during promotion: {run_id}")
        os.rename(staging, final_root)
        promoted = True
        return {"root": str(final_root), "state": state, "report": report}

    try:
        prior_states = _load_prior_states(history)
        prior = prior_states[-1][1] if prior_states else None
        source["working_tree_clean"] = preparation_clean
        if not preparation_clean:
            findings.append({
                "code": "dirty-legacy-source", "rule": "IMP-DIRTY-LEGACY-SOURCE",
                "severity": "blocking", "message": "legacy source paths differ at preparation",
                "locator": initial_source,
            })
        if prior and prior["source"]["commit"] != initial_source:
            if subprocess.run(
                ["git", "merge-base", "--is-ancestor", prior["source"]["commit"], initial_source],
                cwd=repo, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            ).returncode != 0:
                findings.append({
                    "code": "source-watermark-regression",
                    "rule": "IMP-SOURCE-WATERMARK-REGRESSION", "severity": "blocking",
                    "message": "source is not a descendant of prior history",
                    "locator": initial_source,
                })
        candidate_root = staging / "issues"
        manifest = import_legacy(
            repo=repo, root=candidate_root, source_commit=initial_source,
            named_files=named_files, display_root=logical_root + "issues/", emit_closures=True,
        )
        findings.extend(manifest["findings"])
        candidate_paths = list(manifest["written"])
        candidate_digest = _candidate_digest(candidate_root, candidate_paths)
        observed_digest = candidate_digest
        if candidate_digest != manifest["tree_digest"]:
            findings.append({
                "code": "candidate-digest-mismatch", "rule": "IMP-CANDIDATE-DIGEST-MISMATCH",
                "severity": "blocking", "message": "candidate differs from manifest",
                "locator": run_id,
            })
        if before_compare:
            before_compare(staging)

        compare_promotion_inputs()
        blocking = any(finding.get("severity") == "blocking" for finding in findings)
        return retain("rejected" if blocking else "promoted",
                      "rejected" if blocking else "promoted", discard_candidate=False)
    except Exception as exc:
        code = exc.code if isinstance(exc, ImportErrorClosed) else "IMP-POST-RESERVATION-FAILURE"
        findings.append({
            "code": code.lower().replace("imp-", "").replace("_", "-"),
            "rule": code, "severity": "blocking",
            "message": f"post-reservation failure retained: {exc}", "locator": run_id,
        })
        try:
            latest_source = _resolve_commit(repo, watched_ref)
            source_after, _ = _source_identity(repo, latest_source, named_files)
            source_after["working_tree_clean"] = _legacy_source_clean(
                repo, latest_source, named_files
            )
        except Exception:
            latest_source = initial_source
            source_after = source
        if staging.exists() and not final_root.exists():
            return retain("interrupted", "interrupted", discard_candidate=True)
        raise
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--root", required=True, help="disposable destination root")
    parser.add_argument("--source-commit", help="40-hex source commit")
    parser.add_argument("--source-tree", help="directory of frozen blobs (tests)")
    parser.add_argument("--file", action="append", dest="files", help="named source file (repeatable)")
    parser.add_argument("--run-id", help="production mode; --root is immutable history root")
    parser.add_argument("--source-ref", help="production source CAS ref")
    parser.add_argument("--baseline-commit", help="production initial source watermark")
    parser.add_argument("--dispositions", help="migration-dispositions@v1 document (hermetic/tooling only)")
    args = parser.parse_args(argv)
    try:
        if args.run_id:
            if not args.source_commit or args.source_tree:
                raise ImportErrorClosed("IMP-CLI", "--run-id requires --source-commit and forbids --source-tree")
            result = run_migration(repo=Path(args.repo), history_root=Path(args.root), run_id=args.run_id,
                                   source_revision=args.source_commit, source_ref=args.source_ref,
                                   baseline_commit=args.baseline_commit, named_files=args.files)
            state = result["state"]
            sys.stdout.write(_canonical_json({"run_id": state["run_id"],
                                              "tree_digest": state["candidate"]["tree_digest"],
                                              "status": state["status"],
                                              "blocking": bool(state["finding_summary"]["blocking"])}))
            return 2 if state["status"] != "promoted" else 0
        manifest = import_legacy(
            repo=Path(args.repo),
            root=Path(args.root),
            source_commit=args.source_commit,
            source_tree=Path(args.source_tree) if args.source_tree else None,
            named_files=args.files,
            dispositions=Path(args.dispositions) if args.dispositions else None,
        )
        sys.stdout.write(_canonical_json({"tree_digest": manifest["tree_digest"], "blocking": manifest["blocking"]}))
        return 2 if manifest["blocking"] else 0
    except ImportErrorClosed as exc:
        print(exc, file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"IMP-FAILURE: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
