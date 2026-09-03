#!/usr/bin/env python3
"""Tests for Task 0037-43: Integration policy gate verifier."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "issue_integration_policy", ROOT / "_src/tools/issue_integration_policy.py"
)
POL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(POL)


class IssueIntegrationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def _write_workflow(self, profile="issue-store", epoch="2026-09-03", single_auth=True):
        wf = {
            "schema": "agent-workflow@v1",
            "selected_profile": profile,
            "authority_epoch": epoch,
            "single_authority": single_auth,
        }
        wf_path = self.root / "agent-workflow.json"
        wf_path.write_text(json.dumps(wf), encoding="utf-8")
        return wf_path

    def test_conforming_issue_store_change_passes(self):
        self._write_workflow(profile="issue-store")
        issue_dir = self.root / "issues" / "0037" / "0037-43"
        issue_dir.mkdir(parents=True)
        (issue_dir / "index.md").write_text("---\nid: '0037-43'\nstate: 'open'\n---\n", encoding="utf-8")

        res = POL.evaluate_integration_policy(self.root)
        self.assertEqual(res["status"], "passed")
        self.assertEqual(res["violations_count"], 0)

    def test_direct_todo_done_modification_rejected_under_issue_store(self):
        self._write_workflow(profile="issue-store")
        (self.root / "TODO.md").write_text("# Legacy TODO", encoding="utf-8")

        with self.assertRaises(POL.IntegrationPolicyViolation) as ctx:
            POL.evaluate_integration_policy(self.root, enforce_rules=True)
        self.assertEqual(ctx.exception.code, "POLICY-PROHIBITED-GENERATED-EDIT")

        # Via non-raising evaluation
        res = POL.evaluate_integration_policy(self.root, enforce_rules=False)
        self.assertEqual(res["status"], "rejected")
        self.assertTrue(any(v["code"] == "POLICY-PROHIBITED-GENERATED-EDIT" for v in res["violations"]))

    def test_legacy_claim_rejected_under_issue_store(self):
        self._write_workflow(profile="issue-store")
        (self.root / "TODO-worf-legacy-claim.md").write_text("# Claim", encoding="utf-8")

        res = POL.evaluate_integration_policy(self.root, enforce_rules=False)
        self.assertEqual(res["status"], "rejected")
        self.assertTrue(any(v["code"] == "POLICY-LEGACY-CLAIM-PROHIBITED" for v in res["violations"]))

    def test_conforming_legacy_change_allowed_under_legacy_profile(self):
        self._write_workflow(profile="legacy-lists")
        (self.root / "TODO.md").write_text("# Legacy TODO", encoding="utf-8")
        (self.root / "TODO-worf-legacy.md").write_text("# Claim", encoding="utf-8")

        res = POL.evaluate_integration_policy(self.root, enforce_rules=True)
        self.assertEqual(res["status"], "passed")
        self.assertEqual(res["violations_count"], 0)


if __name__ == "__main__":
    unittest.main()
