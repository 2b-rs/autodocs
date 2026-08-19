#!/usr/bin/env python3
"""Read-only completeness checks for explicitly opted-in localized page families.

Usage: python3 _src/tools/validate_page_i18n.py --root . --config _src/i18n/page_families.json --json
"""
import argparse
import json
import sys
from pathlib import Path

from lxml import html as LH


def finding(code, family, detail):
    return {"code": code, "family": family, "detail": detail}


def page_texts(page):
    """Return authored source text used for register coverage, not all HTML text."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from lib_i18n import inline_html_labels, leaf_segmente, maskiere, seg_id

    segments, labels = set(), set()

    def html_text(raw):
        if not raw:
            return
        wrapper = LH.fragment_fromstring(raw, create_parent="x")
        for element in leaf_segmente(wrapper):
            masked, _ = maskiere(element)
            if masked.strip():
                segments.add(seg_id(masked.strip()))
        for element in wrapper.iter():
            if element.tag == "h1":
                masked, _ = maskiere(element)
                if masked.strip():
                    segments.add(seg_id(masked.strip()))
        labels.update(inline_html_labels(wrapper))

    for value in (page.get("title", ""), page.get("nav_html", ""), page.get("main_lead", "")):
        html_text(value)

    def blocks(items):
        for block in items:
            if block.get("nolang"):
                continue
            if block.get("t") == "html":
                html_text(block.get("html", ""))
            elif block.get("t") in ("rec", "fold"):
                blocks(block.get("blocks", []))
            elif block.get("t") == "props":
                for row in block.get("rows", []):
                    html_text(row.get("th", "")); html_text(row.get("td", ""))
            elif block.get("t") == "params":
                for row in block.get("rows", []):
                    for cell in row.get("cells", []): html_text(cell.get("html", ""))
    blocks(page.get("main", []))
    return segments, labels


def dom(path):
    return LH.parse(str(path)).getroot()


def visible_strings(tree):
    return [text.strip() for text in tree.xpath("//text()[normalize-space()]") if text.strip()]


def check_family(root, family):
    name, findings = family["id"], []
    if family.get("status") == "retired":
        return findings
    source = root / family["source"]
    try:
        page = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [finding("source-unreadable", name, str(exc))]
    if page.get(family.get("opt_in_key", "i18n_complete")) is not True:
        return [finding("missing-opt-in", name, str(source))]
    try:
        source_segments, source_labels = page_texts(page)
        registers = root / family["register_root"]
        de_segments = set(json.loads((registers / "segments.de.json").read_text(encoding="utf-8")))
        de_labels = set(json.loads((registers / "labels.de.json").read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        return [finding("register-unreadable", name, str(exc))]
    for value in sorted(source_segments - de_segments): findings.append(finding("missing-extraction", name, value))
    for value in sorted(source_labels - de_labels): findings.append(finding("missing-label-extraction", name, value))
    german = root / family["page"]
    if not german.is_file(): return findings + [finding("missing-rendered-source", name, str(german))]
    de_tree = dom(german)
    de_ids = set(de_tree.xpath("//@id"))
    de_aria = de_tree.xpath("//@aria-label")
    de_svg = de_tree.xpath("//*[local-name()='svg']//*[local-name()='text' or local-name()='tspan']/text()")
    protected = family.get("protected_terms", [])
    for locale in family["locales"]:
        localized = root / locale / family["page"]
        if not localized.is_file():
            findings.append(finding("missing-rendered-output", name, locale)); continue
        tree = dom(localized)
        if set(tree.xpath("//@id")) != de_ids: findings.append(finding("anchor-mismatch", name, locale))
        if len(tree.xpath("//@aria-label")) != len(de_aria): findings.append(finding("aria-coverage", name, locale))
        if len(tree.xpath("//*[local-name()='svg']//*[local-name()='text' or local-name()='tspan']/text()")) != len(de_svg): findings.append(finding("inline-svg-coverage", name, locale))
        text = "\n".join(visible_strings(tree) + tree.xpath("//@aria-label"))
        for marker in family.get("fallback_markers", []):
            if marker and marker not in protected and marker in text: findings.append(finding("fallback-or-leak", name, locale + ": " + marker))
    return findings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--config", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        config = json.loads((root / args.config).read_text(encoding="utf-8"))
        assert config.get("schema") == "page-i18n-families@v1"
        families = config["families"]
    except (OSError, json.JSONDecodeError, AssertionError, KeyError) as exc:
        print(json.dumps({"verdict":"FAIL", "findings":[finding("invalid-config", "config", str(exc))]})); return 2
    results = [item for family in families for item in check_family(root, family)]
    report = {"schema":"page-i18n-validation@v1", "verdict":"PASS" if not results else "FAIL", "finding_count":len(results), "findings":results[:100], "truncated":len(results) > 100}
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if not results else 1

if __name__ == "__main__":
    raise SystemExit(main())
