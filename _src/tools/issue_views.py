#!/usr/bin/env python3
"""Deterministic internal catalog and dependency-graph views (Task 0037-11.02).

Outputs are generated, never parser input. Browser layout/color/DOT semantics
are out of scope.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

import importlib.util

_STORE_FILE = Path(__file__).resolve().parent / "issue_store.py"
_SPEC = importlib.util.spec_from_file_location("issue_store", _STORE_FILE)
STORE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(STORE)
IssueStoreError = STORE.IssueStoreError
ITEM_SCHEMA_PATH = STORE.SCHEMA_PATH
STORE_TOOL_PATH = STORE.TOOL_PATH
_canonical_json = STORE._canonical_json
_sha256 = STORE._sha256
derive_identity = STORE.derive_identity
parse_issue = STORE.parse_issue

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path("_src/tools/issue_views.py")
CATALOG_SCHEMA_PATH = Path("issues/_schema/issue-catalog-v1.schema.json")
GRAPH_SCHEMA_PATH = Path("issues/_schema/issue-dependency-graph-v1.schema.json")
CATALOG_OUT = Path("issues/_views/catalog.json")
GRAPH_OUT = Path("issues/_views/dependency-graph.json")
CONFIG = {
    "schema": "issue-views-config@v1",
    "url_prefix": "/issues/",
    "catalog_schema": "issue-catalog@v1",
    "graph_schema": "issue-dependency-graph@v1",
}
ID_TOKEN = re.compile(r"^[0-9]{4}(?:-[0-9]{2}(?:\.[0-9]{2})?)?$")
PREREQ_LINE = re.compile(r'^\s*-\s*"([^"]+)"\s*$|^\s*-\s*(\S+)\s*$')
BROWSER_KEYS = frozenset({
    "color", "fill", "fontcolor", "stroke", "dot", "svg", "style",
    "shape", "penwidth", "html_label", "cluster_color",
})


class IssueViewsError(ValueError):
    pass


def _digest_bytes(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _generation_id(source_digests, schema_digest, tool_digest, config_digest):
    payload = _canonical_json({
        "config": config_digest,
        "inputs": list(source_digests),
        "schema": schema_digest,
        "tool": tool_digest,
    })
    return _digest_bytes(payload.encode("utf-8") if isinstance(payload, str) else payload)


def item_url(item_id, level):
    prefix = CONFIG["url_prefix"]
    if level == "feature":
        return f"{prefix}{item_id}/"
    if level == "task":
        feature = item_id.split("-", 1)[0]
        return f"{prefix}{feature}/{item_id}/"
    if level == "subtask":
        feature = item_id.split("-", 1)[0]
        return f"{prefix}{feature}/{item_id}/"
    return f"{prefix}{item_id}/"


def _level_from_id(item_id):
    if re.fullmatch(r"[0-9]{4}", item_id):
        return "feature"
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}", item_id):
        return "task"
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}\.[0-9]{2}", item_id):
        return "subtask"
    return None


def _gate_class(source_level, target_level):
    if source_level == "feature" or target_level == "feature":
        return "feature-closure"
    return "start-gate"


def _load_closure(index_path):
    sidecar = Path(index_path).parent / "closure.json"
    if not sidecar.is_file():
        return None
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"malformed": True, "path": sidecar.as_posix()}
    if not isinstance(payload, dict):
        return {"malformed": True, "path": sidecar.as_posix()}
    return payload


def _archive_status(state, closure):
    if not isinstance(closure, dict) or closure.get("malformed"):
        return None
    disposition = closure.get("disposition")
    if disposition == "archived-not-accepted":
        return "archived-not-accepted"
    if state == "closed" and disposition in {
            "completed", "wontfix", "superseded", "duplicate", "cancelled",
            "archived-not-accepted"}:
        return disposition
    return None


def _lifecycle_status(state, closure):
    archive = _archive_status(state, closure)
    if archive:
        return f"closed:{archive}"
    return state


def _extract_prereqs_loose(text):
    lines = text.splitlines()
    collecting = False
    values = []
    for line in lines:
        if line.startswith("prerequisites:"):
            collecting = True
            rest = line.split(":", 1)[1].strip()
            if rest and rest not in ("", "[]"):
                values.append(rest.strip("[]\"' "))
            continue
        if collecting:
            if line.strip() in ("---", "..."):
                break
            if line and not line.startswith(" ") and not line.startswith("-"):
                break
            match = PREREQ_LINE.match(line)
            if match:
                values.append(match.group(1) or match.group(2))
            elif line.strip() == "":
                continue
            else:
                break
    return values


def _iter_index_paths(issues_root):
    root = Path(issues_root)
    if not root.is_dir():
        return []
    found = []
    for path in sorted(root.rglob("index.md"), key=lambda value: value.as_posix().encode("utf-8")):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0].startswith("_"):
            continue
        found.append(path)
    return found


def load_store(issues_root, repository_root):
    issues_root = Path(issues_root).resolve()
    repository_root = Path(repository_root).resolve()
    parsed = []
    malformed = []
    source_files = []
    for path in _iter_index_paths(issues_root):
        data = path.read_bytes()
        rel = path.relative_to(repository_root).as_posix()
        source_files.append({"path": rel, "sha256": _sha256(data)})
        try:
            derive_identity(path.as_posix(), issues_root.as_posix())
            value = parse_issue(path, issues_root=issues_root, repository_root=repository_root)
            parsed.append(value)
        except (IssueStoreError, OSError) as exc:
            text = data.decode("utf-8", "replace")
            identity = None
            try:
                identity = derive_identity(path.as_posix(), issues_root.as_posix())
            except IssueStoreError:
                identity = None
            item_id = identity[0] if identity else path.parent.name
            level = identity[1] if identity else _level_from_id(item_id)
            error = str(exc).replace(str(path), rel).replace(str(repository_root) + "/", "")
            malformed.append({
                "id": item_id,
                "level": level,
                "path": rel,
                "sha256": _sha256(data),
                "bytes": len(data),
                "error": error,
                "prerequisites": _extract_prereqs_loose(text),
            })
    return parsed, malformed, source_files


def _catalog_item(value, repository_root):
    item = value["item"]
    source_path = value["source"]["path"]
    abs_path = Path(repository_root) / source_path
    closure = _load_closure(abs_path)
    archive = _archive_status(item["state"], closure)
    goal = value["sections"].get("Goal", {})
    goal_text = goal.get("text", "")
    return {
        "id": item["id"],
        "level": item["level"],
        "parent": item.get("parent"),
        "state": item["state"],
        "lifecycle_status": _lifecycle_status(item["state"], closure),
        "archive_status": archive,
        "visibility": item.get("visibility", "internal"),
        "url": item_url(item["id"], item["level"]),
        "title": goal_text.splitlines()[0] if goal_text else "",
        "title_source_hash": _digest_bytes(goal_text.encode("utf-8")),
        "prerequisites": list(item.get("prerequisites") or []),
        "relations": list(item.get("relations") or []),
        "criteria": [
            {"id": entry["id"], "status": entry["status"]}
            for entry in value["criteria"]
        ],
        "source": {
            "path": source_path,
            "sha256": value["source"]["sha256"],
            "bytes": value["source"]["bytes"],
            "locator": {
                "path": source_path,
                "byte_start": 0,
                "byte_end": value["source"]["bytes"],
            },
        },
        "normalized_sha256": value["normalized_sha256"],
    }


def _malformed_catalog_item(entry):
    level = entry["level"] or "task"
    return {
        "id": entry["id"],
        "level": level,
        "parent": None,
        "state": None,
        "lifecycle_status": "malformed",
        "archive_status": None,
        "visibility": None,
        "url": item_url(entry["id"], level) if ID_TOKEN.fullmatch(entry["id"] or "") else None,
        "title": "",
        "title_source_hash": None,
        "prerequisites": list(entry["prerequisites"]),
        "relations": [],
        "criteria": [],
        "source": {
            "path": entry["path"],
            "sha256": entry["sha256"],
            "bytes": entry["bytes"],
            "locator": {"path": entry["path"], "byte_start": 0, "byte_end": entry["bytes"]},
        },
        "normalized_sha256": None,
        "endpoint_status": "malformed",
        "parse_error": entry["error"],
    }


def build_catalog(parsed, malformed, source_files, repository_root):
    repository_root = Path(repository_root)
    items = [_catalog_item(value, repository_root) for value in parsed]
    items.extend(_malformed_catalog_item(entry) for entry in malformed)
    items.sort(key=lambda entry: (entry["id"] or "", entry["source"]["path"]))
    schema_bytes = (repository_root / CATALOG_SCHEMA_PATH).read_bytes()
    tool_bytes = (repository_root / TOOL_PATH).read_bytes()
    config_digest = _digest_bytes(_canonical_json(CONFIG).encode("utf-8"))
    source_digests = [
        _digest_bytes(f"{entry['path']}:{entry['sha256']}".encode("utf-8"))
        for entry in sorted(source_files, key=lambda value: value["path"])
    ]
    schema_digest = _digest_bytes(schema_bytes)
    tool_digest = _digest_bytes(tool_bytes)
    catalog = {
        "schema": CONFIG["catalog_schema"],
        "authority": "generated-view",
        "items": items,
        "digests": {
            "schema_sha256": schema_digest,
            "tool_sha256": tool_digest,
            "config_sha256": config_digest,
            "source_sha256": source_digests,
            "item_schema_sha256": _digest_bytes((repository_root / ITEM_SCHEMA_PATH).read_bytes()),
            "store_tool_sha256": _digest_bytes((repository_root / STORE_TOOL_PATH).read_bytes()),
        },
    }
    catalog["generation_id"] = _generation_id(
        source_digests, schema_digest, tool_digest, config_digest)
    return catalog


def build_graph(catalog):
    present = {item["id"] for item in catalog["items"] if item.get("endpoint_status") != "malformed"}
    malformed_ids = {item["id"] for item in catalog["items"] if item.get("endpoint_status") == "malformed"}
    nodes_by_id = {}
    for item in catalog["items"]:
        status = item.get("endpoint_status") or "present"
        nodes_by_id[item["id"]] = {
            "id": item["id"],
            "level": item["level"],
            "state": item["state"],
            "lifecycle_status": item["lifecycle_status"],
            "archive_status": item["archive_status"],
            "url": item["url"],
            "endpoint_status": status,
        }
    edges = []

    def ensure_target(target, *, malformed=False, missing=False):
        if target in nodes_by_id:
            return
        level = _level_from_id(target)
        status = "malformed" if malformed or not ID_TOKEN.fullmatch(target) else "missing"
        if missing:
            status = "missing"
        nodes_by_id[target] = {
            "id": target,
            "level": level,
            "state": None,
            "lifecycle_status": status,
            "archive_status": None,
            "url": item_url(target, level) if level else None,
            "endpoint_status": status,
        }

    for item in catalog["items"]:
        source = item["id"]
        source_level = item["level"] or _level_from_id(source)
        for target in item.get("prerequisites") or []:
            valid = bool(ID_TOKEN.fullmatch(target))
            if not valid:
                ensure_target(target, malformed=True)
                endpoint = "malformed"
            elif target in malformed_ids:
                ensure_target(target, malformed=True)
                endpoint = "malformed"
            elif target not in present:
                ensure_target(target, missing=True)
                endpoint = "missing"
            else:
                endpoint = "present"
            target_level = nodes_by_id[target]["level"]
            edges.append({
                "source": source,
                "target": target,
                "kind": "prerequisite",
                "gate": _gate_class(source_level, target_level),
                "endpoint_status": endpoint,
            })
        for relation in item.get("relations") or []:
            target = relation["target"].split("#", 1)[0]
            valid = bool(ID_TOKEN.fullmatch(target))
            if not valid:
                ensure_target(target, malformed=True)
                endpoint = "malformed"
            elif target in malformed_ids:
                ensure_target(target, malformed=True)
                endpoint = "malformed"
            elif target not in present:
                ensure_target(target, missing=True)
                endpoint = "missing"
            else:
                endpoint = "present"
            edges.append({
                "source": source,
                "target": target,
                "kind": relation["type"],
                "gate": None,
                "endpoint_status": endpoint,
            })
    nodes = [nodes_by_id[key] for key in sorted(nodes_by_id)]
    edges.sort(key=lambda edge: (edge["source"], edge["kind"], edge["target"]))
    return nodes, edges


def assemble_graph(catalog, repository_root, source_files):
    repository_root = Path(repository_root)
    nodes, edges = build_graph(catalog)
    schema_bytes = (repository_root / GRAPH_SCHEMA_PATH).read_bytes()
    tool_bytes = (repository_root / TOOL_PATH).read_bytes()
    config_digest = _digest_bytes(_canonical_json(CONFIG).encode("utf-8"))
    source_digests = [
        _digest_bytes(f"{entry['path']}:{entry['sha256']}".encode("utf-8"))
        for entry in sorted(source_files, key=lambda value: value["path"])
    ]
    schema_digest = _digest_bytes(schema_bytes)
    tool_digest = _digest_bytes(tool_bytes)
    graph = {
        "schema": CONFIG["graph_schema"],
        "authority": "generated-view",
        "nodes": nodes,
        "edges": edges,
        "digests": {
            "schema_sha256": schema_digest,
            "tool_sha256": tool_digest,
            "config_sha256": config_digest,
            "source_sha256": source_digests,
            "catalog_generation_id": catalog["generation_id"],
        },
    }
    graph["generation_id"] = _generation_id(
        source_digests, schema_digest, tool_digest, config_digest)
    return graph


def _reject_browser_keys(value, path="$"):
    if isinstance(value, dict):
        extra = BROWSER_KEYS.intersection(value)
        if extra:
            raise IssueViewsError(f"browser-only key {sorted(extra)} at {path}")
        for key, child in value.items():
            _reject_browser_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_browser_keys(child, f"{path}[{index}]")


def render(issues_root, repository_root):
    parsed, malformed, source_files = load_store(issues_root, repository_root)
    catalog = build_catalog(parsed, malformed, source_files, repository_root)
    graph = assemble_graph(catalog, repository_root, source_files)
    _reject_browser_keys(catalog)
    _reject_browser_keys(graph)
    return catalog, graph


def verify_document(document, expected_kind, repository_root, issues_root):
    catalog, graph = render(issues_root, repository_root)
    expected = catalog if expected_kind == "catalog" else graph
    if document.get("generation_id") != expected["generation_id"]:
        raise IssueViewsError("stale or hand-edited generation_id")
    encoded = _canonical_json(document)
    if encoded != _canonical_json(expected):
        raise IssueViewsError("view bytes diverge from canonical regeneration")
    return True


def write_views(catalog, graph, repository_root):
    repository_root = Path(repository_root)
    catalog_path = repository_root / CATALOG_OUT
    graph_path = repository_root / GRAPH_OUT
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(_canonical_json(catalog), encoding="utf-8")
    graph_path.write_text(_canonical_json(graph), encoding="utf-8")
    return catalog_path, graph_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", default=str(ROOT))
    parser.add_argument("--issues-root")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    repository_root = Path(args.repository_root).resolve()
    issues_root = Path(args.issues_root) if args.issues_root else repository_root / "issues"
    try:
        catalog, graph = render(issues_root, repository_root)
        if args.verify:
            verify_document(json.loads((repository_root / CATALOG_OUT).read_text()),
                            "catalog", repository_root, issues_root)
            verify_document(json.loads((repository_root / GRAPH_OUT).read_text()),
                            "graph", repository_root, issues_root)
        if args.write:
            write_views(catalog, graph, repository_root)
        else:
            sys.stdout.write(_canonical_json({"catalog": catalog, "graph": graph}))
        return 0
    except (IssueViewsError, IssueStoreError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
