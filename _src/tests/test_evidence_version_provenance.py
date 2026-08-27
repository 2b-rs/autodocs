"""Integration tests for Task 0037-26.03 raw-evidence and record-version envelopes."""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_src" / "tools"
sys.path.insert(0, str(TOOLS))

import evidence_snippet  # noqa: E402
import evidence_version_provenance as evp  # noqa: E402
import provenance_query as pq  # noqa: E402
import provenance_store as ps  # noqa: E402
import version_store  # noqa: E402

CID = "AUTOSAR/AP/record/SWS_UCM_02603"
COMMIT = "c" * 40
ISSUE = "0037-26.03"
CRITERION = "DoD-reverse-trace"
CAMPAIGN = "campaign-0037-26.03"
SOURCE_BYTES = b"RS_PER_00010 persistency label source bytes\n"
SOURCE_PATH = "fixtures/rs_per_00010.txt"


def _prov(**overrides):
    value = {
        "environment": "development-test",
        "classification": "internal",
        "issue": ISSUE,
        "criterion": CRITERION,
        "campaign": CAMPAIGN,
        "tool_commit": COMMIT,
        "config_commit": COMMIT,
        "source_commit": COMMIT,
        "input_members": [
            {
                "path": SOURCE_PATH,
                "bytes": SOURCE_BYTES,
                "media_type": "text/plain",
            }
        ],
    }
    value.update(overrides)
    return value


class EvidenceVersionProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._orig_v = version_store.VERSIONS_ROOT
        self._orig_e = evidence_snippet.EVIDENCE_ROOT
        version_store.VERSIONS_ROOT = self.root / "spec" / "versions"
        evidence_snippet.EVIDENCE_ROOT = self.root / "spec" / "evidence"
        (self.root / "_src" / "tools").mkdir(parents=True)
        (self.root / "provenance" / "_schema").mkdir(parents=True)
        for name in (
            "provenance_store.py",
            "provenance_views.py",
            "provenance_query.py",
        ):
            shutil.copy(TOOLS / name, self.root / "_src" / "tools" / name)
        shutil.copy(
            ROOT / "provenance/_schema/provenance-graph-v1.schema.json",
            self.root / "provenance/_schema/provenance-graph-v1.schema.json",
        )
        shutil.copy(
            ROOT / "provenance/_schema/provenance-reverse-v1.schema.json",
            self.root / "provenance/_schema/provenance-reverse-v1.schema.json",
        )

    def tearDown(self):
        version_store.VERSIONS_ROOT = self._orig_v
        evidence_snippet.EVIDENCE_ROOT = self._orig_e
        self.tmp.cleanup()

    def _envelope(self, **overrides):
        req = _prov(**overrides)
        req["store_root"] = self.root
        files = {
            m["path"]: (m["bytes"] if isinstance(m["bytes"], bytes) else m["bytes"].encode("utf-8"))
            for m in req["input_members"]
        }

        def _bytes(path):
            if path not in files:
                raise FileNotFoundError(path)
            return files[path]

        req["file_bytes"] = _bytes
        return req

    def test_immutable_raw_evidence_and_version_history(self):
        env = self._envelope()
        vid1 = version_store.record_version(CID, "R25-11", "first snapshot", provenance=env)
        jsonl = next(version_store.VERSIONS_ROOT.rglob("*.jsonl"))
        before = jsonl.read_bytes()
        vid2 = version_store.record_version(CID, "R25-11", "second snapshot", provenance=env)
        self.assertNotEqual(vid1, vid2)
        after_second = jsonl.read_bytes()
        self.assertTrue(after_second.startswith(before))
        self.assertEqual(before, jsonl.read_bytes()[: len(before)])
        lines = [ln for ln in jsonl.read_text(encoding="utf-8").splitlines() if ln]
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0])["version_id"], vid1)
        self.assertEqual(json.loads(lines[0])["content"], "first snapshot")
        version_store.record_version(CID, "R25-11", "second snapshot", provenance=env)
        self.assertEqual(jsonl.read_bytes(), after_second)

        snip = evidence_snippet.record_evidence_snippet(
            vid2, "raw slice from source bytes", "extract", provenance=env
        )
        evid_path = next(evidence_snippet.EVIDENCE_ROOT.rglob("*.jsonl"))
        evid_before = evid_path.read_bytes()
        evidence_snippet.record_evidence_snippet(
            vid2, "later observation", "extract", provenance=env
        )
        evid_after = evid_path.read_bytes()
        self.assertTrue(evid_after.startswith(evid_before))
        first = json.loads(evid_before.splitlines()[0])
        self.assertEqual(first["id"], snip["id"])
        self.assertEqual(first["text"], "raw slice from source bytes")

    def test_exact_version_linkage(self):
        env = self._envelope()
        vid = version_store.record_version(CID, "R25-11", "linked content", provenance=env)
        snip = evidence_snippet.record_evidence_snippet(
            vid, "pin to exact version", "link", provenance=env
        )
        self.assertEqual(snip["source_version"], vid)
        self.assertEqual(snip["provenance"]["source_version"], vid)
        listed = version_store.get_version(vid)
        self.assertEqual(listed["content"], "linked content")
        self.assertEqual(snip["provenance"]["issue"], ISSUE)
        self.assertEqual(snip["provenance"]["criterion"], CRITERION)
        self.assertNotEqual(listed["provenance"]["run_id"], "")
        self.assertNotEqual(snip["provenance"]["run_id"], "")
        self.assertTrue(listed["provenance"]["source_content_digest"].startswith("sha256:"))
        self.assertEqual(
            listed["provenance"]["source_content_digest"],
            ps.sha256_bytes(b"linked content"),
        )

    def test_legacy_unknown_is_not_backfilled(self):
        vid = version_store.record_version(CID, "R25-11", "legacy-only content")
        versions = version_store.list_versions(CID)
        self.assertEqual(len(versions), 1)
        self.assertNotIn("provenance", versions[0])
        disp = evp.legacy_disposition(versions[0])
        self.assertEqual(disp["confidence"], "unknown")
        self.assertIs(disp["backfill"], False)
        self.assertIsNone(disp["envelope"])
        env = self._envelope()
        again = version_store.record_version(
            CID, "R25-11", "legacy-only content", provenance=env
        )
        self.assertEqual(again, vid)
        after = version_store.list_versions(CID)
        self.assertEqual(len(after), 1)
        self.assertNotIn("provenance", after[0])
        self.assertFalse((self.root / "provenance" / "runs").exists())

        snip = evidence_snippet.record_evidence_snippet(vid, "legacy snippet", "old")
        self.assertNotIn("provenance", snip)
        evidence_snippet.record_evidence_snippet(
            vid, "legacy snippet", "old", provenance=env
        )
        listed = evidence_snippet.list_evidence_snippets(CID)
        self.assertEqual(len(listed), 1)
        self.assertNotIn("provenance", listed[0])
        self.assertEqual(evp.legacy_disposition(listed[0])["confidence"], "unknown")

    def test_duplicate_prevention(self):
        env = self._envelope()
        vid = version_store.record_version(CID, "R25-11", "dup content", provenance=env)
        first = evidence_snippet.record_evidence_snippet(
            vid, "same text", "same-reason", provenance=env
        )
        second = evidence_snippet.record_evidence_snippet(
            vid, "same text", "same-reason", provenance=env
        )
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(evidence_snippet.list_evidence_snippets(CID)), 1)
        path = next(evidence_snippet.EVIDENCE_ROOT.rglob("*.jsonl"))
        self.assertEqual(len([ln for ln in path.read_text().splitlines() if ln]), 1)
        self.assertEqual(
            version_store.record_version(CID, "R25-11", "dup content", provenance=env),
            vid,
        )
        vpath = next(version_store.VERSIONS_ROOT.rglob("*.jsonl"))
        self.assertEqual(len([ln for ln in vpath.read_text().splitlines() if ln]), 1)

    def test_reject_synthetic_relabeled_production(self):
        env = self._envelope(environment="production", synthetic_reason="unittest fixture")
        with self.assertRaises(evp.EnvelopeError) as ctx:
            version_store.record_version(CID, "R25-11", "fixture", provenance=env)
        self.assertEqual(ctx.exception.code, "EV-SYNTHETIC-PRODUCTION")
        env2 = self._envelope(environment="synthetic")
        with self.assertRaises(evp.EnvelopeError) as ctx2:
            version_store.record_version(CID, "R25-11", "fixture2", provenance=env2)
        self.assertEqual(ctx2.exception.code, "EV-SYNTHETIC-REASON")

    def test_reverse_trace_to_source_bytes_and_trigger(self):
        env = self._envelope(environment="synthetic", synthetic_reason="hermetic 0037-26.03 fixture")
        vid = version_store.record_version(CID, "R25-11", "traced content", provenance=env)
        snip = evidence_snippet.record_evidence_snippet(
            vid, "raw evidence text", "trace", provenance=env
        )
        digest = ps.sha256_bytes(SOURCE_BYTES)
        evid_uuid = snip["id"].split(":", 1)[1]
        rev_file = pq.query_trace(
            self.root,
            kind="artifact",
            identifier=f"{SOURCE_PATH}@{digest}",
            direction="reverse",
        )
        self.assertTrue(rev_file["found"])
        self.assertIn(f"issue:{ISSUE}", rev_file["issues"])
        self.assertTrue(any(f["digest"] == digest for f in rev_file["files"]))

        rev_evid = pq.query_trace(
            self.root, kind="evidence", identifier=evid_uuid, direction="reverse"
        )
        self.assertTrue(rev_evid["found"])
        self.assertIn(f"issue:{ISSUE}", rev_evid["issues"])

        rev_ver = pq.query_trace(
            self.root, kind="record-version", identifier=vid, direction="reverse"
        )
        self.assertTrue(rev_ver["found"])
        self.assertIn(f"issue:{ISSUE}", rev_ver["issues"])

        fwd = pq.query_trace(self.root, kind="issue", identifier=ISSUE, direction="forward")
        self.assertTrue(fwd["found"])
        self.assertTrue(any(f.get("digest") == digest for f in fwd["files"]))

    def test_written_records_match_provenance_schema_required_fields(self):
        """Bind to provenance/_schema v1; do not invent a local fork (dispatcher addendum)."""
        env = self._envelope()
        version_store.record_version(CID, "R25-11", "schema-bound", provenance=env)
        schema_dir = ROOT / "provenance" / "_schema"
        run_schema = json.loads((schema_dir / "run-v1.schema.json").read_text(encoding="utf-8"))
        event_schema = json.loads((schema_dir / "provenance-event-v1.schema.json").read_text(encoding="utf-8"))
        aset_schema = json.loads((schema_dir / "artifact-set-v1.schema.json").read_text(encoding="utf-8"))
        run_path = next((self.root / "provenance" / "runs").glob("*.json"))
        run = json.loads(run_path.read_text(encoding="utf-8"))
        for key in run_schema["required"]:
            self.assertIn(key, run)
        self.assertEqual(run["schema_version"], "1.0")
        extra_run = set(run) - set(run_schema["properties"])
        self.assertEqual(extra_run, set())
        event = json.loads(next((self.root / "provenance" / "events").rglob("*.json")).read_text())
        for key in event_schema["required"]:
            self.assertIn(key, event)
        extra_ev = set(event) - set(event_schema["properties"])
        self.assertEqual(extra_ev, set())
        aset = json.loads(next((self.root / "provenance" / "artifact-sets").glob("*.json")).read_text())
        for key in aset_schema["required"]:
            self.assertIn(key, aset)
        extra_as = set(aset) - set(aset_schema["properties"])
        self.assertEqual(extra_as, set())

    def test_ae_duplicate_prevention_red_on_baseline(self):
        """AE-3: identical (source_version, text, reason) duplicated on 2064704457, unique on candidate.

        Adjacent: (AE-4) legacy unknown is not backfilled; synthetic cannot be production.
        """
        import subprocess
        import types

        src = subprocess.check_output(
            [
                "git",
                "-C",
                str(ROOT),
                "show",
                "2064704457f98c66fb6f77ad3c263415864fe2ff:_src/tools/evidence_snippet.py",
            ],
            text=True,
        )
        baseline = types.ModuleType("evidence_snippet_baseline")
        baseline.__file__ = str(TOOLS / "evidence_snippet.py")
        exec(compile(src, "evidence_snippet_baseline.py", "exec"), baseline.__dict__)
        baseline.EVIDENCE_ROOT = evidence_snippet.EVIDENCE_ROOT
        vid = version_store.record_version(CID, "R25-11", "ae content")
        baseline.record_evidence_snippet(vid, "same", "ae")
        baseline.record_evidence_snippet(vid, "same", "ae")
        self.assertEqual(len(baseline.list_evidence_snippets(CID)), 2)
        # Candidate writers on a fresh root:
        evidence_snippet.EVIDENCE_ROOT = self.root / "spec" / "evidence-candidate"
        a = evidence_snippet.record_evidence_snippet(vid, "same", "ae")
        b = evidence_snippet.record_evidence_snippet(vid, "same", "ae")
        self.assertEqual(a["id"], b["id"])
        self.assertEqual(len(evidence_snippet.list_evidence_snippets(CID)), 1)


if __name__ == "__main__":
    unittest.main()
