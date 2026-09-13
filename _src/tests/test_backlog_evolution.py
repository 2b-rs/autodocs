"""Dual-format backlog-evolution loader (legacy TODO.md + issue-store)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "backlog_evolution", ROOT / "_src/tools/backlog_evolution.py")
EVO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVO)
FIXTURES = ROOT / "_src/tests/fixtures/backlog-evolution"
CORE_JS = ROOT / "tools/backlog-evolution-core.js"
GOLDEN_GRAPH = ROOT / "_src/tests/fixtures/0037-12/golden-graph.json"


def _js_load(path):
    script = r"""
const fs = require('fs');
const core = require(process.argv[1]);
const text = fs.readFileSync(process.argv[2], 'utf8');
try {
  const payload = core.load(text);
  process.stdout.write(JSON.stringify({
    ok: true,
    nfeatures: payload.features.length,
    ntimeline: payload.timeline.length,
    source: payload.source,
    fids: payload.timeline[0] && payload.timeline[0].fids,
    marks: payload.timeline[payload.timeline.length-1] && payload.timeline[payload.timeline.length-1].marks,
    firstId: payload.features[0] && payload.features[0].id
  }));
} catch (err) {
  process.stdout.write(JSON.stringify({ok: false, error: String(err.message || err)}));
  process.exit(0);
}
"""
    result = subprocess.run(
        ["node", "-e", script, str(CORE_JS), str(path)],
        capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)


class BacklogEvolutionTest(unittest.TestCase):
    maxDiff = None

    def test_legacy_todo_markdown(self):
        text = (FIXTURES / "todo-v1.md").read_text(encoding="utf-8")
        payload = EVO.load_evolution(text)
        self.assertEqual(payload["source"]["format"], "todo.md")
        self.assertEqual([f["id"] for f in payload["features"]], ["0001", "0002"])
        marks = payload["timeline"][0]["marks"]
        self.assertEqual(marks["0001-01"], " ")
        self.assertEqual(marks["0001-02"], "p")
        self.assertEqual(marks["0002-01"], "x")
        prereqs = payload["features"][0]["tasks"][1]["prereqs"]
        self.assertEqual(prereqs[0]["to"], "0001-01")
        js = _js_load(FIXTURES / "todo-v1.md")
        self.assertTrue(js["ok"], js)
        self.assertEqual(js["nfeatures"], 2)
        self.assertEqual(js["marks"]["0002-01"], "x")

    def test_legacy_baked_object(self):
        path = FIXTURES / "legacy-baked.json"
        payload = EVO.load_evolution(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["source"]["format"], "legacy-baked")
        self.assertEqual(payload["features"][0]["id"], "0099")
        js = _js_load(path)
        self.assertTrue(js["ok"], js)
        self.assertEqual(js["firstId"], "0099")

    def test_issue_graph_new_format(self):
        text = GOLDEN_GRAPH.read_text(encoding="utf-8")
        payload = EVO.load_evolution(text)
        self.assertEqual(payload["source"]["format"], "issue-dependency-graph@v1")
        ids = [f["id"] for f in payload["features"]]
        self.assertIn("0081", ids)
        self.assertIn("0082", ids)
        marks = payload["timeline"][0]["marks"]
        self.assertEqual(marks["0082"], "x")
        self.assertEqual(marks["0081"], "p")
        js = _js_load(GOLDEN_GRAPH)
        self.assertTrue(js["ok"], js)
        self.assertEqual(js["marks"]["0082"], "x")

    def test_v1_roundtrip(self):
        v1 = EVO.load_evolution((FIXTURES / "todo-v1.md").read_text(encoding="utf-8"))
        packed = json.dumps(v1)
        again = EVO.load_evolution(packed)
        self.assertEqual(again["schema"], "backlog-evolution@v1")
        self.assertEqual([f["id"] for f in again["features"]], ["0001", "0002"])

    def test_mark_diff_between_todo_snapshots(self):
        first = EVO.parse_todo_markdown((FIXTURES / "todo-v1.md").read_text(encoding="utf-8"))
        second = EVO.parse_todo_markdown((FIXTURES / "todo-v2.md").read_text(encoding="utf-8"))
        changes = EVO._diff_snapshots(
            first["fids"], first["marks"], EVO._task_text_map(first["features"]),
            second["fids"], second["marks"], EVO._task_text_map(second["features"]),
            {f["id"]: f for f in second["features"]},
        )
        kinds = {(c["type"], c.get("tid") or c.get("fid")) for c in changes}
        self.assertIn(("task_mark", "0001-01"), kinds)
        self.assertIn(("task_add", "0002-02"), kinds)

    def test_visualizer_has_no_baked_timeline(self):
        html = (ROOT / "tools/backlog-evolution-visualizer.html").read_text(encoding="utf-8")
        embed = (ROOT / "tools/backlog-evolution-embed.js").read_text(encoding="utf-8")
        self.assertIn("backlog-evolution-core.js", html)
        self.assertIn("BacklogEvolutionCore.loadFromUrls", html)
        self.assertNotIn("let FEATURES = [{", html)
        self.assertIn("tr-backlog-evolution", embed)
        index_json = (ROOT / "_src/sources/pages/index.json").read_text(encoding="utf-8")
        self.assertIn("tr-backlog-evolution", index_json)


if __name__ == "__main__":
    unittest.main()
