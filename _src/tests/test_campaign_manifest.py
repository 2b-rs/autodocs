import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import campaign_manifest as cm  # noqa: E402


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
        self.assertIn("queue_snapshot", manifest)
        self.assertEqual(manifest["curator_decisions"], [])
        self.assertEqual(manifest["published_reports"], [])

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
        cm.write_manifest("overwrite-test", trigger="v2", overwrite=True)
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


if __name__ == "__main__":
    unittest.main()
