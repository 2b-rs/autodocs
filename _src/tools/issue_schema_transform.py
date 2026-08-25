#!/usr/bin/env python3
"""Versioned shadow schema transforms (Task 0037-15.02).

Fixture-only adjacent pair: ``issue-item@v1-draft`` → ``issue-item@v1``.
No production schema bump. Input is immutable; output is a fresh root.
Mismatch versus a clean ``issue_import_legacy`` run is a blocking finding,
never accepted representation drift.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

TOOL_REL = "_src/tools/issue_schema_transform.py"
FROM_SCHEMA = "issue-item@v1-draft"
TO_SCHEMA = "issue-item@v1"
LOGICAL_FROM = "v0"
LOGICAL_TO = "v1"
ADJACENT = ((FROM_SCHEMA, TO_SCHEMA),)
DRAFT_SCHEMA_VERSION = "1.0-draft"
V1_SCHEMA_VERSION = "1.0"
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")

DRAFT_KEYS = frozenset(
    {
        "schema",
        "schema_version",
        "id",
        "level",
        "parent",
        "state",
        "visibility",
        "prerequisites",
        "labels",
        "work_type",
        "origin",
        "authority",
        "goal",
        "scope",
        "criteria",
        "definition_of_done",
        "source_locator",
    }
)

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


IMP = _load("issue_import_legacy", ROOT / "_src/tools/issue_import_legacy.py")


class TransformError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def tool_digest(tool_path: Optional[Path] = None) -> str:
    path = tool_path or (ROOT / TOOL_REL)
    return "sha256:" + _sha256_hex(path.read_bytes())


def finding_id(rule: str, item: str, field: str, locator: str) -> str:
    payload = "|".join((rule, item, field, locator)).encode("utf-8")
    return "UPG-" + hashlib.sha256(payload).hexdigest()[:16]


def tree_digest(files: Mapping[str, bytes]) -> str:
    h = hashlib.sha256()
    for rel in sorted(files):
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(files[rel])
        h.update(b"\0")
    return "sha256:" + h.hexdigest()


def assert_under_root(path: Path, root: Path) -> None:
    resolved = path.resolve()
    root_res = root.resolve()
    if resolved != root_res and root_res not in resolved.parents:
        raise TransformError("TRN-SCOPE", f"{path} escapes {root}")


def refuse_live_roots(root: Path, repo: Path) -> Path:
    resolved = root.expanduser().resolve()
    repo_resolved = repo.resolve()
    live = [
        repo_resolved / "issues",
        repo_resolved / "provenance",
        repo_resolved / ".runner",
        repo_resolved / "output",
        repo_resolved / "_src" / "output",
        repo_resolved / "TODO.md",
        repo_resolved / "DONE.md",
    ]
    for forbidden in live:
        try:
            resolved.relative_to(forbidden)
            raise TransformError("TRN-LIVE", f"refusing live root {forbidden}")
        except ValueError:
            pass
        if resolved == forbidden:
            raise TransformError("TRN-LIVE", f"refusing live root {forbidden}")
    return resolved


def load_draft_items(input_root: Path) -> Tuple[List[dict], Dict[str, bytes]]:
    items: List[dict] = []
    files: Dict[str, bytes] = {}
    items_dir = input_root / "items"
    if not items_dir.is_dir():
        raise TransformError("TRN-INPUT", f"missing items/ under {input_root}")
    for path in sorted(items_dir.rglob("*.json")):
        rel = path.relative_to(input_root).as_posix()
        raw = path.read_bytes()
        files[rel] = raw
        try:
            obj = json.loads(raw.decode("utf-8"))
        except ValueError as exc:
            raise TransformError("TRN-INPUT", f"invalid JSON {rel}: {exc}") from exc
        if not isinstance(obj, dict):
            raise TransformError("TRN-INPUT", f"non-object {rel}")
        obj["_locator"] = rel
        items.append(obj)
    if not items:
        raise TransformError("TRN-INPUT", "no draft items")
    return items, files


def map_draft_to_v1(draft: Mapping[str, Any]) -> Tuple[Optional[dict], Optional[dict]]:
    locator = str(draft.get("_locator") or draft.get("id") or "unknown")
    extra = set(draft.keys()) - DRAFT_KEYS - {"_locator"}
    extra = {k for k in extra if draft.get(k) not in (None, "", [], {})}
    if extra:
        return None, {
            "id": finding_id("upgrade-lossy-transform", str(draft.get("id") or ""), ",".join(sorted(extra)), locator),
            "code": "upgrade-lossy-transform",
            "severity": "blocking",
            "item": str(draft.get("id") or ""),
            "message": f"unmapped draft fields: {sorted(extra)}",
            "locator": locator,
        }
    schema = draft.get("schema")
    if schema != FROM_SCHEMA:
        return None, {
            "id": finding_id("transform-unknown-version", str(draft.get("id") or ""), "schema", locator),
            "code": "transform-unknown-version",
            "severity": "blocking",
            "item": str(draft.get("id") or ""),
            "message": f"item schema {schema!r} is not {FROM_SCHEMA}",
            "locator": locator,
        }
    ver = draft.get("schema_version")
    if ver != DRAFT_SCHEMA_VERSION:
        return None, {
            "id": finding_id("transform-unknown-version", str(draft.get("id") or ""), "schema_version", locator),
            "code": "transform-unknown-version",
            "severity": "blocking",
            "item": str(draft.get("id") or ""),
            "message": f"item schema_version {ver!r} is not {DRAFT_SCHEMA_VERSION}",
            "locator": locator,
        }
    item_id = draft.get("id")
    if not isinstance(item_id, str):
        return None, {
            "id": finding_id("transform-lossy-transform", "", "id", locator),
            "code": "upgrade-lossy-transform",
            "severity": "blocking",
            "item": "",
            "message": "missing id",
            "locator": locator,
        }
    criteria = draft.get("criteria") or []
    if not isinstance(criteria, list) or any(not isinstance(c, str) for c in criteria):
        return None, {
            "id": finding_id("upgrade-lossy-transform", item_id, "criteria", locator),
            "code": "upgrade-lossy-transform",
            "severity": "blocking",
            "item": item_id,
            "message": "criteria must be a list of strings",
            "locator": locator,
        }
    mapped = {
        "schema": TO_SCHEMA,
        "schema_version": V1_SCHEMA_VERSION,
        "id": item_id,
        "level": draft.get("level"),
        "state": draft.get("state"),
        "visibility": draft.get("visibility") or "internal",
        "prerequisites": list(draft.get("prerequisites") or []),
        "labels": list(draft.get("labels") or []),
        "work_type": draft.get("work_type") or "migration",
        "origin": draft.get("origin")
        or {"kind": "migrated-from-legacy-todo", "source": draft.get("source_locator") or locator},
        "authority": draft.get("authority") or "shadow",
        "goal": draft.get("goal") or "",
        "scope": draft.get("scope") or "",
        "criteria": list(criteria),
        "definition_of_done": draft.get("definition_of_done") or "",
        "source_locator": draft.get("source_locator") or locator,
    }
    if draft.get("parent"):
        mapped["parent"] = draft["parent"]
    return mapped, None


def semantic_view(item: Mapping[str, Any]) -> dict:
    return {
        "id": item.get("id"),
        "level": item.get("level"),
        "parent": item.get("parent"),
        "state": item.get("state"),
        "prerequisites": list(item.get("prerequisites") or []),
        "labels": list(item.get("labels") or []),
        "goal": item.get("goal") or "",
        "scope": item.get("scope") or "",
        "criteria": list(item.get("criteria") or []),
        "definition_of_done": item.get("definition_of_done") or "",
    }


def parse_imported_markdown(text: str) -> dict:
    """Extract semantic fields from importer-rendered index.md."""
    if not text.startswith("---"):
        raise TransformError("TRN-PARSE", "missing front matter")
    rest = text[3:]
    end = rest.find("\n---")
    if end < 0:
        raise TransformError("TRN-PARSE", "unterminated front matter")
    fm = rest[:end]
    body = rest[end + 4 :]
    data: Dict[str, Any] = {}
    current_list: Optional[str] = None
    current_dict: Optional[str] = None
    for line in fm.splitlines():
        if line.startswith("  - ") and current_list:
            data[current_list].append(line[4:].strip().strip('"'))
            continue
        current_list = None
        if ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            val = val.strip()
            if val == "":
                if key in {"prerequisites", "labels"}:
                    data[key] = []
                    current_list = key
                else:
                    current_dict = key
                    data[key] = {}
            elif val == "[]":
                data[key] = []
            else:
                data[key] = val.strip('"')
                current_dict = None
        elif line.startswith("  ") and current_dict:
            ik, _, iv = line.strip().partition(":")
            data[current_dict][ik.strip()] = iv.strip().strip('"')

    def section(name: str) -> str:
        marker = f"## {name}"
        idx = body.find(marker)
        if idx < 0:
            return ""
        chunk = body[idx + len(marker) :]
        nxt = chunk.find("\n## ")
        if nxt >= 0:
            chunk = chunk[:nxt]
        return chunk.strip()

    ac_raw = section("Acceptance criteria")
    criteria = []
    for line in ac_raw.splitlines():
        if line.startswith("- **AC-"):
            rest_line = line.split("**", 2)[-1].strip()
            criteria.append(rest_line)
    return {
        "id": data.get("id"),
        "level": data.get("level"),
        "parent": data.get("parent"),
        "state": data.get("state"),
        "prerequisites": list(data.get("prerequisites") or []),
        "labels": list(data.get("labels") or []),
        "goal": section("Goal"),
        "scope": section("Scope"),
        "criteria": criteria,
        "definition_of_done": section("Definition of Done"),
    }


def write_v1_item(mapped: Mapping[str, Any], dest: Path) -> str:
    item_id = str(mapped["id"])
    rel = IMP.item_path_for(item_id)
    if rel is None:
        raise TransformError("TRN-ID", f"cannot path {item_id}")
    md = IMP.render_item_markdown(
        item_id=item_id,
        state=str(mapped["state"]),
        source_locator=str(mapped.get("source_locator") or ""),
        prerequisites=list(mapped.get("prerequisites") or []),
        goal=str(mapped.get("goal") or ""),
        scope=str(mapped.get("scope") or ""),
        criteria=list(mapped.get("criteria") or []),
        dod=str(mapped.get("definition_of_done") or ""),
        labels=list(mapped.get("labels") or []),
    )
    dest_path = dest / rel
    IMP.atomic_write(dest_path, md.encode("utf-8"), dest)
    json_rel = rel.replace("index.md", "item.json")
    payload = {k: v for k, v in mapped.items() if k != "source_locator"}
    IMP.atomic_write(dest / json_rel, _canonical_json(payload).encode("utf-8"), dest)
    return rel


def compare_clean_import(output_root: Path, clean_import_root: Path) -> List[dict]:
    findings: List[dict] = []
    out_mds = {p.relative_to(output_root).as_posix(): p for p in output_root.rglob("index.md")}
    cln_mds = {p.relative_to(clean_import_root).as_posix(): p for p in clean_import_root.rglob("index.md")}
    keys = sorted(set(out_mds) | set(cln_mds))
    for rel in keys:
        if rel not in out_mds or rel not in cln_mds:
            findings.append(
                {
                    "id": finding_id("upgrade-representation-drift", rel, "path", rel),
                    "code": "upgrade-representation-drift",
                    "severity": "blocking",
                    "item": rel,
                    "message": "item present on only one side of clean-import comparison",
                    "locator": rel,
                }
            )
            continue
        left = semantic_view(parse_imported_markdown(out_mds[rel].read_text(encoding="utf-8")))
        right = semantic_view(parse_imported_markdown(cln_mds[rel].read_text(encoding="utf-8")))
        if left != right:
            findings.append(
                {
                    "id": finding_id("upgrade-representation-drift", str(left.get("id") or rel), "semantic", rel),
                    "code": "upgrade-representation-drift",
                    "severity": "blocking",
                    "item": str(left.get("id") or rel),
                    "message": "transformed candidate diverges from clean import at target schema",
                    "locator": rel,
                }
            )
    return findings


def transform(
    *,
    repo: Path,
    input_root: Path,
    output_parent: Path,
    from_schema: str,
    to_schema: str,
    run_id: str,
    clean_import_root: Optional[Path] = None,
    source_commit: Optional[str] = None,
    crash_after: Optional[int] = None,
    crash_hook: Optional[Callable[[int], None]] = None,
) -> dict:
    repo = repo.resolve()
    input_root = input_root.resolve()
    output_parent = refuse_live_roots(output_parent, repo)
    if not RUN_ID_RE.fullmatch(run_id):
        raise TransformError("TRN-RUN-ID", f"invalid run_id {run_id}")
    if (from_schema, to_schema) not in ADJACENT:
        if from_schema == TO_SCHEMA and to_schema == FROM_SCHEMA:
            raise TransformError("transform-downgrade-rejected", f"{from_schema} → {to_schema} is not an upgrade")
        raise TransformError(
            "transform-unknown-version",
            f"no declared adjacent transform {from_schema} → {to_schema}",
        )

    input_items, input_files = load_draft_items(input_root)
    input_digest = tree_digest(input_files)
    input_snapshot = {rel: hashlib.sha256(raw).digest() for rel, raw in input_files.items()}

    dest = output_parent / run_id
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    assert_under_root(dest, output_parent)

    findings: List[dict] = []
    mapped_items: List[dict] = []
    written = 0
    try:
        for draft in input_items:
            mapped, finding = map_draft_to_v1(draft)
            if finding:
                findings.append(finding)
                continue
            assert mapped is not None
            write_v1_item(mapped, dest)
            mapped_items.append(mapped)
            written += 1
            if crash_hook:
                crash_hook(written)
            if crash_after is not None and written >= crash_after:
                raise TransformError("transform-crash", f"injected crash after {written} items")
    except TransformError as exc:
        if exc.code == "transform-crash":
            marker = dest / "CRASHED"
            marker.write_text(exc.message + "\n", encoding="utf-8")
            return {
                "schema": "upgrade-record@v1",
                "upgrade_run_id": run_id,
                "source_version": LOGICAL_FROM,
                "target_version": LOGICAL_TO,
                "from_schema": from_schema,
                "to_schema": to_schema,
                "tool_digest": tool_digest(),
                "source_tree_digest": input_digest,
                "status": "blocked",
                "blocking_findings": ["transform-crash"],
                "findings": [
                    {
                        "id": finding_id("transform-crash", run_id, "crash", run_id),
                        "code": "transform-crash",
                        "severity": "blocking",
                        "message": exc.message,
                    }
                ],
                "output_root": str(dest),
                "promotable": False,
            }
        raise

    if clean_import_root is not None:
        findings.extend(compare_clean_import(dest, Path(clean_import_root)))

    for rel, digest in input_snapshot.items():
        live = (input_root / rel).read_bytes()
        if hashlib.sha256(live).digest() != digest:
            raise TransformError("TRN-IMMUTABLE", f"input mutated: {rel}")

    blocking = [f for f in findings if f.get("severity") == "blocking"]
    out_files = {p.relative_to(dest).as_posix(): p.read_bytes() for p in dest.rglob("*") if p.is_file()}
    out_digest = tree_digest(out_files) if out_files else "sha256:" + ("0" * 64)
    members = []
    commit = source_commit or ("0" * 40)
    if source_commit and not COMMIT_RE.fullmatch(source_commit):
        raise TransformError("TRN-COMMIT", "source_commit must be 40-hex")
    for rel in sorted(out_files):
        raw = out_files[rel]
        members.append(
            {
                "path": rel,
                "digest": "sha256:" + _sha256_hex(raw),
                "size_bytes": len(raw),
                "media_type": "application/json" if rel.endswith(".json") else "text/markdown",
                "source_commit": commit if COMMIT_RE.fullmatch(commit) else "0" * 40,
            }
        )
    artifact_set = {
        "schema_version": "1.0",
        "classification": "internal",
        "environment": "synthetic",
        "from_schema": from_schema,
        "to_schema": to_schema,
        "tool_digest": tool_digest(),
        "members": members,
    }
    record = {
        "schema": "upgrade-record@v1",
        "upgrade_run_id": run_id,
        "source_version": LOGICAL_FROM,
        "target_version": LOGICAL_TO,
        "from_schema": from_schema,
        "to_schema": to_schema,
        "tool_digest": tool_digest(),
        "source_tree_digest": input_digest,
        "status": "blocked" if blocking else "validated",
        "blocking_findings": sorted({str(f["code"]) for f in blocking}),
        "findings": sorted(findings, key=lambda f: f.get("id", "")),
        "item_ids": [m["id"] for m in mapped_items],
        "output_root": str(dest),
        "promotable": not blocking,
    }
    if not blocking:
        record["output_tree_digest"] = out_digest
    IMP.atomic_write(dest / "upgrade-record.json", _canonical_json(record).encode("utf-8"), dest)
    IMP.atomic_write(dest / "artifact-set.json", _canonical_json(artifact_set).encode("utf-8"), dest)
    return record


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--output-parent", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--from-schema", default=FROM_SCHEMA)
    parser.add_argument("--to-schema", default=TO_SCHEMA)
    parser.add_argument("--clean-import-root")
    parser.add_argument("--source-commit")
    parser.add_argument("--crash-after", type=int)
    args = parser.parse_args(argv)
    try:
        record = transform(
            repo=Path(args.repo),
            input_root=Path(args.input_root),
            output_parent=Path(args.output_parent),
            from_schema=args.from_schema,
            to_schema=args.to_schema,
            run_id=args.run_id,
            clean_import_root=Path(args.clean_import_root) if args.clean_import_root else None,
            source_commit=args.source_commit,
            crash_after=args.crash_after,
        )
        sys_stdout = __import__("sys").stdout
        sys_stdout.write(_canonical_json({"status": record["status"], "promotable": record["promotable"]}))
        return 2 if record["status"] != "validated" else 0
    except TransformError as exc:
        print(exc, file=__import__("sys").stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
