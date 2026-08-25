#!/usr/bin/env python3
"""issuectl query surfaces (Task `0037-10.04`).

Thin CLI over shared libraries: `issue_validate`, `issue_views`,
`provenance_query`. Does not implement a second trace or validation model.
Read-only for validate/view/graph/list/trace. Never treats TODO.md/DONE.md as
authority.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

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

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
        return args.func(args)
    except iv.ConfigurationError as exc:
        print(exc, file=sys.stderr)
        return EXIT_USAGE
    except (views.IssueViewsError, pq.ProvenanceQueryError, pq.ProvenanceViewsError, OSError, json.JSONDecodeError, SystemExit) as exc:
        if isinstance(exc, SystemExit):
            code = exc.code
            return int(code) if isinstance(code, int) else EXIT_USAGE
        print(exc, file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
