#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_feedback_recipe_contract.py -- Comprehensive tests for Feature 0045 feedback handoff consumer.

Covers:
  - REQ-0045-04: Priority-gated Project Lead offer & award verification before trusted ingestion.
  - REQ-0045-05: Central Project Lead decision & runner assignment binding.
  - REQ-0045-06: Feedback/proposal cycle creating trusted committed queue item without mutating canonical record bytes.
  - REQ-0045-08: Typed deterministic recipes with role and effect boundaries.
  - REQ-0045-12: Exact idempotence keys, replay, conflict, retry ancestry, and restart reconstruction.
  - REQ-0045-16: Fail-closed authoritative selector & documentation compatibility check.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import canonical_id as cid  # noqa: E402
import curation_flags as cf  # noqa: E402
import curation_item as ci  # noqa: E402
import feedback_recipe_contract as frc  # noqa: E402
import review_request_ingest as rri  # noqa: E402
import version_id as vid_util  # noqa: E402


class FeedbackRecipeContractTests(unittest.TestCase):
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
        self._orig_frc_records_root = frc.RECORDS_ROOT
        self._orig_frc_versions_root = frc.VERSIONS_ROOT
        self._records_dir = self._root / "records"
        self._versions_dir = self._root / "versions"
        self._records_dir.mkdir(parents=True, exist_ok=True)
        self._versions_dir.mkdir(parents=True, exist_ok=True)
        rri.RECORDS_ROOT = self._records_dir
        rri.VERSIONS_ROOT = self._versions_dir
        frc.RECORDS_ROOT = self._records_dir
        frc.VERSIONS_ROOT = self._versions_dir

        # Autodocs root redirection
        self._orig_autodocs_root = frc.AUTODOCS_ROOT
        self._autodocs_dir = self._root / "autodocs"
        self._autodocs_dir.mkdir(parents=True, exist_ok=True)
        frc.AUTODOCS_ROOT = self._autodocs_dir

        # Create valid agent-workflow.json
        (self._autodocs_dir / "agent-workflow.json").write_text(
            json.dumps({
                "schema": "agent-workflow-bootstrap@v1",
                "workflow_version": "1.0.0",
                "authority_epoch": "legacy-writable",
                "runner_protocol": "runner-request@v1",
            }),
            encoding="utf-8",
        )

        # Reset global replay & consumer receipt trackers
        rri.reset_replay_tracker()
        frc.reset_receipt_store()

        # Seed authoritative record for AUTOSAR/AP/record/tsync-user-guide
        self._rec_file, self._version_id = self._seed_record(
            canonical_id="AUTOSAR/AP/record/tsync-user-guide",
            release="R25-11",
            content_hash="3f9a21bc",
            status_state="valid/published",
            content="Standard TSync User Guide specification text.",
            source_url="https://example.org/en/modules/tsync.html#user-guide",
        )

        # Construct standard valid feedback handoff payload
        payload_data = {
            "text": "Proposed clarification for TSync section 4.2",
            "suggested_change": "Update wording to reflect standard timing clock.",
        }
        payload_digest = frc.compute_sha256(payload_data)

        self.valid_handoff = {
            "schema": "feedback-recipe-contract@v1",
            "contract_version": "v1.0.0",
            "producer_repository": "2b-rs/agent-inbox",
            "producer_commit": "9776291cc5f02086db6be5830176301367ee565d",
            "consumer_baseline": "5c6068537aa4a304c940ca82f62b466a08d72136",
            "scheduling_decision_id": "dec-score-101",
            "assignment_id": "asg-recipe-001",
            "idempotence_key": "feedback:2b-rs/autodocs:issue-42:AUTOSAR/AP/record/tsync-user-guide",
            "normalized_input_digest": payload_digest,
            "status": "succeeded",
            "recipe_name": "feedback_ingestion",
            "trusted_envelope": {
                "schema": "github-event-envelope@v1",
                "event_id": "018f2e1a-7b3c-7c21-9a4e-2f6b1d8c9a01",
                "event_kind": "curation_feedback",
                "repository": "2b-rs/autodocs",
                "source_id": "issue-42",
                "record_id": "AUTOSAR/AP/record/tsync-user-guide",
                "record_version": self._version_id,
                "sender": "contributor-alice",
                "created_at": "2026-09-01T00:00:00Z",
                "payload": payload_data,
            },
            "ingestion_result": {
                "schema": "feedback-ingestion-result@v1",
                "queue_item_id": "queue-item-tsync-user-guide-018f2e1a",
                "queue_item_version": "v1.0.0",
                "deduplication_disposition": "new",
                "submitted_record_version": self._version_id,
                "current_record_version": self._version_id,
            },
            "durable_receipt": {
                "receipt_id": "rcpt-asg-recipe-001",
                "receipt_digest": "4a7d6e8b2c1f9a0e3d5b7c8a1e2f3d4c5b6a7e8f9a0b1c2d3e4f5a6b7c8d9e0f",
                "recorded_at": "2026-09-01T00:00:01Z",
            },
            "retry_ancestry": [],
            "next_event": "proposal_scheduling_continuation:queue-item-tsync-user-guide-018f2e1a",
            "error_details": None,
            "created_at": "2026-09-01T00:00:01Z",
        }

    def tearDown(self):
        cf.QUEUE = self._orig_queue
        cf.OPEN_DIR = self._orig_open
        cf.CLAIMED_DIR = self._orig_claimed
        cf.DONE_DIR = self._orig_done
        rri.RECORDS_ROOT = self._orig_records_root
        rri.VERSIONS_ROOT = self._orig_versions_root
        frc.RECORDS_ROOT = self._orig_frc_records_root
        frc.VERSIONS_ROOT = self._orig_frc_versions_root
        frc.AUTODOCS_ROOT = self._orig_autodocs_root
        rri.reset_replay_tracker()
        frc.reset_receipt_store()
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
    # Conforming Ingestion & Canonical Record Bytes Preservation (REQ-0045-06)
    # -------------------------------------------------------------------------

    def test_conforming_handoff_creates_exactly_one_queue_item_without_record_mutation(self):
        """Happy path: Conforming trusted handoff creates exactly one committed queue item,
        emits continuation receipt, and leaves canonical record bytes strictly untouched."""
        record_bytes_before = self._rec_file.read_bytes()
        record_sha256_before = hashlib.sha256(record_bytes_before).hexdigest()

        report = frc.consume_feedback_recipe_handoff(
            handoff=self.valid_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )

        self.assertEqual(report["status"], frc.FeedbackConsumerOutcome.OK)
        self.assertFalse(report["target_record_mutated"])
        self.assertIsNotNone(report["queue_item_path"])
        self.assertEqual(report["deduplication_disposition"], "new")
        self.assertTrue(report["next_event"].startswith("proposal_scheduling_continuation:"))
        self.assertIsNotNone(report["durable_receipt"])

        # Exactly ONE queue item file in open/
        open_flags = list(cf.list_open_flags())
        self.assertEqual(len(open_flags), 1)
        self.assertEqual(str(open_flags[0]), report["queue_item_path"])

        # Verify queue item structure & conformances
        item_data = json.loads(open_flags[0].read_text(encoding="utf-8"))
        self.assertEqual(item_data["schema"], cf.SCHEMA)
        self.assertEqual(item_data["canonical_id"], "AUTOSAR/AP/record/tsync-user-guide")
        self.assertEqual(item_data["item_kind"], "review-request")
        self.assertEqual(item_data["status"], "open")
        self.assertEqual(item_data["identity"], "contributor-alice")
        self.assertIsNone(item_data["decided_by"])
        self.assertIsNone(item_data["decided_at"])

        basis = item_data["decision_basis"]
        self.assertEqual(basis["handoff_schema"], "feedback-recipe-contract@v1")
        self.assertEqual(basis["scheduling_decision_id"], "dec-score-101")
        self.assertEqual(basis["assignment_id"], "asg-recipe-001")
        self.assertEqual(basis["idempotence_key"], self.valid_handoff["idempotence_key"])
        self.assertEqual(basis["normalized_input_digest"], self.valid_handoff["normalized_input_digest"])

        curation_item_obj = ci.from_curation_flag(item_data)
        self.assertTrue(ci.is_conformant(curation_item_obj))

        # Explicit proof: canonical record bytes are completely identical
        record_bytes_after = self._rec_file.read_bytes()
        record_sha256_after = hashlib.sha256(record_bytes_after).hexdigest()
        self.assertEqual(record_sha256_before, record_sha256_after)
        self.assertEqual(record_bytes_before, record_bytes_after)

    def test_dry_run_validates_without_writing_queue_item(self):
        """Dry-run (apply=False) performs all validations and mints target token without creating queue item."""
        report = frc.consume_feedback_recipe_handoff(
            handoff=self.valid_handoff,
            apply=False,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )
        self.assertEqual(report["status"], frc.FeedbackConsumerOutcome.OK)
        self.assertTrue(report["dry_run"])
        self.assertIsNotNone(report["target_token"])
        self.assertEqual(list(cf.list_open_flags()), [])

    # -------------------------------------------------------------------------
    # Priority-Gated Award & Runner Assignment Verification (REQ-0045-04, REQ-0045-05)
    # -------------------------------------------------------------------------

    def test_unawarded_missing_scheduling_decision_rejected(self):
        """Handoff missing scheduling_decision_id is rejected as unawarded execution (effect-free)."""
        bad_handoff = copy.deepcopy(self.valid_handoff)
        bad_handoff["scheduling_decision_id"] = ""

        report = frc.consume_feedback_recipe_handoff(
            handoff=bad_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )
        self.assertEqual(report["status"], frc.FeedbackConsumerOutcome.REJECTED_INVALID_SCHEMA)
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_missing_assignment_id_rejected(self):
        """Handoff missing assignment_id is rejected (effect-free)."""
        bad_handoff = copy.deepcopy(self.valid_handoff)
        bad_handoff["assignment_id"] = "   "

        report = frc.consume_feedback_recipe_handoff(
            handoff=bad_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )
        self.assertEqual(report["status"], frc.FeedbackConsumerOutcome.REJECTED_INVALID_SCHEMA)
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_mismatched_recipe_name_rejected(self):
        """Handoff with recipe_name other than feedback_ingestion is rejected."""
        bad_handoff = copy.deepcopy(self.valid_handoff)
        bad_handoff["recipe_name"] = "unauthorized_recipe"

        report = frc.consume_feedback_recipe_handoff(
            handoff=bad_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )
        self.assertEqual(report["status"], frc.FeedbackConsumerOutcome.REJECTED_INVALID_SCHEMA)
        self.assertTrue(any("invalid recipe_name" in e for e in report["errors"]))
        self.assertEqual(list(cf.list_open_flags()), [])

    # -------------------------------------------------------------------------
    # Fail-Closed Authoritative Selector Check (REQ-0045-16)
    # -------------------------------------------------------------------------

    def test_fail_closed_on_incompatible_runner_protocol_in_selector(self):
        """If agent-workflow.json declares an incompatible runner_protocol, fail-closed."""
        (self._autodocs_dir / "agent-workflow.json").write_text(
            json.dumps({"runner_protocol": "unsupported-protocol@v9"}),
            encoding="utf-8",
        )

        report = frc.consume_feedback_recipe_handoff(
            handoff=self.valid_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )
        self.assertEqual(report["status"], frc.FeedbackConsumerOutcome.REJECTED_SELECTOR_MISMATCH)
        self.assertEqual(list(cf.list_open_flags()), [])

    # -------------------------------------------------------------------------
    # Idempotence, Replay, Conflict & Duplicate (REQ-0045-12, 0033-07)
    # -------------------------------------------------------------------------

    def test_idempotent_replay_with_same_input_digest_returns_recorded_result(self):
        """Exact same idempotence key + identical normalized input digest returns recorded result."""
        first_report = frc.consume_feedback_recipe_handoff(
            handoff=self.valid_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )
        self.assertEqual(first_report["status"], frc.FeedbackConsumerOutcome.OK)
        self.assertEqual(len(list(cf.list_open_flags())), 1)

        # Replay second time
        second_report = frc.consume_feedback_recipe_handoff(
            handoff=self.valid_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )
        self.assertEqual(second_report["status"], frc.FeedbackConsumerOutcome.OK)
        self.assertEqual(second_report["deduplication_disposition"], "replay")
        self.assertEqual(second_report["queue_item_id"], first_report["queue_item_id"])
        # No second queue item created
        self.assertEqual(len(list(cf.list_open_flags())), 1)

    def test_idempotence_conflict_with_different_input_digest_rejected_effect_free(self):
        """Same idempotence key + different normalized input digest returns conflict (effect-free)."""
        first_report = frc.consume_feedback_recipe_handoff(
            handoff=self.valid_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )
        self.assertEqual(first_report["status"], frc.FeedbackConsumerOutcome.OK)

        # Modify payload digest for same idempotence key
        tampered_handoff = copy.deepcopy(self.valid_handoff)
        tampered_handoff["trusted_envelope"]["payload"]["text"] = "Different conflicting text"
        new_digest = frc.compute_sha256(tampered_handoff["trusted_envelope"]["payload"])
        tampered_handoff["normalized_input_digest"] = new_digest

        conflict_report = frc.consume_feedback_recipe_handoff(
            handoff=tampered_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )
        self.assertEqual(conflict_report["status"], frc.FeedbackConsumerOutcome.REJECTED_CONFLICT)
        self.assertEqual(conflict_report["next_event"], "terminal:idempotence_conflict")
        # No extra queue item
        self.assertEqual(len(list(cf.list_open_flags())), 1)

    def test_active_duplicate_record_in_queue_rejected(self):
        """If an active queue item exists for the target record, new submission is rejected as duplicate."""
        first_report = frc.consume_feedback_recipe_handoff(
            handoff=self.valid_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )
        self.assertEqual(first_report["status"], frc.FeedbackConsumerOutcome.OK)

        # New handoff for the same target record from a different issue/source_id
        diff_handoff = copy.deepcopy(self.valid_handoff)
        diff_handoff["trusted_envelope"]["source_id"] = "issue-99"
        diff_handoff["idempotence_key"] = "feedback:2b-rs/autodocs:issue-99:AUTOSAR/AP/record/tsync-user-guide"

        dup_report = frc.consume_feedback_recipe_handoff(
            handoff=diff_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )
        self.assertEqual(dup_report["status"], frc.FeedbackConsumerOutcome.REJECTED_DUPLICATE)
        self.assertEqual(len(list(cf.list_open_flags())), 1)

    # -------------------------------------------------------------------------
    # Target Resolution & Staleness Checks (REQ-0045-06, 0033-06)
    # -------------------------------------------------------------------------

    def test_unknown_target_record_rejected_without_queue_write(self):
        """Target record not found in authoritative record/version store is rejected."""
        bad_handoff = copy.deepcopy(self.valid_handoff)
        bad_handoff["trusted_envelope"]["record_id"] = "AUTOSAR/AP/record/unknown-record"
        bad_handoff["idempotence_key"] = "feedback:2b-rs/autodocs:issue-42:AUTOSAR/AP/record/unknown-record"

        report = frc.consume_feedback_recipe_handoff(
            handoff=bad_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )
        self.assertEqual(report["status"], frc.FeedbackConsumerOutcome.REJECTED_UNKNOWN_TARGET)
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_ineligible_target_status_rejected(self):
        """Target record in draft or invalid status is rejected as ineligible."""
        self._seed_record(
            canonical_id="AUTOSAR/AP/record/draft-doc",
            status_state="invalid/draft",
        )
        bad_handoff = copy.deepcopy(self.valid_handoff)
        bad_handoff["trusted_envelope"]["record_id"] = "AUTOSAR/AP/record/draft-doc"
        bad_handoff["idempotence_key"] = "feedback:2b-rs/autodocs:issue-42:AUTOSAR/AP/record/draft-doc"

        report = frc.consume_feedback_recipe_handoff(
            handoff=bad_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )
        self.assertEqual(report["status"], frc.FeedbackConsumerOutcome.REJECTED_INELIGIBLE_TARGET)
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_stale_record_version_rejected(self):
        """Submitted record_version mismatching current live version is rejected as stale."""
        # Update live record to R26-03
        self._seed_record(
            canonical_id="AUTOSAR/AP/record/tsync-user-guide",
            release="R26-03",
            content_hash="deadbeef",
        )
        # Handoff still references R25-11
        report = frc.consume_feedback_recipe_handoff(
            handoff=self.valid_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )
        self.assertEqual(report["status"], frc.FeedbackConsumerOutcome.REJECTED_STALE)
        self.assertEqual(list(cf.list_open_flags()), [])

    # -------------------------------------------------------------------------
    # Transport Trust & Envelope Integrity Checks
    # -------------------------------------------------------------------------

    def test_untrusted_repository_rejected(self):
        """Repository not in allowed allowlist is rejected as untrusted transport."""
        bad_handoff = copy.deepcopy(self.valid_handoff)
        bad_handoff["trusted_envelope"]["repository"] = "malicious-org/untrusted-repo"
        bad_handoff["idempotence_key"] = "feedback:malicious-org/untrusted-repo:issue-42:AUTOSAR/AP/record/tsync-user-guide"

        report = frc.consume_feedback_recipe_handoff(
            handoff=bad_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )
        self.assertEqual(report["status"], frc.FeedbackConsumerOutcome.REJECTED_UNTRUSTED_TRANSPORT)
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_tampered_payload_digest_rejected(self):
        """Mismatch between payload content and normalized_input_digest is rejected."""
        bad_handoff = copy.deepcopy(self.valid_handoff)
        bad_handoff["normalized_input_digest"] = "0" * 64

        report = frc.consume_feedback_recipe_handoff(
            handoff=bad_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )
        self.assertEqual(report["status"], frc.FeedbackConsumerOutcome.REJECTED_TAMPERING)
        self.assertEqual(list(cf.list_open_flags()), [])

    # -------------------------------------------------------------------------
    # Producer Status Forwarding
    # -------------------------------------------------------------------------

    def test_producer_conflict_status_handled_effect_free(self):
        """Handoff with status=conflict is handled cleanly and effect-free."""
        conflict_handoff = copy.deepcopy(self.valid_handoff)
        conflict_handoff["status"] = "conflict"
        conflict_handoff["next_event"] = "terminal:idempotence_conflict"

        report = frc.consume_feedback_recipe_handoff(
            handoff=conflict_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )
        self.assertEqual(report["status"], frc.FeedbackConsumerOutcome.REJECTED_CONFLICT)
        self.assertEqual(list(cf.list_open_flags()), [])

    def test_producer_retryable_failure_handled_effect_free(self):
        """Handoff with status=retryable_failure is handled effect-free with resume point."""
        retry_handoff = copy.deepcopy(self.valid_handoff)
        retry_handoff["status"] = "retryable_failure"
        retry_handoff["next_event"] = "retry_from_last_proven_boundary"
        retry_handoff["retry_ancestry"] = [{
            "attempt": 1,
            "timestamp": "2026-09-01T00:00:01Z",
            "error_class": "TransientTransportError",
            "reason": "Temporary network timeout",
            "safe_resume_point": "last_proven_durable_boundary",
        }]

        report = frc.consume_feedback_recipe_handoff(
            handoff=retry_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            autodocs_root=self._autodocs_dir,
        )
        self.assertEqual(report["status"], frc.FeedbackConsumerOutcome.RETRYABLE_FAILURE)
        self.assertEqual(list(cf.list_open_flags()), [])

    # -------------------------------------------------------------------------
    # Curation Ingest & Review Request Ingest Direct Integration
    # -------------------------------------------------------------------------

    def test_review_request_ingest_accepts_feedback_recipe_contract(self):
        """review_request_ingest.ingest() consumes feedback-recipe-contract@v1 seamlessly."""
        report = rri.ingest(
            package_or_envelope=self.valid_handoff,
            apply=True,
            records_root=self._records_dir,
            versions_root=self._versions_dir,
        )
        self.assertEqual(report["outcome"], frc.FeedbackConsumerOutcome.OK)
        self.assertFalse(report.get("target_record_mutated", True))
        self.assertEqual(len(list(cf.list_open_flags())), 1)

    def test_curation_ingest_accepts_feedback_recipe_contract_file(self):
        """curation_ingest.ingest() consumes a feedback-recipe-contract@v1 JSON file."""
        import curation_ingest as ci_tool
        handoff_file = self._root / "handoff.json"
        handoff_file.write_text(json.dumps(self.valid_handoff, indent=2), encoding="utf-8")

        report = ci_tool.ingest(
            paket_pfad=handoff_file,
            apply=True,
            from_issue_body=False,
        )
        self.assertEqual(report["status"], frc.FeedbackConsumerOutcome.OK)
        self.assertEqual(len(list(cf.list_open_flags())), 1)


if __name__ == "__main__":
    unittest.main()
