#!/usr/bin/env python3
"""Bounded forward/reverse provenance trace queries (Task `0037-17.03`).

Read-only: consumes immutable sources and disposable `provenance/_views/`
indexes. Never writes indexes, events, or issue views. Trace depth is file and
commit (DEC-0040-004); line and symbol identities are not query keys.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple

import importlib.util

_TOOLS = Path(__file__).resolve().parent
_VIEW_SPEC = importlib.util.spec_from_file_location(
    "provenance_views", _TOOLS / "provenance_views.py"
)
assert _VIEW_SPEC and _VIEW_SPEC.loader
pv = importlib.util.module_from_spec(_VIEW_SPEC)
_VIEW_SPEC.loader.exec_module(pv)

ProvenanceViewsError = pv.ProvenanceViewsError
GRAPH_OUT = pv.GRAPH_OUT
REVERSE_OUT = pv.REVERSE_OUT

QUERY_KINDS = (
    "issue",
    "criterion",
    "commit",
    "run",
    "campaign",
    "finding",
    "artifact",
    "artifact-set",
    "record-version",
    "evidence",
    "curation-item",
)
CLASS_RANK = {"public": 0, "internal": 1, "restricted": 2}
EXIT_OK = 0
EXIT_MISSING = 1
EXIT_ERROR = 2
SCHEMA = "provenance-query@v1"


class ProvenanceQueryError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def _normalize_uri(kind: str, ident: str) -> str:
    ident = ident.strip()
    if ident.startswith(kind + ":"):
        return ident
    if kind == "artifact" and ident.startswith("artifact:"):
        return ident
    if kind == "commit" and len(ident) == 40:
        return f"commit:{ident}"
    return f"{kind}:{ident}"


def _kind_of_uri(uri: str) -> str:
    if uri.startswith("artifact:"):
        return "artifact"
    if uri.startswith("artifact-set:"):
        return "artifact-set"
    if uri.startswith("record-version:"):
        return "record-version"
    head, _sep, _rest = uri.partition(":")
    return head or "unknown"


def _parse_artifact_uri(uri: str) -> Tuple[Optional[str], Optional[str]]:
    body = uri[len("artifact:") :] if uri.startswith("artifact:") else uri
    if "@" not in body:
        return body or None, None
    path, digest = body.rsplit("@", 1)
    if digest and not digest.startswith("sha256:"):
        digest = f"sha256:{digest}" if len(digest) == 64 else digest
    return path or None, digest or None


def load_indexes(
    repository_root: Path,
    *,
    provenance_root: Optional[Path] = None,
    require_on_disk: bool = False,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Load graph/reverse views. Rebuild in memory; never write."""
    repository_root = Path(repository_root)
    provenance_root = Path(provenance_root) if provenance_root else repository_root / "provenance"
    graph, reverse = pv.build_views(repository_root, provenance_root=provenance_root)
    graph_path = repository_root / GRAPH_OUT
    reverse_path = repository_root / REVERSE_OUT
    if require_on_disk or graph_path.is_file() or reverse_path.is_file():
        if not graph_path.is_file() or not reverse_path.is_file():
            raise ProvenanceQueryError("PQ-MISSING-INDEX", "graph.json or reverse.json absent")
        on_disk_graph = json.loads(graph_path.read_text(encoding="utf-8"))
        on_disk_reverse = json.loads(reverse_path.read_text(encoding="utf-8"))
        pv.verify_document(on_disk_graph, "graph", repository_root, provenance_root)
        pv.verify_document(on_disk_reverse, "reverse", repository_root, provenance_root)
        return on_disk_graph, on_disk_reverse
    return graph, reverse


def _index_nodes(graph: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {node["uri"]: node for node in graph.get("nodes") or [] if node.get("uri")}


def _index_members(repository_root: Path, provenance_root: Path) -> List[Dict[str, Any]]:
    members: List[Dict[str, Any]] = []
    buckets = pv.collect_sources(provenance_root)
    for path, record in buckets["artifact-sets"]:
        set_id = record.get("set_id")
        classification = record.get("classification") or "internal"
        producer = (record.get("producer") or {}).get("uri")
        rel = str(path)
        try:
            rel = path.resolve().relative_to(provenance_root.resolve()).as_posix()
        except ValueError:
            pass
        for member in record.get("members") or []:
            if not isinstance(member, dict):
                continue
            uri = pv._artifact_uri_from_member(member)
            if not uri:
                continue
            members.append(
                {
                    "uri": uri,
                    "path": member.get("path"),
                    "digest": member.get("digest"),
                    "source_commit": member.get("source_commit"),
                    "set_id": set_id,
                    "set_uri": f"artifact-set:{set_id}",
                    "classification": member.get("classification") or classification,
                    "redacted": member.get("redacted") is True or pv._is_redacted(member),
                    "producer": producer,
                    "source_path": rel,
                }
            )
    return members


def _privacy_ok(classification: Optional[str], max_class: str) -> bool:
    rank = CLASS_RANK.get(classification or "internal", 1)
    return rank <= CLASS_RANK.get(max_class, 1)


def _add_unique(seq: List[Dict[str, Any]], item: Dict[str, Any]) -> None:
    key = _canonical_json(item)
    if any(_canonical_json(existing) == key for existing in seq):
        return
    seq.append(item)


def _structured(
    status: str,
    *,
    kind: str,
    identifier: str,
    path: Optional[str] = None,
    extra: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    item = {"status": status, "kind": kind, "identifier": identifier}
    if path:
        item["path"] = path
    if extra:
        item.update(extra)
    return item


def query_trace(
    repository_root: Path,
    *,
    kind: str,
    identifier: str,
    direction: str = "forward",
    depth: Optional[int] = None,
    type_filter: Optional[Iterable[str]] = None,
    max_classification: str = "restricted",
    provenance_root: Optional[Path] = None,
    require_on_disk: bool = False,
) -> Dict[str, Any]:
    if kind not in QUERY_KINDS:
        raise ProvenanceQueryError("PQ-KIND", f"unsupported query kind {kind}")
    if direction not in {"forward", "reverse"}:
        raise ProvenanceQueryError("PQ-DIRECTION", f"unsupported direction {direction}")
    if max_classification not in CLASS_RANK:
        raise ProvenanceQueryError("PQ-PRIVACY", f"unknown classification {max_classification}")

    repository_root = Path(repository_root)
    provenance_root = Path(provenance_root) if provenance_root else repository_root / "provenance"
    graph, reverse = load_indexes(
        repository_root, provenance_root=provenance_root, require_on_disk=require_on_disk
    )
    uri = _normalize_uri(kind, identifier)
    nodes = _index_nodes(graph)
    members = _index_members(repository_root, provenance_root)
    members_by_uri = {m["uri"]: m for m in members}
    members_by_path: Dict[str, List[Dict[str, Any]]] = {}
    members_by_digest: Dict[str, List[Dict[str, Any]]] = {}
    members_by_commit: Dict[str, List[Dict[str, Any]]] = {}
    for member in members:
        if member.get("path"):
            members_by_path.setdefault(member["path"], []).append(member)
        if member.get("digest"):
            members_by_digest.setdefault(member["digest"], []).append(member)
        if member.get("source_commit"):
            members_by_commit.setdefault(member["source_commit"], []).append(member)

    adjacency: Dict[str, List[str]] = {}
    for edge in graph.get("edges") or []:
        src = edge.get("source")
        dst = edge.get("target")
        if src and dst:
            adjacency.setdefault(src, []).append(dst)
            adjacency.setdefault(dst, []).append(src)

    types = set(type_filter) if type_filter else None
    diagnostics: List[Dict[str, Any]] = []
    hops: List[Dict[str, Any]] = []
    files: List[Dict[str, Any]] = []
    commits: List[Dict[str, Any]] = []
    issues: List[str] = []
    criteria: List[str] = []
    evidence: List[str] = []
    cycle_markers: List[List[str]] = []

    def allow_node(node_uri: str) -> bool:
        node = nodes.get(node_uri) or {}
        classification = node.get("classification") or "internal"
        if not _privacy_ok(classification, max_classification):
            _add_unique(
                diagnostics,
                _structured(
                    "privacy-filtered",
                    kind=_kind_of_uri(node_uri),
                    identifier=node_uri,
                ),
            )
            return False
        if node.get("redacted"):
            _add_unique(
                diagnostics,
                _structured(
                    "redacted",
                    kind=_kind_of_uri(node_uri),
                    identifier=node_uri,
                    path=node.get("source_path"),
                ),
            )
            return False
        if types and _kind_of_uri(node_uri) not in types and node_uri != uri:
            return False
        return True

    for finding in graph.get("findings") or []:
        code = finding.get("code")
        ident = finding.get("identifier") or ""
        if code == "PV-CYCLE":
            cycle_markers.append(finding.get("cycle") or [])
        elif code == "PV-REDACTED-ENDPOINT":
            _add_unique(
                diagnostics,
                _structured(
                    "redacted",
                    kind=finding.get("kind") or "unknown",
                    identifier=ident,
                    path=finding.get("path"),
                ),
            )
        elif code in {"PV-DANGLING-ENDPOINT", "PV-UNRESOLVABLE-ENDPOINT"}:
            status = "dangling" if code == "PV-DANGLING-ENDPOINT" else "unresolvable"
            _add_unique(
                diagnostics,
                _structured(
                    status,
                    kind=finding.get("kind") or "unknown",
                    identifier=ident,
                    path=finding.get("path"),
                ),
            )

    start_found = uri in nodes or any(
        m["uri"] == uri or m.get("path") == identifier or m.get("digest") == identifier
        for m in members
    )
    if kind == "commit":
        sha = identifier if len(identifier) == 40 else uri.split(":", 1)[-1]
        start_found = start_found or sha in members_by_commit or uri in nodes
    if kind == "artifact":
        path, digest = _parse_artifact_uri(uri)
        start_found = start_found or bool(
            (path and path in members_by_path) or (digest and digest in members_by_digest)
        )
    if kind in reverse.get("issue", {}) and uri in reverse.get("issue", {}).get("runs", {}):
        start_found = True
    for bucket in ("issue", "criterion", "evidence", "artifact"):
        mapping = reverse.get(bucket) or {}
        for _name, table in mapping.items() if isinstance(mapping, dict) else []:
            if isinstance(table, dict) and uri in table:
                start_found = True

    if kind == "artifact-set":
        set_uris = {m["set_uri"] for m in members}
        if uri not in set_uris and uri not in nodes:
            diagnostics.append(
                _structured("missing", kind="artifact-set", identifier=uri)
            )
            start_found = False

    def record_file_commit(member: Mapping[str, Any]) -> None:
        if member.get("redacted"):
            _add_unique(
                diagnostics,
                _structured(
                    "redacted",
                    kind="artifact",
                    identifier=member.get("uri") or "",
                    path=member.get("source_path") or member.get("path"),
                ),
            )
            return
        if not _privacy_ok(member.get("classification"), max_classification):
            return
        file_rec = {
            "path": member.get("path"),
            "digest": member.get("digest"),
            "uri": member.get("uri"),
            "commit": member.get("source_commit"),
            "artifact_set": member.get("set_uri"),
        }
        _add_unique(files, file_rec)
        if member.get("source_commit"):
            _add_unique(
                commits,
                {
                    "commit": member["source_commit"],
                    "uri": f"commit:{member['source_commit']}",
                    "path": member.get("path"),
                    "digest": member.get("digest"),
                },
            )

    def collect_from_uri(seed: str, remaining: Optional[int]) -> None:
        stack: List[Tuple[str, Optional[int], Tuple[str, ...]]] = [(seed, remaining, (seed,))]
        seen: Set[str] = set()
        while stack:
            current, left, trail = stack.pop()
            if current in seen:
                cycle_markers.append(list(trail) + [current])
                hops.append(
                    {
                        "uri": current,
                        "kind": _kind_of_uri(current),
                        "cycle": True,
                    }
                )
                continue
            seen.add(current)
            if not allow_node(current) and current != seed:
                continue
            hops.append({"uri": current, "kind": _kind_of_uri(current), "cycle": False})
            k = _kind_of_uri(current)
            if k == "issue":
                issues.append(current)
                for ev in (reverse.get("issue") or {}).get("evidence", {}).get(current, []):
                    evidence.append(ev)
                for art in (reverse.get("issue") or {}).get("artifacts", {}).get(current, []):
                    if art in members_by_uri:
                        record_file_commit(members_by_uri[art])
                    evidence.append(art)
                for crit in (reverse.get("issue") or {}).get("criteria", {}).get(current, []):
                    criteria.append(crit)
            elif k == "criterion":
                criteria.append(current)
                for ev in (reverse.get("criterion") or {}).get("evidence", {}).get(current, []):
                    evidence.append(ev)
            elif k in {"artifact", "artifact-set", "evidence", "record-version"}:
                evidence.append(current)
                if current in members_by_uri:
                    record_file_commit(members_by_uri[current])
                for issue_uri in (reverse.get("evidence") or {}).get("issue", {}).get(current, []):
                    issues.append(issue_uri)
                for issue_uri in (reverse.get("artifact") or {}).get("issue", {}).get(current, []):
                    issues.append(issue_uri)
                for crit in (reverse.get("evidence") or {}).get("criterion", {}).get(current, []):
                    criteria.append(crit)
            elif k == "commit":
                sha = current.split(":", 1)[-1]
                for member in members_by_commit.get(sha, []):
                    record_file_commit(member)
                    evidence.append(member["uri"])
                    for issue_uri in (reverse.get("artifact") or {}).get("issue", {}).get(member["uri"], []):
                        issues.append(issue_uri)
            if left is not None and left <= 0:
                continue
            nxt_left = None if left is None else left - 1
            for nxt in adjacency.get(current, []):
                stack.append((nxt, nxt_left, trail + (nxt,)))

    seeds: List[str] = []
    if start_found:
        seeds.append(uri)
    if kind == "commit":
        sha = uri.split(":", 1)[-1]
        for member in members_by_commit.get(sha, []):
            seeds.append(member["uri"])
            record_file_commit(member)
    if kind == "artifact":
        path, digest = _parse_artifact_uri(uri)
        if uri in members_by_uri:
            record_file_commit(members_by_uri[uri])
        elif path and path in members_by_path:
            for member in members_by_path[path]:
                seeds.append(member["uri"])
                record_file_commit(member)
        elif digest and digest in members_by_digest:
            for member in members_by_digest[digest]:
                seeds.append(member["uri"])
                record_file_commit(member)
        # renamed files share digest
        if digest:
            for member in members_by_digest.get(digest, []):
                seeds.append(member["uri"])
                record_file_commit(member)

    for seed in sorted(set(seeds)):
        collect_from_uri(seed, depth)

    # Digest-preserving rename: include every member with the same digest.
    extra_files = []
    for rec in files:
        digest = rec.get("digest")
        if not digest:
            continue
        for member in members_by_digest.get(digest, []):
            extra_files.append(member)
    for member in extra_files:
        record_file_commit(member)

    issues = sorted(set(issues))
    criteria = sorted(set(criteria))
    evidence = sorted(set(evidence))
    hops.sort(key=lambda item: (item.get("kind") or "", item.get("uri") or ""))
    files.sort(key=lambda item: (item.get("path") or "", item.get("digest") or "", item.get("uri") or ""))
    commits.sort(key=lambda item: (item.get("commit") or "", item.get("path") or ""))
    diagnostics.sort(
        key=lambda item: (
            item.get("status") or "",
            item.get("kind") or "",
            item.get("identifier") or "",
            item.get("path") or "",
        )
    )
    unique_cycles = []
    seen_c = set()
    for cycle in cycle_markers:
        key = tuple(cycle)
        if key not in seen_c:
            seen_c.add(key)
            unique_cycles.append(cycle)

    query_found = start_found or bool(files) or bool(hops)
    if not query_found:
        diagnostics.append(_structured("missing", kind=kind, identifier=uri))

    result = {
        "schema": SCHEMA,
        "query": {
            "kind": kind,
            "identifier": uri,
            "direction": direction,
            "depth": depth,
            "types": sorted(types) if types else None,
            "max_classification": max_classification,
        },
        "found": query_found,
        "hops": hops,
        "files": files,
        "commits": commits,
        "issues": issues,
        "criteria": criteria,
        "evidence": evidence,
        "diagnostics": diagnostics,
        "cycles": unique_cycles,
        "generation_id": graph.get("generation_id"),
        "authority": "derived-query",
    }
    return result


def format_human(result: Mapping[str, Any]) -> str:
    q = result["query"]
    lines = [
        f"TRACE {q['kind']} {q['identifier']} direction={q['direction']}",
        f"found={result['found']} generation={result.get('generation_id')}",
    ]
    for rec in result.get("files") or []:
        lines.append(
            f"FILE {rec.get('path')} digest={rec.get('digest')} commit={rec.get('commit')}"
        )
    for rec in result.get("commits") or []:
        lines.append(f"COMMIT {rec.get('commit')} path={rec.get('path')}")
    for issue in result.get("issues") or []:
        lines.append(f"ISSUE {issue}")
    for crit in result.get("criteria") or []:
        lines.append(f"CRITERION {crit}")
    for ev in result.get("evidence") or []:
        lines.append(f"EVIDENCE {ev}")
    for hop in result.get("hops") or []:
        marker = " CYCLE" if hop.get("cycle") else ""
        lines.append(f"HOP {hop.get('kind')} {hop.get('uri')}{marker}")
    for diag in result.get("diagnostics") or []:
        path = f" path={diag['path']}" if diag.get("path") else ""
        lines.append(
            f"{diag['status'].upper()} {diag['kind']} {diag['identifier']}{path}"
        )
    for cycle in result.get("cycles") or []:
        lines.append("CYCLE " + " -> ".join(cycle))
    return "\n".join(lines) + "\n"


def result_exit_code(result: Mapping[str, Any]) -> int:
    if not result.get("found"):
        return EXIT_MISSING
    statuses = {d.get("status") for d in result.get("diagnostics") or []}
    if "missing" in statuses and not result.get("files") and not result.get("issues"):
        return EXIT_MISSING
    return EXIT_OK


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", default=str(pv.ROOT))
    parser.add_argument("--provenance-root")
    parser.add_argument("--kind", required=True, choices=QUERY_KINDS)
    parser.add_argument("--id", required=True, dest="identifier")
    parser.add_argument("--direction", choices=("forward", "reverse"), default="forward")
    parser.add_argument("--depth", type=int)
    parser.add_argument("--type", action="append", dest="types")
    parser.add_argument(
        "--max-classification",
        choices=tuple(CLASS_RANK),
        default="restricted",
    )
    parser.add_argument("--format", choices=("json", "human"), default="json")
    parser.add_argument("--require-index", action="store_true")
    args = parser.parse_args(argv)
    repository_root = Path(args.repository_root).resolve()
    provenance_root = Path(args.provenance_root) if args.provenance_root else None
    try:
        result = query_trace(
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
    except (ProvenanceQueryError, ProvenanceViewsError, OSError, json.JSONDecodeError) as exc:
        print(exc, file=sys.stderr)
        return EXIT_ERROR
    if args.format == "json":
        sys.stdout.write(_canonical_json(result))
    else:
        sys.stdout.write(format_human(result))
    return result_exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main())
