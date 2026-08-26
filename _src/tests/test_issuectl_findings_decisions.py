"""Finding and signed-decision command tests for Task 0037-10.03."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("issuectl_0037_10_03", ROOT / "_src/tools/issuectl.py")
assert SPEC and SPEC.loader
ctl = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ctl
SPEC.loader.exec_module(ctl)

STAMP = "2026-08-26T00:00:00Z"
FINDING = "018f4a31-32ab-7abc-8def-0123456789ab"
COMMIT = "a" * 40
APPROVAL_COMMIT = "b" * 40


class FindingOperationsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def args(self, **overrides):
        values = dict(
            repo=str(self.repo), format="json", dry_run=False, finding_id=FINDING,
            detected_at=STAMP, state="open", classification="internal",
            environment="assessment", issue="0037-10.03", criterion="AC-001",
            run="018f4a31-32aa-7abc-8def-0123456789ab", evidence=["evidence-1"],
            expected_digest=None,
        )
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_mint_rerun_and_disposition_preserve_identity_and_history(self):
        self.assertEqual(ctl.cmd_finding(self.args()), 0)
        path = next((self.repo / "provenance/findings").glob("*/*/*.json"))
        first = path.read_bytes()
        first_record = json.loads(first)
        self.assertEqual(first_record["finding_id"], FINDING)
        self.assertEqual(first_record["subject"]["uri"], "issue:0037-10.03")
        self.assertEqual(first_record["detected_during"]["kind"], "run")
        self.assertEqual({r["kind"] for r in first_record["evidence"]}, {"criterion", "evidence"})
        digest = hashlib.sha256(first).hexdigest()
        self.assertEqual(ctl.cmd_finding(self.args(expected_digest=digest)), 0)
        self.assertEqual(path.read_bytes(), first)
        self.assertEqual(ctl.cmd_finding(self.args(state="remediated", expected_digest=digest, detected_at=None)), 0)
        final = json.loads(path.read_text())
        self.assertEqual(final["finding_id"], FINDING)
        self.assertEqual(final["detected_at"], STAMP)
        self.assertEqual(final["state"], "remediated")
        self.assertEqual(len(list((self.repo / "provenance/finding-history" / FINDING).glob("*.json"))), 2)

    def test_digest_mismatch_and_injected_write_failure_leave_original(self):
        ctl.cmd_finding(self.args())
        path = next((self.repo / "provenance/findings").glob("*/*/*.json"))
        original = path.read_bytes()
        with self.assertRaisesRegex(ctl.IssuectlError, "concurrent edit"):
            ctl.cmd_finding(self.args(state="rejected", detected_at=None, expected_digest="0" * 64))
        with mock.patch.object(ctl.os, "replace", side_effect=OSError("injected")):
            with self.assertRaisesRegex(OSError, "injected"):
                ctl.cmd_finding(self.args(state="rejected", detected_at=None, expected_digest=hashlib.sha256(original).hexdigest()))
        self.assertEqual(path.read_bytes(), original)


class SignedDecisionOperationsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.decision = {
            "schema_version": "1.0", "decision_id": "arch-0037-10-03",
            "item_id": "0037-10.03", "kind": "architecture", "status": "approved",
            "decided_at": STAMP, "authority": {"kind": "reviewer", "identity": "approver", "role": "architecture-approver"},
            "rationale": "reviewed",
        }
        self.authorities = {"schema": "issue-authorities@v1", "principals": [
            {"identity": "approver", "role": "architecture-approver"},
            {"identity": "owner", "role": "repository-owner"},
        ]}
        self.now = dt.datetime(2026, 8, 26, 0, 30, tzinfo=dt.timezone.utc)

    def tearDown(self):
        self.temp.cleanup()

    def approval(self, **overrides):
        value = {
            "schema": "issue-decision-approval@v1",
            "approval_ref": "refs/autodocs/approval/arch-0037-10-03",
            "approval_commit": APPROVAL_COMMIT,
            "package_commit": COMMIT,
            "package_digest": ctl._sha256_bytes(ctl._canonical_json(self.decision).encode()),
            "policy_revision": ctl._sha256_bytes(ctl._canonical_json(self.authorities).encode()),
            "approver": {"identity": "approver", "role": "architecture-approver"},
            "valid_from": "2026-08-26T00:00:00Z", "expires_at": "2026-08-27T00:00:00Z",
            "revoked": False, "conditions": ["independent-review"], "satisfied_conditions": ["independent-review"],
            "implementation_authors": ["implementer"],
        }
        value.update(overrides)
        return value

    def verify(self, approval=None, authorities=None, decision=None):
        approval = approval or self.approval()
        authorities = authorities or self.authorities
        decision = decision or self.decision
        calls = [
            subprocess.CompletedProcess([], 0, stdout=(APPROVAL_COMMIT + "\n").encode(), stderr=b""),
            subprocess.CompletedProcess([], 0, stdout=b"", stderr=b""),
        ]
        with mock.patch.object(ctl.subprocess, "run", side_effect=calls):
            ctl._verify_decision_approval(self.repo, decision, approval, authorities, self.now)

    def test_authorized_normal_and_bootstrap_role_verification(self):
        self.verify()
        bootstrap = dict(self.decision, decision_id="bootstrap-0037", kind="scope")
        approval = self.approval(
            approval_ref="refs/autodocs/approval/bootstrap-0037",
            package_digest=ctl._sha256_bytes(ctl._canonical_json(bootstrap).encode()),
            approver={"identity": "owner", "role": "repository-owner"},
        )
        self.verify(approval=approval, decision=bootstrap)

    def test_revoked_wrong_policy_wrong_role_self_and_conditions_rejected(self):
        cases = [
            (self.approval(revoked=True), "revoked"),
            (self.approval(expires_at="2026-08-26T00:10:00Z"), "validity"),
            (self.approval(policy_revision="sha256:" + "0" * 64), "policy revision"),
            (self.approval(approver={"identity": "owner", "role": "repository-owner"}), "wrong role"),
            (self.approval(implementation_authors=["approver"]), "self-approval"),
            (self.approval(satisfied_conditions=[]), "conditions"),
        ]
        for approval, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ctl.IssuectlError, message):
                self.verify(approval=approval)

    def test_digest_signature_ref_duplicate_replay_and_immutable_history(self):
        with self.assertRaisesRegex(ctl.IssuectlError, "package digest"):
            self.verify(approval=self.approval(package_digest="sha256:" + "0" * 64))
        failed = subprocess.CompletedProcess([], 1, stdout=b"", stderr=b"bad")
        with mock.patch.object(ctl.subprocess, "run", return_value=failed), self.assertRaisesRegex(ctl.IssuectlError, "signature"):
            ctl._verify_decision_approval(self.repo, self.decision, self.approval(), self.authorities, self.now)

        input_path, approval_path, auth_path = self.repo / "decision.json", self.repo / "approval.json", self.repo / "authorities.json"
        input_path.write_text(json.dumps(self.decision))
        approval_path.write_text(json.dumps(self.approval()))
        auth_path.write_text(json.dumps(self.authorities))
        args = argparse.Namespace(repo=str(self.repo), input=str(input_path), approval=str(approval_path), authorities=str(auth_path), id="0037-10.03", decision_id="arch-0037-10-03", expected_digest=None, now="2026-08-26T00:30:00Z", dry_run=False, format="json")
        good = [subprocess.CompletedProcess([], 0, stdout=(APPROVAL_COMMIT + "\n").encode(), stderr=b""), subprocess.CompletedProcess([], 0, stdout=b"", stderr=b"")]
        with mock.patch.object(ctl.subprocess, "run", side_effect=good):
            ctl.cmd_decision(args)
        path = ctl._decision_path(self.repo, args.id, args.decision_id)
        original = path.read_bytes()
        with mock.patch.object(ctl.subprocess, "run", side_effect=good):
            ctl.cmd_decision(args)
        self.assertEqual(path.read_bytes(), original)
        changed = dict(self.decision, rationale="different")
        input_path.write_text(json.dumps(changed))
        approval_path.write_text(json.dumps(self.approval(package_digest=ctl._sha256_bytes(ctl._canonical_json(changed).encode()))))
        with mock.patch.object(ctl.subprocess, "run", side_effect=good), self.assertRaisesRegex(ctl.IssuectlError, "immutable"):
            ctl.cmd_decision(args)


if __name__ == "__main__":
    unittest.main()
