import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import curation_flags as cf  # noqa: E402
import review_request_ingest as rri  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "review_request"


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ReviewRequestIngestTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._orig_queue = cf.QUEUE
        self._orig_open = cf.OPEN_DIR
        self._orig_claimed = cf.CLAIMED_DIR
        self._orig_done = cf.DONE_DIR
        cf.QUEUE = Path(self._tmpdir.name) / "curation-queue"
        cf.OPEN_DIR = cf.QUEUE / "open"
        cf.CLAIMED_DIR = cf.QUEUE / "claimed"
        cf.DONE_DIR = cf.QUEUE / "done"

    def tearDown(self):
        cf.QUEUE = self._orig_queue
        cf.OPEN_DIR = self._orig_open
        cf.CLAIMED_DIR = self._orig_claimed
        cf.DONE_DIR = self._orig_done
        self._tmpdir.cleanup()

    def test_happy_path_github_issue_creates_open_flag(self):
        pkg = load("valid_github_issue.json")
        report = rri.ingest(pkg, apply=True,
                             current_content_hash=pkg["target_content_hash"],
                             current_version_id=pkg["target_version_id"],
                             authoritative_actor="jdoe")
        self.assertEqual(report["outcome"], rri.IngestOutcome.OK)
        self.assertIsNotNone(report["path"])
        payload = json.loads(Path(report["path"]).read_text(encoding="utf-8"))
        self.assertEqual(payload["item_kind"], "review-request")
        self.assertEqual(payload["identity"], "github_authenticated")
        self.assertEqual(payload["decision_basis"]["authoritative_actor"], "jdoe")

    def test_happy_path_json_export_forces_self_declared(self):
        pkg = load("valid_json_export.json")
        report = rri.ingest(pkg, apply=True,
                             current_content_hash=pkg["target_content_hash"],
                             current_version_id=pkg["target_version_id"])
        self.assertEqual(report["outcome"], rri.IngestOutcome.OK)
        payload = json.loads(Path(report["path"]).read_text(encoding="utf-8"))
        self.assertEqual(payload["identity"], "self_declared")
        self.assertTrue(any("self_declared" in w for w in report["warnings"]))

    def test_malformed_schema_rejected_without_queue_write(self):
        pkg = load("invalid_missing_fields.json")
        report = rri.ingest(pkg, apply=True)
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_INVALID)
        self.assertTrue(report["errors"])
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_obsolete_version_and_hash_rejected_as_stale(self):
        pkg = load("valid_github_issue.json")
        report = rri.ingest(
            pkg, apply=True,
            current_content_hash="deadbeef",
            current_version_id="AUTOSAR/AP/record/tsync-user-guide@rel:R25-11#deadbeef",
            authoritative_actor="jdoe")
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_STALE)
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_soft_stale_hash_only_mismatch_is_warning_not_rejection(self):
        pkg = load("valid_github_issue.json")
        report = rri.ingest(
            pkg, apply=True,
            current_content_hash="deadbeef",
            current_version_id=pkg["target_version_id"],
            authoritative_actor="jdoe")
        self.assertEqual(report["outcome"], rri.IngestOutcome.OK)
        self.assertTrue(any("soft warning" in w for w in report["warnings"]))

    def test_duplicate_submission_rejected(self):
        pkg = load("valid_github_issue.json")
        first = rri.ingest(pkg, apply=True,
                            current_content_hash=pkg["target_content_hash"],
                            current_version_id=pkg["target_version_id"],
                            authoritative_actor="jdoe")
        self.assertEqual(first["outcome"], rri.IngestOutcome.OK)

        pkg2 = dict(pkg)
        pkg2["request_id"] = "review-request:018f2e1a-aaaa-7c21-9a4e-2f6b1d8c9a99"
        second = rri.ingest(pkg2, apply=True,
                             current_content_hash=pkg["target_content_hash"],
                             current_version_id=pkg["target_version_id"],
                             authoritative_actor="jdoe")
        self.assertEqual(second["outcome"], rri.IngestOutcome.REJECTED_DUPLICATE)
        self.assertEqual(len(list(cf.list_open_flags())), 1)

    def test_unsupported_category_rejected(self):
        pkg = load("valid_github_issue.json")
        pkg = dict(pkg)
        pkg["category"] = "not-a-real-category"
        report = rri.ingest(pkg, apply=True,
                             current_content_hash=pkg["target_content_hash"],
                             current_version_id=pkg["target_version_id"],
                             authoritative_actor="jdoe")
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_INVALID)
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_insufficient_attribution_rejected(self):
        pkg = load("valid_github_issue.json")
        pkg = dict(pkg)
        pkg["actor_claim"] = {"display_name": "", "identity_kind": "github_authenticated"}
        report = rri.ingest(pkg, apply=True,
                             current_content_hash=pkg["target_content_hash"],
                             current_version_id=pkg["target_version_id"],
                             authoritative_actor="jdoe")
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_INVALID)

    def test_spoofed_trust_claim_over_json_export_rejected(self):
        pkg = load("valid_json_export.json")
        pkg = dict(pkg)
        pkg["actor_claim"] = {"display_name": "jdoe", "identity_kind": "github_authenticated"}
        report = rri.ingest(pkg, apply=True,
                             current_content_hash=pkg["target_content_hash"],
                             current_version_id=pkg["target_version_id"])
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_SPOOFED_TRUST)
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_spoofed_trust_claim_github_issue_without_verified_actor_rejected(self):
        pkg = load("valid_github_issue.json")
        report = rri.ingest(pkg, apply=True,
                             current_content_hash=pkg["target_content_hash"],
                             current_version_id=pkg["target_version_id"],
                             authoritative_actor=None)
        self.assertEqual(report["outcome"], rri.IngestOutcome.REJECTED_SPOOFED_TRUST)
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_lossless_submission_to_queue_mapping(self):
        pkg = load("valid_github_issue.json")
        report = rri.ingest(pkg, apply=True,
                             current_content_hash=pkg["target_content_hash"],
                             current_version_id=pkg["target_version_id"],
                             authoritative_actor="jdoe")
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
        report = rri.ingest(pkg, apply=False,
                             current_content_hash=pkg["target_content_hash"],
                             current_version_id=pkg["target_version_id"],
                             authoritative_actor="jdoe")
        self.assertEqual(report["outcome"], rri.IngestOutcome.OK)
        self.assertTrue(report.get("dry_run"))
        self.assertEqual(list(cf.list_open_flags()), [])


if __name__ == "__main__":
    unittest.main()
