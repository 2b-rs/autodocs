import unittest

from report_page_header import report_page_header


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


if __name__ == "__main__":
    unittest.main()
