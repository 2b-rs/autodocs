"""Canonical project/kind/id identity scheme (Feature 0006-02).

Single source of truth for resolving/validating cross-project curatable-item
identity, backed by _src/spec/projects.json. Backward-compatible default:
project="AUTOSAR/AP", kind="record" for any legacy bare id.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from functools import lru_cache

PROJECTS_JSON = Path(__file__).resolve().parents[1] / "spec" / "projects.json"
DEFAULT_PROJECT = "AUTOSAR/AP"
DEFAULT_KIND = "record"


@lru_cache(maxsize=1)
def load_projects() -> dict:
    if not PROJECTS_JSON.exists():
        return {"projects": {}}
    return json.loads(PROJECTS_JSON.read_text(encoding="utf-8"))


def known_projects() -> list[str]:
    return sorted(load_projects().get("projects", {}).keys())


def is_valid(project: str, kind: str) -> bool:
    entry = load_projects().get("projects", {}).get(project)
    if entry is None:
        return False
    return kind in entry.get("item_types", [])


def canonical_id(item_id: str, project: str = DEFAULT_PROJECT,
                  kind: str = DEFAULT_KIND) -> str:
    """Build project/kind/id, e.g. AUTOSAR/AP/record/SWS_UCM_00348."""
    return f"{project}/{kind}/{item_id}"


_CANON_RE = re.compile(r"^(?P<project>[^/]+/[^/]+)/(?P<kind>[^/]+)/(?P<id>.+)$")


def parse_canonical_id(value: str) -> dict | None:
    match = _CANON_RE.match(value)
    if not match:
        return None
    return match.groupdict()


def slug(value: str) -> str:
    """Filesystem-safe key for queue filenames: project/kind/id -> project__kind__id."""
    return value.replace("/", "__")


def unslug(value: str) -> str:
    return value.replace("__", "/")


def resolve_legacy(rid: str, project: str | None = None,
                    kind: str | None = None) -> str:
    """For call sites that only have a bare legacy id: build canonical id
    with defaults if project/kind are not supplied."""
    return canonical_id(rid, project or DEFAULT_PROJECT, kind or DEFAULT_KIND)
