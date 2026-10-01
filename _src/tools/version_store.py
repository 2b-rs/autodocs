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


def record_version(
    canonical_id: str,
    release: str,
    content: str,
    meta: dict | None = None,
    provenance: dict | None = None,
) -> str:
    """Append a new version if this exact (release, content) isn't already
    recorded; always idempotent for identical repeated calls.
    Returns the version_id (existing or newly appended).

    When ``provenance`` is supplied for a *new* line, the 0037-26.03 envelope
    is attached. A duplicate of a legacy line (no envelope) is not backfilled.
    """
    version_id = requirement_version_id(canonical_id, release, content)
    path = _store_path(canonical_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing_match = None
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                existing = json.loads(line)
                if existing.get("version_id") == version_id:
                    existing_match = existing
                    break
    if existing_match is not None:
        env = existing_match.get("provenance")
        if provenance and env:
            from evidence_version_provenance import attach_record_version_provenance
            attach_record_version_provenance(
                version_id=version_id,
                content=content,
                request=provenance,
                existing_envelope=env,
            )
        return version_id  # already recorded; never rewrite the JSONL line

    envelope = None
    if provenance is not None:
        from evidence_version_provenance import attach_record_version_provenance
        envelope = attach_record_version_provenance(
            version_id=version_id,
            content=content,
            request=provenance,
        )

    entry = {
        "version_id": version_id,
        "canonical_id": canonical_id,
        "release": release,
        "content": content,
        "meta": meta or {},
        "recorded_at": _now(),
    }
    if envelope is not None:
        entry["provenance"] = envelope
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


STANDARD_RELEASES: dict[str, tuple[str, ...]] = {
    "AP": ("R17-03", "R17-10", "R18-03", "R18-10", "R19-03", "R19-11", "R20-11", "R25-11"),
    "CP": ("R18-10", "R19-11", "R20-11", "R21-11", "R22-11", "R25-11"),
}


def get_requirement_lifecycle(canonical_id: str, versions: list[dict] | None = None) -> dict:
    """Analyze lifecycle of a requirement across standard releases.
    Returns whether it was dropped/entfallen in later releases, which release it dropped in, etc.
    """
    if versions is None:
        versions = list_versions(canonical_id)
    if not versions:
        return {
            "canonical_id": canonical_id,
            "is_dropped": False,
            "last_active_release": None,
            "dropped_in": [],
            "first_dropped_release": None,
            "latest_platform_release": None,
        }
    parsed = parse_canonical_id(canonical_id)
    project = parsed.get("project", "") if parsed else ""
    platform = "AP" if "AUTOSAR/AP" in canonical_id or project == "AUTOSAR/AP" else ("CP" if "AUTOSAR/CP" in canonical_id or project == "AUTOSAR/CP" else None)
    std_rels = STANDARD_RELEASES.get(platform, ())
    recorded_rels = set(v.get("release") for v in versions if v.get("release"))
    last_rel = versions[-1].get("release")

    dropped_in = []
    if last_rel and std_rels:
        for r in std_rels:
            if r > last_rel and r not in recorded_rels:
                dropped_in.append(r)

    return {
        "canonical_id": canonical_id,
        "is_dropped": bool(dropped_in),
        "last_active_release": last_rel,
        "dropped_in": dropped_in,
        "first_dropped_release": dropped_in[0] if dropped_in else None,
        "latest_platform_release": std_rels[-1] if std_rels else None,
    }

