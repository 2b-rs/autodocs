"""Dual-format backlog-evolution loader (legacy TODO.md + issue-store)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
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
    return _js_load_text(Path(path).read_text(encoding="utf-8"))


def _js_load_text(text):
    script = r"""
const fs = require('fs');
const core = require(process.argv[1]);
const text = fs.readFileSync(0, 'utf8');
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
        ["node", "-e", script, str(CORE_JS)],
        input=text,
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

    def test_acceptance_promotes_checkbox_to_accepted_mark(self):
        text = (
            "## Feature: 0001 — Alpha\n"
            "- [x] **0001-01** First task **Acceptance: ✓** (2026-08-25, Integrator `belanna`)\n"
            "- [x] **0001-02** Done without acceptance\n"
        )
        parsed = EVO.parse_todo_markdown(text)
        self.assertEqual(parsed["marks"]["0001-01"], "a")
        self.assertEqual(parsed["marks"]["0001-02"], "x")
        js = _js_load_text(text)
        self.assertTrue(js["ok"], js)
        self.assertEqual(js["marks"]["0001-01"], "a")
        self.assertEqual(js["marks"]["0001-02"], "x")

    def test_issue_store_keeps_done_and_promotes_accepted(self):
        self.assertEqual(EVO.lifecycle_to_mark("open", title="still in progress"), " ")
        self.assertEqual(EVO.lifecycle_to_mark("open", prior_mark="x"), "x")
        self.assertEqual(
            EVO.lifecycle_to_mark("open", title="work **Acceptance: ✓** (Integrator)"),
            "a",
        )
        self.assertEqual(EVO.lifecycle_to_mark("closed:completed"), "a")
        self.assertEqual(EVO.lifecycle_to_mark("closed:archived-not-accepted"), "x")

    def test_visualizer_has_no_baked_timeline(self):
        html = (ROOT / "tools/backlog-evolution-visualizer.html").read_text(encoding="utf-8")
        embed = (ROOT / "tools/backlog-evolution-embed.js").read_text(encoding="utf-8")
        self.assertIn("backlog-evolution-core.js", html)
        self.assertIn("BacklogEvolutionCore.loadFromUrls", html)
        self.assertNotIn("let FEATURES = [{", html)
        self.assertIn("tr-backlog-evolution", embed)
        index_json = (ROOT / "_src/sources/pages/index.json").read_text(encoding="utf-8")
        self.assertIn("tr-backlog-evolution", index_json)
        self.assertIn("drawAcceptedStardust", html)
        self.assertIn("function isAccepted", html)

    def test_generated_todo_without_feature_headers(self):
        text = (
            "- [x] **0001-01** (task, open) first **Acceptance: ✓** (Integrator)\n"
            "- [ ] **0001-02** (task, open) still open on 0001\n"
            "- [x] **0037-12** (task, open) freeze Feature 0037\n"
            "- [ ] **0037-10** (task, open) still open\n"
        )
        parsed = EVO.parse_todo_markdown(text)
        self.assertEqual(parsed["fids"], ["0001", "0037"])
        self.assertEqual(parsed["marks"]["0001-01"], "a")
        self.assertEqual(parsed["marks"]["0037-12"], "x")
        self.assertEqual(parsed["marks"]["0037-10"], " ")
        tasks_0001 = {t["id"] for f in parsed["features"] if f["id"] == "0001" for t in f["tasks"]}
        tasks_0037 = {t["id"] for f in parsed["features"] if f["id"] == "0037" for t in f["tasks"]}
        self.assertEqual(tasks_0001, {"0001-01", "0001-02"})
        self.assertEqual(tasks_0037, {"0037-12", "0037-10"})
        js = _js_load_text(text)
        self.assertTrue(js["ok"], js)
        self.assertEqual(js["fids"], ["0001", "0037"])
        self.assertEqual(js["marks"]["0037-12"], "x")
        self.assertEqual(js["marks"]["0001-01"], "a")

    def test_open_checkbox_with_acceptance_is_accepted(self):
        text = (
            "## Feature: 0001 — Alpha\n"
            "- [ ] **0001-01** First task **Acceptance: ✓** (Integrator)\n"
            "- [ ] **0001-02** still open\n"
        )
        parsed = EVO.parse_todo_markdown(text)
        self.assertEqual(parsed["marks"]["0001-01"], "a")
        self.assertEqual(parsed["marks"]["0001-02"], " ")
        js = _js_load_text(text)
        self.assertTrue(js["ok"], js)
        self.assertEqual(js["marks"]["0001-01"], "a")

    def test_generated_open_checkbox_keeps_done_and_accepted(self):
        prior = {"0001-01": "a", "0001-02": "x", "0001-03": "w", "0001-04": " "}
        generated = {"0001-01": " ", "0001-02": " ", "0001-03": " ", "0001-04": " "}
        out = EVO.overlay_keep_completed(generated, prior)
        self.assertEqual(out["0001-01"], "a")
        self.assertEqual(out["0001-02"], "x")
        self.assertEqual(out["0001-03"], "w")
        self.assertEqual(out["0001-04"], " ")
        self.assertTrue(EVO.is_generated_todo_text("- [ ] **0001-01** (task, open) x\n"))
        self.assertFalse(EVO.is_generated_todo_text("## Feature: 0001 — Alpha\n- [ ] **0001-01** x\n"))

    def test_generated_todo_history_does_not_reopen_completed(self):
        tmp = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init"], cwd=tmp, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=tmp, check=True)
        (tmp / "TODO.md").write_text(
            "## Feature: 0001 — Alpha\n"
            "- [x] **0001-01** accepted **Acceptance: ✓** (Integrator)\n"
            "- [x] **0001-02** done without acceptance\n"
            "- [w] **0001-03** withdrawn\n"
            "- [ ] **0001-04** still open\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "TODO.md"], cwd=tmp, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "legacy"], cwd=tmp, check=True, capture_output=True)
        (tmp / "TODO.md").write_text(
            "<!-- GENERATED-VIEW -->\n"
            "- [ ] **0001-01** (task, open) accepted **Acceptance: ✓** (Integrator)\n"
            "- [ ] **0001-02** (task, open) done without acceptance\n"
            "- [ ] **0001-03** (task, open) withdrawn\n"
            "- [ ] **0001-04** (task, open) still open\n"
            "- [ ] **0001-05** (task, open) newly added after cutover\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "TODO.md"], cwd=tmp, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "generated wipe"], cwd=tmp, check=True, capture_output=True)
        payload = EVO.build_from_repo(tmp)
        wipe = [s for s in payload["timeline"] if s["msg"] == "generated wipe"][0]
        self.assertEqual(wipe["marks"]["0001-01"], "a")
        self.assertEqual(wipe["marks"]["0001-02"], "x")
        self.assertEqual(wipe["marks"]["0001-03"], "w")
        self.assertEqual(wipe["marks"]["0001-04"], " ")
        self.assertEqual(wipe["marks"]["0001-05"], " ")


if __name__ == "__main__":
    unittest.main()
