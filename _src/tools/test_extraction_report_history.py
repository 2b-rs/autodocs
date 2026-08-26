import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import extraction_report


class ExtractionReportHistoryTests(unittest.TestCase):
    def test_existing_version_page_is_byte_identical_after_new_write_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            original_dir = extraction_report.VERSION_PAGES_DIR
            extraction_report.VERSION_PAGES_DIR = directory
            try:
                target = Path(directory) / "extraction-report-v0007.json"
                original = b'{"historical":"evidence"}\n'
                target.write_bytes(original)
                created = extraction_report.write_version_page(
                    {"file": "extraction-report-v0007.html", "new": True},
                    {"version": 7},
                )
                self.assertFalse(created)
                self.assertEqual(target.read_bytes(), original)
            finally:
                extraction_report.VERSION_PAGES_DIR = original_dir

    def test_missing_version_page_is_created_once(self):
        with tempfile.TemporaryDirectory() as directory:
            original_dir = extraction_report.VERSION_PAGES_DIR
            extraction_report.VERSION_PAGES_DIR = directory
            try:
                page = {"file": "extraction-report-v0008.html", "main": []}
                self.assertTrue(extraction_report.write_version_page(page, {"version": 8}))
                self.assertEqual(
                    json.loads((Path(directory) / "extraction-report-v0008.json").read_text()),
                    page,
                )
            finally:
                extraction_report.VERSION_PAGES_DIR = original_dir

    def test_assemble_updates_current_model_and_preserves_archive_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            old_page = extraction_report.PAGE
            extraction_report.PAGE = str(Path(directory) / "extraction-report.json")
            target = Path(extraction_report.PAGE)
            original = b'{"stale":"current working model"}\n'
            target.write_bytes(original)
            try:
                with mock.patch.object(extraction_report, "load_raw_records", return_value={}), \
                     mock.patch.object(extraction_report, "baue", return_value={"file": "new.html"}), \
                     mock.patch.object(extraction_report, "ensure_version_pages") as ensure, \
                     mock.patch.object(extraction_report, "verlinke_startseite") as index:
                    extraction_report.cmd_assemble(directory)
                self.assertEqual(json.loads(target.read_text()), {"file": "new.html"})
                self.assertNotEqual(target.read_bytes(), original)
                ensure.assert_called_once()
                index.assert_called_once()
            finally:
                extraction_report.PAGE = old_page


if __name__ == "__main__":
    unittest.main()
