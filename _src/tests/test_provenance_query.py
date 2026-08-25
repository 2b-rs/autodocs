"""Hermetic forward/reverse trace query tests for Task `0037-17.03`."""
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
QUERY_TOOL = ROOT / "_src" / "tools" / "provenance_query.py"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ps = _load("provenance_store", STORE_TOOL)
pv = _load("provenance_views", VIEW_TOOL)
pq = _load("provenance_query", QUERY_TOOL)

COMMIT = "a" * 40
COMMIT2 = "b" * 40
RUN_ID = "018f4a31-32aa-7abc-8def-0123456789ab"
FINDING_ID = "018f4a31-32ab-7abc-8def-0123456789ab"
EVENT_ID = "018f4a31-32ac-7abc-8def-0123456789ab"
SET_ID = "018f4a31-32ad-7abc-8def-0123456789ab"
STAMP = "2026-08-16T08:01:00Z"
ISSUE = "issue:0037-17.03"


def _ref(kind, ident, **extra):
    value = {
        "schema_version": "1.0",
        "kind": kind,
        "uri": f"{kind}:{ident}" if ":" not in str(ident) else ident if str(ident).startswith(kind + ":") else f"{kind}:{ident}",
        "classification": "internal",
    }
    value.update(extra)
    return value


class ProvenanceQueryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.files = {}
        self.store = ps.ProvenanceStore(self.root, file_bytes=self.files.__getitem__)
        (self.root / "_src" / "tools").mkdir(parents=True)
        (self.root / "provenance" / "_schema").mkdir(parents=True)
        shutil.copy(STORE_TOOL, self.root / "_src" / "tools" / "provenance_store.py")
        shutil.copy(VIEW_TOOL, self.root / "_src" / "tools" / "provenance_views.py")
        shutil.copy(QUERY_TOOL, self.root / "_src" / "tools" / "provenance_query.py")
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

    def _run(self, run_id=RUN_ID, issue="0037-17.03", **overrides):
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

    def _finding(self, finding_id=FINDING_ID, issue="0037-17.03", **overrides):
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

    def _artifact_set(self, set_id=SET_ID, path="docs/evidence.md", content=b"closed-item\n", source_commit=COMMIT, **overrides):
        self.files[path] = content
        member = {
            "path": path,
            "digest": ps.sha256_bytes(content),
            "size_bytes": len(content),
            "media_type": "text/markdown",
            "source_commit": source_commit,
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

    def _seed_causal(self):
        self.store.create_run(self._run())
        aset = self.store.create_artifact_set(self._artifact_set())
        digest = aset["record"]["members"][0]["digest"]
        self.store.create_finding(
            self._finding(
                evidence=[
                    _ref("artifact", f"docs/evidence.md@{digest}", digest=digest)
                ]
            )
        )
        self.store.create_event(self._event())
        self.store.create_event(
            self._event(
                event_id="018f4a31-32ae-7abc-8def-0123456789ab",
                relation="verifies",
                source=_ref("evidence", "bundle-1"),
                target=_ref("criterion", "AC-001"),
            )
        )
        graph, reverse = pv.build_views(self.root)
        pv.write_views(graph, reverse, self.root)
        return aset, digest

    def test_forward_and_reverse_file_and_commit(self):
        aset, digest = self._seed_causal()
        fwd = pq.query_trace(self.root, kind="issue", identifier="0037-17.03", direction="forward")
        self.assertTrue(fwd["found"])
        self.assertTrue(any(f["path"] == "docs/evidence.md" and f["digest"] == digest for f in fwd["files"]))
        self.assertTrue(any(c["commit"] == COMMIT for c in fwd["commits"]))
        self.assertIn("criterion:AC-001", fwd["criteria"])
        self.assertTrue(any("docs/evidence.md" in e or e.startswith("evidence:") for e in fwd["evidence"]))

        rev_file = pq.query_trace(
            self.root,
            kind="artifact",
            identifier=f"docs/evidence.md@{digest}",
            direction="reverse",
        )
        self.assertIn(ISSUE, rev_file["issues"])
        self.assertTrue(any(c["commit"] == COMMIT for c in rev_file["commits"]))

        rev_commit = pq.query_trace(self.root, kind="commit", identifier=COMMIT, direction="reverse")
        self.assertIn(ISSUE, rev_commit["issues"])
        self.assertTrue(any(f["digest"] == digest for f in rev_commit["files"]))

        for kind, ident in (
            ("run", RUN_ID),
            ("campaign", "camp-1"),
            ("finding", FINDING_ID),
            ("artifact-set", SET_ID),
            ("criterion", "AC-001"),
            ("evidence", "bundle-1"),
        ):
            result = pq.query_trace(self.root, kind=kind, identifier=ident, direction="forward")
            self.assertTrue(result["found"], msg=kind)

    def test_broken_link_missing_set_redacted_distinct(self):
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
            source=_ref("finding", FINDING_ID, classification="restricted", redacted=True),
            target=_ref("issue", "0037-17.03"),
        )
        self._write_raw_event(redacted)
        pv.write_views(*pv.build_views(self.root), self.root)

        result = pq.query_trace(self.root, kind="issue", identifier="0037-17.03")
        statuses = {d["status"] for d in result["diagnostics"]}
        self.assertIn("dangling", statuses)
        self.assertIn("redacted", statuses)
        dangling_items = [d for d in result["diagnostics"] if d["status"] == "dangling"]
        self.assertTrue(any(d.get("path") for d in dangling_items))
        self.assertTrue(any("ffff" in d["identifier"] for d in dangling_items))
        self.assertFalse(any(d["status"] == "dangling" and d["status"] == "redacted" for d in result["diagnostics"]))

        missing = pq.query_trace(self.root, kind="artifact-set", identifier="018f4a31-dead-7abc-8def-0123456789ab")
        self.assertFalse(missing["found"])
        self.assertTrue(any(d["status"] == "missing" for d in missing["diagnostics"]))
        self.assertEqual(pq.result_exit_code(missing), pq.EXIT_MISSING)

    def test_renamed_file_preserves_historical_trace(self):
        aset, digest = self._seed_causal()
        later_set = "018f4a31-42ad-7abc-8def-0123456789ab"
        later_run = "018f4a31-42aa-7abc-8def-0123456789ab"
        self.store.create_run(
            self._run(
                run_id=later_run,
                outputs=[_ref("artifact-set", later_set)],
                started_at="2026-08-17T00:00:00Z",
                ended_at="2026-08-17T00:01:00Z",
            )
        )
        renamed = self._artifact_set(
            set_id=later_set,
            path="docs/renamed-evidence.md",
            content=b"closed-item\n",
            producer=_ref("run", later_run),
            created_at="2026-08-17T00:00:00Z",
        )
        self.assertEqual(renamed["members"][0]["digest"], digest)
        self.store.create_artifact_set(renamed)
        pv.write_views(*pv.build_views(self.root), self.root)
        rev = pq.query_trace(self.root, kind="artifact", identifier=f"docs/evidence.md@{digest}", direction="reverse")
        paths = {f["path"] for f in rev["files"]}
        self.assertIn("docs/evidence.md", paths)
        self.assertIn("docs/renamed-evidence.md", paths)
        self.assertIn(ISSUE, rev["issues"])

    def test_line_symbol_movement_does_not_invalidate_file_commit_trace(self):
        aset, digest = self._seed_causal()
        fwd_before = pq.query_trace(self.root, kind="issue", identifier="0037-17.03")
        # Working-tree line movement: bytes change, stored artifact identity does not.
        live = self.root / "docs" / "evidence.md"
        live.parent.mkdir(parents=True, exist_ok=True)
        live.write_text("alpha\nbeta\nclosed-item\n", encoding="utf-8")
        fwd_after = pq.query_trace(self.root, kind="issue", identifier="0037-17.03")
        self.assertEqual(
            [(f["path"], f["digest"], f["commit"]) for f in fwd_before["files"]],
            [(f["path"], f["digest"], f["commit"]) for f in fwd_after["files"]],
        )
        self.assertNotIn("line", json.dumps(fwd_after))
        self.assertNotIn("symbol", json.dumps(fwd_after).lower().replace("schema", ""))
        self.assertTrue(all("line" not in f and "symbol" not in f for f in fwd_after["files"]))

    def test_privacy_and_cycle_and_stable_exits(self):
        self.store.create_run(self._run())
        secret = self._artifact_set()
        secret["classification"] = "internal"
        self.store.create_artifact_set(secret)
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
        pv.write_views(*pv.build_views(self.root), self.root)
        public = pq.query_trace(
            self.root,
            kind="issue",
            identifier="0037-17.03",
            max_classification="public",
        )
        self.assertFalse(any(f.get("path") == "docs/evidence.md" for f in public["files"]))
        cycled = pq.query_trace(self.root, kind="issue", identifier="loop-a", depth=8)
        self.assertTrue(cycled["cycles"] or any(h.get("cycle") for h in cycled["hops"]))
        self.assertEqual(
            pq.main(
                [
                    "--repository-root",
                    str(self.root),
                    "--kind",
                    "issue",
                    "--id",
                    "0037-17.03",
                    "--format",
                    "json",
                ]
            ),
            pq.EXIT_OK,
        )
        self.assertEqual(
            pq.main(
                [
                    "--repository-root",
                    str(self.root),
                    "--kind",
                    "issue",
                    "--id",
                    "no-such-issue",
                ]
            ),
            pq.EXIT_MISSING,
        )
        tampered = json.loads((self.root / pv.GRAPH_OUT).read_text(encoding="utf-8"))
        tampered["generation_id"] = "sha256:" + "00" * 32
        (self.root / pv.GRAPH_OUT).write_text(json.dumps(tampered) + "\n", encoding="utf-8")
        self.assertEqual(
            pq.main(
                [
                    "--repository-root",
                    str(self.root),
                    "--kind",
                    "issue",
                    "--id",
                    "0037-17.03",
                    "--require-index",
                ]
            ),
            pq.EXIT_ERROR,
        )

    def test_identical_after_index_regeneration_and_read_only(self):
        self._seed_causal()
        before = {
            path.as_posix(): path.read_bytes()
            for path in (self.root / "provenance").rglob("*.json")
            if "_views" not in path.as_posix() and "_schema" not in path.as_posix()
        }
        a = pq.query_trace(self.root, kind="issue", identifier="0037-17.03", direction="forward")
        b = pq.query_trace(self.root, kind="commit", identifier=COMMIT, direction="reverse")
        shutil.rmtree(self.root / "provenance" / "_views")
        pv.write_views(*pv.build_views(self.root), self.root)
        a2 = pq.query_trace(self.root, kind="issue", identifier="0037-17.03", direction="forward")
        b2 = pq.query_trace(self.root, kind="commit", identifier=COMMIT, direction="reverse")
        self.assertEqual(pq._canonical_json(a), pq._canonical_json(a2))
        self.assertEqual(pq._canonical_json(b), pq._canonical_json(b2))
        after = {
            path.as_posix(): path.read_bytes()
            for path in (self.root / "provenance").rglob("*.json")
            if "_views" not in path.as_posix() and "_schema" not in path.as_posix()
        }
        self.assertEqual(before, after)
        human = pq.format_human(a)
        self.assertIn("FILE docs/evidence.md", human)
        self.assertIn("COMMIT", human)

    def test_type_and_depth_filters(self):
        self._seed_causal()
        shallow = pq.query_trace(self.root, kind="issue", identifier="0037-17.03", depth=0)
        typed = pq.query_trace(
            self.root,
            kind="issue",
            identifier="0037-17.03",
            type_filter=["artifact", "commit"],
        )
        self.assertTrue(shallow["found"])
        self.assertTrue(all(h["kind"] in {"artifact", "commit", "issue"} for h in typed["hops"]))


if __name__ == "__main__":
    unittest.main()
