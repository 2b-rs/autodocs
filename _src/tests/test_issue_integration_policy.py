#!/usr/bin/env python3
"""Tests for Task 0037-43: Integration policy gate verifier."""
from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import subprocess
import sys
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
        self._install_bundle("legacy")
        self._install_bundle("future")

    def _install_bundle(self, profile: str) -> None:
        src = ROOT / f"docs/pipeline/agent-instructions/{profile}/index.md"
        dest = self.root / f"docs/pipeline/agent-instructions/{profile}/index.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    def _write_selector(
        self,
        profile="legacy-lists",
        epoch="legacy-writable",
        phase="legacy-writable",
        schema="agent-workflow-bootstrap@v1",
        repair_digest=True,
    ):
        bundle_path = f"docs/pipeline/agent-instructions/{'legacy' if profile == 'legacy-lists' else 'future'}/index.md"
        wf = {
            "schema": schema,
            "workflow_version": "1.0.0",
            "authority_epoch": epoch,
            "authority_profile": profile,
            "write_phase": phase,
            "required_capability": "unprivileged",
            "instruction_bundle": bundle_path,
        }
        if schema == "agent-workflow-bootstrap@v1":
            wf["runner_protocol"] = "runner-request@v1"
        else:
            wf["execution_model"] = "direct"

        if repair_digest:
            wf["selector_digest"] = POL.compute_selector_digest(wf)
        else:
            wf["selector_digest"] = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

        wf_path = self.root / "agent-workflow.json"
        wf_path.write_text(json.dumps(wf, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        return wf_path

    def test_conforming_legacy_change_passes(self):
        self._write_selector(profile="legacy-lists")
        (self.root / "TODO.md").write_text("# Legacy TODO", encoding="utf-8")
        (self.root / "TODO-worf-claim.md").write_text("# Claim", encoding="utf-8")

        res = POL.evaluate_integration_policy(self.root, changed_files=["TODO.md", "TODO-worf-claim.md"], enforce_rules=True)
        self.assertEqual(res["status"], "passed")
        self.assertEqual(res["violations_count"], 0)
        self.assertEqual(res["authority_profile"], "legacy-lists")

    def test_conforming_issue_store_change_passes(self):
        self._write_selector(profile="issue-store", epoch="issue-store-writable", phase="issue-store-writable", schema="agent-workflow-bootstrap@v2")
        issue_dir = self.root / "issues" / "0037" / "0037-43"
        issue_dir.mkdir(parents=True)
        (issue_dir / "index.md").write_text("---\nid: '0037-43'\nstate: 'open'\n---\n", encoding="utf-8")

        res = POL.evaluate_integration_policy(self.root, changed_files=["issues/0037/0037-43/index.md"], enforce_rules=True)
        self.assertEqual(res["status"], "passed")
        self.assertEqual(res["violations_count"], 0)
        self.assertEqual(res["authority_profile"], "issue-store")

    def test_direct_todo_done_modification_rejected_under_issue_store(self):
        self._write_selector(profile="issue-store", epoch="issue-store-writable", phase="issue-store-writable", schema="agent-workflow-bootstrap@v2")
        (self.root / "TODO.md").write_text("# Legacy TODO", encoding="utf-8")

        with self.assertRaises(POL.IntegrationPolicyViolation) as ctx:
            POL.evaluate_integration_policy(self.root, changed_files=["TODO.md"], enforce_rules=True)
        self.assertEqual(ctx.exception.code, "POLICY-PROHIBITED-GENERATED-EDIT")

    def test_legacy_claim_rejected_under_issue_store(self):
        self._write_selector(profile="issue-store", epoch="issue-store-writable", phase="issue-store-writable", schema="agent-workflow-bootstrap@v2")
        (self.root / "TODO-worf-legacy-claim.md").write_text("# Claim", encoding="utf-8")

        res = POL.evaluate_integration_policy(self.root, changed_files=["TODO-worf-legacy-claim.md"], enforce_rules=False)
        self.assertEqual(res["status"], "rejected")
        self.assertTrue(any(v["code"] == "POLICY-LEGACY-CLAIM-PROHIBITED" for v in res["violations"]))

    def test_missing_or_unsupported_selector_schema_rejected(self):
        wf = {"schema": "invalid-schema@v99"}
        (self.root / "agent-workflow.json").write_text(json.dumps(wf), encoding="utf-8")

        with self.assertRaises(POL.IntegrationPolicyViolation) as ctx:
            POL.evaluate_integration_policy(self.root, changed_files=[], enforce_rules=True)
        self.assertEqual(ctx.exception.code, "UNSUPPORTED-SCHEMA")

    def test_profile_phase_contradiction_rejected(self):
        wf = {
            "schema": "agent-workflow-bootstrap@v1",
            "workflow_version": "1.0.0",
            "authority_epoch": "legacy-writable",
            "authority_profile": "legacy-lists",
            "write_phase": "issue-store-writable",
            "required_capability": "unprivileged",
            "runner_protocol": "runner-request@v1",
            "instruction_bundle": "docs/pipeline/agent-instructions/legacy/index.md",
        }
        wf["selector_digest"] = POL.compute_selector_digest(wf)
        (self.root / "agent-workflow.json").write_text(json.dumps(wf), encoding="utf-8")

        with self.assertRaises(POL.IntegrationPolicyViolation) as ctx:
            POL.evaluate_integration_policy(self.root, changed_files=[], enforce_rules=True)
        self.assertEqual(ctx.exception.code, "PROFILE-PHASE-CONTRADICTION")

    def test_placeholder_or_mismatched_digest_rejected(self):
        self._write_selector(profile="legacy-lists", repair_digest=False)
        with self.assertRaises(POL.IntegrationPolicyViolation) as ctx:
            POL.evaluate_integration_policy(self.root, changed_files=[], enforce_rules=True)
        self.assertEqual(ctx.exception.code, "SELECTOR-DIGEST-MISMATCH")

    def test_missing_boundary_or_nonexistent_base_rejected(self):
        self._write_selector(profile="legacy-lists")
        with self.assertRaises(POL.IntegrationPolicyViolation) as ctx:
            POL.evaluate_integration_policy(self.root, changed_files=None, base_ref=None, enforce_rules=True)
        self.assertEqual(ctx.exception.code, "MISSING-BOUNDARY")

        with self.assertRaises(POL.IntegrationPolicyViolation) as ctx:
            POL.evaluate_integration_policy(self.root, changed_files=None, base_ref="nonexistent-ref-12345", enforce_rules=True)
        self.assertEqual(ctx.exception.code, "INVALID-BASE-BOUNDARY")

    def test_cli_exit_code_non_zero_on_rejection_both_human_and_json(self):
        self._write_selector(profile="issue-store", epoch="issue-store-writable", phase="issue-store-writable", schema="agent-workflow-bootstrap@v2")
        (self.root / "TODO.md").write_text("# Rejected TODO", encoding="utf-8")

        tool_script = str(ROOT / "_src/tools/issue_integration_policy.py")

        # 1. Human mode exit code check
        proc_human = subprocess.run(
            [sys.executable, tool_script, "--root", str(self.root), "--files", "TODO.md"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc_human.returncode, 1, "Human mode must exit 1 on rejection")
        self.assertIn("REJECTED", proc_human.stderr)

        # 2. JSON mode exit code check
        proc_json = subprocess.run(
            [sys.executable, tool_script, "--root", str(self.root), "--files", "TODO.md", "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc_json.returncode, 1, "JSON mode must exit 1 on rejection")
        data = json.loads(proc_json.stdout)
        self.assertEqual(data["status"], "rejected")


if __name__ == "__main__":
    unittest.main()
