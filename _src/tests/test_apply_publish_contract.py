#!/usr/bin/env python3
"""test_apply_publish_contract.py — End-to-end tests for autodocs apply/publication consumer.

Part of Feature 0045 (Task 0045-06.02).
Covers REQ-0045-02, REQ-0045-07, REQ-0045-09, REQ-0045-11, and REQ-0045-12.
"""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "_src" / "tools"))

from apply_publish_contract import (
    PUBLICATION_RESULT_SCHEMA,
    CONTRACT_VERSION,
    ApplyPublishConsumerError,
    ApplyPublishContractConsumer,
    compute_digest_manifest,
)


class TestApplyPublishContractConsumer(unittest.TestCase):
    def setUp(self):
        self.valid_handoff = {
            "schema": "apply-publish-contract@v1",
            "contract_version": "v1.0.0",
            "producer_repository": "2b-rs/agent-inbox",
            "producer_commit": "071c1cb1365ec90a9c4f70748275e615b9df475d",
            "consumer_baseline": "5c6068537aa4a304c940ca82f62b466a08d72136",
            "scheduling_decision_id": "dec-score-301",
            "assignment_id": "asg-apply-001",
            "idempotence_key": "decision:prop-score-301:1",
            "normalized_input_digest": "a" * 64,
            "status": "succeeded",
            "recipe_name": "apply_publish",
            "curator_decision": {
                "decision_id": "dec-curator-999",
                "proposal_id": "prop-score-301",
                "proposal_version": "v1.0.0",
                "baseline_version": "v1.0.0",
                "baseline_hash": "a1b2c3d4e5f60718293a4b5c6d7e8f90",
                "disposition": "accept",
                "curator": {
                    "name": "Jane Curator",
                    "identity_kind": "github_authenticated"
                },
                "revision": 1,
                "rationale": "Verified against AUTOSAR R25-11 SWS Core specification.",
                "evidence_refs": ["AUTOSAR_AP_SWS_Core.pdf#page=12"],
                "created_at": "2026-09-01T01:00:00Z",
                "stale_detected": False
            },
            "apply_command": {
                "schema": "apply-command@v1",
                "proposal_id": "prop-score-301",
                "decision_id": "dec-curator-999",
                "decision_revision": 1,
                "baseline_version": "v1.0.0",
                "baseline_hash": "a1b2c3d4e5f60718293a4b5c6d7e8f90",
                "database_target": "production_docmodel",
                "apply_idempotence_key": "apply:prop-score-301:1:a1b2c3d4e5f60718293a4b5c6d7e8f90",
                "suggested_change": {
                    "field": "summary",
                    "old_value": "Old text",
                    "new_value": "New corrected text"
                }
            },
            "publish_command": {
                "schema": "publish-command@v1",
                "proposal_id": "prop-score-301",
                "decision_revision": 1,
                "target_environment": "static_site",
                "configured_languages": ["en", "de", "fr", "ja", "zh"],
                "generator_version": "v1.0.0",
                "publish_idempotence_key": "publish:prop-score-301:1:a1b2c3d4e5f60718293a4b5c6d7e8f90"
            },
            "durable_receipt": {
                "receipt_id": "rcpt-apply-1234",
                "receipt_digest": "b" * 64,
                "recorded_at": "2026-09-01T01:05:00Z"
            },
            "retry_ancestry": [],
            "error_details": None,
            "created_at": "2026-09-01T01:05:00Z"
        }

    def test_consume_valid_handoff_success(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            out_dir = td / "public_site"
            receipt_dir = td / "_receipts"
            consumer = ApplyPublishContractConsumer(autodocs_root=td, receipt_store_dir=receipt_dir)

            res = consumer.consume(self.valid_handoff, output_dir=out_dir)
            self.assertEqual(res["schema"], PUBLICATION_RESULT_SCHEMA)
            self.assertEqual(res["status"], "succeeded")
            self.assertEqual(res["proposal_id"], "prop-score-301")
            self.assertEqual(res["decision_id"], "dec-curator-999")
            self.assertEqual(res["configured_languages"], ["en", "de", "fr", "ja", "zh"])
            self.assertTrue(res["validation_result"]["valid"])
            self.assertIsNotNone(res["database_commit"])

            # Verify multilingual generation
            for lang in ["en", "de", "fr", "ja", "zh"]:
                index_file = out_dir / lang / "index.html"
                self.assertTrue(index_file.exists())
                self.assertIn(f"Autodocs S-Core ({lang})", index_file.read_text(encoding="utf-8"))

            # Verify manifest
            self.assertIn("en/index.html", res["digest_manifest"])
            self.assertIn("de/index.html", res["digest_manifest"])

    def test_consume_rejected_producer_status(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            consumer = ApplyPublishContractConsumer(autodocs_root=td)
            bad_handoff = copy.deepcopy(self.valid_handoff)
            bad_handoff["status"] = "rejected_curator_decision"
            bad_handoff["apply_command"] = None
            bad_handoff["publish_command"] = None

            res = consumer.consume(bad_handoff)
            self.assertEqual(res["status"], "rejected_by_producer_rejected_curator_decision")
            self.assertEqual(res["workflow_state"], "terminal_non_mutating")
            self.assertIsNone(res["database_commit"])

    def test_stale_baseline_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            consumer = ApplyPublishContractConsumer(autodocs_root=td)
            stale_handoff = copy.deepcopy(self.valid_handoff)
            stale_handoff["curator_decision"]["stale_detected"] = True

            with self.assertRaises(ApplyPublishConsumerError) as ctx:
                consumer.consume(stale_handoff)
            self.assertEqual(ctx.exception.error_class, "StaleBaselineError")

    def test_same_key_same_payload_replay(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            receipt_dir = td / "_receipts"
            consumer = ApplyPublishContractConsumer(autodocs_root=td, receipt_store_dir=receipt_dir)

            res1 = consumer.consume(self.valid_handoff, output_dir=td / "out1")
            res2 = consumer.consume(self.valid_handoff, output_dir=td / "out2")

            self.assertEqual(res1["database_commit"], res2["database_commit"])
            self.assertEqual(res1["status"], res2["status"])

    def test_same_key_different_payload_conflict(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            receipt_dir = td / "_receipts"
            consumer = ApplyPublishContractConsumer(autodocs_root=td, receipt_store_dir=receipt_dir)

            res1 = consumer.consume(self.valid_handoff, output_dir=td / "out1")
            self.assertEqual(res1["status"], "succeeded")

            conflicting_handoff = copy.deepcopy(self.valid_handoff)
            conflicting_handoff["normalized_input_digest"] = "f" * 64

            res2 = consumer.consume(conflicting_handoff, output_dir=td / "out2")
            self.assertEqual(res2["status"], "conflict")


if __name__ == "__main__":
    unittest.main()
