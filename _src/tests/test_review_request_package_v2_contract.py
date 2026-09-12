# pyright: basic

import copy
import datetime as dt
import hashlib
import ipaddress
import json
import re
import unicodedata
import unittest
import urllib.parse
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "review_request_v2"
SCHEMA_PATH = ROOT / "docs" / "pipeline" / "review-request-package-v2.schema.json"

UUID_V7_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
UTC_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z$")
SHA_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
FORBIDDEN_FIELDS = {
    "trust", "verified", "verification_result", "authoritative_actor",
    "received_at", "server_timestamp", "receipt", "receipt_url",
    "repository", "installation_id", "delivery_id", "issue_id",
    "issue_number", "queue", "status", "outcome", "decided_by",
    "claimed_by", "writer", "route", "authorization", "access_token",
    "refresh_token", "token", "password", "secret", "private_key",
    "api_key", "credential", "credential_handle", "cookie", "session",
    "session_id", "ip", "ip_address", "fingerprint", "user_agent",
    "local_path", "filesystem_path", "signature", "signature_header",
    "transport",
}
PACKAGE_KEYS = {
    "schema", "client", "event_id", "created_at", "concern_key", "target",
    "category", "rationale", "evidence_refs", "actor_claim",
}
TARGET_KEYS = {
    "binding", "canonical_id", "version_id", "content_sha256",
    "status_snapshot", "source_url",
}
CATEGORIES = {
    "factual-accuracy", "outdated-source", "missing-context",
    "ai-hallucination-suspected", "other",
}
STATUSES = {
    "valid/auto-approved", "valid/corrected", "valid/ai-decided",
    "valid/curator-decided",
}


def duplicate_rejecting_loads(raw: str):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


def canonical_bytes(value, *, require_nfc=True) -> bytes:
    def check(node):
        if isinstance(node, float):
            raise TypeError("floats are not canonical contract values")
        if require_nfc and isinstance(node, str) and unicodedata.normalize("NFC", node) != node:
            raise ValueError("non-NFC string")
        if isinstance(node, dict):
            for key, child in node.items():
                if not isinstance(key, str) or unicodedata.normalize("NFC", key) != key:
                    raise ValueError("noncanonical key")
                check(child)
        elif isinstance(node, list):
            for child in node:
                check(child)
    check(value)
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256(value) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_canonical(name):
    raw = (FIXTURES / name).read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8")
    value = duplicate_rejecting_loads(text)
    require_nfc = name != "invalid-cases.json"
    assert raw == canonical_bytes(value, require_nfc=require_nfc), name
    return value


def package_from_fixture(value):
    if value.get("schema") == "review-request-package@v2":
        return value
    return value["package"]


def concern_projection(package):
    target = package["target"]
    return {
        "schema": "review-request-concern@v1",
        "target": {
            "binding": target["binding"],
            "canonical_id": target["canonical_id"],
            "version_id": target["version_id"],
            "content_sha256": target["content_sha256"],
        },
        "category": package["category"],
        "rationale": package["rationale"],
    }


def set_path(value, path, replacement):
    parts = path.split(".")
    node = value
    for part in parts[:-1]:
        node = node[int(part)] if isinstance(node, list) else node.setdefault(part, {})
    final = parts[-1]
    if isinstance(node, list):
        node[int(final)] = replacement
    else:
        node[final] = replacement


def delete_path(value, path):
    parts = path.split(".")
    node = value
    for part in parts[:-1]:
        node = node[int(part)] if isinstance(node, list) else node[part]
    final = parts[-1]
    if isinstance(node, list):
        del node[int(final)]
    else:
        del node[final]


def validate_url(value):
    codes = set()
    if not isinstance(value, str):
        return {"url.type"}
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != "https":
        codes.add("url.scheme")
        return codes
    if parsed.username is not None or parsed.password is not None:
        codes.add("url.userinfo")
    host = parsed.hostname or ""
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and (
        address.is_private or address.is_loopback or address.is_link_local
        or address.is_multicast or address.is_unspecified
    ):
        codes.add("url.private-target")
    if host.lower() == "localhost" or host.lower().endswith((".local", ".internal")):
        codes.add("url.private-target")
    return codes


def validate_text(value):
    codes = set()
    if not isinstance(value, str):
        return {"text.type"}
    if unicodedata.normalize("NFC", value) != value:
        codes.add("text.non-nfc")
    if any((ord(ch) < 32 and ch not in "\t\n") or 127 <= ord(ch) <= 159 for ch in value):
        codes.add("text.control")
    return codes


def recursive_forbidden(value):
    found = set()
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower().replace("-", "_")
            if normalized in FORBIDDEN_FIELDS:
                found.add(normalized)
            found |= recursive_forbidden(child)
    elif isinstance(value, list):
        for child in value:
            found |= recursive_forbidden(child)
    return found


def validate_package(package):
    codes = set()
    if not isinstance(package, dict):
        return {"package.type"}
    schema = package.get("schema")
    if schema != "review-request-package@v2":
        if isinstance(schema, str) and schema.startswith("review-request-package@"):
            codes.add("schema.unsupported-major")
        else:
            codes.add("schema.invalid")
    unknown = set(package) - PACKAGE_KEYS
    if unknown:
        if recursive_forbidden({key: package[key] for key in unknown}):
            codes.add("package.reserved-field")
        else:
            codes.add("package.additional-property")
    if recursive_forbidden({key: value for key, value in package.items() if key not in {"target"}}):
        codes.add("package.reserved-field")

    client = package.get("client")
    client_version = client.get("version") if isinstance(client, dict) else None
    if not isinstance(client_version, str):
        codes.add("client.version.type")
    elif not SEMVER_RE.fullmatch(client_version):
        codes.add("client.version.format")

    event = package.get("event_id")
    parsed_uuid = None
    if not isinstance(event, str):
        codes.add("event_id.type")
    else:
        try:
            parsed_uuid = uuid.UUID(event)
            if parsed_uuid.version != 7:
                codes.add("event_id.version")
            if parsed_uuid.variant != uuid.RFC_4122:
                codes.add("event_id.variant")
            if event != str(parsed_uuid) or not UUID_V7_RE.fullmatch(event):
                codes.add("event_id.noncanonical")
        except (ValueError, AttributeError):
            codes.add("event_id.format")

    created = package.get("created_at")
    if not isinstance(created, str) or not UTC_RE.fullmatch(created):
        codes.add("created_at.utc-format")
    elif parsed_uuid is not None and parsed_uuid.version == 7:
        created_ms = int(dt.datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
        event_ms = parsed_uuid.int >> 80
        if abs(created_ms - event_ms) > 300_000:
            codes.add("event_id.timestamp-mismatch")

    rationale = package.get("rationale")
    codes |= validate_text(rationale)
    if isinstance(rationale, str) and len(rationale) > 4000:
        codes.add("rationale.max-length")

    if package.get("category") not in CATEGORIES:
        codes.add("category.invalid")

    target = package.get("target")
    if not isinstance(target, dict):
        codes.add("target.type")
    else:
        if set(target) != TARGET_KEYS:
            codes.add("target.fields")
        content_sha = target.get("content_sha256")
        if not isinstance(content_sha, str) or not SHA_RE.fullmatch(content_sha):
            codes.add("target.content_sha256.format")
        binding = target.get("binding")
        version_id = target.get("version_id")
        canonical_id = target.get("canonical_id")
        if binding == "versioned":
            if not isinstance(version_id, str):
                codes.add("target.version.required")
            else:
                prefix = version_id.split("@rel:", 1)[0]
                if prefix != canonical_id:
                    codes.add("target.version.canonical-mismatch")
                if isinstance(content_sha, str) and SHA_RE.fullmatch(content_sha):
                    hash8 = version_id.rsplit("#", 1)[-1] if "#" in version_id else ""
                    if hash8 != content_sha[len("sha256:"):len("sha256:") + 8]:
                        codes.add("target.version.hash-prefix-mismatch")
        elif binding == "legacy-hash-only":
            if version_id is not None:
                codes.add("target.version.forbidden")
        else:
            codes.add("target.binding")
        if target.get("status_snapshot") not in STATUSES:
            codes.add("target.status")
        codes |= validate_url(target.get("source_url"))

    refs = package.get("evidence_refs")
    if not isinstance(refs, list):
        codes.add("evidence_refs.type")
    else:
        if len(refs) > 3:
            codes.add("evidence_refs.max-items")
        kinds = [ref.get("kind") for ref in refs if isinstance(ref, dict)]
        if len(kinds) != len(set(kinds)):
            codes.add("evidence_refs.duplicate-kind")
        for index, ref in enumerate(refs):
            if not isinstance(ref, dict):
                codes.add(f"evidence_refs[{index}].type")
                continue
            if ref.get("kind") not in {"url", "citation", "note"}:
                codes.add(f"evidence_refs[{index}].kind")
            if ref.get("kind") == "url":
                codes |= validate_url(ref.get("value"))
            else:
                codes |= validate_text(ref.get("value"))

    actor = package.get("actor_claim")
    if not isinstance(actor, dict) or actor.get("kind") not in {"anonymous", "self-declared"}:
        codes.add("actor_claim.invalid")

    try:
        expected_concern = sha256(concern_projection(package))
        if package.get("concern_key") != expected_concern:
            codes.add("concern_key.mismatch")
    except (KeyError, TypeError, ValueError):
        codes.add("concern_key.unavailable")
    return codes


def stable_binding(envelope):
    return {
        "transport": "github-issue",
        "repository_id": envelope["repository"]["id"],
        "installation_id": envelope["installation_id"],
        "issue_id": envelope["issue"]["id"],
        "author_id": envelope["issue"]["author_id"],
        "issue_body_sha256": envelope["package_binding"]["issue_body_sha256"],
        "package_sha256": envelope["package_sha256"],
    }


def validate_envelope(envelope):
    codes = set()
    if not isinstance(envelope, dict):
        return {"envelope.type"}
    if "verified" in envelope:
        codes.add("envelope.untrusted-field")
    package = envelope.get("package")
    codes |= validate_package(package)
    if isinstance(package, dict):
        try:
            if envelope.get("package_sha256") != sha256(package):
                codes.add("package.digest-mismatch")
        except (TypeError, ValueError):
            codes.add("package.noncanonical")
    if envelope.get("schema") == "review-request-envelope@v1":
        binding = envelope.get("package_binding")
        if (
            isinstance(binding, dict)
            and binding.get("method") == "github-issue-form-v1"
            and binding.get("normalization_profile") != "github-issue-form-review-request@v1"
        ):
            codes.add("package_binding.normalization-required")
        try:
            if envelope.get("stable_binding_sha256") != sha256(stable_binding(envelope)):
                codes.add("stable_binding.digest-mismatch")
        except (KeyError, TypeError, ValueError):
            codes.add("stable_binding.unavailable")
    elif envelope.get("schema") == "review-request-local-envelope@v1":
        source = envelope.get("source")
        if isinstance(source, dict):
            if set(source) - {"kind", "media_type", "source_bytes_sha256", "source_size_bytes"}:
                codes.add("source.additional-property")
            if isinstance(package, dict):
                try:
                    if source.get("source_bytes_sha256") != sha256(package):
                        codes.add("source.digest-mismatch")
                    if source.get("source_size_bytes") != len(canonical_bytes(package)):
                        codes.add("source.size-mismatch")
                except (TypeError, ValueError):
                    codes.add("source.package-noncanonical")
    else:
        codes.add("envelope.schema")
    return codes


class ReviewRequestPackageV2ContractTests(unittest.TestCase):
    def test_all_fixture_json_is_duplicate_free_canonical_utf8_with_one_lf(self):
        for path in sorted(FIXTURES.glob("*.json")):
            with self.subTest(path=path.name):
                raw = path.read_bytes()
                self.assertTrue(raw.endswith(b"\n"))
                self.assertFalse(raw.endswith(b"\n\n"))
                value = duplicate_rejecting_loads(raw.decode("utf-8"))
                require_nfc = path.name != "invalid-cases.json"
                self.assertEqual(raw, canonical_bytes(value, require_nfc=require_nfc))

    def test_formal_schema_is_draft_2020_12_and_closes_every_concrete_object(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["$ref"], "#/$defs/clientPackage")
        required = {"clientPackage", "trustedEnvelope", "localEnvelope", "targetVersioned", "targetLegacyHashOnly"}
        self.assertTrue(required <= set(schema["$defs"]))

        def inspect(node, path="$"):
            if isinstance(node, dict):
                if node.get("type") == "object":
                    self.assertIs(node.get("additionalProperties"), False, path)
                for key, value in node.items():
                    inspect(value, f"{path}/{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    inspect(value, f"{path}/{index}")
        inspect(schema)

    def test_three_positive_envelopes_and_packages_are_semantically_consistent(self):
        for name in ("valid-github.json", "valid-json-export.json", "valid-nojs-normalized.json"):
            with self.subTest(name=name):
                envelope = load_canonical(name)
                self.assertEqual(validate_envelope(envelope), set())
                self.assertLessEqual(len(canonical_bytes(envelope["package"])), 32768)

    def test_rfc_9562_uuid7_appendix_vector(self):
        vectors = load_canonical("canonical-vectors.json")
        vector = vectors["uuid7"]
        value = uuid.UUID(vector["value"])
        self.assertEqual(value.version, 7)
        self.assertEqual(value.variant, uuid.RFC_4122)
        self.assertEqual(value.int >> 80, vector["unix_ms"])
        observed = dt.datetime.fromtimestamp(vector["unix_ms"] / 1000, tz=dt.timezone.utc)
        self.assertEqual(observed.strftime("%Y-%m-%dT%H:%M:%S.%f")[:23] + "Z", vector["created_at"])

    def test_canonical_vectors_reproduce_package_concern_and_envelope_bytes(self):
        vectors = load_canonical("canonical-vectors.json")
        for vector in vectors["packages"]:
            envelope = load_canonical(vector["fixture"])
            package = package_from_fixture(envelope)
            self.assertEqual(canonical_bytes(package).decode(), vector["canonical_package"])
            self.assertEqual(len(canonical_bytes(package)), vector["size_bytes"])
            self.assertEqual(sha256(package), vector["sha256"])
            self.assertEqual(canonical_bytes(concern_projection(package)).decode(), vector["concern_preimage"])
            self.assertEqual(sha256(concern_projection(package)), vector["concern_key"])
        for vector in vectors["envelopes"]:
            envelope = load_canonical(vector["fixture"])
            self.assertEqual(canonical_bytes(envelope).decode(), vector["canonical_envelope"])
            self.assertEqual(len(canonical_bytes(envelope)), vector["size_bytes"])
            self.assertEqual(sha256(envelope), vector["sha256"])

    def test_invalid_case_matrix_reaches_each_declared_rule(self):
        matrix = load_canonical("invalid-cases.json")
        self.assertEqual(len(matrix["cases"]), 28)
        for case in matrix["cases"]:
            with self.subTest(case=case["id"]):
                if case["op"] == "raw":
                    if case["id"] == "RRP2-PARSE-001":
                        with self.assertRaisesRegex(ValueError, "duplicate key"):
                            duplicate_rejecting_loads(case["raw"])
                        observed = {"parse.duplicate-key"}
                    else:
                        parsed = duplicate_rejecting_loads(case["raw"])
                        observed = {"parse.noncanonical"} if case["raw"].encode() != canonical_bytes(parsed) else set()
                else:
                    value = copy.deepcopy(load_canonical(case["base"]))
                    if case["op"] == "set":
                        set_path(value, case["path"], case["value"])
                    else:
                        delete_path(value, case["path"])
                    observed = validate_envelope(value)
                self.assertTrue(set(case["expected"]) <= observed, (case["id"], case["expected"], sorted(observed)))

    def test_client_packages_cannot_claim_transport_or_authority(self):
        for name in ("valid-github.json", "valid-json-export.json", "valid-nojs-normalized.json"):
            package = package_from_fixture(load_canonical(name))
            forbidden = recursive_forbidden(package)
            self.assertEqual(forbidden, set(), (name, forbidden))
            rendered = canonical_bytes(package).decode().lower()
            for token in ("github_authenticated", "verified", "decided_by", "receipt_url", "access_token"):
                self.assertNotIn(token, rendered)

    def test_same_concern_excludes_actor_evidence_event_time_and_source(self):
        package = package_from_fixture(load_canonical("valid-github.json"))
        changed = copy.deepcopy(package)
        changed["event_id"] = package_from_fixture(load_canonical("valid-nojs-normalized.json"))["event_id"]
        changed["created_at"] = "2026-08-19T06:55:00.000Z"
        changed["actor_claim"] = {"kind": "anonymous"}
        changed["evidence_refs"] = [{"kind": "note", "value": "Supplementary evidence."}]
        changed["target"]["source_url"] = "https://example.org/de/modules/tsync.html#SWS_TSYNC_00123"
        self.assertEqual(sha256(concern_projection(package)), sha256(concern_projection(changed)))
        self.assertNotEqual(sha256(package), sha256(changed))

    def test_compatibility_matrix_is_explicit_and_sources_exist(self):
        matrix = load_canonical("compatibility-cases.json")
        self.assertEqual(len(matrix["cases"]), 5)
        dispositions = {case["expected"] for case in matrix["cases"]}
        self.assertIn("quarantine-sensitive", dispositions)
        self.assertIn("quarantine-legacy-semantic-ambiguous", dispositions)
        for case in matrix["cases"]:
            if "source" in case:
                self.assertTrue((ROOT / case["source"]).is_file(), case["source"])

    def test_manifest_counts_and_profiles_are_truthful(self):
        manifest = load_canonical("manifest.json")
        self.assertEqual(manifest["approval_state"], "candidate-not-approved")
        self.assertEqual(manifest["enabled_github_profiles"], [])
        self.assertEqual(manifest["invalid"]["count"], 28)
        self.assertEqual(manifest["compatibility"]["count"], 5)
        self.assertEqual(len(manifest["positive"]), 3)
        for entry in manifest["positive"]:
            self.assertTrue((FIXTURES / entry["file"]).is_file())

    def test_historical_v1_contract_and_fixtures_remain_separate(self):
        old_schema = ROOT / "docs" / "pipeline" / "review-request-package-schema.md"
        self.assertIn("V1 never passes v2 schema directly", old_schema.read_text(encoding="utf-8"))
        self.assertTrue((ROOT / "_src/tests/fixtures/review_request/valid_github_issue.json").is_file())
        self.assertTrue((ROOT / "_src/tools/review_request_package.py").is_file())


if __name__ == "__main__":
    unittest.main()
