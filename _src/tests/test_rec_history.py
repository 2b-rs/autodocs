import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lib_docmodel as dm

class TestRecHistoryRendering(unittest.TestCase):
    def test_rec_history_html_empty(self):
        html = dm._render_rec_history_html("REC_1", None, None, 0)
        self.assertEqual(html, "")

    def test_rec_history_html_populated(self):
        status = {
            "state": "valid/auto-approved",
            "reason": "verified against PDF",
            "campaign": "2026-08-pilot"
        }
        history = [
            {
                "date": "2026-08-10",
                "actor": "tool",
                "from": None,
                "to": "valid/unversioned",
                "reason": "initial import",
                "campaign": "2026-08-pilot"
            },
            {
                "date": "2026-08-11",
                "actor": "curator",
                "from": "valid/unversioned",
                "to": "valid/auto-approved",
                "reason": "confirmed",
                "campaign": "2026-08-pilot"
            }
        ]
        html = dm._render_rec_history_html("SWS_LOG_00046", status, history, 1)
        self.assertIn("Status: valid/auto-approved", html)
        self.assertIn("rec-status-valid", html)
        self.assertIn("initial import", html)
        self.assertIn("curator", html)

    def test_render_blocks_includes_history(self):
        blocks = [
            {
                "t": "rec",
                "attrs": [["class", "rec"], ["id", "SWS_TEST_001"]],
                "lead": "",
                "status": {"state": "valid/corrected", "reason": "fixed signature"},
                "history": [{"date": "2026-08-14", "actor": "ai", "from": "invalid/obsolete", "to": "valid/corrected", "reason": "fixed signature", "campaign": "test"}],
                "blocks": [{"t": "html", "html": "<p>Content</p>"}]
            }
        ]
        rendered = "".join(dm.render_blocks(blocks, 1))
        self.assertIn("rec-history-panel", rendered)
        self.assertIn("valid/corrected", rendered)
        self.assertIn("fixed signature", rendered)

if __name__ == "__main__":
    unittest.main()
