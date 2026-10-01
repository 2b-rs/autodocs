#!/usr/bin/env python3
"""Traceability & dependency graph widget contract (Cuttlefish / Cytoscape).

Cuttlefish is **not** vendored in this repository: the only graph runtime on the
publication pages is `cytoscape.min.js`. There is no `cytoscape-euler` (or other
Cuttlefish) bundle. The widget therefore:

* keeps the existing custom spring-physics loop as the Cuttlefish-style layout
  (Euler is the same force class; CoSE is the built-in Cytoscape fallback);
* renders AUTOSAR SW-C layer stereotypes as the suitable Cuttlefish badges
  (`<<Service>>`, `<<Application>>`, `<<ECU Abstraction>>`, `<<Driver>>`, …).

This module is the source of truth for serialization, stereotype mapping, and
the accessible no-JS fallback table (RQ-UIUX-012). The browser widget must
consume the same fields.
"""
from __future__ import annotations

import html
import re
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "ara-api-component-graph/v1"

UNIVERSE_ADAPTIVE = "adaptive"
UNIVERSE_CLASSIC = "classic"
UNIVERSE_SCORE = "score"

UNIVERSE_CATALOG: tuple[dict[str, str], ...] = (
    {
        "id": UNIVERSE_ADAPTIVE,
        "label": "AUTOSAR Adaptive",
        "border": "#0e7490",  # cyan / teal
    },
    {
        "id": UNIVERSE_CLASSIC,
        "label": "AUTOSAR Classic",
        "border": "#3730a3",  # indigo / blue
    },
    {
        "id": UNIVERSE_SCORE,
        "label": "Eclipse S-Core",
        "border": "#047857",  # emerald / green
    },
)
UNIVERSE_IDS = {row["id"] for row in UNIVERSE_CATALOG}
UNIVERSE_BORDERS = {row["id"]: row["border"] for row in UNIVERSE_CATALOG}
UNIVERSE_LABELS = {row["id"]: row["label"] for row in UNIVERSE_CATALOG}

# Suitable Cuttlefish / UML stereotypes for AUTOSAR + S-Core nodes.
STEREOTYPE_CATALOG: tuple[str, ...] = (
    "Application",
    "Service",
    "ECU Abstraction",
    "Driver",
    "Complex Device Driver",
    "Sensor Actuator",
    "Data Type",
    "Package",
    "Composition",
)
STEREOTYPE_SET = set(STEREOTYPE_CATALOG)

CURATION_REVIEWED = "Reviewed"
CURATION_DRAFT = "Draft"
CURATION_UNVALIDATED = "Unvalidated"
CURATION_STATUSES: tuple[str, ...] = (
    CURATION_REVIEWED,
    CURATION_DRAFT,
    CURATION_UNVALIDATED,
)
CURATION_SET = set(CURATION_STATUSES)

CUTTLEFISH_IN_LIBRARY = False
CUTTLEFISH_LAYOUT = "spring-physics"
CUTTLEFISH_FALLBACK_LAYOUTS: tuple[str, ...] = ("cose",)

_SERVICE_MODULES = frozenset({
    "com", "diag", "log", "nm", "per", "crypto", "tsync", "ucm", "fw", "idsm", "rds",
})
_APPLICATION_MODULES = frozenset({"core", "exec", "sm", "phm"})
_DRIVER_MODULES = frozenset({"shwa", "can", "lin", "eth", "spi", "adc", "dio", "port", "pwm", "gpt"})
_ECU_ABSTRACTION_MODULES = frozenset({"iohwab", "ecuabstraction", "ecu_abstraction"})
_CLASSIC_MODULES = frozenset({
    "rte", "bswm", "ecum", "comm", "canif", "nvm", "dem", "dcm",
    "pdur", "cancnm", "linif", "ethif", "wdgm", "os", "iohwab",
})
_SCORE_MARKERS = (
    "eclipse/s-core",
    "eclipse-score",
    "eclipscore",
    "s-core",
    "score::",
)
_CLASSIC_MARKERS = (
    "autosar/cp",
    "autosar classic",
    "classic platform",
    "rte_",
    "bsw/",
)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _haystack(node: Mapping[str, Any]) -> str:
    parts = [
        _text(node.get("id")),
        _text(node.get("label")),
        _text(node.get("shortLabel")),
        _text(node.get("module")),
        _text(node.get("namespace")),
        _text(node.get("project")),
        _text(node.get("canonicalId")),
        _text(node.get("universe")),
        _text(node.get("url")),
    ]
    return " ".join(parts).lower()


def format_stereotype_chip(name: str) -> str:
    """ASCII Cuttlefish / UML badge, e.g. ``<<Service>>``."""
    text = _text(name).strip("<>«»").strip()
    if not text:
        return ""
    return f"<<{text}>>"


def infer_universe(node: Mapping[str, Any]) -> str:
    explicit = _text(node.get("universe")).lower()
    if explicit in UNIVERSE_IDS:
        return explicit
    aliases = {
        "autosar adaptive": UNIVERSE_ADAPTIVE,
        "adaptive": UNIVERSE_ADAPTIVE,
        "ap": UNIVERSE_ADAPTIVE,
        "autosar classic": UNIVERSE_CLASSIC,
        "classic": UNIVERSE_CLASSIC,
        "cp": UNIVERSE_CLASSIC,
        "eclipse s-core": UNIVERSE_SCORE,
        "s-core": UNIVERSE_SCORE,
        "score": UNIVERSE_SCORE,
    }
    if explicit in aliases:
        return aliases[explicit]

    hay = _haystack(node)
    project = _text(node.get("project")).lower()
    if any(marker in hay for marker in _SCORE_MARKERS) or project.startswith("eclipse/s-core"):
        return UNIVERSE_SCORE
    if any(marker in hay for marker in _CLASSIC_MARKERS) or project.startswith("autosar/cp"):
        return UNIVERSE_CLASSIC
    module = _text(node.get("module")).lower()
    label = re.sub(r"^namespace\s+", "", _text(node.get("label")))
    if label.startswith(("ara::", "apext::")):
        return UNIVERSE_ADAPTIVE
    if module in _CLASSIC_MODULES:
        return UNIVERSE_CLASSIC
    return UNIVERSE_ADAPTIVE


def _normalize_stereotype(value: Any) -> str | None:
    text = _text(value).strip("<>«»").strip()
    if not text:
        return None
    lowered = text.lower()
    aliases = {
        "application": "Application",
        "service": "Service",
        "service interface": "Service",
        "ecu abstraction": "ECU Abstraction",
        "ecuabstraction": "ECU Abstraction",
        "iohwab": "ECU Abstraction",
        "driver": "Driver",
        "complex device driver": "Complex Device Driver",
        "cdd": "Complex Device Driver",
        "sensor actuator": "Sensor Actuator",
        "sensor/actuator": "Sensor Actuator",
        "data type": "Data Type",
        "struct": "Data Type",
        "package": "Package",
        "namespace": "Package",
        "composition": "Composition",
    }
    if text in STEREOTYPE_SET:
        return text
    return aliases.get(lowered)


def map_stereotypes(node: Mapping[str, Any]) -> list[str]:
    """Return the ordered, de-duplicated Cuttlefish stereotype list for a node."""
    found: list[str] = []
    seen: set[str] = set()

    def add(value: Any) -> None:
        name = _normalize_stereotype(value)
        if name and name not in seen:
            seen.add(name)
            found.append(name)

    raw = node.get("stereotypes")
    if isinstance(raw, str):
        add(raw)
    elif isinstance(raw, Sequence):
        for item in raw:
            add(item)
    add(node.get("stereotype"))

    if found:
        return found

    kind = _text(node.get("kind")).lower()
    module = _text(node.get("module")).lower()
    hay = _haystack(node)

    if kind in {"struct", "enum", "typedef", "data type"}:
        add("Data Type")
    elif kind in {"namespace", "package"}:
        add("Package")
    elif kind in {"composition"}:
        add("Composition")
    elif "complex device driver" in hay or " cdd" in f" {hay}":
        add("Complex Device Driver")
    elif "ecu abstraction" in hay or module in _ECU_ABSTRACTION_MODULES:
        add("ECU Abstraction")
    elif "sensor" in hay and "actuator" in hay:
        add("Sensor Actuator")
    elif module in _DRIVER_MODULES or kind == "driver":
        add("Driver")
    elif kind in {"service interface", "service"} or module in _SERVICE_MODULES:
        add("Service")
    else:
        add("Application")

    return found


def infer_curation(node: Mapping[str, Any]) -> str:
    explicit = _text(node.get("curation") or node.get("curationStatus"))
    if explicit in CURATION_SET:
        return explicit
    lowered = explicit.lower()
    aliases = {
        "reviewed": CURATION_REVIEWED,
        "review": CURATION_REVIEWED,
        "draft": CURATION_DRAFT,
        "unvalidated": CURATION_UNVALIDATED,
        "unchecked": CURATION_UNVALIDATED,
    }
    if lowered in aliases:
        return aliases[lowered]

    visibility = _text(node.get("visibility")).lower()
    if "ai" in visibility or _text(node.get("namespaceDeviation")):
        return CURATION_DRAFT
    # Derived Adaptive API pages are not independently reviewed as graph nodes.
    return CURATION_UNVALIDATED


def enrich_node(node: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(node)
    universe = infer_universe(out)
    stereotypes = map_stereotypes(out)
    curation = infer_curation(out)
    out["universe"] = universe
    out["universeLabel"] = UNIVERSE_LABELS[universe]
    out["universeBorder"] = UNIVERSE_BORDERS[universe]
    out["stereotypes"] = stereotypes
    out["stereotypeChips"] = [format_stereotype_chip(s) for s in stereotypes]
    out["curation"] = curation
    return out


def serialize_graph(graph: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a JSON-serializable graph with widget fields present on every node.

    Idempotent: a second pass does not change node identity, cardinality, or
    already-valid universe/stereotype/curation values. Missing nodes/edges
    become empty lists rather than being dropped as ``None``.
    """
    source = dict(graph or {})
    raw_nodes = source.get("nodes")
    raw_edges = source.get("edges")
    nodes_in = list(raw_nodes) if isinstance(raw_nodes, Sequence) and not isinstance(raw_nodes, (str, bytes)) else []
    edges_in = list(raw_edges) if isinstance(raw_edges, Sequence) and not isinstance(raw_edges, (str, bytes)) else []
    nodes = [enrich_node(n if isinstance(n, Mapping) else {"id": n}) for n in nodes_in]
    edges = [dict(e) if isinstance(e, Mapping) else {"id": e} for e in edges_in]
    out = dict(source)
    out["schema"] = source.get("schema") or SCHEMA
    out["nodes"] = nodes
    out["edges"] = edges
    out["universes"] = [dict(row) for row in UNIVERSE_CATALOG]
    out["stereotypeCatalog"] = list(STEREOTYPE_CATALOG)
    out["curationStatuses"] = list(CURATION_STATUSES)
    out["cuttlefish"] = {
        "inLibrary": CUTTLEFISH_IN_LIBRARY,
        "layout": CUTTLEFISH_LAYOUT,
        "fallbackLayouts": list(CUTTLEFISH_FALLBACK_LAYOUTS),
        "stereotypeSource": "autosar-swc-layers",
    }
    stats = dict(source.get("stats") or {})
    stats["nodes"] = len(nodes)
    stats["edges"] = len(edges)
    out["stats"] = stats
    return out


def node_matches_filters(
    node: Mapping[str, Any],
    *,
    universe: str = "all",
    stereotype: str = "all",
    curation: str = "all",
) -> bool:
    enriched = enrich_node(node)
    if universe not in {"", "all", None} and enriched["universe"] != universe:
        return False
    if curation not in {"", "all", None} and enriched["curation"] != curation:
        return False
    if stereotype not in {"", "all", None}:
        wanted = _normalize_stereotype(stereotype) or _text(stereotype)
        if wanted not in enriched["stereotypes"]:
            return False
    return True


def filter_nodes(
    nodes: Iterable[Mapping[str, Any]],
    *,
    universe: str = "all",
    stereotype: str = "all",
    curation: str = "all",
) -> list[dict[str, Any]]:
    return [
        enrich_node(n)
        for n in nodes
        if node_matches_filters(n, universe=universe, stereotype=stereotype, curation=curation)
    ]


def _esc(value: Any) -> str:
    return html.escape(_text(value), quote=True)


def _relationship_cells(
    node_id: str,
    edges: Sequence[Mapping[str, Any]],
    labels: Mapping[str, str],
) -> str:
    parts: list[str] = []
    for edge in edges:
        source = _text(edge.get("source"))
        target = _text(edge.get("target"))
        rel = _text(edge.get("type") or "reference")
        if source == node_id and target:
            parts.append(f"{rel} → {_esc(labels.get(target, target))}")
        elif target == node_id and source:
            parts.append(f"{rel} ← {_esc(labels.get(source, source))}")
    if not parts:
        return "—"
    return "; ".join(parts)


def fallback_table_html(graph: Mapping[str, Any] | None, href_prefix: str = "") -> str:
    """Semantic HTML tables listing every node, relationship, and stereotype.

    Used as the no-JS / Tabellenansicht surface (RQ-UIUX-012). Cardinality of
    the input node and edge sequences is preserved: nothing is silently dropped.
    """
    serialized = serialize_graph(graph)
    nodes = serialized["nodes"]
    edges = serialized["edges"]
    labels = {_text(n.get("id")): _text(n.get("label") or n.get("shortLabel") or n.get("id")) for n in nodes}

    node_rows: list[str] = []
    for node in nodes:
        node_id = _text(node.get("id"))
        chips = ", ".join(_esc(chip) for chip in node.get("stereotypeChips") or []) or "—"
        rel = _relationship_cells(node_id, edges, labels)
        href = _text(node.get("url"))
        name = _esc(node.get("label") or node.get("shortLabel") or node_id)
        name_html = f'<a href="{_esc(href_prefix + href)}">{name}</a>' if href else name
        node_rows.append(
            "<tr"
            f' data-node-id="{_esc(node_id)}"'
            f' data-universe="{_esc(node.get("universe"))}"'
            f' data-curation="{_esc(node.get("curation"))}"'
            f' data-stereotypes="{_esc("|".join(node.get("stereotypes") or []))}"'
            ">"
            f"<td>{_esc(node_id)}</td>"
            f"<td>{name_html}</td>"
            f"<td>{_esc(node.get('universeLabel') or node.get('universe'))}</td>"
            f"<td>{chips}</td>"
            f"<td>{_esc(node.get('curation'))}</td>"
            f"<td>{_esc(node.get('kind'))}</td>"
            f"<td>{_esc(node.get('module'))}</td>"
            f"<td>{rel}</td>"
            "</tr>"
        )

    edge_rows: list[str] = []
    for edge in edges:
        edge_rows.append(
            "<tr"
            f' data-edge-id="{_esc(edge.get("id"))}"'
            f' data-source="{_esc(edge.get("source"))}"'
            f' data-target="{_esc(edge.get("target"))}"'
            ">"
            f"<td>{_esc(edge.get('id'))}</td>"
            f"<td>{_esc(edge.get('source'))}</td>"
            f"<td>{_esc(edge.get('target'))}</td>"
            f"<td>{_esc(edge.get('type') or 'reference')}</td>"
            f"<td>{_esc(edge.get('weight'))}</td>"
            "</tr>"
        )

    node_body = "\n".join(node_rows) or '<tr><td colspan="8">Keine Knoten.</td></tr>'
    edge_body = "\n".join(edge_rows) or '<tr><td colspan="5">Keine Beziehungen.</td></tr>'
    return (
        '<div class="component-graph-fallback" data-graph-fallback id="component-graph-table">'
        "<h3>Komponentengraph (Tabellenansicht)</h3>"
        "<p class=\"dim\">Zugängliche Darstellung aller Knoten, Stereotypen und "
        "Beziehungen. Diese Tabelle bleibt ohne JavaScript lesbar (RQ-UIUX-012).</p>"
        '<table class="component-graph-table" data-graph-node-table>'
        f"<caption>Knoten ({len(nodes)})</caption>"
        "<thead><tr>"
        '<th scope="col">ID</th>'
        '<th scope="col">Name</th>'
        '<th scope="col">Universum</th>'
        '<th scope="col">Stereotypen</th>'
        '<th scope="col">Kuration</th>'
        '<th scope="col">Art</th>'
        '<th scope="col">Modul</th>'
        '<th scope="col">Beziehungen</th>'
        "</tr></thead>"
        f"<tbody>{node_body}</tbody>"
        "</table>"
        '<table class="component-graph-table" data-graph-edge-table>'
        f"<caption>Beziehungen ({len(edges)})</caption>"
        "<thead><tr>"
        '<th scope="col">ID</th>'
        '<th scope="col">Quelle</th>'
        '<th scope="col">Ziel</th>'
        '<th scope="col">Typ</th>'
        '<th scope="col">Gewicht</th>'
        "</tr></thead>"
        f"<tbody>{edge_body}</tbody>"
        "</table>"
        "</div>"
    )


def inspector_payload(node: Mapping[str, Any]) -> dict[str, Any]:
    """Payload of the ``component:selected`` event."""
    enriched = enrich_node(node)
    attributes = {
        key: value
        for key, value in enriched.items()
        if key not in {"id", "universe", "stereotypes"}
    }
    return {
        "id": enriched.get("id"),
        "universe": enriched["universe"],
        "stereotypes": list(enriched["stereotypes"]),
        "attributes": attributes,
    }
