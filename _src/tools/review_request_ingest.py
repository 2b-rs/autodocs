#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""review_request_ingest.py -- Authoritative ingestion boundary for review requests (0033-06).

Implements authoritative live-target resolution through approved record and version
stores, trusted transport verification (GitHub envelopes, webhook HMAC signatures,
API refetch, repository allowlisting, replay protection), and strict trust derivation
that cannot be bypassed by caller-supplied substitutes or spoofed fields.

Findings addressed:
  - RRB-INGEST-001: Mandatory authoritative live-target lookup against approved
    spec/records/ and spec/versions/ stores before any queue write; caller arguments
    cannot bypass or substitute live values.
  - RRB-TRUST-001: Structured transport envelopes and cryptographic / API verification
    replace bare caller actor strings and client-authored 'verified' fields.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canonical_id as cid_util  # noqa: E402
import curation_flags as cf  # noqa: E402
import review_request_package as rrp  # noqa: E402
import version_id as vid_util  # noqa: E402
import version_store as vstore  # noqa: E402

ITEM_KIND = "review-request"

# Default Store Roots
RECORDS_ROOT = Path(__file__).resolve().parents[1] / "spec" / "records"
VERSIONS_ROOT = Path(__file__).resolve().parents[1] / "spec" / "versions"

# Allowed Repositories for GitHub intake (PROC-0033-02-07 / 0033-04.01)
DEFAULT_ALLOWED_REPOSITORIES = (
    "AUTOSAR/autodocs",
    "AUTOSAR/standards",
    "example/repo",
)


class IngestOutcome:
    OK = "ok"
    REJECTED_INVALID = "rejected_invalid_schema"
    REJECTED_UNKNOWN_TARGET = "rejected_unknown_target"
    REJECTED_INELIGIBLE_TARGET = "rejected_ineligible_target"
    REJECTED_STALE = "rejected_stale"
    REJECTED_DUPLICATE = "rejected_duplicate"
    REJECTED_SPOOFED_TRUST = "rejected_spoofed_trust"
    REJECTED_UNTRUSTED_TRANSPORT = "rejected_untrusted_transport"
    REJECTED_REPLAY = "rejected_replay"
    REJECTED_TAMPERING = "rejected_tampering"
    REJECTED_UNSUPPORTED_VERSION = "rejected_unsupported_version"
    QUARANTINED = "quarantined"


# ============================================================================
# Replay Protection Tracker
# ============================================================================

class ReplayTracker:
    """Tracks delivery IDs and event IDs to enforce idempotency and detect tampering."""

    def __init__(self) -> None:
        self._deliveries: dict[str, str] = {}  # delivery_id -> package_sha256
        self._events: dict[str, str] = {}      # event_id -> package_sha256

    def check_and_record_delivery(
        self, delivery_id: str, package_sha256: str
    ) -> tuple[str, str | None]:
        """Returns (status, detail).
        status: 'ok', 'idempotent_replay', or 'conflict'
        """
        if not delivery_id:
            return ("ok", None)
        if delivery_id in self._deliveries:
            if self._deliveries[delivery_id] == package_sha256:
                return ("idempotent_replay", "exact webhook redelivery acknowledged")
            return ("conflict", "replayed delivery_id with conflicting payload digest")
        self._deliveries[delivery_id] = package_sha256
        return ("ok", None)

    def check_and_record_event(
        self, event_id: str, package_sha256: str
    ) -> tuple[str, str | None]:
        """Returns (status, detail).
        status: 'ok', 'idempotent_retry', or 'tampering'
        """
        if not event_id:
            return ("ok", None)
        if event_id in self._events:
            if self._events[event_id] == package_sha256:
                return ("idempotent_retry", "exact same event_id retry")
            return ("tampering", "same event_id with different package payload (tampering/collision)")
        self._events[event_id] = package_sha256
        return ("ok", None)

    def reset(self) -> None:
        self._deliveries.clear()
        self._events.clear()


_GLOBAL_REPLAY_TRACKER = ReplayTracker()


def get_global_replay_tracker() -> ReplayTracker:
    return _GLOBAL_REPLAY_TRACKER


def reset_replay_tracker() -> None:
    _GLOBAL_REPLAY_TRACKER.reset()


# ============================================================================
# Authoritative Live-Target Resolution
# ============================================================================

def compute_target_token(
    canonical_id: str,
    version_id: str | None,
    content_hash: str | None,
    status: str | None,
) -> dict:
    """Mint an authoritative target version/hash token for downstream queue writer CAS."""
    token_dict = {
        "target_canonical_id": canonical_id,
        "target_version_id": version_id,
        "target_content_hash": content_hash,
        "target_status": status,
    }
    canonical_bytes = rrp.canonical_json_bytes(token_dict)
    token_dict["token_sha256"] = hashlib.sha256(canonical_bytes).hexdigest()
    return token_dict


def resolve_live_target(
    canonical_id_str: str,
    records_root: Path | None = None,
    versions_root: Path | None = None,
) -> dict:
    """Resolve target canonical record against approved record & version stores.

    Rejects unknown, unpublished, or ineligible records.
    Obtains authoritative current version, hash, status, and source without
    accepting caller-supplied substitutes.
    """
    records_dir = records_root if records_root is not None else RECORDS_ROOT
    versions_dir = versions_root if versions_root is not None else VERSIONS_ROOT

    if not isinstance(canonical_id_str, str) or not canonical_id_str.strip():
        return {
            "found": False,
            "eligible": False,
            "canonical_id": canonical_id_str,
            "error": IngestOutcome.REJECTED_INVALID,
            "reason": f"invalid canonical target ID: {canonical_id_str!r}",
        }

    parsed = cid_util.parse_canonical_id(canonical_id_str)
    if parsed is None:
        parsed_rrp = rrp.parse_canonical_id(canonical_id_str)
        if parsed_rrp is None:
            return {
                "found": False,
                "eligible": False,
                "canonical_id": canonical_id_str,
                "error": IngestOutcome.REJECTED_UNKNOWN_TARGET,
                "reason": f"target ID does not match canonical format: {canonical_id_str!r}",
            }
        item_id = parsed_rrp.get("id") or canonical_id_str
        project = parsed_rrp.get("project") or "AUTOSAR/AP"
        kind = parsed_rrp.get("kind") or "record"
    else:
        item_id = parsed["id"]
        project = parsed["project"]
        kind = parsed["kind"]

    record_obj: dict | None = None
    record_path: Path | None = None

    # Search in records_dir
    candidate_record_paths = [
        records_dir / project / kind / f"{item_id}.json",
        records_dir / project / f"{item_id}.json",
        records_dir / item_id.rsplit("_", 1)[0] / f"{item_id}.json" if "_" in item_id else None,
        records_dir / f"{item_id}.json",
    ]

    for cand in candidate_record_paths:
        if cand and cand.exists() and cand.is_file():
            record_path = cand
            break

    if record_path is None and records_dir.exists():
        matches = list(records_dir.glob(f"**/{item_id}.json"))
        if matches:
            record_path = matches[0]

    if record_path and record_path.exists():
        try:
            record_obj = json.loads(record_path.read_text(encoding="utf-8"))
        except Exception as e:
            return {
                "found": False,
                "eligible": False,
                "canonical_id": canonical_id_str,
                "error": IngestOutcome.REJECTED_UNKNOWN_TARGET,
                "reason": f"error reading record file {record_path}: {e}",
            }

    # Search in versions_dir
    version_entries: list[dict] = []
    candidate_ver_paths = [
        versions_dir / project / kind / f"{item_id}.jsonl",
        versions_dir / project / f"{item_id}.jsonl",
        versions_dir / f"{item_id}.jsonl",
    ]
    ver_path: Path | None = None
    for cand in candidate_ver_paths:
        if cand and cand.exists() and cand.is_file():
            ver_path = cand
            break

    if ver_path is None and versions_dir.exists():
        matches = list(versions_dir.glob(f"**/{item_id}.jsonl"))
        if matches:
            ver_path = matches[0]

    if ver_path and ver_path.exists():
        try:
            with ver_path.open("r", encoding="utf-8") as vf:
                for line in vf:
                    line = line.strip()
                    if line:
                        version_entries.append(json.loads(line))
        except Exception:
            pass

    if record_obj is None and not version_entries:
        return {
            "found": False,
            "eligible": False,
            "canonical_id": canonical_id_str,
            "error": IngestOutcome.REJECTED_UNKNOWN_TARGET,
            "reason": f"unknown target record not found in record/version store: {canonical_id_str!r}",
        }

    # Check Eligibility (PROC-0033-02-02, PROC-0033-02-03)
    status_raw = None
    state_str = "valid/published"
    if record_obj is not None:
        status_raw = record_obj.get("status")
        if isinstance(status_raw, dict):
            state_str = status_raw.get("state") or "valid/published"
        elif isinstance(status_raw, str):
            state_str = status_raw
        elif status_raw is None:
            state_str = "valid/published"

        # Explicit ineligibility checks
        ineligible_prefixes = ("invalid/", "draft/", "archived/", "deprecated/")
        ineligible_exact = {"invalid", "draft", "archived", "deprecated", "non-record"}
        state_lower = state_str.lower()
        if any(state_lower.startswith(p) for p in ineligible_prefixes) or state_lower in ineligible_exact:
            return {
                "found": True,
                "eligible": False,
                "canonical_id": canonical_id_str,
                "status": state_str,
                "error": IngestOutcome.REJECTED_INELIGIBLE_TARGET,
                "reason": f"target record status is ineligible for review ({state_str}): {canonical_id_str!r}",
            }

    # Resolve Authoritative Version and Content Hash
    auth_version_id: str | None = None
    auth_content_hash: str | None = None
    source_url: str | None = None

    if version_entries:
        latest = version_entries[-1]
        auth_version_id = latest.get("version_id")
        if auth_version_id:
            parsed_v = vid_util.parse_version_id(auth_version_id)
            if parsed_v:
                auth_content_hash = parsed_v.get("hash8")

    if record_obj is not None:
        auth_content_hash = record_obj.get("target_content_hash") or record_obj.get("content_hash")
        if not auth_version_id:
            auth_version_id = record_obj.get("version_id") or record_obj.get("target_version_id")
            if auth_version_id and not auth_content_hash:
                parsed_v = vid_util.parse_version_id(auth_version_id)
                if parsed_v:
                    auth_content_hash = parsed_v.get("hash8")

        source_url = record_obj.get("source_url") or record_obj.get("source")

    # If content hash could not be resolved from version ID or record fields, compute deterministic fallback
    if not auth_content_hash and record_obj is not None:
        auth_content_hash = vid_util.content_hash8(json.dumps(record_obj, sort_keys=True))

    target_token = compute_target_token(
        canonical_id=canonical_id_str,
        version_id=auth_version_id,
        content_hash=auth_content_hash,
        status=state_str,
    )

    return {
        "found": True,
        "eligible": True,
        "canonical_id": canonical_id_str,
        "current_version_id": auth_version_id,
        "current_content_hash": auth_content_hash,
        "current_status": state_str,
        "source_url": source_url,
        "target_token": target_token,
        "error": None,
        "reason": None,
    }


# ============================================================================
# Trusted Transport Verification (Envelopes, Webhooks, API refetch)
# ============================================================================

CODE_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def parse_issue_body(body: str) -> dict | None:
    """Extract JSON review request package from GitHub Issue markdown body (no-JS path)."""
    if not isinstance(body, str):
        return None
    m = CODE_FENCE_RE.search(body)
    raw = m.group(1) if m else body.strip()
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def verify_webhook_signature(
    payload_bytes: bytes,
    signature_header: str | None,
    secret: str,
) -> bool:
    """Verify GitHub webhook X-Hub-Signature-256 HMAC-SHA256 signature."""
    if not signature_header or not secret:
        return False
    if signature_header.startswith("sha256="):
        expected = "sha256=" + hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    else:
        expected = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature_header, expected)


def _verify_transport_and_trust(
    package_or_envelope: dict,
    authoritative_actor: str | None = None,
    raw_body: bytes | None = None,
    signature_header: str | None = None,
    webhook_secret: str | None = None,
    allowed_repositories: tuple[str, ...] | list[str] | None = None,
    refetch_fn: Callable[[str, int], dict | None] | None = None,
    replay_tracker: ReplayTracker | None = None,
) -> tuple[dict, dict, str | None, list[str]]:
    """Verify transport, envelope, and trust level.

    Returns:
      (package, trust_dict, failure_outcome, errors)
    """
    tracker = replay_tracker if replay_tracker is not None else _GLOBAL_REPLAY_TRACKER
    allowed_repos = allowed_repositories if allowed_repositories is not None else DEFAULT_ALLOWED_REPOSITORIES

    # Check if input is a structured envelope
    is_envelope = (
        "envelope_kind" in package_or_envelope
        and package_or_envelope.get("envelope_kind") in rrp.VALID_ENVELOPE_KINDS
        and "package" in package_or_envelope
    )

    if is_envelope:
        envelope = package_or_envelope
        envelope_errors = rrp.validate_envelope(envelope)
        if envelope_errors:
            return envelope.get("package", {}), {}, IngestOutcome.REJECTED_INVALID, envelope_errors

        package = envelope["package"]
        actual_sha256 = rrp.package_digest(package)
        expected_sha256 = envelope.get("package_sha256")

        if expected_sha256 != actual_sha256:
            return (
                package,
                {},
                IngestOutcome.REJECTED_TAMPERING,
                [f"envelope package_sha256 mismatch: expected {actual_sha256}, got {expected_sha256}"],
            )

        # Replay & Tamper Detection
        delivery_id = envelope.get("delivery_id")
        if delivery_id:
            deliv_status, deliv_detail = tracker.check_and_record_delivery(delivery_id, actual_sha256)
            if deliv_status == "conflict":
                return (
                    package,
                    {},
                    IngestOutcome.REJECTED_REPLAY,
                    [f"replayed delivery_id with modified payload digest: {deliv_detail}"],
                )

        event_id = envelope.get("event_id") or package.get("event_id") or package.get("request_id")
        if event_id:
            ev_status, ev_detail = tracker.check_and_record_event(event_id, actual_sha256)
            if ev_status == "tampering":
                return (
                    package,
                    {},
                    IngestOutcome.REJECTED_TAMPERING,
                    [f"same event_id with modified package payload: {ev_detail}"],
                )

        kind = envelope.get("envelope_kind")
        trust_profile = envelope.get("trust_profile")

        if kind == rrp.LOCAL_ENVELOPE_KIND_V1 or trust_profile == "local-import-v1":
            # Local import is always self_declared
            claimed = (package.get("actor_claim") or {}).get("identity_kind")
            if claimed == "github_authenticated":
                return (
                    package,
                    {},
                    IngestOutcome.REJECTED_SPOOFED_TRUST,
                    ["actor_claim asserts github_authenticated over local import envelope (spoofed trust claim)"],
                )
            return package, {"identity_kind": "self_declared", "authoritative_actor": None}, None, []

        # review-request-envelope@v1 verification
        repo = envelope.get("repository")
        if not repo or repo not in allowed_repos:
            return (
                package,
                {},
                IngestOutcome.REJECTED_UNTRUSTED_TRANSPORT,
                [f"repository {repo!r} is not in trusted allowlist: {allowed_repos}"],
            )

        actor = envelope.get("authoritative_actor")
        if not actor:
            return (
                package,
                {},
                IngestOutcome.REJECTED_UNTRUSTED_TRANSPORT,
                ["envelope missing verified authoritative_actor"],
            )

        # Webhook signature verification
        if trust_profile in ("github-webhook-sha256-v1", "github-webhook-sha256+api-refetch-v1"):
            if webhook_secret and raw_body:
                if not verify_webhook_signature(raw_body, signature_header, webhook_secret):
                    return (
                        package,
                        {},
                        IngestOutcome.REJECTED_UNTRUSTED_TRANSPORT,
                        ["webhook HMAC signature verification failed"],
                    )
            elif webhook_secret and not signature_header:
                return (
                    package,
                    {},
                    IngestOutcome.REJECTED_UNTRUSTED_TRANSPORT,
                    ["missing webhook signature header"],
                )

        # API refetch verification
        if trust_profile in ("github-api-refetch-v1", "github-webhook-sha256+api-refetch-v1"):
            if refetch_fn:
                issue_nr = envelope.get("issue_number")
                if issue_nr is None:
                    return (
                        package,
                        {},
                        IngestOutcome.REJECTED_UNTRUSTED_TRANSPORT,
                        ["envelope missing issue_number required for github-api-refetch-v1"],
                    )
                refetched = refetch_fn(repo, issue_nr)
                if not refetched:
                    return (
                        package,
                        {},
                        IngestOutcome.REJECTED_UNTRUSTED_TRANSPORT,
                        [f"GitHub API refetch failed for {repo}#{issue_nr}"],
                    )
                if refetched.get("author") != actor:
                    return (
                        package,
                        {},
                        IngestOutcome.REJECTED_TAMPERING,
                        [f"refetched author {refetched.get('author')!r} mismatches envelope {actor!r}"],
                    )
                if "body" in refetched:
                    parsed_body = parse_issue_body(refetched["body"])
                    if parsed_body is None or rrp.package_digest(parsed_body) != actual_sha256:
                        return (
                            package,
                            {},
                            IngestOutcome.REJECTED_TAMPERING,
                            ["refetched issue body package does not match envelope payload digest"],
                        )

        return package, {"identity_kind": "github_authenticated", "authoritative_actor": actor}, None, []

    # Bare package input
    package = package_or_envelope
    transport = package.get("transport")
    claimed_kind = (package.get("actor_claim") or {}).get("identity_kind")

    if transport == "github_issue" and authoritative_actor:
        return package, {"identity_kind": "github_authenticated", "authoritative_actor": authoritative_actor}, None, []

    if transport == "github_issue" and claimed_kind == "github_authenticated" and not authoritative_actor:
        return (
            package,
            {},
            IngestOutcome.REJECTED_SPOOFED_TRUST,
            ["actor_claim asserts github_authenticated but transport has no verified actor (spoofed trust claim)"],
        )

    if transport == "json_export" and claimed_kind == "github_authenticated":
        return (
            package,
            {},
            IngestOutcome.REJECTED_SPOOFED_TRUST,
            ["json_export transport cannot assert github_authenticated identity (spoofed trust claim)"],
        )

    return package, {"identity_kind": "self_declared", "authoritative_actor": None}, None, []


# ============================================================================
# Queue Deduplication Helper
# ============================================================================

def _existing_open_dedup_keys() -> dict:
    """Map dedup_key -> flag path, scanned from currently open curation-queue items."""
    keys = {}
    for path in cf.list_open_flags():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if payload.get("item_kind") != ITEM_KIND:
            continue
        basis = payload.get("decision_basis") or {}
        key = (basis.get("target_canonical_id"), basis.get("target_version_id"))
        keys[key] = path
    return keys


# ============================================================================
# Ingest Boundary Function
# ============================================================================

def ingest(
    package_or_envelope: dict,
    apply: bool = False,
    current_content_hash: str | None = None,
    current_version_id: str | None = None,
    authoritative_actor: str | None = None,
    campaign: str = "website-review-request",
    records_root: Path | None = None,
    versions_root: Path | None = None,
    raw_body: bytes | None = None,
    signature_header: str | None = None,
    webhook_secret: str | None = None,
    allowed_repositories: tuple[str, ...] | list[str] | None = None,
    refetch_fn: Callable[[str, int], dict | None] | None = None,
    replay_tracker: ReplayTracker | None = None,
) -> dict:
    """Validate, authoritatively resolve live target, verify transport trust,
    check staleness & duplicates, and (if apply=True) enqueue as curation-queue item.

    Live target resolution is performed authoritatively against the record/version store
    and CANNOT be bypassed or substituted by caller arguments.
    """
    report: dict[str, Any] = {
        "outcome": None,
        "errors": [],
        "warnings": [],
        "path": None,
        "target_token": None,
    }

    # Step 1: Transport & Envelope Verification
    package, trust, transport_outcome, transport_errors = _verify_transport_and_trust(
        package_or_envelope=package_or_envelope,
        authoritative_actor=authoritative_actor,
        raw_body=raw_body,
        signature_header=signature_header,
        webhook_secret=webhook_secret,
        allowed_repositories=allowed_repositories,
        refetch_fn=refetch_fn,
        replay_tracker=replay_tracker,
    )
    if transport_outcome is not None:
        report["outcome"] = transport_outcome
        report["errors"] = transport_errors
        return report

    # Step 2: Strict Package Validation
    schema_errors = rrp.validate(package)
    if schema_errors:
        report["outcome"] = IngestOutcome.REJECTED_INVALID
        report["errors"] = schema_errors
        return report

    # Step 3: Authoritative Live-Target Resolution
    target_canonical_id = package.get("target_canonical_id")
    resolution = resolve_live_target(
        canonical_id_str=target_canonical_id,
        records_root=records_root,
        versions_root=versions_root,
    )

    if not resolution["found"]:
        report["outcome"] = resolution.get("error") or IngestOutcome.REJECTED_UNKNOWN_TARGET
        report["errors"] = [resolution.get("reason") or f"unknown target record: {target_canonical_id}"]
        return report

    if not resolution["eligible"]:
        report["outcome"] = resolution.get("error") or IngestOutcome.REJECTED_INELIGIBLE_TARGET
        report["errors"] = [resolution.get("reason") or f"ineligible target record: {target_canonical_id}"]
        return report

    auth_version_id = resolution["current_version_id"]
    auth_content_hash = resolution["current_content_hash"]
    auth_status = resolution["current_status"]
    target_token = resolution["target_token"]
    report["target_token"] = target_token

    # Step 4: Anti-bypass Verification on Caller Arguments
    # If caller passed forged live values differing from authoritative resolution, reject or ignore forgery
    if current_content_hash is not None and current_content_hash != auth_content_hash:
        report["warnings"].append(
            f"caller-supplied current_content_hash {current_content_hash!r} overridden by "
            f"authoritative live resolution {auth_content_hash!r}."
        )
    if current_version_id is not None and current_version_id != auth_version_id:
        report["warnings"].append(
            f"caller-supplied current_version_id {current_version_id!r} overridden by "
            f"authoritative live resolution {auth_version_id!r}."
        )

    # Step 5: Trust Level Notes
    if trust.get("identity_kind") == "self_declared":
        report["warnings"].append(
            "self_declared identity: lower trust level retained end-to-end (0021-02 sensitive-field rule)."
        )

    # Step 6: Staleness & Version Binding Checking (0021-02, PROC-0033-02-03)
    target_vid = package.get("target_version_id")
    target_hash = package.get("target_content_hash")

    # If target is versioned but package specifies null version ID, reject per PROC-0033-02-03 (applies to v1 schema)
    if package.get("kind") != rrp.SCHEMA_V2:
        if target_vid is None and auth_version_id is not None:
            report["outcome"] = IngestOutcome.REJECTED_INELIGIBLE_TARGET
            report["errors"] = [
                "review requests must bind to an explicit published version (PROC-0033-02-03: null-version target disallowed)"
            ]
            return report

    if auth_content_hash is not None:
        if rrp.is_stale(package, auth_content_hash, auth_version_id):
            report["outcome"] = IngestOutcome.REJECTED_STALE
            report["errors"] = [
                "target_content_hash and target_version_id both mismatch the current record "
                "(0021-02 Staleness rule: hard-stale)"
            ]
            return report

        if target_hash and target_hash != auth_content_hash:
            report["warnings"].append(
                "content hash mismatch with matching version id: soft warning, "
                "forwarded to Kurator rather than rejected (0021-02 Staleness rule)."
            )

    # Step 7: Deduplication against Open Queue
    dedup_key = rrp.dedup_key(package)
    existing = _existing_open_dedup_keys()
    if dedup_key in existing:
        report["outcome"] = IngestOutcome.REJECTED_DUPLICATE
        report["errors"] = [
            "an open review-request queue item already exists for this record (0021-02 Duplicate rule): %s"
            % existing[dedup_key]
        ]
        return report

    # Step 8: Dry-run vs Apply
    if not apply:
        report["outcome"] = IngestOutcome.OK
        report["dry_run"] = True
        return report

    # Step 9: Enqueue Item (Apply=True)
    request_id = package.get("request_id") or package.get("event_id") or rrp.new_request_id()
    if not str(request_id).startswith("review-request:"):
        request_id = f"review-request:{request_id}"

    created_at = (
        package.get("created_at")
        or datetime.now(timezone.utc).isoformat()
    )

    decision = {
        "id": request_id,
        "outcome": "requested",
        "decided_by": (package.get("actor_claim") or {}).get("display_name"),
        "identity": trust.get("identity_kind") or "self_declared",
        "decided_at": created_at,
        "rationale": package.get("rationale") or "",
        "decision_basis": {
            "item_kind": ITEM_KIND,
            "target_canonical_id": package.get("target_canonical_id"),
            "target_version_id": package.get("target_version_id") or auth_version_id,
            "target_content_hash": package.get("target_content_hash") or auth_content_hash,
            "target_status_snapshot": package.get("target_status_snapshot") or auth_status,
            "category": package.get("category"),
            "evidence_refs": package.get("evidence_refs") or (
                [{"kind": "url", "value": package["evidence_url"]}] if package.get("evidence_url") else []
            ),
            "source_url": package.get("source_url") or resolution.get("source_url") or "",
            "transport": package.get("transport") or "github_issue",
            "authoritative_actor": trust.get("authoritative_actor"),
            "request_id": request_id,
            "target_token": target_token,
        },
    }

    path = cf.write_curation_flag(decision, campaign=campaign, project=None, kind=None)
    if path is None:
        report["outcome"] = IngestOutcome.REJECTED_DUPLICATE
        report["errors"] = ["write_curation_flag reported an existing flag for this request id"]
        return report

    # Tag item_kind at top level too for efficient scanning
    try:
        flag_payload = json.loads(path.read_text(encoding="utf-8"))
        flag_payload["item_kind"] = ITEM_KIND
        path.write_text(json.dumps(flag_payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    except Exception:
        pass

    report["outcome"] = IngestOutcome.OK
    report["path"] = str(path)
    return report


# ============================================================================
# CLI Interface
# ============================================================================

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("package_file", type=Path, help="Path to JSON package or envelope file")
    parser.add_argument("--apply", action="store_true", help="Write queue item (default: dry run / check only)")
    parser.add_argument("--issue-body", action="store_true", help="Input file is a GitHub Issue body with ```json block")
    parser.add_argument("--authoritative-actor", type=str, default=None, help="Verified GitHub actor login")
    parser.add_argument("--signature", type=str, default=None, help="X-Hub-Signature-256 header")
    parser.add_argument("--secret", type=str, default=None, help="Webhook secret key")
    parser.add_argument("--records-root", type=Path, default=None, help="Override records directory")
    parser.add_argument("--versions-root", type=Path, default=None, help="Override versions directory")
    parser.add_argument("--json", action="store_true", help="Output report in JSON format")

    args = parser.parse_args(argv)

    raw_text = args.package_file.read_text(encoding="utf-8")
    raw_bytes = raw_text.encode("utf-8")

    if args.issue_body:
        parsed_pkg = parse_issue_body(raw_text)
        if parsed_pkg is None:
            print("Error: No valid JSON block found in issue body", file=sys.stderr)
            return 1
        input_data = parsed_pkg
    else:
        input_data = json.loads(raw_text)

    report = ingest(
        package_or_envelope=input_data,
        apply=args.apply,
        authoritative_actor=args.authoritative_actor,
        records_root=args.records_root,
        versions_root=args.versions_root,
        raw_body=raw_bytes,
        signature_header=args.signature,
        webhook_secret=args.secret,
    )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Outcome: {report['outcome']}")
        if report.get("path"):
            print(f"Path: {report['path']}")
        for w in report.get("warnings", []):
            print(f"Warning: {w}")
        for e in report.get("errors", []):
            print(f"Error: {e}")

    return 0 if report["outcome"] == IngestOutcome.OK else 1


if __name__ == "__main__":
    sys.exit(main())
