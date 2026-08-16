#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_curation_report.py — Unit tests for unified curation report (0006-09 / 0006-10).
"""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import curation_report


class TestCurationReport(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._orig_page_model = curation_report.PAGE_MODEL
        self._orig_dataset_json = curation_report.DATASET_JSON
        tmp = Path(self._tmpdir.name)
        curation_report.PAGE_MODEL = str(tmp / "curation-report.json")
        curation_report.DATASET_JSON = str(tmp / "curation-items.json")

    def tearDown(self):
        curation_report.PAGE_MODEL = self._orig_page_model
        curation_report.DATASET_JSON = self._orig_dataset_json
        self._tmpdir.cleanup()

    def test_generate_page_surfaces_review_request_requester_fields_and_terminal_statuses(self):
        """0021-06 regression/DoD test: review-request items must show
        requester trust + transport/target-version details, and accepted/
        rejected items must not be silently dropped from the 'other items'
        table."""
        items = [
            {
                "schema": "curation-item@v1",
                "canonical_id": "AUTOSAR/AP/record/REC1",
                "project": "AUTOSAR/AP",
                "release": "R25-11",
                "item_kind": "review-request",
                "origin": "browser",
                "status": "open",
                "subject": "Request re-review",
                "current_state": "github_authenticated",
                "proposed_state": None,
                "evidence": [],
                "counter_evidence": [],
                "decision_basis": {
                    "authoritative_actor": "octocat",
                    "transport": "github_issue",
                    "target_version_id": "AUTOSAR/AP/record/REC1@rel:R25-11#abc123",
                },
                "campaign": "html-curation",
                "created": "2026-08-15T00:00:00Z",
                "claimed_by": None,
                "decided_by": "octocat",
                "completed_at": None,
                "history": [],
                "field": None,
                "current_value": "Browser-raised concern",
                "proposed_value": None,
                "curator": "octocat",
                "target_page": "records/rec1.html",
                "source_file": "spec/curation-queue/open/req-1.json",
            },
            {
                "schema": "curation-item@v1",
                "canonical_id": "AUTOSAR/AP/record/REC2",
                "project": "AUTOSAR/AP",
                "release": "R25-11",
                "item_kind": "review-request",
                "origin": "browser",
                "status": "rejected",
                "subject": "Request re-review",
                "current_state": "self_declared",
                "proposed_state": None,
                "evidence": [],
                "counter_evidence": [],
                "decision_basis": {
                    "transport": "json_export",
                    "target_version_id": "AUTOSAR/AP/record/REC2@rel:R25-11#def456",
                },
                "campaign": "html-curation",
                "created": "2026-08-15T00:00:00Z",
                "claimed_by": None,
                "decided_by": "kurator",
                "completed_at": None,
                "history": [],
                "field": None,
                "current_value": "Lower-trust concern",
                "proposed_value": None,
                "curator": "kurator",
                "target_page": None,
                "source_file": "spec/curation-queue/done/req-2.json",
            },
        ]
        page_path = curation_report.generate_curation_report_page(items)
        with open(page_path, encoding="utf-8") as f:
            pdata = json.load(f)
        html = pdata["main"][0]["html"]
        self.assertIn("github_authenticated", html)
        self.assertIn("octocat", html)
        self.assertIn("github_issue", html)
        self.assertIn("R25-11#abc123", html)
        self.assertIn("self_declared", html)
        self.assertIn("json_export", html)
        self.assertIn("cr-badge-rejected", html)
        self.assertIn("REC2", html)

    def test_collect_and_generate(self):
        items = curation_report.collect_all_curation_items()
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)

        # Verify unified schema on items
        for it in items[:10]:
            self.assertEqual(it.get("schema"), "curation-item@v1")
            self.assertIn("canonical_id", it)
            self.assertIn("project", it)
            self.assertIn("status", it)

        # Generate page model
        page_path = curation_report.generate_curation_report_page(items)
        self.assertTrue(os.path.exists(page_path))
        with open(page_path, encoding="utf-8") as f:
            pdata = json.load(f)
        self.assertEqual(pdata["file"], "curation-report.html")
        self.assertTrue(pdata["nolang"])
        self.assertIn("Zentraler Kurations- & Review-Bericht", pdata["main"][0]["html"])

        # Check export dataset
        self.assertTrue(os.path.exists(curation_report.DATASET_JSON))
        with open(curation_report.DATASET_JSON, encoding="utf-8") as f:
            ddata = json.load(f)
        self.assertEqual(ddata["schema"], "curation-items-export@v1")
        self.assertEqual(ddata["count"], len(items))


if __name__ == "__main__":
    unittest.main()
