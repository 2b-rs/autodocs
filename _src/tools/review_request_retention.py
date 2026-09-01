#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""review_request_retention.py -- Privacy, retention, redaction, expiry, and disposal policy (0033-07.02).

Implements the approved privacy, retention, redaction, expiry, and disposal policy across:
  - Active/done queues (open, claimed, done)
  - Receipts and transport envelopes
  - Historical records, reports, logs, and exports
  - Public status projections
  - External GitHub deletion limitations and explicit consent disclaimer handling

Governed by authority decisions PROC-0033-02-08, PROC-0033-02-12, PROC-0033-02-13,
PROC-0033-02-14, PROC-0033-02-15, and PROC-0033-02-16 (0033-04.01 / DEC-0033-002):
  - 10 years for immutable decision audit trail / proof
  - 3 years maximum for raw review-request payloads and personal data
  - 120 days for unclaimed/unacted review-request queue items
  - Legal hold support (exempts flagged items from expiry/disposal)
  - Public projection redaction (strips PII, credentials, private metadata)
  - Safe disposal and atomic conversion of expired raw items into redacted proof records
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import curation_flags as cf  # noqa: E402
import review_request_package as rrp  # noqa: E402

# Retention Periods (Days) per PROC-0033-02-13
RETENTION_DAYS_DECISION_PROOF = 3650  # 10 years
RETENTION_DAYS_RAW_PAYLOAD = 1095      # 3 years
RETENTION_DAYS_UNCLAIMED_EXPIRY = 120  # 120 days

DEFAULT_QUEUE_ROOT = Path(__file__).resolve().parents[1] / "spec" / "curation-queue"

# Consent disclaimer text (PROC-0033-02-08, PROC-0033-02-14)
CONSENT_DISCLAIMER_EN = (
    "By submitting this review request, you consent to the processing of the "
    "submitted details (including category, rationale, and cited evidence) "
    "for documentation verification and quality assurance purposes."
)

CONSENT_DISCLAIMER_DE = (
    "Mit dem Absenden dieser Überprüfungsanfrage erklären Sie sich mit der "
    "Verarbeitung der angegebenen Daten (einschließlich Kategorie, Begründung und "
    "Belegen) zum Zweck der Dokumentationsprüfung und Qualitätssicherung einverstanden."
)

# External limitation notice regarding third-party controller deletion boundaries (PROC-0033-02-14)
EXTERNAL_LIMITATIONS_NOTICE_EN = (
    "Notice regarding external platforms: Requests submitted via public GitHub Issues, "
    "comments, or external mirrors cannot be irrevocably deleted by this repository's "
    "controller once published externally due to third-party hosting limitations."
)

EXTERNAL_LIMITATIONS_NOTICE_DE = (
    "Hinweis zu externen Plattformen: Meldungen, die über öffentliche GitHub-Issues, "
    "Kommentare oder externe Spiegel eingereicht werden, können nach Veröffentlichung "
    "aufgrund von Plattformgrenzen nicht durch den Betreiber dieses Repositories "
    "vollständig oder rückwirkend gelöscht werden."
)


def get_consent_disclaimer(lang: str = "en") -> str:
    """Return the approved consent disclaimer text."""
    if lang.lower().startswith("de"):
        return CONSENT_DISCLAIMER_DE
    return CONSENT_DISCLAIMER_EN


def get_external_limitations_notice(lang: str = "en") -> str:
    """Return the approved external platforms limitation notice."""
    if lang.lower().startswith("de"):
        return EXTERNAL_LIMITATIONS_NOTICE_DE
    return EXTERNAL_LIMITATIONS_NOTICE_EN


def get_retention_policy_limits() -> dict[str, Any]:
    """Return structured retention policy parameters."""
    return {
        "decision_proof_retention_days": RETENTION_DAYS_DECISION_PROOF,
        "raw_payload_retention_days": RETENTION_DAYS_RAW_PAYLOAD,
        "unclaimed_expiry_days": RETENTION_DAYS_UNCLAIMED_EXPIRY,
        "governing_decisions": [
            "PROC-0033-02-08",
            "PROC-0033-02-12",
            "PROC-0033-02-13",
            "PROC-0033-02-14",
            "PROC-0033-02-15",
            "PROC-0033-02-16",
        ],
    }


def parse_timestamp(ts_str: Any) -> datetime | None:
    """Parse ISO 8601 UTC timestamp string safely."""
    if not isinstance(ts_str, str) or not ts_str.strip():
        return None
    return rrp.parse_utc_timestamp(ts_str)


def is_timestamp_expired(
    ts_str: str | None,
    period_days: int,
    as_of: datetime | None = None,
) -> bool:
    """Check whether a timestamp is older than period_days relative to as_of (default: current UTC)."""
    if not ts_str:
        return False
    dt = parse_timestamp(ts_str)
    if dt is None:
        return False
    now = as_of if as_of is not None else datetime.now(timezone.utc)
    cutoff = now - timedelta(days=period_days)
    return dt < cutoff


def redact_for_public_projection(item: dict) -> dict:
    """Create a privacy-safe public status projection of a review request (PROC-0033-02-12).

    Retains:
      - item id, canonical_id, item_kind, outcome, status, created, decided_at
      - category, target_version_id, target_content_hash
      - target_token (for verification)
      - warnings if public

    Redacts / Strips:
      - Personal display names of self-declared actors
      - Internal email addresses, tokens, credentials, IP addresses
      - Raw unbounded text or private operator instructions
    """
    if not isinstance(item, dict):
        return {}

    proj: dict[str, Any] = {
        "schema": "review-request-public-projection@v1",
        "id": item.get("id"),
        "canonical_id": item.get("canonical_id"),
        "item_kind": item.get("item_kind") or "review-request",
        "status": item.get("status") or "open",
        "outcome": item.get("outcome") or "requested",
        "created": item.get("created"),
        "decided_at": item.get("decided_at"),
    }

    basis = item.get("decision_basis") or {}
    proj["category"] = basis.get("category")
    proj["target_canonical_id"] = basis.get("target_canonical_id") or item.get("canonical_id")
    proj["target_version_id"] = basis.get("target_version_id")
    proj["target_content_hash"] = basis.get("target_content_hash")
    proj["target_status_snapshot"] = basis.get("target_status_snapshot")
    proj["source_url"] = basis.get("source_url")

    # Authoritative actor is included if public (e.g. GitHub login), else anonymous / self-declared
    identity_kind = item.get("identity") or basis.get("identity_kind") or "self_declared"
    if identity_kind == "github_authenticated" and basis.get("authoritative_actor"):
        proj["authoritative_actor"] = basis.get("authoritative_actor")
        proj["identity_trust"] = "github_authenticated"
    else:
        proj["authoritative_actor"] = None
        proj["identity_trust"] = "self_declared"

    if basis.get("target_token"):
        proj["target_token_sha256"] = (basis["target_token"].get("token_sha256")
                                       if isinstance(basis["target_token"], dict) else None)

    # Omit raw rationale and raw personal data from public projection
    return proj


def redact_for_long_term_proof(item: dict) -> dict:
    """Convert an expired raw review request (>3 years old) into a 10-year immutable decision proof record.

    Purges:
      - Raw text rationale
      - Raw evidence attachments and URLs
      - Actor personal claims and display names
      - Temporary notes and transient logs

    Retains:
      - id, canonical_id, item_kind, outcome, status, created, decided_at, decided_by
      - target_version_id, target_content_hash, category
      - retention status tag ('redacted_long_term_proof')
    """
    if not isinstance(item, dict):
        return {}

    basis = item.get("decision_basis") or {}
    proof: dict[str, Any] = {
        "schema": "curation-decision-proof@v1",
        "id": item.get("id"),
        "canonical_id": item.get("canonical_id"),
        "item_kind": item.get("item_kind") or "review-request",
        "outcome": item.get("outcome"),
        "status": item.get("status") or "completed",
        "created": item.get("created"),
        "decided_at": item.get("decided_at"),
        "decided_by": item.get("decided_by"),
        "completed_at": item.get("completed_at"),
        "retention_status": "redacted_long_term_proof",
        "retention_redacted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "decision_summary": {
            "category": basis.get("category"),
            "target_canonical_id": basis.get("target_canonical_id") or item.get("canonical_id"),
            "target_version_id": basis.get("target_version_id"),
            "target_content_hash": basis.get("target_content_hash"),
            "target_status_snapshot": basis.get("target_status_snapshot"),
            "outcome_class": item.get("outcome_class") or "no_action",
            "target_token_sha256": (basis["target_token"].get("token_sha256")
                                    if isinstance(basis.get("target_token"), dict) else None),
        },
    }
    return proof


def evaluate_item_retention(
    item: dict,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    """Evaluate retention and expiry state of a queue item or envelope.

    Returns:
      {
        "disposition": "retain_active" | "expire_unclaimed" | "redact_raw_payload" | "dispose_proof" | "held",
        "reason": str,
        "is_held": bool,
        "age_days": float,
      }
    """
    now = as_of if as_of is not None else datetime.now(timezone.utc)

    # Check legal hold
    if item.get("legal_hold") is True:
        return {
            "disposition": "held",
            "reason": "item has active legal_hold flag; exempt from expiry and disposal",
            "is_held": True,
            "age_days": 0.0,
        }

    created_dt = parse_timestamp(item.get("created") or item.get("created_at") or item.get("received_at"))
    if not created_dt:
        return {
            "disposition": "retain_active",
            "reason": "missing or unparseable timestamp; retained safely",
            "is_held": False,
            "age_days": 0.0,
        }

    age = (now - created_dt).total_seconds() / 86400.0
    status = item.get("status") or "open"
    is_completed = status in ("done", "completed", "resolved") or "completed_at" in item

    # 1. 10-year proof limit check
    if age > RETENTION_DAYS_DECISION_PROOF:
        return {
            "disposition": "dispose_proof",
            "reason": f"item age ({age:.1f} days) exceeds 10-year proof retention limit ({RETENTION_DAYS_DECISION_PROOF} days)",
            "is_held": False,
            "age_days": age,
        }

    # 2. 3-year raw payload limit check (completed items)
    if is_completed and age > RETENTION_DAYS_RAW_PAYLOAD:
        if item.get("retention_status") == "redacted_long_term_proof":
            return {
                "disposition": "retain_active",
                "reason": "already redacted to long-term proof",
                "is_held": False,
                "age_days": age,
            }
        return {
            "disposition": "redact_raw_payload",
            "reason": f"completed item age ({age:.1f} days) exceeds 3-year raw payload limit ({RETENTION_DAYS_RAW_PAYLOAD} days)",
            "is_held": False,
            "age_days": age,
        }

    # 3. 120-day unclaimed expiry check (open items)
    if not is_completed and status == "open" and age > RETENTION_DAYS_UNCLAIMED_EXPIRY:
        return {
            "disposition": "expire_unclaimed",
            "reason": f"unclaimed open item age ({age:.1f} days) exceeds 120-day expiry limit ({RETENTION_DAYS_UNCLAIMED_EXPIRY} days)",
            "is_held": False,
            "age_days": age,
        }

    return {
        "disposition": "retain_active",
        "reason": f"item age ({age:.1f} days) within policy limits",
        "is_held": False,
        "age_days": age,
    }


def _atomic_write_json(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp-%s" % uuid.uuid4().hex[:8])
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def plan_queue_retention(
    queue_root: Path | None = None,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    """Scan queue directories (open, claimed, done) and generate a retention actions plan."""
    root = queue_root if queue_root is not None else DEFAULT_QUEUE_ROOT
    open_dir = root / "open"
    claimed_dir = root / "claimed"
    done_dir = root / "done"

    plan: dict[str, Any] = {
        "as_of": (as_of if as_of is not None else datetime.now(timezone.utc)).isoformat(),
        "total_scanned": 0,
        "retain_active": [],
        "expire_unclaimed": [],
        "redact_raw_payload": [],
        "dispose_proof": [],
        "held": [],
        "errors": [],
    }

    for dir_path in (open_dir, claimed_dir, done_dir):
        if not dir_path.exists():
            continue
        for file_path in sorted(dir_path.glob("*.json")):
            plan["total_scanned"] += 1
            try:
                content = json.loads(file_path.read_text(encoding="utf-8"))
            except Exception as e:
                plan["errors"].append({"path": str(file_path), "error": str(e)})
                continue

            eval_res = evaluate_item_retention(content, as_of=as_of)
            entry = {
                "path": str(file_path),
                "id": content.get("id"),
                "canonical_id": content.get("canonical_id"),
                "disposition": eval_res["disposition"],
                "reason": eval_res["reason"],
                "age_days": eval_res["age_days"],
                "is_held": eval_res["is_held"],
            }
            plan[eval_res["disposition"]].append(entry)

    return plan


def apply_queue_retention(
    queue_root: Path | None = None,
    as_of: datetime | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Apply retention plan to queue files safely and atomically."""
    plan = plan_queue_retention(queue_root=queue_root, as_of=as_of)
    summary: dict[str, Any] = {
        "dry_run": dry_run,
        "total_scanned": plan["total_scanned"],
        "unclaimed_expired_count": len(plan["expire_unclaimed"]),
        "redacted_count": len(plan["redact_raw_payload"]),
        "disposed_count": len(plan["dispose_proof"]),
        "held_count": len(plan["held"]),
        "actions_performed": [],
        "errors": plan["errors"],
    }

    if dry_run:
        return summary

    # 1. Process expire_unclaimed (mark as expired or move to done with outcome=unclaimed_expired)
    for entry in plan["expire_unclaimed"]:
        p = Path(entry["path"])
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
            payload["status"] = "expired"
            payload["outcome"] = "unclaimed_expired"
            payload["expired_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            payload["operator_note"] = "Expired automatically after 120 days unclaimed (PROC-0033-02-13)"
            target_done = p.parents[1] / "done" / p.name
            target_done.parent.mkdir(parents=True, exist_ok=True)
            _atomic_write_json(target_done, payload)
            if p.exists() and p != target_done:
                p.unlink()
            summary["actions_performed"].append(f"expired_unclaimed: {p.name} -> done/{p.name}")
        except Exception as e:
            summary["errors"].append({"path": str(p), "error": str(e)})

    # 2. Process redact_raw_payload (convert done items >3 years to redacted proof)
    for entry in plan["redact_raw_payload"]:
        p = Path(entry["path"])
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
            redacted_payload = redact_for_long_term_proof(payload)
            _atomic_write_json(p, redacted_payload)
            summary["actions_performed"].append(f"redacted_raw_payload: {p.name}")
        except Exception as e:
            summary["errors"].append({"path": str(p), "error": str(e)})

    # 3. Process dispose_proof (purge records >10 years old)
    for entry in plan["dispose_proof"]:
        p = Path(entry["path"])
        try:
            p.unlink()
            summary["actions_performed"].append(f"disposed_proof: {p.name}")
        except Exception as e:
            summary["errors"].append({"path": str(p), "error": str(e)})

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Subcommand: plan
    p_plan = sub.add_parser("plan", help="Scan queues and print retention actions plan")
    p_plan.add_argument("--root", type=Path, default=DEFAULT_QUEUE_ROOT, help="Queue root directory")
    p_plan.add_argument("--json", action="store_true", help="Output JSON")

    # Subcommand: gc
    p_gc = sub.add_parser("gc", help="Run garbage collection / retention enforcement")
    p_gc.add_argument("--root", type=Path, default=DEFAULT_QUEUE_ROOT, help="Queue root directory")
    p_gc.add_argument("--apply", action="store_true", help="Apply modifications (default is dry-run)")
    p_gc.add_argument("--json", action="store_true", help="Output JSON")

    # Subcommand: project
    p_proj = sub.add_parser("project", help="Generate public projection for an item file")
    p_proj.add_argument("file", type=Path, help="Path to item JSON file")
    p_proj.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args(argv)

    if args.command == "plan":
        plan = plan_queue_retention(queue_root=args.root)
        if args.json:
            print(json.dumps(plan, indent=2, ensure_ascii=False))
        else:
            print("Retention Plan Summary:")
            print(f"  Total Scanned:     {plan['total_scanned']}")
            print(f"  Retain Active:     {len(plan['retain_active'])}")
            print(f"  Expire Unclaimed:  {len(plan['expire_unclaimed'])}")
            print(f"  Redact Raw:        {len(plan['redact_raw_payload'])}")
            print(f"  Dispose Proof:     {len(plan['dispose_proof'])}")
            print(f"  Legal Hold:        {len(plan['held'])}")
        return 0

    if args.command == "gc":
        res = apply_queue_retention(queue_root=args.root, dry_run=not args.apply)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            mode = "APPLY" if args.apply else "DRY-RUN"
            print(f"Retention Enforcement ({mode}):")
            print(f"  Total Scanned:     {res['total_scanned']}")
            print(f"  Unclaimed Expired: {res['unclaimed_expired_count']}")
            print(f"  Redacted:          {res['redacted_count']}")
            print(f"  Disposed:          {res['disposed_count']}")
            print(f"  Held:              {res['held_count']}")
            if res["actions_performed"]:
                print("  Actions:")
                for a in res["actions_performed"]:
                    print(f"    - {a}")
        return 0

    if args.command == "project":
        if not args.file.exists():
            print(f"Error: file {args.file} does not exist", file=sys.stderr)
            return 1
        item = json.loads(args.file.read_text(encoding="utf-8"))
        proj = redact_for_public_projection(item)
        print(json.dumps(proj, indent=2, ensure_ascii=False))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
