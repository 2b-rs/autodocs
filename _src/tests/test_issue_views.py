"""Tests for catalog.json and dependency-graph.json (Task 0037-11.02)."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("issue_views", ROOT / "_src/tools/issue_views.py")
VIEWS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VIEWS)
FIXTURES = ROOT / "_src/tests/fixtures/0037-11.02"
GOLDEN_CATALOG = FIXTURES / "golden-catalog.json"
GOLDEN_GRAPH = FIXTURES / "golden-graph.json"
ISSUES = FIXTURES / "issues"


def _validate_schema(instance, schema):
    try:
        import jsonschema
        jsonschema.validate(instance=instance, schema=schema)
        return
    except ImportError:
        pass
    required = schema.get("required", [])
    if not isinstance(instance, dict):
        raise AssertionError("expected object")
    for field in required:
        if field not in instance:
            raise AssertionError(f"missing {field}")
    if schema.get("additionalProperties") is False:
        extra = set(instance) - set(schema.get("properties", {}))
        if extra:
            raise AssertionError(f"unknown fields {extra}")
    props = schema.get("properties", {})
    for key, child in instance.items():
        rule = props.get(key, {})
        if "const" in rule and child != rule["const"]:
            raise AssertionError(f"{key} != {rule['const']}")
        if "pattern" in rule and isinstance(child, str):
            import re
            if not re.fullmatch(rule["pattern"], child):
                raise AssertionError(f"{key} fails {rule['pattern']}")


class IssueViewsTest(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.catalog, self.graph = VIEWS.render(ISSUES, ROOT)

    def test_schema_and_authority(self):
        catalog_schema = json.loads((ROOT / VIEWS.CATALOG_SCHEMA_PATH).read_text())
        graph_schema = json.loads((ROOT / VIEWS.GRAPH_SCHEMA_PATH).read_text())
        _validate_schema(self.catalog, catalog_schema)
        _validate_schema(self.graph, graph_schema)
        self.assertEqual(self.catalog["authority"], "generated-view")
        self.assertEqual(self.graph["authority"], "generated-view")

    def test_byte_determinism(self):
        second_catalog, second_graph = VIEWS.render(ISSUES, ROOT)
        self.assertEqual(VIEWS._canonical_json(self.catalog), VIEWS._canonical_json(second_catalog))
        self.assertEqual(VIEWS._canonical_json(self.graph), VIEWS._canonical_json(second_graph))
        encoded = VIEWS._canonical_json(self.catalog)
        self.assertEqual(encoded, VIEWS._canonical_json(json.loads(encoded)))

    def test_golden_files(self):
        self.assertEqual(VIEWS._canonical_json(self.catalog), GOLDEN_CATALOG.read_text(encoding="utf-8"))
        self.assertEqual(VIEWS._canonical_json(self.graph), GOLDEN_GRAPH.read_text(encoding="utf-8"))

    def test_source_reconciliation(self):
        ids = [item["id"] for item in self.catalog["items"]]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(set(ids), {"0081", "0081-01", "0081-01.01", "0081-02", "0081-03", "0081-04", "0082"})
        by_id = {item["id"]: item for item in self.catalog["items"]}
        self.assertEqual(by_id["0081"]["state"], "in_progress")
        self.assertEqual(by_id["0081-01"]["state"], "open")
        self.assertEqual(by_id["0081-02"]["state"], "blocked")
        self.assertEqual(by_id["0081-04"]["state"], "withdrawn")
        self.assertEqual(by_id["0082"]["state"], "closed")
        self.assertEqual(by_id["0082"]["archive_status"], "archived-not-accepted")
        self.assertEqual(by_id["0082"]["lifecycle_status"], "closed:archived-not-accepted")
        self.assertEqual(by_id["0081-03"]["lifecycle_status"], "malformed")
        self.assertEqual(by_id["0081-03"]["endpoint_status"], "malformed")
        self.assertEqual(by_id["0081"]["url"], "/issues/0081/")
        self.assertEqual(by_id["0081-01"]["url"], "/issues/0081/0081-01/")
        self.assertEqual(by_id["0081-01.01"]["url"], "/issues/0081/0081-01.01/")
        self.assertTrue(by_id["0081"]["source"]["path"].endswith("0081/index.md"))
        self.assertTrue(by_id["0081"]["source"]["sha256"])
        self.assertEqual(by_id["0081"]["criteria"][0]["id"], "AC-001")

    def test_graph_classes_and_endpoints(self):
        nodes = {node["id"]: node for node in self.graph["nodes"]}
        self.assertIn("0090-01", nodes)
        self.assertEqual(nodes["0090-01"]["endpoint_status"], "missing")
        self.assertEqual(nodes["0081-03"]["endpoint_status"], "malformed")
        self.assertEqual(nodes["0082"]["archive_status"], "archived-not-accepted")
        edges = {(edge["source"], edge["target"], edge["kind"]): edge for edge in self.graph["edges"]}
        self.assertEqual(edges[("0081-01", "0081-02", "prerequisite")]["gate"], "start-gate")
        self.assertEqual(edges[("0081", "0082", "prerequisite")]["gate"], "feature-closure")
        self.assertEqual(edges[("0081-02", "0081", "prerequisite")]["gate"], "feature-closure")
        self.assertEqual(edges[("0081-02", "0090-01", "prerequisite")]["endpoint_status"], "missing")
        self.assertEqual(edges[("0081-03", "not a valid id", "prerequisite")]["endpoint_status"], "malformed")
        self.assertEqual(edges[("0081-02", "0081-01", "blocks")]["kind"], "blocks")
        kinds = {node["lifecycle_status"] for node in self.graph["nodes"] if node["endpoint_status"] == "present"}
        self.assertTrue({"open", "in_progress", "blocked", "withdrawn", "closed:archived-not-accepted"} <= kinds)

    def test_no_browser_semantics(self):
        blob = VIEWS._canonical_json(self.catalog) + VIEWS._canonical_json(self.graph)
        for token in ("fillcolor", "penwidth", "html_label", "dot", "svg"):
            self.assertNotIn(token, blob)

    def test_stale_and_manual_edit_detection(self):
        tampered = copy.deepcopy(self.catalog)
        tampered["items"][0]["title"] = "hand edited"
        with self.assertRaises(VIEWS.IssueViewsError):
            VIEWS.verify_document(tampered, "catalog", ROOT, ISSUES)
        stale = copy.deepcopy(self.catalog)
        stale["generation_id"] = "sha256:" + ("0" * 64)
        with self.assertRaises(VIEWS.IssueViewsError):
            VIEWS.verify_document(stale, "catalog", ROOT, ISSUES)
        VIEWS.verify_document(self.catalog, "catalog", ROOT, ISSUES)
        VIEWS.verify_document(self.graph, "graph", ROOT, ISSUES)

    def test_write_and_cli_verify(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            shutil.copytree(ROOT / "issues/_schema", repo / "issues/_schema")
            shutil.copytree(ISSUES, repo / "issues", dirs_exist_ok=True)
            (repo / "_src/tools").mkdir(parents=True)
            shutil.copy2(ROOT / "_src/tools/issue_views.py", repo / "_src/tools/issue_views.py")
            shutil.copy2(ROOT / "_src/tools/issue_store.py", repo / "_src/tools/issue_store.py")
            catalog, graph = VIEWS.render(repo / "issues", repo)
            VIEWS.write_views(catalog, graph, repo)
            self.assertEqual((repo / VIEWS.CATALOG_OUT).read_text(encoding="utf-8"),
                             VIEWS._canonical_json(catalog))
            self.assertEqual(VIEWS.main(["--repository-root", str(repo), "--verify", "--write"]), 0)
            text = (repo / VIEWS.CATALOG_OUT).read_text(encoding="utf-8")
            mutated = json.loads(text)
            mutated["generation_id"] = "sha256:" + ("a" * 64)
            (repo / VIEWS.CATALOG_OUT).write_text(VIEWS._canonical_json(mutated), encoding="utf-8")
            self.assertEqual(VIEWS.main(["--repository-root", str(repo), "--verify"]), 2)

    def test_generation_id_covers_inputs(self):
        digests = self.catalog["digests"]
        for key in ("schema_sha256", "tool_sha256", "config_sha256"):
            self.assertRegex(digests[key], r"^sha256:[0-9a-f]{64}$")
        self.assertTrue(digests["source_sha256"])
        self.assertRegex(self.catalog["generation_id"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(self.graph["generation_id"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(self.graph["digests"]["catalog_generation_id"], self.catalog["generation_id"])
        payload = json.dumps({
            "config": digests["config_sha256"],
            "inputs": digests["source_sha256"],
            "schema": digests["schema_sha256"],
            "tool": digests["tool_sha256"],
        }, sort_keys=True, separators=(",", ":")) + "\n"
        expected = "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self.assertEqual(self.catalog["generation_id"], expected)


if __name__ == "__main__":
    unittest.main()
