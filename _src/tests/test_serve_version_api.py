import json
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import serve


class TestServeVersionApi(unittest.TestCase):
    def test_modules_loaded(self):
        self.assertIsNotNone(serve.ASOF)
        self.assertIsNotNone(serve.DELTA)
        self.assertIsNotNone(serve.VS)

    def test_asof_view_functionality(self):
        res = serve.ASOF.as_of_release("AUTOSAR/AP/record/A1", "R25-11")
        self.assertIn("version", res)
        self.assertIn("canonical_id", res)
        self.assertEqual(res["canonical_id"], "AUTOSAR/AP/record/A1")

    def test_delta_view_functionality(self):
        res = serve.DELTA.delta_view(release="R25-11")
        self.assertIn("baseline", res)
        self.assertIn("changed_requirements", res)

    def test_ai_bridge_and_status(self):
        self.assertIsNotNone(serve.AI_BRIDGE)
        status = serve.AI_BRIDGE.get_health_status()
        self.assertIn("ok", status)
        self.assertTrue(status["ok"])
        self.assertIn("providers", status)
        self.assertIn("agy", status["providers"])
        self.assertIn("cursor", status["providers"])



if __name__ == "__main__":
    unittest.main()
