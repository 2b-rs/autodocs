import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import campaign_manifest as cm  # noqa: E402

LEGACY_MANIFEST = {
    "schema": "campaign-manifest@v1",
    "campaign": "requirement-import",
    "trigger": "spec_scrape.py reqs --write-reqs (default --campaign value)",
    "release": None,
    "scope": "additive prose-requirement writes across all modules",
    "created": "2026-08-13T21:18:52+00:00",
    "updated": "2026-08-13T21:19:59+00:00",
    "tool_git_commit": "8a172e9b01402d87ceba7141b9e02be4cc2186ff",
    "backends": [],
    "corpus_hash": "ca284cb3",
    "queue_snapshot": {
        "review-queue": {"open": 349, "claimed": 0, "done": 0},
        "curation-queue": {"open": 34, "claimed": 0, "done": 0},
    },
    "curator_decisions": [],
    "published_reports": [],
}


class CampaignManifestTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        self._orig_spec_root = cm.SPEC_ROOT
        self._orig_campaigns_dir = cm.CAMPAIGNS_DIR
        self._orig_records_dir = cm.RECORDS_DIR
        cm.SPEC_ROOT = base
        cm.CAMPAIGNS_DIR = base / "campaigns"
        cm.RECORDS_DIR = base / "records"
        self.addCleanup(self._restore)

    def _restore(self):
        cm.SPEC_ROOT = self._orig_spec_root
        cm.CAMPAIGNS_DIR = self._orig_campaigns_dir
        cm.RECORDS_DIR = self._orig_records_dir

    def _write_record(self, name: str, body: str) -> Path:
        cm.RECORDS_DIR.mkdir(parents=True, exist_ok=True)
        path = cm.RECORDS_DIR / name
        path.write_text(body, encoding="utf-8")
        return path

    def test_write_manifest_creates_file_with_expected_schema(self):
        path = cm.write_manifest("test-campaign", trigger="unit test", release="R99-99", scope="all")
        self.assertTrue(path.exists())
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "campaign-manifest@v1")
        self.assertEqual(manifest["campaign"], "test-campaign")
        self.assertEqual(manifest["trigger"], "unit test")
        self.assertEqual(manifest["release"], "R99-99")
        self.assertEqual(manifest["scope"], "all")
        self.assertIn("corpus_hash", manifest)
        self.assertEqual(manifest["corpus_hash_role"], "staleness-hint")
        self.assertIn("content_artifacts", manifest)
        self.assertIn("content_set_digest", manifest)
        self.assertIn("queue_snapshot", manifest)
        self.assertEqual(manifest["curator_decisions"], [])
        self.assertEqual(manifest["published_reports"], [])
        self.assertEqual(manifest["disposition"]["kind"], "current")

    def test_write_manifest_is_idempotent_without_overwrite(self):
        p1 = cm.write_manifest("idempotent-test", trigger="first")
        m1 = json.loads(p1.read_text(encoding="utf-8"))
        p2 = cm.write_manifest("idempotent-test", trigger="second (should be ignored)")
        m2 = json.loads(p2.read_text(encoding="utf-8"))
        self.assertEqual(m1["trigger"], m2["trigger"])
        self.assertEqual(m2["trigger"], "first")

    def test_write_manifest_overwrite_refreshes_but_preserves_decisions(self):
        cm.write_manifest("overwrite-test", trigger="v1")
        cm.append_decision("overwrite-test", "decision-1")
        first_bytes = cm.snapshot_dir("overwrite-test")
        before = {p: p.read_bytes() for p in first_bytes.glob("*.json")}
        cm.write_manifest("overwrite-test", trigger="v2", overwrite=True)
        for path, data in before.items():
            self.assertEqual(path.read_bytes(), data)
        manifest = cm.read_manifest("overwrite-test")
        self.assertEqual(manifest["trigger"], "v2")
        self.assertEqual(manifest["curator_decisions"], ["decision-1"])

    def test_append_decision_creates_manifest_if_missing(self):
        cm.append_decision("auto-created", "decision-x")
        manifest = cm.read_manifest("auto-created")
        self.assertIsNotNone(manifest)
        self.assertEqual(manifest["curator_decisions"], ["decision-x"])

    def test_append_decision_is_idempotent(self):
        cm.append_decision("dedup-test", "same-ref")
        cm.append_decision("dedup-test", "same-ref")
        manifest = cm.read_manifest("dedup-test")
        self.assertEqual(manifest["curator_decisions"], ["same-ref"])

    def test_append_report_appends_distinct_refs(self):
        cm.append_report("report-test", "reports/a.html")
        cm.append_report("report-test", "reports/b.html")
        manifest = cm.read_manifest("report-test")
        self.assertEqual(manifest["published_reports"], ["reports/a.html", "reports/b.html"])

    def test_read_manifest_returns_none_when_missing(self):
        self.assertIsNone(cm.read_manifest("does-not-exist"))

    def test_corpus_hash_changes_when_a_record_is_added(self):
        cm.RECORDS_DIR.mkdir(parents=True, exist_ok=True)
        h1 = cm.corpus_hash()
        (cm.RECORDS_DIR / "NEW_RECORD.json").write_text("{}", encoding="utf-8")
        h2 = cm.corpus_hash()
        self.assertNotEqual(h1, h2)

    def test_corpus_hash_none_when_records_dir_missing(self):
        self.assertIsNone(cm.corpus_hash())

    def test_legacy_manifest_receives_explicit_disposition_without_rewrite(self):
        cm.CAMPAIGNS_DIR.mkdir(parents=True, exist_ok=True)
        path = cm.manifest_path("requirement-import")
        original = json.dumps(LEGACY_MANIFEST, indent=2, ensure_ascii=False) + "\n"
        path.write_text(original, encoding="utf-8")
        adapted = cm.adapt_manifest(json.loads(path.read_text(encoding="utf-8")))
        self.assertEqual(adapted["disposition"]["kind"], "legacy")
        self.assertEqual(adapted["disposition"]["adapter"], "campaign-manifest-legacy@v1")
        self.assertEqual(adapted["corpus_hash_role"], "staleness-hint")
        self.assertIsNone(adapted["content_set_digest"])
        self.assertEqual(path.read_text(encoding="utf-8"), original)
        cm.write_manifest(
            "requirement-import",
            trigger="new-run",
            trigger_issue="0037-26.02",
            overwrite=True,
        )
        self.assertEqual(path.read_text(encoding="utf-8"), original)
        current = cm.read_manifest("requirement-import")
        self.assertEqual(current["disposition"]["kind"], "current")
        self.assertEqual(current["trigger_issue"], "0037-26.02")
        legacy_rows = [
            row for row in cm.list_snapshots("requirement-import") if row["disposition"]["kind"] == "legacy"
        ]
        self.assertEqual(len(legacy_rows), 1)

    def test_new_snapshots_are_immutable_and_queryable(self):
        self._write_record("A.json", '{"n":1}')
        path = cm.write_manifest(
            "snap-q",
            trigger="t",
            scope="all",
            trigger_issue="issue:0037-26.02",
            trigger_criterion="criterion:DoD",
            runs=["run:1"],
            source_commit="a" * 40,
            config_commit="b" * 40,
        )
        digest = json.loads(path.read_text(encoding="utf-8"))["content_set_digest"]
        original = path.read_bytes()
        cm.write_manifest("snap-q", trigger="ignored")
        self.assertEqual(path.read_bytes(), original)
        hits = cm.query_snapshots("snap-q", digest)
        self.assertGreaterEqual(len(hits), 1)
        self.assertEqual(hits[-1]["content_set_digest"], digest)
        self.assertEqual(hits[-1]["trigger_issue"], "issue:0037-26.02")
        self.assertEqual(hits[-1]["runs"], ["run:1"])
        self.assertEqual(hits[-1]["source_commit"], "a" * 40)
        self.assertEqual(hits[-1]["config_commit"], "b" * 40)

    def test_content_change_alters_identity_mtime_only_does_not(self):
        record = self._write_record("A.json", '{"n":1}')
        first = cm.content_set_digest()
        hint_before = cm.corpus_hash()
        os.utime(record, (record.stat().st_atime + 10, record.stat().st_mtime + 10))
        self.assertEqual(cm.content_set_digest(), first)
        hint_after_mtime = cm.corpus_hash()
        self.assertNotEqual(hint_before, hint_after_mtime)
        record.write_text('{"n":2}', encoding="utf-8")
        self.assertNotEqual(cm.content_set_digest(), first)
        path_a = cm.write_manifest("id-camp", trigger="a", overwrite=True)
        id_a = json.loads(path_a.read_text(encoding="utf-8"))["content_set_digest"]
        record.write_text('{"n":3}', encoding="utf-8")
        path_b = cm.write_manifest("id-camp", trigger="b", overwrite=True)
        id_b = json.loads(path_b.read_text(encoding="utf-8"))["content_set_digest"]
        self.assertNotEqual(id_a, id_b)
        self.assertEqual(path_a.read_bytes(), path_a.read_bytes())
        self.assertTrue(path_a.exists())
        self.assertNotEqual(path_a.read_bytes(), path_b.read_bytes())

    def test_content_set_identity_property_independent_of_mtime_and_walk_order(self):
        """AE-5: identity is the sorted (path, digest, size) set, not mtimes."""
        import random

        rng = random.Random(20260827)
        executed = 0
        for i in range(25):
            for child in cm.RECORDS_DIR.glob("**/*.json") if cm.RECORDS_DIR.exists() else []:
                child.unlink()
            names = [f"r{j:02d}.json" for j in range(rng.randint(1, 8))]
            rng.shuffle(names)
            bodies = {}
            for name in names:
                bodies[name] = json.dumps({"k": rng.randint(0, 10_000), "i": i})
                self._write_record(name, bodies[name])
            digest = cm.content_set_digest()
            members = cm.content_artifact_members()
            self.assertEqual([m["path"] for m in members], sorted(bodies))
            for rec in cm.RECORDS_DIR.glob("*.json"):
                os.utime(rec, (rec.stat().st_atime + rng.randint(1, 5000), rec.stat().st_mtime + rng.randint(1, 5000)))
            self.assertEqual(cm.content_set_digest(), digest)
            executed += 1
        self.assertEqual(executed, 25)


if __name__ == "__main__":
    unittest.main()
