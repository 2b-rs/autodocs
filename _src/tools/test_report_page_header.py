import unittest

from report_page_header import report_page_header, upsert_report_page_header


class ReportPageHeaderTests(unittest.TestCase):
    def test_header_has_required_metadata_and_s_core_evidence_reference(self):
        header = report_page_header(
            generator="tool.py",
            data_source="records.json",
            purpose="Explains the report.",
            generated_at="2026-08-21T09:07:00Z",
        )
        for expected in (
            'data-report-header="0043-05"', "Erzeugt:", "2026-08-21T09:07:00Z",
            "Werkzeug:", "tool.py", "Datenquelle:", "records.json",
            "Explains the report.", "0019-06", "Eclipse S-Core",
        ):
            self.assertIn(expected, header)

    def test_upsert_inserts_and_then_replaces_one_generated_header(self):
        page = {"main": [{"t": "html", "html": "<h1>Report data</h1>"}]}
        upsert_report_page_header(
            page, generator="first.py", data_source="first.json",
            purpose="First purpose", generated_at="2026-08-21T09:07:00Z",
        )
        upsert_report_page_header(
            page, generator="second.py", data_source="second.json",
            purpose="Second purpose", generated_at="2026-08-22T16:41:00Z",
        )
        body = page["main"][0]["html"]
        self.assertEqual(body.count('data-report-header="0043-05"'), 1)
        self.assertIn("second.py", body)
        self.assertIn("Second purpose", body)
        self.assertIn("<h1>Report data</h1>", body)
        self.assertNotIn("first.py", body)


if __name__ == "__main__":
    unittest.main()
