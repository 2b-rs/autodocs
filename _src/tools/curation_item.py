"""Unified curation-item schema (Feature 0006-03), curation-item@v1.

Read-side adapters that normalize existing review-flag@v1 and
curation-flag@v1 payloads into one unified shape. Does not change how
review_flags.py/curation_flags.py write to disk; see
docs/pipeline/curation-item-schema.md for the full field reference.
"""
from __future__ import annotations
import sys
from pathlib import Path

_TOOLS_DIR = str(Path(__file__).resolve().parent)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
from canonical_id import resolve_legacy, parse_canonical_id  # noqa: E402
from version_store import latest_version  # noqa: E402

CURATION_ITEM_SCHEMA = "curation-item@v1"

VALID_ITEM_KINDS = (
    "record-field", "record", "ai-amendment", "ai-hypothesis",
    "scrape-observation", "report-entry",
)
VALID_ORIGINS = ("tool", "ai", "browser", "curator")
VALID_STATUSES = (
    "open", "claimed", "proposed", "accepted", "rejected",
    "superseded", "applied",
)


def _canonical_and_project(payload: dict) -> tuple[str, str]:
    rid = payload.get("id", "")
    canonical = payload.get("canonical_id") or resolve_legacy(rid)
    parsed = parse_canonical_id(canonical) or {}
    project = parsed.get("project", "AUTOSAR/AP")
    return canonical, project


def from_review_flag(payload: dict) -> dict:
    """Normalize a review-flag@v1 payload (see review_flags.write_review_flag)
    into curation-item@v1."""
    canonical, project = _canonical_and_project(payload)
    finding = payload.get("finding") or {}
    status = "claimed" if payload.get("claimed_by") else "open"
    if payload.get("completed_at"):
        status = "applied"
    return {
        "schema": CURATION_ITEM_SCHEMA,
        "canonical_id": canonical,
        "project": project,
        "release": payload.get("release"),
        "item_kind": "scrape-observation",
        "origin": "tool",
        "status": status,
        "subject": payload.get("reason") or "review-flag",
        "current_state": None,
        "proposed_state": None,
        "evidence": (finding.get("suspects") or []) + (finding.get("repairs") or []),
        "counter_evidence": [],
        "decision_basis": payload.get("instruction") or {},
        "campaign": payload.get("campaign"),
        "created": payload.get("created"),
        "claimed_by": payload.get("claimed_by"),
        "decided_by": None,
        "decided_on_version": payload.get("decided_on_version"),
        "completed_at": payload.get("completed_at"),
        "history": payload.get("history") or [],
    }


def from_curation_flag(payload: dict) -> dict:
    """Normalize a curation-flag@v1 payload (see
    curation_flags.write_curation_flag) into curation-item@v1."""
    canonical, project = _canonical_and_project(payload)
    outcome = payload.get("outcome")
    status = {
        "accepted": "accepted", "rejected": "rejected",
    }.get(outcome, "proposed")
    if payload.get("completed_at"):
        status = "applied"
    return {
        "schema": CURATION_ITEM_SCHEMA,
        "canonical_id": canonical,
        "project": project,
        "release": payload.get("release"),
        "item_kind": "record",
        "origin": "curator",
        "status": status,
        "subject": payload.get("rationale") or "curation-flag",
        "current_state": None,
        "proposed_state": None,
        "evidence": [],
        "counter_evidence": [],
        "decision_basis": payload.get("decision_basis") or {},
        "campaign": payload.get("campaign"),
        "created": payload.get("created"),
        "claimed_by": payload.get("claimed_by"),
        "decided_by": payload.get("decided_by"),
        "decided_on_version": payload.get("decided_on_version"),
        "completed_at": payload.get("completed_at"),
        "history": payload.get("history") or [],
    }


def is_conformant(item: dict) -> bool:
    required = (
        "schema", "canonical_id", "project", "item_kind", "origin",
        "status", "subject", "campaign", "created", "history",
    )
    if any(k not in item for k in required):
        return False
    if item["schema"] != CURATION_ITEM_SCHEMA:
        return False
    if item["item_kind"] not in VALID_ITEM_KINDS:
        return False
    if item["origin"] not in VALID_ORIGINS:
        return False
    if item["status"] not in VALID_STATUSES:
        return False
    return True


def resolve_decided_on_version(canonical_id: str) -> str | None:
    """0006-17: convenience lookup for future writer wiring -- the
    requirement-version id (from the 0006-16 immutable version store) that
    was CURRENT at the moment this is called, suitable for stamping onto a
    curation decision's decided_on_version field. Returns None if no
    version has been recorded yet for this requirement (store not yet
    backfilled for that record), which callers should treat as "pin
    unavailable", not as an error."""
    entry = latest_version(canonical_id)
    return entry["version_id"] if entry else None
