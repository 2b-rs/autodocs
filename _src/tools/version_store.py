"""Immutable, append-only requirement-version store (Feature 0006-16).

Separate from the current mutable record store
(_src/spec/records/<MODULE>/<ID>.json), which remains the "current
 pointer" view. This store retains every prior content snapshot per
requirement, keyed by the requirement-version ID minted in
version_id.py (0006-15): "<canonical-id>@rel:<release>#<hash8>".

Layout: _src/spec/versions/<project>/<kind>/<id>.jsonl
  - one JSON object per line, appended only, never rewritten in place.
  - idempotent: recording identical (release, content) twice is a no-op,
    since the resulting version_id (and thus the JSON line) is identical.

Retention: entries are never deleted or edited. Old versions remain
retrievable via get_version()/list_versions() indefinitely.
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
from canonical_id import parse_canonical_id  # noqa: E402
from version_id import requirement_version_id, parse_version_id  # noqa: E402

VERSIONS_ROOT = Path(__file__).resolve().parents[1] / "spec" / "versions"


def _store_path(canonical_id: str) -> Path:
    parsed = parse_canonical_id(canonical_id)
    if parsed is None:
        raise ValueError(f"not a canonical id: {canonical_id!r}")
    return VERSIONS_ROOT / parsed["project"] / parsed["kind"] / (parsed["id"] + ".jsonl")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def record_version(canonical_id: str, release: str, content: str, meta: dict | None = None) -> str:
    """Append a new version if this exact (release, content) isn't already
    the most recent entry; always idempotent for identical repeated calls.
    Returns the version_id (existing or newly appended)."""
    version_id = requirement_version_id(canonical_id, release, content)
    path = _store_path(canonical_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                existing = json.loads(line)
                if existing.get("version_id") == version_id:
                    return version_id  # already recorded, no-op

    entry = {
        "version_id": version_id,
        "canonical_id": canonical_id,
        "release": release,
        "content": content,
        "meta": meta or {},
        "recorded_at": _now(),
    }
    tmp = path.with_suffix(path.suffix + ".tmp-%s" % uuid.uuid4().hex[:8])
    if path.exists():
        tmp.write_bytes(path.read_bytes())
    with tmp.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    os.replace(tmp, path)  # atomic swap; original file content is only ever appended to
    return version_id


def list_versions(canonical_id: str) -> list[dict]:
    """All recorded versions for this canonical id, oldest-first. Never
    raises if none exist; returns []."""
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


def get_version(version_id: str) -> dict | None:
    """Look up one exact version by its version_id. O(versions for that
    requirement); fine at this project's scale."""
    parsed = parse_version_id(version_id)
    if parsed is None:
        return None
    for entry in list_versions(parsed["canonical_id"]):
        if entry["version_id"] == version_id:
            return entry
    return None


def latest_version(canonical_id: str) -> dict | None:
    versions = list_versions(canonical_id)
    return versions[-1] if versions else None
