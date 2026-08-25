"""Golden, reverse-index, and hermetic tests for Task `0037-17.02`."""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STORE_TOOL = ROOT / "_src" / "tools" / "provenance_store.py"
VIEW_TOOL = ROOT / "_src" / "tools" / "provenance_views.py"

STORE_SPEC = importlib.util.spec_from_file_location("provenance_store", STORE_TOOL)
assert STORE_SPEC and STORE_SPEC.loader
ps = importlib.util.module_from_spec(STORE_SPEC)
sys.modules["provenance_store"] = ps
STORE_SPEC.loader.exec_module(ps)

VIEW_SPEC = importlib.util.spec_from_file_location("provenance_views", VIEW_TOOL)
assert VIEW_SPEC and VIEW_SPEC.loader
pv = importlib.util.module_from_spec(VIEW_SPEC)
sys.modules["provenance_views"] = pv
VIEW_SPEC.loader.exec_module(pv)

COMMIT = "a" * 40
RUN_ID = "018f4a31-32aa-7abc-8def-0123456789ab"
FINDING_ID = "018f4a31-32ab-7abc-8def-0123456789ab"
EVENT_ID = "018f4a31-32ac-7abc-8def-0123456789ab"
SET_ID = "018f4a31-32ad-7abc-8def-0123456789ab"
STAMP = "2026-08-16T08:01:00Z"
ISSUE = "issue:0037-17.02"
CRITERION = "criterion:AC-001"
CAMPAIGN = "campaign:camp-1"


def _ref(kind, ident, **extra):
    value = {
        "schema_version": "1.0",
        "kind": kind,
        "uri": f"{kind}:{ident}" if ":" not in str(ident) else ident if str(ident).startswith(kind + ":") else f"{kind}:{ident}",
        "classification": "internal",
    }
    value.update(extra)
    return value


class ProvenanceViewsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.files = {}
        self.store = ps.ProvenanceStore(self.root, file_bytes=self.files.__getitem__)
        (self.root / "_src" / "tools").mkdir(parents=True)
        (self.root / "provenance" / "_schema").mkdir(parents=True)
        shutil.copy(STORE_TOOL, self.root / "_src" / "tools" / "provenance_store.py")
        shutil.copy(VIEW_TOOL, self.root / "_src" / "tools" / "provenance_views.py")
        shutil.copy(
            ROOT / "provenance/_schema/provenance-graph-v1.schema.json",
            self.root / "provenance/_schema/provenance-graph-v1.schema.json",
        )
        shutil.copy(
            ROOT / "provenance/_schema/provenance-reverse-v1.schema.json",
            self.root / "provenance/_schema/provenance-reverse-v1.schema.json",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, run_id=RUN_ID, issue="0037-17.02", **overrides):
        value = {
            "schema_version": "1.0",
            "run_id": run_id,
            "started_at": STAMP,
            "ended_at": "2026-08-16T08:02:00Z",
            "environment": "assessment",
            "classification": "internal",
            "status": "succeeded",
            "producer": _ref("commit", COMMIT),
            "inputs": [
                _ref("commit", COMMIT),
                _ref("issue", issue),
                _ref("criterion", "AC-001"),
                _ref("campaign", "camp-1"),
            ],
            "outputs": [_ref("artifact-set", SET_ID)],
        }
        value.update(overrides)
        return value

    def _finding(self, finding_id=FINDING_ID, issue="0037-17.02", **overrides):
        value = {
            "schema_version": "1.0",
            "finding_id": finding_id,
            "detected_at": STAMP,
            "state": "open",
            "classification": "internal",
            "environment": "assessment",
            "subject": _ref("issue", issue),
            "detected_during": _ref("run", RUN_ID),
            "evidence": [
                _ref(
                    "artifact",
                    "docs/evidence.md@sha256:" + "ab" * 32,
                    digest="sha256:" + "ab" * 32,
                )
            ],
        }
        value.update(overrides)
        return value

    def _event(self, event_id=EVENT_ID, **overrides):
        value = {
            "schema_version": "1.0",
            "event_id": event_id,
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

    def _artifact_set(self, set_id=SET_ID, path="docs/evidence.md", content=b"closed-item\n", **overrides):
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
            "set_id": set_id,
            "created_at": STAMP,
            "classification": "internal",
            "environment": "assessment",
            "producer": _ref("run", RUN_ID),
            "members": [member],
        }
        value.update(overrides)
        return value

    def _write_raw_event(self, payload):
        year, month = payload["occurred_at"][:4], payload["occurred_at"][5:7]
        directory = self.root / "provenance" / "events" / year / month
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{payload['event_id']}.json"
        path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        return path

    def _seed_closed_item(self):
        self.store.create_run(self._run())
        aset = self.store.create_artifact_set(self._artifact_set())
        digest = aset["record"]["members"][0]["digest"]
        self.store.create_finding(
            self._finding(
                evidence=[
                    _ref(
                        "artifact",
                        f"docs/evidence.md@{digest}",
                        digest=digest,
                    )
                ]
            )
        )
        self.store.create_event(self._event())
        verify = self._event(
            event_id="018f4a31-32ae-7abc-8def-0123456789ab",
            relation="verifies",
            source=_ref("evidence", "bundle-1"),
            target=_ref("criterion", "AC-001"),
        )
        self.store.create_event(verify)
        return aset

    def test_bidirectional_mapping_and_byte_stable_rebuild(self):
        aset = self._seed_closed_item()
        graph1, reverse1 = pv.build_views(self.root)
        pv.write_views(graph1, reverse1, self.root)
        encoded_graph = (self.root / pv.GRAPH_OUT).read_bytes()
        encoded_reverse = (self.root / pv.REVERSE_OUT).read_bytes()

        issue_uri = "issue:0037-17.02"
        self.assertIn(f"run:{RUN_ID}", reverse1["issue"]["runs"][issue_uri])
        self.assertIn("criterion:AC-001", reverse1["issue"]["criteria"][issue_uri])
        self.assertIn(f"finding:{FINDING_ID}", reverse1["issue"]["findings"][issue_uri])
        member_uri = f"artifact:docs/evidence.md@{aset['record']['members'][0]['digest']}"
        self.assertIn(member_uri, reverse1["issue"]["artifacts"][issue_uri])
        self.assertIn(issue_uri, reverse1["artifact"]["issue"][member_uri])
        self.assertIn(f"run:{RUN_ID}", reverse1["artifact"]["producer"][member_uri])
        self.assertIn(CAMPAIGN, reverse1["artifact"]["campaign"][member_uri])
        self.assertEqual(reverse1["criterion"]["evidence"]["criterion:AC-001"], ["evidence:bundle-1"])
        self.assertEqual(
            reverse1["evidence"]["criterion"]["evidence:bundle-1"],
            ["criterion:AC-001"],
        )
        self.assertIn(issue_uri, reverse1["evidence"]["issue"][member_uri])

        shutil.rmtree(self.root / "provenance" / "_views")
        graph2, reverse2 = pv.build_views(self.root)
        pv.write_views(graph2, reverse2, self.root)
        self.assertEqual(encoded_graph, (self.root / pv.GRAPH_OUT).read_bytes())
        self.assertEqual(encoded_reverse, (self.root / pv.REVERSE_OUT).read_bytes())
        self.assertEqual(graph1["counts"]["events"], 2)
        self.assertEqual(graph1["counts"]["events"], len(graph1["events"]))

    def test_enumeration_order_independent(self):
        self._seed_closed_item()
        later_run = "018f4a31-42aa-7abc-8def-0123456789ab"
        later_set = "018f4a31-42ad-7abc-8def-0123456789ab"
        self.store.create_run(
            self._run(
                run_id=later_run,
                issue="0037-99",
                outputs=[_ref("artifact-set", later_set)],
                started_at="2026-08-17T00:00:00Z",
                ended_at="2026-08-17T00:01:00Z",
            )
        )
        self.store.create_artifact_set(
            self._artifact_set(
                set_id=later_set,
                path="docs/unrelated.md",
                content=b"later\n",
                producer=_ref("run", later_run),
                created_at="2026-08-17T00:00:00Z",
            )
        )
        a, ra = pv.build_views(self.root)
        events_dir = self.root / "provenance" / "events"
        files = list(events_dir.rglob("*.json"))
        if len(files) >= 2:
            # touch reverse mtime order; builder sorts by path
            files[0].touch()
            files[-1].touch()
        b, rb = pv.build_views(self.root)
        self.assertEqual(pv._canonical_json(a), pv._canonical_json(b))
        self.assertEqual(pv._canonical_json(ra), pv._canonical_json(rb))

    def test_dangling_missing_and_redacted_distinct(self):
        self.store.create_run(self._run())
        dangling = self._event(
            event_id="018f4a31-32af-7abc-8def-0123456789ab",
            source=_ref("finding", "018f4a31-ffff-7abc-8def-0123456789ab"),
            target=_ref("run", RUN_ID),
        )
        self._write_raw_event(dangling)
        redacted = self._event(
            event_id="018f4a31-32b0-7abc-8def-0123456789ab",
            relation="reported-by",
            source=_ref(
                "finding",
                FINDING_ID,
                classification="restricted",
                redacted=True,
            ),
            target=_ref("issue", "0037-17.02"),
        )
        self._write_raw_event(redacted)
        missing_run = self._event(
            event_id="018f4a31-32b1-7abc-8def-0123456789ab",
            source=_ref("finding", FINDING_ID),
            target=_ref("run", "018f4a31-eeee-7abc-8def-0123456789ab"),
        )
        self._write_raw_event(missing_run)
        graph, _reverse = pv.build_views(self.root)
        codes = {item["code"] for item in graph["findings"]}
        self.assertIn("PV-DANGLING-ENDPOINT", codes)
        self.assertIn("PV-REDACTED-ENDPOINT", codes)
        dangling_items = [item for item in graph["findings"] if item["code"] == "PV-DANGLING-ENDPOINT"]
        redacted_items = [item for item in graph["findings"] if item["code"] == "PV-REDACTED-ENDPOINT"]
        self.assertTrue(any(item["identifier"].endswith("ffff-7abc-8def-0123456789ab") or "ffff" in item["identifier"] for item in dangling_items))
        self.assertTrue(all(item.get("path") for item in dangling_items))
        self.assertTrue(all(item["redacted"] is True for item in redacted_items))
        self.assertFalse(any(item.get("redacted") is True and item["code"] == "PV-DANGLING-ENDPOINT" for item in graph["findings"]))

    def test_cycles_recorded_without_traversal_loop(self):
        a = "018f4a31-50aa-7abc-8def-0123456789ab"
        b = "018f4a31-50ab-7abc-8def-0123456789ab"
        self.store.create_run(self._run())
        self.store.create_event(
            self._event(
                event_id="018f4a31-50ac-7abc-8def-0123456789ab",
                relation="supersedes",
                source=_ref("issue", "loop-a"),
                target=_ref("issue", "loop-b"),
            )
        )
        self.store.create_event(
            self._event(
                event_id="018f4a31-50ad-7abc-8def-0123456789ab",
                relation="supersedes",
                source=_ref("issue", "loop-b"),
                target=_ref("issue", "loop-a"),
            )
        )
        graph, _reverse = pv.build_views(self.root)
        cycle_findings = [item for item in graph["findings"] if item["code"] == "PV-CYCLE"]
        self.assertTrue(cycle_findings)
        adjacency = {}
        for edge in graph["edges"]:
            src = f"{edge['source_kind']}|{edge['source']}"
            dst = f"{edge['target_kind']}|{edge['target']}"
            adjacency.setdefault(src, []).append(dst)
        walked = pv.walk_without_loops(adjacency, "issue|issue:loop-a")
        self.assertEqual(len(walked), len(set(walked)))

    def test_stale_and_hand_edited_indexes_rejected(self):
        self._seed_closed_item()
        graph, reverse = pv.build_views(self.root)
        pv.write_views(graph, reverse, self.root)
        pv.verify_document(graph, "graph", self.root)
        tampered = json.loads((self.root / pv.GRAPH_OUT).read_text(encoding="utf-8"))
        tampered["generation_id"] = "sha256:" + "00" * 32
        with self.assertRaises(pv.ProvenanceViewsError) as ctx:
            pv.verify_document(tampered, "graph", self.root)
        self.assertEqual(ctx.exception.code, "PV-STALE-INDEX")
        tampered2 = json.loads((self.root / pv.REVERSE_OUT).read_text(encoding="utf-8"))
        tampered2["issue"]["runs"]["issue:forged"] = ["run:nope"]
        with self.assertRaises(pv.ProvenanceViewsError):
            pv.verify_document(tampered2, "reverse", self.root)

    def test_hermetic_closed_item_survives_later_activity_and_index_rebuild(self):
        aset = self._seed_closed_item()
        graph0, reverse0 = pv.build_views(self.root)
        pv.write_views(graph0, reverse0, self.root)
        baseline_issue = reverse0["issue"]["artifacts"]["issue:0037-17.02"]
        baseline_digest = aset["record"]["set_digest"]
        member_digest = aset["record"]["members"][0]["digest"]
        snapshot = json.loads(json.dumps(reverse0["issue"]))
        closed_evidence = json.loads(json.dumps(reverse0["evidence"]["issue"].get("issue:0037-17.02") or reverse0["issue"]["evidence"]["issue:0037-17.02"]))

        later_run = "018f4a31-99aa-7abc-8def-0123456789ab"
        later_set = "018f4a31-99ad-7abc-8def-0123456789ab"
        later_event = "018f4a31-99ac-7abc-8def-0123456789ab"
        later_finding = "018f4a31-99ab-7abc-8def-0123456789ab"
        self.store.create_run(
            self._run(
                run_id=later_run,
                issue="0037-99",
                outputs=[_ref("artifact-set", later_set)],
                started_at="2026-08-20T00:00:00Z",
                ended_at="2026-08-20T00:01:00Z",
            )
        )
        self.store.create_finding(
            self._finding(
                finding_id=later_finding,
                issue="0037-99",
                detected_at="2026-08-20T00:00:00Z",
                detected_during=_ref("run", later_run),
                evidence=[_ref("artifact", "docs/later.md@sha256:" + "cd" * 32, digest="sha256:" + "cd" * 32)],
            )
        )
        self.store.create_artifact_set(
            self._artifact_set(
                set_id=later_set,
                path="docs/later.md",
                content=b"unrelated later task\n",
                producer=_ref("run", later_run),
                created_at="2026-08-20T00:00:00Z",
            )
        )
        self.store.create_event(
            self._event(
                event_id=later_event,
                occurred_at="2026-08-20T00:00:00Z",
                source=_ref("finding", later_finding),
                target=_ref("run", later_run),
                run=_ref("run", later_run),
            )
        )

        shutil.rmtree(self.root / "provenance" / "_views")
        graph1, reverse1 = pv.build_views(self.root)
        pv.write_views(graph1, reverse1, self.root)
        self.assertEqual(reverse1["issue"]["artifacts"]["issue:0037-17.02"], baseline_issue)
        self.assertEqual(reverse1["issue"]["runs"]["issue:0037-17.02"], snapshot["runs"]["issue:0037-17.02"])
        self.assertEqual(reverse1["issue"]["findings"]["issue:0037-17.02"], snapshot["findings"]["issue:0037-17.02"])
        self.assertEqual(reverse1["issue"]["evidence"]["issue:0037-17.02"], closed_evidence)
        rebuilt_sets = {
            record.get("set_digest")
            for _path, record in pv.collect_sources(self.root / "provenance")["artifact-sets"]
        }
        self.assertIn(baseline_digest, rebuilt_sets)
        member_uris = reverse1["issue"]["artifacts"]["issue:0037-17.02"]
        self.assertTrue(any(member_digest in uri for uri in member_uris))
        self.assertIn("issue:0037-99", reverse1["issue"]["runs"])
        self.assertNotEqual(graph0["generation_id"], graph1["generation_id"])

    def test_does_not_write_immutable_sources(self):
        self._seed_closed_item()
        before = {
            path.as_posix(): path.read_bytes()
            for path in (self.root / "provenance").rglob("*.json")
            if "_views" not in path.as_posix() and "_schema" not in path.as_posix()
        }
        graph, reverse = pv.build_views(self.root)
        pv.write_views(graph, reverse, self.root)
        after = {
            path.as_posix(): path.read_bytes()
            for path in (self.root / "provenance").rglob("*.json")
            if "_views" not in path.as_posix() and "_schema" not in path.as_posix()
        }
        self.assertEqual(before, after)
        self.assertTrue((self.root / pv.GRAPH_OUT).is_file())
        self.assertTrue((self.root / pv.REVERSE_OUT).is_file())

    def test_cli_write_and_verify(self):
        self._seed_closed_item()
        rc = pv.main(["--repository-root", str(self.root), "--write"])
        self.assertEqual(rc, 0)
        rc = pv.main(["--repository-root", str(self.root), "--verify"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
