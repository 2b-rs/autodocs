"""Focused lifecycle closure tests for Task 0037-10.05."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("issuectl_closure", ROOT / "_src/tools/issuectl.py")
assert SPEC and SPEC.loader
ctl = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ctl
SPEC.loader.exec_module(ctl)


class ClosureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Closure Test"], check=True)
        self.issues = self.repo / "issues"
        self._write_item("0099", "feature")
        self._write_item("0099-01", "task", "0099")
        self._commit("initial")
        self.first = self._head()
        (self.repo / "evidence.txt").write_text("verified\n", encoding="utf-8")
        self._commit("evidence")
        self.second = self._head()

    def tearDown(self):
        self.temp.cleanup()

    def _write_item(self, item_id, level, parent=None, state="in_progress", historical=False):
        path = ctl.item_path(self.issues, item_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        meta = {"schema_version": "1.0", "id": item_id, "level": level, "state": state,
                "visibility": "internal", "authority": "shadow", "created_at": "2026-08-26",
                "updated_at": "2026-08-26", "origin": {"kind": "authored"}}
        if parent:
            meta["parent"] = parent
        criteria = "- **AC-001** Criterion one.\n"
        if historical:
            criteria += "- **AC-002** ~~Old criterion.~~ (withdrawn, 2026-08-26: obsolete)\n"
        body = "## Goal\n\nGoal.\n\n## Scope\n\nScope.\n\n## Acceptance criteria\n\n" + criteria + "\n## Definition of Done\n\nDone.\n"
        path.write_bytes(ctl._compose(meta, body))
        return path

    def _commit(self, message):
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-q", "-m", message], check=True)

    def _head(self):
        return subprocess.check_output(["git", "-C", str(self.repo), "rev-parse", "HEAD"], text=True).strip()

    def _decision(self, item_id, kind):
        path = ctl.item_path(self.issues, item_id).parent / "decisions" / f"{kind}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {"schema_version": "1.0", "decision_id": f"d-{kind}",
            "item_id": item_id, "kind": kind, "status": "approved", "decided_at": "2026-08-26T03:00:00Z",
            "authority": {"kind": "maintainer", "identity": "owner", "role": "repository-owner"},
            "question": "Disposition?", "options": [{"id": "yes", "summary": "Yes"}],
            "selected_option": "yes", "rationale": "Authorized.", "evidence": ["evidence.txt"]}
        if kind in {"supersession", "duplicate"}:
            record["successor_item"] = "0099-02"
        path.write_text(json.dumps(record) + "\n")
        self._commit(kind)
        return self._head()

    def _closure(self, item_id="0099-01", disposition="wontfix", *, decision_ref=None, historical=False):
        criteria = [{"id": "AC-001", "status": "checked", "evidence": ["evidence.txt", f"commit:{self.first}"]}]
        if historical:
            criteria.append({"id": "AC-002", "status": "withdrawn", "evidence": ["evidence.txt"]})
        result = {"schema_version": "1.0", "item_id": item_id, "disposition": disposition,
                  "closed_at": "2026-08-26T04:00:00Z", "closed_by": "agent:test", "criteria": criteria,
                  "commit_refs": [self.first, self.second],
                  "validation": [{"name": "tests", "result": "pass", "evidence": "evidence.txt"}]}
        if disposition in {"wontfix", "cancelled", "archived-not-accepted"}:
            result["reason"] = "Authorized disposition."
        if disposition in {"superseded", "duplicate"}:
            result["successor_item"] = "0099-02"
        if decision_ref:
            result["decision_ref"] = decision_ref
        if disposition == "archived-not-accepted":
            result["validation"][0]["result"] = "not-applicable"
        return result

    def _validate(self, closure, item_id="0099-01"):
        path = ctl.item_path(self.issues, item_id)
        meta, body, _ = ctl.parse_document(path, self.issues)
        ctl.validate_closure_candidate(self.repo, self.issues, path, meta, body, closure)

    def _approval(self, item_id="0099-01"):
        path = ctl.item_path(self.issues, item_id).parent / "approval.json"
        path.write_text(json.dumps({"schema": "issue-approval@v1",
            "package_commit": self.first, "package_digest": "sha256:" + "a" * 64,
            "approval_ref": "refs/autodocs/approval/test", "approver_role": "reviewer",
            "signature_verified": True}) + "\n")
        self._commit("approval")
        self.second = self._head()

    def test_every_terminal_disposition_and_decision_authority(self):
        self._validate(self._closure())
        for disposition, kind in ctl.DECISION_DISPOSITIONS.items():
            with self.subTest(disposition=disposition):
                ref = self._decision("0099-01", kind)
                self.second = ref
                self._validate(self._closure(disposition=disposition, decision_ref=ref))

    def test_completed_requires_verified_approval(self):
        with self.assertRaisesRegex(ctl.IssuectlError, "approval"):
            self._validate(self._closure(disposition="completed"))
        self._approval()
        self._validate(self._closure(disposition="completed"))

    def test_missing_invalid_evidence_and_same_commit_reject(self):
        candidate = self._closure()
        candidate["criteria"][0]["evidence"] = ["pending"]
        with self.assertRaisesRegex(ctl.IssuectlError, "placeholder"):
            self._validate(candidate)
        candidate = self._closure()
        candidate["commit_refs"] = [self.first, self.first]
        with self.assertRaisesRegex(ctl.IssuectlError, "two-commit"):
            self._validate(candidate)

    def test_feature_0021_archive_semantics(self):
        self._write_item("0021", "feature")
        self._commit("0021")
        self.second = self._head()
        with self.assertRaisesRegex(ctl.IssuectlError, "0021"):
            self._validate(self._closure("0021", "completed"), "0021")
        ref = self._decision("0021", "archival")
        self.second = ref
        self._validate(self._closure("0021", "archived-not-accepted", decision_ref=ref), "0021")

    def test_partial_feature_closure_rejects(self):
        with self.assertRaisesRegex(ctl.IssuectlError, "0099-01"):
            self._validate(self._closure("0099", "wontfix"), "0099")

    def test_feature_requires_child_terminal_record_not_only_closed_state(self):
        self._write_item("0099-01", "task", "0099", state="closed")
        self._commit("closed child without terminal record")
        self.second = self._head()
        with self.assertRaisesRegex(ctl.IssuectlError, "0099-01"):
            self._validate(self._closure("0099", "wontfix"), "0099")

    def test_close_command_dry_run_promotion_and_immutable_terminal_record(self):
        closure = self._closure()
        candidate = self.repo / "candidate-closure.json"
        candidate.write_text(json.dumps(closure) + "\n")
        item = ctl.item_path(self.issues, "0099-01")
        digest = ctl._sha256_bytes(item.read_bytes())
        args = SimpleNamespace(repo=str(self.repo), issues_root=str(self.issues), id="0099-01",
            closure=str(candidate), expected_digest=digest, owner_token=None, date="2026-08-26",
            dry_run=True, format="json")
        ctl.cmd_close(args)
        self.assertFalse(item.parent.joinpath("closure.json").exists())
        args.dry_run = False
        ctl.cmd_close(args)
        self.assertEqual(json.loads(item.parent.joinpath("closure.json").read_text()), closure)
        changed = dict(closure)
        changed["reason"] = "changed"
        candidate.write_text(json.dumps(changed) + "\n")
        metadata, body, _ = ctl.parse_document(item, self.issues)
        metadata["state"] = "in_progress"
        item.write_bytes(ctl._compose(metadata, body))
        args.expected_digest = ctl._sha256_bytes(item.read_bytes())
        with self.assertRaisesRegex(ctl.IssuectlError, "immutable"):
            ctl.cmd_close(args)

    def test_malformed_extra_history_and_decision_successor_reject(self):
        malformed = self._closure()
        malformed["unexpected"] = True
        with self.assertRaisesRegex(ctl.IssuectlError, "incomplete or unsupported"):
            self._validate(malformed)
        extra = self._closure()
        extra["criteria"].append({"id": "AC-999", "status": "checked", "evidence": ["evidence.txt"]})
        with self.assertRaisesRegex(ctl.IssuectlError, "exactly match"):
            self._validate(extra)
        ref = self._decision("0099-01", "duplicate")
        self.second = ref
        mismatch = self._closure(disposition="duplicate", decision_ref=ref)
        mismatch["successor_item"] = "0099-03"
        with self.assertRaisesRegex(ctl.IssuectlError, "successor"):
            self._validate(mismatch)

    def test_injected_write_failure_rolls_back_and_history_is_immutable(self):
        closure = self._closure()
        path = ctl.item_path(self.issues, "0099-01")
        original = path.read_bytes()
        with mock.patch.object(ctl.os, "replace", side_effect=OSError("injected")):
            with self.assertRaises(OSError):
                ctl.atomic_promote([(path, original + b"x", original), (path.parent / "closure.json", ctl._canonical_json(closure).encode(), None)], dry_run=False)
        self.assertEqual(path.read_bytes(), original)
        self.assertFalse((path.parent / "closure.json").exists())
        (path.parent / "closure.json").write_text(ctl._canonical_json(closure), encoding="utf-8")
        changed = dict(closure)
        changed["reason"] = "changed"
        existing = (path.parent / "closure.json").read_bytes()
        self.assertNotEqual(existing, ctl._canonical_json(changed).encode())

    def test_withdrawn_history_not_presented_as_success(self):
        self._write_item("0099-01", "task", "0099", historical=True)
        self._commit("history")
        self.second = self._head()
        candidate = self._closure(historical=True)
        self._validate(candidate)
        candidate["criteria"][1]["status"] = "checked"
        with self.assertRaisesRegex(ctl.IssuectlError, "must not be presented"):
            self._validate(candidate)


if __name__ == "__main__":
    unittest.main()
