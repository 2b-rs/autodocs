#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_review_request_retention.py -- Test suite for review request privacy and retention policy (0033-07.02)."""
import json
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import review_request_retention as rrr


class TestReviewRequestRetentionPolicy(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_retention_"))
        self.queue_root = self.test_dir / "curation-queue"
        self.open_dir = self.queue_root / "open"
        self.claimed_dir = self.queue_root / "claimed"
        self.done_dir = self.queue_root / "done"
        for d in (self.open_dir, self.claimed_dir, self.done_dir):
            d.mkdir(parents=True, exist_ok=True)

        self.fixed_now = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_policy_limits_metadata(self):
        limits = rrr.get_retention_policy_limits()
        self.assertEqual(limits["decision_proof_retention_days"], 3650)
        self.assertEqual(limits["raw_payload_retention_days"], 1095)
        self.assertEqual(limits["unclaimed_expiry_days"], 120)
        self.assertIn("PROC-0033-02-13", limits["governing_decisions"])

    def test_consent_and_limitations_disclaimers(self):
        en_consent = rrr.get_consent_disclaimer("en")
        de_consent = rrr.get_consent_disclaimer("de")
        self.assertIn("consent to the processing", en_consent)
        self.assertIn("Verarbeitung der angegebenen Daten", de_consent)

        en_notice = rrr.get_external_limitations_notice("en")
        de_notice = rrr.get_external_limitations_notice("de")
        self.assertIn("cannot be irrevocably deleted", en_notice)
        self.assertIn("Plattformgrenzen", de_notice)

    def test_public_projection_redaction(self):
        raw_item = {
            "id": "review-request:0191aa11-1111-7111-8111-111111111111",
            "canonical_id": "AUTOSAR/AP/record/tsync-user-guide",
            "item_kind": "review-request",
            "status": "open",
            "outcome": "requested",
            "created": "2026-08-15T07:40:00Z",
            "identity": "self_declared",
            "rationale": "Confidential internal rationale with user name John Doe and email jdoe@example.com",
            "decision_basis": {
                "category": "factual-error",
                "target_canonical_id": "AUTOSAR/AP/record/tsync-user-guide",
                "target_version_id": "AUTOSAR/AP/record/tsync-user-guide@rel:R25-11#3f9a21bc",
                "target_content_hash": "3f9a21bc",
                "source_url": "https://example.org/en/modules/tsync.html",
                "authoritative_actor": None,
                "target_token": {"token_sha256": "abcdef1234567890"},
            },
        }

        proj = rrr.redact_for_public_projection(raw_item)
        self.assertEqual(proj["schema"], "review-request-public-projection@v1")
        self.assertEqual(proj["id"], raw_item["id"])
        self.assertEqual(proj["canonical_id"], raw_item["canonical_id"])
        self.assertEqual(proj["category"], "factual-error")
        self.assertEqual(proj["target_version_id"], "AUTOSAR/AP/record/tsync-user-guide@rel:R25-11#3f9a21bc")
        self.assertEqual(proj["identity_trust"], "self_declared")
        self.assertIsNone(proj["authoritative_actor"])
        self.assertNotIn("rationale", proj)
        self.assertNotIn("John Doe", json.dumps(proj))

    def test_public_projection_github_authenticated(self):
        raw_item = {
            "id": "review-request:0191aa22-2222-7222-8222-222222222222",
            "canonical_id": "AUTOSAR/AP/record/exec-manager",
            "item_kind": "review-request",
            "status": "completed",
            "outcome": "applied",
            "created": "2026-08-10T10:00:00Z",
            "decided_at": "2026-08-11T12:00:00Z",
            "identity": "github_authenticated",
            "decision_basis": {
                "category": "outdated-content",
                "authoritative_actor": "verified-gh-user",
                "target_canonical_id": "AUTOSAR/AP/record/exec-manager",
            },
        }

        proj = rrr.redact_for_public_projection(raw_item)
        self.assertEqual(proj["identity_trust"], "github_authenticated")
        self.assertEqual(proj["authoritative_actor"], "verified-gh-user")

    def test_redact_for_long_term_proof(self):
        old_item = {
            "id": "review-request:0180aa33-3333-7333-8333-333333333333",
            "canonical_id": "AUTOSAR/AP/record/diag-service",
            "item_kind": "review-request",
            "status": "completed",
            "outcome": "applied",
            "created": "2022-01-01T00:00:00Z",
            "decided_at": "2022-01-05T00:00:00Z",
            "decided_by": "curator@example.org",
            "completed_at": "2022-01-05T01:00:00Z",
            "rationale": "Detailed sensitive historical explanation containing PII",
            "decision_basis": {
                "category": "factual-error",
                "target_canonical_id": "AUTOSAR/AP/record/diag-service",
                "target_version_id": "AUTOSAR/AP/record/diag-service@rel:R21-11#11223344",
                "target_content_hash": "11223344",
                "evidence_refs": [{"kind": "citation", "value": "internal doc"}],
            },
        }

        proof = rrr.redact_for_long_term_proof(old_item)
        self.assertEqual(proof["schema"], "curation-decision-proof@v1")
        self.assertEqual(proof["id"], old_item["id"])
        self.assertEqual(proof["retention_status"], "redacted_long_term_proof")
        self.assertNotIn("rationale", proof)
        self.assertNotIn("evidence_refs", proof["decision_summary"])
        self.assertEqual(proof["decision_summary"]["category"], "factual-error")
        self.assertEqual(proof["decision_summary"]["target_version_id"], "AUTOSAR/AP/record/diag-service@rel:R21-11#11223344")

    def test_evaluate_retention_dispositions(self):
        # 1. Active recent item (<120 days) -> retain_active
        recent_item = {
            "id": "item-1",
            "status": "open",
            "created": (self.fixed_now - timedelta(days=10)).isoformat(),
        }
        res = rrr.evaluate_item_retention(recent_item, as_of=self.fixed_now)
        self.assertEqual(res["disposition"], "retain_active")

        # 2. Unclaimed open item >120 days -> expire_unclaimed
        unclaimed_item = {
            "id": "item-2",
            "status": "open",
            "created": (self.fixed_now - timedelta(days=130)).isoformat(),
        }
        res = rrr.evaluate_item_retention(unclaimed_item, as_of=self.fixed_now)
        self.assertEqual(res["disposition"], "expire_unclaimed")

        # 3. Completed item >3 years (1095 days) but <10 years -> redact_raw_payload
        done_old_item = {
            "id": "item-3",
            "status": "completed",
            "created": (self.fixed_now - timedelta(days=1200)).isoformat(),
        }
        res = rrr.evaluate_item_retention(done_old_item, as_of=self.fixed_now)
        self.assertEqual(res["disposition"], "redact_raw_payload")

        # 4. Item >10 years (3650 days) -> dispose_proof
        ancient_item = {
            "id": "item-4",
            "status": "completed",
            "created": (self.fixed_now - timedelta(days=3700)).isoformat(),
        }
        res = rrr.evaluate_item_retention(ancient_item, as_of=self.fixed_now)
        self.assertEqual(res["disposition"], "dispose_proof")

        # 5. Legal hold item -> held
        held_item = {
            "id": "item-5",
            "status": "completed",
            "legal_hold": True,
            "created": (self.fixed_now - timedelta(days=4000)).isoformat(),
        }
        res = rrr.evaluate_item_retention(held_item, as_of=self.fixed_now)
        self.assertEqual(res["disposition"], "held")
        self.assertTrue(res["is_held"])

    def test_plan_and_apply_retention_gc(self):
        # Create fixtures in temporary queue
        # Open recent
        (self.open_dir / "recent.json").write_text(json.dumps({
            "id": "recent",
            "status": "open",
            "created": (self.fixed_now - timedelta(days=5)).isoformat(),
        }), encoding="utf-8")

        # Open expired (>120 days)
        (self.open_dir / "unclaimed_old.json").write_text(json.dumps({
            "id": "unclaimed_old",
            "status": "open",
            "created": (self.fixed_now - timedelta(days=150)).isoformat(),
        }), encoding="utf-8")

        # Done raw expired (>3 years)
        (self.done_dir / "done_3yr.json").write_text(json.dumps({
            "id": "done_3yr",
            "canonical_id": "test/record",
            "status": "completed",
            "outcome": "applied",
            "created": (self.fixed_now - timedelta(days=1200)).isoformat(),
            "rationale": "raw secret rationale",
            "decision_basis": {"category": "other"},
        }), encoding="utf-8")

        # Done ancient (>10 years)
        (self.done_dir / "done_10yr.json").write_text(json.dumps({
            "id": "done_10yr",
            "status": "completed",
            "created": (self.fixed_now - timedelta(days=3800)).isoformat(),
        }), encoding="utf-8")

        # 1. Test Plan
        plan = rrr.plan_queue_retention(queue_root=self.queue_root, as_of=self.fixed_now)
        self.assertEqual(plan["total_scanned"], 4)
        self.assertEqual(len(plan["retain_active"]), 1)
        self.assertEqual(len(plan["expire_unclaimed"]), 1)
        self.assertEqual(len(plan["redact_raw_payload"]), 1)
        self.assertEqual(len(plan["dispose_proof"]), 1)

        # 2. Test Apply (Dry-run first)
        res_dry = rrr.apply_queue_retention(queue_root=self.queue_root, as_of=self.fixed_now, dry_run=True)
        self.assertTrue(res_dry["dry_run"])
        self.assertEqual(len(res_dry["actions_performed"]), 0)
        self.assertTrue((self.open_dir / "unclaimed_old.json").exists())

        # 3. Test Apply (real apply)
        res_apply = rrr.apply_queue_retention(queue_root=self.queue_root, as_of=self.fixed_now, dry_run=False)
        self.assertFalse(res_apply["dry_run"])
        self.assertEqual(len(res_apply["actions_performed"]), 3)

        # Verify filesystem post-conditions
        # unclaimed_old moved to done/ with expired status
        self.assertFalse((self.open_dir / "unclaimed_old.json").exists())
        self.assertTrue((self.done_dir / "unclaimed_old.json").exists())
        expired_data = json.loads((self.done_dir / "unclaimed_old.json").read_text(encoding="utf-8"))
        self.assertEqual(expired_data["status"], "expired")
        self.assertEqual(expired_data["outcome"], "unclaimed_expired")

        # done_3yr redacted to proof
        self.assertTrue((self.done_dir / "done_3yr.json").exists())
        redacted_data = json.loads((self.done_dir / "done_3yr.json").read_text(encoding="utf-8"))
        self.assertEqual(redacted_data["schema"], "curation-decision-proof@v1")
        self.assertNotIn("rationale", redacted_data)

        # done_10yr deleted
        self.assertFalse((self.done_dir / "done_10yr.json").exists())


if __name__ == "__main__":
    unittest.main()
