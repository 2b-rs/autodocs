"""Typed synthesized knowledge-unit schema (Feature 0006-21).

A synthesized description must not be a single opaque blob. This module
turns the sketched typed-claim object model into a concrete field-by-field
schema plus minimal constructors/validators so later callers can create and
inspect claims consistently.

Schema: typed-claim@v1
Required top-level fields:
- schema: always "typed-claim@v1"
- claim_id: stable claim id (hypothesis_id() from 0006-15)
- parent_artifact_id: the synthesis/artifact this claim belongs to
- claim_type: one of hard_fact / curated_fact / user_comment / ai_inferred
- content: textual claim content
- evidence_refs: list[str] -- direct evidence node ids / version ids / curation ids
- dependency_refs: list[str] -- broader graph dependencies the claim relied on
- current_confidence: float in [0,1]
- confidence_history: append-only list of entries
- invalidation: {invalidated: bool, reason: str|None, invalidated_at: str|None}
- dismissed_from_future_synthesis: bool
- supersedes_claim_ids: list[str] -- earlier claims this claim revisits/replaces
- superseded_by_claim_ids: list[str] -- later claims known to supersede this one
- created: ISO 8601 timestamp
- updated: ISO 8601 timestamp

This is an in-memory / JSON-serializable schema helper only. It does not
create persistence stores or wire itself into a renderer yet.
"""
from __future__ import annotations
from datetime import datetime, timezone
from copy import deepcopy
import sys
from pathlib import Path

_TOOLS_DIR = str(Path(__file__).resolve().parent)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

import version_id as vid  # noqa: E402

VALID_CLAIM_TYPES = (
    "hard_fact",
    "curated_fact",
    "user_comment",
    "ai_inferred",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_claim(parent_artifact_id: str, claim_type: str, content: str,
              evidence_refs: list[str] | None = None,
              dependency_refs: list[str] | None = None,
              current_confidence: float = 0.0,
              supersedes_claim_ids: list[str] | None = None) -> dict:
    if claim_type not in VALID_CLAIM_TYPES:
        raise ValueError(f"unknown claim_type: {claim_type!r}")
    if not (0.0 <= current_confidence <= 1.0):
        raise ValueError("current_confidence must be in [0,1]")
    now = _now()
    return {
        "schema": "typed-claim@v1",
        "claim_id": vid.hypothesis_id(),
        "parent_artifact_id": parent_artifact_id,
        "claim_type": claim_type,
        "content": content,
        "evidence_refs": list(evidence_refs or []),
        "dependency_refs": list(dependency_refs or []),
        "current_confidence": round(float(current_confidence), 4),
        "confidence_history": [],
        "invalidation": {
            "invalidated": False,
            "reason": None,
            "invalidated_at": None,
        },
        "dismissed_from_future_synthesis": False,
        "supersedes_claim_ids": list(supersedes_claim_ids or []),
        "superseded_by_claim_ids": [],
        "created": now,
        "updated": now,
    }


def validate_claim(claim: dict) -> None:
    required = {
        "schema", "claim_id", "parent_artifact_id", "claim_type", "content",
        "evidence_refs", "dependency_refs", "current_confidence",
        "confidence_history", "invalidation",
        "dismissed_from_future_synthesis", "supersedes_claim_ids",
        "superseded_by_claim_ids", "created", "updated",
    }
    missing = sorted(required - set(claim))
    if missing:
        raise ValueError(f"missing required fields: {missing}")
    if claim["schema"] != "typed-claim@v1":
        raise ValueError(f"unexpected schema: {claim['schema']!r}")
    if claim["claim_type"] not in VALID_CLAIM_TYPES:
        raise ValueError(f"unknown claim_type: {claim['claim_type']!r}")
    score = claim["current_confidence"]
    if not isinstance(score, (int, float)) or not (0.0 <= float(score) <= 1.0):
        raise ValueError("current_confidence must be numeric in [0,1]")
    inv = claim["invalidation"]
    if not isinstance(inv, dict) or set(inv.keys()) != {"invalidated", "reason", "invalidated_at"}:
        raise ValueError("invalidation must be a dict with keys invalidated/reason/invalidated_at")
    if not isinstance(claim["dismissed_from_future_synthesis"], bool):
        raise ValueError("dismissed_from_future_synthesis must be bool")


def append_confidence(claim: dict, score: float, cause: str, inputs: dict | None = None) -> dict:
    validate_claim(claim)
    if not (0.0 <= score <= 1.0):
        raise ValueError("score must be in [0,1]")
    entry = {
        "score": round(float(score), 4),
        "cause": cause,
        "inputs": deepcopy(inputs or {}),
        "computed_at": _now(),
    }
    claim["confidence_history"].append(entry)
    claim["current_confidence"] = entry["score"]
    claim["updated"] = entry["computed_at"]
    return claim


def mark_invalidated(claim: dict, reason: str) -> dict:
    validate_claim(claim)
    ts = _now()
    claim["invalidation"] = {
        "invalidated": True,
        "reason": reason,
        "invalidated_at": ts,
    }
    claim["updated"] = ts
    return claim


def dismiss_from_future_synthesis(claim: dict) -> dict:
    validate_claim(claim)
    claim["dismissed_from_future_synthesis"] = True
    claim["updated"] = _now()
    return claim


def link_supersession(old_claim: dict, new_claim: dict) -> tuple[dict, dict]:
    validate_claim(old_claim)
    validate_claim(new_claim)
    if old_claim["claim_id"] not in new_claim["supersedes_claim_ids"]:
        new_claim["supersedes_claim_ids"].append(old_claim["claim_id"])
    if new_claim["claim_id"] not in old_claim["superseded_by_claim_ids"]:
        old_claim["superseded_by_claim_ids"].append(new_claim["claim_id"])
    ts = _now()
    old_claim["updated"] = ts
    new_claim["updated"] = ts
    return old_claim, new_claim
