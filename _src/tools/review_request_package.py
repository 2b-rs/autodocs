#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""review_request_package.py -- validator for review-request-package@v1 (0021-02).

Implements the schema defined in
``docs/pipeline/review-request-package-schema.md``. Pure validation module:
does not write to the curation queue (that is 0021-03's ingestion boundary).

Deliberately mirrors the style of ``curation_item.py``'s ``is_conformant``
rather than pulling in an external jsonschema dependency, consistent with
this repo's existing hand-rolled schema validators.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from canonical_id import parse_canonical_id  # noqa: E402
from version_id import parse_version_id, uuid7  # noqa: E402

SCHEMA = "review-request-package@v1"

VALID_CATEGORY = (
    "factual-accuracy", "outdated-source", "missing-context",
    "ai-hallucination-suspected", "other",
)
VALID_TRANSPORT = ("github_issue", "json_export")
VALID_ACTOR_IDENTITY = ("github_authenticated", "self_declared")

REQUIRED_FIELDS = (
    "schema", "client_schema_version", "request_id", "target_canonical_id",
    "target_version_id", "target_content_hash", "target_status_snapshot",
    "source_url", "category", "rationale", "actor_claim", "created_at",
    "transport",
)

_REQUEST_ID_RE = re.compile(r"^review-request:[0-9a-f-]{36}$")
_HASH8_RE = re.compile(r"^[0-9a-f]{8}$")
_ISO8601_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")


def new_request_id() -> str:
    return f"review-request:{uuid7()}"


def validate(package: dict) -> list[str]:
    """Return a list of human-readable errors; empty list means valid."""
    errors = []

    if not isinstance(package, dict):
        return ["package must be a JSON object"]

    for field in REQUIRED_FIELDS:
        if field not in package:
            errors.append(f"missing required field: {field}")

    if package.get("schema") != SCHEMA:
        errors.append(f"unknown schema: {package.get('schema')!r} (expected {SCHEMA!r})")

    rid = package.get("request_id")
    if rid is not None and not _REQUEST_ID_RE.match(rid):
        errors.append(f"request_id does not match 'review-request:<uuid7>': {rid!r}")

    tcid = package.get("target_canonical_id")
    if tcid is not None and parse_canonical_id(tcid) is None:
        errors.append(f"target_canonical_id is not a valid canonical id: {tcid!r}")

    tvid = package.get("target_version_id")
    if tvid is not None and parse_version_id(tvid) is None:
        errors.append(f"target_version_id is not a valid version id: {tvid!r}")

    tchash = package.get("target_content_hash")
    if tchash is not None and not _HASH8_RE.match(str(tchash)):
        errors.append(f"target_content_hash is not 8 hex chars: {tchash!r}")

    if package.get("category") not in VALID_CATEGORY and "category" in package:
        errors.append(f"category must be one of {VALID_CATEGORY}: got {package.get('category')!r}")

    if not str(package.get("rationale") or "").strip():
        errors.append("rationale must be a non-empty string")

    if package.get("transport") not in VALID_TRANSPORT and "transport" in package:
        errors.append(f"transport must be one of {VALID_TRANSPORT}: got {package.get('transport')!r}")

    actor = package.get("actor_claim")
    if isinstance(actor, dict):
        if not str(actor.get("display_name") or "").strip():
            errors.append("actor_claim.display_name must be non-empty")
        if actor.get("identity_kind") not in VALID_ACTOR_IDENTITY:
            errors.append(f"actor_claim.identity_kind must be one of {VALID_ACTOR_IDENTITY}")
    elif "actor_claim" in package:
        errors.append("actor_claim must be an object")

    created_at = package.get("created_at")
    if created_at is not None and not _ISO8601_RE.match(str(created_at)):
        errors.append(f"created_at is not ISO 8601: {created_at!r}")

    refs = package.get("evidence_refs")
    if refs is not None:
        if not isinstance(refs, list):
            errors.append("evidence_refs must be a list")
        else:
            for i, ref in enumerate(refs):
                if not isinstance(ref, dict) or "kind" not in ref or "value" not in ref:
                    errors.append(f"evidence_refs[{i}] must be an object with kind and value")

    return errors


def is_valid(package: dict) -> bool:
    return not validate(package)


def canonical_serialize(package: dict) -> str:
    """Deterministic serialization for de-duplication/comparison purposes."""
    return json.dumps(package, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def dedup_key(package: dict) -> tuple[str, str | None]:
    """De-duplication key per docs/pipeline/review-request-package-schema.md:
    (target_canonical_id, target_version_id) -- NOT request_id."""
    return (package.get("target_canonical_id"), package.get("target_version_id"))


def is_stale(package: dict, current_content_hash: str, current_version_id: str | None) -> bool:
    """Hard-stale only if BOTH content hash and version id mismatch
    (docs/pipeline/review-request-package-schema.md, Staleness rule)."""
    hash_mismatch = package.get("target_content_hash") != current_content_hash
    version_mismatch = (
        package.get("target_version_id") is not None
        and package.get("target_version_id") != current_version_id
    )
    return hash_mismatch and version_mismatch
