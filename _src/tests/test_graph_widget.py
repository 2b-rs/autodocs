#!/usr/bin/env python3
"""Tests for the interactive graph widget contract (serialization, stereotypes, fallback)."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "_src"
sys.path.insert(0, str(SRC))

import graph_widget as gw  # noqa: E402

FIXTURE = SRC / "tests" / "fixtures" / "graph-widget" / "sample-graph.json"
JS_PATH = ROOT / "component-graph.js"
INDEX_SOURCE = SRC / "sources" / "pages" / "index.json"


PRECHANGE_REF = "29aeadfbd"  # tree before this widget change; AE-2 baseline


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _baseline_graph() -> dict | None:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{PRECHANGE_REF}:data/component-graph.json"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        return None
    return json.loads(proc.stdout)


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables = 0
        self.captions: list[str] = []
        self.th_scopes: list[str] = []
        self.node_ids: list[str] = []
        self.edge_ids: list[str] = []
        self.edge_sources: list[str] = []
        self.edge_targets: list[str] = []
        self.stereotypes: list[str] = []
        self._capture_caption = False
        self._caption_bits: list[str] = []

    def handle_starttag(self, tag, attrs):
        ad = dict(attrs)
        if tag == "table":
            self.tables += 1
        elif tag == "caption":
            self._capture_caption = True
            self._caption_bits = []
        elif tag == "th":
            self.th_scopes.append(ad.get("scope", ""))
        elif tag == "tr" and ad.get("data-node-id") is not None:
            self.node_ids.append(ad["data-node-id"])
            self.stereotypes.append(ad.get("data-stereotypes", ""))
        elif tag == "tr" and ad.get("data-edge-id") is not None:
            self.edge_ids.append(ad["data-edge-id"])
            self.edge_sources.append(ad.get("data-source", ""))
            self.edge_targets.append(ad.get("data-target", ""))

    def handle_endtag(self, tag):
        if tag == "caption" and self._capture_caption:
            self.captions.append("".join(self._caption_bits))
            self._capture_caption = False

    def handle_data(self, data):
        if self._capture_caption:
            self._caption_bits.append(data)


def _parse(html: str) -> _TableParser:
    parser = _TableParser()
    parser.feed(html)
    parser.close()
    return parser


class TestStereotypeMapping(unittest.TestCase):
    def test_service_interface_maps_to_service_chip(self):
        node = {"id": "sv", "kind": "service interface", "module": "com", "label": "ara::com::X"}
        self.assertEqual(gw.map_stereotypes(node), ["Service"])
        self.assertEqual(gw.format_stereotype_chip("Service"), "<<Service>>")

    def test_application_core_class(self):
        node = {"id": "c", "kind": "class", "module": "core", "label": "ara::core::Future"}
        self.assertEqual(gw.map_stereotypes(node), ["Application"])

    def test_ecu_abstraction_and_driver(self):
        ecu = {"id": "io", "kind": "class", "module": "iohwab", "project": "AUTOSAR/CP"}
        driver = {"id": "can", "kind": "driver", "module": "can", "project": "AUTOSAR/CP"}
        self.assertEqual(gw.map_stereotypes(ecu), ["ECU Abstraction"])
        self.assertEqual(gw.map_stereotypes(driver), ["Driver"])
        self.assertIn("<<ECU Abstraction>>", gw.enrich_node(ecu)["stereotypeChips"])
        self.assertIn("<<Driver>>", gw.enrich_node(driver)["stereotypeChips"])

    def test_explicit_stereotypes_preserved_and_normalized(self):
        node = {
            "id": "x",
            "kind": "class",
            "module": "core",
            "stereotypes": ["<<Service>>", "Application", "Service"],
        }
        self.assertEqual(gw.map_stereotypes(node), ["Service", "Application"])

    def test_struct_is_data_type(self):
        node = {"id": "s", "kind": "struct", "module": "diag", "label": "ara::diag::ReadOutput"}
        self.assertEqual(gw.map_stereotypes(node), ["Data Type"])

    def test_unknown_kind_still_gets_a_catalog_stereotype(self):
        node = {"id": "z", "kind": "mystery", "module": "other"}
        mapped = gw.map_stereotypes(node)
        self.assertEqual(mapped, ["Application"])
        self.assertTrue(set(mapped) <= gw.STEREOTYPE_SET)


class TestUniverseAndCuration(unittest.TestCase):
    def test_adaptive_com_placeholders_are_not_classic(self):
        node = {
            "id": "classes/cl_SI_Namespace_common_SI.html",
            "label": "<SI-Namespace>::common::<SI>",
            "kind": "class",
            "module": "com",
        }
        self.assertEqual(gw.infer_universe(node), "adaptive")
        ns = {
            "id": "namespaces/ns_com_ara_com.html",
            "label": "namespace ara::com",
            "kind": "namespace",
            "module": "com",
        }
        self.assertEqual(gw.infer_universe(ns), "adaptive")
        graph = gw.serialize_graph(_load_fixture())
        by_id = {n["id"]: n for n in graph["nodes"]}
        self.assertEqual(by_id["classes/cl_ara_core_Future.html"]["universe"], "adaptive")
        self.assertEqual(by_id["classic/rte/Rte_Write"]["universe"], "classic")
        self.assertEqual(by_id["score/communication/Router"]["universe"], "score")
        self.assertEqual(by_id["classes/cl_ara_core_Future.html"]["universeBorder"], "#0e7490")
        self.assertEqual(by_id["classic/rte/Rte_Write"]["universeBorder"], "#3730a3")
        self.assertEqual(by_id["score/communication/Router"]["universeBorder"], "#047857")

    def test_curation_statuses(self):
        graph = gw.serialize_graph(_load_fixture())
        by_id = {n["id"]: n for n in graph["nodes"]}
        self.assertEqual(by_id["score/communication/Router"]["curation"], "Reviewed")
        self.assertEqual(by_id["classic/rte/Rte_Write"]["curation"], "Draft")
        self.assertEqual(by_id["classes/cl_diag_ReadOutput.html"]["curation"], "Draft")
        self.assertEqual(by_id["classes/cl_ara_core_Future.html"]["curation"], "Unvalidated")


class TestGraphSerialization(unittest.TestCase):
    def test_serialize_preserves_node_and_edge_cardinality(self):
        raw = _load_fixture()
        serialized = gw.serialize_graph(raw)
        self.assertEqual(len(serialized["nodes"]), len(raw["nodes"]))
        self.assertEqual(len(serialized["edges"]), len(raw["edges"]))
        self.assertEqual(
            [n["id"] for n in serialized["nodes"]],
            [n["id"] for n in raw["nodes"]],
        )
        self.assertEqual(
            [e["id"] for e in serialized["edges"]],
            [e["id"] for e in raw["edges"]],
        )

    def test_serialize_is_idempotent(self):
        once = gw.serialize_graph(_load_fixture())
        twice = gw.serialize_graph(once)
        self.assertEqual(
            [(n["id"], n["universe"], n["stereotypes"], n["curation"]) for n in once["nodes"]],
            [(n["id"], n["universe"], n["stereotypes"], n["curation"]) for n in twice["nodes"]],
        )
        self.assertEqual(once["stats"]["nodes"], twice["stats"]["nodes"])
        self.assertEqual(once["cuttlefish"]["inLibrary"], False)

    def test_empty_and_none_inputs_do_not_drop_structure(self):
        empty = gw.serialize_graph({"nodes": [], "edges": []})
        self.assertEqual(empty["nodes"], [])
        self.assertEqual(empty["edges"], [])
        none = gw.serialize_graph(None)
        self.assertEqual(none["nodes"], [])
        self.assertEqual(none["edges"], [])

    def test_inspector_payload_shape(self):
        node = _load_fixture()["nodes"][1]
        payload = gw.inspector_payload(node)
        self.assertEqual(payload["id"], node["id"])
        self.assertEqual(payload["universe"], "adaptive")
        self.assertEqual(payload["stereotypes"], ["Service"])
        self.assertIn("label", payload["attributes"])
        self.assertIn("curation", payload["attributes"])

    def test_cuttlefish_is_not_claimed_as_vendored(self):
        self.assertFalse(gw.CUTTLEFISH_IN_LIBRARY)
        meta = gw.serialize_graph({})["cuttlefish"]
        self.assertEqual(meta["layout"], "spring-physics")
        self.assertEqual(meta["fallbackLayouts"], ["cose"])


class TestFiltersAndAdjacentCases(unittest.TestCase):
    def test_universe_filter_cardinality(self):
        nodes = gw.serialize_graph(_load_fixture())["nodes"]
        adaptive = gw.filter_nodes(nodes, universe="adaptive")
        classic = gw.filter_nodes(nodes, universe="classic")
        score = gw.filter_nodes(nodes, universe="score")
        self.assertEqual(len(adaptive) + len(classic) + len(score), len(nodes))
        self.assertTrue(all(n["universe"] == "classic" for n in classic))
        self.assertGreaterEqual(len(classic), 1)
        self.assertGreaterEqual(len(score), 1)

    def test_stereotype_filter_adjacent_to_universe_filter(self):
        nodes = _load_fixture()["nodes"]
        services = gw.filter_nodes(nodes, stereotype="Service")
        self.assertTrue(all("Service" in n["stereotypes"] for n in services))
        self.assertTrue(any(n["universe"] == "adaptive" for n in services))
        ecu = gw.filter_nodes(nodes, stereotype="ECU Abstraction")
        self.assertEqual(len(ecu), 1)
        self.assertEqual(ecu[0]["universe"], "classic")

    def test_curation_filter_adjacent_to_stereotype_filter(self):
        nodes = _load_fixture()["nodes"]
        reviewed = gw.filter_nodes(nodes, curation="Reviewed")
        self.assertEqual(len(reviewed), 1)
        self.assertEqual(reviewed[0]["id"], "score/communication/Router")
        drafts = gw.filter_nodes(nodes, curation="Draft")
        self.assertGreaterEqual(len(drafts), 2)
        both = gw.filter_nodes(nodes, stereotype="Data Type", curation="Draft")
        self.assertEqual([n["id"] for n in both], ["classes/cl_diag_ReadOutput.html"])


class TestFallbackTable(unittest.TestCase):
    def test_table_lists_every_node_edge_and_stereotype(self):
        raw = _load_fixture()
        html = gw.fallback_table_html(raw)
        parsed = _parse(html)
        self.assertGreaterEqual(parsed.tables, 2)
        self.assertTrue(all(scope == "col" for scope in parsed.th_scopes))
        self.assertEqual(parsed.node_ids, [n["id"] for n in raw["nodes"]])
        self.assertEqual(parsed.edge_ids, [e["id"] for e in raw["edges"]])
        self.assertEqual(parsed.edge_sources, [e["source"] for e in raw["edges"]])
        self.assertEqual(parsed.edge_targets, [e["target"] for e in raw["edges"]])
        self.assertIn("Knoten", parsed.captions[0])
        self.assertIn("Beziehungen", parsed.captions[1])
        self.assertTrue(any("Service" in s for s in parsed.stereotypes))
        self.assertIn("&lt;&lt;Service&gt;&gt;", html)
        self.assertIn("&lt;&lt;ECU Abstraction&gt;&gt;", html)
        self.assertIn("data-graph-fallback", html)
        self.assertIn("<thead>", html)
        self.assertIn("<tbody>", html)
        self.assertIn("<caption>", html)

    def test_empty_graph_still_emits_semantic_tables(self):
        html = gw.fallback_table_html({"nodes": [], "edges": []})
        parsed = _parse(html)
        self.assertEqual(parsed.tables, 2)
        self.assertEqual(parsed.node_ids, [])
        self.assertEqual(parsed.edge_ids, [])
        self.assertIn("Keine Knoten", html)
        self.assertIn("Keine Beziehungen", html)

    def test_html_special_characters_are_escaped(self):
        graph = {
            "nodes": [{"id": "a<b>", "label": "Foo & Bar", "kind": "class", "module": "core"}],
            "edges": [],
        }
        html = gw.fallback_table_html(graph)
        self.assertNotIn("a<b>", html)
        self.assertIn("a&lt;b&gt;", html)
        self.assertIn("Foo &amp; Bar", html)


class TestAdversarialCompletionEvidence(unittest.TestCase):
    """AE-1..5: serialization shape, identity, cardinality, red-on-baseline."""

    def test_ae3_classic_identity_was_missing_on_baseline(self):
        # Baseline behaviour: no universe field, so Classic cannot be distinguished.
        classic = {
            "id": "classic/rte/Rte_Write",
            "label": "Rte_Write",
            "kind": "class",
            "module": "rte",
            "project": "AUTOSAR/CP",
        }
        baseline_universe = classic.get("universe")
        self.assertIsNone(baseline_universe)
        self.assertEqual(gw.infer_universe(classic), "classic")

        baseline = _baseline_graph()
        if baseline is None:
            self.skipTest("HEAD:data/component-graph.json unavailable")
        self.assertTrue(baseline["nodes"], "baseline graph unexpectedly empty")
        sample = baseline["nodes"][0]
        self.assertNotIn("universe", sample)
        self.assertNotIn("stereotypes", sample)
        candidate = gw.serialize_graph(baseline)
        self.assertEqual(len(candidate["nodes"]), len(baseline["nodes"]))
        self.assertEqual(len(candidate["edges"]), len(baseline["edges"]))
        self.assertTrue(all("universe" in n and n["universe"] in gw.UNIVERSE_IDS for n in candidate["nodes"]))
        self.assertTrue(all("stereotypes" in n for n in candidate["nodes"]))
        self.assertTrue(all(n["curation"] in gw.CURATION_SET for n in candidate["nodes"]))

    def test_ae5_universe_assignment_is_a_total_function(self):
        raw = _load_fixture()
        serialized = gw.serialize_graph(raw)
        universes = [n["universe"] for n in serialized["nodes"]]
        self.assertEqual(len(universes), len(raw["nodes"]))
        self.assertTrue(set(universes) <= gw.UNIVERSE_IDS)
        self.assertEqual(set(universes), {"adaptive", "classic", "score"})
        # Exhaustive enumeration of the fixture domain (7 nodes).
        self.assertEqual(len(serialized["nodes"]), 7)


LIVE_GRAPH = ROOT / "data" / "component-graph.json"
CLASSIC_NODE_IDS = (
    "CP_RTE", "CP_OS", "CP_COM", "CP_CAN", "CP_ETH",
    "CP_NVRAM", "CP_CRYPTO", "CP_DIAG", "CP_MCAL",
)
SCORE_NODE_IDS = (
    "SCORE_CORE", "SCORE_COM", "SCORE_DIAG",
    "SCORE_MEM", "SCORE_CRYPTO", "SCORE_SAFETY",
)
INSPECTOR_JS_PATH = ROOT / "component-inspector.js"


def _load_live_graph() -> dict:
    return json.loads(LIVE_GRAPH.read_text(encoding="utf-8"))


class TestLiveMultiUniverseGraph(unittest.TestCase):
    def test_classic_and_score_nodes_present_and_filterable(self):
        raw = _load_live_graph()
        by_id = {n["id"]: n for n in raw["nodes"]}
        for node_id in CLASSIC_NODE_IDS:
            self.assertIn(node_id, by_id)
            self.assertEqual(by_id[node_id]["universe"], "classic")
            self.assertEqual(by_id[node_id]["stereotype"], {
                "CP_RTE": "execution-environment",
                "CP_OS": "operating-system",
                "CP_COM": "communication",
                "CP_CAN": "hardware-interface",
                "CP_ETH": "hardware-interface",
                "CP_NVRAM": "persistence",
                "CP_CRYPTO": "security",
                "CP_DIAG": "diagnostics",
                "CP_MCAL": "driver",
            }[node_id])
        for node_id in SCORE_NODE_IDS:
            self.assertIn(node_id, by_id)
            self.assertEqual(by_id[node_id]["universe"], "score")

        classic = gw.filter_nodes(raw["nodes"], universe="classic")
        score = gw.filter_nodes(raw["nodes"], universe="score")
        adaptive = gw.filter_nodes(raw["nodes"], universe="adaptive")
        self.assertTrue(all(n["universe"] == "classic" for n in classic))
        self.assertTrue(all(n["universe"] == "score" for n in score))
        self.assertTrue(all(n["universe"] == "adaptive" for n in adaptive))
        self.assertTrue(set(CLASSIC_NODE_IDS) <= {n["id"] for n in classic})
        self.assertTrue(set(SCORE_NODE_IDS) <= {n["id"] for n in score})
        self.assertGreaterEqual(len(adaptive), 1)
        self.assertEqual(len(classic) + len(score) + len(adaptive), len(raw["nodes"]))

        edge_ends = {(e["source"], e["target"]) for e in raw["edges"]}
        self.assertIn(("CP_RTE", "CP_OS"), edge_ends)
        self.assertIn(("SCORE_CORE", "SCORE_COM"), edge_ends)
        for source, target in edge_ends:
            self.assertIn(source, by_id)
            self.assertIn(target, by_id)

    def test_elements_projection_exposes_all_three_universes(self):
        raw = _load_live_graph()
        nodes = raw["elements"]["nodes"]
        universes = {n["data"].get("universe") for n in nodes}
        self.assertIn("classic", universes)
        self.assertIn("score", universes)
        self.assertIn("adaptive", universes)
        self.assertEqual(len(nodes), len(raw["nodes"]))
        element_ids = {n["data"]["id"] for n in nodes}
        self.assertTrue(set(CLASSIC_NODE_IDS) <= element_ids)
        self.assertTrue(set(SCORE_NODE_IDS) <= element_ids)

    def test_filtering_hides_other_universes_without_dropping_ids(self):
        raw = _load_live_graph()
        classic = {n["id"] for n in gw.filter_nodes(raw["nodes"], universe="classic")}
        score = {n["id"] for n in gw.filter_nodes(raw["nodes"], universe="score")}
        self.assertTrue(classic.isdisjoint(score))
        self.assertNotIn("SCORE_CORE", classic)
        self.assertNotIn("CP_RTE", score)
        # Adjacent case: Adaptive remains the majority universe and is not lost.
        adaptive = {n["id"] for n in gw.filter_nodes(raw["nodes"], universe="adaptive")}
        self.assertGreater(len(adaptive), len(classic))
        self.assertNotIn("CP_RTE", adaptive)
        self.assertNotIn("SCORE_CORE", adaptive)


class TestWidgetSourceContract(unittest.TestCase):
    def test_js_dispatches_component_selected_and_exposes_filters(self):
        js = JS_PATH.read_text(encoding="utf-8")
        self.assertIn("component:selected", js)
        self.assertIn("data-graph-filter-universe", js)
        self.assertIn("data-graph-filter-stereotype", js)
        self.assertIn("data-graph-filter-curation", js)
        self.assertIn("data-graph-physics", js)
        self.assertIn("data-graph-table-view", js)
        self.assertIn("data-component-inspector", js)
        self.assertIn("All Universes", js)
        self.assertIn('data-graph-universe="adaptive"', js)
        self.assertIn('data-graph-universe="classic"', js)
        self.assertIn('data-graph-universe="score"', js)
        self.assertIn("UNIVERSE_BADGE", js)
        self.assertIn("delete-unbind-btn", js)
        self.assertIn("ComponentInspector", js)

    def test_inspector_shows_universe_badge_and_unbind(self):
        js = INSPECTOR_JS_PATH.read_text(encoding="utf-8")
        self.assertIn("universe-badge", js)
        self.assertIn('"Classic"', js)
        self.assertIn('"S-Core"', js)
        self.assertIn('"Adaptive"', js)
        self.assertIn('"[" + universeBadgeLabel', js)
        self.assertIn("Source Requirements", js)
        self.assertIn("delete-unbind-btn", js)
        self.assertIn("unbind_feature", js)

    def test_page_source_has_fallback_marker(self):
        source = INDEX_SOURCE.read_text(encoding="utf-8")
        self.assertIn("@@COMPONENT_GRAPH_TABLE@@", source)
        self.assertIn("data-component-graph", source)


if __name__ == "__main__":
    unittest.main()
