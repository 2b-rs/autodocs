#!/usr/bin/env python3
"""Tests for Task 0037-42: agent_bootstrap_boundary protocol negotiation and client tuples."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "agent_bootstrap_boundary", ROOT / "_src/tools/agent_bootstrap_boundary.py"
)
BND = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BND)


class AgentBootstrapBoundaryTests(unittest.TestCase):
    def test_current_protocol_negotiation(self):
        res = BND.negotiate_protocol("2025-06-18")
        self.assertEqual(res["protocol_version"], "2025-06-18")
        self.assertFalse(res["is_stale"])
        self.assertFalse(res["is_deprecated"])
        self.assertIn("assignment_transition", res["available_tools"])

    def test_stale_protocol_negotiation(self):
        res = BND.negotiate_protocol("2025-03-26")
        self.assertEqual(res["protocol_version"], "2025-03-26")
        self.assertTrue(res["is_stale"])
        self.assertFalse(res["is_deprecated"])

    def test_deprecated_protocol_negotiation(self):
        res = BND.negotiate_protocol("2024-11-05")
        self.assertEqual(res["protocol_version"], "2024-11-05")
        self.assertTrue(res["is_stale"])
        self.assertTrue(res["is_deprecated"])

    def test_missing_or_unsupported_protocol_fails_closed(self):
        with self.assertRaises(BND.BootstrapCompatibilityError) as ctx:
            BND.negotiate_protocol(None)
        self.assertEqual(ctx.exception.code, "MISSING-PROTOCOL-VERSION")

        with self.assertRaises(BND.BootstrapCompatibilityError) as ctx:
            BND.negotiate_protocol("")
        self.assertEqual(ctx.exception.code, "MISSING-PROTOCOL-VERSION")

        with self.assertRaises(BND.BootstrapCompatibilityError) as ctx:
            BND.negotiate_protocol("unknown-proto-999")
        self.assertEqual(ctx.exception.code, "UNSUPPORTED-PROTOCOL-VERSION")

    def test_client_bootstrap_validation(self):
        # Valid client v1.2.0 on proto 2025-06-18
        valid_client = {
            "name": "agent-worf",
            "version": "1.2.0",
            "protocolVersion": "2025-06-18",
        }
        res = BND.validate_client_bootstrap(valid_client)
        self.assertEqual(res["status"], "accepted")
        self.assertEqual(res["client"]["name"], "agent-worf")

        # Valid legacy client v0.9.0 on proto 2024-11-05
        legacy_client = {
            "name": "legacy-agent",
            "version": "0.9.0",
            "protocolVersion": "2024-11-05",
        }
        res_leg = BND.validate_client_bootstrap(legacy_client)
        self.assertEqual(res_leg["status"], "accepted")

        # Missing / bogus client payloads fail closed
        with self.assertRaises(BND.BootstrapCompatibilityError) as ctx:
            BND.validate_client_bootstrap({})
        self.assertEqual(ctx.exception.code, "MISSING-CLIENT-NAME")

        with self.assertRaises(BND.BootstrapCompatibilityError) as ctx:
            BND.validate_client_bootstrap({"name": "unknown", "version": "1.0.0", "protocolVersion": "2025-06-18"})
        self.assertEqual(ctx.exception.code, "MISSING-CLIENT-NAME")

        with self.assertRaises(BND.BootstrapCompatibilityError) as ctx:
            BND.validate_client_bootstrap({"name": "test-agent", "version": "0.0.0", "protocolVersion": "2025-06-18"})
        self.assertEqual(ctx.exception.code, "INVALID-CLIENT-VERSION")

        with self.assertRaises(BND.BootstrapCompatibilityError) as ctx:
            BND.validate_client_bootstrap({"name": "test-agent", "version": "bogus", "protocolVersion": "2025-06-18"})
        self.assertEqual(ctx.exception.code, "INVALID-CLIENT-VERSION")

        with self.assertRaises(BND.BootstrapCompatibilityError) as ctx:
            BND.validate_client_bootstrap({"name": "test-agent", "version": "1", "protocolVersion": "2025-06-18"})
        self.assertEqual(ctx.exception.code, "INVALID-CLIENT-VERSION")

        # Incompatible (client_version, protocol) tuple
        with self.assertRaises(BND.BootstrapCompatibilityError) as ctx:
            BND.validate_client_bootstrap({"name": "test-agent", "version": "0.1.0", "protocolVersion": "2025-06-18"})
        self.assertEqual(ctx.exception.code, "INCOMPATIBLE-CLIENT-PROTOCOL-TUPLE")

        with self.assertRaises(BND.BootstrapCompatibilityError) as ctx:
            BND.validate_client_bootstrap({"name": "test-agent", "version": "1.0.0", "protocolVersion": "2024-11-05"})
        self.assertEqual(ctx.exception.code, "INCOMPATIBLE-CLIENT-PROTOCOL-TUPLE")

    def test_cli_client_handshake_invocation(self):
        tool_script = str(ROOT / "_src/tools/agent_bootstrap_boundary.py")

        # 1. Valid client handshake JSON exit 0
        proc_ok = subprocess.run(
            [sys.executable, tool_script, "--client-json", '{"name":"agent-worf","version":"1.0.0","protocolVersion":"2025-06-18"}'],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc_ok.returncode, 0)
        self.assertIn("ACCEPTED", proc_ok.stdout)

        # 2. Bogus client handshake JSON exit 1
        proc_err = subprocess.run(
            [sys.executable, tool_script, "--client-json", '{"name":"agent-worf","version":"bogus","protocolVersion":"2025-06-18"}'],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc_err.returncode, 1)

        # 3. Incompatible client tuple JSON mode exit 1
        proc_tuple_err = subprocess.run(
            [sys.executable, tool_script, "--client-json", '{"name":"agent-worf","version":"1.0.0","protocolVersion":"2024-11-05"}', "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc_tuple_err.returncode, 1)
        data = json.loads(proc_tuple_err.stdout)
        self.assertEqual(data["status"], "rejected")
        self.assertEqual(data["error_code"], "INCOMPATIBLE-CLIENT-PROTOCOL-TUPLE")


if __name__ == "__main__":
    unittest.main()
