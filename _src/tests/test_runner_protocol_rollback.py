#!/usr/bin/env python3
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from _src.tools.runner_protocol_rollback import (
    EXCLUSIVE_MUTATION,
    FAILURE_STORES,
    HEALTH_AFTER_SWITCH,
    INJECTED_EPOCH,
    INJECTED_PROTOCOL,
    POST_SWITCH_VERIFICATION,
    PRIOR_EPOCH,
    SELECTOR_NAME,
    SERVICE_NAME,
    SINGLETON_PROTOCOL,
    capture,
    inject_failed_activation,
    prove,
    sha256_bytes,
)

SELECTOR = {
    "schema": "agent-workflow-bootstrap@v1",
    "workflow_version": "1.0.0",
    "authority_epoch": PRIOR_EPOCH,
    "authority_profile": "legacy-lists",
    "write_phase": PRIOR_EPOCH,
    "required_capability": "sandboxed-grunt",
    "runner_protocol": SINGLETON_PROTOCOL,
    "selector_digest": "sha256:" + ("a" * 64),
    "instruction_bundle": "docs/pipeline/agent-instructions/legacy/index.md",
}
SERVICE = {
    "schema": "runner-service@v1",
    "run_slot": "run.sh",
    "rollback_path": "git checkout HEAD -- runner-host/run-loop.sh",
}


class ProtocolRollbackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="rollback-proof-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        git = self.tmp / ".git"
        git.mkdir()
        (git / "HEAD").write_text("ref: refs/heads/0037-46.02\n", encoding="utf-8")
        (self.tmp / SELECTOR_NAME).write_text(json.dumps(SELECTOR) + "\n", encoding="utf-8")
        service = self.tmp / SERVICE_NAME
        service.parent.mkdir(parents=True)
        service.write_text(json.dumps(SERVICE) + "\n", encoding="utf-8")

    def test_injection_changes_protocol_and_epoch(self) -> None:
        fields = inject_failed_activation(self.tmp)
        self.assertEqual(fields["runner_protocol"], INJECTED_PROTOCOL)
        self.assertEqual(fields["authority_epoch"], INJECTED_EPOCH)

    def test_prove_restores_bytes_and_fields(self) -> None:
        before = (self.tmp / SELECTOR_NAME).read_bytes()
        service_before = (self.tmp / SERVICE_NAME).read_bytes()
        result = prove(self.tmp)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["injected"]["runner_protocol"], INJECTED_PROTOCOL)
        self.assertEqual(result["injected"]["authority_epoch"], INJECTED_EPOCH)
        self.assertEqual(result["after"]["fields"]["runner_protocol"], SINGLETON_PROTOCOL)
        self.assertEqual(result["after"]["fields"]["authority_epoch"], PRIOR_EPOCH)
        after = (self.tmp / SELECTOR_NAME).read_bytes()
        self.assertEqual(after, before)
        self.assertEqual(sha256_bytes(after), sha256_bytes(before))
        self.assertEqual((self.tmp / SERVICE_NAME).read_bytes(), service_before)

    def test_all_named_failure_stores_prove_and_restore_bytes(self) -> None:
        self.assertEqual(
            FAILURE_STORES,
            (HEALTH_AFTER_SWITCH, POST_SWITCH_VERIFICATION, EXCLUSIVE_MUTATION),
        )
        for store in FAILURE_STORES:
            with self.subTest(store=store):
                before = capture(self.tmp)
                result = prove(self.tmp, store)
                after = capture(self.tmp)
                self.assertTrue(result["ok"], result)
                self.assertEqual(result["failure_store"], store)
                self.assertEqual(before["selector"]["digest"], after["selector"]["digest"])
                self.assertEqual(before["service"]["digest"], after["service"]["digest"])
                self.assertEqual(before["fields"], after["fields"])

    def test_invalid_failure_store_is_rejected_without_mutation(self) -> None:
        before = (self.tmp / SELECTOR_NAME).read_bytes()
        with self.assertRaises(ValueError):
            inject_failed_activation(self.tmp, "not-a-gate")
        self.assertEqual((self.tmp / SELECTOR_NAME).read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
