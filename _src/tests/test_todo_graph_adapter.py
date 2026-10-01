"""Python/JS parity tests for the 0037-12 graph adapter."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "todo_graph_adapter", ROOT / "_src/tools/todo_graph_adapter.py")
ADP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADP)
FIXTURES = ROOT / "_src/tests/fixtures/0037-12"
CORE_JS = ROOT / "tools/todo-graph-core.js"
EMBED = ROOT / "tools/todo-graph-embed.js"
HTML = ROOT / "tools/todo-dependency-graph.html"


def _js(payload_path, extra=""):
    script = r"""
const fs = require('fs');
const path = require('path');
const corePath = process.argv[1];
const text = fs.readFileSync(process.argv[2], 'utf8');
const core = require(corePath);
const mode = process.argv[3];
try {
  if (mode === 'load') {
    const graph = core.loadGraph(text);
    const built = core.buildDot(graph);
    process.stdout.write(JSON.stringify({
      ok: true,
      counts: core.counts(graph),
      built: {
        nodeCount: built.nodeCount,
        edgeCount: built.edgeCount,
        liveFeatureCount: built.liveFeatureCount,
        unresolvedEdgeCount: built.unresolvedEdgeCount,
        unresolvedNodeCount: built.unresolvedNodeCount
      },
      dot: built.dot,
      hasParseTodo: typeof core.parseTodo === 'function'
    }));
  } else if (mode === 'fail') {
    core.loadGraph(text);
    process.stdout.write(JSON.stringify({ok: true}));
  }
} catch (err) {
  process.stdout.write(JSON.stringify({ok: false, error: String(err.message || err)}));
  process.exit(0);
}
"""
    result = subprocess.run(
        ["node", "-e", script, str(CORE_JS), str(payload_path), extra or "load"],
        capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)


class TodoGraphAdapterTest(unittest.TestCase):
    maxDiff = None

    def test_golden_parity_every_node_edge_count(self):
        path = FIXTURES / "golden-graph.json"
        text = path.read_text(encoding="utf-8")
        graph = ADP.load_graph(text)
        py_counts = ADP.counts(graph)
        py_built = ADP.build_dot(graph)
        js = _js(path, "load")
        self.assertTrue(js["ok"], js)
        self.assertFalse(js["hasParseTodo"])
        self.assertEqual(js["counts"], py_counts)
        self.assertEqual(js["built"]["nodeCount"], py_built["nodeCount"])
        self.assertEqual(js["built"]["edgeCount"], py_built["edgeCount"])
        self.assertEqual(js["built"]["liveFeatureCount"], py_built["liveFeatureCount"])
        self.assertEqual(js["built"]["unresolvedEdgeCount"], py_built["unresolvedEdgeCount"])
        self.assertEqual(js["dot"], py_built["dot"])
        self.assertEqual(py_counts["features"], 2)
        self.assertEqual(py_counts["tasks"], 5)
        self.assertEqual(py_counts["subtasks"], 1)
        self.assertEqual(py_counts["withdrawn"], 1)
        self.assertGreaterEqual(py_counts["missing_nodes"], 1)
        self.assertGreaterEqual(py_counts["malformed_nodes"], 1)
        self.assertGreaterEqual(py_counts["start_gate_edges"], 1)
        self.assertGreaterEqual(py_counts["feature_closure_edges"], 1)
        self.assertIn("[w]", py_built["dot"])
        self.assertIn("0090-01 missing", py_built["dot"])
        self.assertIn("not a valid id malformed", py_built["dot"])
        self.assertIn("edgetooltip=\"start-gate\"", py_built["dot"])
        self.assertIn("edgetooltip=\"feature-closure\"", py_built["dot"])
        self.assertIn("URL=\"/issues/0081/\"", py_built["dot"])
        self.assertIn("archived-not-accepted", py_built["dot"])

    def test_withdrawn_cycle_and_feature_prereq_kept(self):
        path = FIXTURES / "withdrawn-and-cycle.json"
        graph = ADP.load_graph(path.read_text(encoding="utf-8"))
        built = ADP.build_dot(graph)
        js = _js(path, "load")
        self.assertEqual(js["dot"], built["dot"])
        self.assertIn("0088-01 [w]", built["dot"])
        self.assertIn('"0088" -> "0089"', built["dot"])
        self.assertIn('"0088-01" -> "0088-02"', built["dot"])
        self.assertIn('"0088-02" -> "0088-01"', built["dot"])
        self.assertEqual(ADP.counts(graph)["withdrawn"], 1)
        self.assertEqual(ADP.MARK_COLORS["w"], "#e8d5ff")

    def test_duplicate_ids_fail_visibly(self):
        path = FIXTURES / "duplicate-ids.json"
        with self.assertRaises(ADP.GraphAdapterError) as ctx:
            ADP.load_graph(path.read_text(encoding="utf-8"))
        self.assertIn("duplicate", str(ctx.exception).lower())
        js = _js(path, "fail")
        self.assertFalse(js["ok"])
        self.assertIn("duplicate", js["error"].lower())

    def test_silently_dropped_endpoint_fails(self):
        path = FIXTURES / "dropped-endpoint.json"
        with self.assertRaises(ADP.GraphAdapterError) as ctx:
            ADP.load_graph(path.read_text(encoding="utf-8"))
        self.assertIn("silently dropped", str(ctx.exception))
        js = _js(path, "fail")
        self.assertFalse(js["ok"])
        self.assertIn("silently dropped", js["error"])

    def test_stale_schema_fails(self):
        path = FIXTURES / "stale-schema.json"
        with self.assertRaises(ADP.GraphAdapterError):
            ADP.load_graph(path.read_text(encoding="utf-8"))
        js = _js(path, "fail")
        self.assertFalse(js["ok"])

    def test_markdown_todo_refused(self):
        path = FIXTURES / "legacy-todo.md"
        with self.assertRaises(ADP.GraphAdapterError) as ctx:
            ADP.load_graph(path.read_text(encoding="utf-8"))
        self.assertIn("Markdown", str(ctx.exception))
        js = _js(path, "fail")
        self.assertFalse(js["ok"])

    def test_consumers_use_same_core_no_parseTodo(self):
        core = CORE_JS.read_text(encoding="utf-8")
        embed = EMBED.read_text(encoding="utf-8")
        html = HTML.read_text(encoding="utf-8")
        self.assertNotIn("function parseTodo", core)
        self.assertNotIn("parseTodo", embed)
        self.assertIn("core.loadGraph", embed)
        self.assertIn("core.buildDot", embed)
        self.assertIn("issues/_views/dependency-graph.json", embed)
        self.assertNotIn("fetch('TODO.md'", embed)
        self.assertNotIn("fetch(\"TODO.md\"", embed)
        self.assertIn("todo-graph-core.js", html)
        self.assertIn("core.loadGraph", html)
        self.assertIn("dependency-graph.json", html)
        self.assertNotIn("../TODO.md", html)
        self.assertIn("typeof core.parseTodo", html)

    def test_empty_live_catalog_parity(self):
        path = ROOT / "issues/_views/dependency-graph.json"
        graph = ADP.load_graph(path.read_text(encoding="utf-8"))
        py_built = ADP.build_dot(graph)
        js = _js(path, "load")
        self.assertEqual(js["dot"], py_built["dot"])
        self.assertEqual(js["counts"], ADP.counts(graph))


if __name__ == "__main__":
    unittest.main()
