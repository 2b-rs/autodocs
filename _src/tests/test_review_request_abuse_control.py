#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_review_request_abuse_control.py -- Test suite for abuse, quota, quarantine, moderation, and escalation controls (0033-07.04)."""

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import authenticated_lifecycle as al  # noqa: E402
import curation_flags as cf  # noqa: E402
import review_request_abuse_control as rrac  # noqa: E402
import review_request_ingest as rri  # noqa: E402
import review_request_package as rrp  # noqa: E402


class TestURLSecurity(unittest.TestCase):
    def test_valid_https_url(self):
        ok, err = rrac.validate_evidence_url("https://standards.autosar.org/spec/R25-11/tsync.html")
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_reject_http_scheme(self):
        ok, err = rrac.validate_evidence_url("http://standards.autosar.org/spec/tsync.html")
        self.assertFalse(ok)
        self.assertIn("must use 'https://'", err)

    def test_reject_javascript_and_data_schemes(self):
        ok, err = rrac.validate_evidence_url("javascript:alert(1)")
        self.assertFalse(ok)
        ok, err = rrac.validate_evidence_url("data:text/html,<script>alert(1)</script>")
        self.assertFalse(ok)

    def test_reject_localhost_and_loopback(self):
        for host in ["localhost", "127.0.0.1", "[::1]", "sub.localhost", "app.local"]:
            ok, err = rrac.validate_evidence_url(f"https://{host}/secret")
            self.assertFalse(ok, f"Failed to reject {host}")
            self.assertIn("private or loopback", err)

    def test_reject_private_rfc1918_networks(self):
        for ip in ["10.0.1.5", "192.168.1.1", "172.16.0.50", "169.254.169.254"]:
            ok, err = rrac.validate_evidence_url(f"https://{ip}/metadata")
            self.assertFalse(ok, f"Failed to reject private IP {ip}")
            self.assertIn("private or loopback", err)

    def test_reject_embedded_credentials(self):
        ok, err = rrac.validate_evidence_url("https://user:password@example.org/spec")
        self.assertFalse(ok)
        self.assertIn("contains credentials", err)

    def test_reject_dangerous_executable_extensions(self):
        for ext in [".exe", ".sh", ".bat", ".dll", ".ps1"]:
            ok, err = rrac.validate_evidence_url(f"https://example.org/payload{ext}")
            self.assertFalse(ok, f"Failed to reject extension {ext}")
            self.assertIn("dangerous executable", err)

    def test_validate_all_evidence_urls_in_package(self):
        pkg = {
            "evidence_url": "http://insecure.org",
            "evidence_refs": [
                {"kind": "url", "value": "https://127.0.0.1/admin"},
                {"kind": "citation", "value": "Valid citation"},
            ],
        }
        errors = rrac.validate_all_evidence_urls(pkg)
        self.assertEqual(len(errors), 2)


class TestContentModeration(unittest.TestCase):
    def test_clean_text_passes(self):
        flagged, cat, reason = rrac.scan_text_for_abuse("This section needs clarification on monotonic clocks.")
        self.assertFalse(flagged)
        self.assertIsNone(cat)

    def test_detect_github_token_leak(self):
        token = "ghp_" + "A" * 36
        flagged, cat, reason = rrac.scan_text_for_abuse(f"Here is my auth header: bearer {token}")
        self.assertTrue(flagged)
        self.assertEqual(cat, "credential_leak")

    def test_detect_aws_key_leak(self):
        flagged, cat, reason = rrac.scan_text_for_abuse("Key is AKIAIOSFODNN7EXAMPLE")
        self.assertTrue(flagged)
        self.assertEqual(cat, "credential_leak")

    def test_detect_private_key_leak(self):
        flagged, cat, reason = rrac.scan_text_for_abuse("-----BEGIN RSA PRIVATE KEY-----\nMIIEowI...")
        self.assertTrue(flagged)
        self.assertEqual(cat, "credential_leak")

    def test_detect_xss_script_injection(self):
        flagged, cat, reason = rrac.scan_text_for_abuse("Description <script>alert(document.cookie)</script>")
        self.assertTrue(flagged)
        self.assertEqual(cat, "content_abuse")

    def test_detect_prohibited_sensitive_phrase(self):
        flagged, cat, reason = rrac.scan_text_for_abuse("Please commit suicide immediately")
        self.assertTrue(flagged)
        self.assertEqual(cat, "content_abuse")

    def test_check_package_content_moderation(self):
        pkg = {
            "rationale": "Legitimate rationale",
            "evidence_refs": [
                {"kind": "url", "value": "https://example.org", "note": "Leak: ghp_" + "B" * 36}
            ],
        }
        flagged, cat, reason = rrac.check_package_content_moderation(pkg)
        self.assertTrue(flagged)
        self.assertEqual(cat, "credential_leak")


class TestRateLimitingAndBurstQuotas(unittest.TestCase):
    def setUp(self):
        self.controller = rrac.AbuseController(
            window_seconds=60,
            max_requests_per_window=5,
            burst_threshold=3,
            burst_seconds=5,
            suspension_hours=24,
            recovery_floor_hours=1,
        )

    def test_normal_requests_within_limits(self):
        base_time = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
        for i in range(3):
            t = base_time + timedelta(seconds=i * 10)
            allowed, code, msg = self.controller.check_and_record_request("user1", "target1", now=t)
            self.assertTrue(allowed)
            self.assertEqual(code, "ok")

    def test_burst_flood_triggers_suspension(self):
        base_time = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
        # 3 requests in 2 seconds
        for i in range(3):
            t = base_time + timedelta(seconds=i)
            self.controller.check_and_record_request("spammer1", "target1", now=t)

        # 4th request within burst window triggers burst flood suspension
        t_burst = base_time + timedelta(seconds=3)
        allowed, code, msg = self.controller.check_and_record_request("spammer1", "target1", now=t_burst)
        self.assertFalse(allowed)
        self.assertEqual(code, "burst_flooding")

        # Subsequent request is suspended
        t_next = base_time + timedelta(minutes=10)
        allowed, code, msg = self.controller.check_and_record_request("spammer1", "target1", now=t_next)
        self.assertFalse(allowed)
        self.assertEqual(code, "suspended")

    def test_manual_recovery_floor_enforcement(self):
        base_time = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
        # Trigger suspension
        for i in range(4):
            self.controller.check_and_record_request("spammer2", "target1", now=base_time + timedelta(seconds=i))

        moderator_auth = al.create_session("mod-security-1", "moderator")
        
        # Try to lift suspension after 30 minutes (before 1-hour floor)
        t_early = base_time + timedelta(minutes=30)
        ok, msg = self.controller.manual_lift_suspension("spammer2", moderator_auth, now=t_early, force=False)
        self.assertFalse(ok)
        self.assertIn("recovery floor", msg)

        # Lift suspension with emergency force override
        ok, msg = self.controller.manual_lift_suspension("spammer2", moderator_auth, now=t_early, force=True)
        self.assertTrue(ok)
        self.assertIn("Suspension lifted", msg)

    def test_unauthorized_role_cannot_lift_suspension(self):
        ai_auth = al.create_session("agent-1", "ai_agent")
        ok, msg = self.controller.manual_lift_suspension("spammer2", ai_auth)
        self.assertFalse(ok)
        self.assertIn("not authorized", msg)


class TestQuarantineAndModerationControls(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._root = Path(self._tmpdir.name)
        self._q_dir = self._root / "quarantine"
        self._m_dir = self._root / "moderation_audit"
        self._o_dir = self._root / "open"
        self._q_dir.mkdir(parents=True, exist_ok=True)
        self._m_dir.mkdir(parents=True, exist_ok=True)
        self._o_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_quarantine_writing_and_retrieval(self):
        payload = {
            "id": "review-request:bad-payload-01",
            "target_canonical_id": "AUTOSAR/AP/record/tsync-user-guide",
            "rationale": "Malicious probe <script>alert(1)</script>",
        }
        path = rrac.write_quarantine_item(
            package_or_payload=payload,
            reason="XSS injection attempt",
            category="content_abuse",
            origin_id="attacker-42",
            queue_root=self._root,
        )
        self.assertTrue(path.exists())
        self.assertEqual(path.parent, self._q_dir)

        # Retrieve
        item = rrac.get_quarantined_item("review-request:bad-payload-01", queue_root=self._root)
        self.assertIsNotNone(item)
        assert item is not None
        self.assertEqual(item["status"], "quarantined")
        self.assertEqual(item["category"], "content_abuse")
        self.assertEqual(item["reason"], "XSS injection attempt")
        self.assertEqual(item["origin_hash"], rrac.hash_origin("attacker-42"))

    def test_moderator_release_workflow(self):
        payload = {
            "id": "review-request:false-positive-01",
            "canonical_id": "AUTOSAR/AP/record/tsync-user-guide",
            "item_kind": "review-request",
            "origin": "browser",
            "status": "open",
            "rationale": "False positive trigger word in valid context",
            "decision_basis": {},
            "actor_claim": {"claimed_actor": "submitter_bob"},
        }
        rrac.write_quarantine_item(
            package_or_payload=payload,
            reason="False positive flag",
            origin_id="submitter_bob",
            queue_root=self._root,
        )

        moderator_auth = al.create_session("mod-alice", "moderator")
        ok, msg, res_path = rrac.moderate_quarantine_action(
            item_id="review-request:false-positive-01",
            action="release",
            moderator_auth=moderator_auth,
            reason="Reviewed and verified as false positive",
            queue_root=self._root,
        )
        self.assertTrue(ok)
        self.assertTrue(Path(res_path).exists())
        self.assertEqual(Path(res_path).parent, self._o_dir)

        # Quarantine item should be unlinked
        self.assertIsNone(rrac.get_quarantined_item("review-request:false-positive-01", queue_root=self._root))

    def test_4eyes_submitter_cannot_self_release(self):
        payload = {
            "id": "review-request:self-appeal-01",
            "rationale": "Suspicious request",
            "actor_claim": {"claimed_actor": "moderator_charlie"},
        }
        rrac.write_quarantine_item(
            package_or_payload=payload,
            reason="Suspicious pattern",
            origin_id="moderator_charlie",
            queue_root=self._root,
        )

        moderator_auth = al.create_session("moderator_charlie", "moderator")
        ok, msg, _ = rrac.moderate_quarantine_action(
            item_id="review-request:self-appeal-01",
            action="release",
            moderator_auth=moderator_auth,
            reason="Self release attempt",
            queue_root=self._root,
        )
        self.assertFalse(ok)
        self.assertIn("4-Eyes Violation", msg)

    def test_moderator_refuse_and_escalate(self):
        payload = {
            "id": "review-request:malicious-02",
            "rationale": "Doxxing threat",
        }
        rrac.write_quarantine_item(
            package_or_payload=payload,
            reason="Harassment pattern",
            queue_root=self._root,
        )

        moderator_auth = al.create_session("mod-dan", "moderator")
        
        # Escalate
        ok, msg, _ = rrac.moderate_quarantine_action(
            item_id="review-request:malicious-02",
            action="escalate",
            moderator_auth=moderator_auth,
            reason="Escalated to legal review",
            target_group="legal_counsel",
            queue_root=self._root,
        )
        self.assertTrue(ok)
        item = rrac.get_quarantined_item("review-request:malicious-02", queue_root=self._root)
        self.assertEqual(item["status"], "escalated")
        self.assertEqual(item["escalation_target"], "legal_counsel")

        # Refuse
        ok, msg, _ = rrac.moderate_quarantine_action(
            item_id="review-request:malicious-02",
            action="refuse",
            moderator_auth=moderator_auth,
            reason="Confirmed policy violation",
            queue_root=self._root,
        )
        self.assertTrue(ok)
        item = rrac.get_quarantined_item("review-request:malicious-02", queue_root=self._root)
        self.assertEqual(item["status"], "refused")


class TestIngestBoundaryAbuseIntegration(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._root = Path(self._tmpdir.name)
        self._records_dir = self._root / "records"
        self._versions_dir = self._root / "versions"
        self._records_dir.mkdir(parents=True, exist_ok=True)
        self._versions_dir.mkdir(parents=True, exist_ok=True)
        
        # Seed record
        rec_dir = self._records_dir / "AUTOSAR" / "AP" / "record"
        rec_dir.mkdir(parents=True, exist_ok=True)
        rec_data = {
            "id": "tsync-user-guide",
            "canonical_id": "AUTOSAR/AP/record/tsync-user-guide",
            "status": {"state": "valid/published"},
            "version_id": "AUTOSAR/AP/record/tsync-user-guide@rel:R25-11#3f9a21bc",
            "content_hash": "3f9a21bc",
        }
        (rec_dir / "tsync-user-guide.json").write_text(json.dumps(rec_data), encoding="utf-8")

        rri.reset_replay_tracker()
        rrac.reset_abuse_controller()

    def tearDown(self):
        rri.reset_replay_tracker()
        rrac.reset_abuse_controller()
        self._tmpdir.cleanup()

    def test_ingest_quarantines_prohibited_url(self):
        req_id = rrp.new_request_id()
        pkg = {
            "schema": "review-request-package@v1",
            "client_schema_version": "1.0.0",
            "request_id": req_id,
            "target_canonical_id": "AUTOSAR/AP/record/tsync-user-guide",
            "target_version_id": "AUTOSAR/AP/record/tsync-user-guide@rel:R25-11#3f9a21bc",
            "target_content_hash": "3f9a21bc",
            "target_status_snapshot": "valid/published",
            "source_url": "https://standards.autosar.org/spec/tsync.html",
            "category": "ai-hallucination-suspected",
            "rationale": "Valid rationale text",
            "evidence_refs": [
                {"kind": "url", "value": "http://127.0.0.1:8080/internal-exploit"}
            ],
            "actor_claim": {"display_name": "attacker", "identity_kind": "github_authenticated"},
            "transport": "github_issue",
            "created_at": "2026-09-01T12:00:00Z",
        }
        report = rri.ingest(
            pkg,
            apply=True,
            authoritative_actor="attacker",
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            queue_root=self._root,
        )
        self.assertEqual(report["outcome"], rri.IngestOutcome.QUARANTINED)
        self.assertIn("must use 'https://'", report["errors"][0])
        self.assertTrue(Path(report["path"]).exists())
        self.assertEqual(Path(report["path"]).parent, self._root / "quarantine")

    def test_ingest_quarantines_secret_token_leak(self):
        req_id = rrp.new_request_id()
        pkg = {
            "schema": "review-request-package@v1",
            "client_schema_version": "1.0.0",
            "request_id": req_id,
            "target_canonical_id": "AUTOSAR/AP/record/tsync-user-guide",
            "target_version_id": "AUTOSAR/AP/record/tsync-user-guide@rel:R25-11#3f9a21bc",
            "target_content_hash": "3f9a21bc",
            "target_status_snapshot": "valid/published",
            "source_url": "https://standards.autosar.org/spec/tsync.html",
            "category": "ai-hallucination-suspected",
            "rationale": "I found a problem using token ghp_" + "X" * 36,
            "evidence_refs": [],
            "actor_claim": {"display_name": "dev_user", "identity_kind": "github_authenticated"},
            "transport": "github_issue",
            "created_at": "2026-09-01T12:00:00Z",
        }
        report = rri.ingest(
            pkg,
            apply=True,
            authoritative_actor="dev_user",
            records_root=self._records_dir,
            versions_root=self._versions_dir,
            queue_root=self._root,
        )
        self.assertEqual(report["outcome"], rri.IngestOutcome.QUARANTINED)
        self.assertIn("credential_leak", report["errors"][0])


if __name__ == "__main__":
    unittest.main()
