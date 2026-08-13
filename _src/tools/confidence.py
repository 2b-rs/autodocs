"""Confidence scoring and invalidation state (Feature 0006-19).

Orthogonal to the curation-item lifecycle (0006-06). Builds on the
canonical-item schema (0006-03) and the dependency graph (0006-18).

Formula (resolved 2026-08-13, discussed and refined with the user):
  score = clamp01(base(origin, item_kind) + confirms_bonus + feedback_sum)
  overridden to a fixed 0.05 floor if the node is dismissed
  (dependency_graph.is_dismissed()) -- dismissal caps confidence low but
  never to exactly 0; nothing is ever fully discarded.

Feedback (2026-08-13, user-defined; distinct from the existing "Ingest
Feedback" ACTION in docs/pipeline/actions.md, which names the
curation-decision-ingest tool, not this per-fragment reaction mechanism):
each feedback item has a valence (positive/negative) and a strength in
[0, 1], contributing sign(valence) * strength * FEEDBACK_DELTA_MAX to the
score -- i.e. up to +/-0.15 per feedback item.

Revisit-eligibility rule (2026-08-13, user-defined): every confidence
recompute is recorded with a `cause`. Dismissal of a node blocks the AI
from "answering" that specific decision (can_derive_from() is already
False for it, per 0006-18's Option B) -- and must NOT additionally trigger
a revisit of the AI's own prior knowledge on that node. All OTHER causes
(feedback, confirmation, cascade_invalidation) DO enqueue a revisit, since
the AI may ingest that changed confidence and resynthesize.
"""
from __future__ import annotations
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

_TOOLS_DIR = str(Path(__file__).resolve().parent)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
import dependency_graph as dg  # noqa: E402

GRAPH_ROOT = dg.GRAPH_ROOT
FEEDBACK_FILE = GRAPH_ROOT / "feedback.jsonl"
HISTORY_FILE = GRAPH_ROOT / "confidence_history.jsonl"
REVISITS_FILE = GRAPH_ROOT / "pending_revisits.jsonl"
INVALIDATED_FILE = GRAPH_ROOT / "invalidated.jsonl"

FEEDBACK_DELTA_MAX = 0.15
DISMISSED_FLOOR = 0.05
CONFIRMS_BONUS = 0.25

BASE_SCORES = {
    ("curator", "record"): 0.90,
    ("tool", "scrape-observation"): 0.70,
    ("browser", "scrape-observation"): 0.70,
    ("ai", "ai-amendment"): 0.55,
    ("ai", "ai-hypothesis"): 0.35,
}

VALID_CAUSES = ("feedback", "confirmation", "dismissal", "cascade_invalidation")


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


def record_feedback(node_id: str, valence: str, strength: float = 1.0) -> dict:
    if valence not in ("positive", "negative"):
        raise ValueError(f"valence must be 'positive' or 'negative', got {valence!r}")
    if not (0.0 <= strength <= 1.0):
        raise ValueError(f"strength must be in [0,1], got {strength!r}")
    entry = {"node_id": node_id, "valence": valence, "strength": strength, "created": _now()}
    _append_jsonl(FEEDBACK_FILE, entry)
    return entry


def _feedback_sum(node_id: str) -> float:
    total = 0.0
    for f in _read_jsonl(FEEDBACK_FILE):
        if f["node_id"] != node_id:
            continue
        sign = 1.0 if f["valence"] == "positive" else -1.0
        total += sign * f["strength"] * FEEDBACK_DELTA_MAX
    return total


def _confirms_bonus(node_id: str) -> float:
    for e in dg.list_edges():
        if e["to"] == node_id and e["edge_type"] == "confirms":
            return CONFIRMS_BONUS
    return 0.0


def compute_confidence(node_id: str, origin: str, item_kind: str) -> float:
    base = BASE_SCORES.get((origin, item_kind))
    if base is None:
        raise ValueError(f"no base score defined for origin={origin!r}, item_kind={item_kind!r}")
    score = base + _confirms_bonus(node_id) + _feedback_sum(node_id)
    score = max(0.0, min(1.0, score))
    if dg.is_dismissed(node_id):
        score = DISMISSED_FLOOR
    return round(score, 4)


def record_confidence(node_id: str, score: float, cause: str, inputs: dict | None = None) -> dict:
    """Append a confidence_history entry (never overwritten). Enqueues a
    revisit task UNLESS cause == 'dismissal' (2026-08-13 user rule)."""
    if cause not in VALID_CAUSES:
        raise ValueError(f"unknown cause: {cause!r}")
    entry = {
        "node_id": node_id, "score": score, "cause": cause,
        "inputs": inputs or {}, "computed_at": _now(),
    }
    _append_jsonl(HISTORY_FILE, entry)
    if cause != "dismissal":
        _append_jsonl(REVISITS_FILE, {
            "node_id": node_id, "reason": cause, "enqueued_at": _now(),
        })
    return entry


def list_confidence_history(node_id: str) -> list[dict]:
    return [e for e in _read_jsonl(HISTORY_FILE) if e["node_id"] == node_id]


def list_pending_revisits() -> list[dict]:
    return _read_jsonl(REVISITS_FILE)


def mark_invalidated(node_id: str, reason: str) -> dict:
    """Orthogonal to the curation-item lifecycle (0006-06): flag only,
    never deletes. Callers should also record_confidence(...,
    cause='cascade_invalidation') to trigger a revisit."""
    entry = {"node_id": node_id, "reason": reason, "invalidated_at": _now()}
    _append_jsonl(INVALIDATED_FILE, entry)
    return entry


def is_invalidated(node_id: str) -> bool:
    return any(e["node_id"] == node_id for e in _read_jsonl(INVALIDATED_FILE))


def cascade_invalidate(node_id: str, reason: str) -> set[str]:
    """Walk dependency_graph.find_dependents() (0006-18) and mark every
    reachable dependent invalidated + record a cascade_invalidation
    confidence event for each (which enqueues a revisit, per the rule
    that non-dismissal causes ARE revisit-eligible)."""
    dependents = dg.find_dependents(node_id)
    for dep in dependents:
        mark_invalidated(dep, reason)
    return dependents
