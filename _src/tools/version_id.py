"""Cross-release ID naming schemes (Feature 0006-15).

Mints and parses the 5 ID families needed for cross-release traceability:
  - requirement version:  <canonical-id>@rel:<release>#<hash8>
  - curation decision:    curation:<uuid7>
  - evidence snippet:     evidence:<uuid7>
  - AI artifact/synthesis: artifact:<uuid7>
  - supersession edge:    supersedes:<old-version-id>-><new-version-id>

Pinned design choices (2026-08-13, closing the open items in 0006-15):
  - Content hash: SHA-256, truncated to the first 8 hex characters (hash8).
    Rationale: 8 hex chars = 32 bits, collision risk is negligible at the
    per-requirement-per-release scale this project operates at, and stays
    short enough to remain human-readable inside a canonical ID string.
  - UUIDv7: this Python's stdlib `uuid` module has no `uuid7()` (verified
    2026-08-13), so a minimal RFC 9562 compliant generator is implemented
    here: 48-bit millisecond Unix timestamp, 4-bit version (0b0111),
    2-bit variant (0b10), and 74 bits of randomness. This keeps decision/
    evidence/artifact IDs sortable-by-time across concurrent queue/
    browser/AI write paths (per 0006-06) without a central ID allocator.
"""
from __future__ import annotations
import hashlib
import os
import re
import time


def content_hash8(content: str) -> str:
    """SHA-256 of content, truncated to first 8 hex chars (pinned 0006-15)."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]


def uuid7() -> str:
    """Hand-rolled RFC 9562 UUIDv7: sortable-by-time, no stdlib uuid7 here."""
    unix_ms = int(time.time() * 1000) & 0xFFFFFFFFFFFF  # 48 bits
    rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF  # 12 random bits
    rand_b = int.from_bytes(os.urandom(8), "big") & 0x3FFFFFFFFFFFFFFF  # 62 random bits
    value = (unix_ms << 80) | (0x7 << 76) | (rand_a << 64) | (0b10 << 62) | rand_b
    hex_str = f"{value:032x}"
    return f"{hex_str[0:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"


def requirement_version_id(canonical_id: str, release: str, content: str) -> str:
    """<canonical-id>@rel:<release>#<hash8> -- one immutable snapshot per release."""
    return f"{canonical_id}@rel:{release}#{content_hash8(content)}"


_VERSION_RE = re.compile(r"^(?P<canonical_id>.+)@rel:(?P<release>[^#]+)#(?P<hash8>[0-9a-f]{8})$")


def parse_version_id(value: str) -> dict | None:
    m = _VERSION_RE.match(value)
    return m.groupdict() if m else None


def curation_id() -> str:
    return f"curation:{uuid7()}"


def evidence_id() -> str:
    return f"evidence:{uuid7()}"


def artifact_id() -> str:
    return f"artifact:{uuid7()}"


_PREFIXED_RE = re.compile(r"^(?P<prefix>curation|evidence|artifact):(?P<uuid>[0-9a-f-]{36})$")


def parse_prefixed_id(value: str) -> dict | None:
    m = _PREFIXED_RE.match(value)
    return m.groupdict() if m else None


def supersession_edge(old_version_id: str, new_version_id: str) -> str:
    return f"supersedes:{old_version_id}->{new_version_id}"


_SUPERSEDES_RE = re.compile(r"^supersedes:(?P<old>.+)->(?P<new>.+)$")


def parse_supersession_edge(value: str) -> dict | None:
    m = _SUPERSEDES_RE.match(value)
    return m.groupdict() if m else None
