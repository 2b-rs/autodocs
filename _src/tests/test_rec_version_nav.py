import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import lib_docmodel as dm
import version_store as vs


class TestRecVersionNav(unittest.TestCase):
    def test_version_badge_rendered(self):
        status = {"state": "valid/auto-approved", "reason": "verified"}
        history = [{"date": "2026-08-10", "actor": "tool", "to": "valid/auto-approved"}]
        html = dm._render_rec_history_html("SWS_CORE_00017", status, history)
        self.assertIn("rec-version-badge", html)
        self.assertIn("Version:", html)
        self.assertIn("Active Version", html)

    def test_version_nav_container_and_controls(self):
        status = {"state": "valid/unmigrated"}
        history = [{"date": "2026-08-13", "actor": "tool", "to": "valid/unmigrated"}]
        html = dm._render_rec_history_html("SWS_CORE_00017", status, history)
        self.assertIn("rec-version-nav", html)
        self.assertIn('data-canonical-id="AUTOSAR/AP/record/SWS_CORE_00017"', html)
        self.assertIn("rec-asof-select", html)
        self.assertIn("rec-asof-btn", html)
        self.assertIn("rec-asof-display", html)
        self.assertIn("Point-in-Time History:", html)

    def test_multi_version_timeline_rendering(self):
        cid = "AUTOSAR/AP/record/TEST_MULTI_VER"
        vs.record_version(cid, "R20-11", "Initial content")
        vs.record_version(cid, "R25-11", "Updated content")

        status = {"state": "valid/corrected"}
        history = [{"date": "2026-08-14", "actor": "curator", "to": "valid/corrected"}]
        html = dm._render_rec_history_html(cid, status, history)

        self.assertIn("rec-version-timeline", html)
        self.assertIn("Recorded Revisions (2)", html)
        self.assertIn("R20-11", html)
        self.assertIn("R25-11", html)
        self.assertIn("data-inspect-version", html)

    def tearDown(self):
        test_file = Path(__file__).resolve().parents[1] / "spec" / "versions" / "AUTOSAR" / "AP" / "record" / "TEST_MULTI_VER.jsonl"
        if test_file.exists():
            test_file.unlink()



if __name__ == "__main__":
    unittest.main()
