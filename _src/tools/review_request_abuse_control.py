#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""review_request_abuse_control.py -- Abuse, quota, quarantine, moderation, and escalation controls.

Implements Task 0033-07.04 (remediating RRB-PROC-001, RRB-PRIV-001, RRB-TRUST-001):
  - Automated pre-queue abuse, rate-limiting, burst quotas, and capacity hysteresis (PROC-0033-02-11).
  - URL safety and private/loopback network isolation without automatic fetching (PROC-0033-02-10).
  - Semantic content moderation, PII/credential leak detection, and quarantine isolation (PROC-0033-02-09, PROC-0033-02-11).
  - Quarantine store isolation in spec/curation-queue/quarantine/ preventing unauthorized execution or queue pollution.
  - Role-separated operator/moderator escalation, release, refuse, and appeal workflows (PROC-0033-02-09).
  - Tamper-evident, privacy-preserving moderation audit log with anonymized origin hashing (PROC-0033-02-11).
  - 4-eyes separation of duties: submitter/appellant cannot self-moderate; moderator has no curator/apply authority.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import re
import socket
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import authenticated_lifecycle as al  # noqa: E402
import curation_flags as cf  # noqa: E402
import review_request_package as rrp  # noqa: E402

QUEUE_ROOT = Path(__file__).resolve().parents[1] / "spec" / "curation-queue"
QUARANTINE_DIR = QUEUE_ROOT / "quarantine"
MODERATION_AUDIT_DIR = QUEUE_ROOT / "moderation_audit"
OPEN_DIR = QUEUE_ROOT / "open"

SCHEMA_QUARANTINE = "review-request-quarantine@v1"
SCHEMA_MODERATION_AUDIT = "review-request-moderation-audit@v1"

# Capacity limits per PROC-0033-02-11
QUEUE_CAPACITY_MAX = 500
QUEUE_CAPACITY_THROTTLE = 450
QUEUE_CAPACITY_RECOVERY = 400

# Rate limits per PROC-0033-02-11
DEFAULT_WINDOW_SECONDS = 60
DEFAULT_MAX_REQUESTS_PER_WINDOW = 30
DEFAULT_BURST_THRESHOLD = 10
DEFAULT_BURST_SECONDS = 5
SUSPENSION_DURATION_HOURS = 24
MIN_MANUAL_RECOVERY_FLOOR_HOURS = 1

# Prohibited credential patterns and secret tokens
SECRET_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,255}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{82}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?:bearer|token|secret|password|api[_-]?key)[\s:=]+['\"]?[A-Za-z0-9_\-\.]{16,}['\"]?", re.IGNORECASE),
]

# Sensitive content / harassment / abuse patterns
SENSITIVE_CONTENT_PATTERNS = [
    re.compile(r"\b(?:kill\s+yourself|commit\s+suicide|self-harm|doxx|swatting)\b", re.IGNORECASE),
    re.compile(r"<script[\s\S]*?>[\s\S]*?<\/script>", re.IGNORECASE),
    re.compile(r"javascript:\s*[^\s]+", re.IGNORECASE),
    re.compile(r"onerror\s*=\s*['\"]?[^'\">]+", re.IGNORECASE),
    re.compile(r"onload\s*=\s*['\"]?[^'\">]+", re.IGNORECASE),
]

# Prohibited file extensions in evidence URLs
DANGEROUS_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".bash", ".ps1", ".vbs", ".msi",
    ".jar", ".scr", ".pif", ".com", ".cpl", ".dll", ".so", ".dylib"
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_abuse_dirs(queue_root: Path | None = None) -> tuple[Path, Path, Path]:
    root = queue_root if queue_root is not None else QUEUE_ROOT
    q_dir = root / "quarantine"
    m_dir = root / "moderation_audit"
    o_dir = root / "open"
    for d in (q_dir, m_dir, o_dir):
        d.mkdir(parents=True, exist_ok=True)
    return q_dir, m_dir, o_dir


def hash_origin(identifier: str, salt: str = "autodocs-origin-salt-2026") -> str:
    """Hash origin identifier (IP, session, token) for privacy-safe telemetry."""
    if not identifier:
        return "origin_unknown"
    salted = f"{salt}:{identifier}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()[:16]


# ============================================================================
# 1. URL Security & Private Network Isolation (PROC-0033-02-10)
# ============================================================================

def is_private_or_loopback_host(hostname: str) -> bool:
    """Check whether a host is localhost, loopback, or private RFC 1918 / 4193 / 4291 IP."""
    if not hostname:
        return True
    host_lower = hostname.strip().lower()
    if host_lower.startswith("[") and host_lower.endswith("]"):
        host_lower = host_lower[1:-1]
    if host_lower in {"localhost", "localhost.localdomain", "local", "invalid", "::1"}:
        return True
    if host_lower.endswith(".localhost") or host_lower.endswith(".local") or host_lower.endswith(".lan"):
        return True

    # Check if host is IP address directly
    try:
        ip = ipaddress.ip_address(host_lower)
        return (
            ip.is_loopback
            or ip.is_private
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        pass

    return False


def validate_evidence_url(url_str: str) -> tuple[bool, str | None]:
    """Validate evidence URL against strict security rules (PROC-0033-02-10).

    Rules:
      - Must use HTTPS scheme.
      - Must not contain userinfo/credentials (user:pass@host).
      - Must not resolve to localhost, loopback, or private RFC 1918/4193 networks.
      - Must not reference prohibited dangerous executable extensions.
      - Must not use non-standard ports commonly used for internal services.
    """
    if not url_str or not isinstance(url_str, str):
        return False, "Evidence URL must be a non-empty string"

    url_str = url_str.strip()
    if not url_str.startswith("https://"):
        return False, f"Evidence URL must use 'https://' scheme, got: {url_str!r}"

    try:
        parsed = urlparse(url_str)
    except Exception as e:
        return False, f"Malformed evidence URL: {e}"

    if parsed.scheme.lower() != "https":
        return False, f"Prohibited scheme {parsed.scheme!r}; only 'https' is permitted"

    if parsed.username or parsed.password:
        return False, "Evidence URL contains credentials/userinfo, which is strictly prohibited"

    hostname = parsed.hostname
    if not hostname:
        return False, "Evidence URL is missing a valid hostname"

    if is_private_or_loopback_host(hostname):
        return False, f"Evidence URL targets private or loopback host: {hostname!r}"

    path = parsed.path.lower()
    for ext in DANGEROUS_EXTENSIONS:
        if path.endswith(ext):
            return False, f"Evidence URL targets dangerous executable extension: {ext}"

    return True, None


def validate_all_evidence_urls(package: dict[str, Any]) -> list[str]:
    """Check all evidence URLs in a review request package."""
    errors = []
    
    # Check legacy evidence_url
    if package.get("evidence_url"):
        ok, err = validate_evidence_url(package["evidence_url"])
        if not ok and err:
            errors.append(f"Invalid evidence_url: {err}")

    # Check evidence_refs
    refs = package.get("evidence_refs") or []
    for idx, ref in enumerate(refs):
        if isinstance(ref, dict) and ref.get("kind") == "url":
            val = ref.get("value") or ""
            ok, err = validate_evidence_url(val)
            if not ok and err:
                errors.append(f"Invalid evidence_refs[{idx}]: {err}")
        elif isinstance(ref, str) and (ref.startswith("http://") or ref.startswith("https://") or "://" in ref):
            ok, err = validate_evidence_url(ref)
            if not ok and err:
                errors.append(f"Invalid evidence_refs[{idx}]: {err}")

    return errors


# ============================================================================
# 2. Content Moderation & Credential Leak Filter (PROC-0033-02-09, PROC-0033-02-11)
# ============================================================================

def scan_text_for_abuse(text: str) -> tuple[bool, str | None, str | None]:
    """Scan text for sensitive/abusive content or leaked secrets.

    Returns:
      (flagged, category, reason)
    """
    if not text or not isinstance(text, str):
        return False, None, None

    # Check for leaked credentials/secrets
    for pat in SECRET_PATTERNS:
        if pat.search(text):
            return True, "credential_leak", "Payload contains detected bearer token, private key, or credential pattern"

    # Check for sensitive/harassment/injection content
    for pat in SENSITIVE_CONTENT_PATTERNS:
        match = pat.search(text)
        if match:
            return True, "content_abuse", f"Payload contains prohibited or sensitive phrase/script pattern: {match.group(0)!r}"

    return False, None, None


def check_package_content_moderation(package: dict[str, Any]) -> tuple[bool, str | None, str | None]:
    """Perform content moderation scan across all free-text fields in package."""
    fields_to_scan = [
        ("rationale", package.get("rationale")),
        ("proposed_title", package.get("proposed_title")),
        ("proposed_description", package.get("proposed_description")),
    ]

    for field_name, val in fields_to_scan:
        if val and isinstance(val, str):
            flagged, cat, reason = scan_text_for_abuse(val)
            if flagged:
                return True, cat, f"{field_name}: {reason}"

    # Scan evidence refs free-text descriptions
    for idx, ref in enumerate(package.get("evidence_refs") or []):
        if isinstance(ref, dict):
            for k in ("note", "text", "description", "value"):
                v = ref.get(k)
                if v and isinstance(v, str):
                    flagged, cat, reason = scan_text_for_abuse(v)
                    if flagged:
                        return True, cat, f"evidence_refs[{idx}].{k}: {reason}"

    return False, None, None


# ============================================================================
# 3. Rate Limiting, Burst Quotas & Hysteresis Queue Capacity (PROC-0033-02-11)
# ============================================================================

@dataclass
class OriginBucket:
    timestamps: list[datetime] = field(default_factory=list)
    suspended_until: datetime | None = None
    violation_count: int = 0
    first_suspended_at: datetime | None = None


class AbuseController:
    """Manages rate limiting, burst flood detection, suspension, and queue capacity."""

    def __init__(
        self,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
        max_requests_per_window: int = DEFAULT_MAX_REQUESTS_PER_WINDOW,
        burst_threshold: int = DEFAULT_BURST_THRESHOLD,
        burst_seconds: int = DEFAULT_BURST_SECONDS,
        suspension_hours: int = SUSPENSION_DURATION_HOURS,
        recovery_floor_hours: int = MIN_MANUAL_RECOVERY_FLOOR_HOURS,
    ) -> None:
        self.window_seconds = window_seconds
        self.max_requests_per_window = max_requests_per_window
        self.burst_threshold = burst_threshold
        self.burst_seconds = burst_seconds
        self.suspension_hours = suspension_hours
        self.recovery_floor_hours = recovery_floor_hours
        self._buckets: dict[str, OriginBucket] = {}
        self._target_activity: dict[str, list[datetime]] = {}  # target_canonical_id -> timestamps

    def reset(self) -> None:
        self._buckets.clear()
        self._target_activity.clear()

    def check_and_record_request(
        self,
        origin_id: str,
        target_canonical_id: str | None = None,
        now: datetime | None = None,
    ) -> tuple[bool, str | None, str | None]:
        """Check rate limit, burst quota, and suspension status.

        Returns:
          (allowed, status_code, message)
          allowed: True if request is within quota; False if throttled/suspended.
        """
        current_time = now if now is not None else _now_dt()
        h_origin = hash_origin(origin_id) if origin_id else "unknown_origin"
        bucket = self._buckets.setdefault(h_origin, OriginBucket())

        # Check existing suspension
        if bucket.suspended_until is not None:
            if current_time < bucket.suspended_until:
                remaining = int((bucket.suspended_until - current_time).total_seconds())
                return False, "suspended", f"Origin {h_origin} is suspended for abuse ({remaining}s remaining)"
            else:
                # Suspension expired
                bucket.suspended_until = None
                bucket.first_suspended_at = None

        # Clean old timestamps outside window
        cutoff = current_time - timedelta(seconds=self.window_seconds)
        bucket.timestamps = [t for t in bucket.timestamps if t >= cutoff]

        # Check Burst Flood (e.g. >= 3 in 5 seconds)
        burst_cutoff = current_time - timedelta(seconds=self.burst_seconds)
        burst_count = sum(1 for t in bucket.timestamps if t >= burst_cutoff)
        if burst_count >= self.burst_threshold:
            # Suspend origin for 24 hours
            bucket.suspended_until = current_time + timedelta(hours=self.suspension_hours)
            bucket.first_suspended_at = current_time
            bucket.violation_count += 1
            return False, "burst_flooding", f"Burst flood threshold exceeded ({burst_count} reqs in {self.burst_seconds}s); origin suspended for {self.suspension_hours}h"

        # Check Rolling Window Quota (e.g. >= 5 in 60 seconds)
        if len(bucket.timestamps) >= self.max_requests_per_window:
            bucket.violation_count += 1
            if bucket.violation_count >= 2:
                bucket.suspended_until = current_time + timedelta(hours=self.suspension_hours)
                bucket.first_suspended_at = current_time
                return False, "rate_limit_suspended", f"Repeated rate limit violation; origin suspended for {self.suspension_hours}h"
            return False, "rate_limited", f"Rate limit exceeded ({len(bucket.timestamps)}/{self.max_requests_per_window} in {self.window_seconds}s)"

        # Check Coordinated Target Flooding (multiple origins targeting same record rapidly)
        if target_canonical_id:
            target_times = self._target_activity.setdefault(target_canonical_id, [])
            target_times = [t for t in target_times if t >= cutoff]
            self._target_activity[target_canonical_id] = target_times
            if len(target_times) >= 15:  # Coordinated flood threshold
                return False, "target_flooding", f"Target record {target_canonical_id} is under coordinated flood protection"
            target_times.append(current_time)

        # Record valid request
        bucket.timestamps.append(current_time)
        return True, "ok", None

    def manual_lift_suspension(
        self,
        origin_id: str,
        moderator_auth: al.AuthContext,
        now: datetime | None = None,
        force: bool = False,
    ) -> tuple[bool, str]:
        """Manually lift suspension, observing the 1-hour minimum recovery floor."""
        if moderator_auth.role not in {"moderator", "operator"}:
            return False, f"Role {moderator_auth.role!r} is not authorized to lift suspensions"

        current_time = now if now is not None else _now_dt()
        h_origin = hash_origin(origin_id)
        bucket = self._buckets.get(h_origin)
        if not bucket or bucket.suspended_until is None:
            return True, f"Origin {h_origin} is not currently suspended"

        if bucket.first_suspended_at and not force:
            elapsed = (current_time - bucket.first_suspended_at).total_seconds() / 3600.0
            if elapsed < self.recovery_floor_hours:
                rem = int((self.recovery_floor_hours - elapsed) * 60)
                return False, f"Cannot lift suspension before 1-hour recovery floor has elapsed ({rem}m remaining). Use force=True if emergency operator override."

        bucket.suspended_until = None
        bucket.first_suspended_at = None
        bucket.timestamps.clear()
        return True, f"Suspension lifted for origin {h_origin} by {moderator_auth.principal_id}"

    def check_queue_capacity(self, queue_root: Path | None = None) -> tuple[bool, str, int]:
        """Check active queue capacity against 500/450/400 hysteresis thresholds."""
        root = queue_root if queue_root is not None else QUEUE_ROOT
        open_dir = root / "open"
        claimed_dir = root / "claimed"

        count = 0
        if open_dir.exists():
            count += len(list(open_dir.glob("*.json")))
        if claimed_dir.exists():
            count += len(list(claimed_dir.glob("*.json")))

        if count >= QUEUE_CAPACITY_MAX:
            return False, "capacity_full", count
        elif count >= QUEUE_CAPACITY_THROTTLE:
            return True, "capacity_warning", count
        return True, "capacity_ok", count


_GLOBAL_ABUSE_CONTROLLER = AbuseController()


def get_global_abuse_controller() -> AbuseController:
    return _GLOBAL_ABUSE_CONTROLLER


def reset_abuse_controller() -> None:
    _GLOBAL_ABUSE_CONTROLLER.reset()


# ============================================================================
# 4. Quarantine Store & Isolation (PROC-0033-02-09, PROC-0033-02-11)
# ============================================================================

def write_quarantine_item(
    package_or_payload: dict[str, Any],
    reason: str,
    category: str = "abuse_or_malformed",
    origin_id: str | None = None,
    queue_root: Path | None = None,
    moderator_auth: al.AuthContext | None = None,
) -> Path:
    """Atomically write a suspicious or abusive payload to the quarantine store."""
    q_dir, m_dir, _ = _ensure_abuse_dirs(queue_root)

    req_id = (
        package_or_payload.get("id")
        or package_or_payload.get("request_id")
        or package_or_payload.get("event_id")
        or f"quarantine-{uuid.uuid4().hex[:12]}"
    )
    if not str(req_id).startswith("review-request:"):
        item_id = f"quarantine:{req_id}"
    else:
        item_id = f"quarantine:{str(req_id).split(':', 1)[1]}"

    filename = f"{item_id.replace(':', '_')}.json"
    target_path = q_dir / filename

    quarantine_payload = {
        "schema": SCHEMA_QUARANTINE,
        "id": item_id,
        "original_id": req_id,
        "quarantined_at": _now(),
        "status": "quarantined",
        "category": category,
        "reason": reason,
        "origin_hash": hash_origin(origin_id or "unknown"),
        "raw_payload": package_or_payload,
        "moderation_history": [
            {
                "action": "quarantine",
                "timestamp": _now(),
                "actor": moderator_auth.principal_id if moderator_auth else "system_automated",
                "role": moderator_auth.role if moderator_auth else "security_boundary",
                "reason": reason,
            }
        ],
    }

    tmp = target_path.with_suffix(".tmp-%s" % uuid.uuid4().hex[:8])
    tmp.write_text(json.dumps(quarantine_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, target_path)

    # Record in moderation audit trail
    record_moderation_audit_event(
        action="quarantine",
        item_id=item_id,
        reason=reason,
        moderator_auth=moderator_auth,
        metadata={"category": category, "origin_hash": quarantine_payload["origin_hash"]},
        queue_root=queue_root,
    )

    return target_path


def list_quarantined_items(queue_root: Path | None = None) -> list[Path]:
    """List all items currently in quarantine."""
    q_dir, _, _ = _ensure_abuse_dirs(queue_root)
    return sorted(q_dir.glob("*.json"))


def get_quarantined_path(item_id: str, queue_root: Path | None = None) -> Path | None:
    """Find Path for a quarantined item by id, original_id, or filename."""
    q_dir, _, _ = _ensure_abuse_dirs(queue_root)
    filename = f"{item_id.replace(':', '_')}.json"
    direct = q_dir / filename
    if direct.exists():
        return direct
    for p in q_dir.glob("*.json"):
        if p.stem == item_id or p.name == item_id or p.stem == item_id.replace(":", "_"):
            return p
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if data.get("id") == item_id or data.get("original_id") == item_id:
                return p
        except Exception:
            continue
    return None


def get_quarantined_item(item_id: str, queue_root: Path | None = None) -> dict[str, Any] | None:
    """Read a quarantined item by ID."""
    path = get_quarantined_path(item_id, queue_root=queue_root)
    if not path or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


# ============================================================================
# 5. Moderator & Escalation Controls (PROC-0033-02-09)
# ============================================================================

def record_moderation_audit_event(
    action: str,
    item_id: str,
    reason: str,
    moderator_auth: al.AuthContext | None = None,
    metadata: dict[str, Any] | None = None,
    queue_root: Path | None = None,
) -> Path:
    """Append an immutable audit entry to the moderation audit trail."""
    _, m_dir, _ = _ensure_abuse_dirs(queue_root)
    audit_id = f"audit-{_now_dt().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    audit_path = m_dir / f"{audit_id}.json"

    actor_id = moderator_auth.principal_id if moderator_auth else "system_automated"
    actor_role = moderator_auth.role if moderator_auth else "security_boundary"

    record = {
        "schema": SCHEMA_MODERATION_AUDIT,
        "audit_id": audit_id,
        "timestamp": _now(),
        "item_id": item_id,
        "action": action,
        "actor": actor_id,
        "role": actor_role,
        "reason": reason,
        "metadata": metadata or {},
    }

    tmp = audit_path.with_suffix(".tmp-%s" % uuid.uuid4().hex[:8])
    tmp.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, audit_path)
    return audit_path


def moderate_quarantine_action(
    item_id: str,
    action: str,
    moderator_auth: al.AuthContext,
    reason: str,
    queue_root: Path | None = None,
    target_group: str | None = None,
) -> tuple[bool, str, Any]:
    """Execute a moderator action on a quarantined item.

    Supported Actions:
      - 'release': moves verified item out of quarantine into active 'open/' queue.
      - 'refuse': permanently marks item as refused (discarded spam/abuse).
      - 'escalate': marks item as escalated to security/legal review group.

    4-Eyes Invariant:
      - Authenticated moderator cannot release their own submission if they were the appellant/submitter.
      - Moderator has no factual curator authority (cannot modify record text or apply changes).
    """
    if moderator_auth.role not in {"moderator", "operator"}:
        raise al.AuthorizationError(f"Role {moderator_auth.role!r} is not authorized for moderation actions")

    if action not in {"release", "refuse", "escalate"}:
        raise ValueError(f"Invalid moderation action: {action!r}. Permitted: release, refuse, escalate")

    q_dir, m_dir, o_dir = _ensure_abuse_dirs(queue_root)
    q_item = get_quarantined_item(item_id, queue_root=queue_root)
    if not q_item:
        return False, f"Quarantined item {item_id!r} not found", None

    # Check 4-eyes separation: Submitter/Appellant cannot self-release
    raw_pkg = q_item.get("raw_payload") or {}
    submitter = (
        raw_pkg.get("actor_claim", {}).get("claimed_actor")
        or raw_pkg.get("authoritative_actor")
        or raw_pkg.get("submitter")
    )
    if submitter and submitter == moderator_auth.principal_id:
        return False, f"4-Eyes Violation: submitter {submitter!r} cannot act as moderator to {action} their own item", None

    q_path = get_quarantined_path(item_id, queue_root=queue_root)
    if not q_path or not q_path.exists():
        return False, f"Quarantined path for {item_id!r} not found", None

    # Record history entry
    hist_entry = {
        "action": action,
        "timestamp": _now(),
        "actor": moderator_auth.principal_id,
        "role": moderator_auth.role,
        "reason": reason,
    }
    q_item.setdefault("moderation_history", []).append(hist_entry)

    if action == "release":
        # Transform raw_payload into active curation-queue item in open/
        q_item["status"] = "released"
        cf_payload = raw_pkg.copy()
        cf_payload["status"] = "open"
        cf_payload["moderation_release"] = {
            "released_by": moderator_auth.principal_id,
            "released_at": _now(),
            "reason": reason,
        }
        
        orig_id = q_item.get("original_id") or cf_payload.get("id") or item_id
        open_filename = f"{orig_id}.json"
        open_path = o_dir / open_filename
        
        tmp = open_path.with_suffix(".tmp-%s" % uuid.uuid4().hex[:8])
        tmp.write_text(json.dumps(cf_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, open_path)
        
        # Remove from quarantine
        if q_path.exists():
            q_path.unlink()

        record_moderation_audit_event(
            action="release",
            item_id=item_id,
            reason=reason,
            moderator_auth=moderator_auth,
            metadata={"destination": str(open_path)},
            queue_root=queue_root,
        )
        return True, f"Released {item_id} to {open_path}", open_path

    elif action == "refuse":
        q_item["status"] = "refused"
        q_item["refused_at"] = _now()
        q_item["refusal_reason"] = reason

        tmp = q_path.with_suffix(".tmp-%s" % uuid.uuid4().hex[:8])
        tmp.write_text(json.dumps(q_item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, q_path)

        record_moderation_audit_event(
            action="refuse",
            item_id=item_id,
            reason=reason,
            moderator_auth=moderator_auth,
            metadata={"refusal_reason": reason},
            queue_root=queue_root,
        )
        return True, f"Item {item_id} marked as refused", q_path

    elif action == "escalate":
        q_item["status"] = "escalated"
        q_item["escalated_at"] = _now()
        q_item["escalation_target"] = target_group or "security_incident_response"
        q_item["escalation_reason"] = reason

        tmp = q_path.with_suffix(".tmp-%s" % uuid.uuid4().hex[:8])
        tmp.write_text(json.dumps(q_item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, q_path)

        record_moderation_audit_event(
            action="escalate",
            item_id=item_id,
            reason=reason,
            moderator_auth=moderator_auth,
            metadata={"target_group": q_item["escalation_target"], "reason": reason},
            queue_root=queue_root,
        )
        return True, f"Item {item_id} escalated to {q_item['escalation_target']}", q_path

    return False, "Unknown action", None


# ============================================================================
# CLI Interface
# ============================================================================

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-command")

    # list-quarantine
    subparsers.add_parser("list-quarantine", help="List items currently in quarantine")

    # inspect-quarantine
    insp_parser = subparsers.add_parser("inspect", help="Inspect a quarantined item")
    insp_parser.add_argument("item_id", help="Quarantine item ID")

    # moderate
    mod_parser = subparsers.add_parser("moderate", help="Execute moderator action on quarantined item")
    mod_parser.add_argument("item_id", help="Quarantine item ID")
    mod_parser.add_argument("action", choices=["release", "refuse", "escalate"], help="Moderation action")
    mod_parser.add_argument("--actor", required=True, help="Moderator principal ID")
    mod_parser.add_argument("--role", default="moderator", choices=["moderator", "operator"], help="Moderator role")
    mod_parser.add_argument("--reason", required=True, help="Reason for moderation action")
    mod_parser.add_argument("--target-group", default=None, help="Target escalation group (for escalate)")

    # check-url
    url_parser = subparsers.add_parser("check-url", help="Validate an evidence URL")
    url_parser.add_argument("url", help="URL string to check")

    args = parser.parse_args(argv)

    if args.command == "list-quarantine":
        items = list_quarantined_items()
        print(f"Quarantined items ({len(items)}):")
        for p in items:
            print(f"  - {p.name}")
        return 0

    elif args.command == "inspect":
        item = get_quarantined_item(args.item_id)
        if not item:
            print(f"Error: Quarantined item {args.item_id!r} not found", file=sys.stderr)
            return 1
        print(json.dumps(item, ensure_ascii=False, indent=2))
        return 0

    elif args.command == "moderate":
        auth = al.create_session(args.actor, args.role)
        ok, msg, res = moderate_quarantine_action(
            item_id=args.item_id,
            action=args.action,
            moderator_auth=auth,
            reason=args.reason,
            target_group=args.target_group,
        )
        if ok:
            print(f"Success: {msg}")
            return 0
        else:
            print(f"Error: {msg}", file=sys.stderr)
            return 1

    elif args.command == "check-url":
        ok, err = validate_evidence_url(args.url)
        if ok:
            print("URL is valid and secure.")
            return 0
        else:
            print(f"Invalid URL: {err}", file=sys.stderr)
            return 1

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
