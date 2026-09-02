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
SCHEMA_IDENTITIES = {
    "issue-item": ITEM_SCHEMA_REL,
    "issue-closure": CLOSURE_SCHEMA_REL,
    "migration-state": MIGRATION_SCHEMA_REL,
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


def _legacy_field(block: str, name: str) -> Optional[str]:
    for raw in block.splitlines():
        normalized = raw.strip().lstrip("-").strip().replace("**", "")
        key, separator, value = normalized.partition(":")
        if separator and key.strip().lower() == name.lower():
            return value.strip().strip("`")
    return None


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
    if "Acceptance: ✓" not in block and "**Acceptance:** ✓" not in block:
        _closure_finding(findings, "IMP-CLOSURE-ACCEPTANCE-MISSING", item_id, locator,
                         "terminal marker has no explicit legacy Acceptance record; closure not emitted")
        return None
    if PLACEHOLDER_EVIDENCE_RE.search(block):
        _closure_finding(findings, "IMP-CLOSURE-EVIDENCE-PLACEHOLDER", item_id, locator,
                         "terminal legacy block contains pending/local placeholder evidence")
        return None
    disposition = (_legacy_field(block, "Disposition") or ("completed" if marker == "x" else "wontfix")).lower()
    expected = "completed" if marker == "x" else "wontfix"
    if disposition != expected:
        _closure_finding(findings, "IMP-CLOSURE-DISPOSITION-CONFLICT", item_id, locator,
                         f"marker [{marker}] conflicts with disposition {disposition!r}")
        return None
    closed_by = _legacy_field(block, "Accepted by")
    closed_at = _legacy_field(block, "Accepted at")
    refs = sorted(set(FULL_COMMIT_RE.findall(block)))
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
    reason = _legacy_field(block, "Reason")
    if disposition == "wontfix" and not reason:
        missing.append("Reason")
    if missing:
        _closure_finding(findings, "IMP-CLOSURE-EVIDENCE-MISSING", item_id, locator,
                         "terminal legacy block lacks " + ", ".join(missing))
        return None
    evidence = [f"commit:{ref}" for ref in reachable] + [f"legacy:{locator}#acceptance"]
    closure = {
        "schema_version": "1.0", "item_id": item_id, "disposition": disposition,
        "closed_at": closed_at, "closed_by": closed_by,
        "criteria": [{"id": f"AC-{index:03d}", "status": "checked", "evidence": evidence}
                     for index in range(1, max(criteria_count, 1) + 1)],
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
    blocking = [f for f in findings if f["severity"] == "blocking"]
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
    }
    atomic_write(dest / "import-manifest.json", _canonical_json(manifest).encode("utf-8"), dest)
    atomic_write(dest / "import-findings.json", _canonical_json(findings).encode("utf-8"), dest)
    # Mutation guard: every written file remains under dest.
    for rel in written + claims_written + closures_written + ["import-manifest.json", "import-findings.json"]:
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


def _legacy_source_clean(repo: Path, source_commit: str, names: Sequence[str]) -> bool:
    paths = sorted(set(names))
    unstaged = subprocess.run(["git", "diff", "--quiet", source_commit, "--", *paths], cwd=repo, check=False)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet", source_commit, "--", *paths], cwd=repo, check=False)
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all", "--", *paths],
                            cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return unstaged.returncode == 0 and staged.returncode == 0 and status.returncode == 0 and not status.stdout


def _history_root(root: Path, repo: Path) -> Path:
    resolved, repo_resolved = root.expanduser().resolve(), repo.resolve()
    if resolved == repo_resolved:
        raise ImportErrorClosed("IMP-LIVE-ROOT", "refusing repository root as run history")
    for rel in ("issues", "provenance", ".runner"):
        live = (repo_resolved / rel).resolve()
        try:
            resolved.relative_to(live)
            raise ImportErrorClosed("IMP-LIVE-ROOT", f"refusing authoritative/control root {live}")
        except ValueError:
            pass
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
    history.mkdir(parents=True, exist_ok=True)
    final_root, lock_path = history / run_id, history / f".{run_id}.lock"
    try:
        lock_fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise ImportErrorClosed("IMP-RUN-EXISTS", f"run is already reserved: {run_id}") from exc
    os.close(lock_fd)
    staging = Path(tempfile.mkdtemp(prefix=f".{run_id}.staging-", dir=history))
    promoted = False
    try:
        if final_root.exists():
            raise ImportErrorClosed("IMP-RUN-EXISTS", f"run already exists: {run_id}")
        initial_source = _resolve_commit(repo, source_revision)
        watched_ref = source_ref or source_revision
        if _resolve_commit(repo, watched_ref) != initial_source:
            raise ImportErrorClosed("IMP-SOURCE-STALE",
                                    "source revision and watched source ref disagree at preparation")
        baseline = _resolve_commit(repo, baseline_commit) if baseline_commit else initial_source
        if subprocess.run(["git", "merge-base", "--is-ancestor", baseline, initial_source], cwd=repo,
                          check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
            raise ImportErrorClosed("IMP-BASELINE-REGRESSION", "baseline is not an ancestor of source")
        source, _ = _source_identity(repo, initial_source, named_files)
        names = [str(artifact["path"]) for artifact in source["artifacts"]]
        findings = []
        if not _legacy_source_clean(repo, initial_source, names):
            findings.append({"code": "dirty-legacy-source", "rule": "IMP-DIRTY-LEGACY-SOURCE",
                             "severity": "blocking", "message": "legacy source paths differ from watermark",
                             "locator": initial_source})
            source["working_tree_clean"] = False
        prior_states = _load_prior_states(history)
        prior = prior_states[-1][1] if prior_states else None
        if prior and prior["source"]["commit"] != initial_source:
            if subprocess.run(["git", "merge-base", "--is-ancestor", prior["source"]["commit"], initial_source],
                              cwd=repo, check=False, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL).returncode != 0:
                findings.append({"code": "source-watermark-regression", "rule": "IMP-SOURCE-WATERMARK-REGRESSION",
                                 "severity": "blocking", "message": "source is not a descendant of prior history",
                                 "locator": initial_source})
        importer_before = _importer_identity(repo)
        logical_root = f"_src/output/issue-migration/{run_id}/"
        candidate_root = staging / "issues"
        manifest = import_legacy(repo=repo, root=candidate_root, source_commit=initial_source,
                                 named_files=named_files, display_root=logical_root + "issues/",
                                 emit_closures=True)
        findings.extend(manifest["findings"])
        candidate_paths = list(manifest["written"])
        candidate_digest = _candidate_digest(candidate_root, candidate_paths)
        if candidate_digest != manifest["tree_digest"]:
            findings.append({"code": "candidate-digest-mismatch", "rule": "IMP-CANDIDATE-DIGEST-MISMATCH",
                             "severity": "blocking", "message": "candidate differs from manifest",
                             "locator": run_id})
        if before_compare:
            before_compare(staging)
        latest_source = _resolve_commit(repo, watched_ref)
        importer_after = _importer_identity(repo)
        observed_digest = _candidate_digest(candidate_root, candidate_paths)
        if latest_source != initial_source:
            findings.append({"code": "stale-candidate", "rule": "IMP-STALE-CANDIDATE", "severity": "blocking",
                             "message": "source ref drifted between preparation and promotion", "locator": watched_ref})
        if importer_after != importer_before:
            findings.append({"code": "importer-identity-drift", "rule": "IMP-IMPORTER-IDENTITY-DRIFT",
                             "severity": "blocking", "message": "importer or schema drifted before promotion",
                             "locator": TOOL_REL})
        if observed_digest != candidate_digest:
            findings.append({"code": "candidate-drift", "rule": "IMP-CANDIDATE-DRIFT", "severity": "blocking",
                             "message": "candidate bytes drifted after preparation", "locator": run_id})
        findings.sort(key=lambda f: (str(f.get("rule")), str(f.get("locator")), str(f.get("message"))))
        blocking = any(f.get("severity") == "blocking" for f in findings)
        previous_digest = _sha256_bytes(_canonical_json(prior).encode("utf-8")) if prior else None
        history_link = {"sequence": len(prior_states) + 1,
                        "previous_run_id": prior.get("run_id") if prior else None,
                        "previous_source_commit": prior.get("source", {}).get("commit") if prior else None,
                        "previous_state_digest": previous_digest}
        counts = {"items": len(manifest["items"]),
                  "closures": sum(1 for rel in candidate_paths if rel.endswith("/closure.json")),
                  "written": len(candidate_paths), "findings": len(findings)}
        candidate_identity = _sha256_bytes(
            f"migration-candidate@v1|{run_id}|{candidate_digest}".encode("utf-8")
        )
        state = {"schema": "migration-state@v1", "run_id": run_id,
                 "source": {key: source[key] for key in ("commit", "tree", "tree_digest", "files", "working_tree_clean")},
                 "importer": {"commit": importer_before["commit"], "digest": importer_before["digest"],
                              "schema_versions": importer_before["schema_versions"],
                              "schema_digests": importer_before["schema_digests"]},
                 "watermarks": {"baseline": baseline, "latest_source": latest_source, "candidate": initial_source},
                 "candidate": {"root": logical_root, "issues_root": logical_root + "issues/",
                               "reports_root": logical_root + "reports/", "tree": source["tree"],
                               "identity": candidate_identity, "tree_digest": candidate_digest,
                               "promotable": not blocking},
                 "phase": "rejected" if blocking else "promoted",
                 "status": "rejected" if blocking else "promoted", "counts": counts,
                 "finding_summary": _finding_summary(findings), "history": history_link,
                 "findings": _state_findings(findings)}
        report = {"schema": "issue-import-legacy-report@v1", "run_id": run_id, "source": source,
                  "importer": importer_before,
                  "candidate": {"logical_root": logical_root, "identity": candidate_identity,
                                "tree_digest": candidate_digest,
                                "observed_tree_digest": observed_digest, "paths": candidate_paths},
                  "counts": counts, "finding_summary": state["finding_summary"], "findings": findings,
                  "history": history_link, "status": state["status"]}
        atomic_write(staging / "reports/migration-state.json", _canonical_json(state).encode(), staging)
        atomic_write(staging / "reports/migration-report.json", _canonical_json(report).encode(), staging)
        if final_root.exists():
            raise ImportErrorClosed("IMP-RUN-EXISTS", f"run appeared during promotion: {run_id}")
        os.rename(staging, final_root)
        promoted = True
        return {"root": str(final_root), "state": state, "report": report}
    except Exception:
        if not promoted and staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
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
