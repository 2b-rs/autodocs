"""Unified curation-item schema (Feature 0006-03), curation-item@v1.

Read-side adapters that normalize existing review-flag@v1 and
curation-flag@v1 payloads into one unified shape. Does not change how
review_flags.py/curation_flags.py write to disk; see
docs/pipeline/curation-item-schema.md for the full field reference.
"""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any, Dict

_TOOLS_DIR = str(Path(__file__).resolve().parent)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
from canonical_id import resolve_legacy, parse_canonical_id  # noqa: E402
from version_store import latest_version  # noqa: E402

CURATION_ITEM_SCHEMA = "curation-item@v1"

VALID_ITEM_KINDS = (
    "record-field", "record", "ai-amendment", "ai-hypothesis",
    "scrape-observation", "report-entry", "module", "component",
    "design-doc", "process-doc",
)
VALID_ORIGINS = ("tool", "ai", "browser", "curator", "score-scraper")
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
    """Normalize a review-flag@v1 payload into curation-item@v1."""
    canonical, project = _canonical_and_project(payload)
    finding = payload.get("finding") or {}
    status = "claimed" if payload.get("claimed_by") else "open"
    if payload.get("completed_at"):
        status = "applied"
    return {
        "schema": CURATION_ITEM_SCHEMA,
        "canonical_id": canonical,
        "project": project,
        "item_kind": "record-field",
        "field": payload.get("field"),
        "origin": "curator",
        "status": status,
        "current_value": payload.get("current_value"),
        "proposed_value": payload.get("proposed_value"),
        "curator": payload.get("claimed_by") or payload.get("author"),
        "evidence": payload.get("evidence", []),
        "history": payload.get("history", []),
        "created_at": payload.get("created_at"),
        "updated_at": payload.get("updated_at"),
    }


def from_score_record(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Map an Eclipse S-CORE scraped record into curation-item@v1 (0009-05)."""
    canonical = payload.get("canonical_id", "")
    project = payload.get("project", "ECLIPSE/S-CORE")
    kind = payload.get("kind", "module")
    return {
        "schema": CURATION_ITEM_SCHEMA,
        "canonical_id": canonical,
        "project": project,
        "item_kind": kind,
        "field": "body",
        "origin": "score-scraper",
        "status": "open",
        "current_value": payload.get("description"),
        "proposed_value": None,
        "curator": None,
        "evidence": [payload.get("provenance", {})],
        "history": [],
        "version_id": payload.get("version_id"),
        "created_at": None,
        "updated_at": None,
    }
