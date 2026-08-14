#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_build_report.py — Tests and fixtures for build report combination and page publishing (Task 0001-10).
"""
import json
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

import build_report


class TestBuildReport(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.orig_reports_dir = build_report.REPORTS_DIR
        self.orig_page_model = build_report.PAGE_MODEL
        build_report.REPORTS_DIR = os.path.join(self.test_dir, "build-reports")
        build_report.PAGE_MODEL = os.path.join(self.test_dir, "build-reports.json")
        os.makedirs(build_report.REPORTS_DIR, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        build_report.REPORTS_DIR = self.orig_reports_dir
        build_report.PAGE_MODEL = self.orig_page_model

    def test_combine_reports_schema_stability(self):
        # Create subreports
        ts = int(time.time())
        merge_rep = {
            "schema_version": "1.0",
            "report_kind": "i18n_merge",
            "tool": "i18n_translate.py",
            "command": "i18n_translate.py merge en",
            "inputs": ["_src/i18n/en/batches/batch_01.json"],
            "started_at": "2026-08-14T15:00:00Z",
            "finished_at": "2026-08-14T15:00:05Z",
            "duration_s": 5.0,
            "exit_code": 0,
            "changed_artifacts": ["_src/i18n/en/segments.json"],
            "counts": {"batches_consumed": 1, "accepted": 10, "rejected": 0, "register_changes": 10},
            "findings": [],
            "run_archive_ref": "output/run-archive/run-test.sh",
        }
        with open(os.path.join(build_report.REPORTS_DIR, f"i18n_merge-{ts}.json"), "w", encoding="utf-8") as f:
            json.dump(merge_rep, f)

        val_rep = {
            "schema_version": "1.0",
            "report_kind": "validate",
            "tool": "validate.py",
            "command": "validate.py",
            "inputs": ["_src/"],
            "started_at": "2026-08-14T15:00:10Z",
            "finished_at": "2026-08-14T15:00:15Z",
            "duration_s": 5.0,
            "exit_code": 0,
            "changed_artifacts": [],
            "counts": {"checks_performed": 10, "findings_by_category": {}, "success": True},
            "findings": [{"category": "notice", "severity": "info", "message": "all good", "ref": "root"}],
            "run_archive_ref": "output/run-archive/run-test.sh",
        }
        with open(os.path.join(build_report.REPORTS_DIR, f"validate-{ts}.json"), "w", encoding="utf-8") as f:
            json.dump(val_rep, f)

        combined, out_path = build_report.combine_reports("output/run-archive/run-test.sh")
        self.assertEqual(combined["schema_version"], "1.0")
        self.assertEqual(combined["report_kind"], "combined")
        self.assertTrue(combined["counts"]["overall_success"])
        self.assertEqual(combined["run_archive_ref"], "output/run-archive/run-test.sh")
        self.assertEqual(len(combined["findings"]), 1)
        self.assertIn("i18n_merge", combined["counts"]["by_stage"])
        self.assertIn("validate", combined["counts"]["by_stage"])

        # Test page model generation
        page_path = build_report.generate_report_page(combined, "output/run-archive/run-test.sh")
        self.assertTrue(os.path.exists(page_path))
        with open(page_path, encoding="utf-8") as f:
            pdata = json.load(f)
        self.assertEqual(pdata["file"], "build-reports.html")
        self.assertTrue(pdata["nolang"])
        self.assertIn("Traceable Build- &amp; Publikations-Report", pdata["main"][0]["html"].replace("& ", "&amp; "))


if __name__ == "__main__":
    unittest.main()
