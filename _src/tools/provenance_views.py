#!/usr/bin/env python3
"""Deterministic provenance graph and reverse indexes (Task `0037-17.02`).

Rebuilds disposable views under `provenance/_views/` from immutable one-file
stores only. Indexes are never relation authority and must not write sources.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple

import importlib.util

_STORE_FILE = Path(__file__).resolve().parent / "provenance_store.py"
_SPEC = importlib.util.spec_from_file_location("provenance_store", _STORE_FILE)
STORE = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(STORE)

canonical_bytes = STORE.canonical_bytes
sha256_bytes = STORE.sha256_bytes
validate_typed_ref = STORE.validate_typed_ref
ProvenanceError = STORE.ProvenanceError

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path("_src/tools/provenance_views.py")
GRAPH_SCHEMA_PATH = Path("provenance/_schema/provenance-graph-v1.schema.json")
REVERSE_SCHEMA_PATH = Path("provenance/_schema/provenance-reverse-v1.schema.json")
GRAPH_OUT = Path("provenance/_views/graph.json")
REVERSE_OUT = Path("provenance/_views/reverse.json")
CONFIG = {
    "schema": "provenance-views-config@v1",
    "graph_schema": "provenance-graph@v1",
    "reverse_schema": "provenance-reverse@v1",
}

STORE_KINDS = frozenset({"run", "finding", "artifact-set", "event"})
EVIDENCE_KINDS = frozenset({"artifact", "artifact-set", "evidence", "record-version"})
INDEXABLE_RELATIONS = frozenset(STORE.RELATIONS)


class ProvenanceViewsError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def _digest_bytes(data: bytes) -> str:
    return sha256_bytes(data)


def _generation_id(source_digests, schema_digest, tool_digest, config_digest) -> str:
    payload = canonical_bytes(
        {
            "config": config_digest,
            "inputs": source_digests,
            "schema": schema_digest,
            "tool": tool_digest,
        }
    )
    return _digest_bytes(payload)


def _sorted_unique(values: Iterable[str]) -> List[str]:
    return sorted(set(values))


def _iter_json_files(directory: Path) -> List[Path]:
    if not directory.is_dir():
        return []
    files = [path for path in directory.rglob("*.json") if path.is_file()]
    files.sort(key=lambda path: path.as_posix())
    return files


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProvenanceViewsError("PV-CORRUPT", f"invalid JSON at {path}") from exc
    if not isinstance(value, dict):
        raise ProvenanceViewsError("PV-CORRUPT", f"non-object JSON at {path}")
    return value


def _ref_key(ref: Mapping[str, Any]) -> str:
    return str(ref.get("uri") or "")


def _node_id(kind: str, uri: str) -> str:
    return f"{kind}|{uri}"


def _is_redacted(ref: Mapping[str, Any]) -> bool:
    if ref.get("redacted") is True:
        return True
    if ref.get("classification") == "restricted" and ref.get("redacted") is True:
        return True
    return bool(ref.get("redacted"))


def collect_sources(provenance_root: Path) -> Dict[str, List[Tuple[Path, Dict[str, Any]]]]:
    buckets = {
        "events": [],
        "runs": [],
        "findings": [],
        "artifact-sets": [],
    }
    mapping = {
        "events": provenance_root / "events",
        "runs": provenance_root / "runs",
        "findings": provenance_root / "findings",
        "artifact-sets": provenance_root / "artifact-sets",
    }
    for kind, directory in mapping.items():
        for path in _iter_json_files(directory):
            buckets[kind].append((path, _load_json(path)))
    return buckets


def _index_records(buckets: Mapping[str, List[Tuple[Path, Dict[str, Any]]]]) -> Dict[str, Tuple[Path, Dict[str, Any]]]:
    by_uri: Dict[str, Tuple[Path, Dict[str, Any]]] = {}
    for path, record in buckets["runs"]:
        run_id = record.get("run_id")
        if isinstance(run_id, str):
            by_uri[f"run:{run_id}"] = (path, record)
    for path, record in buckets["findings"]:
        finding_id = record.get("finding_id")
        if isinstance(finding_id, str):
            by_uri[f"finding:{finding_id}"] = (path, record)
    for path, record in buckets["events"]:
        event_id = record.get("event_id")
        if isinstance(event_id, str):
            by_uri[f"event:{event_id}"] = (path, record)
    for path, record in buckets["artifact-sets"]:
        set_id = record.get("set_id")
        digest = record.get("set_digest")
        if isinstance(set_id, str):
            by_uri[f"artifact-set:{set_id}"] = (path, record)
        if isinstance(digest, str):
            by_uri[f"artifact-set:{digest}"] = (path, record)
            hex_part = digest.split(":")[-1]
            by_uri[f"artifact-set:{hex_part}"] = (path, record)
        for member in record.get("members") or []:
            if not isinstance(member, dict):
                continue
            member_path = member.get("path")
            member_digest = member.get("digest")
            if isinstance(member_path, str) and isinstance(member_digest, str):
                uri = f"artifact:{member_path}@{member_digest}"
                by_uri[uri] = (path, member)
                by_uri[f"artifact:{member_path}"] = (path, member)
    return by_uri


def _walk_refs(record: Mapping[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    found: List[Tuple[str, Dict[str, Any]]] = []

    def visit(obj: Any, locator: str) -> None:
        if isinstance(obj, dict):
            if {"kind", "uri"} <= set(obj):
                found.append((locator, obj))
            for key, child in obj.items():
                if key in {"kind", "uri", "classification", "schema_version"}:
                    continue
                visit(child, f"{locator}.{key}" if locator else key)
        elif isinstance(obj, list):
            for index, child in enumerate(obj):
                visit(child, f"{locator}[{index}]")

    visit(record, "")
    return found


def _endpoint_finding(
    code: str,
    *,
    kind: str,
    identifier: str,
    path: Optional[str],
    field: str,
    redacted: bool = False,
) -> Dict[str, Any]:
    finding = {
        "code": code,
        "kind": kind,
        "identifier": identifier,
        "field": field,
        "redacted": redacted,
    }
    if path:
        finding["path"] = path
    return finding


def _artifact_uri_from_member(member: Mapping[str, Any]) -> Optional[str]:
    path = member.get("path")
    digest = member.get("digest")
    if isinstance(path, str) and isinstance(digest, str):
        return f"artifact:{path}@{digest}"
    return None


def build_views(
    repository_root: Path,
    *,
    provenance_root: Optional[Path] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    repository_root = Path(repository_root)
    provenance_root = Path(provenance_root) if provenance_root else repository_root / "provenance"
    buckets = collect_sources(provenance_root)
    by_uri = _index_records(buckets)

    def rel_path(path: Path) -> str:
        try:
            return path.resolve().relative_to(provenance_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()

    source_files: List[Tuple[str, bytes]] = []
    for kind in ("events", "runs", "findings", "artifact-sets"):
        for path, _record in buckets[kind]:
            source_files.append((rel_path(path), path.read_bytes()))
    source_files.sort(key=lambda item: item[0])
    source_digests = [
        {"path": name, "sha256": _digest_bytes(data)} for name, data in source_files
    ]

    graph_schema_bytes = (repository_root / GRAPH_SCHEMA_PATH).read_bytes()
    reverse_schema_bytes = (repository_root / REVERSE_SCHEMA_PATH).read_bytes()
    tool_bytes = (repository_root / TOOL_PATH).read_bytes()
    schema_digest = _digest_bytes(graph_schema_bytes + b"\n" + reverse_schema_bytes)
    tool_digest = _digest_bytes(tool_bytes)
    config_digest = _digest_bytes(canonical_bytes(CONFIG))
    generation_id = _generation_id(source_digests, schema_digest, tool_digest, config_digest)
    digests = {
        "schema_sha256": schema_digest,
        "tool_sha256": tool_digest,
        "config_sha256": config_digest,
        "source_sha256": source_digests,
    }

    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []
    findings: List[Dict[str, Any]] = []
    adjacency: Dict[str, List[str]] = defaultdict(list)

    def ensure_node(ref: Mapping[str, Any], *, path: Optional[str] = None) -> str:
        kind = str(ref.get("kind") or "unknown")
        uri = str(ref.get("uri") or "")
        key = _node_id(kind, uri)
        if key not in nodes:
            node = {
                "kind": kind,
                "uri": uri,
                "classification": ref.get("classification"),
                "redacted": _is_redacted(ref),
            }
            if path:
                node["source_path"] = path
            if ref.get("digest"):
                node["digest"] = ref["digest"]
            nodes[key] = node
        return key

    def resolve_endpoint(ref: Mapping[str, Any], field: str, source_path: str) -> None:
        kind = str(ref.get("kind") or "")
        uri = str(ref.get("uri") or "")
        if _is_redacted(ref):
            findings.append(
                _endpoint_finding(
                    "PV-REDACTED-ENDPOINT",
                    kind=kind,
                    identifier=uri,
                    path=source_path,
                    field=field,
                    redacted=True,
                )
            )
            return
        if not uri:
            findings.append(
                _endpoint_finding(
                    "PV-UNRESOLVABLE-ENDPOINT",
                    kind=kind,
                    identifier="",
                    path=source_path,
                    field=field,
                )
            )
            return
        if kind in {"run", "finding", "artifact-set", "artifact"}:
            if uri not in by_uri:
                # artifact URIs may be kind:path@digest already indexed
                alt = uri
                if kind == "artifact" and not uri.startswith("artifact:"):
                    alt = f"artifact:{uri}"
                if alt not in by_uri:
                    findings.append(
                        _endpoint_finding(
                            "PV-DANGLING-ENDPOINT",
                            kind=kind,
                            identifier=uri,
                            path=source_path,
                            field=field,
                        )
                    )

    for path, record in buckets["runs"]:
        rel = rel_path(path)
        ensure_node(
            {
                "kind": "run",
                "uri": f"run:{record.get('run_id')}",
                "classification": record.get("classification"),
            },
            path=rel,
        )
        for locator, ref in _walk_refs(record):
            ensure_node(ref, path=rel)
            resolve_endpoint(ref, locator or "run", rel)

    for path, record in buckets["findings"]:
        rel = rel_path(path)
        ensure_node(
            {
                "kind": "finding",
                "uri": f"finding:{record.get('finding_id')}",
                "classification": record.get("classification"),
                "redacted": bool(record.get("redaction_reason")),
            },
            path=rel,
        )
        for locator, ref in _walk_refs(record):
            ensure_node(ref, path=rel)
            resolve_endpoint(ref, locator or "finding", rel)

    for path, record in buckets["artifact-sets"]:
        rel = rel_path(path)
        ensure_node(
            {
                "kind": "artifact-set",
                "uri": f"artifact-set:{record.get('set_id')}",
                "classification": record.get("classification"),
                "digest": record.get("set_digest"),
            },
            path=rel,
        )
        for member in record.get("members") or []:
            if not isinstance(member, dict):
                continue
            uri = _artifact_uri_from_member(member)
            if uri:
                ensure_node(
                    {
                        "kind": "artifact",
                        "uri": uri,
                        "classification": record.get("classification"),
                        "digest": member.get("digest"),
                        "redacted": member.get("redacted") is True,
                    },
                    path=rel,
                )
                if member.get("redacted") is True:
                    findings.append(
                        _endpoint_finding(
                            "PV-REDACTED-ENDPOINT",
                            kind="artifact",
                            identifier=uri,
                            path=rel,
                            field="members",
                            redacted=True,
                        )
                    )
        for locator, ref in _walk_refs(record):
            ensure_node(ref, path=rel)
            resolve_endpoint(ref, locator or "artifact-set", rel)

    for path, record in buckets["events"]:
        rel = rel_path(path)
        event_id = record.get("event_id")
        relation = record.get("relation")
        source = record.get("source") or {}
        target = record.get("target") or {}
        events.append(
            {
                "event_id": event_id,
                "occurred_at": record.get("occurred_at"),
                "relation": relation,
                "source": _ref_key(source) if isinstance(source, dict) else None,
                "target": _ref_key(target) if isinstance(target, dict) else None,
                "path": rel,
            }
        )
        ensure_node(
            {
                "kind": "event",
                "uri": f"event:{event_id}",
                "classification": record.get("classification"),
            },
            path=rel,
        )
        if isinstance(source, dict):
            src_key = ensure_node(source, path=rel)
            resolve_endpoint(source, "source", rel)
        else:
            src_key = None
            findings.append(
                _endpoint_finding(
                    "PV-UNRESOLVABLE-ENDPOINT",
                    kind="",
                    identifier="",
                    path=rel,
                    field="source",
                )
            )
        if isinstance(target, dict):
            dst_key = ensure_node(target, path=rel)
            resolve_endpoint(target, "target", rel)
        else:
            dst_key = None
            findings.append(
                _endpoint_finding(
                    "PV-UNRESOLVABLE-ENDPOINT",
                    kind="",
                    identifier="",
                    path=rel,
                    field="target",
                )
            )
        if src_key and dst_key:
            edge = {
                "event_id": event_id,
                "relation": relation,
                "source": source.get("uri") if isinstance(source, dict) else None,
                "target": target.get("uri") if isinstance(target, dict) else None,
                "source_kind": source.get("kind") if isinstance(source, dict) else None,
                "target_kind": target.get("kind") if isinstance(target, dict) else None,
            }
            edges.append(edge)
            adjacency[src_key].append(dst_key)
        for locator, ref in _walk_refs(record):
            ensure_node(ref, path=rel)
            if locator not in {"source", "target"}:
                resolve_endpoint(ref, locator or "event", rel)

    cycles = detect_cycles(adjacency)
    for cycle in cycles:
        findings.append(
            {
                "code": "PV-CYCLE",
                "kind": "graph",
                "identifier": " -> ".join(cycle),
                "field": "edges",
                "redacted": False,
                "cycle": cycle,
            }
        )

    node_list = [nodes[key] for key in sorted(nodes)]
    events.sort(key=lambda item: (item.get("occurred_at") or "", item.get("event_id") or ""))
    edges.sort(
        key=lambda item: (
            item.get("relation") or "",
            item.get("source") or "",
            item.get("target") or "",
            item.get("event_id") or "",
        )
    )
    findings.sort(
        key=lambda item: (
            item.get("code") or "",
            item.get("kind") or "",
            item.get("identifier") or "",
            item.get("field") or "",
            item.get("path") or "",
        )
    )

    reverse = build_reverse_indexes(buckets, by_uri)
    reverse["schema"] = CONFIG["reverse_schema"]
    reverse["authority"] = "generated-view"
    reverse["digests"] = digests
    reverse["generation_id"] = generation_id

    graph = {
        "schema": CONFIG["graph_schema"],
        "authority": "generated-view",
        "events": events,
        "nodes": node_list,
        "edges": edges,
        "findings": findings,
        "digests": digests,
        "generation_id": generation_id,
        "counts": {
            "events": len(events),
            "nodes": len(node_list),
            "edges": len(edges),
            "findings": len(findings),
            "sources": len(source_files),
        },
    }
    return graph, reverse


def detect_cycles(adjacency: Mapping[str, List[str]]) -> List[List[str]]:
    """Record cycles as data; callers must not follow a node already on the stack."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {node: WHITE for node in adjacency}
    for node in adjacency:
        color.setdefault(node, WHITE)
        for nxt in adjacency[node]:
            color.setdefault(nxt, WHITE)
    stack: List[str] = []
    cycles: List[List[str]] = []

    def dfs(node: str) -> None:
        color[node] = GRAY
        stack.append(node)
        for nxt in adjacency.get(node, []):
            state = color.get(nxt, WHITE)
            if state == GRAY:
                start = stack.index(nxt)
                cycles.append(stack[start:] + [nxt])
                continue
            if state == WHITE:
                dfs(nxt)
        stack.pop()
        color[node] = BLACK

    for node in sorted(color):
        if color[node] == WHITE:
            dfs(node)
    unique = []
    seen = set()
    for cycle in cycles:
        key = tuple(cycle)
        if key not in seen:
            seen.add(key)
            unique.append(cycle)
    return unique


def walk_without_loops(adjacency: Mapping[str, List[str]], start: str) -> List[str]:
    """Depth-first walk that treats a back-edge as a cycle marker, not a loop."""
    visited: Set[str] = set()
    order: List[str] = []

    def dfs(node: str) -> None:
        if node in visited:
            return
        visited.add(node)
        order.append(node)
        for nxt in adjacency.get(node, []):
            dfs(nxt)

    dfs(start)
    return order


def build_reverse_indexes(
    buckets: Mapping[str, List[Tuple[Path, Dict[str, Any]]]],
    by_uri: Mapping[str, Tuple[Path, Dict[str, Any]]],
) -> Dict[str, Any]:
    issue_criteria: Dict[str, Set[str]] = defaultdict(set)
    issue_runs: Dict[str, Set[str]] = defaultdict(set)
    issue_artifacts: Dict[str, Set[str]] = defaultdict(set)
    issue_findings: Dict[str, Set[str]] = defaultdict(set)
    issue_evidence: Dict[str, Set[str]] = defaultdict(set)
    criterion_evidence: Dict[str, Set[str]] = defaultdict(set)
    evidence_issues: Dict[str, Set[str]] = defaultdict(set)
    evidence_criteria: Dict[str, Set[str]] = defaultdict(set)
    artifact_producer: Dict[str, Set[str]] = defaultdict(set)
    artifact_issue: Dict[str, Set[str]] = defaultdict(set)
    artifact_campaign: Dict[str, Set[str]] = defaultdict(set)
    artifact_input: Dict[str, Set[str]] = defaultdict(set)

    run_issues: Dict[str, Set[str]] = defaultdict(set)
    run_campaigns: Dict[str, Set[str]] = defaultdict(set)
    run_criteria: Dict[str, Set[str]] = defaultdict(set)
    run_outputs: Dict[str, Set[str]] = defaultdict(set)
    run_inputs: Dict[str, Set[str]] = defaultdict(set)

    for _path, record in buckets["runs"]:
        run_uri = f"run:{record.get('run_id')}"
        for ref in record.get("inputs") or []:
            if not isinstance(ref, dict):
                continue
            kind = ref.get("kind")
            uri = ref.get("uri")
            if not isinstance(uri, str):
                continue
            run_inputs[run_uri].add(uri)
            if kind == "issue":
                issue_runs[uri].add(run_uri)
                run_issues[run_uri].add(uri)
            elif kind == "criterion":
                run_criteria[run_uri].add(uri)
                for issue_uri in list(run_issues[run_uri]):
                    issue_criteria[issue_uri].add(uri)
            elif kind == "campaign":
                run_campaigns[run_uri].add(uri)
            elif kind in EVIDENCE_KINDS or kind == "artifact":
                artifact_input[uri].add(run_uri)
        for ref in record.get("outputs") or []:
            if not isinstance(ref, dict):
                continue
            uri = ref.get("uri")
            if isinstance(uri, str):
                run_outputs[run_uri].add(uri)
                artifact_producer[uri].add(run_uri)

    for _path, record in buckets["findings"]:
        finding_uri = f"finding:{record.get('finding_id')}"
        subject = record.get("subject") or {}
        if isinstance(subject, dict) and subject.get("kind") == "issue":
            issue_uri = subject.get("uri")
            if isinstance(issue_uri, str):
                issue_findings[issue_uri].add(finding_uri)
        during = record.get("detected_during") or {}
        if isinstance(during, dict) and during.get("kind") == "run":
            run_uri = during.get("uri")
            if isinstance(run_uri, str):
                for issue_uri in run_issues.get(run_uri, ()):
                    issue_findings[issue_uri].add(finding_uri)
        for ref in record.get("evidence") or []:
            if not isinstance(ref, dict):
                continue
            uri = ref.get("uri")
            if not isinstance(uri, str):
                continue
            if isinstance(subject, dict) and subject.get("kind") == "issue":
                issue_uri = subject.get("uri")
                if isinstance(issue_uri, str):
                    issue_evidence[issue_uri].add(uri)
                    issue_artifacts[issue_uri].add(uri)
                    evidence_issues[uri].add(issue_uri)
                    artifact_issue[uri].add(issue_uri)
            if isinstance(subject, dict) and subject.get("kind") == "criterion":
                crit = subject.get("uri")
                if isinstance(crit, str):
                    criterion_evidence[crit].add(uri)
                    evidence_criteria[uri].add(crit)

    for _path, record in buckets["artifact-sets"]:
        set_uri = f"artifact-set:{record.get('set_id')}"
        producer = record.get("producer") or {}
        producer_uri = producer.get("uri") if isinstance(producer, dict) else None
        if isinstance(producer_uri, str):
            artifact_producer[set_uri].add(producer_uri)
        members = []
        for member in record.get("members") or []:
            if isinstance(member, dict):
                uri = _artifact_uri_from_member(member)
                if uri:
                    members.append(uri)
                    if isinstance(producer_uri, str):
                        artifact_producer[uri].add(producer_uri)
        if isinstance(producer_uri, str) and producer_uri.startswith("run:"):
            for issue_uri in run_issues.get(producer_uri, ()):
                issue_artifacts[issue_uri].add(set_uri)
                artifact_issue[set_uri].add(issue_uri)
                for member_uri in members:
                    issue_artifacts[issue_uri].add(member_uri)
                    artifact_issue[member_uri].add(issue_uri)
            for campaign_uri in run_campaigns.get(producer_uri, ()):
                artifact_campaign[set_uri].add(campaign_uri)
                for member_uri in members:
                    artifact_campaign[member_uri].add(campaign_uri)
            for input_uri in run_inputs.get(producer_uri, ()):
                artifact_input[set_uri].add(input_uri)
                for member_uri in members:
                    artifact_input[member_uri].add(input_uri)

    for _path, record in buckets["events"]:
        source = record.get("source") if isinstance(record.get("source"), dict) else {}
        target = record.get("target") if isinstance(record.get("target"), dict) else {}
        relation = record.get("relation")
        src_kind, src_uri = source.get("kind"), source.get("uri")
        dst_kind, dst_uri = target.get("kind"), target.get("uri")
        if relation == "verifies" and src_kind in EVIDENCE_KINDS:
            if dst_kind == "issue" and isinstance(dst_uri, str) and isinstance(src_uri, str):
                issue_evidence[dst_uri].add(src_uri)
                evidence_issues[src_uri].add(dst_uri)
                issue_artifacts[dst_uri].add(src_uri)
            if dst_kind == "criterion" and isinstance(dst_uri, str) and isinstance(src_uri, str):
                criterion_evidence[dst_uri].add(src_uri)
                evidence_criteria[src_uri].add(dst_uri)
        if relation == "produced-by" and isinstance(src_uri, str) and isinstance(dst_uri, str):
            artifact_producer[src_uri].add(dst_uri)
        if relation == "implements" and dst_kind == "issue" and isinstance(src_uri, str) and isinstance(dst_uri, str):
            artifact_issue[src_uri].add(dst_uri)
            issue_artifacts[dst_uri].add(src_uri)

    def freeze_map(raw: Mapping[str, Set[str]]) -> Dict[str, List[str]]:
        return {key: _sorted_unique(values) for key, values in sorted(raw.items())}

    return {
        "issue": {
            "criteria": freeze_map(issue_criteria),
            "runs": freeze_map(issue_runs),
            "artifacts": freeze_map(issue_artifacts),
            "findings": freeze_map(issue_findings),
            "evidence": freeze_map(issue_evidence),
        },
        "artifact": {
            "producer": freeze_map(artifact_producer),
            "issue": freeze_map(artifact_issue),
            "campaign": freeze_map(artifact_campaign),
            "input": freeze_map(artifact_input),
        },
        "criterion": {"evidence": freeze_map(criterion_evidence)},
        "evidence": {
            "issue": freeze_map(evidence_issues),
            "criterion": freeze_map(evidence_criteria),
        },
    }


def write_views(graph: Mapping[str, Any], reverse: Mapping[str, Any], repository_root: Path) -> Tuple[Path, Path]:
    repository_root = Path(repository_root)
    graph_path = repository_root / GRAPH_OUT
    reverse_path = repository_root / REVERSE_OUT
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(_canonical_json(graph), encoding="utf-8")
    reverse_path.write_text(_canonical_json(reverse), encoding="utf-8")
    return graph_path, reverse_path


def verify_document(document: Mapping[str, Any], expected_kind: str, repository_root: Path, provenance_root: Optional[Path] = None) -> bool:
    graph, reverse = build_views(repository_root, provenance_root=provenance_root)
    expected = graph if expected_kind == "graph" else reverse
    if document.get("generation_id") != expected["generation_id"]:
        raise ProvenanceViewsError("PV-STALE-INDEX", "stale or hand-edited generation_id")
    if _canonical_json(document) != _canonical_json(expected):
        raise ProvenanceViewsError("PV-STALE-INDEX", "view bytes diverge from canonical regeneration")
    return True


def reconcile_counts(graph: Mapping[str, Any], buckets: Mapping[str, List]) -> None:
    if graph["counts"]["events"] != len(buckets["events"]):
        raise ProvenanceViewsError("PV-RECONCILE", "event count mismatch")
    source_ids = {record.get("event_id") for _path, record in buckets["events"]}
    view_ids = {event.get("event_id") for event in graph["events"]}
    if source_ids != view_ids:
        raise ProvenanceViewsError("PV-RECONCILE", "event identity mismatch")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", default=str(ROOT))
    parser.add_argument("--provenance-root")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    repository_root = Path(args.repository_root).resolve()
    provenance_root = Path(args.provenance_root) if args.provenance_root else repository_root / "provenance"
    try:
        graph, reverse = build_views(repository_root, provenance_root=provenance_root)
        buckets = collect_sources(provenance_root)
        reconcile_counts(graph, buckets)
        if args.verify:
            graph_path = repository_root / GRAPH_OUT
            reverse_path = repository_root / REVERSE_OUT
            verify_document(json.loads(graph_path.read_text(encoding="utf-8")), "graph", repository_root, provenance_root)
            verify_document(json.loads(reverse_path.read_text(encoding="utf-8")), "reverse", repository_root, provenance_root)
        if args.write:
            write_views(graph, reverse, repository_root)
        elif not args.verify:
            sys.stdout.write(_canonical_json({"graph": graph, "reverse": reverse}))
        return 0
    except (ProvenanceViewsError, ProvenanceError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
