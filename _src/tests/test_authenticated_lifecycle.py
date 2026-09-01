#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for authenticated_lifecycle.py (Task 0033-07.01 / RRB-AUTH-001)."""

import sys
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import authenticated_lifecycle as al


class TestAuthenticatedLifecycle(unittest.TestCase):
    def setUp(self):
        self.item = {
            "id": "RR-20260901-001",
            "version": "1.0",
            "status": "queued",
            "lifecycle_state": "queued",
            "history": [],
        }

    def test_anonymous_transition_rejected(self):
        with self.assertRaises(al.AuthorizationError) as ctx:
            al.validate_transition(self.item, "claim", auth=None)
        self.assertIn("Anonymous", str(ctx.exception))

    def test_invalid_role_rejected(self):
        with self.assertRaises(al.AuthorizationError) as ctx:
            al.create_session("bad_actor", "superadmin")
        self.assertIn("Invalid role", str(ctx.exception))

    def test_empty_principal_rejected(self):
        with self.assertRaises(al.AuthorizationError):
            al.create_session("   ", "curator")

    def test_ai_agent_cannot_accept_or_reject_or_apply(self):
        ai_auth = al.create_session("agent-deepspace-1", "ai_agent")
        
        # AI can claim
        claimed = al.validate_transition(self.item, "claim", ai_auth)
        self.assertEqual(claimed["status"], "claimed")
        self.assertEqual(claimed["claimed_by"], "agent-deepspace-1")

        # AI can propose
        proposed = al.validate_transition(claimed, "propose", ai_auth)
        self.assertEqual(proposed["status"], "proposed")

        # AI cannot accept
        with self.assertRaises(al.AuthorizationError) as ctx:
            al.validate_transition(proposed, "accept", ai_auth)
        self.assertIn("not authorized", str(ctx.exception))

        # AI cannot reject
        with self.assertRaises(al.AuthorizationError) as ctx:
            al.validate_transition(proposed, "reject", ai_auth)
        self.assertIn("not authorized", str(ctx.exception))

        # AI cannot apply
        with self.assertRaises(al.AuthorizationError) as ctx:
            al.validate_transition(proposed, "apply", ai_auth)
        self.assertIn("not authorized", str(ctx.exception))

    def test_requester_cannot_claim_or_accept(self):
        req_auth = al.create_session("browser-user-42", "requester")
        with self.assertRaises(al.AuthorizationError) as ctx:
            al.validate_transition(self.item, "claim", req_auth)
        self.assertIn("not authorized", str(ctx.exception))

    def test_curator_can_accept_and_reject(self):
        ai_auth = al.create_session("agent-1", "ai_agent")
        curator_auth = al.create_session("curator-jadzia", "curator")

        claimed = al.validate_transition(self.item, "claim", ai_auth)
        proposed = al.validate_transition(claimed, "propose", ai_auth)

        # Curator accepts
        accepted = al.validate_transition(proposed, "accept", curator_auth)
        self.assertEqual(accepted["status"], "accepted")
        self.assertEqual(accepted["outcome"], "accepted")
        self.assertEqual(accepted["decided_by"], "curator-jadzia")
        self.assertEqual(len(accepted["history"]), 3)

    def test_rejection_is_terminal_and_cannot_apply(self):
        ai_auth = al.create_session("agent-1", "ai_agent")
        curator_auth = al.create_session("curator-jadzia", "curator")
        operator_auth = al.create_session("operator-sisko", "operator")

        claimed = al.validate_transition(self.item, "claim", ai_auth)
        proposed = al.validate_transition(claimed, "propose", ai_auth)
        rejected = al.validate_transition(proposed, "reject", curator_auth)

        self.assertEqual(rejected["status"], "rejected")
        self.assertEqual(rejected["outcome"], "rejected")

        # Rejection cannot transition to applied
        with self.assertRaises(al.AuthorizationError):
            al.validate_transition(rejected, "apply", operator_auth)

    def test_operator_full_lifecycle(self):
        ai_auth = al.create_session("agent-1", "ai_agent")
        curator_auth = al.create_session("curator-1", "curator")
        op_auth = al.create_session("operator-1", "operator")

        claimed = al.validate_transition(self.item, "claim", ai_auth)
        proposed = al.validate_transition(claimed, "propose", ai_auth)
        accepted = al.validate_transition(proposed, "accept", curator_auth)
        applied = al.validate_transition(accepted, "apply", op_auth)
        self.assertEqual(applied["status"], "applied")

        closed = al.validate_transition(applied, "close", op_auth)
        self.assertEqual(closed["status"], "closed")

    def test_stale_version_rejected(self):
        ai_auth = al.create_session("agent-1", "ai_agent")
        with self.assertRaises(al.AuthorizationError) as ctx:
            al.validate_transition(self.item, "claim", ai_auth, expected_version="2.0")
        self.assertIn("Stale version", str(ctx.exception))

    def test_out_of_order_apply_before_accept_rejected(self):
        op_auth = al.create_session("operator-1", "operator")
        with self.assertRaises(al.AuthorizationError) as ctx:
            al.validate_transition(self.item, "apply", op_auth)
        self.assertIn("Invalid transition", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
