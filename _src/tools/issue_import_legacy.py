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
import sys
import unicodedata
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

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
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)
    assert_under_root(path, root)


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
                            "severity": "warning",
                            "message": "REF is a typed pending placeholder; not fabricated as evidence",
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
                            "severity": "warning",
                            "message": f"{value} retained as unresolved placeholder",
                            "locator": f"{locator}:{value}",
                        }
                    )
            blobs_text = blobs[path][0].decode("utf-8") if path in blobs else ""
            # reconstruct block from inventory title_tail + inventory fields
            title = (item.get("title_tail") or "").strip()
            goal, scope, criteria, dod = extract_goal_scope_ac_dod(title + "\n", title)
            # Prefer source blob slice for the task block when available
            if path in blobs:
                lines = blobs_text.splitlines()
                start = max(int(line) - 1, 0)
                chunk = []
                for idx in range(start, len(lines)):
                    row = lines[idx]
                    if idx > start and row.startswith("- [") and "**" in row:
                        break
                    if idx > start and row.startswith("## "):
                        break
                    chunk.append(row)
                goal, scope, criteria, dod = extract_goal_scope_ac_dod("\n".join(chunk), title)
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
                "severity": "info",
                "message": "legacy claim blob copied without synthesizing claim.json",
                "locator": name,
            }
        )

    findings.sort(key=lambda f: (f["id"], f["rule"], f["locator"]))
    items_out.sort(key=lambda i: i["id"])
    written.sort()
    blocking = [f for f in findings if f["severity"] == "blocking"]
    tree_digest = hashlib.sha256()
    for rel in written + claims_written:
        payload = (dest / rel).read_bytes()
        tree_digest.update(rel.encode("utf-8"))
        tree_digest.update(b"\0")
        tree_digest.update(payload)
        tree_digest.update(b"\0")
    manifest = {
        "schema": IMPORTER_SCHEMA,
        "source_commit": commit,
        "importer_digest": _sha256_bytes(tool_bytes),
        "disposable_root": str(dest),
        "items": items_out,
        "written": written + sorted(claims_written),
        "findings": findings,
        "blocking": bool(blocking),
        "tree_digest": tree_digest.hexdigest(),
        "claim_json_emitted": False,
        "closure_json_emitted": False,
        "approval_emitted": False,
    }
    atomic_write(dest / "import-manifest.json", _canonical_json(manifest).encode("utf-8"), dest)
    atomic_write(dest / "import-findings.json", _canonical_json(findings).encode("utf-8"), dest)
    # Mutation guard: every written file remains under dest.
    for rel in written + claims_written + ["import-manifest.json", "import-findings.json"]:
        assert_under_root(dest / rel, dest)
    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--root", required=True, help="disposable destination root")
    parser.add_argument("--source-commit", help="40-hex source commit")
    parser.add_argument("--source-tree", help="directory of frozen blobs (tests)")
    parser.add_argument("--file", action="append", dest="files", help="named source file (repeatable)")
    args = parser.parse_args(argv)
    try:
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
