import json
import tempfile
import unittest
from pathlib import Path

import build_report
import curation_report
import extraction_report
import open_reviews_report
import traceability_report


class ReportHeaderGeneratorTests(unittest.TestCase):
    def test_all_five_generators_emit_the_shared_report_header(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            originals = (
                build_report.PAGE_MODEL,
                curation_report.PAGE_MODEL,
                curation_report.DATASET_JSON,
                extraction_report.ARCHIVE_PAGE,
                extraction_report.ARCHIVE_DATA_JS,
            )
            build_report.PAGE_MODEL = str(root / "build-reports.json")
            curation_report.PAGE_MODEL = str(root / "curation-report.json")
            curation_report.DATASET_JSON = str(root / "curation-items.json")
            extraction_report.ARCHIVE_PAGE = str(root / "extraction-reports.json")
            extraction_report.ARCHIVE_DATA_JS = str(root / "extraction-reports-data.js")
            try:
                combined = {
                    "counts": {"by_stage": {}, "overall_success": True},
                    "run_archive_ref": "test-run", "started_at": "start",
                    "finished_at": "finish", "findings": [],
                }
                build_report.generate_report_page(combined, "test-run")
                curation_report.generate_curation_report_page([])
                extraction_report.write_archive_page([])
                traceability = traceability_report.baue({
                    "backends": ["builtin"], "database": {"builtin": {
                        "checked": [], "only_in_pdf": [], "only_in_db": [],
                        "diffs": [], "namespace_diffs": [], "empty_extraction": [],
                    }}, "record_counts": {"builtin": 0}, "documents": [],
                    "release": "R25-11", "backend_deviations": [],
                }, "2026-08-21", {}, "fixture.json")
                pages = [
                    json.loads((root / "build-reports.json").read_text()),
                    json.loads((root / "curation-report.json").read_text()),
                    json.loads((root / "extraction-reports.json").read_text()),
                    open_reviews_report.build_page([]),
                    traceability,
                ]
                for page in pages:
                    rendered = "".join(block.get("html", "") for block in page["main"])
                    with self.subTest(page=page["file"]):
                        self.assertIn('data-report-header="0043-05"', rendered)
                        self.assertIn("Erzeugt:", rendered)
                        self.assertIn("Werkzeug:", rendered)
                        self.assertIn("Datenquelle:", rendered)
                        self.assertIn("0019-06", rendered)
            finally:
                (build_report.PAGE_MODEL, curation_report.PAGE_MODEL,
                 curation_report.DATASET_JSON, extraction_report.ARCHIVE_PAGE,
                 extraction_report.ARCHIVE_DATA_JS) = originals


if __name__ == "__main__":
    unittest.main()
