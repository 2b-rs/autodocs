import json
import subprocess
import sys
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"


class TestAsofViewCli(unittest.TestCase):
    def test_asof_view_cli_help(self):
        cmd = [sys.executable, str(TOOLS_DIR / "asof_view.py"), "--help"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        self.assertIn("Query coherent point-in-time view", res.stdout)
        self.assertIn("--release", res.stdout)

    def test_asof_view_cli_json(self):
        cmd = [sys.executable, str(TOOLS_DIR / "asof_view.py"), "AUTOSAR/AP/record/A1", "--release", "R25-11", "--json"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        self.assertEqual(data["canonical_id"], "AUTOSAR/AP/record/A1")
        self.assertEqual(data["as_of"]["value"], "R25-11")
        self.assertIn("version", data)

    def test_delta_view_cli_help(self):
        cmd = [sys.executable, str(TOOLS_DIR / "delta_view.py"), "--help"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        self.assertIn("Query delta view since release R", res.stdout)

    def test_delta_view_cli_json(self):
        cmd = [sys.executable, str(TOOLS_DIR / "delta_view.py"), "--release", "R25-11", "--json"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        self.assertIn("baseline", data)
        self.assertIn("changed_requirements", data)


if __name__ == "__main__":
    unittest.main()
