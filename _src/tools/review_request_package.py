#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""review_request_package.py -- Strict validation and canonical identity utilities.

Implements strict validation for review-request-package@v1, review-request-package@v2,
and review-request envelopes (review-request-envelope@v1, review-request-local-envelope@v1).

Addresses:
  - RRB-SCHEMA-001: Strict types, schema enums, format rules, closed properties,
    and prohibition of server-owned / sensitive / credential fields.
  - RRB-SCHEMA-002: Type-safe parsing and diagnostics without uncaught TypeErrors,
    AttributeErrors, or crashes on untrusted JSON types.
  - RRB-IDENT-001: Deterministic canonicalization (autodocs-canonical-json-nfc-lf@v1),
    concern-key derivation, UUIDv7 parsing, and staleness checking.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import sys
import unicodedata
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from canonical_id import parse_canonical_id as _base_parse_canonical_id  # noqa: E402
from version_id import parse_version_id as _base_parse_version_id, uuid7  # noqa: E402

# Schema identifiers
SCHEMA_V1 = "review-request-package@v1"
SCHEMA_V2 = "review-request-package@v2"
SCHEMA = SCHEMA_V1  # Default / backward-compatible schema name

ENVELOPE_KIND_V1 = "review-request-envelope@v1"
LOCAL_ENVELOPE_KIND_V1 = "review-request-local-envelope@v1"

# Enumerations
VALID_CATEGORY_V1 = (
    "factual-accuracy",
    "outdated-source",
    "missing-context",
    "ai-hallucination-suspected",
    "other",
)

VALID_CATEGORY_V2 = (
    "factual-error",
    "outdated-content",
    "broken-link",
    "accessibility",
    "other",
)

# Combined valid categories
VALID_CATEGORY = VALID_CATEGORY_V1

VALID_TRANSPORT = ("github_issue", "json_export")
VALID_ACTOR_IDENTITY = ("github_authenticated", "self_declared")

VALID_ENVELOPE_KINDS = (ENVELOPE_KIND_V1, LOCAL_ENVELOPE_KIND_V1)

VALID_TRUST_PROFILES = (
    "github-api-refetch-v1",
    "github-webhook-sha256-v1",
    "github-webhook-sha256+api-refetch-v1",
    "local-import-v1",
)

# Required fields
REQUIRED_FIELDS_V1 = (
    "schema",
    "client_schema_version",
    "request_id",
    "target_canonical_id",
    "target_version_id",
    "target_content_hash",
    "target_status_snapshot",
    "source_url",
    "category",
    "rationale",
    "actor_claim",
    "created_at",
    "transport",
)
REQUIRED_FIELDS = REQUIRED_FIELDS_V1

REQUIRED_FIELDS_V2 = (
    "kind",
    "event_id",
    "target_canonical_id",
    "category",
    "rationale",
)

ALLOWED_PROPERTIES_V1 = {
    "schema",
    "client_schema_version",
    "request_id",
    "target_canonical_id",
    "target_version_id",
    "target_content_hash",
    "target_status_snapshot",
    "source_url",
    "category",
    "rationale",
    "actor_claim",
    "created_at",
    "transport",
    "evidence_refs",
    "evidence_links",
}

ALLOWED_PROPERTIES_V2 = {
    "kind",
    "event_id",
    "concern_key",
    "target_canonical_id",
    "category",
    "rationale",
    "evidence_url",
    "envelope_kind",
    "trust_profile",
}

ALLOWED_PROPERTIES_ENVELOPE = {
    "envelope_kind",
    "event_id",
    "package",
    "package_sha256",
    "trust_profile",
    "authoritative_actor",
    "repository",
    "issue_number",
    "delivery_id",
    "received_at",
}

ALLOWED_PROPERTIES_LOCAL_ENVELOPE = {
    "envelope_kind",
    "event_id",
    "package",
    "package_sha256",
    "trust_profile",
    "received_at",
}

# Forbidden server-owned, sensitive, credential, and fingerprint fields
FORBIDDEN_FIELDS = {
    "verified",
    "status",
    "pat_token",
    "session_token",
    "signature_secret",
    "decided_by",
    "applied_at",
    "received_at",
    "server_timestamp",
    "session_id",
    "trust",
    "ip",
    "ip_address",
    "client_ip",
    "remote_addr",
    "fingerprint",
    "client_fingerprint",
    "device_fingerprint",
    "token",
    "bearer_token",
    "auth_token",
    "authorization",
    "cookie",
    "secret",
    "password",
    "api_key",
}

# Regular expressions
_UUID7_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_REQUEST_ID_RE = re.compile(
    r"^review-request:[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_HASH8_RE = re.compile(r"^[0-9a-f]{8}$")
_HASH64_RE = re.compile(r"^[0-9a-f]{64}$")
_SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)(?:\.(0|[1-9]\d*))?"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)
_ISO8601_UTC_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(\.\d+)?(Z|[+-]00:00|-00:00)$"
)
_CANON_RECORD_RE = re.compile(r"^[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+$")
_CANON_QUALIFIED_RE = re.compile(r"^[a-zA-Z0-9_-]+:[a-zA-Z0-9_:\.\-]+$")
_UNSAFE_HTML_RE = re.compile(r"<\s*script\b|javascript\s*:|<\s*iframe\b|\bon\w+\s*=", re.IGNORECASE)
_MARKDOWN_FENCE_UNMATCHED_RE = re.compile(r"(?<!\\)```")


# ============================================================================
# Parsers and Low-Level Validators
# ============================================================================

def parse_uuid7(value: Any) -> dict | None:
    """Parse and validate an RFC 9562 UUIDv7 string."""
    if not isinstance(value, str):
        return None
    if not _UUID7_RE.match(value):
        return None
    try:
        clean = value.replace("-", "")
        unix_ms = int(clean[:12], 16)
        version = int(clean[12], 16)
        variant_nibble = int(clean[16], 16)
        if version != 7 or variant_nibble not in (8, 9, 0xA, 0xB, 0xa, 0xb):
            return None
        return {
            "uuid": value.lower(),
            "unix_ms": unix_ms,
            "version": version,
            "variant": "RFC 9562",
        }
    except Exception:
        return None


def is_valid_uuid7(value: Any) -> bool:
    """Return True if value is a valid UUIDv7 string."""
    return parse_uuid7(value) is not None


def new_request_id() -> str:
    """Mint a fresh UUIDv7 request_id for review-request-package@v1."""
    return f"review-request:{uuid7()}"


def new_event_id() -> str:
    """Mint a fresh RFC 9562 UUIDv7 event_id for review-request-package@v2."""
    return uuid7()


def parse_canonical_id(value: Any) -> dict | None:
    """Safely parse canonical ID (e.g. AUTOSAR/AP/record/tsync or class:ara::exec::ExecutionClient)."""
    if not isinstance(value, str) or not value.strip():
        return None
    # Reject control characters or whitespace
    if any(ord(c) < 32 or ord(c) == 127 for c in value) or " " in value:
        return None
    res = _base_parse_canonical_id(value)
    if res is not None:
        return res
    if _CANON_QUALIFIED_RE.match(value):
        prefix, rest = value.split(":", 1)
        return {"kind": prefix, "id": rest}
    if _CANON_RECORD_RE.match(value):
        parts = value.split("/", 2)
        return {"project": f"{parts[0]}/{parts[1]}", "kind": parts[2].split("/")[0], "id": parts[2].split("/", 1)[1]}
    return None


def parse_version_id(value: Any) -> dict | None:
    """Safely parse requirement version id: <canonical_id>@rel:<release>#<hash8>."""
    if not isinstance(value, str) or not value.strip():
        return None
    if any(ord(c) < 32 or ord(c) == 127 for c in value) or " " in value:
        return None
    return _base_parse_version_id(value)


def parse_semver(value: Any) -> dict | None:
    """Safely parse semver string."""
    if not isinstance(value, str) or not value.strip():
        return None
    m = _SEMVER_RE.match(value)
    if not m:
        return None
    major, minor, patch, prerelease, build = m.groups()
    return {
        "major": int(major),
        "minor": int(minor),
        "patch": int(patch) if patch is not None else 0,
        "prerelease": prerelease,
        "build": build,
    }


def parse_utc_timestamp(value: Any) -> datetime | None:
    """Safely parse ISO 8601 UTC timestamp and validate calendar date."""
    if not isinstance(value, str) or not value.strip():
        return None
    m = _ISO8601_UTC_RE.match(value)
    if not m:
        return None
    year, month, day, hour, minute, second, frac, tz = m.groups()
    try:
        y, mo, d = int(year), int(month), int(day)
        h, mi, s = int(hour), int(minute), int(second)
        us = int(float(frac) * 1_000_000) if frac else 0
        dt = datetime(y, mo, d, h, mi, s, us, tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def parse_url(value: Any) -> dict | None:
    """Safely parse URL, checking scheme, authority, and safety."""
    if not isinstance(value, str) or not value.strip():
        return None
    if any(ord(c) < 32 or ord(c) == 127 for c in value) or " " in value:
        return None
    try:
        parsed = urllib.parse.urlsplit(value)
        return {
            "scheme": parsed.scheme,
            "netloc": parsed.netloc,
            "path": parsed.path,
            "query": parsed.query,
            "fragment": parsed.fragment,
            "username": parsed.username,
            "password": parsed.password,
            "hostname": parsed.hostname,
            "port": parsed.port,
        }
    except Exception:
        return None


def _check_text_safety(text: str, field_name: str, allow_newlines: bool = True) -> list[str]:
    """Check text for control characters, unsafe HTML/script, and broken fences."""
    errors = []
    # Check control characters
    for ch in text:
        code = ord(ch)
        if code == 127 or (code < 32 and ch not in ("\n", "\r", "\t")):
            errors.append(f"{field_name} contains forbidden control character (code {code})")
            break
        if not allow_newlines and ch in ("\n", "\r", "\t"):
            errors.append(f"{field_name} must not contain newlines or tabs")
            break

    # Unsafe script / HTML tags
    if _UNSAFE_HTML_RE.search(text):
        errors.append(f"{field_name} contains disallowed HTML tags or script patterns")

    return errors


def validate_url_field(
    url_str: Any,
    field_name: str,
    allow_relative: bool = False,
) -> list[str]:
    """Validate a URL field against allowed schemes, no credentials, and no private targets."""
    errors = []
    if not isinstance(url_str, str):
        return [f"{field_name} must be a string"]

    text_errs = _check_text_safety(url_str, field_name, allow_newlines=False)
    if text_errs:
        return text_errs

    parsed = parse_url(url_str)
    if not parsed:
        return [f"{field_name} is not a valid URL: {url_str!r}"]

    scheme = parsed["scheme"].lower() if parsed["scheme"] else ""
    if not scheme:
        if allow_relative and parsed["path"].startswith("/"):
            return []
        return [f"{field_name} missing required URL scheme (http/https): {url_str!r}"]

    if scheme not in ("http", "https"):
        return [f"{field_name} has disallowed scheme {scheme!r} (must be http or https)"]

    if parsed["username"] or parsed["password"]:
        return [f"{field_name} must not contain embedded credentials (user:password)"]

    hostname = parsed["hostname"]
    if not hostname:
        return [f"{field_name} missing host in URL: {url_str!r}"]

    hostname_lower = hostname.lower()
    if hostname_lower in ("localhost", "0.0.0.0") or hostname_lower.endswith(".localhost") or hostname_lower.endswith(".local"):
        return [f"{field_name} cannot target localhost or private host: {hostname!r}"]

    # Check for private / loopback IP addresses
    try:
        ip = ipaddress.ip_address(hostname_lower)
        if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local or ip.is_unspecified:
            errors.append(f"{field_name} cannot target private or loopback IP address: {hostname!r}")
    except ValueError:
        pass

    return errors


# ============================================================================
# Core Validation
# ============================================================================

def validate_package_v1(package: dict) -> list[str]:
    """Strictly validate a review-request-package@v1 object."""
    errors: list[str] = []

    # Check additional properties
    for key in sorted(package.keys()):
        if key not in ALLOWED_PROPERTIES_V1:
            errors.append(f"additional property {key!r} not permitted in {SCHEMA_V1}")

    # Check forbidden server-owned / sensitive fields
    for key in sorted(package.keys()):
        if key in FORBIDDEN_FIELDS:
            errors.append(f"forbidden field {key!r} is server-owned or sensitive and cannot be client-authored")

    # Required fields check
    for field in REQUIRED_FIELDS_V1:
        if field not in package:
            errors.append(f"missing required field: {field}")

    # schema
    schema_val = package.get("schema")
    if schema_val is not None:
        if not isinstance(schema_val, str):
            errors.append(f"schema must be a string: got {type(schema_val).__name__}")
        elif schema_val != SCHEMA_V1:
            errors.append(f"unknown schema: {schema_val!r} (expected {SCHEMA_V1!r})")

    # client_schema_version
    csv = package.get("client_schema_version")
    if csv is not None:
        if not isinstance(csv, str):
            errors.append(f"client_schema_version must be a string: got {type(csv).__name__}")
        elif not parse_semver(csv):
            errors.append(f"client_schema_version is not valid semver: {csv!r}")

    # request_id
    rid = package.get("request_id")
    if rid is not None:
        if not isinstance(rid, str):
            errors.append(f"request_id must be a string: got {type(rid).__name__}")
        elif not _REQUEST_ID_RE.match(rid):
            errors.append(f"request_id does not match 'review-request:<uuid7>': {rid!r}")
        else:
            uuid_part = rid.split(":", 1)[1]
            if not is_valid_uuid7(uuid_part):
                errors.append(f"request_id UUID component is not a valid UUIDv7: {uuid_part!r}")

    # target_canonical_id
    tcid = package.get("target_canonical_id")
    if tcid is not None:
        if not isinstance(tcid, str):
            errors.append(f"target_canonical_id must be a string: got {type(tcid).__name__}")
        elif not tcid.strip():
            errors.append("target_canonical_id must be a non-empty string")
        elif parse_canonical_id(tcid) is None:
            errors.append(f"target_canonical_id is not a valid canonical id: {tcid!r}")

    # target_content_hash
    tchash = package.get("target_content_hash")
    if tchash is not None:
        if not isinstance(tchash, str):
            errors.append(f"target_content_hash must be a string: got {type(tchash).__name__}")
        elif not _HASH8_RE.match(tchash):
            errors.append(f"target_content_hash is not 8 hex chars: {tchash!r}")

    # target_version_id (nullable string)
    if "target_version_id" in package:
        tvid = package.get("target_version_id")
        if tvid is not None:
            if not isinstance(tvid, str):
                errors.append(f"target_version_id must be a string or null: got {type(tvid).__name__}")
            else:
                pvid = parse_version_id(tvid)
                if pvid is None:
                    errors.append(f"target_version_id is not a valid version id: {tvid!r}")
                else:
                    # Relationship checks
                    if isinstance(tcid, str) and tcid.strip() and pvid.get("canonical_id") != tcid:
                        errors.append(
                            f"target_version_id canonical prefix {pvid.get('canonical_id')!r} "
                            f"does not match target_canonical_id {tcid!r}"
                        )
                    if isinstance(tchash, str) and _HASH8_RE.match(tchash) and pvid.get("hash8") != tchash:
                        errors.append(
                            f"target_version_id content hash {pvid.get('hash8')!r} "
                            f"does not match target_content_hash {tchash!r}"
                        )

    # target_status_snapshot
    tss = package.get("target_status_snapshot")
    if tss is not None:
        if not isinstance(tss, str):
            errors.append(f"target_status_snapshot must be a string: got {type(tss).__name__}")
        elif not tss.strip():
            errors.append("target_status_snapshot must be a non-empty string")
        elif len(tss) > 100:
            errors.append("target_status_snapshot exceeds maximum length 100")
        else:
            errors.extend(_check_text_safety(tss, "target_status_snapshot", allow_newlines=False))

    # source_url
    surl = package.get("source_url")
    if surl is not None:
        errors.extend(validate_url_field(surl, "source_url", allow_relative=True))

    # category
    cat = package.get("category")
    if cat is not None:
        if not isinstance(cat, str):
            errors.append(f"category must be a string: got {type(cat).__name__}")
        elif cat not in VALID_CATEGORY_V1 and cat not in VALID_CATEGORY_V2:
            errors.append(f"category must be one of {VALID_CATEGORY_V1}: got {cat!r}")

    # rationale
    rat = package.get("rationale")
    if rat is not None:
        if not isinstance(rat, str):
            errors.append(f"rationale must be a string: got {type(rat).__name__}")
        elif not rat.strip():
            errors.append("rationale must be a non-empty string")
        elif len(rat) > 4000:
            errors.append(f"rationale exceeds maximum length 4000: got {len(rat)}")
        else:
            errors.extend(_check_text_safety(rat, "rationale", allow_newlines=True))

    # actor_claim
    if "actor_claim" in package:
        actor = package.get("actor_claim")
        if not isinstance(actor, dict):
            errors.append(f"actor_claim must be an object: got {type(actor).__name__}")
        else:
            # Check for forbidden fields inside actor_claim
            for k in actor:
                if k in FORBIDDEN_FIELDS:
                    errors.append(f"forbidden field {k!r} in actor_claim is not permitted")

            dname = actor.get("display_name")
            if dname is None and "name" in actor:
                dname = actor.get("name")
            if dname is None:
                errors.append("actor_claim.display_name must be present")
            elif not isinstance(dname, str):
                errors.append(f"actor_claim.display_name must be a string: got {type(dname).__name__}")
            elif not dname.strip():
                errors.append("actor_claim.display_name must be non-empty")
            elif len(dname) > 100:
                errors.append("actor_claim.display_name exceeds maximum length 100")
            else:
                errors.extend(_check_text_safety(dname, "actor_claim.display_name", allow_newlines=False))

            ikind = actor.get("identity_kind")
            if ikind is None and "identity" in actor:
                ikind = actor.get("identity")
            if ikind is None:
                errors.append("actor_claim.identity_kind must be present")
            elif not isinstance(ikind, str):
                errors.append(f"actor_claim.identity_kind must be a string: got {type(ikind).__name__}")
            elif ikind not in VALID_ACTOR_IDENTITY:
                errors.append(f"actor_claim.identity_kind must be one of {VALID_ACTOR_IDENTITY}: got {ikind!r}")

    # created_at
    created_at = package.get("created_at")
    if created_at is not None:
        if not isinstance(created_at, str):
            errors.append(f"created_at must be a string: got {type(created_at).__name__}")
        elif parse_utc_timestamp(created_at) is None:
            errors.append(f"created_at is not ISO 8601 UTC timestamp: {created_at!r}")

    # transport
    trans = package.get("transport")
    if trans is not None:
        if not isinstance(trans, str):
            errors.append(f"transport must be a string: got {type(trans).__name__}")
        elif trans not in VALID_TRANSPORT:
            errors.append(f"transport must be one of {VALID_TRANSPORT}: got {trans!r}")

    # evidence_refs
    if "evidence_refs" in package:
        refs = package.get("evidence_refs")
        if not isinstance(refs, list):
            errors.append(f"evidence_refs must be a list: got {type(refs).__name__}")
        else:
            for i, ref in enumerate(refs):
                if not isinstance(ref, dict):
                    errors.append(f"evidence_refs[{i}] must be an object")
                    continue
                for k in ref:
                    if k in FORBIDDEN_FIELDS:
                        errors.append(f"forbidden field {k!r} in evidence_refs[{i}] is not permitted")
                if "kind" not in ref:
                    errors.append(f"evidence_refs[{i}] missing required field 'kind'")
                elif not isinstance(ref["kind"], str) or not ref["kind"].strip():
                    errors.append(f"evidence_refs[{i}].kind must be a non-empty string")
                if "value" not in ref:
                    errors.append(f"evidence_refs[{i}] missing required field 'value'")
                elif not isinstance(ref["value"], str) or not ref["value"].strip():
                    errors.append(f"evidence_refs[{i}].value must be a non-empty string")
                else:
                    errors.extend(_check_text_safety(ref["value"], f"evidence_refs[{i}].value", allow_newlines=False))
                if "note" in ref and ref["note"] is not None:
                    if not isinstance(ref["note"], str):
                        errors.append(f"evidence_refs[{i}].note must be a string")
                    elif len(ref["note"]) > 500:
                        errors.append(f"evidence_refs[{i}].note exceeds maximum length 500")

    # evidence_links
    if "evidence_links" in package:
        links = package.get("evidence_links")
        if not isinstance(links, list):
            errors.append(f"evidence_links must be a list: got {type(links).__name__}")
        else:
            for i, link in enumerate(links):
                errors.extend(validate_url_field(link, f"evidence_links[{i}]"))

    return errors


def validate_package_v2(package: dict) -> list[str]:
    """Strictly validate a review-request-package@v2 object."""
    errors: list[str] = []

    # Check additional properties
    for key in sorted(package.keys()):
        if key not in ALLOWED_PROPERTIES_V2:
            errors.append(f"additional properties not permitted: {key!r}")

    # Check forbidden server-owned / sensitive fields
    for key in sorted(package.keys()):
        if key in FORBIDDEN_FIELDS:
            errors.append(f"forbidden server/trust/credential fields present: {key!r}")

    # Required fields check
    for field in REQUIRED_FIELDS_V2:
        if field not in package:
            errors.append(f"missing required field: {field}")

    # kind
    kind_val = package.get("kind")
    if kind_val is not None:
        if not isinstance(kind_val, str) or kind_val != SCHEMA_V2:
            errors.append(f"kind must be the exact literal {SCHEMA_V2}")

    # event_id
    event_id = package.get("event_id")
    if event_id is not None:
        if not isinstance(event_id, str) or not is_valid_uuid7(event_id):
            errors.append("event_id is not a syntactically valid UUIDv7")

    # concern_key (optional / nullable string)
    if "concern_key" in package:
        ck = package.get("concern_key")
        if ck is not None:
            if not isinstance(ck, str) or not _HASH64_RE.match(ck):
                errors.append("concern_key must be 64 lowercase hex characters or null")

    # target_canonical_id
    tcid = package.get("target_canonical_id")
    if tcid is not None:
        if not isinstance(tcid, str) or not tcid.strip():
            errors.append("target_canonical_id must be present and non-empty")
        elif parse_canonical_id(tcid) is None:
            errors.append(f"target_canonical_id is not a valid canonical id: {tcid!r}")

    # category
    cat = package.get("category")
    if cat is not None:
        if not isinstance(cat, str) or cat not in VALID_CATEGORY_V2:
            errors.append(f"category {cat!r} not in closed enum")

    # rationale
    rat = package.get("rationale")
    if rat is not None:
        if not isinstance(rat, str):
            errors.append("rationale must be a string")
        elif not rat.strip():
            errors.append("rationale must be a non-empty string")
        elif len(rat) > 2000:
            errors.append(f"rationale exceeds maximum length 2000: got {len(rat)}")
        else:
            errors.extend(_check_text_safety(rat, "rationale", allow_newlines=True))

    # evidence_url (optional / nullable string)
    if "evidence_url" in package:
        eurl = package.get("evidence_url")
        if eurl is not None:
            errors.extend(validate_url_field(eurl, "evidence_url"))

    # envelope_kind (optional / nullable string)
    if "envelope_kind" in package:
        ek = package.get("envelope_kind")
        if ek is not None and ek not in VALID_ENVELOPE_KINDS:
            errors.append(f"envelope_kind must be one of {VALID_ENVELOPE_KINDS} or null: got {ek!r}")

    # trust_profile (optional / nullable string)
    if "trust_profile" in package:
        tp = package.get("trust_profile")
        if tp is not None and tp not in VALID_TRUST_PROFILES:
            errors.append(f"trust_profile must be one of {VALID_TRUST_PROFILES} or null: got {tp!r}")

    return errors


def validate_envelope(envelope: dict) -> list[str]:
    """Strictly validate a review-request envelope."""
    errors: list[str] = []
    if not isinstance(envelope, dict):
        return ["envelope must be a JSON object"]

    kind = envelope.get("envelope_kind")
    if kind not in VALID_ENVELOPE_KINDS:
        return [f"unknown or missing envelope_kind: {kind!r} (expected one of {VALID_ENVELOPE_KINDS})"]

    is_local = kind == LOCAL_ENVELOPE_KIND_V1
    allowed = ALLOWED_PROPERTIES_LOCAL_ENVELOPE if is_local else ALLOWED_PROPERTIES_ENVELOPE

    for key in sorted(envelope.keys()):
        if key not in allowed:
            errors.append(f"additional property {key!r} not permitted in {kind}")

    forbidden_envelope = FORBIDDEN_FIELDS - allowed
    for key in sorted(envelope.keys()):
        if key in forbidden_envelope:
            errors.append(f"forbidden field {key!r} is not permitted in envelope")

    # event_id
    eid = envelope.get("event_id")
    if eid is None or not is_valid_uuid7(eid):
        errors.append("envelope event_id must be a valid UUIDv7")

    # package
    pkg = envelope.get("package")
    if not isinstance(pkg, dict):
        errors.append("envelope package must be an object")
    else:
        pkg_errs = validate(pkg)
        for err in pkg_errs:
            errors.append(f"envelope.package: {err}")

    # package_sha256
    psha = envelope.get("package_sha256")
    if psha is None or not isinstance(psha, str) or not _HASH64_RE.match(psha):
        errors.append("envelope package_sha256 must be 64 hex characters")
    elif isinstance(pkg, dict):
        actual_sha = hashlib.sha256(canonical_json_bytes(pkg)).hexdigest()
        if psha != actual_sha:
            errors.append(f"envelope package_sha256 mismatch: expected {actual_sha}, got {psha}")

    # trust_profile
    tp = envelope.get("trust_profile")
    if tp is not None and tp not in VALID_TRUST_PROFILES:
        errors.append(f"envelope trust_profile must be one of {VALID_TRUST_PROFILES}")

    # received_at
    rat = envelope.get("received_at")
    if rat is not None:
        if parse_utc_timestamp(rat) is None:
            errors.append(f"envelope received_at must be ISO 8601 UTC timestamp: got {rat!r}")

    if not is_local:
        actor = envelope.get("authoritative_actor")
        if actor is None or not isinstance(actor, str) or not actor.strip():
            errors.append("envelope authoritative_actor must be a non-empty string")

    return errors


def validate(package: Any) -> list[str]:
    """Universal strict validator for review-request packages and envelopes.

    Returns a list of human-readable errors; empty list means valid.
    Never raises uncaught TypeError, AttributeError, or other exceptions on arbitrary JSON structures.
    """
    if not isinstance(package, dict):
        return ["package must be a JSON object"]

    # Dispatch based on kind / schema / envelope_kind
    if "envelope_kind" in package and package.get("envelope_kind") in VALID_ENVELOPE_KINDS and "package" in package:
        return validate_envelope(package)

    if package.get("kind") == SCHEMA_V2:
        return validate_package_v2(package)

    schema_val = package.get("schema")
    if schema_val == SCHEMA_V1:
        return validate_package_v1(package)

    if "kind" in package:
        # User specified an unknown kind or invalid version
        return validate_package_v2(package)

    # Default to v1 validation for packages specifying schema or missing schema
    return validate_package_v1(package)


def is_valid(package: Any) -> bool:
    """Return True if package is conformant with zero errors."""
    return not validate(package)


# ============================================================================
# Canonicalization and Identity Utilities
# ============================================================================

def _normalize_obj_for_canonicalization(obj: Any) -> Any:
    """Recursively normalize string values to Unicode NFC and reject floats."""
    if isinstance(obj, str):
        return unicodedata.normalize("NFC", obj)
    if isinstance(obj, float):
        raise TypeError("floating-point numbers are not permitted in autodocs-canonical-json-nfc-lf@v1")
    if isinstance(obj, dict):
        return {
            unicodedata.normalize("NFC", k): _normalize_obj_for_canonicalization(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_normalize_obj_for_canonicalization(x) for x in obj]
    return obj


def canonical_json_bytes(obj: Any) -> bytes:
    """Serialize object according to profile 'autodocs-canonical-json-nfc-lf@v1'.

    Rules:
      - UTF-8, no BOM
      - NFC-normalized strings
      - Sorted keys
      - Compact separators (',', ':')
      - Array element order preserved as authored
      - Exactly one trailing LF ('\\n') terminator
    """
    norm = _normalize_obj_for_canonicalization(obj)
    s = json.dumps(norm, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return (s + "\n").encode("utf-8")


def canonical_serialize(package: dict) -> str:
    """Deterministic string serialization for comparison / de-duplication."""
    norm = _normalize_obj_for_canonicalization(package)
    return json.dumps(norm, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def package_digest(obj: Any) -> str:
    """Compute SHA-256 hex digest over canonical package bytes."""
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def concern_key_preimage(package: dict) -> dict | None:
    """Extract canonical target/category/rationale concern projection for concern_key computation."""
    if not isinstance(package, dict):
        return None
    target = package.get("target_canonical_id")
    category = package.get("category")
    rationale = package.get("rationale")
    if not target or not category or not rationale:
        return None
    return {
        "category": category,
        "rationale": rationale,
        "target_canonical_id": target,
    }


def compute_concern_key(package: dict) -> str | None:
    """Compute concern_key: SHA-256 over canonical target/category/rationale projection."""
    preimage = concern_key_preimage(package)
    if preimage is None:
        return None
    return hashlib.sha256(canonical_json_bytes(preimage)).hexdigest()


def dedup_key(package: dict) -> tuple[str | None, str | None]:
    """De-duplication key per docs/pipeline/review-request-package-schema.md:
    (target_canonical_id, target_version_id) -- NOT request_id."""
    if not isinstance(package, dict):
        return (None, None)
    return (package.get("target_canonical_id"), package.get("target_version_id"))


def is_stale(package: dict, current_content_hash: str, current_version_id: str | None) -> bool:
    """Hard-stale only if BOTH content hash and version id mismatch
    (docs/pipeline/review-request-package-schema.md, Staleness rule)."""
    if not isinstance(package, dict):
        return False
    hash_mismatch = package.get("target_content_hash") != current_content_hash
    target_vid = package.get("target_version_id")
    version_mismatch = (
        target_vid is not None
        and target_vid != current_version_id
    )
    return hash_mismatch and version_mismatch
