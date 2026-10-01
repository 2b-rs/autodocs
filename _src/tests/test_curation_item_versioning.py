import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import curation_item  # noqa: E402
import version_store  # noqa: E402
import evidence_snippet  # noqa: E402

CID = "AUTOSAR/AP/record/SWS_UCM_00999"


class DecidedOnVersionTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._orig_versions_root = version_store.VERSIONS_ROOT
        self._orig_evidence_root = evidence_snippet.EVIDENCE_ROOT
        version_store.VERSIONS_ROOT = Path(self._tmpdir.name) / "versions"
        evidence_snippet.EVIDENCE_ROOT = Path(self._tmpdir.name) / "evidence"

    def tearDown(self):
        version_store.VERSIONS_ROOT = self._orig_versions_root
        evidence_snippet.EVIDENCE_ROOT = self._orig_evidence_root
        self._tmpdir.cleanup()

    def test_from_review_flag_defaults_decided_on_version_none(self):
        item = curation_item.from_review_flag({"id": "SWS_UCM_00999", "reason": "x", "created": "2026-01-01"})
        self.assertIn("decided_on_version", item)
        self.assertIsNone(item["decided_on_version"])

    def test_from_curation_flag_passes_through_decided_on_version(self):
        vid = version_store.record_version(CID, "R25-11", "some requirement text")
        item = curation_item.from_curation_flag({
            "id": "SWS_UCM_00999", "outcome": "accepted", "created": "2026-01-01",
            "decided_on_version": vid,
        })
        self.assertEqual(item["decided_on_version"], vid)

    def test_resolve_decided_on_version_uses_latest(self):
        self.assertIsNone(curation_item.resolve_decided_on_version(CID))
        vid1 = version_store.record_version(CID, "R25-11", "v1 text")
        self.assertEqual(curation_item.resolve_decided_on_version(CID), vid1)
        vid2 = version_store.record_version(CID, "R25-11", "v2 text (changed)")
        self.assertNotEqual(vid1, vid2)
        self.assertEqual(curation_item.resolve_decided_on_version(CID), vid2)

    def test_is_conformant_unaffected_by_new_optional_field(self):
        item = curation_item.from_review_flag({"id": "SWS_UCM_00999", "reason": "x", "created": "2026-01-01"})
        self.assertTrue(curation_item.is_conformant(item))


class EvidenceSnippetTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._orig_versions_root = version_store.VERSIONS_ROOT
        self._orig_evidence_root = evidence_snippet.EVIDENCE_ROOT
        version_store.VERSIONS_ROOT = Path(self._tmpdir.name) / "versions"
        evidence_snippet.EVIDENCE_ROOT = Path(self._tmpdir.name) / "evidence"

    def tearDown(self):
        version_store.VERSIONS_ROOT = self._orig_versions_root
        evidence_snippet.EVIDENCE_ROOT = self._orig_evidence_root
        self._tmpdir.cleanup()

    def test_source_version_is_mandatory(self):
        with self.assertRaises(ValueError):
            evidence_snippet.record_evidence_snippet(None, "text", "reason")
        with self.assertRaises(ValueError):
            evidence_snippet.record_evidence_snippet("not-a-version-id", "text", "reason")

    def test_record_and_list_roundtrip(self):
        vid = version_store.record_version(CID, "R25-11", "requirement text")
        snip = evidence_snippet.record_evidence_snippet(vid, "found X near Y", "missing_space_suspects")
        self.assertEqual(snip["source_version"], vid)
        self.assertEqual(snip["canonical_id"], CID)
        self.assertTrue(snip["id"].startswith("evidence:"))
        listed = evidence_snippet.list_evidence_snippets(CID)
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["id"], snip["id"])

    def test_is_stale_when_requirement_changes(self):
        vid1 = version_store.record_version(CID, "R25-11", "v1 text")
        snip = evidence_snippet.record_evidence_snippet(vid1, "evidence for v1", "manual")
        self.assertFalse(evidence_snippet.is_stale(snip))
        version_store.record_version(CID, "R25-11", "v2 text (changed upstream)")
        self.assertTrue(evidence_snippet.is_stale(snip))

    def test_is_stale_for_unknown_version(self):
        fake = "AUTOSAR/AP/record/SWS_UCM_00999@rel:R25-11#deadbeef"
        snip = {"canonical_id": CID, "source_version": fake}
        self.assertTrue(evidence_snippet.is_stale(snip))


if __name__ == "__main__":
    unittest.main()
