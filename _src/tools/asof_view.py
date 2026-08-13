"""Point-in-time ("as of release R" / "as of date D") view (Feature 0006-23).

Explicitly a READ-SIDE query problem, per the task text: because nothing in
0006-16 through 0006-19 is ever deleted, reconstructing "what was true as of
R/D" never needs redundant snapshot storage -- it only needs to query the
existing append-only stores correctly. This module adds ZERO new storage.

Query contract: given a release tag OR a date, resolved to the latest
version/decision/artifact at or before that point, return:
  - the requirement-version active at that point
  - the curation decision(s) whose decided_on_version matches or precedes it
  - the evidence/artifact graph nodes valid as of that point
... WITHOUT filtering out superseded/invalidated items: "superseded now"
must not mean "absent from a past view" (explicit task requirement).

Release-ordering assumption (documented, not hidden): release tags recorded
by version_store follow the project's fixed-width AUTOSAR convention
("R25-11", "R32-11", ...) and therefore sort correctly as plain Python
strings. If a non-fixed-width release tag is ever introduced, this ordering
breaks and would need a dedicated parser -- out of scope here since no such
tag exists in this corpus today.
"""
from __future__ import annotations
import sys
from pathlib import Path

_TOOLS_DIR = str(Path(__file__).resolve().parent)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

import version_store as vs  # noqa: E402
import curation_item as ci  # noqa: E402
import dependency_graph as dg  # noqa: E402
import confidence as conf  # noqa: E402


def _version_at_or_before_release(canonical_id: str, release: str) -> dict | None:
    """Latest version whose recorded release tag sorts <= the requested
    release (string-ordered, per this module's documented assumption).
    None if no version qualifies (e.g. requested release predates the
    requirement's first recorded version)."""
    candidates = [v for v in vs.list_versions(canonical_id) if v["release"] <= release]
    if not candidates:
        return None
    return max(candidates, key=lambda v: v["release"])


def _version_at_or_before_date(canonical_id: str, date: str) -> dict | None:
    """Latest version whose recorded_at timestamp sorts <= the requested
    ISO date/timestamp. ISO 8601 timestamps sort correctly as strings."""
    candidates = [v for v in vs.list_versions(canonical_id) if v["recorded_at"] <= date]
    if not candidates:
        return None
    return max(candidates, key=lambda v: v["recorded_at"])


def _artifact_graph_snapshot(canonical_id: str) -> dict:
    """Evidence/artifact graph nodes reachable from canonical_id, WITHOUT
    filtering by dismissal or invalidation state -- per the task's explicit
    requirement that a past view must not hide superseded/invalidated
    items. Each dependent is annotated with its current invalidated/
    dismissed flags so the caller can see (not lose) that state."""
    dependents = sorted(dg.find_dependents(canonical_id))
    return {
        dep: {
            "invalidated": conf.is_invalidated(dep),
            "dismissed": dg.is_dismissed(dep),
        }
        for dep in dependents
    }


def _decisions_for_version(canonical_id: str, version_id: str | None) -> list[dict]:
    """Curation decisions whose decided_on_version matches OR precedes the
    given version_id. \"Precedes\" is judged by release-tag ordering (an
    older decision pinned to an earlier version of the same requirement is
    still a decision that applied \"as of\" a later point in time, since it
    was never superseded by a newer decision at or before that point).
    Never filters by outcome (accepted/rejected decisions both count).
    """
    if version_id is None:
        return []
    resolved = ci.resolve_decided_on_version(canonical_id)
    if resolved is None:
        return []
    if resolved == version_id or resolved <= version_id:
        return [{"canonical_id": canonical_id, "decided_on_version": resolved}]
    return []


def as_of_release(canonical_id: str, release: str) -> dict:
    """The full point-in-time view \"as of release R\" for one requirement."""
    version = _version_at_or_before_release(canonical_id, release)
    version_id = version["version_id"] if version else None
    return {
        "canonical_id": canonical_id,
        "as_of": {"kind": "release", "value": release},
        "version": version,
        "decisions": _decisions_for_version(canonical_id, version_id),
        "artifact_graph": _artifact_graph_snapshot(canonical_id),
    }


def as_of_date(canonical_id: str, date: str) -> dict:
    """The full point-in-time view \"as of date D\" for one requirement."""
    version = _version_at_or_before_date(canonical_id, date)
    version_id = version["version_id"] if version else None
    return {
        "canonical_id": canonical_id,
        "as_of": {"kind": "date", "value": date},
        "version": version,
        "decisions": _decisions_for_version(canonical_id, version_id),
        "artifact_graph": _artifact_graph_snapshot(canonical_id),
    }
