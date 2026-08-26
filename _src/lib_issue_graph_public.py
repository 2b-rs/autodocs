# -*- coding: utf-8 -*-
"""Public issue-graph page integration (Task 0037-23.02).

Consumes the locale-neutral projector output `_src/data/issue-graph-public.json`.
Does not rewrite the projector. Internal catalog paths stay out of published HTML.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re

SCHEMA = "issue-graph-public@v1"
PAYLOAD_REL = os.path.join("data", "issue-graph-public.json")
ITEM_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")
INTERNAL_PATH_TOKENS = (
    "issues/_views/",
    "issue-catalog.internal",
    "data/issue-catalog.internal.json",
    "privacy_projector.py",
    "../TODO.md",
    "TODO.md",
)
RESTRICTED_FIXTURE_TOKENS = (
    "SECRETLEAK",
    "claim.json",
    "/private/",
    "owner_token",
    "decision_ref",
    "finding_id",
)
REQUIRED_ITEM_KEYS = (
    "id",
    "level",
    "title_key",
    "title_source_hash",
    "state_coarse",
    "public_prerequisites",
    "public_summary_key",
    "link",
)


class PublicIssueGraphError(ValueError):
    """Missing, stale, or unsafe public payload — fail the build visibly."""


def payload_path(srcdir):
    return os.path.join(srcdir, PAYLOAD_REL)


def digest_file(path):
    with open(path, "rb") as f:
        return "sha256:" + hashlib.sha256(f.read()).hexdigest()


def _scan_blob(blob, extra=()):
    lowered = blob.lower()
    for token in INTERNAL_PATH_TOKENS + RESTRICTED_FIXTURE_TOKENS + extra:
        if token.lower() in lowered:
            raise PublicIssueGraphError("published payload must not contain %r" % token)


def load_public_graph(srcdir):
    path = payload_path(srcdir)
    if not os.path.isfile(path):
        raise PublicIssueGraphError(
            "required public issue-graph payload missing: %s" % path
        )
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        data = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PublicIssueGraphError("unreadable public issue-graph payload: %s" % exc) from exc
    if not isinstance(data, dict):
        raise PublicIssueGraphError("public issue-graph payload must be an object")
    if data.get("schema") != SCHEMA:
        raise PublicIssueGraphError(
            "stale or unsupported public issue-graph schema %r (want %s)"
            % (data.get("schema"), SCHEMA)
        )
    if "restricted_item_count" not in data or "items" not in data:
        raise PublicIssueGraphError("stale public issue-graph payload: missing required fields")
    if not isinstance(data["items"], list):
        raise PublicIssueGraphError("public issue-graph items must be a list")
    if not isinstance(data.get("restricted_item_count"), int):
        raise PublicIssueGraphError("restricted_item_count must be an integer")
    for item in data["items"]:
        if not isinstance(item, dict):
            raise PublicIssueGraphError("public issue-graph item must be an object")
        missing = [k for k in REQUIRED_ITEM_KEYS if k not in item]
        if missing:
            raise PublicIssueGraphError("stale public item missing keys: %s" % ",".join(missing))
        if not ITEM_ID_RE.match(str(item["id"])):
            raise PublicIssueGraphError("unsafe public item id %r" % item["id"])
    _scan_blob(raw)
    data["_payload_digest"] = digest_file(path)
    data["_payload_path"] = path
    return data


def public_anchor(item_id):
    return str(item_id)


def public_href(item_id, page="issues.html"):
    return "%s#%s" % (page, public_anchor(item_id))


def build_dot(payload):
    items = payload.get("items") or []
    lines = [
        "digraph public_issues {",
        "  graph [rankdir=LR, bgcolor=transparent];",
        '  node [shape=box, style=rounded, fontname="Helvetica"];',
        '  edge [fontname="Helvetica"];',
    ]
    seen = set()
    for item in items:
        iid = str(item["id"])
        seen.add(iid)
        label = "%s\\n%s" % (iid, item.get("title_key") or "")
        href = public_href(iid)
        lines.append(
            "  %s [id=%s, label=%s, URL=%s, href=%s];"
            % (
                _dot_id(iid),
                _dot_quote(iid),
                _dot_quote(label),
                _dot_quote(href),
                _dot_quote(href),
            )
        )
    edge_pairs = []
    for item in items:
        src = str(item["id"])
        for pred in item.get("public_prerequisites") or []:
            edge_pairs.append((str(pred), src))
    for edge in payload.get("edges") or []:
        if isinstance(edge, dict):
            frm, to = edge.get("from") or edge.get("source"), edge.get("to") or edge.get("target")
            if frm and to:
                edge_pairs.append((str(frm), str(to)))
    emitted = set()
    for frm, to in edge_pairs:
        key = (frm, to)
        if key in emitted:
            continue
        emitted.add(key)
        if frm not in seen or to not in seen:
            continue
        lines.append("  %s -> %s;" % (_dot_id(frm), _dot_id(to)))
    lines.append("}")
    return "\n".join(lines) + "\n"


def _dot_id(value):
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", value):
        return value
    return _dot_quote(value)


def _dot_quote(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_svg(payload):
    import lib_svgdiag as D

    return D.render_dot(build_dot(payload))


def summary_html(payload):
    items = payload.get("items") or []
    restricted = payload.get("restricted_item_count", 0)
    counts = {}
    for item in items:
        state = str(item.get("state_coarse") or "unknown")
        counts[state] = counts.get(state, 0) + 1
    parts = [
        '<div class="public-issue-summary" role="region" '
        'aria-labelledby="public-issue-summary-heading">',
        '<h2 id="public-issue-summary-heading" class="sect">Öffentlicher Bearbeitungsstand</h2>',
        '<p class="public-issue-counts" data-public-item-count="%d" '
        'data-restricted-item-count="%d" data-payload-digest="%s">'
        % (len(items), restricted, html.escape(payload["_payload_digest"], quote=True)),
        "Öffentlich zusammengefasst: <strong>%d</strong> Einträge. "
        "Intern beschränkt (ohne Identitäten): <strong>%d</strong>."
        % (len(items), restricted),
        "</p>",
        '<ul class="public-issue-list">',
    ]
    for item in items:
        iid = str(item["id"])
        title = html.escape(str(item.get("title_key") or iid))
        state = html.escape(str(item.get("state_coarse") or ""))
        summary = html.escape(str(item.get("public_summary_key") or ""))
        href = html.escape(public_href(iid), quote=True)
        parts.append(
            '<li><a href="%s">%s</a> — %s'
            ' <span class="dim">(%s)</span></li>'
            % (href, html.escape(iid), title, state)
        )
        if summary:
            parts[-1] = parts[-1].replace(
                "</li>",
                ' <span class="public-issue-item-summary dim">%s</span></li>' % summary,
            )
    if not items:
        parts.append("<li>Keine öffentlichen Einträge.</li>")
    parts.append("</ul></div>")
    return "".join(parts)


def issues_articles_html(payload):
    parts = []
    for item in items_sorted(payload):
        iid = str(item["id"])
        aid = html.escape(public_anchor(iid), quote=True)
        title = html.escape(str(item.get("title_key") or iid))
        state = html.escape(str(item.get("state_coarse") or ""))
        summary = html.escape(str(item.get("public_summary_key") or ""))
        level = html.escape(str(item.get("level") or ""))
        parts.append(
            '<article class="public-issue" id="%s" tabindex="-1">'
            "<h2>%s <span class=\"dim\">%s</span></h2>"
            "<p>Ebene: %s · Zustand: %s</p>"
            "<p>%s</p>"
            "</article>"
            % (aid, html.escape(iid), title, level, state, summary)
        )
    if not parts:
        parts.append('<p class="dim">Keine öffentlichen Einträge.</p>')
    return "".join(parts)


def items_sorted(payload):
    return sorted(payload.get("items") or [], key=lambda it: str(it["id"]))


def publication_view(payload):
    """Drop projector-internal store links; published hrefs are issues.html#id only."""
    public = {k: v for k, v in payload.items() if not str(k).startswith("_")}
    items = []
    for item in public.get("items") or []:
        cloned = dict(item)
        cloned["link"] = public_href(cloned["id"])
        items.append(cloned)
    public["items"] = items
    return public


def embed_json(payload):
    text = json.dumps(
        publication_view(payload),
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return text.replace("</", "<\\/")


def graph_region_html(payload, asset_prefix_marker="@@ASSET_PREFIX@@"):
    svg = render_svg(payload)
    json_blob = embed_json(payload)
    return "".join(
        [
            '<section id="public-issue-graph" class="public-issue-graph" '
            'data-payload-digest="%s" data-schema="%s">'
            % (
                html.escape(payload["_payload_digest"], quote=True),
                html.escape(SCHEMA, quote=True),
            ),
            summary_html(payload),
            '<div class="public-issue-svg" role="img" '
            'aria-label="Abhängigkeitsgraph der öffentlichen Einträge">',
            '<noscript><p>Ohne JavaScript bleibt die vorgerenderte Grafik und die Liste sichtbar.</p></noscript>',
            svg,
            "</div>",
            '<script id="issue-graph-public-data" type="application/json">',
            json_blob,
            "</script>",
            '<script src="%stools/issue-graph-public-embed.js" defer></script>'
            % asset_prefix_marker,
            "</section>",
        ]
    )


def apply_markers(html_text, srcdir, asset_prefix):
    if "@@PUBLIC_ISSUE_" not in html_text and "@@ASSET_PREFIX@@" not in html_text:
        return html_text
    payload = load_public_graph(srcdir)
    if "@@PUBLIC_ISSUE_GRAPH_REGION@@" in html_text:
        html_text = html_text.replace(
            "@@PUBLIC_ISSUE_GRAPH_REGION@@",
            graph_region_html(payload, asset_prefix),
        )
    if "@@PUBLIC_ISSUE_SUMMARY@@" in html_text:
        html_text = html_text.replace("@@PUBLIC_ISSUE_SUMMARY@@", summary_html(payload))
    if "@@PUBLIC_ISSUE_ARTICLES@@" in html_text:
        html_text = html_text.replace("@@PUBLIC_ISSUE_ARTICLES@@", issues_articles_html(payload))
    if "@@PUBLIC_ISSUE_GRAPH_JSON@@" in html_text:
        html_text = html_text.replace("@@PUBLIC_ISSUE_GRAPH_JSON@@", embed_json(payload))
    if "@@PUBLIC_ISSUE_GRAPH_SVG@@" in html_text:
        html_text = html_text.replace("@@PUBLIC_ISSUE_GRAPH_SVG@@", render_svg(payload))
    html_text = html_text.replace("@@ASSET_PREFIX@@", asset_prefix)
    _scan_published_html(html_text)
    return html_text


def _scan_published_html(html_text):
    lowered = html_text.lower()
    for token in INTERNAL_PATH_TOKENS + RESTRICTED_FIXTURE_TOKENS:
        # Allow the word "todo" in ordinary German copy; block fetch of TODO.md and catalog paths.
        if token == "TODO.md":
            if "todo.md" in lowered:
                raise PublicIssueGraphError("published HTML must not reference TODO.md")
            continue
        if token.lower() in lowered:
            raise PublicIssueGraphError("published HTML must not contain %r" % token)


def copy_published_payload(srcdir, rootdir):
    """Write a published copy of the sanitized graph (store paths rewritten)."""
    payload = load_public_graph(srcdir)
    dest_dir = os.path.join(rootdir, "data")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, "issue-graph-public.json")
    view = publication_view(payload)
    view["source_digest"] = payload["_payload_digest"]
    text = json.dumps(view, sort_keys=True, ensure_ascii=True, indent=2) + "\n"
    _scan_blob(text)
    with open(dest, "w", encoding="utf-8") as outf:
        outf.write(text)
    return dest


def validate_required_deployment(srcdir, html_blobs):
    payload = load_public_graph(srcdir)
    digest = payload["_payload_digest"]
    findings = []
    if not html_blobs:
        findings.append("required deployment missing generated public issue pages")
    for name, blob in html_blobs:
        if digest not in blob:
            findings.append("%s does not embed current public payload digest" % name)
        try:
            _scan_published_html(blob)
        except PublicIssueGraphError as exc:
            findings.append("%s: %s" % (name, exc))
        if 'id="' not in blob and "public-issue" not in blob:
            findings.append("%s missing public issue markup" % name)
    return findings, payload
