from __future__ import annotations

import hashlib
import hmac
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import canonical_id as cid  # noqa: E402
import curation_flags as cf  # noqa: E402
import review_request_ingest as rri  # noqa: E402
import review_request_package as rrp  # noqa: E402
import version_id as vid_util  # noqa: E402
import version_store as vstore  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "review_request"


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ReviewRequestIngestTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._root = Path(self._tmpdir.name)

        # Queue redirection
        self._orig_queue = cf.QUEUE
        self._orig_open = cf.OPEN_DIR
        self._orig_claimed = cf.CLAIMED_DIR
        self._orig_done = cf.DONE_DIR
        cf.QUEUE = self._root / "curation-queue"
        cf.OPEN_DIR = cf.QUEUE / "open"
        cf.CLAIMED_DIR = cf.QUEUE / "claimed"
        cf.DONE_DIR = cf.QUEUE / "done"

        # Record / Version store redirection
        self._orig_records_root = rri.RECORDS_ROOT
        self._orig_versions_root = rri.VERSIONS_ROOT
        self._records_dir = self._root / "records"
        self._versions_dir = self._root / "versions"
        self._records_dir.mkdir(parents=True, exist_ok=True)
        self._versions_dir.mkdir(parents=True, exist_ok=True)
        rri.RECORDS_ROOT = self._records_dir
        rri.VERSIONS_ROOT = self._versions_dir

        # Reset global replay tracker
        rri.reset_replay_tracker()

        # Seed authoritative record for the standard fixture: AUTOSAR/AP/record/tsync-user-guide
        self._seed_record(
            canonical_id="AUTOSAR/AP/record/tsync-user-guide",
            release="R25-11",
            content_hash="3f9a21bc",
            status_state="valid/published",
            content="Standard TSync User Guide specification text.",
            source_url="https://example.org/en/modules/tsync.html#user-guide",
        )

    def tearDown(self):
        cf.QUEUE = self._orig_queue
        cf.OPEN_DIR = self._orig_open
        cf.CLAIMED_DIR = self._orig_claimed
        cf.DONE_DIR = self._orig_done
        rri.RECORDS_ROOT = self._orig_records_root
        rri.VERSIONS_ROOT = self._orig_versions_root
        rri.reset_replay_tracker()
        self._tmpdir.cleanup()

    def _seed_record(
        self,
        canonical_id: str,
        release: str = "R25-11",
        content_hash: str = "3f9a21bc",
        status_state: str = "valid/published",
        content: str = "Specification text",
        source_url: str | None = None,
    ) -> tuple[Path, str]:
        parsed = cid.parse_canonical_id(canonical_id)
        assert parsed is not None, f"invalid canonical_id: {canonical_id}"
        item_id = parsed["id"]
        project = parsed["project"]
        kind = parsed["kind"]

        version_id = f"{canonical_id}@rel:{release}#{content_hash}"

        # Write spec record
        rec_dir = self._records_dir / project / kind
        rec_dir.mkdir(parents=True, exist_ok=True)
        rec_file = rec_dir / f"{item_id}.json"
        rec_data = {
            "id": item_id,
            "canonical_id": canonical_id,
            "status": {"state": status_state, "campaign": "2026-08-test"},
            "version_id": version_id,
            "target_content_hash": content_hash,
            "source_url": source_url or f"https://example.org/{item_id}.html",
        }
        rec_file.write_text(json.dumps(rec_data, indent=2), encoding="utf-8")

        # Write version store entry
        ver_dir = self._versions_dir / project / kind
        ver_dir.mkdir(parents=True, exist_ok=True)
        ver_file = ver_dir / f"{item_id}.jsonl"
        ver_entry = {
            "version_id": version_id,
            "canonical_id": canonical_id,
            "release": release,
            "content": content,
            "meta": {},
            "recorded_at": "2026-08-15T00:00:00Z",
        }
        with ver_file.open("a", encoding="utf-8") as vf:
            vf.write(json.dumps(ver_entry) + "\n")

        return rec_file, version_id

    # -------------------------------------------------------------------------
    # Target Resolution & Staleness Tests
    # -------------------------------------------------------------------------

    def test_happy_path_github_issue_creates_open_flag(self):
        pkg = load("valid_github_issue.json")
        report = rri.ingest(pkg, apply=True, authoritative_actor="jdoe")
        self.assertEqual(report["outcome"], rri.IngestOutcome.OK)
        self.assertIsNotNone(report["path"])
        payload = json.loads(Path(report["path"]).read_text(encoding="utf-8"))
        self.assertEqual(payload["item_kind"], "review-request")
        self.assertEqual(payload["identity"], "github_authenticated")
        self.assertEqual(payload["decision_basis"]["authoritative_actor"], "jdoe")
        self.assertIsNotNone(report.get("target_token"))
        self.assertEqual(report["target_token"]["target_canonical_id"], pkg["target_canonical_id"])

    def test_happy_path_json_export_forces_self_declared(self):
        pkg = load("valid_json_export.json")
        # Update pkg to have target_version_id matching the versioned record
        pkg["target_version_id"] = "AUTOSAR/AP/record/tsync-user-guide@rel:R25-11#3f9a21bc"
        report = rri.ingest(pkg, apply=True)
        self.assertEqual(report["outcome"], rri.IngestOutcome.OK)
        payload = json.loads(Path(report["path"]).read_text(encoding="utf-8"))
        self.assertEqual(payload["identity"], "self_declared")
        self.assertTrue(any("self_declared" in w for w in report["warnings"]))

    def test_unknown_target_record_rejected_without_queue_write(self):
        pkg = load("valid_github_issue.json")
        pkg["target_canonical_id"] = "AUTOSAR/AP/record/unknown-nonexistent-element"
        pkg["target_version_id"] = "AUTOSAR/AP/record/unknown-nonexistent-element@rel:R25-11#3f9a21bc"
        report = rri.ingest(pkg, apply=True, authoritative_actor="jdoe")
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_UNKNOWN_TARGET)
        self.assertTrue(any("unknown target record" in e for e in report["errors"]))
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_ineligible_record_status_rejected(self):
        self._seed_record(
            canonical_id="AUTOSAR/AP/record/draft-element",
            status_state="invalid/draft",
        )
        pkg = load("valid_github_issue.json")
        pkg["target_canonical_id"] = "AUTOSAR/AP/record/draft-element"
        pkg["target_version_id"] = "AUTOSAR/AP/record/draft-element@rel:R25-11#3f9a21bc"
        report = rri.ingest(pkg, apply=True, authoritative_actor="jdoe")
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_INELIGIBLE_TARGET)
        self.assertTrue(any("ineligible" in e for e in report["errors"]))
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_null_version_on_versioned_record_rejected_proc_0033_02_03(self):
        pkg = load("valid_json_export.json")
        self.assertIsNone(pkg["target_version_id"])
        # The live record in setUp is versioned; null-version submission must be rejected
        report = rri.ingest(pkg, apply=True)
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_INELIGIBLE_TARGET)
        self.assertTrue(any("PROC-0033-02-03" in e for e in report["errors"]))
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_forged_caller_arguments_cannot_bypass_live_resolution(self):
        pkg = load("valid_github_issue.json")
        # Caller tries to pass forged live values that do not match the real store
        report = rri.ingest(
            pkg,
            apply=True,
            current_content_hash="forged99",
            current_version_id="AUTOSAR/AP/record/tsync-user-guide@rel:R99#forged99",
            authoritative_actor="jdoe",
        )
        # Ingestion succeeds based on the authoritative store lookup, and warns about caller override
        self.assertEqual(report["outcome"], rri.IngestOutcome.OK)
        self.assertTrue(any("overridden by authoritative" in w for w in report["warnings"]))
        # Target token reflects the true authoritative store state (3f9a21bc), not the forged argument
        self.assertEqual(report["target_token"]["target_content_hash"], "3f9a21bc")

    def test_omitted_caller_arguments_succeed_via_live_resolution(self):
        pkg = load("valid_github_issue.json")
        # Omit current_content_hash and current_version_id completely
        report = rri.ingest(pkg, apply=True, authoritative_actor="jdoe")
        self.assertEqual(report["outcome"], rri.IngestOutcome.OK)
        self.assertEqual(report["target_token"]["target_content_hash"], "3f9a21bc")
        self.assertEqual(len(list(cf.list_open_flags())), 1)

    def test_malformed_schema_rejected_without_queue_write(self):
        pkg = load("invalid_missing_fields.json")
        report = rri.ingest(pkg, apply=True)
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_INVALID)
        self.assertTrue(report["errors"])
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_obsolete_version_and_hash_rejected_as_stale(self):
        # Update live record to a newer version/hash
        self._seed_record(
            canonical_id="AUTOSAR/AP/record/tsync-user-guide",
            release="R26-03",
            content_hash="deadbeef",
        )
        pkg = load("valid_github_issue.json")  # has target_content_hash: 3f9a21bc, R25-11
        report = rri.ingest(pkg, apply=True, authoritative_actor="jdoe")
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_STALE)
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_soft_stale_hash_only_mismatch_is_warning_not_rejection(self):
        # Seed record with matching version ID string but differing content hash
        parsed_v = vid_util.parse_version_id(load("valid_github_issue.json")["target_version_id"])
        assert parsed_v is not None
        # Record has same version_id string in metadata, but content hash in store is 11223344
        rec_dir = self._records_dir / "AUTOSAR/AP/record"
        rec_file = rec_dir / "tsync-user-guide.json"
        rec_data = {
            "id": "tsync-user-guide",
            "canonical_id": "AUTOSAR/AP/record/tsync-user-guide",
            "status": {"state": "valid/published"},
            "version_id": load("valid_github_issue.json")["target_version_id"],
            "target_content_hash": "11223344",
        }
        rec_file.write_text(json.dumps(rec_data), encoding="utf-8")

        pkg = load("valid_github_issue.json")
        report = rri.ingest(pkg, apply=True, authoritative_actor="jdoe")
        self.assertEqual(report["outcome"], rri.IngestOutcome.OK)
        self.assertTrue(any("soft" in w.lower() or "mismatch" in w.lower() for w in report["warnings"]))

    def test_duplicate_submission_rejected(self):
        pkg = load("valid_github_issue.json")
        first = rri.ingest(pkg, apply=True, authoritative_actor="jdoe")
        self.assertEqual(first["outcome"], rri.IngestOutcome.OK)

        pkg2 = dict(pkg)
        pkg2["request_id"] = "review-request:018f2e1a-aaaa-7c21-9a4e-2f6b1d8c9a99"
        second = rri.ingest(pkg2, apply=True, authoritative_actor="jdoe")
        self.assertEqual(second["outcome"], rri.IngestOutcome.REJECTED_DUPLICATE)
        self.assertEqual(len(list(cf.list_open_flags())), 1)

    def test_unsupported_category_rejected(self):
        pkg = load("valid_github_issue.json")
        pkg = dict(pkg)
        pkg["category"] = "not-a-real-category"
        report = rri.ingest(pkg, apply=True, authoritative_actor="jdoe")
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_INVALID)
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_insufficient_attribution_rejected(self):
        pkg = load("valid_github_issue.json")
        pkg = dict(pkg)
        pkg["actor_claim"] = {"display_name": "", "identity_kind": "github_authenticated"}
        report = rri.ingest(pkg, apply=True, authoritative_actor="jdoe")
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_INVALID)

    def test_spoofed_trust_claim_over_json_export_rejected(self):
        pkg = load("valid_json_export.json")
        pkg = dict(pkg)
        pkg["target_version_id"] = "AUTOSAR/AP/record/tsync-user-guide@rel:R25-11#3f9a21bc"
        pkg["actor_claim"] = {"display_name": "jdoe", "identity_kind": "github_authenticated"}
        report = rri.ingest(pkg, apply=True)
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_SPOOFED_TRUST)
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_spoofed_trust_claim_github_issue_without_verified_actor_rejected(self):
        pkg = load("valid_github_issue.json")
        report = rri.ingest(pkg, apply=True, authoritative_actor=None)
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_SPOOFED_TRUST)
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_lossless_submission_to_queue_mapping(self):
        pkg = load("valid_github_issue.json")
        report = rri.ingest(pkg, apply=True, authoritative_actor="jdoe")
        payload = json.loads(Path(report["path"]).read_text(encoding="utf-8"))
        basis = payload["decision_basis"]
        self.assertEqual(basis["target_canonical_id"], pkg["target_canonical_id"])
        self.assertEqual(basis["target_version_id"], pkg["target_version_id"])
        self.assertEqual(basis["category"], pkg["category"])
        self.assertEqual(basis["evidence_refs"], pkg["evidence_refs"])
        self.assertEqual(basis["source_url"], pkg["source_url"])
        self.assertEqual(basis["request_id"], pkg["request_id"])
        self.assertEqual(payload["rationale"], pkg["rationale"])

    def test_dry_run_does_not_write_queue_item(self):
        pkg = load("valid_github_issue.json")
        report = rri.ingest(pkg, apply=False, authoritative_actor="jdoe")
        self.assertEqual(report["outcome"], rri.IngestOutcome.OK)
        self.assertTrue(report.get("dry_run"))
        self.assertIsNotNone(report.get("target_token"))
        self.assertEqual(list(cf.list_open_flags()), [])

    # -------------------------------------------------------------------------
    # Trusted Transport Profiles, Envelopes & Replay Tests
    # -------------------------------------------------------------------------

    def test_github_webhook_sha256_profile_valid_signature_succeeds(self):
        pkg = load("valid_github_issue.json")
        pkg_digest = rrp.package_digest(pkg)
        raw_bytes = json.dumps(pkg, sort_keys=True).encode("utf-8")
        secret = "super-secret-webhook-key"
        sig = "sha256=" + hmac.new(secret.encode("utf-8"), raw_bytes, hashlib.sha256).hexdigest()

        envelope = {
            "envelope_kind": "review-request-envelope@v1",
            "event_id": "018f2e1a-7b3c-7c21-9a4e-2f6b1d8c9a01",
            "package": pkg,
            "package_sha256": pkg_digest,
            "trust_profile": "github-webhook-sha256-v1",
            "authoritative_actor": "verified-committer",
            "repository": "AUTOSAR/autodocs",
            "issue_number": 42,
            "delivery_id": "d-777",
            "received_at": "2026-08-15T07:40:05Z",
        }

        report = rri.ingest(
            package_or_envelope=envelope,
            apply=True,
            raw_body=raw_bytes,
            signature_header=sig,
            webhook_secret=secret,
        )
        self.assertEqual(report["outcome"], rri.IngestOutcome.OK)
        payload = json.loads(Path(report["path"]).read_text(encoding="utf-8"))
        self.assertEqual(payload["identity"], "github_authenticated")
        self.assertEqual(payload["decision_basis"]["authoritative_actor"], "verified-committer")

    def test_github_webhook_sha256_profile_invalid_signature_rejected(self):
        pkg = load("valid_github_issue.json")
        pkg_digest = rrp.package_digest(pkg)
        raw_bytes = json.dumps(pkg, sort_keys=True).encode("utf-8")

        envelope = {
            "envelope_kind": "review-request-envelope@v1",
            "event_id": "018f2e1a-7b3c-7c21-9a4e-2f6b1d8c9a01",
            "package": pkg,
            "package_sha256": pkg_digest,
            "trust_profile": "github-webhook-sha256-v1",
            "authoritative_actor": "verified-committer",
            "repository": "AUTOSAR/autodocs",
            "issue_number": 42,
            "delivery_id": "d-778",
        }

        report = rri.ingest(
            package_or_envelope=envelope,
            apply=True,
            raw_body=raw_bytes,
            signature_header="sha256=invalid-bogus-sig",
            webhook_secret="super-secret-webhook-key",
        )
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_UNTRUSTED_TRANSPORT)
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_github_api_refetch_profile_valid_refetch_succeeds(self):
        pkg = load("valid_github_issue.json")
        pkg_digest = rrp.package_digest(pkg)

        envelope = {
            "envelope_kind": "review-request-envelope@v1",
            "event_id": "018f2e1a-7b3c-7c21-9a4e-2f6b1d8c9a01",
            "package": pkg,
            "package_sha256": pkg_digest,
            "trust_profile": "github-api-refetch-v1",
            "authoritative_actor": "octocat",
            "repository": "AUTOSAR/autodocs",
            "issue_number": 99,
        }

        def mock_refetch(repo: str, issue_nr: int):
            return {
                "author": "octocat",
                "body": f"```json\n{json.dumps(pkg)}\n```",
                "package_sha256": pkg_digest,
            }

        report = rri.ingest(
            package_or_envelope=envelope,
            apply=True,
            refetch_fn=mock_refetch,
        )
        self.assertEqual(report["outcome"], rri.IngestOutcome.OK)
        payload = json.loads(Path(report["path"]).read_text(encoding="utf-8"))
        self.assertEqual(payload["decision_basis"]["authoritative_actor"], "octocat")

    def test_github_api_refetch_profile_author_mismatch_rejected_tampering(self):
        pkg = load("valid_github_issue.json")
        pkg_digest = rrp.package_digest(pkg)

        envelope = {
            "envelope_kind": "review-request-envelope@v1",
            "event_id": "018f2e1a-7b3c-7c21-9a4e-2f6b1d8c9a01",
            "package": pkg,
            "package_sha256": pkg_digest,
            "trust_profile": "github-api-refetch-v1",
            "authoritative_actor": "octocat",
            "repository": "AUTOSAR/autodocs",
            "issue_number": 99,
        }

        def mock_refetch(repo: str, issue_nr: int):
            return {
                "author": "attacker-not-octocat",
                "body": f"```json\n{json.dumps(pkg)}\n```",
                "package_sha256": pkg_digest,
            }

        report = rri.ingest(
            package_or_envelope=envelope,
            apply=True,
            refetch_fn=mock_refetch,
        )
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_TAMPERING)
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_disallowed_repository_rejected(self):
        pkg = load("valid_github_issue.json")
        pkg_digest = rrp.package_digest(pkg)

        envelope = {
            "envelope_kind": "review-request-envelope@v1",
            "event_id": "018f2e1a-7b3c-7c21-9a4e-2f6b1d8c9a01",
            "package": pkg,
            "package_sha256": pkg_digest,
            "trust_profile": "github-webhook-sha256-v1",
            "authoritative_actor": "verified-user",
            "repository": "untrusted-attacker-org/malicious-repo",
            "issue_number": 1,
        }

        report = rri.ingest(package_or_envelope=envelope, apply=True)
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_UNTRUSTED_TRANSPORT)
        self.assertTrue(any("allowlist" in e for e in report["errors"]))
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_envelope_package_sha256_mismatch_rejected_tampering(self):
        pkg = load("valid_github_issue.json")
        envelope = {
            "envelope_kind": "review-request-envelope@v1",
            "event_id": "018f2e1a-7b3c-7c21-9a4e-2f6b1d8c9a01",
            "package": pkg,
            "package_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
            "trust_profile": "github-webhook-sha256-v1",
            "authoritative_actor": "verified-user",
            "repository": "AUTOSAR/autodocs",
            "issue_number": 1,
        }
        report = rri.ingest(package_or_envelope=envelope, apply=True)
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_INVALID)
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_replay_protection_replayed_delivery_id_with_modified_payload_rejected(self):
        pkg1 = load("valid_github_issue.json")
        pkg1_digest = rrp.package_digest(pkg1)

        envelope1 = {
            "envelope_kind": "review-request-envelope@v1",
            "event_id": "018f2e1a-7b3c-7c21-9a4e-2f6b1d8c9a01",
            "package": pkg1,
            "package_sha256": pkg1_digest,
            "trust_profile": "github-webhook-sha256-v1",
            "authoritative_actor": "verified-user",
            "repository": "AUTOSAR/autodocs",
            "issue_number": 10,
            "delivery_id": "delivery-unique-123",
        }

        # First ingestion succeeds
        rep1 = rri.ingest(package_or_envelope=envelope1, apply=True)
        self.assertEqual(rep1["outcome"], rri.IngestOutcome.OK)

        # Modified package with SAME delivery_id -> Replay conflict / tampering
        pkg2 = dict(pkg1)
        pkg2["rationale"] = "Modified tampered rationale"
        pkg2_digest = rrp.package_digest(pkg2)

        envelope2 = {
            "envelope_kind": "review-request-envelope@v1",
            "event_id": "018f2e1a-7b3c-7c21-9a4e-2f6b1d8c9a02",
            "package": pkg2,
            "package_sha256": pkg2_digest,
            "trust_profile": "github-webhook-sha256-v1",
            "authoritative_actor": "verified-user",
            "repository": "AUTOSAR/autodocs",
            "issue_number": 10,
            "delivery_id": "delivery-unique-123",
        }

        rep2 = rri.ingest(package_or_envelope=envelope2, apply=True)
        self.assertEqual(rep2["outcome"], rri.IngestOutcome.REJECTED_REPLAY)

    def test_local_import_envelope_forces_self_declared(self):
        pkg = load("valid_json_export.json")
        pkg["target_version_id"] = "AUTOSAR/AP/record/tsync-user-guide@rel:R25-11#3f9a21bc"
        pkg_digest = rrp.package_digest(pkg)

        envelope = {
            "envelope_kind": "review-request-local-envelope@v1",
            "event_id": "018f2e1a-7b3c-7c21-9a4e-2f6b1d8c9a01",
            "package": pkg,
            "package_sha256": pkg_digest,
            "trust_profile": "local-import-v1",
        }

        report = rri.ingest(package_or_envelope=envelope, apply=True)
        self.assertEqual(report["outcome"], rri.IngestOutcome.OK)
        payload = json.loads(Path(report["path"]).read_text(encoding="utf-8"))
        self.assertEqual(payload["identity"], "self_declared")
        self.assertIsNone(payload["decision_basis"]["authoritative_actor"])

    def test_no_js_github_issue_body_intake_normalized(self):
        pkg = load("valid_github_issue.json")
        issue_body_text = f"Hello team,\n\n```json\n{json.dumps(pkg, indent=2)}\n```\n\nThanks!"
        parsed_pkg = rri.parse_issue_body(issue_body_text)
        self.assertIsNotNone(parsed_pkg)
        assert parsed_pkg is not None
        self.assertEqual(parsed_pkg["request_id"], pkg["request_id"])

        report = rri.ingest(parsed_pkg, apply=True, authoritative_actor="jdoe")
        self.assertEqual(report["outcome"], rri.IngestOutcome.OK)
        self.assertEqual(len(list(cf.list_open_flags())), 1)

    def test_no_js_github_issue_body_malformed_rejected(self):
        issue_body_text = "```json\n{ this is not valid json }\n```"
        parsed_pkg = rri.parse_issue_body(issue_body_text)
        self.assertIsNone(parsed_pkg)

    def test_review_request_package_v2_ingestion_with_envelope(self):
        self._seed_record(
            canonical_id="AUTOSAR/AP/record/ExecutionClient",
            status_state="valid/published",
            content_hash="c0ffee01",
            release="R25-11",
        )
        pkg_v2 = {
            "kind": "review-request-package@v2",
            "event_id": "017f22e2-79b0-7cc3-98c4-dc0c0c07398f",
            "target_canonical_id": "AUTOSAR/AP/record/ExecutionClient",
            "category": "factual-error",
            "rationale": "Method signature does not match generated header.",
            "evidence_url": "https://example.org/docs/ara-exec.html",
        }
        pkg_digest = rrp.package_digest(pkg_v2)

        envelope = {
            "envelope_kind": "review-request-envelope@v1",
            "event_id": "017f22e2-79b0-7cc3-98c4-dc0c0c07398f",
            "package": pkg_v2,
            "package_sha256": pkg_digest,
            "trust_profile": "github-webhook-sha256-v1",
            "authoritative_actor": "reviewer-alice",
            "repository": "AUTOSAR/autodocs",
            "issue_number": 55,
        }

        report = rri.ingest(package_or_envelope=envelope, apply=True)
        self.assertEqual(report["outcome"], rri.IngestOutcome.OK)
        payload = json.loads(Path(report["path"]).read_text(encoding="utf-8"))
        self.assertEqual(payload["decision_basis"]["authoritative_actor"], "reviewer-alice")
        self.assertEqual(payload["decision_basis"]["target_canonical_id"], "AUTOSAR/AP/record/ExecutionClient")


if __name__ == "__main__":
    unittest.main()
