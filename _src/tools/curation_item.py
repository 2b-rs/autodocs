"""Unified curation-item schema (Feature 0006-03), curation-item@v1.

Read-side adapters normalize existing review-flag@v1 and curation-flag@v1
payloads into one unified shape. Existing queue writers remain unchanged; see
docs/pipeline/curation-item-schema.md for the field contract.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_TOOLS_DIR = str(Path(__file__).resolve().parent)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from canonical_id import parse_canonical_id, resolve_legacy  # noqa: E402
from version_store import latest_version  # noqa: E402

CURATION_ITEM_SCHEMA = "curation-item@v1"

VALID_ITEM_KINDS = (
    "record-field",
    "record",
    "ai-amendment",
    "ai-hypothesis",
    "scrape-observation",
    "report-entry",
    "module",
    "component",
    "design-doc",
    "process-doc",
)
VALID_ORIGINS = ("tool", "ai", "browser", "curator", "score-scraper")
VALID_STATUSES = (
    "open",
    "claimed",
    "proposed",
    "accepted",
    "rejected",
    "superseded",
    "applied",
)

REQUIRED_FIELDS = (
    "schema",
    "canonical_id",
    "project",
    "release",
    "item_kind",
    "origin",
    "status",
    "subject",
    "current_state",
    "proposed_state",
    "evidence",
    "counter_evidence",
    "decision_basis",
    "campaign",
    "created",
    "claimed_by",
    "decided_by",
    "completed_at",
    "history",
)


def _canonical_and_project(payload: dict[str, Any]) -> tuple[str, str]:
    rid = str(payload.get("id", ""))
    canonical = str(payload.get("canonical_id") or resolve_legacy(rid))
    parsed = parse_canonical_id(canonical) or {}
    project = str(parsed.get("project", "AUTOSAR/AP"))
    return canonical, project


def _status_from_curation_flag(payload: dict[str, Any]) -> str:
    if payload.get("completed_at"):
        return "applied"
    outcome = payload.get("outcome")
    if outcome in ("accepted", "rejected"):
        return str(outcome)
    if outcome in ("proposed", "proposed_change"):
        return "proposed"
    if payload.get("claimed_by"):
        return "claimed"
    # A curation flag is a proposal even before a curator claims it.
    return "proposed"


def _compatibility_aliases(item: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Keep legacy report consumers working while the canonical names are used."""
    item.update(
        {
            "field": payload.get("field"),
            "current_value": item["current_state"],
            "proposed_value": item["proposed_state"],
            "curator": item["claimed_by"] or item["decided_by"],
            "created_at": item["created"],
            "updated_at": payload.get("updated_at") or payload.get("decided_at"),
        }
    )
    return item


def from_review_flag(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize a review-flag@v1 payload into curation-item@v1."""
    canonical, project = _canonical_and_project(payload)
    finding = payload.get("finding") or {}
    status = "claimed" if payload.get("claimed_by") else "open"
    if payload.get("completed_at"):
        status = "applied"
    evidence = payload.get("evidence")
    if evidence is None:
        evidence = [finding] if finding else []
    item: dict[str, Any] = {
        "schema": CURATION_ITEM_SCHEMA,
        "canonical_id": canonical,
        "project": project,
        "release": payload.get("release"),
        "item_kind": payload.get("item_kind") or (
            "scrape-observation" if finding else "record-field"
        ),
        "origin": payload.get("origin") or "tool",
        "status": status,
        "subject": payload.get("subject") or payload.get("reason") or f"Review {payload.get('id', '')}",
        "current_state": payload.get("current_state", payload.get("current_value", finding or None)),
        "proposed_state": payload.get("proposed_state", payload.get("proposed_value")),
        "evidence": evidence,
        "counter_evidence": payload.get("counter_evidence", []),
        "decision_basis": payload.get("decision_basis", {}),
        "campaign": payload.get("campaign"),
        "created": payload.get("created") or payload.get("created_at"),
        "claimed_by": payload.get("claimed_by"),
        "decided_by": payload.get("decided_by") or payload.get("author"),
        "completed_at": payload.get("completed_at"),
        "history": payload.get("history", []),
        "decided_on_version": payload.get("decided_on_version"),
    }
    return _compatibility_aliases(item, payload)


def from_curation_flag(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize a curation-flag@v1 payload into curation-item@v1."""
    canonical, project = _canonical_and_project(payload)
    decision_basis = payload.get("decision_basis") or {}
    item: dict[str, Any] = {
        "schema": CURATION_ITEM_SCHEMA,
        "canonical_id": canonical,
        "project": project,
        "release": payload.get("release"),
        "item_kind": payload.get("item_kind") or "record",
        "origin": payload.get("origin") or "curator",
        "status": _status_from_curation_flag(payload),
        "subject": payload.get("subject") or payload.get("rationale") or f"Curate {payload.get('id', '')}",
        "current_state": payload.get("current_state", payload.get("current_value", payload.get("identity"))),
        "proposed_state": payload.get("proposed_state", payload.get("proposed_value")),
        "evidence": payload.get("evidence", decision_basis.get("spec_evidence", [])),
        "counter_evidence": payload.get("counter_evidence", []),
        "decision_basis": decision_basis,
        "campaign": payload.get("campaign"),
        "created": payload.get("created") or payload.get("created_at") or payload.get("decided_at"),
        "claimed_by": payload.get("claimed_by"),
        "decided_by": payload.get("decided_by"),
        "completed_at": payload.get("completed_at"),
        "history": payload.get("history", []),
        "decided_on_version": payload.get("decided_on_version"),
    }
    return _compatibility_aliases(item, payload)


def from_score_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Map an Eclipse S-CORE scraped record into curation-item@v1."""
    canonical = str(payload.get("canonical_id", ""))
    project = str(payload.get("project", "ECLIPSE/S-CORE"))
    kind = str(payload.get("kind", "module"))
    item: dict[str, Any] = {
        "schema": CURATION_ITEM_SCHEMA,
        "canonical_id": canonical,
        "project": project,
        "release": payload.get("release"),
        "item_kind": kind,
        "origin": "score-scraper",
        "status": "open",
        "subject": payload.get("title") or payload.get("name") or canonical,
        "current_state": payload.get("description"),
        "proposed_state": None,
        "evidence": [payload.get("provenance", {})],
        "counter_evidence": [],
        "decision_basis": {},
        "campaign": payload.get("campaign"),
        "created": None,
        "claimed_by": None,
        "decided_by": None,
        "completed_at": None,
        "history": [],
        "decided_on_version": payload.get("decided_on_version"),
    }
    return _compatibility_aliases(item, payload)


def is_conformant(item: dict[str, Any]) -> bool:
    """Return whether an item satisfies the curation-item@v1 read contract."""
    if any(field not in item for field in REQUIRED_FIELDS):
        return False
    if item.get("schema") != CURATION_ITEM_SCHEMA:
        return False
    canonical = item.get("canonical_id")
    parsed = parse_canonical_id(canonical) if isinstance(canonical, str) else None
    if parsed is None or item.get("project") != parsed.get("project"):
        return False
    if item.get("item_kind") not in VALID_ITEM_KINDS:
        return False
    if item.get("origin") not in VALID_ORIGINS:
        return False
    if item.get("status") not in VALID_STATUSES:
        return False
    if not isinstance(item.get("subject"), str):
        return False
    if not isinstance(item.get("evidence"), list):
        return False
    if not isinstance(item.get("counter_evidence"), list):
        return False
    if not isinstance(item.get("decision_basis"), dict):
        return False
    if not isinstance(item.get("history"), list):
        return False
    if item.get("campaign") is not None and not isinstance(item.get("campaign"), str):
        return False
    if item.get("decided_on_version") is not None and not isinstance(item.get("decided_on_version"), str):
        return False
    return True


def resolve_decided_on_version(canonical_id: str) -> str | None:
    """Return the latest immutable requirement-version ID, if one exists."""
    latest = latest_version(canonical_id)
    if latest is None:
        return None
    version_id = latest.get("version_id")
    return str(version_id) if version_id else None
