#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""feedback_recipe_contract.py -- Consumer contract and trusted ingestion for feedback handoff.

Part of Feature 0045 (S-Core/AUTOSAR Feedback Loop).
Implements the autodocs consumer side of:
  - REQ-0045-04: Priority-gated Project Lead offer & award verification before trusted ingestion.
  - REQ-0045-05: Central Project Lead decision & runner assignment binding.
  - REQ-0045-06: Feedback/proposal cycle creating trusted committed queue item without mutating canonical record bytes.
  - REQ-0045-08: Typed deterministic recipes with role and effect boundaries.
  - REQ-0045-12: Exact idempotence keys, replay, conflict, retry ancestry, and restart reconstruction.
  - REQ-0045-16: Fail-closed authoritative selector & documentation compatibility check.

Consumes the immutable handoff schema `feedback-recipe-contract@v1` produced by
agent-inbox `FeedbackIngestionRecipeProducer` and commits exactly one conformant queue
item into `spec/curation-queue/open/`.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canonical_id as cid_util  # noqa: E402
import curation_flags as cf  # noqa: E402
import curation_item as ci  # noqa: E402
import review_request_ingest as rri  # noqa: E402
import review_request_package as rrp  # noqa: E402
import version_id as vid_util  # noqa: E402
import version_store as vstore  # noqa: E402

# Schema Constants
FEEDBACK_RECIPE_CONTRACT_SCHEMA = "feedback-recipe-contract@v1"
FEEDBACK_INGESTION_RESULT_SCHEMA = "feedback-ingestion-result@v1"
FEEDBACK_CONSUMER_RESULT_SCHEMA = "feedback-recipe-consumer-result@v1"
CONTRACT_VERSION = "v1.0.0"
RECIPE_NAME = "feedback_ingestion"
ITEM_KIND = "review-request"

# Root Paths
AUTODOCS_ROOT = Path(__file__).resolve().parents[2]
RECORDS_ROOT = Path(__file__).resolve().parents[1] / "spec" / "records"
VERSIONS_ROOT = Path(__file__).resolve().parents[1] / "spec" / "versions"

# Allowed Repositories for Trusted GitHub Intake
DEFAULT_ALLOWED_REPOSITORIES = (
    "2b-rs/autodocs",
    "AUTOSAR/autodocs",
    "AUTOSAR/standards",
    "eclipse-score/score",
    "2b-rs/agent-inbox",
    "example/repo",
)

COMMIT_HASH_RE = re.compile(r"^[0-9a-f]{7,40}$", re.IGNORECASE)
DIGEST_SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
IDEMPOTENCE_KEY_RE = re.compile(r"^feedback:[^:]+:[^:]+:[^:]+$")


class FeedbackConsumerOutcome:
    OK = "ok"
    REJECTED_INVALID_SCHEMA = "rejected_invalid_schema"
    REJECTED_UNAWARDED = "rejected_unawarded_execution"
    REJECTED_RECIPE_MISMATCH = "rejected_recipe_mismatch"
    REJECTED_SELECTOR_MISMATCH = "rejected_selector_mismatch"
    REJECTED_DOCUMENTATION_CONTRADICTION = "rejected_documentation_contradiction"
    REJECTED_UNTRUSTED_TRANSPORT = "rejected_untrusted_transport"
    REJECTED_UNKNOWN_TARGET = "rejected_unknown_target"
    REJECTED_INELIGIBLE_TARGET = "rejected_ineligible_target"
    REJECTED_STALE = "rejected_stale"
    REJECTED_DUPLICATE = "rejected_duplicate"
    REJECTED_CONFLICT = "rejected_conflict"
    REJECTED_TAMPERING = "rejected_tampering"
    RETRYABLE_FAILURE = "retryable_failure"
    TERMINAL_FAILURE = "terminal_failure"


def canonical_json_bytes(obj: Any) -> bytes:
    """Deterministic UTF-8 canonical JSON bytes representation."""
    return (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def compute_sha256(data: Any) -> str:
    """Compute sha256 hex digest of data."""
    if isinstance(data, (dict, list)):
        payload_bytes = canonical_json_bytes(data)
    elif isinstance(data, str):
        payload_bytes = data.encode("utf-8")
    elif isinstance(data, bytes):
        payload_bytes = data
    else:
        payload_bytes = str(data).encode("utf-8")
    return hashlib.sha256(payload_bytes).hexdigest()


# ============================================================================
# Authoritative Selector and Baseline Compatibility Check (REQ-0045-16)
# ============================================================================

def check_authoritative_selector(autodocs_root: Optional[Path] = None) -> Tuple[bool, str]:
    """Verify that the authoritative runner selector complies with the approved baseline.

    Fails closed if `agent-workflow.json` or its runner_protocol contradicts `runner-request@v1`.
    """
    root = autodocs_root if autodocs_root is not None else AUTODOCS_ROOT
    selector_file = root / "agent-workflow.json"
    if not selector_file.exists():
        return False, f"authoritative selector file missing: {selector_file}"

    try:
        data = json.loads(selector_file.read_text(encoding="utf-8"))
    except Exception as e:
        return False, f"error parsing authoritative selector: {e}"

    if data.get("runner_protocol") != "runner-request@v1":
        return False, f"unsupported runner_protocol in selector: {data.get('runner_protocol')!r}; expected 'runner-request@v1'"

    if data.get("authority_epoch") != "legacy-writable":
        return False, f"unsupported authority_epoch in selector: {data.get('authority_epoch')!r}"

    return True, "selector compatible with runner-request@v1"


# ============================================================================
# Consumer In-Memory & Durable Receipt Store
# ============================================================================

class FeedbackConsumerReceiptStore:
    """Durable receipt and idempotence store for the autodocs feedback consumer."""

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}

    def get(self, idempotence_key: str) -> Optional[Dict[str, Any]]:
        return self._store.get(idempotence_key)

    def record(self, idempotence_key: str, result_record: Dict[str, Any]) -> None:
        self._store[idempotence_key] = copy.deepcopy(result_record)

    def reset(self) -> None:
        self._store.clear()


_GLOBAL_CONSUMER_RECEIPT_STORE = FeedbackConsumerReceiptStore()


def get_global_receipt_store() -> FeedbackConsumerReceiptStore:
    return _GLOBAL_CONSUMER_RECEIPT_STORE


def reset_receipt_store() -> None:
    _GLOBAL_CONSUMER_RECEIPT_STORE.reset()


# ============================================================================
# Schema and Handoff Validation
# ============================================================================

def validate_handoff_contract(handoff: Dict[str, Any]) -> List[str]:
    """Validate handoff payload against feedback-recipe-contract@v1 requirements."""
    errors: List[str] = []
    if not isinstance(handoff, dict):
        return ["handoff must be a json object"]

    if handoff.get("schema") != FEEDBACK_RECIPE_CONTRACT_SCHEMA:
        errors.append(f"invalid handoff schema: {handoff.get('schema')!r}; expected {FEEDBACK_RECIPE_CONTRACT_SCHEMA!r}")

    if handoff.get("contract_version") != CONTRACT_VERSION:
        errors.append(f"invalid contract_version: {handoff.get('contract_version')!r}; expected {CONTRACT_VERSION!r}")

    if handoff.get("recipe_name") != RECIPE_NAME:
        errors.append(f"invalid recipe_name: {handoff.get('recipe_name')!r}; expected {RECIPE_NAME!r}")

    for req in (
        "producer_repository",
        "producer_commit",
        "consumer_baseline",
        "scheduling_decision_id",
        "assignment_id",
        "idempotence_key",
        "normalized_input_digest",
        "status",
        "trusted_envelope",
        "durable_receipt",
        "next_event",
        "created_at",
    ):
        if req not in handoff:
            errors.append(f"missing required field: {req!r}")
        elif isinstance(handoff[req], str) and not handoff[req].strip():
            errors.append(f"field {req!r} cannot be empty")

    producer_commit = handoff.get("producer_commit")
    if producer_commit and not COMMIT_HASH_RE.match(str(producer_commit)):
        errors.append(f"invalid producer_commit pattern: {producer_commit!r}")

    consumer_baseline = handoff.get("consumer_baseline")
    if consumer_baseline and not COMMIT_HASH_RE.match(str(consumer_baseline)):
        errors.append(f"invalid consumer_baseline pattern: {consumer_baseline!r}")

    idemp_key = handoff.get("idempotence_key")
    if idemp_key and not IDEMPOTENCE_KEY_RE.match(str(idemp_key)):
        errors.append(f"invalid idempotence_key format: {idemp_key!r}; expected feedback:<repo>:<source_id>:<record_id>")

    input_digest = handoff.get("normalized_input_digest")
    if input_digest and not DIGEST_SHA256_RE.match(str(input_digest)):
        errors.append(f"invalid normalized_input_digest format: {input_digest!r}")

    status = handoff.get("status")
    if status not in ("succeeded", "conflict", "retryable_failure", "terminal_failure"):
        errors.append(f"invalid status: {status!r}")

    # Validate trusted envelope structure
    envelope = handoff.get("trusted_envelope")
    if isinstance(envelope, dict):
        for req_env in (
            "schema",
            "event_id",
            "event_kind",
            "repository",
            "source_id",
            "record_id",
            "record_version",
            "sender",
            "created_at",
            "payload",
        ):
            if req_env not in envelope:
                errors.append(f"trusted_envelope missing required field: {req_env!r}")

        if envelope.get("event_kind") != "curation_feedback":
            errors.append(f"trusted_envelope event_kind must be 'curation_feedback'; got {envelope.get('event_kind')!r}")
    else:
        errors.append("trusted_envelope must be a dictionary")

    # Validate durable receipt structure
    receipt = handoff.get("durable_receipt")
    if isinstance(receipt, dict):
        for req_rcpt in ("receipt_id", "receipt_digest", "recorded_at"):
            if req_rcpt not in receipt:
                errors.append(f"durable_receipt missing required field: {req_rcpt!r}")
    else:
        errors.append("durable_receipt must be a dictionary")

    return errors


# ============================================================================
# Main Consumer Function
# ============================================================================

def consume_feedback_recipe_handoff(
    handoff: Dict[str, Any],
    apply: bool = False,
    records_root: Optional[Path] = None,
    versions_root: Optional[Path] = None,
    autodocs_root: Optional[Path] = None,
    allowed_repositories: Optional[Tuple[str, ...]] = None,
    receipt_store: Optional[FeedbackConsumerReceiptStore] = None,
) -> Dict[str, Any]:
    """Validate and consume a `feedback-recipe-contract@v1` handoff.

    Guarantees:
      - Validates Project Lead award & runner assignment binding before ingestion.
      - Resolves authoritative live target without accepting caller overrides.
      - Preserves canonical record bytes strictly untouched (target_record_mutated=False).
      - Replay of identical key + input digest returns recorded result.
      - Replay of identical key + conflicting digest returns typed conflict (effect-free).
      - Stale, ineligible, unknown, or malformed inputs are typed and effect-free.
      - Exactly ONE committed queue item created when apply=True and valid.
    """
    store = receipt_store if receipt_store is not None else _GLOBAL_CONSUMER_RECEIPT_STORE
    allowed_repos = allowed_repositories if allowed_repositories is not None else DEFAULT_ALLOWED_REPOSITORIES
    rec_root = records_root if records_root is not None else RECORDS_ROOT
    ver_root = versions_root if versions_root is not None else VERSIONS_ROOT
    doc_root = autodocs_root if autodocs_root is not None else AUTODOCS_ROOT

    report: Dict[str, Any] = {
        "schema": FEEDBACK_CONSUMER_RESULT_SCHEMA,
        "status": None,
        "queue_item_id": None,
        "queue_item_path": None,
        "next_event": None,
        "durable_receipt": None,
        "deduplication_disposition": None,
        "target_record_mutated": False,
        "target_canonical_id": None,
        "target_token": None,
        "errors": [],
        "warnings": [],
        "dry_run": not apply,
    }

    # 1. Authoritative Runner Selector & Documentation Compatibility Check (REQ-0045-16)
    sel_ok, sel_msg = check_authoritative_selector(autodocs_root=doc_root)
    if not sel_ok:
        report["status"] = FeedbackConsumerOutcome.REJECTED_SELECTOR_MISMATCH
        report["errors"].append(sel_msg)
        return report

    # 2. Strict Handoff Contract Validation
    schema_errors = validate_handoff_contract(handoff)
    if schema_errors:
        report["status"] = FeedbackConsumerOutcome.REJECTED_INVALID_SCHEMA
        report["errors"].extend(schema_errors)
        return report

    # 3. Verify Priority-Gated Award & Assignment Binding (REQ-0045-04, REQ-0045-05)
    decision_id = handoff.get("scheduling_decision_id", "").strip()
    assignment_id = handoff.get("assignment_id", "").strip()
    if not decision_id or not assignment_id:
        report["status"] = FeedbackConsumerOutcome.REJECTED_UNAWARDED
        report["errors"].append("unawarded execution: missing scheduling_decision_id or assignment_id")
        return report

    # 4. Handle Incoming Handoff Status from Producer
    producer_status = handoff.get("status")
    idempotence_key = handoff["idempotence_key"]
    input_digest = handoff["normalized_input_digest"]

    if producer_status == "conflict":
        report["status"] = FeedbackConsumerOutcome.REJECTED_CONFLICT
        report["errors"].append("producer recorded idempotence conflict")
        report["next_event"] = handoff.get("next_event") or "terminal:idempotence_conflict"
        return report

    if producer_status == "retryable_failure":
        report["status"] = FeedbackConsumerOutcome.RETRYABLE_FAILURE
        report["errors"].append("producer recorded retryable failure")
        report["next_event"] = handoff.get("next_event") or "retry_from_last_proven_boundary"
        return report

    if producer_status == "terminal_failure":
        report["status"] = FeedbackConsumerOutcome.TERMINAL_FAILURE
        report["errors"].append("producer recorded terminal failure")
        report["next_event"] = handoff.get("next_event") or "terminal:failure"
        return report

    # 5. Envelope & Transport Trust Verification (Feature 0033 / 0033-06)
    envelope = handoff["trusted_envelope"]
    repo = envelope.get("repository")
    if repo not in allowed_repos:
        report["status"] = FeedbackConsumerOutcome.REJECTED_UNTRUSTED_TRANSPORT
        report["errors"].append(f"envelope repository {repo!r} is not in trusted allowlist: {allowed_repos}")
        return report

    # Verify digest of payload against normalized_input_digest
    actual_payload_digest = compute_sha256(envelope.get("payload", {}))
    if actual_payload_digest != input_digest:
        report["status"] = FeedbackConsumerOutcome.REJECTED_TAMPERING
        report["errors"].append(f"normalized_input_digest mismatch: expected {actual_payload_digest}, got {input_digest}")
        return report

    # Verify idempotence key matches envelope fields
    expected_idemp_key = f"feedback:{envelope.get('repository')}:{envelope.get('source_id')}:{envelope.get('record_id')}"
    if idempotence_key != expected_idemp_key:
        report["status"] = FeedbackConsumerOutcome.REJECTED_TAMPERING
        report["errors"].append(f"idempotence_key mismatch: expected {expected_idemp_key}, got {idempotence_key}")
        return report

    target_record_id = envelope.get("record_id")
    target_canonical_id = envelope.get("record_id")
    submitted_record_version = envelope.get("record_version")
    report["target_canonical_id"] = target_canonical_id

    # 6. Replay & Idempotence Check against Receipt Store (REQ-0045-12)
    stored = store.get(idempotence_key)
    if stored is not None:
        if stored.get("normalized_input_digest") == input_digest:
            # Idempotent replay: return recorded result
            replay_report = copy.deepcopy(stored.get("result", {}))
            replay_report["deduplication_disposition"] = "replay"
            replay_report["warnings"].append("idempotent replay of previously committed feedback handoff")
            return replay_report
        else:
            # Conflicting payload under same idempotence key -> conflict, no effect
            report["status"] = FeedbackConsumerOutcome.REJECTED_CONFLICT
            report["errors"].append(
                f"idempotence key {idempotence_key} already recorded with different input digest {stored.get('normalized_input_digest')}"
            )
            report["next_event"] = "terminal:idempotence_conflict"
            return report

    # 7. Authoritative Live-Target Resolution (Feature 0033 / 0033-06)
    target_res = rri.resolve_live_target(
        canonical_id_str=target_canonical_id,
        records_root=rec_root,
        versions_root=ver_root,
    )

    if not target_res["found"]:
        report["status"] = target_res.get("error") or FeedbackConsumerOutcome.REJECTED_UNKNOWN_TARGET
        report["errors"].append(target_res.get("reason") or f"target record not found: {target_canonical_id}")
        return report

    if not target_res["eligible"]:
        report["status"] = target_res.get("error") or FeedbackConsumerOutcome.REJECTED_INELIGIBLE_TARGET
        report["errors"].append(target_res.get("reason") or f"ineligible target record status: {target_canonical_id}")
        return report

    auth_version_id = target_res["current_version_id"]
    auth_content_hash = target_res["current_content_hash"]
    target_token = target_res["target_token"]
    report["target_token"] = target_token

    # 8. Staleness Verification (REQ-0045-06, 0021-02 staleness rule)
    if submitted_record_version and auth_version_id:
        if submitted_record_version != auth_version_id:
            report["status"] = FeedbackConsumerOutcome.REJECTED_STALE
            report["errors"].append(
                f"submitted record_version {submitted_record_version!r} mismatches current live version {auth_version_id!r}"
            )
            return report

    # 9. Duplicate Check against Active Queue (0033-07 / 0021-02 Duplicate Rule)
    existing_active = rri._existing_active_dedup_keys()
    dedup_key = (target_canonical_id, auth_version_id)
    if dedup_key in existing_active:
        report["status"] = FeedbackConsumerOutcome.REJECTED_DUPLICATE
        report["errors"].append(
            f"an active queue item already exists for this record: {existing_active[dedup_key]}"
        )
        return report

    # Determine Queue Item ID and Continuation Next Event
    ingestion_res = handoff.get("ingestion_result") or {}
    queue_item_id = (
        ingestion_res.get("queue_item_id")
        or f"feedback-{envelope.get('record_id')}-{envelope.get('event_id')[:8]}"
    )
    if not queue_item_id.startswith("feedback:") and not queue_item_id.startswith("queue-item-"):
        queue_item_id = f"feedback:{queue_item_id}"

    next_event = (
        handoff.get("next_event")
        or f"proposal_scheduling_continuation:{queue_item_id}"
    )

    recorded_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    consumer_receipt_digest = compute_sha256({
        "assignment_id": assignment_id,
        "scheduling_decision_id": decision_id,
        "idempotence_key": idempotence_key,
        "input_digest": input_digest,
        "queue_item_id": queue_item_id,
        "recorded_at": recorded_at,
    })
    durable_receipt = {
        "receipt_id": f"rcpt-consumer-{assignment_id}",
        "receipt_digest": consumer_receipt_digest,
        "recorded_at": recorded_at,
    }

    report["queue_item_id"] = queue_item_id
    report["next_event"] = next_event
    report["durable_receipt"] = durable_receipt
    report["deduplication_disposition"] = "new"
    report["status"] = FeedbackConsumerOutcome.OK

    # 10. Dry-Run Check (if apply=False, do not write queue item)
    if not apply:
        return report

    # 11. Atomic Committed Queue Item Creation (apply=True)
    created_at = handoff.get("created_at") or recorded_at
    payload_text = (
        envelope.get("payload", {}).get("text")
        or envelope.get("payload", {}).get("suggested_change")
        or "Feedback received via trusted ingestion recipe"
    )

    item_payload = {
        "schema": cf.SCHEMA,
        "id": queue_item_id,
        "canonical_id": target_canonical_id,
        "item_kind": ITEM_KIND,
        "origin": "browser",
        "status": "open",
        "created": created_at,
        "campaign": "score-curation-feedback",
        "outcome": "requested",
        "decided_by": None,
        "identity": envelope.get("sender") or "github_authenticated",
        "decided_at": None,
        "rationale": payload_text,
        "decision_basis": {
            "schema": "feedback-recipe-decision-basis@v1",
            "handoff_schema": FEEDBACK_RECIPE_CONTRACT_SCHEMA,
            "producer_repository": handoff.get("producer_repository"),
            "producer_commit": handoff.get("producer_commit"),
            "scheduling_decision_id": decision_id,
            "assignment_id": assignment_id,
            "idempotence_key": idempotence_key,
            "normalized_input_digest": input_digest,
            "trusted_envelope": envelope,
            "durable_receipt": handoff.get("durable_receipt"),
            "retry_ancestry": handoff.get("retry_ancestry", []),
            "target_token": target_token,
            "source_url": target_res.get("source_url") or "",
        },
    }

    path = cf.write_review_request_flag(item_payload)
    if path is None:
        report["status"] = FeedbackConsumerOutcome.REJECTED_DUPLICATE
        report["errors"].append("write_review_request_flag reported an existing queue flag file")
        return report

    report["queue_item_path"] = str(path)
    # Guarantee that canonical record bytes were NOT mutated
    report["target_record_mutated"] = False

    # Store in consumer receipt store for idempotence tracking
    store.record(
        idempotence_key=idempotence_key,
        result_record={
            "idempotence_key": idempotence_key,
            "normalized_input_digest": input_digest,
            "result": report,
            "recorded_at": recorded_at,
        },
    )

    return report


# ============================================================================
# CLI Interface
# ============================================================================

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("handoff_file", type=Path, help="Path to feedback-recipe-contract@v1 JSON file")
    parser.add_argument("--apply", action="store_true", help="Atomically commit queue item (default: dry run check)")
    parser.add_argument("--json", action="store_true", help="Print report as JSON")
    args = parser.parse_args(argv)

    if not args.handoff_file.exists():
        sys.stderr.write(f"Error: file not found: {args.handoff_file}\n")
        return 1

    try:
        handoff_data = json.loads(args.handoff_file.read_text(encoding="utf-8"))
    except Exception as e:
        sys.stderr.write(f"Error parsing JSON from {args.handoff_file}: {e}\n")
        return 1

    report = consume_feedback_recipe_handoff(handoff_data, apply=args.apply)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Status:            {report['status']}")
        print(f"Target Record:     {report['target_canonical_id']}")
        print(f"Queue Item ID:     {report['queue_item_id']}")
        print(f"Queue Item Path:   {report['queue_item_path']}")
        print(f"Next Event:        {report['next_event']}")
        print(f"Record Mutated:    {report['target_record_mutated']}")
        for err in report["errors"]:
            print(f"ERROR:             {err}")
        for warn in report["warnings"]:
            print(f"WARNING:           {warn}")

    return 0 if report["status"] == FeedbackConsumerOutcome.OK else 1


if __name__ == "__main__":
    sys.exit(main())
