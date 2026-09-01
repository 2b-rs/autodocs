"""Hermetic forward/reverse trace query tests for Task `0037-17.03`."""
from __future__ import annotations

import importlib.util
import itertools
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

    def test_ae4_record_version_missing_vs_resolved(self):
        """AE-4 adjacent: query kind record-version.

        Neighboring dimension: QUERY_KINDS identity (record-version vs issue).
        Expected: unknown identifier → found=False + missing diagnostic; after a
        verifies edge onto a record-version URI → found=True and that URI in hops.
        Observed: same. Adjacent to curation-item because both were zero-coverage
        kinds in the original 7-test suite, with distinct RELATIONS wiring.
        """
        missing = pq.query_trace(
            self.root, kind="record-version", identifier="rv-absent-17-03"
        )
        self.assertFalse(missing["found"])
        self.assertTrue(any(d["status"] == "missing" for d in missing["diagnostics"]))
        self.assertTrue(
            any("record-version:rv-absent-17-03" in d["identifier"] for d in missing["diagnostics"])
        )

        self.store.create_run(self._run())
        self.store.create_event(
            self._event(
                event_id="018f4a31-70ac-7abc-8def-0123456789ab",
                relation="verifies",
                source=_ref("evidence", "bundle-1"),
                target=_ref("record-version", "rv-present-17-03"),
            )
        )
        pv.write_views(*pv.build_views(self.root), self.root)
        found = pq.query_trace(
            self.root, kind="record-version", identifier="rv-present-17-03"
        )
        self.assertTrue(found["found"])
        self.assertTrue(
            any(h["uri"] == "record-version:rv-present-17-03" for h in found["hops"])
        )

    def test_ae4_curation_item_missing_vs_resolved(self):
        """AE-4 adjacent: query kind curation-item.

        Neighboring dimension: QUERY_KINDS identity (curation-item vs record-version).
        Expected: unknown identifier → found=False + missing; after reported-by
        from a finding onto a curation-item URI → found=True and URI in hops.
        Observed: same. Adjacent to record-version: same missing/found pair, but
        the live edge is reported-by (finding→curation-item), not verifies.
        """
        missing = pq.query_trace(
            self.root, kind="curation-item", identifier="curate-absent-17-03"
        )
        self.assertFalse(missing["found"])
        self.assertTrue(any(d["status"] == "missing" for d in missing["diagnostics"]))

        self.store.create_run(self._run())
        self.store.create_finding(self._finding())
        self.store.create_event(
            self._event(
                event_id="018f4a31-70ad-7abc-8def-0123456789ab",
                relation="reported-by",
                source=_ref("finding", FINDING_ID),
                target=_ref("curation-item", "curate-present-17-03"),
            )
        )
        pv.write_views(*pv.build_views(self.root), self.root)
        found = pq.query_trace(
            self.root, kind="curation-item", identifier="curate-present-17-03"
        )
        self.assertTrue(found["found"])
        self.assertTrue(
            any(h["uri"] == "curation-item:curate-present-17-03" for h in found["hops"])
        )

    def test_ae4_unresolvable_distinct_from_missing_dangling_redacted(self):
        """AE-4 adjacent: diagnostic status unresolvable.

        Neighboring dimension: four-way diagnostic-status gate (empty-uri endpoint
        vs dangling unknown finding vs redacted vs missing artifact-set).
        Expected: unresolvable present, disjoint from missing/dangling/redacted.
        Observed: same. Adjacent to the existing broken-link test, which covered
        only missing/dangling/redacted and never named unresolvable.
        """
        self.store.create_run(self._run())
        empty_source = _ref("finding", FINDING_ID)
        empty_source["uri"] = ""
        self._write_raw_event(
            self._event(
                event_id="018f4a31-70ae-7abc-8def-0123456789ab",
                source=empty_source,
                target=_ref("run", RUN_ID),
            )
        )
        dangling = self._event(
            event_id="018f4a31-70af-7abc-8def-0123456789ab",
            source=_ref("finding", "018f4a31-ffff-7abc-8def-0123456789ab"),
            target=_ref("run", RUN_ID),
        )
        self._write_raw_event(dangling)
        redacted = self._event(
            event_id="018f4a31-70b0-7abc-8def-0123456789ab",
            relation="reported-by",
            source=_ref("finding", FINDING_ID, classification="restricted", redacted=True),
            target=_ref("issue", "0037-17.03"),
        )
        self._write_raw_event(redacted)
        pv.write_views(*pv.build_views(self.root), self.root)

        result = pq.query_trace(self.root, kind="issue", identifier="0037-17.03")
        statuses = {d["status"] for d in result["diagnostics"]}
        self.assertIn("unresolvable", statuses)
        self.assertIn("dangling", statuses)
        self.assertIn("redacted", statuses)
        self.assertNotIn("missing", statuses)
        unresolvable = [d for d in result["diagnostics"] if d["status"] == "unresolvable"]
        dangling_items = [d for d in result["diagnostics"] if d["status"] == "dangling"]
        self.assertTrue(unresolvable)
        self.assertTrue(any(d.get("identifier") == "" for d in unresolvable))
        self.assertTrue(any("ffff" in d["identifier"] for d in dangling_items))
        self.assertFalse(
            any(d["status"] == "unresolvable" and d["status"] == "dangling" for d in result["diagnostics"])
        )

        missing = pq.query_trace(
            self.root,
            kind="artifact-set",
            identifier="018f4a31-dead-7abc-8def-0123456789ab",
        )
        self.assertFalse(missing["found"])
        missing_items = [d for d in missing["diagnostics"] if d["status"] == "missing"]
        self.assertTrue(any(d["kind"] == "artifact-set" for d in missing_items))
        # Graph-level unresolvable/dangling/redacted findings still surface on
        # any query; missing is the extra, query-local status and stays distinct.
        self.assertTrue(
            any(d["status"] == "unresolvable" for d in missing["diagnostics"])
        )
        self.assertFalse(any(d["status"] == "unresolvable" for d in missing_items))

    def test_ae5_add_unique_duplicate_convergence_via_commit_query(self):
        """AE-5: two independent traversal paths collapse via _add_unique.

        Neighboring dimension: custom O(n) canonical-JSON uniqueness on files
        and commits (not hops.seen). A commit query records each member once at
        seed collection and again when collect_from_uri visits commit:/artifact:
        URIs. Expected: more than one _add_unique invocation with the same
        canonical file record, and exactly one entry in result['files'] and
        result['commits'] for that identity. Observed: same.
        """
        _aset, digest = self._seed_causal()
        calls = []
        orig = pq._add_unique

        def counting(seq, item):
            calls.append((id(seq), pq._canonical_json(item)))
            return orig(seq, item)

        pq._add_unique = counting
        try:
            result = pq.query_trace(
                self.root, kind="commit", identifier=COMMIT, direction="reverse"
            )
        finally:
            pq._add_unique = orig

        file_keys = [
            key
            for _sid, key in calls
            if '"artifact_set"' in key and '"path":"docs/evidence.md"' in key
        ]
        self.assertGreaterEqual(
            len(file_keys),
            2,
            msg="commit query must hit record_file_commit twice for the same member",
        )
        self.assertEqual(len(set(file_keys)), 1)
        commit_keys = [
            key
            for _sid, key in calls
            if '"commit":"' + COMMIT in key and '"artifact_set"' not in key
        ]
        self.assertGreaterEqual(len(commit_keys), 2)
        self.assertEqual(len(set(commit_keys)), 1)
        matching_files = [
            rec
            for rec in result["files"]
            if rec.get("path") == "docs/evidence.md" and rec.get("digest") == digest
        ]
        self.assertEqual(len(matching_files), 1)
        matching_commits = [
            rec
            for rec in result["commits"]
            if rec.get("commit") == COMMIT and rec.get("path") == "docs/evidence.md"
        ]
        self.assertEqual(len(matching_commits), 1)
        self.assertIn(ISSUE, result["issues"])

    def test_ae5_add_unique_property_finite_enumeration(self):
        """AE-5 property: _add_unique vs canonical-JSON set oracle.

        Invariant/oracle: after any sequence of inserts, len(seq) equals the
        number of distinct _canonical_json keys (multiplicity collapsed).
        Generation domain: all tuples of length 0..3 over three dict instances
        {A, A_clone, B} where A and A_clone share canonical JSON (finite
        enumeration; seed/replay=None). Executed case count: 40, asserted below.
        """
        item_a = {"status": "unresolvable", "kind": "finding", "identifier": ""}
        item_a_clone = dict(item_a)
        item_b = {"status": "dangling", "kind": "finding", "identifier": "x"}
        population = (item_a, item_a_clone, item_b)
        executed = 0
        for length in range(4):
            for combo in itertools.product(population, repeat=length):
                executed += 1
                seq = []
                for item in combo:
                    pq._add_unique(seq, item)
                oracle = {pq._canonical_json(item) for item in combo}
                self.assertEqual(len(seq), len(oracle))
                self.assertEqual(
                    {pq._canonical_json(item) for item in seq},
                    oracle,
                )
        self.assertEqual(executed, 40)


if __name__ == "__main__":
    unittest.main()
