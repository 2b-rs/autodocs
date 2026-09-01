#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_review_request_package.py -- Comprehensive tests for strict package/envelope validation.

Exercises:
  - Valid v1 and v2 review request packages
  - Baseline findings RRB-SCHEMA-001 (adversarial malformed types and reserved trust/server fields)
  - Baseline findings RRB-SCHEMA-002 (uncaught non-string request_id crashes)
  - Strict parsers: UUIDv7, Canonical IDs, Semver, UTC Timestamps, URLs
  - Server-owned and sensitive field prohibitions
  - Additional property rejection in closed schemas
  - Text safety: control characters, unsafe HTML/script injection
  - Relationship checks: target_version_id canonical prefix and embedded hash matching
  - Canonicalization profile (autodocs-canonical-json-nfc-lf@v1) against pinned vectors
  - Envelope validation (review-request-envelope@v1, review-request-local-envelope@v1)
  - Resilience against arbitrary untrusted JSON structures without raising uncaught exceptions
"""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import review_request_package as rrp  # noqa: E402
from version_id import content_hash8  # noqa: E402

FIXTURES_V1 = Path(__file__).resolve().parent / "fixtures" / "review_request"
FIXTURES_V2 = Path(__file__).resolve().parent / "fixtures" / "review_request_v2"


def load_v1(name: str) -> dict:
    return json.loads((FIXTURES_V1 / name).read_text(encoding="utf-8"))


def load_v2(name: str) -> dict:
    return json.loads((FIXTURES_V2 / name).read_text(encoding="utf-8"))


class ReviewRequestPackageTests(unittest.TestCase):
    """Core package tests for review-request-package@v1."""

    def test_valid_github_issue_package_has_no_errors(self):
        pkg = load_v1("valid_github_issue.json")
        errors = rrp.validate(pkg)
        self.assertEqual(errors, [])
        self.assertTrue(rrp.is_valid(pkg))

    def test_valid_json_export_package_has_no_errors(self):
        pkg = load_v1("valid_json_export.json")
        errors = rrp.validate(pkg)
        self.assertEqual(errors, [])
        self.assertTrue(rrp.is_valid(pkg))

    def test_invalid_package_reports_multiple_errors(self):
        pkg = load_v1("invalid_missing_fields.json")
        errors = rrp.validate(pkg)
        self.assertTrue(errors)
        self.assertTrue(any("unknown schema" in e for e in errors))
        self.assertTrue(any("rationale" in e for e in errors))
        self.assertTrue(any("request_id" in e for e in errors))
        self.assertFalse(rrp.is_valid(pkg))

    def test_new_request_id_matches_schema_pattern(self):
        rid = rrp.new_request_id()
        self.assertTrue(rid.startswith("review-request:"))
        self.assertIsNotNone(rrp._REQUEST_ID_RE.match(rid))
        uuid_part = rid.split(":", 1)[1]
        self.assertTrue(rrp.is_valid_uuid7(uuid_part))

    def test_dedup_key_ignores_request_id(self):
        a = load_v1("valid_github_issue.json")
        b = dict(a)
        b["request_id"] = rrp.new_request_id()
        self.assertEqual(rrp.dedup_key(a), rrp.dedup_key(b))

    def test_canonical_serialize_is_deterministic_regardless_of_key_order(self):
        pkg = load_v1("valid_github_issue.json")
        reordered = dict(reversed(list(pkg.items())))
        self.assertEqual(rrp.canonical_serialize(pkg), rrp.canonical_serialize(reordered))

    def test_content_hash8_is_deterministic(self):
        content = "Global time as a service for applications..."
        h1 = content_hash8(content)
        h2 = content_hash8(content)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 8)

    def test_is_stale_requires_both_hash_and_version_mismatch(self):
        pkg = load_v1("valid_github_issue.json")
        self.assertFalse(rrp.is_stale(pkg, pkg["target_content_hash"], pkg["target_version_id"]))
        self.assertFalse(rrp.is_stale(pkg, "deadbeef", pkg["target_version_id"]))
        self.assertTrue(rrp.is_stale(
            pkg, "deadbeef",
            "AUTOSAR/AP/record/tsync-user-guide@rel:R25-11#deadbeef"))

    def test_json_export_null_version_id_is_valid(self):
        pkg = load_v1("valid_json_export.json")
        self.assertIsNone(pkg["target_version_id"])
        self.assertEqual(rrp.validate(pkg), [])


class HistoricalDefectReproductionTests(unittest.TestCase):
    """Explicit tests for RRB-SCHEMA-001 and RRB-SCHEMA-002."""

    def test_rrb_schema_001_adversarial_probe_rejected_with_stable_diagnostics(self):
        pkg = load_v1("valid_json_export.json")
        pkg.update({
            "client_schema_version": [1, 0, 0],
            "target_status_snapshot": {"server_owned": True},
            "source_url": {"scheme": "javascript"},
            "rationale": ["not", "a", "string"],
            "actor_claim": {"display_name": 17, "identity_kind": "self_declared"},
            "evidence_refs": [{"kind": 7, "value": {"nested": True}}],
            "trust": {"verified": True, "authoritative_actor": "caller-authored"},
            "received_at": "2026-08-15T00:00:00Z",
            "server_timestamp": "2026-08-15T00:00:00Z",
            "session_id": "reserved-client-value",
        })
        errors = rrp.validate(pkg)
        self.assertTrue(len(errors) >= 7, f"expected >=7 errors, got {len(errors)}: {errors}")
        self.assertTrue(any("client_schema_version" in e for e in errors))
        self.assertTrue(any("target_status_snapshot" in e for e in errors))
        self.assertTrue(any("source_url" in e for e in errors))
        self.assertTrue(any("rationale" in e for e in errors))
        self.assertTrue(any("actor_claim.display_name" in e for e in errors))
        self.assertTrue(any("evidence_refs[0]" in e for e in errors))
        self.assertTrue(any("trust" in e for e in errors))
        self.assertTrue(any("received_at" in e for e in errors))
        self.assertTrue(any("server_timestamp" in e for e in errors))
        self.assertTrue(any("session_id" in e for e in errors))

    def test_rrb_schema_002_integer_request_id_does_not_crash(self):
        pkg = load_v1("valid_json_export.json")
        pkg["request_id"] = 7
        try:
            errors = rrp.validate(pkg)
        except Exception as exc:
            self.fail(f"validate raised unexpected exception on integer request_id: {exc}")
        self.assertTrue(any("request_id must be a string" in e for e in errors))
        self.assertFalse(rrp.is_valid(pkg))

    def test_untrusted_non_dict_inputs_never_raise(self):
        untrusted_values = [
            None,
            42,
            3.14,
            "not-a-dict",
            True,
            False,
            [],
            [1, 2, 3],
            {"schema": 123},
        ]
        for val in untrusted_values:
            try:
                errors = rrp.validate(val)
                self.assertIsInstance(errors, list)
                self.assertTrue(errors)
                self.assertFalse(rrp.is_valid(val))
            except Exception as exc:
                self.fail(f"validate raised {type(exc).__name__} on input {val!r}: {exc}")


class ServerOwnedAndForbiddenFieldsTests(unittest.TestCase):
    """Ensures server-owned, sensitive, credential, and fingerprint fields are prohibited."""

    def test_forbidden_fields_at_root_level(self):
        forbidden = [
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
            "token",
            "password",
            "secret",
            "api_key",
        ]
        base_v1 = load_v1("valid_github_issue.json")
        for field in forbidden:
            pkg = dict(base_v1)
            pkg[field] = "malicious_value"
            errors = rrp.validate(pkg)
            self.assertTrue(
                any(field in e and ("forbidden" in e or "additional property" in e) for e in errors),
                f"forbidden field '{field}' was not rejected in v1: {errors}",
            )

        base_v2 = load_v2("valid-github.json")
        for field in forbidden:
            pkg = dict(base_v2)
            pkg[field] = "malicious_value"
            errors = rrp.validate(pkg)
            self.assertTrue(
                any(field in e for e in errors),
                f"forbidden field '{field}' was not rejected in v2: {errors}",
            )


class RobustParsersTests(unittest.TestCase):
    """Exercises low-level parsers: UUIDv7, Canonical IDs, Semver, UTC Timestamps, URLs."""

    def test_parse_uuid7_valid_and_invalid(self):
        # Appendix A vector
        rfc_uuid = "017f22e2-79b0-7cc3-98c4-dc0c0c07398f"
        parsed = rrp.parse_uuid7(rfc_uuid)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["version"], 7)
        self.assertEqual(parsed["variant"], "RFC 9562")
        self.assertEqual(parsed["unix_ms"], 1645557742000)

        # Freshly minted UUID
        fresh = rrp.uuid7()
        self.assertTrue(rrp.is_valid_uuid7(fresh))

        # Invalid UUIDs
        self.assertIsNone(rrp.parse_uuid7("not-a-uuid"))
        self.assertIsNone(rrp.parse_uuid7(12345))
        self.assertIsNone(rrp.parse_uuid7(None))
        # UUIDv4 (version nibble is 4, not 7)
        self.assertIsNone(rrp.parse_uuid7("c9a646d3-9c61-4cc9-bc8d-9b507e0561a0"))
        # Invalid variant (nibble '0' instead of 8, 9, a, b)
        self.assertIsNone(rrp.parse_uuid7("017f22e2-79b0-7cc3-08c4-dc0c0c07398f"))

    def test_parse_canonical_id_valid_and_invalid(self):
        self.assertIsNotNone(rrp.parse_canonical_id("AUTOSAR/AP/record/tsync-user-guide"))
        self.assertIsNotNone(rrp.parse_canonical_id("class:ara::exec::ExecutionClient"))
        self.assertIsNotNone(rrp.parse_canonical_id("namespace:ara::com"))
        self.assertIsNotNone(rrp.parse_canonical_id("service:ara::sm::StateManagement"))

        self.assertIsNone(rrp.parse_canonical_id(""))
        self.assertIsNone(rrp.parse_canonical_id(123))
        self.assertIsNone(rrp.parse_canonical_id(None))
        self.assertIsNone(rrp.parse_canonical_id("invalid with spaces"))
        self.assertIsNone(rrp.parse_canonical_id("invalid\x00with_null"))

    def test_parse_semver(self):
        v1 = rrp.parse_semver("1.0.0")
        self.assertEqual(v1, {"major": 1, "minor": 0, "patch": 0, "prerelease": None, "build": None})
        v2 = rrp.parse_semver("2.1.3-beta.1+exp.sha.5114f85")
        self.assertEqual(v2["major"], 2)
        self.assertEqual(v2["minor"], 1)
        self.assertEqual(v2["patch"], 3)
        self.assertEqual(v2["prerelease"], "beta.1")
        self.assertEqual(v2["build"], "exp.sha.5114f85")

        self.assertIsNone(rrp.parse_semver("not_semver"))
        self.assertIsNone(rrp.parse_semver(100))
        self.assertIsNone(rrp.parse_semver(None))

    def test_parse_utc_timestamp(self):
        dt = rrp.parse_utc_timestamp("2026-08-15T07:40:00Z")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 8)
        self.assertEqual(dt.day, 15)
        self.assertEqual(dt.hour, 7)
        self.assertEqual(dt.minute, 40)

        # Microseconds and +00:00
        dt2 = rrp.parse_utc_timestamp("2026-08-15T07:40:00.123456+00:00")
        self.assertIsNotNone(dt2)

        # Invalid calendar dates
        self.assertIsNone(rrp.parse_utc_timestamp("2026-02-30T12:00:00Z"))
        self.assertIsNone(rrp.parse_utc_timestamp("2026-13-01T12:00:00Z"))
        self.assertIsNone(rrp.parse_utc_timestamp("2026-08-15T25:00:00Z"))
        # Non-UTC timezone (rejected by strict UTC matcher)
        self.assertIsNone(rrp.parse_utc_timestamp("2026-08-15T07:40:00+02:00"))
        self.assertIsNone(rrp.parse_utc_timestamp(123456789))

    def test_url_validation_and_security_rules(self):
        # Valid URLs
        self.assertEqual(rrp.validate_url_field("https://example.org/spec/tsync.html", "source_url"), [])
        self.assertEqual(rrp.validate_url_field("http://docs.autosar.io/manual", "source_url"), [])
        self.assertEqual(rrp.validate_url_field("/relative/path/page.html", "source_url", allow_relative=True), [])

        # Disallowed schemes
        self.assertTrue(rrp.validate_url_field("javascript:alert(1)", "source_url"))
        self.assertTrue(rrp.validate_url_field("data:text/html,<script>", "source_url"))
        self.assertTrue(rrp.validate_url_field("file:///etc/passwd", "source_url"))
        self.assertTrue(rrp.validate_url_field("ftp://example.com/file", "source_url"))

        # Embedded credentials
        self.assertTrue(any("credentials" in e for e in rrp.validate_url_field("https://user:pass@example.com", "source_url")))

        # Private / loopback targets
        self.assertTrue(any("localhost" in e for e in rrp.validate_url_field("http://localhost:8080/flag", "source_url")))
        self.assertTrue(any("private" in e or "loopback" in e for e in rrp.validate_url_field("http://127.0.0.1/admin", "source_url")))
        self.assertTrue(any("private" in e for e in rrp.validate_url_field("http://10.0.0.1/intake", "source_url")))
        self.assertTrue(any("private" in e for e in rrp.validate_url_field("http://192.168.1.100/intake", "source_url")))


class TextSafetyAndInjectionTests(unittest.TestCase):
    """Tests for control characters, unsafe script/HTML, and length limits."""

    def test_control_characters_rejected(self):
        pkg = load_v1("valid_github_issue.json")
        pkg["rationale"] = "Valid text with a forbidden null byte \x00 in the middle."
        errors = rrp.validate(pkg)
        self.assertTrue(any("forbidden control character" in e for e in errors))

        pkg2 = load_v1("valid_github_issue.json")
        pkg2["actor_claim"]["display_name"] = "Alice\nBob"
        errors2 = rrp.validate(pkg2)
        self.assertTrue(any("actor_claim.display_name" in e for e in errors2))

    def test_unsafe_html_script_rejected(self):
        pkg = load_v1("valid_github_issue.json")
        pkg["rationale"] = "Suspected issue <script>window.location='https://attacker.org'</script>"
        errors = rrp.validate(pkg)
        self.assertTrue(any("disallowed HTML tags or script patterns" in e for e in errors))

        pkg2 = load_v2("valid-github.json")
        pkg2["rationale"] = "Check this out <iframe src='evil.com'></iframe>"
        errors2 = rrp.validate(pkg2)
        self.assertTrue(any("disallowed HTML tags or script patterns" in e for e in errors2))

    def test_length_limits(self):
        pkg = load_v1("valid_github_issue.json")
        pkg["rationale"] = "A" * 4001
        errors = rrp.validate(pkg)
        self.assertTrue(any("rationale exceeds maximum length" in e for e in errors))

        pkg["rationale"] = "Valid rationale"
        pkg["target_status_snapshot"] = "S" * 101
        errors2 = rrp.validate(pkg)
        self.assertTrue(any("target_status_snapshot exceeds maximum length" in e for e in errors2))


class RelationshipValidationTests(unittest.TestCase):
    """Tests cross-field relationship consistency."""

    def test_version_id_canonical_prefix_mismatch(self):
        pkg = load_v1("valid_github_issue.json")
        pkg["target_canonical_id"] = "AUTOSAR/AP/record/tsync-user-guide"
        pkg["target_version_id"] = "AUTOSAR/AP/record/different-guide@rel:R25-11#3f9a21bc"
        errors = rrp.validate(pkg)
        self.assertTrue(any("target_version_id canonical prefix" in e for e in errors))

    def test_version_id_hash_mismatch(self):
        pkg = load_v1("valid_github_issue.json")
        pkg["target_content_hash"] = "3f9a21bc"
        pkg["target_version_id"] = "AUTOSAR/AP/record/tsync-user-guide@rel:R25-11#deadbeef"
        errors = rrp.validate(pkg)
        self.assertTrue(any("target_version_id content hash" in e for e in errors))


class CanonicalizationAndVectorsTests(unittest.TestCase):
    """Tests canonical serialization matching pinned vectors and NFC normalization."""

    def test_pinned_package_v2_vector(self):
        vectors = load_v2("canonical-vectors.json")
        pkg_vec = vectors["vectors"][0]
        canonical = rrp.canonical_json_bytes(pkg_vec["object"])
        self.assertEqual(len(canonical), pkg_vec["canonical_byte_length"])
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), pkg_vec["package_sha256"])

    def test_pinned_concern_key_preimage_vector(self):
        vectors = load_v2("canonical-vectors.json")
        concern_vec = vectors["vectors"][1]
        self.assertNotIn("event_id", concern_vec["object"])
        canonical = rrp.canonical_json_bytes(concern_vec["object"])
        self.assertEqual(len(canonical), concern_vec["canonical_byte_length"])
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), concern_vec["concern_key_sha256"])

    def test_compute_concern_key_matches_preimage(self):
        pkg = load_v2("valid-github.json")
        ck = rrp.compute_concern_key(pkg)
        self.assertEqual(ck, "fe305d2299e75649199c024d37803ae793825947d7131910130e132891787230")

    def test_unicode_nfc_normalization_in_canonicalization(self):
        # 'e' + combining acute accent (U+0301) vs precomposed 'é' (U+00E9)
        decomposed = {"rationale": "Resum\u0065\u0301"}
        precomposed = {"rationale": "Resum\u00e9"}
        self.assertEqual(rrp.canonical_json_bytes(decomposed), rrp.canonical_json_bytes(precomposed))
        self.assertEqual(rrp.package_digest(decomposed), rrp.package_digest(precomposed))

    def test_array_order_is_strictly_preserved(self):
        a = {"items": ["z", "a", "m"]}
        b = {"items": ["a", "m", "z"]}
        self.assertNotEqual(rrp.canonical_json_bytes(a), rrp.canonical_json_bytes(b))

    def test_float_rejection_in_canonicalization(self):
        with self.assertRaises(TypeError):
            rrp.canonical_json_bytes({"price": 19.99})


class EnvelopeValidationTests(unittest.TestCase):
    """Tests for review-request envelopes."""

    def test_valid_github_envelope(self):
        pkg = load_v2("valid-github.json")
        pkg_bytes = rrp.canonical_json_bytes(pkg)
        envelope = {
            "envelope_kind": "review-request-envelope@v1",
            "event_id": pkg["event_id"],
            "package": pkg,
            "package_sha256": hashlib.sha256(pkg_bytes).hexdigest(),
            "trust_profile": "github-webhook-sha256-v1",
            "authoritative_actor": "octocat",
            "repository": "autosar/docs",
            "issue_number": 42,
            "received_at": "2026-08-30T12:00:00Z",
        }
        self.assertEqual(rrp.validate(envelope), [])
        self.assertTrue(rrp.is_valid(envelope))

    def test_valid_local_envelope(self):
        pkg = load_v2("valid-nojs-normalized.json")
        pkg_bytes = rrp.canonical_json_bytes(pkg)
        envelope = {
            "envelope_kind": "review-request-local-envelope@v1",
            "event_id": pkg["event_id"],
            "package": pkg,
            "package_sha256": hashlib.sha256(pkg_bytes).hexdigest(),
            "trust_profile": "local-import-v1",
            "received_at": "2026-08-30T12:00:00Z",
        }
        self.assertEqual(rrp.validate(envelope), [])
        self.assertTrue(rrp.is_valid(envelope))

    def test_envelope_package_sha_mismatch(self):
        pkg = load_v2("valid-github.json")
        envelope = {
            "envelope_kind": "review-request-envelope@v1",
            "event_id": pkg["event_id"],
            "package": pkg,
            "package_sha256": "0" * 64,
            "trust_profile": "github-webhook-sha256-v1",
            "authoritative_actor": "octocat",
            "received_at": "2026-08-30T12:00:00Z",
        }
        errors = rrp.validate(envelope)
        self.assertTrue(any("package_sha256 mismatch" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
