"""Evidence/dependency graph (Feature 0006-18).

First-class node kinds: requirement-version, curation-decision,
evidence-snippet, artifact, human-comment. Typed edges: derived_from,
quotes, supersedes, revisits, comments_on, dismisses, confirms.

Dismissal semantics (Option B, user-confirmed 2026-08-13): dismissing a
node halts FUTURE propagation only (can_derive_from() returns False for
it) but never severs existing edges -- find_dependents() keeps traversing
through them exactly as before. Audit is served by the node-level
dismissed flag/timestamp, not by cutting edges. This keeps the fixed-point
traversal used by later invalidation-cascade work (0006-19/0006-20) simple
and correct: it just walks all existing edges to a fixed point.

Storage: append-only JSON-Lines under _src/spec/graph/, matching the
never-delete pattern used by version_store.py (0006-16).
"""
from __future__ import annotations
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

GRAPH_ROOT = Path(__file__).resolve().parents[1] / "spec" / "graph"
EDGES_FILE = GRAPH_ROOT / "edges.jsonl"
DISMISSED_FILE = GRAPH_ROOT / "dismissed.jsonl"

VALID_NODE_KINDS = (
    "requirement-version", "curation-decision", "evidence-snippet",
    "artifact", "human-comment",
)
VALID_EDGE_TYPES = (
    "derived_from", "quotes", "supersedes", "revisits",
    "comments_on", "dismisses", "confirms",
)


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _append_jsonl(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp-%s" % uuid.uuid4().hex[:8])
    if path.exists():
        tmp.write_bytes(path.read_bytes())
    with tmp.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def add_edge(from_id: str, to_id: str, edge_type: str, meta: dict | None = None) -> dict:
    """Append a typed edge. Idempotent: an identical (from, to, type) edge
    is not duplicated."""
    if edge_type not in VALID_EDGE_TYPES:
        raise ValueError(f"unknown edge_type: {edge_type!r}")
    for existing in _read_jsonl(EDGES_FILE):
        if (existing["from"], existing["to"], existing["edge_type"]) == (from_id, to_id, edge_type):
            return existing
    entry = {
        "from": from_id, "to": to_id, "edge_type": edge_type,
        "meta": meta or {}, "created": _now(),
    }
    _append_jsonl(EDGES_FILE, entry)
    return entry


def list_edges() -> list[dict]:
    return _read_jsonl(EDGES_FILE)


def dismiss_node(node_id: str, reason: str) -> dict:
    """Option B: node-level flag only. Never removes or alters existing
    edges to/from node_id."""
    entry = {"node_id": node_id, "reason": reason, "dismissed_at": _now()}
    _append_jsonl(DISMISSED_FILE, entry)
    return entry


def is_dismissed(node_id: str) -> bool:
    return any(e["node_id"] == node_id for e in _read_jsonl(DISMISSED_FILE))


def can_derive_from(node_id: str) -> bool:
    """False if node_id is dismissed: blocks NEW derived_from/quotes edges
    being added FROM a dismissed node going forward (halt future
    propagation). Does not affect edges that already exist."""
    return not is_dismissed(node_id)


def find_dependents(node_id: str, edge_types: set[str] | None = None) -> set[str]:
    """Cycle-safe fixed-point traversal of all downstream dependents of
    node_id, following edges where `from` matches a visited node.
    Explicitly supports artifact->artifact cycles (real scenario: AI
    resynthesizing its own prior text). Dismissal never blocks this
    traversal (Option B: existing edges are never severed)."""
    edges = list_edges()
    if edge_types is not None:
        edges = [e for e in edges if e["edge_type"] in edge_types]

    visited: set[str] = set()
    frontier = {node_id}
    while frontier:
        next_frontier = set()
        for e in edges:
            if e["from"] in frontier and e["to"] not in visited and e["to"] != node_id:
                next_frontier.add(e["to"])
        visited |= next_frontier
        frontier = next_frontier - visited if False else (next_frontier - visited)
        # fixed point: stop once a pass discovers nothing new
        if not next_frontier:
            break
        frontier = next_frontier
    return visited
