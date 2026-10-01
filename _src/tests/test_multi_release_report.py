#!/usr/bin/env python3
"""Tests for multi_release_report delta categorization and CLI."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import multi_release_report as mrr  # noqa: E402
import version_store as vs  # noqa: E402


class MultiReleaseReportTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(self._tmp.cleanup)
        self._orig_root = vs.VERSIONS_ROOT
        vs.VERSIONS_ROOT = Path(self._tmp.name) / "versions"
        self.addCleanup(setattr, vs, "VERSIONS_ROOT", self._orig_root)

    def _record(self, canonical_id: str, release: str, content: str) -> None:
        vs.record_version(canonical_id, release, content)

    def test_delta_categorization_across_releases(self):
        self._record("AUTOSAR/CP/record/ONLY_OLD", "R20-11", "old-only content")
        self._record("AUTOSAR/CP/record/ONLY_NEW", "R25-11", "brand new")
        self._record("AUTOSAR/CP/record/STABLE", "R20-11", "same text")
        self._record("AUTOSAR/CP/record/STABLE", "R25-11", "same text")
        self._record("AUTOSAR/CP/record/EVOLVED", "R20-11", "version one")
        self._record("AUTOSAR/CP/record/EVOLVED", "R25-11", "version two changed")

        report = mrr.generate_release_report("R20-11", "R25-11", platform="CP")

        added_ids = {e["canonical_id"] for e in report["added"]}
        removed_ids = {e["canonical_id"] for e in report["deprecated_or_removed"]}
        unchanged_ids = {e["canonical_id"] for e in report["unchanged"]}
        modified_ids = {e["canonical_id"] for e in report["modified"]}

        self.assertIn("AUTOSAR/CP/record/ONLY_NEW", added_ids)
        self.assertIn("AUTOSAR/CP/record/ONLY_OLD", removed_ids)
        self.assertIn("AUTOSAR/CP/record/STABLE", unchanged_ids)
        self.assertIn("AUTOSAR/CP/record/EVOLVED", modified_ids)
        self.assertEqual(report["summary"]["added"], 1)
        self.assertEqual(report["summary"]["deprecated_or_removed"], 1)
        self.assertEqual(report["summary"]["unchanged"], 1)
        self.assertEqual(report["summary"]["modified"], 1)

        mod = report["modified"][0]
        self.assertNotEqual(mod["from_content_hash"], mod["to_content_hash"])

    def test_platform_filter_excludes_other_kind(self):
        self._record("AUTOSAR/AP/record/AP_ONLY", "R20-11", "ap")
        self._record("AUTOSAR/CP/record/CP_ONLY", "R20-11", "cp")
        self._record("AUTOSAR/AP/record/AP_ONLY", "R25-11", "ap")
        self._record("AUTOSAR/CP/record/CP_ONLY", "R25-11", "cp")

        cp_report = mrr.generate_release_report("R20-11", "R25-11", platform="CP")
        ids = {e["canonical_id"] for e in cp_report["unchanged"]}
        self.assertIn("AUTOSAR/CP/record/CP_ONLY", ids)
        self.assertTrue(all("/CP/" in cid for cid in ids))

        ap_report = mrr.generate_release_report("R20-11", "R25-11", platform="AP")
        ap_ids = {e["canonical_id"] for e in ap_report["unchanged"]}
        self.assertIn("AUTOSAR/AP/record/AP_ONLY", ap_ids)
        self.assertTrue(all("/AP/" in cid for cid in ap_ids))

    def test_cli_json_output_shape(self):
        self._record("AUTOSAR/CP/record/CLI_ITEM", "R20-11", "x")
        self._record("AUTOSAR/CP/record/CLI_ITEM", "R25-11", "x")

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = mrr.main(["--from", "R20-11", "--to", "R25-11", "--platform", "CP", "--json"])
        self.assertEqual(rc, 0)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["from_release"], "R20-11")
        self.assertEqual(payload["to_release"], "R25-11")
        self.assertEqual(payload["platform"], "CP")
        self.assertIn("summary", payload)
        self.assertIn("unchanged", payload)


if __name__ == "__main__":
    unittest.main()
