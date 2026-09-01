#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_score_curator_decision.py -- End-to-end tests for Curator Decision UI & Durable Contract.

Covers Feature 0045 (Task 0045-05):
  - REQ-0045-04: Priority-gated Project Lead offer & award routing before downstream execution.
  - REQ-0045-07: Human curator review and decision interface with diff/baseline binding.
  - REQ-0045-09: Unvalidated candidate boundaries (never mutate facts or queues on arrival).
  - REQ-0045-10: Exact replay-safe decision key format decision:<proposal-id>:<revision>.
  - REQ-0045-13: Accessibility, progressive enhancement, and no-JS fallback support.
  - REQ-0045-14: Durable GitHub decision arrival envelope and stale baseline validation.
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
import curation_ingest as ci  # noqa: E402
import score_curation_views as scv  # noqa: E402


class ScoreCuratorDecisionContractTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._root = Path(self._tmpdir.name)

        # Queue redirection to test environment
        self._orig_queue = cf.QUEUE
        self._orig_open = cf.OPEN_DIR
        self._orig_claimed = cf.CLAIMED_DIR
        self._orig_done = cf.DONE_DIR
        cf.QUEUE = self._root / "curation-queue"
        cf.OPEN_DIR = cf.QUEUE / "open"
        cf.CLAIMED_DIR = cf.QUEUE / "claimed"
        cf.DONE_DIR = cf.QUEUE / "done"
        cf.OPEN_DIR.mkdir(parents=True, exist_ok=True)
        cf.CLAIMED_DIR.mkdir(parents=True, exist_ok=True)
        cf.DONE_DIR.mkdir(parents=True, exist_ok=True)

        self.sample_baseline_digest = "b2898d9c666ac86235875e3230c902908be44a2208c4085a0ec584b8a6e73692"
        self.sample_proposal_id = "proposal-score-norm-001"
        self.sample_envelope = {
            "schema": "curator-decision-envelope@v1",
            "contract_version": "v1.0.0",
            "decision_key": f"decision:{self.sample_proposal_id}:1",
            "proposal_id": self.sample_proposal_id,
            "proposal_revision": 1,
            "baseline_digest": self.sample_baseline_digest,
            "evidence_digest": "494662e83e3d4a1e0f97909437d5e09c2965413b500a047a8946ee711b486df7",
            "target_canonical_id": "ECLIPSE/S-CORE/process-doc/feat__feature_name",
            "curator": {
                "identity": "curator-jane-doe",
                "role": "Curator",
                "auth_mode": "github_authenticated",
                "auth_evidence": "gh-oauth-curator-token-verified",
            },
            "decision": {
                "outcome": "accept",
                "rationale": "Verified architecture documentation collision fix against source locator lines 428-454.",
                "decided_at": "2026-09-01T12:00:00Z",
                "revision_instructions": None,
                "conditions": [],
            },
            "routing": {
                "requires_pl_offer": True,
                "downstream_recipe": "curator_decision_routing",
                "status": "pending_safe_routing",
            },
        }

    def tearDown(self):
        cf.QUEUE = self._orig_queue
        cf.OPEN_DIR = self._orig_open
        cf.CLAIMED_DIR = self._orig_claimed
        cf.DONE_DIR = self._orig_done
        self._tmpdir.cleanup()

    def test_valid_curator_envelope_accept(self):
        """Test accepting a valid curator decision arrival envelope."""
        env_file = self._root / "decision.json"
        env_file.write_text(json.dumps(self.sample_envelope), encoding="utf-8")

        result = ci.ingest(env_file, apply=True, from_issue_body=False)
        self.assertEqual(result["schema"], "curator-decision-envelope@v1")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["decision_key"], f"decision:{self.sample_proposal_id}:1")
        self.assertEqual(result["outcome"], "accept")
        self.assertTrue(result["routing"]["pl_offer_required"])
        self.assertEqual(len(result["fehler"]), 0)

    def test_valid_curator_envelope_reject_and_revision(self):
        """Test reject and request_revision outcomes."""
        for outcome in ("reject", "request_revision"):
            env = copy.deepcopy(self.sample_envelope)
            env["decision"]["outcome"] = outcome
            env["decision_key"] = f"decision:{self.sample_proposal_id}:2"
            env_file = self._root / f"decision_{outcome}.json"
            env_file.write_text(json.dumps(env), encoding="utf-8")

            result = ci.ingest(env_file, apply=False, from_issue_body=False)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["outcome"], outcome)
            self.assertEqual(len(result["fehler"]), 0)

    def test_stale_baseline_digest_rejection(self):
        """Test that a decision bound to an obsolete baseline is rejected fail-closed."""
        env = copy.deepcopy(self.sample_envelope)
        env["baseline_digest"] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"

        errors, warnings = ci.validate_curator_envelope(
            env, current_baseline_digest=self.sample_baseline_digest
        )
        self.assertTrue(any("stale" in e for e in errors))

    def test_invalid_decision_key_rejection(self):
        """Test that non-conforming decision_key formats are rejected."""
        env = copy.deepcopy(self.sample_envelope)
        env["decision_key"] = "invalid-key-format"

        errors, warnings = ci.validate_curator_envelope(env)
        self.assertTrue(any("decision_key" in e for e in errors))

    def test_missing_curator_identity_or_rationale(self):
        """Test fail-closed rejection on missing identity or rationale."""
        env = copy.deepcopy(self.sample_envelope)
        env["curator"]["identity"] = ""
        errors, _ = ci.validate_curator_envelope(env)
        self.assertTrue(any("identity" in e for e in errors))

        env = copy.deepcopy(self.sample_envelope)
        env["decision"]["rationale"] = "   "
        errors, _ = ci.validate_curator_envelope(env)
        self.assertTrue(any("rationale" in e for e in errors))

    def test_arrival_check_does_not_mutate_canonical_state(self):
        """Arrival check validates routing envelope without altering canonical records or queues."""
        open_items_before = list(cf.OPEN_DIR.glob("*.json"))
        env_file = self._root / "decision.json"
        env_file.write_text(json.dumps(self.sample_envelope), encoding="utf-8")

        result = ci.ingest(env_file, apply=True, from_issue_body=False)
        self.assertEqual(result["status"], "ok")

        open_items_after = list(cf.OPEN_DIR.glob("*.json"))
        self.assertEqual(open_items_before, open_items_after)

    def test_html_rendering_accessibility_and_no_js(self):
        """Test that the curator decision HTML page includes accessible form, diff, and no-JS markup."""
        proposal = {
            "id": self.sample_proposal_id,
            "diff": "--- a/spec/test.rst\n+++ b/spec/test.rst\n@@ -1 +1 @@\n-old\n+new",
            "evidence_digest": "494662e83e3d4a1e0f97909437d5e09c2965413b500a047a8946ee711b486df7",
            "chat_history": [{"sender": "curator", "text": "Please check collision."}],
        }
        baseline = {"digest": self.sample_baseline_digest}

        rendered_html = scv.render_curator_decision_page(proposal, baseline)
        self.assertIn("S-Core Curator Decision Console", rendered_html)
        self.assertIn(self.sample_proposal_id, rendered_html)
        self.assertIn(self.sample_baseline_digest, rendered_html)
        self.assertIn('role="region"', rendered_html)
        self.assertIn('aria-label="Curator Decision Form"', rendered_html)
        self.assertIn('role="status"', rendered_html)
        self.assertIn('aria-live="polite"', rendered_html)
        self.assertIn('method="POST"', rendered_html)  # No-JS semantic form
        self.assertIn('action="/curator/decision"', rendered_html)
        self.assertIn("score_curator.js", rendered_html)
        self.assertIn(scv.UNVALIDATED_MARKER, rendered_html)


if __name__ == "__main__":
    unittest.main()
