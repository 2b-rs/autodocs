"""Tests for catalog.json and dependency-graph.json (Task 0037-11.02)."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import itertools
import json
import math
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

    def test_archive_status_closed_disposition_literals(self):
        """AE-4 adjacent: each closed-only disposition when state==closed.

        Neighboring dimension: disposition literal (completed/wontfix/superseded/
        duplicate/cancelled) vs the already-asserted archived-not-accepted path.
        Expected: _archive_status returns that exact literal.
        Observed: asserted below.
        Why adjacent: same second-branch membership, different literal; a typo in
        one member would pass the archived-not-accepted fixture alone.
        """
        closed_only = ("completed", "wontfix", "superseded", "duplicate", "cancelled")
        for disposition in closed_only:
            observed = VIEWS._archive_status("closed", {"disposition": disposition})
            self.assertEqual(observed, disposition, disposition)

    def test_archive_status_open_state_guard(self):
        """AE-4 adjacent: state==closed guard for those five literals.

        Neighboring dimension: state (open vs closed) with the same disposition.
        Expected: None (not archived) when state is not closed.
        Observed: asserted below.
        Why adjacent: dropping the state==closed guard would still pass the
        closed-literal cases and the 0082 archived-not-accepted fixture.
        """
        closed_only = ("completed", "wontfix", "superseded", "duplicate", "cancelled")
        for disposition in closed_only:
            observed = VIEWS._archive_status("open", {"disposition": disposition})
            self.assertIsNone(observed, disposition)
            observed_progress = VIEWS._archive_status(
                "in_progress", {"disposition": disposition})
            self.assertIsNone(observed_progress, disposition)

    def test_archive_status_archived_not_accepted_unconditional(self):
        """AE-4 adjacent: archived-not-accepted ignores the closed guard.

        Neighboring dimension: first-branch special case vs second-branch guard.
        Expected: 'archived-not-accepted' even when state is open.
        Observed: asserted below.
        Why adjacent: the five closed-only literals require closed; this one does
        not. Collapsing both branches would fail this case.
        """
        observed_open = VIEWS._archive_status(
            "open", {"disposition": "archived-not-accepted"})
        self.assertEqual(observed_open, "archived-not-accepted")
        observed_closed = VIEWS._archive_status(
            "closed", {"disposition": "archived-not-accepted"})
        self.assertEqual(observed_closed, "archived-not-accepted")

    def test_archive_status_unrecognized_and_malformed(self):
        """AE-4 adjacent: non-member disposition and malformed closure.

        Neighboring dimension: recognized vs unrecognized / malformed payload.
        Expected: None.
        Observed: asserted below.
        Why adjacent: an unknown string must not be echoed as archive_status.
        """
        self.assertIsNone(VIEWS._archive_status("closed", {"disposition": "unknown"}))
        self.assertIsNone(VIEWS._archive_status("closed", {"malformed": True}))
        self.assertIsNone(VIEWS._archive_status("closed", None))

    def test_reject_browser_keys_positive_raise_all_members(self):
        """AE-4 adjacent: every real BROWSER_KEYS member raises at top level.

        Neighboring dimension: which of the 11 keys is present (not fillcolor).
        Expected: IssueViewsError naming that key at $.
        Observed: asserted below.
        Why adjacent: test_no_browser_semantics only checks absence on clean
        output; deleting _reject_browser_keys would still pass that test.
        """
        expected_keys = (
            "color", "fill", "fontcolor", "stroke", "dot", "svg", "style",
            "shape", "penwidth", "html_label", "cluster_color",
        )
        self.assertEqual(set(expected_keys), set(VIEWS.BROWSER_KEYS))
        self.assertNotIn("fillcolor", VIEWS.BROWSER_KEYS)
        for key in expected_keys:
            with self.subTest(key=key, position="top"):
                with self.assertRaises(VIEWS.IssueViewsError) as ctx:
                    VIEWS._reject_browser_keys({key: "x"})
                message = str(ctx.exception)
                self.assertIn(key, message)
                self.assertIn("at $", message)

    def test_reject_browser_keys_nested_raise_all_members(self):
        """AE-4 adjacent: same 11 keys nested (dict-in-list-in-dict).

        Neighboring dimension: nesting depth / path, same key set.
        Expected: IssueViewsError with path $.{wrapper}[0].{key}.
        Observed: asserted below.
        Why adjacent: a top-level-only intersection would miss nested keys.
        """
        for key in sorted(VIEWS.BROWSER_KEYS):
            nested = {"wrapper": [{key: True}]}
            with self.subTest(key=key, position="nested"):
                with self.assertRaises(VIEWS.IssueViewsError) as ctx:
                    VIEWS._reject_browser_keys(nested)
                message = str(ctx.exception)
                self.assertIn(key, message)
                self.assertIn("$.wrapper[0]", message)

    def test_reject_browser_keys_fillcolor_is_not_a_member(self):
        """AE-4 adjacent: fillcolor must not be treated as a BROWSER_KEYS member.

        Neighboring dimension: substring/lookalike vs actual set membership
        (fill and color exist separately; fillcolor does not).
        Expected: no raise for fillcolor at top level or nested.
        Observed: asserted below.
        Why adjacent: the shipped absence check listed fillcolor, which could
        never appear as a rejected key even if enforcement were broken.
        """
        VIEWS._reject_browser_keys({"fillcolor": "#fff"})
        VIEWS._reject_browser_keys({"wrapper": [{"fillcolor": "#fff"}]})
        VIEWS._reject_browser_keys({"authority": "generated-view"})

    def test_catalog_and_graph_order_and_id_dedup_property(self):
        """AE-5 property: catalog/graph set-or-sequence invariants.

        Invariant/oracle:
          - catalog items are uniquely keyed by id in the fixture store;
          - catalog item sequence is sorted by (id, source.path);
          - source_sha256 follows sorted source path order;
          - graph nodes are one-per-id (last write wins) and sorted by id;
          - graph edges are sorted by (source, kind, target).
        Generation domain / finite enumeration boundary:
          - every permutation of parsed load_store records (6! for this fixture);
          - every permutation of malformed load_store records (1!);
          - every permutation of source_files for digest order (7!);
          - every permutation of the 7 catalog items through build_graph (7!);
          - plus 7 duplicate-id injections (one extra copy of each item).
        Seed/replay: none (exhaustive enumeration, no RNG).
        Executed case count: recorded on AE5_CASE_COUNT below.
        """
        parsed, malformed, source_files = VIEWS.load_store(ISSUES, ROOT)
        baseline_catalog = VIEWS.build_catalog(parsed, malformed, source_files, ROOT)
        baseline_ids = [item["id"] for item in baseline_catalog["items"]]
        self.assertEqual(len(baseline_ids), len(set(baseline_ids)))
        cases = 0

        combined = list(parsed) + list(malformed)
        for perm in itertools.permutations(range(len(parsed))):
            shuffled_parsed = [parsed[i] for i in perm]
            catalog = VIEWS.build_catalog(shuffled_parsed, malformed, source_files, ROOT)
            ids = [item["id"] for item in catalog["items"]]
            paths = [item["source"]["path"] for item in catalog["items"]]
            self.assertEqual(ids, sorted(ids))
            self.assertEqual(
                list(zip(ids, paths)),
                sorted(zip(ids, paths), key=lambda pair: (pair[0] or "", pair[1])),
            )
            self.assertEqual(ids, baseline_ids)
            cases += 1

        for perm in itertools.permutations(range(len(malformed))):
            shuffled_malformed = [malformed[i] for i in perm]
            catalog = VIEWS.build_catalog(parsed, shuffled_malformed, source_files, ROOT)
            ids = [item["id"] for item in catalog["items"]]
            self.assertEqual(ids, baseline_ids)
            cases += 1

        for perm in itertools.permutations(range(len(source_files))):
            shuffled_sources = [source_files[i] for i in perm]
            catalog = VIEWS.build_catalog(parsed, malformed, shuffled_sources, ROOT)
            expected = [
                VIEWS._digest_bytes(f"{entry['path']}:{entry['sha256']}".encode("utf-8"))
                for entry in sorted(source_files, key=lambda value: value["path"])
            ]
            self.assertEqual(catalog["digests"]["source_sha256"], expected)
            cases += 1

        items = list(baseline_catalog["items"])
        for perm in itertools.permutations(items):
            shuffled = {"items": list(perm)}
            nodes, edges = VIEWS.build_graph(shuffled)
            node_ids = [node["id"] for node in nodes]
            self.assertEqual(len(node_ids), len(set(node_ids)))
            self.assertEqual(node_ids, sorted(node_ids))
            edge_keys = [(edge["source"], edge["kind"], edge["target"]) for edge in edges]
            self.assertEqual(edge_keys, sorted(edge_keys))
            cases += 1

        for item in items:
            duplicated = {"items": items + [item]}
            nodes, _edges = VIEWS.build_graph(duplicated)
            node_ids = [node["id"] for node in nodes]
            self.assertEqual(len(node_ids), len(set(node_ids)))
            self.assertEqual(node_ids.count(item["id"]), 1)
            cases += 1

        expected_cases = (
            math.factorial(len(parsed))
            + math.factorial(len(malformed))
            + math.factorial(len(source_files))
            + math.factorial(len(items))
            + len(items)
        )
        self.assertEqual(cases, expected_cases)
        self.assertEqual(len(parsed), 6)
        self.assertEqual(len(malformed), 1)
        self.assertEqual(len(source_files), 7)
        self.assertEqual(len(items), 7)


if __name__ == "__main__":
    unittest.main()
