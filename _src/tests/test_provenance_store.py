"""API tests for `_src/tools/provenance_store.py` (Task `0037-17.01`)."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_src" / "tools" / "provenance_store.py"
SPEC = importlib.util.spec_from_file_location("provenance_store", TOOL)
assert SPEC and SPEC.loader
ps = importlib.util.module_from_spec(SPEC)
sys.modules["provenance_store"] = ps
SPEC.loader.exec_module(ps)

COMMIT = "a" * 40
RUN_ID = "018f4a31-32aa-7abc-8def-0123456789ab"
FINDING_ID = "018f4a31-32ab-7abc-8def-0123456789ab"
EVENT_ID = "018f4a31-32ac-7abc-8def-0123456789ab"
SET_ID = "018f4a31-32ad-7abc-8def-0123456789ab"
STAMP = "2026-08-16T08:01:00Z"


def _ref(kind, ident, **extra):
    value = {
        "schema_version": "1.0",
        "kind": kind,
        "uri": f"{kind}:{ident}",
        "classification": "internal",
    }
    value.update(extra)
    return value


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.files = {}
        self.store = ps.ProvenanceStore(self.root, file_bytes=self.files.__getitem__)

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, **overrides):
        value = {
            "schema_version": "1.0",
            "run_id": RUN_ID,
            "started_at": STAMP,
            "ended_at": "2026-08-16T08:02:00Z",
            "environment": "assessment",
            "classification": "internal",
            "status": "succeeded",
            "producer": _ref("commit", COMMIT),
            "inputs": [
                _ref("commit", COMMIT),
                _ref("issue", "0037-17.01"),
                _ref("criterion", "AC-001"),
                _ref("campaign", "camp-1"),
            ],
            "outputs": [_ref("artifact-set", SET_ID)],
        }
        value.update(overrides)
        return value

    def _finding(self, **overrides):
        value = {
            "schema_version": "1.0",
            "finding_id": FINDING_ID,
            "detected_at": STAMP,
            "state": "open",
            "classification": "internal",
            "environment": "assessment",
            "subject": _ref("issue", "0037-17.01"),
            "detected_during": _ref("run", RUN_ID),
            "evidence": [_ref("artifact", "report@sha256:" + "ab" * 32, digest="sha256:" + "ab" * 32)],
        }
        value.update(overrides)
        return value

    def _event(self, **overrides):
        value = {
            "schema_version": "1.0",
            "event_id": EVENT_ID,
            "occurred_at": STAMP,
            "relation": "detected-during",
            "source": _ref("finding", FINDING_ID),
            "target": _ref("run", RUN_ID),
            "environment": "assessment",
            "classification": "internal",
            "run": _ref("run", RUN_ID),
        }
        value.update(overrides)
        return value

    def _artifact_set(self, path="docs/pipeline/provenance-contract.md", content=b"hello\n", **overrides):
        self.files[path] = content
        member = {
            "path": path,
            "digest": ps.sha256_bytes(content),
            "size_bytes": len(content),
            "media_type": "text/markdown",
            "source_commit": COMMIT,
        }
        value = {
            "schema_version": "1.0",
            "set_id": SET_ID,
            "created_at": STAMP,
            "classification": "internal",
            "environment": "assessment",
            "producer": _ref("run", RUN_ID),
            "members": [member],
        }
        value.update(overrides)
        return value

    def test_create_and_read_run_finding_event_artifact_set(self):
        run = self.store.create_run(self._run())
        self.assertEqual(run["status"], "created")
        finding = self.store.create_finding(self._finding())
        self.assertEqual(finding["status"], "created")
        aset = self.store.create_artifact_set(self._artifact_set())
        self.assertEqual(aset["status"], "created")
        self.assertTrue(aset["record"]["set_digest"].startswith("sha256:"))
        event = self.store.create_event(self._event())
        self.assertEqual(event["status"], "created")
        self.assertEqual(self.store.read_run(RUN_ID)["run_id"], RUN_ID)

    def test_replay_idempotence(self):
        first = self.store.create_run(self._run())
        second = self.store.create_run(self._run())
        self.assertEqual(first["status"], "created")
        self.assertEqual(second["status"], "replay")
        self.assertEqual(Path(first["path"]).read_bytes(), Path(second["path"]).read_bytes())

    def test_collision_rejects_different_payload(self):
        self.store.create_run(self._run())
        other = self._run()
        other["status"] = "failed"
        with self.assertRaises(ps.ProvenanceError) as ctx:
            self.store.create_run(other)
        self.assertEqual(ctx.exception.code, "PV-COLLISION")

    def test_overwrite_attempt_rejected(self):
        result = self.store.create_run(self._run())
        path = Path(result["path"])
        with self.assertRaises(ps.ProvenanceError):
            self.store._atomic_create(path, b"{}\n")

    def test_concurrent_create_one_winner(self):
        barrier = threading.Barrier(8)
        errors = []
        statuses = []

        def worker():
            try:
                barrier.wait()
                statuses.append(self.store.create_run(self._run())["status"])
            except ps.ProvenanceError as exc:
                errors.append(exc.code)

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda _: worker(), range(8)))
        self.assertEqual(statuses.count("created") + statuses.count("replay"), len(statuses))
        self.assertGreaterEqual(statuses.count("created") + statuses.count("replay"), 1)
        self.assertTrue(self.store.run_path(RUN_ID).is_file())
        for code in errors:
            self.assertIn(code, {"PV-COLLISION", "PV-OVERWRITE"})

    def test_crash_before_rename_leaves_no_partial_target(self):
        def boom(tmp_path, dest):
            raise RuntimeError("injected crash before link")

        self.store._inject_before_link = boom
        with self.assertRaises(RuntimeError):
            self.store.create_run(self._run())
        dest = self.store.run_path(RUN_ID)
        self.assertFalse(dest.exists())
        leftovers = list(dest.parent.glob(".*")) if dest.parent.exists() else []
        for leftover in leftovers:
            self.assertTrue(leftover.name.startswith("."))
            self.assertNotEqual(leftover.name, dest.name)

    def test_file_digest_change_rejected(self):
        payload = self._artifact_set(content=b"alpha")
        payload["members"][0]["digest"] = ps.sha256_bytes(b"beta")
        with self.assertRaises(ps.ProvenanceError) as ctx:
            self.store.create_artifact_set(payload)
        self.assertEqual(ctx.exception.code, "PV-DIGEST-CHANGE")

    def test_tree_digest_changes_with_member_order_independent_canonicalization(self):
        self.store.create_run(self._run())
        first = self._artifact_set()
        extra = {
            "path": "docs/pipeline/tools.md",
            "digest": ps.sha256_bytes(b"tools"),
            "size_bytes": 5,
            "media_type": "text/markdown",
            "source_commit": COMMIT,
        }
        first["members"].append(extra)
        self.files["docs/pipeline/tools.md"] = b"tools"
        a = self.store.create_artifact_set(first)
        second = self._artifact_set()
        second["members"] = [extra, first["members"][0]]
        b = self.store.create_artifact_set(second)
        self.assertEqual(a["record"]["set_digest"], b["record"]["set_digest"])
        self.assertEqual(b["status"], "replay")

    def test_redaction_required_for_restricted(self):
        self.store.create_run(self._run())
        finding = self._finding(classification="restricted")
        with self.assertRaises(ps.ProvenanceError) as ctx:
            self.store.create_finding(finding)
        self.assertEqual(ctx.exception.code, "PV-REDACTION")
        finding["redaction_reason"] = "contains secrets"
        finding["subject"] = _ref("issue", "0037-17.01", classification="restricted", redacted=True)
        self.store.create_finding(finding)

    def test_legacy_confidence_adapter_does_not_invent_scores(self):
        self.assertEqual(ps.adapt_legacy_confidence(None)["confidence"], "unknown")
        self.assertEqual(ps.adapt_legacy_confidence({"legacy": True})["confidence"], "legacy")
        self.assertEqual(ps.adapt_legacy_confidence({"confidence": 0.4})["confidence"], 0.4)
        with self.assertRaises(ps.ProvenanceError):
            ps.adapt_legacy_confidence({"confidence": 1.5})

    def test_dangling_and_fabricated_history_rejected(self):
        with self.assertRaises(ps.ProvenanceError) as ctx:
            self.store.create_event(self._event())
        self.assertEqual(ctx.exception.code, "PV-DANGLING")
        self.store.create_run(self._run())
        self.store.create_finding(self._finding())
        early = self._event(occurred_at="2020-01-01T00:00:00Z")
        with self.assertRaises(ps.ProvenanceError) as ctx:
            self.store.create_event(early)
        self.assertEqual(ctx.exception.code, "PV-FABRICATED")

    def test_duplicate_id_different_digest_collision_for_artifact_set(self):
        self.store.create_run(self._run())
        first = self.store.create_artifact_set(self._artifact_set(content=b"one"))
        self.assertEqual(first["status"], "created")
        with self.assertRaises(ps.ProvenanceError) as ctx:
            self.store.create_artifact_set(self._artifact_set(content=b"two"))
        self.assertEqual(ctx.exception.code, "PV-COLLISION")

    def test_no_partial_file_after_injected_write_failure(self):
        def boom(tmp_path, dest):
            tmp_path.unlink()
            raise OSError("injected unlink")

        self.store._inject_before_link = boom
        with self.assertRaises(OSError):
            self.store.create_run(self._run())
        self.assertFalse(self.store.run_path(RUN_ID).exists())


if __name__ == "__main__":
    unittest.main()
