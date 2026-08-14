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
