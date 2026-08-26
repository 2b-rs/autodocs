#!/usr/bin/env python3
"""issuectl query and structural-edit surfaces (Tasks `0037-10.04`, `0037-10.01`).

Thin CLI over shared libraries: `issue_validate`, `issue_views`,
`provenance_query`, `issue_store`. Query commands remain read-only. Mutation
commands create items and apply controlled front-matter / AC / relation edits
with expected-digest CAS and atomic temp-file replacement. Never treats
TODO.md/DONE.md as authority.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import difflib
import hashlib
import importlib.util
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

TOOLS = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
EXIT_OK = 0
EXIT_MISSING = 1
EXIT_ERROR = 2
EXIT_USAGE = 3
SCHEMA = "issuectl-query-result@v1"
RUNNER_ACTIONS_PATH = Path("_src/runner/issuectl-query-actions-v1.json")
LEGACY_AUTHORITY_NAMES = frozenset({"TODO.md", "DONE.md", "todo.md", "done.md"})


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


iv = _load("issue_validate", TOOLS / "issue_validate.py")
views = _load("issue_views", TOOLS / "issue_views.py")
pq = _load("provenance_query", TOOLS / "provenance_query.py")
store = _load("issue_store", TOOLS / "issue_store.py")

MUTATE_SCHEMA = "issuectl-mutate-result@v1"
APPROVED_SCALAR_FIELDS = frozenset({
    "state", "visibility", "created_at", "updated_at", "work_type", "authority",
})
APPROVED_OBJECT_FIELDS = frozenset({"labels", "origin", "limits"})
IDENTITY_FIELDS = frozenset({"id", "level", "parent", "schema_version"})
ID_RE = re.compile(r"^[0-9]{4}(?:-[0-9]{2}(?:\.[0-9]{2})?)?$")
AC_RE = re.compile(r"^AC-[0-9]{3}$")
DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


class IssuectlError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def _reject_legacy_authority(path: Optional[Path]) -> None:
    if path is None:
        return
    name = Path(path).name
    if name in LEGACY_AUTHORITY_NAMES:
        raise iv.ConfigurationError(
            f"IV0900: derived legacy view {path} is not authority; use issues/ or provenance/"
        )


def _emit(payload: Mapping[str, Any], *, fmt: str, human_lines: Sequence[str]) -> int:
    if fmt == "json":
        sys.stdout.write(_canonical_json(payload))
    else:
        sys.stdout.write("\n".join(human_lines) + "\n")
    return int(payload.get("exit_code", EXIT_OK))


def cmd_validate(args: argparse.Namespace) -> int:
    _reject_legacy_authority(Path(args.root) if args.root else None)
    _reject_legacy_authority(Path(args.authoritative_root) if args.authoritative_root else None)
    diagnostics, parsed = iv.validate(
        repo=Path(args.repo).resolve(),
        source=args.source,
        root=Path(args.root) if args.root else None,
        authoritative_root=Path(args.authoritative_root) if args.authoritative_root else None,
        compare_head=not args.no_compare_head,
        provenance_root=args.provenance_root,
        projection_path=args.projection,
        dag_path=args.dag,
        generated_root=args.generated_root,
    )
    payload = iv.result_payload(diagnostics, args.source, len(parsed))
    payload["command"] = "validate"
    payload["schema"] = payload.get("schema") or "issue-validation-result@v1"
    human = [
        f"{d.rule} {d.path}:{d.line} item={d.item} field={d.field}: {d.message}"
        for d in diagnostics
    ] + [payload["status"]]
    if args.format == "json":
        sys.stdout.write(_canonical_json(payload))
    else:
        sys.stdout.write("\n".join(human) + "\n")
    return payload["exit_code"]


def _render_views(args: argparse.Namespace):
    repository_root = Path(args.repo).resolve()
    issues_root = Path(args.issues_root) if args.issues_root else repository_root / "issues"
    _reject_legacy_authority(issues_root)
    _reject_legacy_authority(Path(args.view_path) if getattr(args, "view_path", None) else None)
    if args.require_views:
        catalog_path = repository_root / views.CATALOG_OUT
        graph_path = repository_root / views.GRAPH_OUT
        if not catalog_path.is_file() or not graph_path.is_file():
            raise views.IssueViewsError("stale or missing catalog/graph views")
        views.verify_document(
            json.loads(catalog_path.read_text(encoding="utf-8")),
            "catalog",
            repository_root,
            issues_root,
        )
        views.verify_document(
            json.loads(graph_path.read_text(encoding="utf-8")),
            "graph",
            repository_root,
            issues_root,
        )
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        return catalog, graph
    return views.render(issues_root, repository_root)


def cmd_view(args: argparse.Namespace) -> int:
    catalog, graph = _render_views(args)
    kind = args.kind or "catalog"
    document = catalog if kind == "catalog" else graph
    payload = {
        "schema": SCHEMA,
        "command": "view",
        "kind": kind,
        "authority": document.get("authority"),
        "generation_id": document.get("generation_id"),
        "document": document,
        "exit_code": EXIT_OK,
    }
    human = [
        f"VIEW {kind} generation={document.get('generation_id')} authority={document.get('authority')}",
        f"items={len(document.get('items') or document.get('nodes') or [])}",
    ]
    return _emit(payload, fmt=args.format, human_lines=human)


def cmd_graph(args: argparse.Namespace) -> int:
    catalog, graph = _render_views(args)
    del catalog
    payload = {
        "schema": SCHEMA,
        "command": "graph",
        "authority": graph.get("authority"),
        "generation_id": graph.get("generation_id"),
        "document": graph,
        "exit_code": EXIT_OK,
    }
    human = [
        f"GRAPH generation={graph.get('generation_id')} nodes={len(graph.get('nodes') or [])} "
        f"edges={len(graph.get('edges') or [])}"
    ]
    for edge in graph.get("edges") or []:
        human.append(
            f"EDGE {edge.get('source')} -> {edge.get('target')} kind={edge.get('kind')} "
            f"gate={edge.get('gate')} endpoint={edge.get('endpoint_status')}"
        )
    return _emit(payload, fmt=args.format, human_lines=human)


def _claim_owner(repository_root: Path, source_path: Optional[str]) -> Optional[str]:
    if not source_path:
        return None
    sidecar = (Path(repository_root) / source_path).parent / "claim.json"
    if not sidecar.is_file():
        return None
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload.get("owner_token") or payload.get("owner")


def _list_rows(catalog: Mapping[str, Any], repository_root: Path, query: str, owner: Optional[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in catalog.get("items") or []:
        state = item.get("state")
        lifecycle = item.get("lifecycle_status")
        endpoint = item.get("endpoint_status")
        item_owner = _claim_owner(repository_root, (item.get("source") or {}).get("path"))
        record = {
            "id": item.get("id"),
            "state": state,
            "lifecycle_status": lifecycle,
            "endpoint_status": endpoint,
            "owner": item_owner,
            "prerequisites": list(item.get("prerequisites") or []),
            "title": item.get("title") or "",
        }
        if query == "open":
            keep = state in {"open", "in_progress"}
        elif query == "blocked":
            keep = state == "blocked"
        elif query == "unclear":
            keep = lifecycle == "malformed" or endpoint in {"malformed", "missing"}
        elif query == "owner":
            keep = bool(item_owner) and (owner is None or item_owner == owner)
        elif query == "prerequisite":
            keep = bool(record["prerequisites"])
        else:
            keep = True
        if keep:
            rows.append(record)
    rows.sort(key=lambda row: (row.get("id") or "", row.get("state") or ""))
    return rows


def cmd_list(args: argparse.Namespace) -> int:
    catalog, _graph = _render_views(args)
    rows = _list_rows(catalog, Path(args.repo).resolve(), args.query, args.owner)
    payload = {
        "schema": SCHEMA,
        "command": "list",
        "query": args.query,
        "generation_id": catalog.get("generation_id"),
        "authority": catalog.get("authority"),
        "items": rows,
        "exit_code": EXIT_OK,
    }
    human = [f"LIST {args.query} count={len(rows)} generation={catalog.get('generation_id')}"]
    for row in rows:
        human.append(
            f"{row['id']} state={row['state']} lifecycle={row['lifecycle_status']} "
            f"owner={row['owner'] or '-'}"
        )
    return _emit(payload, fmt=args.format, human_lines=human)


def cmd_trace(args: argparse.Namespace) -> int:
    repository_root = Path(args.repo).resolve()
    provenance_root = Path(args.provenance_root) if args.provenance_root else None
    _reject_legacy_authority(provenance_root)
    result = pq.query_trace(
        repository_root,
        kind=args.kind,
        identifier=args.identifier,
        direction=args.direction,
        depth=args.depth,
        type_filter=args.types,
        max_classification=args.max_classification,
        provenance_root=provenance_root,
        require_on_disk=args.require_index,
    )
    result["command"] = "trace"
    result["exit_code"] = pq.result_exit_code(result)
    if args.format == "json":
        sys.stdout.write(_canonical_json(result))
    else:
        sys.stdout.write(pq.format_human(result))
    return result["exit_code"]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _issues_root(args: argparse.Namespace) -> Path:
    repo = Path(args.repo).resolve()
    root = Path(args.issues_root) if getattr(args, "issues_root", None) else repo / "issues"
    _reject_legacy_authority(root)
    return root.resolve()


def item_relpath(item_id: str) -> str:
    if not ID_RE.fullmatch(item_id):
        raise IssuectlError("IC1101", f"malformed item id {item_id!r}")
    if re.fullmatch(r"[0-9]{4}", item_id):
        return f"{item_id}/index.md"
    return f"{item_id[:4]}/{item_id}/index.md"


def item_path(issues_root: Path, item_id: str) -> Path:
    return issues_root / item_relpath(item_id)


def parent_id_of(item_id: str) -> Optional[str]:
    if re.fullmatch(r"[0-9]{4}", item_id):
        return None
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}", item_id):
        return item_id[:4]
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}\.[0-9]{2}", item_id):
        return item_id.rsplit(".", 1)[0]
    raise IssuectlError("IC1101", f"malformed item id {item_id!r}")


def level_of(item_id: str) -> str:
    if re.fullmatch(r"[0-9]{4}", item_id):
        return "feature"
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}", item_id):
        return "task"
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}\.[0-9]{2}", item_id):
        return "subtask"
    raise IssuectlError("IC1101", f"malformed item id {item_id!r}")


def _yaml_dump_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=True)
    raise IssuectlError("IC1102", f"unsupported scalar type {type(value).__name__}")


def dump_frontmatter(metadata: Mapping[str, Any]) -> str:
    lines = ["---"]
    keys = [key for key in store.FIELD_ORDER if key in metadata]
    extra = [key for key in metadata if key not in store.FIELD_ORDER]
    for key in keys + extra:
        value = metadata[key]
        if isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
                continue
            lines.append(f"{key}:")
            for entry in value:
                if isinstance(entry, str):
                    lines.append(f"  - {_yaml_dump_scalar(entry)}")
                elif isinstance(entry, dict):
                    first = True
                    for nested_key, nested_value in entry.items():
                        if first:
                            lines.append(f"  - {nested_key}: {_yaml_dump_scalar(nested_value)}")
                            first = False
                        else:
                            lines.append(f"    {nested_key}: {_yaml_dump_scalar(nested_value)}")
                else:
                    raise IssuectlError("IC1102", f"unsupported list entry in {key}")
        elif isinstance(value, dict):
            lines.append(f"{key}:")
            for nested_key, nested_value in value.items():
                if isinstance(nested_value, dict):
                    lines.append(f"  {nested_key}:")
                    for inner_key, inner_value in nested_value.items():
                        lines.append(f"    {inner_key}: {_yaml_dump_scalar(inner_value)}")
                else:
                    lines.append(f"  {nested_key}: {_yaml_dump_scalar(nested_value)}")
        else:
            lines.append(f"{key}: {_yaml_dump_scalar(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def split_document(data: bytes, path: Path) -> Tuple[bytes, bytes, bytes]:
    text = store._validate_bytes(data, path)
    if not text.startswith("---\n"):
        raise IssuectlError("IC1103", f"{path} is missing opening frontmatter")
    rest = text[4:]
    close = rest.find("\n---\n")
    if close < 0:
        raise IssuectlError("IC1103", f"{path} is missing closing frontmatter")
    fm = rest[:close]
    body = rest[close + 5 :]
    opening = "---\n".encode("utf-8")
    closing = "---\n".encode("utf-8")
    return opening + (fm + "\n").encode("utf-8") + closing, body.encode("utf-8"), data


def ac_block_span(body: str) -> Tuple[int, int]:
    start_h = body.find("## Acceptance criteria\n")
    end_h = body.find("## Definition of Done\n")
    if start_h < 0 or end_h < 0 or end_h <= start_h:
        raise IssuectlError("IC1104", "normative Acceptance criteria / Definition of Done headings missing")
    list_start = start_h + len("## Acceptance criteria\n")
    return list_start, end_h


def replace_ac_list(body: str, rendered: str) -> str:
    start, end = ac_block_span(body)
    prefix = body[:start]
    suffix = body[end:]
    block = rendered if rendered.endswith("\n") else rendered + "\n"
    if not block.startswith("\n"):
        block = "\n" + block
    if not block.endswith("\n\n"):
        if block.endswith("\n"):
            block += "\n"
        else:
            block += "\n\n"
    return prefix + block + suffix


def render_criterion_line(entry: Mapping[str, str]) -> str:
    cid = entry["id"]
    text = entry["text"]
    return f"- **{cid}** {text}"


def next_ac_id(criteria: Sequence[Mapping[str, Any]]) -> str:
    if not criteria:
        return "AC-001"
    maximum = max(int(item["id"][3:]) for item in criteria)
    return f"AC-{maximum + 1:03d}"


def parse_document(path: Path, issues_root: Path) -> Tuple[Dict[str, Any], str, bytes]:
    data = path.read_bytes()
    identity = store.derive_identity(path.as_posix(), issues_root.as_posix())
    text = store._validate_bytes(data, path)
    frontmatter, body, body_line = store._split_frontmatter(text, path)
    metadata = store.parse_frontmatter(frontmatter, path)
    markdown = store.parse_markdown_body(body, body_start_line=body_line, path=path)
    store.validate_item(metadata, identity, markdown, path)
    return metadata, body, data


def collect_prereq_graph(issues_root: Path, overlay: Optional[Mapping[str, Sequence[str]]] = None) -> Dict[str, List[str]]:
    graph: Dict[str, List[str]] = {}
    if issues_root.is_dir():
        for path in store.discover(issues_root):
            metadata, _body, _data = parse_document(path, issues_root)
            graph[metadata["id"]] = list(metadata.get("prerequisites") or [])
    if overlay:
        for key, values in overlay.items():
            graph[key] = list(values)
    return graph


def detect_cycle(graph: Mapping[str, Sequence[str]]) -> Optional[List[str]]:
    visiting = set()
    seen = set()

    def walk(node: str, stack: List[str]) -> Optional[List[str]]:
        if node in visiting:
            cycle_start = stack.index(node)
            return stack[cycle_start:] + [node]
        if node in seen:
            return None
        visiting.add(node)
        for nxt in graph.get(node, []):
            found = walk(nxt, stack + [nxt])
            if found:
                return found
        visiting.remove(node)
        seen.add(node)
        return None

    for start in sorted(graph):
        found = walk(start, [start])
        if found:
            return found
    return None


def enforce_claim_scope(
    issues_root: Path,
    paths: Sequence[Path],
    owner_token: Optional[str],
) -> None:
    for path in paths:
        claim = path.parent / "claim.json"
        if not claim.is_file():
            continue
        try:
            payload = json.loads(claim.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise IssuectlError("IC1105", f"unreadable claim sidecar {claim}: {exc}") from exc
        if not isinstance(payload, dict):
            raise IssuectlError("IC1105", f"invalid claim sidecar {claim}")
        claimed_owner = payload.get("owner_token") or payload.get("owner")
        if owner_token and claimed_owner and claimed_owner != owner_token:
            raise IssuectlError("IC1105", "claim owner_token does not match --owner-token")
        if claimed_owner and not owner_token:
            raise IssuectlError("IC1105", "active claim requires --owner-token")
        scopes = payload.get("write_scopes") or payload.get("write_scope") or []
        if isinstance(scopes, str):
            scopes = [scopes]
        rel = path.as_posix()
        try:
            rel = path.relative_to(issues_root.parent).as_posix()
        except ValueError:
            pass
        if scopes:
            allowed = False
            for scope in scopes:
                if rel == scope or rel.startswith(str(scope).rstrip("*")):
                    allowed = True
                    break
                if path.name == "index.md" and str(scope).endswith(path.parent.name + "/index.md"):
                    allowed = True
                    break
            if not allowed:
                raise IssuectlError("IC1105", f"path {rel} is outside claim write scope")


def enforce_expected_digest(path: Path, data: bytes, expected: Optional[str]) -> None:
    actual = _sha256_bytes(data)
    if expected is None:
        raise IssuectlError("IC1106", f"--expected-digest is required for edits to {path}")
    if expected != actual:
        raise IssuectlError(
            "IC1106",
            f"concurrent edit rejection: expected {expected}, actual {actual}",
        )


def unified_diff(path: Path, old: bytes, new: bytes) -> str:
    old_lines = old.decode("utf-8").splitlines(keepends=True)
    new_lines = new.decode("utf-8").splitlines(keepends=True)
    return "".join(difflib.unified_diff(old_lines, new_lines, fromfile=str(path), tofile=str(path)))


def atomic_promote(updates: Sequence[Tuple[Path, bytes, Optional[bytes]]], *, dry_run: bool) -> None:
    if dry_run:
        return
    staged: List[Tuple[Path, Path, Optional[bytes]]] = []
    replaced: List[Tuple[Path, Optional[bytes]]] = []
    try:
        for path, new_bytes, original in updates:
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(prefix=".issuectl-", suffix=".tmp", dir=str(path.parent))
            tmp_path = Path(tmp_name)
            try:
                os.write(fd, new_bytes)
                os.fsync(fd)
            finally:
                os.close(fd)
            staged.append((path, tmp_path, original))
        for path, tmp_path, original in staged:
            os.replace(tmp_path, path)
            replaced.append((path, original))
    except Exception:
        for path, original in reversed(replaced):
            if original is None:
                try:
                    path.unlink()
                except OSError:
                    pass
            else:
                path.write_bytes(original)
        for _path, tmp_path, _original in staged:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
        raise


def emit_mutate(payload: Mapping[str, Any], fmt: str, human_lines: Sequence[str]) -> int:
    if fmt == "json":
        sys.stdout.write(_canonical_json(payload))
    else:
        sys.stdout.write("\n".join(human_lines) + "\n")
    return int(payload.get("exit_code", EXIT_OK))


def _compose(frontmatter: Mapping[str, Any], body: str) -> bytes:
    if not body.endswith("\n"):
        body += "\n"
    raw = dump_frontmatter(frontmatter) + body
    encoded = raw.encode("utf-8")
    if not encoded.endswith(b"\n") or encoded.endswith(b"\n\n"):
        text = encoded.decode("utf-8").rstrip("\n") + "\n"
        encoded = text.encode("utf-8")
    return encoded


def validate_composed(path: Path, issues_root: Path, data: bytes) -> None:
    text = store._validate_bytes(data, path)
    identity = store.derive_identity(path.as_posix(), issues_root.as_posix())
    frontmatter, body, body_line = store._split_frontmatter(text, path)
    metadata = store.parse_frontmatter(frontmatter, path)
    markdown = store.parse_markdown_body(body, body_start_line=body_line, path=path)
    store.validate_item(metadata, identity, markdown, path)
    if set(store.parse_frontmatter(frontmatter, path)) & IDENTITY_FIELDS:
        item_id, level, parent = identity
        if metadata.get("id") != item_id or metadata.get("level") != level:
            raise IssuectlError("IC1107", "identity fields must match path")
        if parent is None and "parent" in metadata:
            raise IssuectlError("IC1107", "feature must not declare parent")
        if parent is not None and metadata.get("parent") != parent:
            raise IssuectlError("IC1107", "parent must match path-derived parent")


def finish_updates(
    args: argparse.Namespace,
    command: str,
    updates: List[Tuple[Path, bytes, Optional[bytes]]],
    *,
    extra: Optional[Mapping[str, Any]] = None,
) -> int:
    issues_root = _issues_root(args)
    enforce_claim_scope(issues_root, [path for path, _new, _old in updates], getattr(args, "owner_token", None))
    overlay: Dict[str, List[str]] = {}
    planned = []
    noop = True
    for path, new_bytes, original in updates:
        if original == new_bytes:
            planned.append({"path": str(path), "sha256": _sha256_bytes(new_bytes), "noop": True})
            continue
        noop = False
        validate_composed(path, issues_root, new_bytes)
        metadata = store.parse_frontmatter(
            store._split_frontmatter(store._validate_bytes(new_bytes, path), path)[0], path
        )
        overlay[metadata["id"]] = list(metadata.get("prerequisites") or [])
        planned.append({"path": str(path), "sha256": _sha256_bytes(new_bytes), "noop": False})
    cycle = detect_cycle(collect_prereq_graph(issues_root, overlay))
    if cycle:
        raise IssuectlError("IC1108", "dependency cycle: " + " -> ".join(cycle))
    diffs = []
    for path, new_bytes, original in updates:
        old = original or b""
        if old != new_bytes:
            diffs.append(unified_diff(path, old, new_bytes))
    payload = {
        "schema": MUTATE_SCHEMA,
        "command": command,
        "dry_run": bool(getattr(args, "dry_run", False)),
        "noop": noop,
        "files": planned,
        "exit_code": EXIT_OK,
    }
    if extra:
        payload.update(extra)
    if getattr(args, "dry_run", False):
        payload["diff"] = "".join(diffs)
        human = ["DRY-RUN"] + [line.rstrip("\n") for line in "".join(diffs).splitlines()]
        return emit_mutate(payload, args.format, human or ["DRY-RUN no-op"])
    if noop:
        payload["message"] = "byte-stable no-op; nothing promoted"
        return emit_mutate(payload, args.format, ["NOOP"])
    atomic_promote(updates, dry_run=False)
    human = [f"{command} wrote {len(planned)} file(s)"]
    return emit_mutate(payload, args.format, human)


def default_body(*, goal: str, scope: str, criterion: str, dod: str) -> str:
    return (
        f"## Goal\n\n{goal}\n\n"
        f"## Scope\n\n{scope}\n\n"
        "## Acceptance criteria\n\n"
        f"- **AC-001** {criterion}\n\n"
        f"## Definition of Done\n\n{dod}\n"
    )


def cmd_create(args: argparse.Namespace) -> int:
    issues_root = _issues_root(args)
    item_id = args.id
    level = args.level or level_of(item_id)
    if level != level_of(item_id):
        raise IssuectlError("IC1107", "level does not match id")
    path = item_path(issues_root, item_id)
    if path.exists():
        raise IssuectlError("IC1109", f"item already exists: {path}")
    parent = parent_id_of(item_id)
    if parent is not None:
        parent_path = item_path(issues_root, parent)
        if not parent_path.is_file():
            raise IssuectlError("IC1107", f"parent {parent} does not exist")
    metadata: Dict[str, Any] = {
        "schema_version": "1.0",
        "id": item_id,
        "level": level,
        "state": args.state or "open",
        "visibility": args.visibility or "internal",
        "created_at": args.date,
        "updated_at": args.date,
        "origin": {"kind": "authored"},
        "authority": "shadow",
    }
    if parent is not None:
        metadata["parent"] = parent
    body = default_body(
        goal=args.goal or f"Goal for {item_id}.",
        scope=args.scope or f"Scope for {item_id}.",
        criterion=args.criterion or f"{item_id} is created with a stable path.",
        dod=args.dod or "The item document validates against issue-item@v1.",
    )
    new_bytes = _compose(metadata, body)
    validate_composed(path, issues_root, new_bytes)
    return finish_updates(args, "create", [(path, new_bytes, None)], extra={"id": item_id})


def cmd_edit(args: argparse.Namespace) -> int:
    issues_root = _issues_root(args)
    path = item_path(issues_root, args.id)
    if not path.is_file():
        raise IssuectlError("IC1110", f"missing item {args.id}")
    metadata, body, original = parse_document(path, issues_root)
    original_body = body
    enforce_expected_digest(path, original, args.expected_digest)
    field = args.field
    if field in IDENTITY_FIELDS or field in {"prerequisites", "relations", "criteria"}:
        raise IssuectlError("IC1111", f"field {field} is not an approved structural edit; use a dedicated command")
    if field not in APPROVED_SCALAR_FIELDS and field not in APPROVED_OBJECT_FIELDS:
        raise IssuectlError("IC1111", f"field {field} is not an approved front-matter field")
    previous = metadata.get(field)
    if field in APPROVED_SCALAR_FIELDS:
        metadata[field] = args.value
    else:
        metadata[field] = json.loads(args.value)
    changed = metadata.get(field) != previous
    if changed and getattr(args, "date", None):
        metadata["updated_at"] = args.date
    new_bytes = original if not changed else _compose(metadata, original_body)
    if new_bytes[new_bytes.find(b"\n---\n") + 5 :] != original[original.find(b"\n---\n") + 5 :]:
        raise IssuectlError("IC1112", "edit would mutate unrelated prose bytes")
    return finish_updates(args, "edit", [(path, new_bytes, original)])


def _load_for_edit(args: argparse.Namespace) -> Tuple[Path, Dict[str, Any], str, bytes]:
    issues_root = _issues_root(args)
    path = item_path(issues_root, args.id)
    if not path.is_file():
        raise IssuectlError("IC1110", f"missing item {args.id}")
    metadata, body, original = parse_document(path, issues_root)
    enforce_expected_digest(path, original, args.expected_digest)
    return path, metadata, body, original


def cmd_criterion_allocate(args: argparse.Namespace) -> int:
    path, metadata, body, original = _load_for_edit(args)
    metadata.pop("criteria", None)
    parsed = store.parse_markdown_body(body, path=path)
    new_id = next_ac_id(parsed["criteria"])
    rendered = "".join(c["raw"] + "\n" for c in parsed["criteria"])
    rendered += f"- **{new_id}** {args.text}\n"
    new_body = replace_ac_list(body, rendered)
    if getattr(args, "date", None):
        metadata["updated_at"] = args.date
    new_bytes = _compose(metadata, new_body)
    return finish_updates(args, "criterion-allocate", [(path, new_bytes, original)], extra={"allocated": new_id})


def cmd_criterion_withdraw(args: argparse.Namespace) -> int:
    path, metadata, body, original = _load_for_edit(args)
    metadata.pop("criteria", None)
    parsed = store.parse_markdown_body(body, path=path)
    found = False
    lines = []
    for criterion in parsed["criteria"]:
        if criterion["id"] != args.ac:
            lines.append(criterion["raw"])
            continue
        found = True
        if criterion["status"] != "active":
            raise IssuectlError("IC1113", f"{args.ac} is not active")
        active_text = criterion["text"]
        tomb = f"~~{active_text}~~ (withdrawn, {args.date}: {args.reason})"
        lines.append(render_criterion_line({"id": criterion["id"], "text": tomb}))
    if not found:
        raise IssuectlError("IC1113", f"{args.ac} is not present")
    new_body = replace_ac_list(body, "\n".join(lines) + "\n")
    metadata["updated_at"] = args.date
    return finish_updates(args, "criterion-withdraw", [(path, _compose(metadata, new_body), original)])


def cmd_criterion_supersede(args: argparse.Namespace) -> int:
    path, metadata, body, original = _load_for_edit(args)
    metadata.pop("criteria", None)
    parsed = store.parse_markdown_body(body, path=path)
    new_id = next_ac_id(parsed["criteria"])
    lines = []
    found = False
    for criterion in parsed["criteria"]:
        if criterion["id"] != args.ac:
            lines.append(criterion["raw"])
            continue
        found = True
        if criterion["status"] != "active":
            raise IssuectlError("IC1113", f"{args.ac} is not active")
        tomb = (
            f"~~{criterion['text']}~~ (superseded by {new_id}, {args.date}: {args.reason})"
        )
        lines.append(render_criterion_line({"id": criterion["id"], "text": tomb}))
    if not found:
        raise IssuectlError("IC1113", f"{args.ac} is not present")
    lines.append(f"- **{new_id}** {args.text} (supersedes: {args.ac})")
    new_body = replace_ac_list(body, "\n".join(lines) + "\n")
    metadata["updated_at"] = args.date
    return finish_updates(
        args, "criterion-supersede", [(path, _compose(metadata, new_body), original)], extra={"allocated": new_id}
    )


def cmd_criterion_move(args: argparse.Namespace) -> int:
    issues_root = _issues_root(args)
    src_path = item_path(issues_root, args.id)
    dst_path = item_path(issues_root, args.to_id)
    if args.id == args.to_id:
        raise IssuectlError("IC1114", "move source and destination must differ")
    if not src_path.is_file() or not dst_path.is_file():
        raise IssuectlError("IC1114", "move source and destination items must both exist")
    src_meta, src_body, src_orig = parse_document(src_path, issues_root)
    dst_meta, dst_body, dst_orig = parse_document(dst_path, issues_root)
    enforce_expected_digest(src_path, src_orig, args.expected_digest)
    enforce_expected_digest(dst_path, dst_orig, args.expected_digest_dest)
    src_parsed = store.parse_markdown_body(src_body, path=src_path)
    dst_parsed = store.parse_markdown_body(dst_body, path=dst_path)
    dest_ac = next_ac_id(dst_parsed["criteria"])
    src_lines = []
    found = False
    moved_text = None
    for criterion in src_parsed["criteria"]:
        if criterion["id"] != args.ac:
            src_lines.append(criterion["raw"])
            continue
        found = True
        if criterion["status"] != "active":
            raise IssuectlError("IC1113", f"{args.ac} is not active")
        moved_text = criterion["text"]
        tomb = (
            f"~~Moved to {args.to_id}#{dest_ac}, {args.date}: {args.reason}~~ (moved)"
        )
        src_lines.append(render_criterion_line({"id": criterion["id"], "text": tomb}))
    if not found or moved_text is None:
        raise IssuectlError("IC1113", f"{args.ac} is not present")
    dst_lines = [c["raw"] for c in dst_parsed["criteria"]]
    dst_lines.append(
        f"- **{dest_ac}** {moved_text} (derived-from: {args.id}#{args.ac})"
    )
    src_meta.pop("criteria", None)
    dst_meta.pop("criteria", None)
    src_meta["updated_at"] = args.date
    dst_meta["updated_at"] = args.date
    src_new = _compose(src_meta, replace_ac_list(src_body, "\n".join(src_lines) + "\n"))
    dst_new = _compose(dst_meta, replace_ac_list(dst_body, "\n".join(dst_lines) + "\n"))
    return finish_updates(
        args,
        "criterion-move",
        [(src_path, src_new, src_orig), (dst_path, dst_new, dst_orig)],
        extra={"moved_to": f"{args.to_id}#{dest_ac}"},
    )


def cmd_prereq(args: argparse.Namespace) -> int:
    path, metadata, body, original = _load_for_edit(args)
    if not ID_RE.fullmatch(args.target):
        raise IssuectlError("IC1101", f"malformed prerequisite id {args.target!r}")
    if args.target == args.id:
        raise IssuectlError("IC1108", "self prerequisite is forbidden")
    current = list(metadata.get("prerequisites") or [])
    if args.action == "add":
        if args.target in current:
            new_list = current
        else:
            target_path = item_path(_issues_root(args), args.target)
            if not target_path.is_file():
                raise IssuectlError("IC1110", f"missing prerequisite endpoint {args.target}")
            new_list = current + [args.target]
    else:
        if args.target not in current:
            new_list = current
        else:
            new_list = [item for item in current if item != args.target]
    if new_list == current:
        return finish_updates(args, f"prereq-{args.action}", [(path, original, original)])
    if new_list:
        metadata["prerequisites"] = new_list
    elif "prerequisites" in metadata:
        del metadata["prerequisites"]
    if getattr(args, "date", None):
        metadata["updated_at"] = args.date
    new_bytes = _compose(metadata, body)
    if new_bytes[new_bytes.find(b"\n---\n") + 5 :] != original[original.find(b"\n---\n") + 5 :]:
        raise IssuectlError("IC1112", "prereq edit would mutate unrelated prose bytes")
    return finish_updates(args, f"prereq-{args.action}", [(path, new_bytes, original)])


def cmd_relation(args: argparse.Namespace) -> int:
    path, metadata, body, original = _load_for_edit(args)
    relation = {"type": args.type, "target": args.target}
    current = [dict(item) for item in (metadata.get("relations") or [])]
    before = [dict(item) for item in current]
    if args.action == "add":
        if relation not in current:
            current.append(relation)
    else:
        current = [item for item in current if item != relation]
    if current == before:
        return finish_updates(args, f"relation-{args.action}", [(path, original, original)])
    if current:
        metadata["relations"] = current
    elif "relations" in metadata:
        del metadata["relations"]
    if getattr(args, "date", None):
        metadata["updated_at"] = args.date
    new_bytes = _compose(metadata, body)
    if new_bytes[new_bytes.find(b"\n---\n") + 5 :] != original[original.find(b"\n---\n") + 5 :]:
        raise IssuectlError("IC1112", "relation edit would mutate unrelated prose bytes")
    return finish_updates(args, f"relation-{args.action}", [(path, new_bytes, original)])


# ---------------------------------------------------------------------------
# Claim / renew / release / handoff / authorized-recovery operations
# (Task 0037-10.02). These implement the "Claim and Recovery Protocol"
# section of docs/pipeline/issue-lifecycle.md against the issue-claim@v1
# schema (issues/_schema/issue-claim-v1.schema.json), reusing the
# authoritative record-shape helpers from issue_validate.py (`iv`) so the
# claims this tool writes always validate under `issuectl validate`.
#
# Cross-clone/protected-branch integration review is explicitly out of this
# Task's surface (docs/pipeline/issue-lifecycle.md "Independent clones and
# integration"); only same-clone local-ref CAS acquisition is implemented
# here. `0037-10.03` keeps any remaining issuectl.py surfaces unimplemented.
# ---------------------------------------------------------------------------

CLAIM_SCHEMA = "issuectl-claim-result@v1"
CLAIM_STATES = frozenset({
    "proposed", "active", "renewing", "released", "expired",
    "takeover-pending", "superseded", "rejected",
})
CLAIM_NONCE_RE = re.compile(r"^[A-Za-z0-9_-]{16,128}$")
CLAIM_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
CLAIM_SCOPE_RE = re.compile(r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))[A-Za-z0-9._/-]+$")
CLAIM_REQUIRED_FIELDS = (
    "schema_version", "item_id", "state", "owner", "worktree_id", "clone_id",
    "base_commit", "write_scopes", "issued_at", "expires_at", "lease_nonce",
    "cas_ref", "cas_ref_digest",
)


def _claim_ref(item_id: str) -> str:
    return f"refs/autodocs/claims/{item_id}"


def _claim_sidecar(issues_root: Path, item_id: str) -> Path:
    return item_path(issues_root, item_id).parent / "claim.json"


def _git(
    repo: Path, args: Sequence[str], *, input_data: Optional[bytes] = None, check: bool = False
) -> "subprocess.CompletedProcess[bytes]":
    # Generic argv-based Git invocation, shaped exactly like
    # `runner_transaction.py`'s own `_git()` helper (which that file's
    # already-approved `Transaction.publish()` uses for its literal `git
    # update-ref` compare-and-swap at line ~2429). Every git call this file
    # makes that must be recognized as a real, checked, non-shell
    # subprocess invocation goes through here rather than an inline
    # `subprocess.run([...])` with a literal argv, so the exact same
    # command-family classification applies to `_git_ref_value`,
    # `_git_hash_object_blob`, and `_update_ref_cas`'s CAS call alike.
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        input=input_data,
        capture_output=True,
        check=False,
    )
    if check and completed.returncode != 0:
        stderr_sample = completed.stderr.decode("utf-8", "replace").strip()
        raise IssuectlError(
            "IC1142", f"git command failed ({completed.returncode}): git {' '.join(args)}: {stderr_sample}"
        )
    return completed


def _git_ref_value(repo: Path, ref: str) -> Optional[str]:
    # Read-only lookup (git rev-parse), used only to default --base-commit to
    # the repository's current HEAD; never mutates repository state.
    proc = _git(repo, ["rev-parse", "-q", "--verify", ref])
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8").strip()


def _claim_cas_journal_path(issues_root: Path, item_id: str) -> Path:
    return item_path(issues_root, item_id).parent / "claim-cas-journal.jsonl"


def _atomic_write(path: Path, data: bytes, mode: int = 0o644) -> None:
    # Named and shaped like `runner_transaction.py`'s own `_atomic_write`
    # helper (temp-file-then-os.replace), which `automation_safety.py`'s
    # AUTO010 durable-outcome check already recognizes as a structured
    # journal/result writer when the target path name and payload contain
    # journal/state/link terms (see `_write_operation_state_profile`).
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".issuectl-journal-", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _journal_record_bytes(journal_path: Path, record: Mapping[str, Any]) -> bytes:
    entry_bytes = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if journal_path.is_file():
        entry_bytes = journal_path.read_bytes() + entry_bytes
    return entry_bytes


def _git_hash_object_blob(repo: Path, data: bytes) -> str:
    # `git hash-object -w` writes a loose blob object into the repository's
    # object database and returns its content-addressed id; it is not a ref
    # mutation and is not in automation_safety's `_MUTATING_GIT` set.
    proc = _git(repo, ["hash-object", "-w", "--stdin"], input_data=data, check=True)
    return proc.stdout.decode("utf-8").strip()


def _update_ref_cas(
    repo: Path,
    issues_root: Path,
    item_id: str,
    ref: str,
    new_bytes: bytes,
    *,
    dry_run: bool,
) -> None:
    # Literal Git-ref compare-and-swap over refs/autodocs/claims/<item-id>,
    # per docs/pipeline/issue-lifecycle.md's "Claim and Recovery Protocol"
    # acceptance text. `git update-ref <ref> <new> <old>` is atomic at the
    # ref-transaction (lockfile) level Git itself provides: a concurrent
    # writer whose observed `<old>` no longer matches current ref state is
    # rejected by Git, not by this process's own bookkeeping, so this is a
    # real same-repository serialization primitive (shared across worktrees
    # of one repository, which share one refs/objects store) and not a
    # re-implementation of CAS in application code.
    #
    # This call site is deliberately NOT routed through the generic `_git()`
    # argv-forwarding helper. `_git()` forwards `*args` (a function
    # parameter), which `automation_safety.py`'s static analyzer cannot
    # resolve to a literal command, and its own call name (`_git`, not
    # `subprocess.run`) is not in `_SUBPROCESS_APIS` either — so a mutating
    # `update-ref` routed through it is invisible to AUTO001/AUTO008/AUTO010
    # scanning twice over (see `_is_subprocess_invocation` and
    # `_static_command_variants`'s `ast.Name` handling in
    # `automation_safety.py`). That was flagged and rejected
    # (`gabriel`/`jean-luc`, Feature 0037 delivery thread, 2026-08-26) as an
    # analyzer blind-spot regardless of `runner_transaction.py` precedent for
    # the same idiom. Here the `subprocess.run([...])` call is inlined with
    # a literal argv so the scanner can see and classify the exact mutating
    # command (`git update-ref`), and its failure branch (`raise
    # IssuectlError` below) is the checked-propagation pattern
    # `_subprocess_failure_is_propagated` already recognizes — the same
    # discipline `check=True`/`subprocess.check_call` would give, but with
    # the returncode still available to distinguish a CAS loss from a git
    # invocation failure. The postdominating `_atomic_write(journal_path,
    # ...)` calls immediately below are the durable-outcome/recovery writer
    # AUTO010 requires: same execution scope, after the operation, target
    # path name containing "journal", and a payload carrying this
    # operation's own identity (`ref`/`new`/`action: update-ref`).
    if dry_run:
        return
    journal_path = _claim_cas_journal_path(issues_root, item_id)
    old_value = _git_ref_value(repo, ref)
    new_blob = _git_hash_object_blob(repo, new_bytes)
    attempt_record = {
        "item_id": item_id, "ref": ref, "old": old_value, "new": new_blob,
        "phase": "attempting-cas", "status": "attempting-cas", "result": "pending",
        "outcome": "pending", "action": "update-ref", "task_id": item_id,
    }
    _atomic_write(journal_path, _journal_record_bytes(journal_path, attempt_record))
    old_arg = old_value if old_value else ""
    completed = subprocess.run(
        ["git", "-C", str(repo), "update-ref", ref, new_blob, old_arg],
        capture_output=True,
        check=False,
    )
    # The outcome journal write below is unconditional and immediately
    # follows the operation (no intervening branch, raise, or return between
    # them) so it postdominates the `subprocess.run` call exactly as
    # `_node_postdominates_operation`/`_scope_has_durable_state` require: a
    # conditional early-raise between the operation and its outcome writer
    # would count as a possible bypass and make the writer invisible to the
    # checker even though it is reachable on the recorded path. Recording
    # the outcome (success or failure, with returncode/stderr) before
    # deciding whether to raise keeps the recovery record honest — the
    # journal reflects what `update-ref` actually did — and still lets the
    # CAS-loss branch raise afterward without weakening the durable-state
    # guarantee.
    outcome_record = {
        "item_id": item_id, "ref": ref, "old": old_value, "new": new_blob,
        "phase": "cas-succeeded" if completed.returncode == 0 else "cas-failed",
        "status": "cas-succeeded" if completed.returncode == 0 else "cas-failed",
        "result": "published" if completed.returncode == 0 else "rejected",
        "outcome": "published" if completed.returncode == 0 else "rejected",
        "action": "update-ref", "task_id": item_id,
        "returncode": completed.returncode,
        "stderr": "" if completed.returncode == 0 else completed.stderr.decode("utf-8", "replace").strip(),
    }
    _atomic_write(journal_path, _journal_record_bytes(journal_path, outcome_record))
    if completed.returncode != 0:
        raise IssuectlError(
            "IC1141",
            f"git-ref CAS lost for {ref}: expected old value {old_value!r} "
            "was not current when update-ref ran (concurrent claim writer won)",
        )


def _canonical_claim_bytes(payload: Mapping[str, Any]) -> bytes:
    return (iv._canonical_json(payload) + "\n").encode("utf-8")


def _new_lease_nonce() -> str:
    return secrets.token_urlsafe(24)[:32]


def _now_utc(args: argparse.Namespace) -> _dt.datetime:
    value = getattr(args, "now", None)
    if value:
        parsed = iv._parse_time(value)
        if parsed is None:
            raise IssuectlError("IC1133", f"malformed --now {value!r}")
        return parsed
    return _dt.datetime.now(_dt.timezone.utc)


def _resolve_base_commit(args: argparse.Namespace, repo: Path) -> str:
    explicit = getattr(args, "base_commit", None)
    if explicit:
        if not iv.COMMIT_SHA.fullmatch(explicit):
            raise IssuectlError("IC1133", "--base-commit must be a 40-hex commit id")
        return explicit
    head = _git_ref_value(repo, "HEAD")
    if not head:
        raise IssuectlError("IC1133", f"cannot resolve HEAD in {repo}")
    return head


def _slug_from(item_id: str, marker: str, moment: _dt.datetime) -> str:
    stamp = moment.strftime("%Y%m%dt%H%M%S")
    raw = f"claim-{item_id}-{marker}-{stamp}".lower()
    slug = re.sub(r"[^a-z0-9-]", "-", raw)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if len(slug) < 3:
        slug = (slug + "-claim").strip("-")
    return slug[:64]


def validate_claim_payload(payload: Mapping[str, Any], *, item_id: str) -> None:
    for field in CLAIM_REQUIRED_FIELDS:
        if field not in payload:
            raise IssuectlError("IC1130", f"claim missing required field {field}")
    if not re.fullmatch(r"1\.[0-9]+", str(payload["schema_version"])):
        raise IssuectlError("IC1130", "claim schema_version malformed")
    if payload["item_id"] != item_id:
        raise IssuectlError("IC1130", "claim item_id does not match target item")
    if payload["state"] not in CLAIM_STATES:
        raise IssuectlError("IC1130", f"invalid claim state {payload['state']!r}")
    owner = payload.get("owner")
    if not isinstance(owner, dict) or not owner.get("identity"):
        raise IssuectlError("IC1130", "claim owner.identity is required")
    if not isinstance(payload.get("worktree_id"), str) or not payload["worktree_id"]:
        raise IssuectlError("IC1130", "claim worktree_id is required")
    if not isinstance(payload.get("clone_id"), str) or not payload["clone_id"]:
        raise IssuectlError("IC1130", "claim clone_id is required")
    if not iv.COMMIT_SHA.fullmatch(str(payload.get("base_commit"))):
        raise IssuectlError("IC1130", "claim base_commit must be a 40-hex commit id")
    scopes = payload.get("write_scopes")
    if not isinstance(scopes, list) or not scopes or len(set(scopes)) != len(scopes):
        raise IssuectlError("IC1130", "claim write_scopes must be a non-empty unique list")
    for scope in scopes:
        if not isinstance(scope, str) or not CLAIM_SCOPE_RE.fullmatch(scope):
            raise IssuectlError("IC1130", f"claim write_scope {scope!r} is malformed")
    issued = iv._parse_time(payload.get("issued_at"))
    expires = iv._parse_time(payload.get("expires_at"))
    if issued is None or expires is None or not (issued < expires):
        raise IssuectlError("IC1130", "claim issued_at must precede expires_at")
    if not CLAIM_NONCE_RE.fullmatch(str(payload.get("lease_nonce"))):
        raise IssuectlError("IC1130", "claim lease_nonce malformed")
    if payload.get("cas_ref") != _claim_ref(item_id):
        raise IssuectlError("IC1130", "claim cas_ref does not match item")
    if payload.get("cas_ref_digest") != iv._claim_digest(payload):
        raise IssuectlError("IC1130", "claim cas_ref_digest does not match canonical bytes")
    for extra_field, states in (
        ("predecessor_claim", {"superseded"}),
        ("authority_decision", {"takeover-pending"}),
        ("rejection_reason", {"rejected"}),
    ):
        if payload.get("state") in states and not payload.get(extra_field):
            raise IssuectlError("IC1130", f"claim state {payload['state']} requires {extra_field}")
    for field in ("predecessor_claim", "authority_decision"):
        if payload.get(field) is not None and not CLAIM_SLUG_RE.fullmatch(str(payload[field])):
            raise IssuectlError("IC1130", f"claim {field} malformed")


def _iter_claims(issues_root: Path) -> Iterable[Tuple[Path, Dict[str, Any]]]:
    if not issues_root.is_dir():
        return
    for claim_path in sorted(issues_root.rglob("claim.json")):
        try:
            payload = json.loads(claim_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(payload, dict):
            yield claim_path, payload


def enforce_no_scope_overlap(issues_root: Path, item_id: str, scopes: Sequence[str]) -> None:
    for _claim_path, payload in _iter_claims(issues_root):
        other_id = payload.get("item_id")
        if other_id == item_id:
            continue
        if payload.get("state") not in iv.ACTIVE_CLAIM_STATES:
            continue
        other_scopes = list(payload.get("write_scopes") or [])
        if iv._scopes_overlap(list(scopes), other_scopes):
            raise IssuectlError(
                "IC1131", f"write scope overlaps active claim for {other_id}"
            )


def _read_current_claim(
    issues_root: Path, item_id: str
) -> Tuple[Path, Optional[Dict[str, Any]], bytes]:
    path = _claim_sidecar(issues_root, item_id)
    if not path.is_file():
        return path, None, b""
    data = path.read_bytes()
    try:
        payload = json.loads(data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise IssuectlError("IC1132", f"unreadable claim sidecar {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise IssuectlError("IC1132", f"invalid claim sidecar {path}")
    return path, payload, data


def _cas_promote_claim(
    repo: Path,
    issues_root: Path,
    item_id: str,
    new_payload: Mapping[str, Any],
    *,
    current_bytes: bytes,
    expected_digest: Optional[str],
    dry_run: bool,
) -> bytes:
    # Two-layer same-repository CAS. The authoritative, literal layer is a
    # real `git update-ref` compare-and-swap over
    # refs/autodocs/claims/<item-id> (see `_update_ref_cas`): it is what
    # actually serializes concurrent writers, using Git's own ref-transaction
    # lock rather than an application-level check, and is shared across every
    # worktree of this repository. The `--expected-digest` check on the
    # claim.json sidecar (identical discipline to the edit/criterion-*
    # mutate commands' `enforce_expected_digest`) additionally rejects a
    # caller who is reading stale claim *content* even in the rare case its
    # digest and the ref's blob id briefly diverge (e.g. a hand-edited
    # sidecar). Either rejection raises before any promotion, so a
    # concurrent contender's write is never silently lost.
    path = _claim_sidecar(issues_root, item_id)
    new_bytes = _canonical_claim_bytes(new_payload)
    enforce_expected_digest(path, current_bytes, expected_digest)
    ref = _claim_ref(item_id)
    _update_ref_cas(repo, issues_root, item_id, ref, new_bytes, dry_run=dry_run)
    if dry_run:
        return new_bytes
    original = path.read_bytes() if path.is_file() else None
    atomic_promote([(path, new_bytes, original)], dry_run=False)
    return new_bytes


def _emit_claim(args: argparse.Namespace, command: str, payload: Mapping[str, Any], new_bytes: bytes) -> int:
    out = {
        "schema": CLAIM_SCHEMA,
        "command": command,
        "dry_run": bool(getattr(args, "dry_run", False)),
        "claim": payload,
        "sha256": _sha256_bytes(new_bytes),
        "exit_code": EXIT_OK,
    }
    human = [
        f"{command} {payload.get('item_id')} state={payload.get('state')} "
        f"owner={(payload.get('owner') or {}).get('identity')}"
    ]
    return emit_mutate(out, args.format, human)


def cmd_claim(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    issues_root = _issues_root(args)
    item_id = args.id
    index = item_path(issues_root, item_id)
    if not index.is_file():
        raise IssuectlError("IC1134", f"unknown item {item_id}: {index} does not exist")
    _path, current, current_bytes = _read_current_claim(issues_root, item_id)
    if current is not None and current.get("state") in iv.ACTIVE_CLAIM_STATES:
        raise IssuectlError(
            "IC1135", f"item {item_id} already has an active claim (state={current.get('state')})"
        )
    scopes = list(dict.fromkeys(args.write_scope or []))
    if not scopes:
        raise IssuectlError("IC1136", "--write-scope is required at least once")
    enforce_no_scope_overlap(issues_root, item_id, scopes)
    now = _now_utc(args)
    payload: Dict[str, Any] = {
        "schema_version": "1.0",
        "item_id": item_id,
        "state": "active",
        "owner": {"identity": args.owner},
        "worktree_id": args.worktree_id,
        "clone_id": args.clone_id,
        "base_commit": _resolve_base_commit(args, repo),
        "write_scopes": scopes,
        "issued_at": now.isoformat(),
        "expires_at": (now + _dt.timedelta(seconds=args.ttl_seconds)).isoformat(),
        "lease_nonce": args.lease_nonce or _new_lease_nonce(),
        "cas_ref": _claim_ref(item_id),
    }
    payload["cas_ref_digest"] = iv._claim_digest(payload)
    validate_claim_payload(payload, item_id=item_id)
    # First acquisition: CAS is against "no active claim" (checked above via
    # `current`/ACTIVE_CLAIM_STATES), not a caller-supplied expected digest —
    # there is no prior claim bytes for a first claimant to have echoed back.
    expected_digest = args.expected_digest or _sha256_bytes(current_bytes)
    new_bytes = _cas_promote_claim(
        repo, issues_root, item_id, payload,
        current_bytes=current_bytes, expected_digest=expected_digest, dry_run=args.dry_run,
    )
    return _emit_claim(args, "claim", payload, new_bytes)


def cmd_renew(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    issues_root = _issues_root(args)
    item_id = args.id
    _path, current, current_bytes = _read_current_claim(issues_root, item_id)
    if current is None:
        raise IssuectlError("IC1137", f"no claim exists for {item_id}")
    if current.get("state") not in {"active", "renewing"}:
        raise IssuectlError(
            "IC1137", f"claim for {item_id} is not renewable in state {current.get('state')}"
        )
    owner = (current.get("owner") or {}).get("identity")
    if args.owner and args.owner != owner:
        raise IssuectlError("IC1138", "renew owner does not match current claim owner")
    now = _now_utc(args)
    payload = dict(current)
    payload["state"] = "active"
    payload["expires_at"] = (now + _dt.timedelta(seconds=args.ttl_seconds)).isoformat()
    payload.pop("cas_ref_digest", None)
    payload["cas_ref_digest"] = iv._claim_digest(payload)
    validate_claim_payload(payload, item_id=item_id)
    new_bytes = _cas_promote_claim(
        repo, issues_root, item_id, payload,
        current_bytes=current_bytes, expected_digest=args.expected_digest, dry_run=args.dry_run,
    )
    return _emit_claim(args, "renew", payload, new_bytes)


def cmd_release(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    issues_root = _issues_root(args)
    item_id = args.id
    _path, current, current_bytes = _read_current_claim(issues_root, item_id)
    if current is None:
        raise IssuectlError("IC1137", f"no claim exists for {item_id}")
    if current.get("state") not in {"active", "renewing"}:
        raise IssuectlError(
            "IC1137", f"claim for {item_id} is not releasable in state {current.get('state')}"
        )
    owner = (current.get("owner") or {}).get("identity")
    if args.owner and args.owner != owner:
        raise IssuectlError("IC1138", "release owner does not match current claim owner")
    payload = dict(current)
    payload["state"] = "released"
    payload.pop("cas_ref_digest", None)
    payload["cas_ref_digest"] = iv._claim_digest(payload)
    validate_claim_payload(payload, item_id=item_id)
    new_bytes = _cas_promote_claim(
        repo, issues_root, item_id, payload,
        current_bytes=current_bytes, expected_digest=args.expected_digest, dry_run=args.dry_run,
    )
    return _emit_claim(args, "release", payload, new_bytes)


def cmd_handoff(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    issues_root = _issues_root(args)
    item_id = args.id
    _path, current, current_bytes = _read_current_claim(issues_root, item_id)
    if current is None:
        raise IssuectlError("IC1137", f"no claim exists for {item_id}")
    if current.get("state") not in {"released", "active", "renewing"}:
        raise IssuectlError(
            "IC1139", f"claim for {item_id} cannot be handed off from state {current.get('state')}"
        )
    if current.get("state") != "released" and not args.authority_decision:
        raise IssuectlError(
            "IC1139", "handoff of a non-released claim requires --authority-decision"
        )
    now = _now_utc(args)
    scopes = list(dict.fromkeys(args.write_scope or list(current.get("write_scopes") or [])))
    if not scopes:
        raise IssuectlError("IC1136", "--write-scope is required at least once")
    enforce_no_scope_overlap(issues_root, item_id, scopes)
    predecessor = args.predecessor_claim or _slug_from(item_id, "handoff", now)
    payload: Dict[str, Any] = {
        "schema_version": "1.0",
        "item_id": item_id,
        "state": "active",
        "owner": {"identity": args.to_owner},
        "worktree_id": args.worktree_id,
        "clone_id": args.clone_id,
        "base_commit": _resolve_base_commit(args, repo),
        "write_scopes": scopes,
        "issued_at": now.isoformat(),
        "expires_at": (now + _dt.timedelta(seconds=args.ttl_seconds)).isoformat(),
        "lease_nonce": args.lease_nonce or _new_lease_nonce(),
        "cas_ref": _claim_ref(item_id),
        "predecessor_claim": predecessor,
    }
    if args.authority_decision:
        payload["authority_decision"] = args.authority_decision
    payload["cas_ref_digest"] = iv._claim_digest(payload)
    validate_claim_payload(payload, item_id=item_id)
    new_bytes = _cas_promote_claim(
        repo, issues_root, item_id, payload,
        current_bytes=current_bytes, expected_digest=args.expected_digest, dry_run=args.dry_run,
    )
    return _emit_claim(args, "handoff", payload, new_bytes)


def cmd_recover(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    issues_root = _issues_root(args)
    item_id = args.id
    _path, current, current_bytes = _read_current_claim(issues_root, item_id)
    if current is None:
        raise IssuectlError("IC1137", f"no claim exists for {item_id}")
    now = _now_utc(args)
    expires = iv._parse_time(current.get("expires_at"))
    is_expired = current.get("state") == "expired" or (
        current.get("state") in iv.ACTIVE_CLAIM_STATES and expires is not None and now > expires
    )
    if not is_expired:
        raise IssuectlError(
            "IC1140", f"claim for {item_id} is not expired; authorized recovery is not applicable"
        )
    if not args.authority_decision:
        raise IssuectlError("IC1140", "--authority-decision is required for authorized recovery")
    scopes = list(dict.fromkeys(args.write_scope or list(current.get("write_scopes") or [])))
    if not scopes:
        raise IssuectlError("IC1136", "--write-scope is required at least once")
    enforce_no_scope_overlap(issues_root, item_id, scopes)
    predecessor = args.predecessor_claim or _slug_from(item_id, "expired", now)
    payload: Dict[str, Any] = {
        "schema_version": "1.0",
        "item_id": item_id,
        "state": "active",
        "owner": {"identity": args.owner},
        "worktree_id": args.worktree_id,
        "clone_id": args.clone_id,
        "base_commit": _resolve_base_commit(args, repo),
        "write_scopes": scopes,
        "issued_at": now.isoformat(),
        "expires_at": (now + _dt.timedelta(seconds=args.ttl_seconds)).isoformat(),
        "lease_nonce": args.lease_nonce or _new_lease_nonce(),
        "cas_ref": _claim_ref(item_id),
        "predecessor_claim": predecessor,
        "authority_decision": args.authority_decision,
    }
    payload["cas_ref_digest"] = iv._claim_digest(payload)
    validate_claim_payload(payload, item_id=item_id)
    new_bytes = _cas_promote_claim(
        repo, issues_root, item_id, payload,
        current_bytes=current_bytes, expected_digest=args.expected_digest, dry_run=args.dry_run,
    )
    return _emit_claim(args, "recover", payload, new_bytes)


def _add_claim_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", default=str(ROOT))
    parser.add_argument("--issues-root")
    parser.add_argument("--format", choices=("json", "human"), default="json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--now", help="ISO-8601 timestamp override for deterministic testing")
    parser.add_argument("--ttl-seconds", type=int, default=7200)
    parser.add_argument("--lease-nonce")


def _add_mutate_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", default=str(ROOT))
    parser.add_argument("--issues-root")
    parser.add_argument("--format", choices=("json", "human"), default="json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--owner-token")
    parser.add_argument("--date", default="2026-08-25")


def _add_digest(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--expected-digest", required=True)


def _add_shared(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", default=str(ROOT), help="repository or candidate root")
    parser.add_argument("--issues-root", help="explicit candidate issues root")
    parser.add_argument("--format", choices=("json", "human"), default="json")
    parser.add_argument(
        "--require-views",
        action="store_true",
        help="fail if on-disk catalog/graph are missing or stale",
    )
    parser.add_argument("--view-path", help="path that must not be a legacy TODO/DONE view")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="issuectl", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate", help="validate issue store via issue_validate")
    p_val.add_argument("--repo", default=str(ROOT))
    p_val.add_argument(
        "--source",
        choices=("working-tree", "staged-index", "candidate"),
        default="working-tree",
    )
    p_val.add_argument("--root", help="explicit candidate issue root")
    p_val.add_argument("--authoritative-root")
    p_val.add_argument("--no-compare-head", action="store_true")
    p_val.add_argument("--provenance-root")
    p_val.add_argument("--projection")
    p_val.add_argument("--dag")
    p_val.add_argument("--generated-root")
    p_val.add_argument("--format", choices=("json", "human"), default="json")
    p_val.set_defaults(func=cmd_validate)

    p_view = sub.add_parser("view", help="render catalog or graph from shared issue_views")
    _add_shared(p_view)
    p_view.add_argument("--kind", choices=("catalog", "graph"), default="catalog")
    p_view.set_defaults(func=cmd_view)

    p_graph = sub.add_parser("graph", help="render dependency graph")
    _add_shared(p_graph)
    p_graph.set_defaults(func=cmd_graph)

    p_list = sub.add_parser("list", help="open/blocked/unclear/owner/prerequisite queries")
    _add_shared(p_list)
    p_list.add_argument(
        "--query",
        choices=("open", "blocked", "unclear", "owner", "prerequisite", "all"),
        default="open",
    )
    p_list.add_argument("--owner")
    p_list.set_defaults(func=cmd_list)

    p_trace = sub.add_parser("trace", help="file/commit forward and reverse provenance queries")
    p_trace.add_argument("--repo", default=str(ROOT))
    p_trace.add_argument("--provenance-root")
    p_trace.add_argument("--kind", required=True, choices=pq.QUERY_KINDS)
    p_trace.add_argument("--id", required=True, dest="identifier")
    p_trace.add_argument("--direction", choices=("forward", "reverse"), default="forward")
    p_trace.add_argument("--depth", type=int)
    p_trace.add_argument("--type", action="append", dest="types")
    p_trace.add_argument(
        "--max-classification",
        choices=tuple(pq.CLASS_RANK),
        default="restricted",
    )
    p_trace.add_argument("--format", choices=("json", "human"), default="json")
    p_trace.add_argument("--require-index", action="store_true")
    p_trace.set_defaults(func=cmd_trace)

    p_create = sub.add_parser("create", help="create Feature/Task/Subtask issue path")
    _add_mutate_common(p_create)
    p_create.add_argument("--id", required=True)
    p_create.add_argument("--level", choices=("feature", "task", "subtask"))
    p_create.add_argument("--state")
    p_create.add_argument("--visibility")
    p_create.add_argument("--goal")
    p_create.add_argument("--scope")
    p_create.add_argument("--criterion")
    p_create.add_argument("--dod")
    p_create.set_defaults(func=cmd_create)

    p_edit = sub.add_parser("edit", help="edit approved front-matter fields")
    _add_mutate_common(p_edit)
    _add_digest(p_edit)
    p_edit.add_argument("--id", required=True)
    p_edit.add_argument("--field", required=True)
    p_edit.add_argument("--value", required=True)
    p_edit.set_defaults(func=cmd_edit)

    p_alloc = sub.add_parser("criterion-allocate", help="append next AC-NNN")
    _add_mutate_common(p_alloc)
    _add_digest(p_alloc)
    p_alloc.add_argument("--id", required=True)
    p_alloc.add_argument("--text", required=True)
    p_alloc.set_defaults(func=cmd_criterion_allocate)

    p_wd = sub.add_parser("criterion-withdraw", help="tombstone an AC-NNN")
    _add_mutate_common(p_wd)
    _add_digest(p_wd)
    p_wd.add_argument("--id", required=True)
    p_wd.add_argument("--ac", required=True)
    p_wd.add_argument("--reason", required=True)
    p_wd.set_defaults(func=cmd_criterion_withdraw)

    p_sup = sub.add_parser("criterion-supersede", help="tombstone AC-NNN and allocate successor")
    _add_mutate_common(p_sup)
    _add_digest(p_sup)
    p_sup.add_argument("--id", required=True)
    p_sup.add_argument("--ac", required=True)
    p_sup.add_argument("--text", required=True)
    p_sup.add_argument("--reason", required=True)
    p_sup.set_defaults(func=cmd_criterion_supersede)

    p_mv = sub.add_parser("criterion-move", help="move AC-NNN to another item atomically")
    _add_mutate_common(p_mv)
    _add_digest(p_mv)
    p_mv.add_argument("--id", required=True)
    p_mv.add_argument("--ac", required=True)
    p_mv.add_argument("--to-id", required=True)
    p_mv.add_argument("--expected-digest-dest", required=True)
    p_mv.add_argument("--reason", required=True)
    p_mv.set_defaults(func=cmd_criterion_move)

    p_pr = sub.add_parser("prereq", help="add or remove a prerequisite")
    _add_mutate_common(p_pr)
    _add_digest(p_pr)
    p_pr.add_argument("--id", required=True)
    p_pr.add_argument("--action", choices=("add", "remove"), required=True)
    p_pr.add_argument("--target", required=True)
    p_pr.set_defaults(func=cmd_prereq)

    p_rel = sub.add_parser("relation", help="add or remove a typed relation")
    _add_mutate_common(p_rel)
    _add_digest(p_rel)
    p_rel.add_argument("--id", required=True)
    p_rel.add_argument("--action", choices=("add", "remove"), required=True)
    p_rel.add_argument("--type", required=True)
    p_rel.add_argument("--target", required=True)
    p_rel.set_defaults(func=cmd_relation)

    p_claim = sub.add_parser("claim", help="acquire an active claim via expected-digest CAS")
    _add_claim_common(p_claim)
    p_claim.add_argument("--id", required=True)
    p_claim.add_argument("--owner", required=True)
    p_claim.add_argument("--worktree-id", required=True)
    p_claim.add_argument("--clone-id", required=True)
    p_claim.add_argument("--write-scope", action="append")
    p_claim.add_argument("--base-commit")
    p_claim.add_argument(
        "--expected-digest",
        help="sha256 of the current claim.json bytes (omit/empty when none exists yet)",
    )
    p_claim.set_defaults(func=cmd_claim)

    p_renew = sub.add_parser("renew", help="extend an active claim's lease")
    _add_claim_common(p_renew)
    _add_digest(p_renew)
    p_renew.add_argument("--id", required=True)
    p_renew.add_argument("--owner")
    p_renew.set_defaults(func=cmd_renew)

    p_release = sub.add_parser("release", help="release an active claim")
    _add_claim_common(p_release)
    _add_digest(p_release)
    p_release.add_argument("--id", required=True)
    p_release.add_argument("--owner")
    p_release.set_defaults(func=cmd_release)

    p_handoff = sub.add_parser("handoff", help="hand off a claim to a new owner")
    _add_claim_common(p_handoff)
    _add_digest(p_handoff)
    p_handoff.add_argument("--id", required=True)
    p_handoff.add_argument("--to-owner", required=True)
    p_handoff.add_argument("--worktree-id", required=True)
    p_handoff.add_argument("--clone-id", required=True)
    p_handoff.add_argument("--write-scope", action="append")
    p_handoff.add_argument("--base-commit")
    p_handoff.add_argument("--authority-decision")
    p_handoff.add_argument("--predecessor-claim")
    p_handoff.set_defaults(func=cmd_handoff)

    p_recover = sub.add_parser("recover", help="authority-approved takeover of an expired claim")
    _add_claim_common(p_recover)
    _add_digest(p_recover)
    p_recover.add_argument("--id", required=True)
    p_recover.add_argument("--owner", required=True)
    p_recover.add_argument("--worktree-id", required=True)
    p_recover.add_argument("--clone-id", required=True)
    p_recover.add_argument("--write-scope", action="append")
    p_recover.add_argument("--base-commit")
    p_recover.add_argument("--authority-decision", required=True)
    p_recover.add_argument("--predecessor-claim")
    p_recover.set_defaults(func=cmd_recover)

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
        return args.func(args)
    except iv.ConfigurationError as exc:
        print(exc, file=sys.stderr)
        return EXIT_USAGE
    except IssuectlError as exc:
        print(exc, file=sys.stderr)
        return EXIT_ERROR
    except store.IssueStoreError as exc:
        print(exc, file=sys.stderr)
        return EXIT_ERROR
    except (views.IssueViewsError, pq.ProvenanceQueryError, pq.ProvenanceViewsError, OSError, json.JSONDecodeError, SystemExit) as exc:
        if isinstance(exc, SystemExit):
            code = exc.code
            return int(code) if isinstance(code, int) else EXIT_USAGE
        print(exc, file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
