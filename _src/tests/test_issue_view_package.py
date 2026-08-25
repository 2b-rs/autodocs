"""Package tests for Task 0037-11 (parent). Does not mutate child products."""

from __future__ import annotations

import ast
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PKG = _load("issue_view_package", "_src/tools/issue_view_package.py")
VIEWS = _load("issue_views", "_src/tools/issue_views.py")
LISTS = _load("issue_lists", "_src/tools/issue_lists.py")
FIXTURE_VIEWS = ROOT / "_src/tests/fixtures/0037-11.02/issues"
FIXTURE_LISTS = ROOT / "_src/tests/fixtures/0037-11.01/issues"


class IssueViewPackageTest(unittest.TestCase):
    maxDiff = None

    def test_shared_catalog_not_view_authority(self):
        PKG.assert_no_sqlite_store()
        PKG.assert_lists_consume_views_render()
        catalog, graph = VIEWS.render(FIXTURE_VIEWS, ROOT)
        self.assertEqual(catalog["authority"], "generated-view")
        self.assertEqual(graph["authority"], "generated-view")
        stats = PKG.check_package(catalog, graph)
        self.assertEqual(stats["catalog_count"], 7)
        lists_src = ast.parse((ROOT / "_src/tools/issue_lists.py").read_text(encoding="utf-8"))
        json_loads_of_catalog_file = False
        for node in ast.walk(lists_src):
            if isinstance(node, ast.Constant) and node.value == "issues/_views/catalog.json":
                json_loads_of_catalog_file = True
        self.assertFalse(json_loads_of_catalog_file)

    def test_dropped_prerequisite_edge_fails(self):
        """Falsification: catalog still lists a prereq the graph omitted."""
        catalog, graph = VIEWS.render(FIXTURE_VIEWS, ROOT)
        broken = copy.deepcopy(graph)
        broken["edges"] = [
            edge for edge in broken["edges"]
            if not (edge["source"] == "0081-01" and edge["target"] == "0081-02")
        ]
        with self.assertRaises(PKG.IssueViewPackageError) as ctx:
            PKG.reconcile_ids_states_criteria_edges(catalog, broken)
        self.assertIn("missing catalog edges", str(ctx.exception))

    def test_state_mismatch_adjacent_to_edge_drop(self):
        catalog, graph = VIEWS.render(FIXTURE_VIEWS, ROOT)
        broken = copy.deepcopy(graph)
        for node in broken["nodes"]:
            if node["id"] == "0081":
                node["state"] = "closed"
        with self.assertRaises(PKG.IssueViewPackageError) as ctx:
            PKG.reconcile_ids_states_criteria_edges(catalog, broken)
        self.assertIn("state mismatch", str(ctx.exception))

    def test_missing_catalog_id_adjacent(self):
        catalog, graph = VIEWS.render(FIXTURE_VIEWS, ROOT)
        broken = copy.deepcopy(graph)
        broken["nodes"] = [node for node in broken["nodes"] if node["id"] != "0082"]
        with self.assertRaises(PKG.IssueViewPackageError) as ctx:
            PKG.reconcile_ids_states_criteria_edges(catalog, broken)
        self.assertIn("missing catalog ids", str(ctx.exception))

    def test_lists_partition_matches_catalog(self):
        catalog, groups, _documents = LISTS.render_lists(FIXTURE_LISTS, ROOT)
        _, graph = VIEWS.render(FIXTURE_LISTS, ROOT)
        PKG.check_package(catalog, graph, groups)

    def test_property_id_set_closure_on_views_fixture(self):
        catalog, graph = VIEWS.render(FIXTURE_VIEWS, ROOT)
        items = list(catalog["items"])
        executed = 0
        # Finite domain: every prefix of the sorted catalog (n+1 enumerations).
        for end in range(len(items) + 1):
            subset = items[:end]
            sub_catalog = dict(catalog)
            sub_catalog["items"] = subset
            nodes, edges = VIEWS.build_graph(sub_catalog)
            sub_graph = {"nodes": nodes, "edges": edges}
            stats = PKG.reconcile_ids_states_criteria_edges(sub_catalog, sub_graph)
            self.assertEqual(stats["catalog_count"], end)
            catalog_ids = {item["id"] for item in subset}
            node_ids = {node["id"] for node in nodes}
            self.assertTrue(catalog_ids <= node_ids)
            executed += 1
        self.assertEqual(executed, 8)


if __name__ == "__main__":
    unittest.main()
