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
import difflib
import hashlib
import importlib.util
import json
import os
import re
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
