#!/usr/bin/env python3
"""Package consistency for Task 0037-11 (parent).

Does not author child products. Both list and graph renderers must consume one
normalized catalog from issue_views.render; generated views are not input
authority. SQLite is out of scope for v1.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LISTS_PATH = ROOT / "_src/tools/issue_lists.py"
VIEWS_PATH = ROOT / "_src/tools/issue_views.py"


class IssueViewPackageError(ValueError):
    pass


def assert_no_sqlite_store(paths=None):
    """v1 views are files + JSON; SQLite is out of scope."""
    for path in paths or (LISTS_PATH, VIEWS_PATH):
        text = Path(path).read_text(encoding="utf-8")
        if "sqlite" in text.lower() or "import sqlite3" in text:
            raise IssueViewPackageError(f"SQLite is out of scope for v1: {path}")


def assert_lists_consume_views_render(lists_path=None):
    path = Path(lists_path or LISTS_PATH)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls = []

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node):
            func = node.func
            name = None
            if isinstance(func, ast.Attribute):
                if isinstance(func.value, ast.Name) and func.value.id == "VIEWS":
                    name = func.attr
            calls.append(name)
            self.generic_visit(node)

    Visitor().visit(tree)
    if "render" not in calls:
        raise IssueViewPackageError("issue_lists.py must call VIEWS.render for the catalog")
    text = path.read_text(encoding="utf-8")
    if "issues/_views/catalog.json" in text and "read_text" in text:
        raise IssueViewPackageError("generated catalog.json must not be list input authority")


def reconcile_ids_states_criteria_edges(catalog, graph, groups=None):
    catalog_ids = [item["id"] for item in catalog["items"]]
    if catalog_ids != sorted(catalog_ids):
        raise IssueViewPackageError("catalog items are not in deterministic id order")
    catalog_by_id = {item["id"]: item for item in catalog["items"]}
    nodes = {node["id"]: node for node in graph["nodes"]}
    missing_nodes = set(catalog_by_id) - set(nodes)
    if missing_nodes:
        raise IssueViewPackageError(f"graph missing catalog ids: {sorted(missing_nodes)}")
    for item_id, item in catalog_by_id.items():
        node = nodes[item_id]
        if node.get("state") != item.get("state"):
            raise IssueViewPackageError(f"state mismatch for {item_id}")
        if node.get("lifecycle_status") != item.get("lifecycle_status"):
            raise IssueViewPackageError(f"lifecycle mismatch for {item_id}")
        if node.get("archive_status") != item.get("archive_status"):
            raise IssueViewPackageError(f"archive mismatch for {item_id}")
        cat_criteria = tuple((c["id"], c.get("status")) for c in item.get("criteria") or [])
        node_criteria = tuple((c["id"], c.get("status")) for c in node.get("criteria") or [])
        if "criteria" in node and node_criteria != cat_criteria:
            raise IssueViewPackageError(f"criteria mismatch for {item_id}")
    expected_edges = []
    for item in catalog["items"]:
        source = item["id"]
        for target in item.get("prerequisites") or []:
            expected_edges.append((source, target, "prerequisite"))
        for relation in item.get("relations") or []:
            target = relation["target"].split("#", 1)[0]
            expected_edges.append((source, target, relation["type"]))
    actual_edges = {(e["source"], e["target"], e["kind"]) for e in graph["edges"]}
    missing_edges = [edge for edge in expected_edges if edge not in actual_edges]
    if missing_edges:
        raise IssueViewPackageError(f"graph missing catalog edges: {missing_edges}")
    if groups is not None:
        bucket_ids = set()
        for key in ("todo", "done", "unclear"):
            bucket_ids |= {item["id"] for item in groups[key]}
        if bucket_ids != set(catalog_by_id):
            raise IssueViewPackageError(
                f"list buckets != catalog ids: extra={sorted(bucket_ids - set(catalog_by_id))} "
                f"missing={sorted(set(catalog_by_id) - bucket_ids)}"
            )
        for item in catalog["items"]:
            cid = item["id"]
            state = item.get("state")
            malformed = item.get("endpoint_status") == "malformed" or state is None
            in_todo = cid in {i["id"] for i in groups["todo"]}
            in_done = cid in {i["id"] for i in groups["done"]}
            in_unclear = cid in {i["id"] for i in groups["unclear"]}
            if malformed or state not in (
                "open", "in_progress", "blocked", "closed", "withdrawn"
            ):
                if not in_unclear:
                    raise IssueViewPackageError(f"{cid} should be unclear")
            elif state == "blocked":
                if not (in_todo and cid in {i["id"] for i in groups["blocked"]}):
                    raise IssueViewPackageError(f"{cid} blocked not in todo/blocked")
            elif state in ("open", "in_progress"):
                if not in_todo:
                    raise IssueViewPackageError(f"{cid} openish missing from todo")
            elif state in ("closed", "withdrawn"):
                if not in_done:
                    raise IssueViewPackageError(f"{cid} terminal missing from done")
            for criterion in item.get("criteria") or []:
                if not criterion.get("id"):
                    raise IssueViewPackageError(f"{cid} criterion missing id")
    return {
        "catalog_count": len(catalog_by_id),
        "graph_node_count": len(nodes),
        "graph_edge_count": len(graph["edges"]),
        "catalog_edge_count": len(expected_edges),
    }


def check_package(catalog, graph, groups=None, *, lists_path=None, views_path=None):
    assert_no_sqlite_store((lists_path or LISTS_PATH, views_path or VIEWS_PATH))
    assert_lists_consume_views_render(lists_path)
    return reconcile_ids_states_criteria_edges(catalog, graph, groups)
