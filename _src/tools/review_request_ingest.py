#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""review_request_ingest.py -- ingestion boundary for review-request-package@v1 (0021-03).

A clearly delegated adapter (per 0021-03's acceptance criteria) rather than a
modification of ``curation_ingest.py`` itself: website re-curation requests
have no ``outcome``/``decided_by`` (they are not a decision, they are a
*request* that a decision be re-examined -- see 0021-01's routing rule), so
reusing ``curation_ingest.validate_package``/``ingest`` unmodified would
silently require fields that don't semantically exist for this input kind.
Both adapters converge on the same ``curation_flags.write_curation_flag``
queue-write primitive and the same ``spec/curation-queue/open/`` directory,
so both produce ordinary ``curation-item@v1``-lineage queue items consumed
by the same downstream AI-agent/Kurator flow.

Trust derivation (0021-01 non-bypass rule / 0021-02 "Two distinct
identities"): the package's own ``actor_claim`` is NEVER trusted as-is.

- ``transport == "github_issue"``: caller MUST supply ``authoritative_actor``
  (the verified GitHub login from the Issue/webhook payload). Result:
  ``trust.identity_kind = "github_authenticated"``.
- ``transport == "json_export"``: no authoritative identity is possible;
  result is always forced to ``trust.identity_kind = "self_declared"``,
  regardless of what ``actor_claim.identity_kind`` says.
- Any package claiming ``github_authenticated`` over ``json_export``
  transport is rejected outright as a spoofed trust claim (0021-03
  acceptance criteria: "rejects spoofed trust claims").

No rejected input creates a queue item; no accepted input writes directly to
a spec record (0021-03 acceptance criteria).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import curation_flags as cf  # noqa: E402
import review_request_package as rrp  # noqa: E402

ITEM_KIND = "review-request"


class IngestOutcome:
    OK = "ok"
    REJECTED_INVALID = "rejected_invalid_schema"
    REJECTED_STALE = "rejected_stale"
    REJECTED_DUPLICATE = "rejected_duplicate"
    REJECTED_SPOOFED_TRUST = "rejected_spoofed_trust"


def _derive_trust(package: dict, authoritative_actor: str | None) -> dict:
    """Derive trust ONLY from transport + server-verified actor, never from
    the package's own actor_claim."""
    transport = package.get("transport")
    claimed_kind = (package.get("actor_claim") or {}).get("identity_kind")

    if transport == "github_issue" and authoritative_actor:
        return {"identity_kind": "github_authenticated", "authoritative_actor": authoritative_actor}

    if transport == "github_issue" and claimed_kind == "github_authenticated" and not authoritative_actor:
        # Claims authenticated transport but caller has no verified actor -- treat as spoofed.
        return {"identity_kind": "__spoofed__", "authoritative_actor": None}

    if transport == "json_export" and claimed_kind == "github_authenticated":
        # json_export can never carry authoritative identity -- spoofed trust claim.
        return {"identity_kind": "__spoofed__", "authoritative_actor": None}

    return {"identity_kind": "self_declared", "authoritative_actor": None}


def _existing_open_dedup_keys() -> dict:
    """Map dedup_key -> flag path, scanned from currently open curation-queue
    review-request items (0021-03: de-duplicate against OPEN items only)."""
    keys = {}
    for path in cf.list_open_flags():
        try:
            import json as _json
            payload = _json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if payload.get("item_kind") != ITEM_KIND:
            continue
        basis = payload.get("decision_basis") or {}
        key = (basis.get("target_canonical_id"), basis.get("target_version_id"))
        keys[key] = path
    return keys


def ingest(package: dict, apply: bool, current_content_hash: str | None = None,
           current_version_id: str | None = None,
           authoritative_actor: str | None = None,
           campaign: str = "website-review-request") -> dict:
    """Validate, de-duplicate, check staleness, and (if apply) enqueue a
    website review-request as a curation-queue item.

    current_content_hash/current_version_id should be looked up by the
    caller from the live record; if omitted, staleness checking is skipped
    (used for pure schema-validation dry runs).
    """
    report = {"outcome": None, "errors": [], "warnings": [], "path": None}

    errors = rrp.validate(package)
    if errors:
        report["outcome"] = IngestOutcome.REJECTED_INVALID
        report["errors"] = errors
        return report

    trust = _derive_trust(package, authoritative_actor)
    if trust["identity_kind"] == "__spoofed__":
        report["outcome"] = IngestOutcome.REJECTED_SPOOFED_TRUST
        report["errors"] = [
            "actor_claim asserts github_authenticated but transport/verification "
            "does not support it (spoofed trust claim)"
        ]
        return report

    if trust["identity_kind"] == "self_declared":
        report["warnings"].append(
            "self_declared identity: lower trust level retained end-to-end "
            "(0021-02 sensitive-field rule).")

    if current_content_hash is not None:
        if rrp.is_stale(package, current_content_hash, current_version_id):
            report["outcome"] = IngestOutcome.REJECTED_STALE
            report["errors"] = [
                "target_content_hash and target_version_id both mismatch the "
                "current record (0021-02 Staleness rule: hard-stale)"
            ]
            return report
        if package.get("target_content_hash") != current_content_hash:
            report["warnings"].append(
                "content hash mismatch with matching version id: soft warning, "
                "forwarded to Kurator rather than rejected (0021-02 Staleness rule).")

    dedup_key = rrp.dedup_key(package)
    existing = _existing_open_dedup_keys()
    if dedup_key in existing:
        report["outcome"] = IngestOutcome.REJECTED_DUPLICATE
        report["errors"] = [
            "an open review-request queue item already exists for this record "
            "(0021-02 Duplicate rule): %s" % existing[dedup_key]
        ]
        return report

    if not apply:
        report["outcome"] = IngestOutcome.OK
        report["dry_run"] = True
        return report

    decision = {
        "id": package["request_id"],
        "outcome": "requested",
        "decided_by": (package.get("actor_claim") or {}).get("display_name"),
        "identity": trust["identity_kind"],
        "decided_at": package["created_at"],
        "rationale": package["rationale"],
        "decision_basis": {
            "item_kind": ITEM_KIND,
            "target_canonical_id": package["target_canonical_id"],
            "target_version_id": package["target_version_id"],
            "target_content_hash": package["target_content_hash"],
            "target_status_snapshot": package["target_status_snapshot"],
            "category": package["category"],
            "evidence_refs": package.get("evidence_refs") or [],
            "source_url": package["source_url"],
            "transport": package["transport"],
            "authoritative_actor": trust["authoritative_actor"],
            "request_id": package["request_id"],
        },
    }
    path = cf.write_curation_flag(decision, campaign=campaign,
                                   project=None, kind=None)
    if path is None:
        report["outcome"] = IngestOutcome.REJECTED_DUPLICATE
        report["errors"] = ["write_curation_flag reported an existing flag for this request id"]
        return report

    # Tag item_kind at top level too, for cheap scanning by _existing_open_dedup_keys
    # and by future report views, without requiring callers to parse decision_basis.
    import json as _json
    payload = _json.loads(path.read_text(encoding="utf-8"))
    payload["item_kind"] = ITEM_KIND
    path.write_text(_json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    report["outcome"] = IngestOutcome.OK
    report["path"] = str(path)
    return report
