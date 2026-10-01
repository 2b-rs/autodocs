#!/usr/bin/env python3
"""Normalized dependency-graph adapter (Task 0037-12).

Consumes validated ``issue-dependency-graph@v1`` JSON only. Never parses
YAML, Markdown, TODO.md, or DONE.md. DOT emission is the Python twin of
``tools/todo-graph-core.js``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCHEMA = "issue-dependency-graph@v1"
AUTHORITY = "generated-view"
REQUIRED_TOP = ("schema", "authority", "nodes", "edges", "digests", "generation_id")
REQUIRED_NODE = ("id", "level", "lifecycle_status", "endpoint_status")
REQUIRED_EDGE = ("source", "target", "kind", "endpoint_status")
ENDPOINT_OK = frozenset({"present", "missing", "malformed"})
ID_TOKEN = r"^[0-9]{4}(?:-[0-9]{2}(?:\.[0-9]{2})?)?$"

FEATURE_COLORS = [
    "#cfe8ff", "#d6ecff", "#d9f2d9", "#ffe0cc",
    "#ffd6d6", "#ffe680", "#ffe9cc", "#e6dcff",
    "#c9f7f5", "#f7d9e3", "#e3f7c9", "#d9d9f7",
]
MARK_COLORS = {
    " ": "#ffffff",
    "p": "#fff3b0",
    "u": "#ffb3b3",
    "w": "#e8d5ff",
    "?": "#d9d9d9",
    "x": "#b6e3b6",
}
DONE_FONT_COLOR = "#808080"
DONE_EDGE_COLOR = "#d9d9d9"


class GraphAdapterError(ValueError):
    pass


def _html_escape(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def dot_quote(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def truncate(text, max_len):
    cleaned = " ".join(str(text or "").split())
    if len(cleaned) <= max_len:
        return cleaned
    trimmed = cleaned[:max_len]
    trimmed = __import__("re").sub(r"\s+\S*$", "", trimmed)
    return trimmed + "\u2026"


def _looks_like_markdown(text):
    head = text.lstrip()[:800]
    if head.startswith("---"):
        return True
    if "## Feature:" in head or head.startswith("# "):
        return True
    if "PREREQ:" in head and "- [" in head:
        return True
    return False


def lifecycle_to_mark(lifecycle_status, endpoint_status):
    if endpoint_status in ("missing", "malformed"):
        return "?"
    status = lifecycle_status or ""
    if status == "open":
        return " "
    if status == "in_progress":
        return "p"
    if status == "blocked":
        return "u"
    if status == "withdrawn":
        return "w"
    if status == "closed" or status.startswith("closed:"):
        return "x"
    return "?"


def feature_prefix(item_id):
    text = str(item_id or "")
    if "-" not in text:
        return text if len(text) == 4 and text.isdigit() else "_unresolved"
    return text.split("-", 1)[0]


def classify_edge(source_id, target_id, gate, kind):
    if gate == "feature-closure":
        return "feature_closure"
    if kind and kind != "prerequisite":
        return "relation"
    src_f = feature_prefix(source_id)
    dst_f = feature_prefix(target_id)
    dst_is_feature = "-" not in str(target_id)
    if src_f == dst_f and not dst_is_feature:
        return "explicit_same"
    if dst_is_feature:
        return "feature_closure"
    return "explicit_cross"


def validate_graph(document):
    if not isinstance(document, dict):
        raise GraphAdapterError("graph document must be a JSON object")
    extra = set(document) - {
        "schema", "authority", "nodes", "edges", "digests", "generation_id",
    }
    if extra:
        raise GraphAdapterError(f"unknown graph fields: {sorted(extra)}")
    for key in REQUIRED_TOP:
        if key not in document:
            raise GraphAdapterError(f"missing required field {key}")
    if document.get("schema") != SCHEMA:
        raise GraphAdapterError(
            f"unsupported schema {document.get('schema')!r}; expected {SCHEMA}")
    if document.get("authority") != AUTHORITY:
        raise GraphAdapterError(
            f"authority {document.get('authority')!r} is not {AUTHORITY}")
    gen = document.get("generation_id")
    if not isinstance(gen, str) or not gen.startswith("sha256:") or len(gen) != 71:
        raise GraphAdapterError("malformed or missing generation_id")
    nodes = document.get("nodes")
    edges = document.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise GraphAdapterError("nodes and edges must be arrays")
    seen = {}
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise GraphAdapterError(f"node[{index}] is not an object")
        for key in REQUIRED_NODE:
            if key not in node:
                raise GraphAdapterError(f"node[{index}] missing {key}")
        nid = node["id"]
        if nid in seen:
            raise GraphAdapterError(f"duplicate node id {nid!r}")
        seen[nid] = node
        ep = node["endpoint_status"]
        if ep not in ENDPOINT_OK:
            raise GraphAdapterError(f"node {nid!r} bad endpoint_status {ep!r}")
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise GraphAdapterError(f"edge[{index}] is not an object")
        for key in REQUIRED_EDGE:
            if key not in edge:
                raise GraphAdapterError(f"edge[{index}] missing {key}")
        ep = edge["endpoint_status"]
        if ep not in ENDPOINT_OK:
            raise GraphAdapterError(f"edge[{index}] bad endpoint_status {ep!r}")
        if ep != "present" and edge.get("target") not in seen:
            raise GraphAdapterError(
                f"unresolved edge target {edge.get('target')!r} missing from nodes "
                "(silently dropped endpoints are forbidden)")
        if edge.get("source") not in seen:
            raise GraphAdapterError(
                f"edge source {edge.get('source')!r} missing from nodes")
    return document


def load_graph(text):
    if not isinstance(text, str):
        raise GraphAdapterError("graph input must be text")
    if _looks_like_markdown(text):
        raise GraphAdapterError(
            "refused Markdown/TODO.md/DONE.md/YAML input; "
            "load issues/_views/dependency-graph.json")
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GraphAdapterError(f"malformed graph JSON: {exc}") from exc
    return validate_graph(document)


def html_done_label(multi_line_label, feature_color):
    text_html = "<BR/>".join(_html_escape(part) for part in multi_line_label.split("\n"))
    return (
        "<"
        f'<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" '
        f'STYLE="ROUNDED" COLOR="#808080" BGCOLOR="{feature_color}">'
        "<TR>"
        f'<TD ALIGN="LEFT"><FONT COLOR="{DONE_FONT_COLOR}">{text_html}</FONT></TD>'
        f'<TD ALIGN="RIGHT" VALIGN="MIDDLE"><FONT COLOR="{DONE_FONT_COLOR}">&#10003;</FONT></TD>'
        "</TR></TABLE>>"
    )


def node_label(node, task_label_max_len):
    status = node.get("endpoint_status") or "present"
    mark = lifecycle_to_mark(node.get("lifecycle_status"), status)
    title = node.get("id")
    extra = []
    if status == "missing":
        extra.append("missing")
    elif status == "malformed":
        extra.append("malformed")
    if node.get("archive_status"):
        extra.append(str(node["archive_status"]))
    if node.get("lifecycle_status") == "withdrawn" or mark == "w":
        extra.append("[w]")
    suffix = (" " + " ".join(extra)) if extra else ""
    if task_label_max_len:
        body = truncate(node.get("lifecycle_status") or "", task_label_max_len)
        return f"{title}{suffix}\n{body}"
    return f"{title}{suffix}"


def build_dot(graph, opts=None):
    opts = opts or {}
    task_label_max_len = opts.get("taskLabelMaxLen")
    include_closed = opts.get("includeClosed", True)
    include_withdrawn = opts.get("includeWithdrawn", True)
    include_unresolved = opts.get("includeUnresolved", True)

    nodes = list(graph["nodes"])
    edges = list(graph["edges"])

    def visible(node):
        mark = lifecycle_to_mark(node.get("lifecycle_status"), node.get("endpoint_status"))
        ep = node.get("endpoint_status")
        if ep in ("missing", "malformed") and not include_unresolved:
            return False
        if mark == "x" and not include_closed:
            return False
        if mark == "w" and not include_withdrawn:
            return False
        return True

    visible_ids = {n["id"] for n in nodes if visible(n)}
    # Edges to unresolved endpoints stay unless the *filter* hides them.
    # A missing node still present in `nodes` is never dropped from counts
    # when include_unresolved is true.
    hidden_required = []
    if include_unresolved:
        for edge in edges:
            if edge["endpoint_status"] != "present":
                if edge["target"] not in visible_ids:
                    hidden_required.append(edge["target"])
        if hidden_required:
            raise GraphAdapterError(
                "unresolved endpoints would be dropped by filter: "
                + ",".join(sorted(set(hidden_required))))

    feature_ids = []
    clusters = {}
    for node in sorted(nodes, key=lambda n: str(n["id"])):
        if node["id"] not in visible_ids:
            continue
        if node.get("level") == "feature" or (
                node.get("level") is None and "-" not in str(node["id"])
                and str(node["id"]).isdigit() and len(str(node["id"])) == 4):
            fid = node["id"]
        else:
            fid = feature_prefix(node["id"])
            if node.get("level") is None and fid == "_unresolved":
                fid = "_unresolved"
        if fid not in clusters:
            clusters[fid] = []
            feature_ids.append(fid)
        clusters[fid].append(node)

    lines = [
        "digraph todo_dependency_graph {",
        "  rankdir=LR;",
        "  splines=true;",
        "  overlap=false;",
        '  bgcolor="white";',
        '  pad="0.3";',
        '  nodesep="0.25";',
        '  ranksep="0.8";',
        '  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize="10", margin="0.08,0.05"];',
        '  edge [fontname="Helvetica", fontsize="9"];',
    ]
    node_by_id = {n["id"]: n for n in nodes}
    rendered_nodes = 0
    for idx, fid in enumerate(feature_ids):
        members = clusters[fid]
        if not members:
            continue
        color = FEATURE_COLORS[idx % len(FEATURE_COLORS)]
        cluster_name = "unresolved" if fid == "_unresolved" else fid
        label = fid if fid != "_unresolved" else "unresolved endpoints"
        lines.append(f"  subgraph cluster_{cluster_name} {{")
        lines.append(f"    label={dot_quote(label)};")
        lines.append('    style="rounded,filled";')
        lines.append('    color="#777777";')
        lines.append(f"    fillcolor={dot_quote(color)};")
        lines.append('    penwidth="1.2";')
        lines.append('    node [fillcolor="white"];')
        for node in members:
            nid = node["id"]
            mark = lifecycle_to_mark(node.get("lifecycle_status"), node.get("endpoint_status"))
            label_text = node_label(node, task_label_max_len)
            url_attr = ""
            if node.get("url"):
                url_attr = f", URL={dot_quote(node['url'])}"
            if node.get("level") == "feature" and node.get("endpoint_status") == "present":
                feat_label = label_text if node.get("archive_status") else nid
                lines.append(
                    f"    {dot_quote(nid)} [label={dot_quote(feat_label)}, shape=tab, "
                    f"fillcolor={dot_quote(color)}, style=\"filled,bold\"{url_attr}];"
                )
            elif mark == "x" and node.get("endpoint_status") == "present":
                html_label = html_done_label(label_text, color)
                lines.append(
                    f"    {dot_quote(nid)} [shape=\"none\", margin=\"0\", "
                    f"label={html_label}{url_attr}];"
                )
            else:
                fill = MARK_COLORS.get(mark, "#ffffff")
                extra = ""
                if node.get("endpoint_status") == "missing":
                    extra = ', style="dashed,filled", color="#b3261e"'
                elif node.get("endpoint_status") == "malformed":
                    extra = ', style="dashed,filled", color="#e65100"'
                lines.append(
                    f"    {dot_quote(nid)} [label={dot_quote(label_text)}, "
                    f"fillcolor={dot_quote(fill)}{extra}{url_attr}];"
                )
            rendered_nodes += 1
        lines.append("  }")

    styles = {
        "explicit_same": 'color="black", penwidth="1.2"',
        "explicit_cross": 'color="#1f4e79", penwidth="1.4"',
        "feature_closure": 'color="crimson", penwidth="1.5"',
        "relation": 'color="#6a1b9a", penwidth="1.3", style="dashed"',
    }
    drawn = 0
    unresolved_edges = 0
    for edge in sorted(edges, key=lambda e: (e["source"], e["kind"], e["target"])):
        if edge["source"] not in visible_ids or edge["target"] not in visible_ids:
            if include_unresolved and edge["endpoint_status"] != "present":
                raise GraphAdapterError(
                    f"would drop unresolved edge {edge['source']}->{edge['target']}")
            continue
        src = node_by_id[edge["source"]]
        src_mark = lifecycle_to_mark(src.get("lifecycle_status"), src.get("endpoint_status"))
        klass = classify_edge(edge["source"], edge["target"], edge.get("gate"), edge.get("kind"))
        if src_mark == "x":
            style = f"color={dot_quote(DONE_EDGE_COLOR)}, penwidth=\"1.2\""
        else:
            style = styles[klass]
        if edge["endpoint_status"] == "missing":
            style += ', style="dotted"'
        elif edge["endpoint_status"] == "malformed":
            style += ', style="dashed", color="#e65100"'
        gate = edge.get("gate")
        if gate:
            style += f", edgetooltip={dot_quote(gate)}"
        lines.append(f"  {dot_quote(edge['source'])} -> {dot_quote(edge['target'])} [{style}];")
        drawn += 1
        if edge["endpoint_status"] != "present":
            unresolved_edges += 1

    lines.append("}")
    return {
        "dot": "\n".join(lines) + "\n",
        "nodeCount": rendered_nodes,
        "edgeCount": drawn,
        "liveFeatureCount": len(feature_ids),
        "unresolvedEdgeCount": unresolved_edges,
        "unresolvedNodeCount": sum(
            1 for n in nodes
            if n.get("endpoint_status") in ("missing", "malformed") and n["id"] in visible_ids),
    }


def counts(graph):
    nodes = graph["nodes"]
    edges = graph["edges"]
    return {
        "nodes": len(nodes),
        "edges": len(edges),
        "features": sum(1 for n in nodes if n.get("level") == "feature"),
        "tasks": sum(1 for n in nodes if n.get("level") == "task"),
        "subtasks": sum(1 for n in nodes if n.get("level") == "subtask"),
        "withdrawn": sum(
            1 for n in nodes
            if lifecycle_to_mark(n.get("lifecycle_status"), n.get("endpoint_status")) == "w"),
        "missing_nodes": sum(1 for n in nodes if n.get("endpoint_status") == "missing"),
        "malformed_nodes": sum(1 for n in nodes if n.get("endpoint_status") == "malformed"),
        "start_gate_edges": sum(1 for e in edges if e.get("gate") == "start-gate"),
        "feature_closure_edges": sum(1 for e in edges if e.get("gate") == "feature-closure"),
        "unresolved_edges": sum(1 for e in edges if e.get("endpoint_status") != "present"),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph_json")
    parser.add_argument("--dot", action="store_true")
    args = parser.parse_args(argv)
    text = Path(args.graph_json).read_text(encoding="utf-8")
    graph = load_graph(text)
    built = build_dot(graph)
    if args.dot:
        sys.stdout.write(built["dot"])
    else:
        payload = {"counts": counts(graph), "built": {
            k: v for k, v in built.items() if k != "dot"
        }}
        json.dump(payload, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
