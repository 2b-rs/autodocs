"""First-class evidence snippet objects (Feature 0006-17).

0006-15 minted the evidence:<uuid7> id family; 0006-18's dependency graph
gives evidence snippets a node kind, but until now nothing actually
constructed one as a concrete object with a mandatory pin to the exact
requirement version it was extracted from. This module is that missing
piece: every evidence snippet MUST carry a source_version (a
requirement-version id from the 0006-16 immutable version store), so
drift detection can say "this evidence snippet is now stale relative to
version X" instead of only "this record changed since some undated
point" (the exact gap 0006-17 was written to close).

Storage: append-only JSONL, one file per canonical requirement, under
_src/spec/evidence/<project>/<kind>/<id>.jsonl -- mirrors version_store.py's
layout convention for consistency.
"""
from __future__ import annotations
import json
import os
import sys
import uuid as _uuid
from datetime import datetime, timezone
from pathlib import Path

_TOOLS_DIR = str(Path(__file__).resolve().parent)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
from canonical_id import parse_canonical_id  # noqa: E402
from version_id import evidence_id, parse_version_id  # noqa: E402
from version_store import get_version  # noqa: E402

EVIDENCE_ROOT = Path(__file__).resolve().parents[1] / "spec" / "evidence"


def _store_path(canonical_id: str) -> Path:
    parsed = parse_canonical_id(canonical_id)
    if parsed is None:
        raise ValueError(f"not a canonical id: {canonical_id!r}")
    return EVIDENCE_ROOT / parsed["project"] / parsed["kind"] / (parsed["id"] + ".jsonl")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def record_evidence_snippet(source_version: str, text: str, reason: str,
                            meta: dict | None = None) -> dict:
    """Create and append one evidence snippet, pinned to source_version
    (a requirement-version id, e.g. from version_store.latest_version()).

    Raises ValueError if source_version is falsy or not a well-formed
    requirement-version id -- source_version is mandatory by design
    (0006-17's whole point), never optional/nullable like
    curation_item.decided_on_version (which may legitimately be unknown
    for pre-existing decisions).
    """
    if not source_version:
        raise ValueError("source_version is required for every evidence snippet (0006-17)")
    parsed = parse_version_id(source_version)
    if parsed is None:
        raise ValueError(f"source_version is not a well-formed requirement-version id: {source_version!r}")
    canonical_id = parsed["canonical_id"]

    entry = {
        "id": evidence_id(),
        "canonical_id": canonical_id,
        "source_version": source_version,
        "text": text,
        "reason": reason,
        "meta": meta or {},
        "created": _now(),
    }
    path = _store_path(canonical_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp-%s" % _uuid.uuid4().hex[:8])
    if path.exists():
        tmp.write_bytes(path.read_bytes())
    with tmp.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    os.replace(tmp, path)
    return entry


def list_evidence_snippets(canonical_id: str) -> list[dict]:
    path = _store_path(canonical_id)
    if not path.exists():
        return []
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def is_stale(snippet: dict) -> bool:
    """True if snippet["source_version"] is no longer the latest recorded
    version for its requirement -- i.e. the requirement changed since this
    evidence was extracted (the exact drift-detection capability 0006-17
    exists to unlock)."""
    resolved = get_version(snippet["source_version"])
    if resolved is None:
        return True  # version itself unknown to the store -- treat as stale
    from version_store import latest_version  # local import avoids a cycle at module load
    latest = latest_version(snippet["canonical_id"])
    return latest is None or latest["version_id"] != snippet["source_version"]
