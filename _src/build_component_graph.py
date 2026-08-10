#!/usr/bin/env python3
"""Build the abstract API dependency graph from page models and spec records.

The graph is derived, never hand-maintained. Record ownership comes from rec-ref
blocks in page models; dependencies come from internal links in the owned record.
"""
from __future__ import annotations
import argparse, json, posixpath, re
from collections import Counter, defaultdict
from pathlib import Path
from lxml import html as LH

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
PAGES = SRC / "sources" / "pages"
RECORDS = SRC / "spec" / "records"
OUT = ROOT / "data" / "component-graph.json"
MODULE_RE = re.compile(r'href="(?:\.\./)?modules/([^"/.]+)\.html"')


def walk(blocks):
    for block in blocks:
        yield block
        yield from walk(block.get("blocks", []))


def text(fragment):
    """HTML fragment → visible text (for kind badges etc.)."""
    try:
        return LH.fragment_fromstring(fragment, create_parent="div").text_content().strip()
    except Exception:
        return re.sub(r"<[^>]+>", "", fragment).strip()


def page_kind(page):
    for block in page.get("main", []):
        if block.get("t") == "html" and "<h1" in block.get("html", ""):
            m = re.search(r'<span class="kind">(.*?)</span>', block["html"], re.S)
            return text(m.group(1)).lower() if m else "page"
    return "page"


def qualified_name_of(page):
    """Best-effort qualified C++ name derived from a page title, e.g.
    "ara::core::Exception — ara::* API" -> "ara::core::Exception".
    Strips template placeholders like <T> for matching against base-class text.
    """
    label = page_label(page)
    label = re.sub(r"<[^>]*>", "", label).strip()
    return label


def page_label(page):
    # Titles are plain text and may contain C++ placeholders like <DataElement>.
    # Do NOT run them through an HTML parser — that strips the placeholders.
    title = re.sub(r"\s+", " ", (page.get("title") or "")).strip()
    label = re.split(r"\s+[—|]\s+", title, maxsplit=1)[0].strip()
    return label or page.get("file", "")


def short_label(label: str) -> str:
    """Compact node caption: last meaningful :: segment, keep <placeholders>."""
    if not label:
        return "?"
    parts = [p.strip() for p in label.split("::")]
    parts = [p for p in parts if p]
    s = parts[-1] if parts else label
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > 36:
        s = s[:34] + "…"
    return s or label[:36]


def module_of(page):
    file = page.get("file", "")
    if file.startswith("modules/"):
        return Path(file).stem
    m = MODULE_RE.search(page.get("nav_html", "") or "")
    if m:
        return m.group(1)
    title = re.sub(r"\s+", " ", (page.get("title") or "")).strip()
    m = re.search(r"(?:ara|apext)::([A-Za-z0-9_]+)", title)
    return m.group(1) if m else "other"


def internal_hrefs(value):
    """Extract internal hrefs from HTML fragments embedded anywhere in a record."""
    hrefs = []

    def visit(v):
        if isinstance(v, dict):
            for item in v.values():
                visit(item)
        elif isinstance(v, list):
            for item in v:
                visit(item)
        elif isinstance(v, str) and '<' in v and 'href=' in v:
            try:
                root = LH.fragment_fromstring(v, create_parent='div')
                for el in root.xpath('.//*[@href]'):
                    href = (el.get('href') or '').split('#', 1)[0]
                    if href:
                        hrefs.append(href)
            except Exception:
                pass

    visit(value)
    return hrefs


# Namensraum-Segmente sind in ara::* durchgaengig klein geschrieben, Typen
# beginnen mit Grossbuchstaben. Damit laesst sich aus einem qualifizierten
# Namen der Namensraum auch dann ableiten, wenn die Seite keinen eigenen
# Record besitzt (z. B. ara::log::Argument) oder einen verschachtelten Typ
# beschreibt (ara::diag::Conversation::ConversationIdentifierType -> ara::diag).
def namespace_from_label(label: str, kind: str = "") -> tuple[str | None, str | None]:
    if not label:
        return None, None
    name = re.sub(r"^namespace\s+", "", label.strip())
    name = re.sub(r"<[^<>]*>", "", name).strip()
    parts = [seg.strip() for seg in name.split("::") if seg.strip()]
    if not parts:
        return None, None
    if kind == "namespace":
        return "::".join(parts), None          # die Seite IST der Namensraum
    if parts[0] not in ("ara", "apext", "std"):
        return None, None                      # Modell-Platzhalter u. ae.
    ns, rest = [], []
    for seg in parts:
        if not rest and (seg[:1].islower() or seg[:1] == "_"):
            ns.append(seg)
        else:
            rest.append(seg)
    if not ns:
        return None, None
    enclosing = "::".join(ns + rest[:-1]) if len(rest) > 1 else None
    return "::".join(ns), enclosing


def module_label(module_id: str) -> str:
    return "Other" if module_id == "other" else f"ara::{module_id}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()

    pages = {}
    owners = defaultdict(set)
    for path in sorted(PAGES.rglob("*.json")):
        page = json.loads(path.read_text(encoding="utf-8"))
        file = page.get("file")
        if not file:
            continue
        pages[file] = page
        for block in walk(page.get("main", [])):
            if block.get("t") == "rec-ref":
                owners[Path(block["src"]).stem].add(file)

    name_to_file = {}
    for file, page in pages.items():
        name = qualified_name_of(page)
        if name:
            name_to_file.setdefault(name, file)

    # Namensraum/Modul kommen jetzt explizit aus den Spec-Records (ns-Block,
    # siehe KONVENTIONEN.md "Namensraum-Zugehoerigkeit") statt aus gerendertem
    # Navigations-HTML. Pro Seite gewinnt der haeufigste ns-Block ihrer Records.
    page_ns = defaultdict(Counter)
    for path in sorted(RECORDS.rglob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        ns = rec.get("ns") or {}
        if not ns.get("modul"):
            continue
        key = (ns.get("modul"), ns.get("namespace"), ns.get("abweichung"))
        for owner in owners.get(path.stem, ()):
            page_ns[owner][key] += 1

    def ns_of(file):
        counts = page_ns.get(file)
        if not counts:
            return None, None, None
        return counts.most_common(1)[0][0]

    nodes_used = set()
    edges = Counter()
    edge_records = defaultdict(set)
    inheritance_edges = set()

    # Inheritance is a formal schema field ("bases") on the page itself —
    # not re-derived from free-text HTML. Each entry: {access, name, href}.
    for source, page in pages.items():
        inheritance_files = set()
        for entry in page.get("bases", []):
            if entry.get("access") != "public":
                continue  # only public inheritance implies an is-a API relationship
            target_file = None
            href = entry.get("href")
            if href:
                target_file = posixpath.normpath(posixpath.join(posixpath.dirname(source), href))
                if target_file not in pages:
                    target_file = None
            if target_file is None:
                target_file = name_to_file.get(entry.get("name"))
            if not target_file or target_file == source or target_file not in pages:
                continue
            inheritance_files.add(target_file)
            key = (source, target_file)
            edges[key] += 3
            edge_records[key].add(f"bases:{source}")
            inheritance_edges.add(key)
            nodes_used.update(key)

    for path in sorted(RECORDS.rglob("*.json")):
        rid = path.stem
        record = json.loads(path.read_text(encoding="utf-8"))
        for source in owners.get(rid, ()):
            base = posixpath.dirname(source)
            inheritance_files = {
                posixpath.normpath(posixpath.join(base, e["href"]))
                for e in pages[source].get("bases", [])
                if e.get("access") == "public" and e.get("href")
            } if source in pages else set()
            for href in internal_hrefs(record):
                if re.match(r"^[a-z]+://", href) or href.startswith(("mailto:", "javascript:")):
                    continue
                target = posixpath.normpath(posixpath.join(base, href))
                if target not in pages or target == source:
                    continue
                key = (source, target)
                edges[key] += 2 if target in inheritance_files else 1
                edge_records[key].add(rid)
                nodes_used.update(key)

    node_rows = []
    module_ids = set()
    for file in sorted(nodes_used):
        page = pages[file]
        label = page_label(page)
        modul, namespace, abweichung = ns_of(file)
        kind = page_kind(page)
        # Seiten ohne eigenen Spec-Record (oder mit klassenbezogenem Scope)
        # bekommen den Namensraum aus ihrem qualifizierten Namen.
        enclosing = None
        if not namespace:
            namespace, enclosing = namespace_from_label(label, kind)
        row = {
            "id": file,
            "label": label,
            "shortLabel": short_label(label),
            "kind": kind,
            "module": modul or module_of(page),
            "namespace": namespace,
            "url": file,
            "visibility": page.get("body_class", ""),
        }
        if enclosing:
            row["enclosing"] = enclosing
        if abweichung:
            row["namespaceDeviation"] = abweichung
        module_ids.add(row["module"])
        node_rows.append(row)
    modules = sorted(module_ids)
    edge_rows = []
    for n, ((source, target), count) in enumerate(edges.most_common(), 1):
        edge_rows.append({
            "id": f"e{n}", "source": source, "target": target,
            "weight": count, "records": sorted(edge_records[(source, target)]),
            "type": "inheritance" if (source, target) in inheritance_edges else "reference",
        })
    result = {
        "schema": "ara-api-component-graph/v1",
        "derivedFrom": ["_src/sources/pages", "_src/spec/records"],
        "modules": [{"id": m, "label": module_label(m)} for m in modules],
        "nodes": node_rows,
        "edges": edge_rows,
        "stats": {"nodes": len(node_rows), "edges": len(edge_rows), "references": sum(edges.values())},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{args.output}: {len(node_rows)} nodes, {len(edge_rows)} edges, {sum(edges.values())} references")

if __name__ == "__main__":
    main()
