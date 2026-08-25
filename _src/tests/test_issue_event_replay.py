#!/usr/bin/env python3
"""Tests for Task 0037-15.03 exactly-once authorized event replay."""
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "issue_event_replay", ROOT / "_src/tools/issue_event_replay.py"
)
RPL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RPL)

COMMIT_A = "a" * 40
COMMIT_B = "b" * 40
EVENT_ID = "018f4a31-32ac-7abc-8def-0123456789ab"
EVENT_ID_2 = "018f4a31-32ad-7abc-8def-0123456789ab"
FINDING_ID = "018f4a31-32ab-7abc-8def-0123456789ab"
RUN_ID = "018f4a31-32aa-7abc-8def-0123456789ab"
STAMP = "2026-08-16T08:01:00Z"
BODY_V1 = b"# 0037-01\nKeep identity.\n"
BODY_V2 = b"# 0037-01\nChanged imported text.\n"


def _ref(kind, ident, **extra):
    value = {
        "schema_version": "1.0",
        "kind": kind,
        "uri": f"{kind}:{ident}",
        "classification": "internal",
    }
    value.update(extra)
    return value


class ReplayTests(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.store_root = self.root / "prov-host"
        self.store_root.mkdir()
        self.issues = self.root / "issues" / "0037" / "0037-01"
        self.issues.mkdir(parents=True)
        (self.issues / "index.md").write_bytes(BODY_V1)

    def tearDown(self):
        self.tmp.cleanup()

    def _candidate(self, **overrides):
        digest = RPL.item_digest(BODY_V1)
        value = {
            "source_commit": COMMIT_A,
            "latest_source": COMMIT_A,
            "schema": "issue-item@v1",
            "issues_root": str(self.root),
            "items": {
                "0037-01": {
                    "id": "0037-01",
                    "path": "issues/0037/0037-01/index.md",
                    "digest": digest,
                    "deleted": False,
                    "active_claims": [],
                }
            },
        }
        value.update(overrides)
        return value

    def _event(self, **overrides):
        digest = RPL.item_digest(BODY_V1)
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
            "reconciliation_authorized_by": "decision:0037-06.02",
            "base_source": COMMIT_A,
            "item_id": "0037-01",
            "item_digest": digest,
            "mutates_item": False,
        }
        value.update(overrides)
        return value

    def _seed_store(self, store_root: Path):
        store = RPL.PS.ProvenanceStore(store_root)
        store.create_run(
            {
                "schema_version": "1.0",
                "run_id": RUN_ID,
                "started_at": "2026-08-16T08:00:00Z",
                "ended_at": "2026-08-16T08:02:00Z",
                "environment": "assessment",
                "classification": "internal",
                "status": "succeeded",
                "producer": _ref("commit", COMMIT_A),
                "inputs": [_ref("commit", COMMIT_A), _ref("issue", "0037-01")],
                "outputs": [],
            }
        )
        store.create_finding(
            {
                "schema_version": "1.0",
                "finding_id": FINDING_ID,
                "detected_at": STAMP,
                "state": "open",
                "classification": "internal",
                "environment": "assessment",
                "subject": _ref("issue", "0037-01"),
                "detected_during": _ref("run", RUN_ID),
            }
        )
        return store

    def _replay(self, candidate, events, store_root=None):
        store_root = store_root or self.store_root
        self._seed_store(store_root)
        return RPL.replay_events(
            candidate=candidate,
            events=events,
            store_root=store_root,
            replay_run_id=RUN_ID,
            record_findings=True,
        )

    def test_compatible_replay(self):
        report = self._replay(self._candidate(), [self._event()])
        self.assertTrue(report["promotable"])
        self.assertEqual(report["replayed"], 1)
        self.assertEqual(report["results"][0]["status"], "created")
        self.assertFalse(report["candidate_items_mutated"])
        body = (self.root / "issues/0037/0037-01/index.md").read_bytes()
        self.assertEqual(body, BODY_V1)
        store = RPL.PS.ProvenanceStore(self.store_root)
        stored = store.read_event(EVENT_ID, STAMP)
        self.assertEqual(stored["event_id"], EVENT_ID)
        self.assertNotIn("reconciliation_authorized_by", stored)

    def test_duplicate_replay_identical_is_idempotent(self):
        first = self._replay(self._candidate(), [self._event()])
        self.assertEqual(first["results"][0]["status"], "created")
        second = RPL.replay_events(
            candidate=self._candidate(),
            events=[self._event()],
            store_root=self.store_root,
            replay_run_id=RUN_ID,
            record_findings=True,
        )
        self.assertTrue(second["promotable"])
        self.assertEqual(second["results"][0]["status"], "replay")
        self.assertEqual(second["skipped"], 0)

    def test_collision_different_payload(self):
        self._replay(self._candidate(), [self._event()])
        collided = self._event(occurred_at="2026-08-16T09:00:00Z")
        report = RPL.replay_events(
            candidate=self._candidate(),
            events=[collided],
            store_root=self.store_root,
            replay_run_id=RUN_ID,
        )
        codes = [f["code"] for f in report["findings"]]
        self.assertIn(RPL.FINDING_DUPLICATE, codes)
        self.assertFalse(report["promotable"])
        self.assertEqual(report["findings"][0]["disposition"], "reject-collision")

    def test_deletion(self):
        cand = self._candidate()
        cand["items"]["0037-01"]["deleted"] = True
        report = self._replay(cand, [self._event()])
        self.assertIn(RPL.FINDING_TARGET_DELETED, [f["code"] for f in report["findings"]])
        self.assertEqual(report["findings"][0]["disposition"], "reject-deleted-target")

    def test_stale_base(self):
        cand = self._candidate(source_commit=COMMIT_A, latest_source=COMMIT_B)
        report = self._replay(cand, [self._event(base_source=COMMIT_A)])
        self.assertIn(RPL.FINDING_STALE_BASE, [f["code"] for f in report["findings"]])
        event_stale = self._event(base_source=COMMIT_B)
        cand2 = self._candidate(source_commit=COMMIT_A, latest_source=COMMIT_A)
        alt = self.root / "prov2"
        alt.mkdir()
        report2 = self._replay(cand2, [event_stale], store_root=alt)
        self.assertIn(RPL.FINDING_STALE_BASE, [f["code"] for f in report2["findings"]])

    def test_unauthorized_event(self):
        event = self._event()
        del event["reconciliation_authorized_by"]
        report = self._replay(self._candidate(), [event])
        self.assertIn(RPL.FINDING_UNAUTHORIZED, [f["code"] for f in report["findings"]])
        self.assertEqual(report["findings"][0]["disposition"], "reject-unauthorized")

    def test_changed_item(self):
        (self.root / "issues/0037/0037-01/index.md").write_bytes(BODY_V2)
        cand = self._candidate()
        cand["items"]["0037-01"]["digest"] = RPL.item_digest(BODY_V2)
        report = self._replay(cand, [self._event()])
        self.assertIn(RPL.FINDING_CHANGED, [f["code"] for f in report["findings"]])
        self.assertEqual(report["findings"][0]["disposition"], "reject-changed-item")

    def test_mutates_imported_text(self):
        report = self._replay(self._candidate(), [self._event(mutates_item=True)])
        self.assertIn(RPL.FINDING_OVERWRITE, [f["code"] for f in report["findings"]])

    def test_concurrent_claim(self):
        cand = self._candidate()
        cand["items"]["0037-01"]["active_claims"] = ["agent:other:0037-01:tok"]
        report = self._replay(cand, [self._event()])
        self.assertIn(RPL.FINDING_CLAIM, [f["code"] for f in report["findings"]])

    def test_zero_loss_after_full_reimport(self):
        report = self._replay(self._candidate(), [self._event()])
        self.assertTrue(report["promotable"])
        # Simulate a fresh full re-import: new issues tree, same identity, provenance store kept.
        fresh = self.root / "fresh-issues"
        dest = fresh / "issues/0037/0037-01"
        dest.mkdir(parents=True)
        shutil.copy2(self.root / "issues/0037/0037-01/index.md", dest / "index.md")
        cand = self._candidate()
        cand["issues_root"] = str(fresh)
        cand["items"]["0037-01"]["path"] = "issues/0037/0037-01/index.md"
        second = RPL.replay_events(
            candidate=cand,
            events=[self._event()],
            store_root=self.store_root,
            replay_run_id=RUN_ID,
        )
        self.assertEqual(second["results"][0]["status"], "replay")
        store = RPL.PS.ProvenanceStore(self.store_root)
        stored = store.read_event(EVENT_ID, STAMP)
        self.assertEqual(stored["event_id"], EVENT_ID)
        self.assertEqual((dest / "index.md").read_bytes(), BODY_V1)

    def test_batch_collision_before_write(self):
        a = self._event()
        b = self._event(occurred_at="2026-08-16T10:00:00Z")
        report = self._replay(self._candidate(), [a, b])
        self.assertIn(RPL.FINDING_DUPLICATE, [f["code"] for f in report["findings"]])
        self.assertEqual(report["replayed"], 1)
        self.assertEqual(report["skipped"], 1)

    def test_cli_writes_report(self):
        self._seed_store(self.store_root)
        cand_path = self.root / "candidate.json"
        ev_path = self.root / "events.json"
        report_path = self.root / "report.json"
        cand_path.write_text(json.dumps(self._candidate()), encoding="utf-8")
        ev_path.write_text(json.dumps([self._event()]), encoding="utf-8")
        rc = RPL.main(
            [
                "--candidate",
                str(cand_path),
                "--events",
                str(ev_path),
                "--store-root",
                str(self.store_root),
                "--report",
                str(report_path),
            ]
        )
        self.assertEqual(rc, 0)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["schema"], "event-replay-report@v1")
        self.assertTrue(report["promotable"])


if __name__ == "__main__":
    unittest.main()
