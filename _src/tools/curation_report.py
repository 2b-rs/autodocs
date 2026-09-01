#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
curation_report.py — Unified static curation report (Tasks 0006-09, 0006-10).

Collects open, claimed, and recent curation/review items across:
  - spec/curation-queue/ (open, claimed, done)
  - spec/review-queue/ (open, claimed, done)
Normalizes all payloads into the unified curation-item@v1 schema (curation_item.py),
exports a standalone JSON/JS dataset for dynamic filtering (0006-10), and generates
the browsable static page model _src/sources/pages/curation-report.json -> curation-report.html.

CLI:
    python3 _src/tools/curation_report.py build
"""
import csv
import html
from report_page_header import report_page_header
import json
import os
import sys
from pathlib import Path

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(SRC)
SPEC = os.path.join(SRC, "spec")
PAGE_MODEL = os.path.join(SRC, "sources", "pages", "curation-report.json")
DATASET_JSON = os.path.join(SRC, "data", "curation-items.json")
RECORDS_CSV = os.path.join(SRC, "data", "records.csv")

_TOOLS_DIR = os.path.join(SRC, "tools")
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
import curation_item  # noqa: E402
from canonical_id import parse_canonical_id  # noqa: E402


def _esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def load_page_index():
    mapping = {}
    if os.path.exists(RECORDS_CSV):
        with open(RECORDS_CSV, newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                rid = row.get("id")
                datei = row.get("datei")
                if rid and datei:
                    mapping[rid] = datei
    return mapping


def _normalize_queue_item(raw, state_dir, queue_name):
    """Keep direct canonical items intact while adapting legacy flags.

    Task 0019-07 queues S-Core exceptions as ``curation-item@v1`` directly so
    their source/version links and rejected-retention state survive reporting.
    The physical ``done`` directory means ``applied`` only for legacy flags;
    a canonical item carries its own valid persisted status and lifecycle state.
    """
    direct = raw.get("schema") == curation_item.CURATION_ITEM_SCHEMA
    if direct:
        item = dict(raw)
    elif queue_name == "curation":
        item = curation_item.from_curation_flag(raw)
    else:
        item = curation_item.from_review_flag(raw)
    if not direct:
        if state_dir == "claimed":
            item["status"] = "claimed"
        elif state_dir == "done":
            item["status"] = "applied"
    item["display_status"] = item.get("lifecycle_state") or item.get("status", "open")
    return item


def _evidence_links(item):
    """Render direct S-Core record/version/source links without inventing URLs."""
    links = item.get("links") or {}
    parts = []
    record = links.get("record")
    if isinstance(record, str) and record:
        parts.append(f'<a href="{_esc(record)}">Record</a>')
    versions = links.get("versions")
    if isinstance(versions, list) and versions:
        version_links = ", ".join(f'<a href="{_esc(url)}">Version</a>' for url in versions if isinstance(url, str) and url)
        if version_links:
            parts.append(version_links)
    source = links.get("source")
    if isinstance(source, str) and source:
        parts.append(f'<a href="{_esc(source)}">Source locator</a>')
    return " · ".join(parts) if parts else "-"


def collect_all_curation_items():
    """Scan both review-queue and curation-queue and normalize into curation-item@v1."""
    items = []
    page_map = load_page_index()

    # 1. curation-queue
    c_base = Path(SPEC) / "curation-queue"
    for state_dir in ("open", "claimed", "done"):
        p = c_base / state_dir
        if not p.is_dir():
            continue
        for f in sorted(p.glob("*.json")):
            try:
                raw = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            item = _normalize_queue_item(raw, state_dir, "curation")
            cid = item.get("canonical_id", "")
            raw_id = raw.get("id", "")
            target_page = page_map.get(raw_id) or page_map.get(cid.split("/")[-1])
            item["target_page"] = target_page
            item["source_file"] = f"spec/curation-queue/{state_dir}/{f.name}"
            items.append(item)

    # 2. review-queue
    r_base = Path(SPEC) / "review-queue"
    for state_dir in ("open", "claimed", "done"):
        p = r_base / state_dir
        if not p.is_dir():
            continue
        for f in sorted(p.glob("*.json")):
            try:
                raw = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            item = _normalize_queue_item(raw, state_dir, "review")
            cid = item.get("canonical_id", "")
            raw_id = raw.get("id", "")
            target_page = page_map.get(raw_id) or page_map.get(cid.split("/")[-1])
            item["target_page"] = target_page
            item["source_file"] = f"spec/review-queue/{state_dir}/{f.name}"
            items.append(item)

    return items


def generate_curation_report_page(items):
    """Build the static page model and export the dataset."""
    os.makedirs(os.path.dirname(DATASET_JSON), exist_ok=True)
    with open(DATASET_JSON, "w", encoding="utf-8") as f:
        json.dump({"schema": "curation-items-export@v1", "count": len(items), "items": items}, f, ensure_ascii=False, indent=1)

    total_count = len(items)
    open_count = sum(1 for x in items if x.get("display_status", x.get("status")) == "open")
    claimed_count = sum(1 for x in items if x.get("display_status", x.get("status")) == "claimed")
    applied_count = sum(1 for x in items if x.get("display_status", x.get("status")) in {"applied", "published"})

    html_parts = []
    html_parts.append("""<style>
.cr-head{padding:1.15rem 1.35rem;border:1px solid #d9dce3;border-radius:14px;background:linear-gradient(135deg,#f8faff,#eef4ff);margin:1rem 0 1.4rem}
.cr-meta{display:flex;gap:.5rem;flex-wrap:wrap;margin:.6rem 0 0}
.cr-meta span{background:#fff;border:1px solid #d7dcea;border-radius:999px;padding:.28rem .66rem;font-size:.88rem}
.cr-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:.8rem;margin:1rem 0 1.5rem}
.cr-grid article{border:1px solid #d9dce3;border-radius:12px;padding:.95rem;background:#fff;box-shadow:0 3px 14px rgba(20,40,80,.06)}
.cr-grid span{display:block;color:#596274}
.cr-grid strong{display:block;font-size:1.7rem;margin:.18rem 0;font-variant-numeric:tabular-nums}
.cr-section{border:1px solid #d9dce3;border-radius:10px;margin:.8rem 0;background:#fff;overflow:hidden}
.cr-section summary{display:flex;justify-content:space-between;gap:1rem;padding:.8rem 1rem;cursor:pointer;background:#f7f8fa}
.cr-table-wrap{overflow:auto;max-height:45rem}
.cr-table{border-collapse:collapse;width:100%;font-size:.88rem}
.cr-table th{position:sticky;top:0;background:#eef1f6;text-align:left;z-index:1}
.cr-table th,.cr-table td{padding:.5rem .7rem;border-bottom:1px solid #e4e7ec;vertical-align:top}
.cr-badge-open{color:#9a3412;background:#ffedd5;border-radius:999px;padding:.12rem .5rem;font-weight:600}
.cr-badge-claimed{color:#1e40af;background:#dbeafe;border-radius:999px;padding:.12rem .5rem;font-weight:600}
.cr-badge-applied{color:#166534;background:#dcfce7;border-radius:999px;padding:.12rem .5rem;font-weight:600}
.cr-badge-proposed{color:#7e22ce;background:#f3e8ff;border-radius:999px;padding:.12rem .5rem;font-weight:600}
.cr-badge-accepted{color:#166534;background:#dcfce7;border-radius:999px;padding:.12rem .5rem;font-weight:600}
.cr-badge-rejected{color:#991b1b;background:#fee2e2;border-radius:999px;padding:.12rem .5rem;font-weight:600}
.cr-badge-superseded{color:#4b5563;background:#f3f4f6;border-radius:999px;padding:.12rem .5rem;font-weight:600}
.cr-badge-published{color:#166534;background:#dcfce7;border-radius:999px;padding:.12rem .5rem;font-weight:600}
.cr-trust-self_declared{color:#92400e;background:#fef3c7;border-radius:999px;padding:.08rem .45rem;font-size:.78rem}
.cr-trust-github_authenticated{color:#166534;background:#dcfce7;border-radius:999px;padding:.08rem .45rem;font-size:.78rem}
</style>""")

    html_parts.append(report_page_header(generator="_src/tools/curation_report.py", data_source="_src/spec/curation-queue/ und _src/spec/review-queue/", purpose="Zeigt offene, beanspruchte und abgeschlossene Kurations- und Review-Entscheidungen; Status und Quelle erklären den jeweiligen Bearbeitungsstand."))
    html_parts.append(f"""<h1>Zentraler Kurations- & Review-Bericht</h1>
<section class="cr-head">
<p>Übersicht aller offenen, in Bearbeitung befindlichen und abgeschlossenen Kurations- und Review-Entscheidungen über alle Warteschlangen (<code>curation-queue</code>, <code>review-queue</code>). Normalisiert nach dem kanonischen <code>curation-item@v1</code> Schema.</p>
<p class="cr-meta">
<span>Gesamt-Items: <strong>{total_count}</strong></span>
<span>Offen: <strong>{open_count}</strong></span>
<span>In Bearbeitung: <strong>{claimed_count}</strong></span>
<span>Abgeschlossen: <strong>{applied_count}</strong></span>
</p>
</section>""")

    html_parts.append(f"""<h2 class="sect">Warteschlangen-Status</h2>
<div class="cr-grid">
<article><span>Offene Entscheidungen</span><strong>{open_count}</strong></article>
<article><span>Beansprucht (Claimed)</span><strong>{claimed_count}</strong></article>
<article><span>Abgeschlossen / Angewendet</span><strong>{applied_count}</strong></article>
<article><span>Gesamterfassung</span><strong>{total_count}</strong></article>
</div>""")

    # Open items table
    html_parts.append(f"""<details class="cr-section" open>
<summary><strong>Offene Kurations- & Review-Items ({open_count})</strong></summary>
<div class="cr-table-wrap">
<table class="cr-table">
<thead><tr><th>Kanonische ID</th><th>Projekt</th><th>Art</th><th>Feld</th><th>Status</th><th>Anfragende(r)</th><th>Record / Version / Quelle</th><th>Queue-Datei</th><th>Vorschlag / Rationale</th></tr></thead>
<tbody>""")

    def _requester_cell(it):
        """0021-06: for item_kind=review-request, show identity/trust and
        transport/target-version, mirroring the record-page queue-state
        panel (lib_docmodel._render_review_request_panel) rather than
        showing the generic 'curator' field, which is meaningless for a
        not-yet-decided request."""
        if it.get("item_kind") != "review-request":
            return _esc(it.get("curator", "-"))
        basis = it.get("decision_basis") or {}
        identity = _esc(it.get("current_state") or "-")
        trust_badge = f'<span class="cr-trust-{identity}">{identity}</span>' if identity in ("self_declared", "github_authenticated") else identity
        actor = _esc(basis.get("authoritative_actor") or it.get("decided_by") or "")
        transport = _esc(basis.get("transport") or "-")
        target_version = _esc(basis.get("target_version_id") or "-")
        return (f'{trust_badge}{" (" + actor + ")" if actor else ""}<br>'
                f'<small>Transport: <code>{transport}</code></small><br>'
                f'<small>Target version: <code>{target_version}</code></small>')

    open_items = [x for x in items if x.get("display_status", x.get("status")) == "open"]
    if open_items:
        for it in open_items:
            cid = _esc(it.get("canonical_id", "-"))
            proj = _esc(it.get("project", "-"))
            kind = _esc(it.get("item_kind", "-"))
            fld = _esc(it.get("field", "-"))
            st = it.get("display_status", it.get("status", "open"))
            badge = f'<span class="cr-badge-{st}">{_esc(st)}</span>'
            tpage = it.get("target_page")
            link_html = f'<a href="{_esc(tpage)}">{_esc(cid)}</a>' if tpage else cid
            evidence_links = _evidence_links(it)
            src_file = _esc(it.get("source_file", "-"))
            prop_val = _esc(it.get("proposed_value") or it.get("current_value") or "-")
            if len(prop_val) > 120:
                prop_val = prop_val[:117] + "..."
            raw_rid = it.get("canonical_id", "").split("/")[-1]
            row_id_attr = f' id="{_esc(raw_rid)}"' if raw_rid else ''
            requester_html = _requester_cell(it)
            html_parts.append(f"<tr{row_id_attr}><td><code>{link_html}</code></td><td>{proj}</td><td>{kind}</td><td><code>{fld}</code></td><td>{badge}</td><td>{requester_html}</td><td>{evidence_links}</td><td><small>{src_file}</small></td><td>{prop_val}</td></tr>")
    else:
        html_parts.append("<tr><td colspan=\"9\">Keine offenen Kurations-Items vorhanden.</td></tr>")
    html_parts.append("</tbody></table></div></details>")

    # 0021-06: previously only status in (claimed, applied) was shown here,
    # silently dropping proposed/accepted/rejected/superseded items -- which
    # meant a review-request's accepted or rejected lifecycle outcome (the
    # Definition of Done's central assertion) never appeared on this report
    # at all. Show every non-open status.
    other_items = [x for x in items if x.get("display_status", x.get("status")) != "open"]
    html_parts.append(f"""<details class="cr-section">
<summary><strong>In Bearbeitung & Abgeschlossen ({len(other_items)})</strong></summary>
<div class="cr-table-wrap">
<table class="cr-table">
<thead><tr><th>Kanonische ID</th><th>Projekt</th><th>Art</th><th>Status</th><th>Bearbeiter</th><th>Record / Version / Quelle</th><th>Queue-Datei</th></tr></thead>
<tbody>""")
    if other_items:
        for it in other_items:
            cid = _esc(it.get("canonical_id", "-"))
            proj = _esc(it.get("project", "-"))
            kind = _esc(it.get("item_kind", "-"))
            st = it.get("display_status", it.get("status", "-"))
            badge = f'<span class="cr-badge-{st}">{_esc(st)}</span>'
            curator = _requester_cell(it) if it.get("item_kind") == "review-request" else _esc(it.get("curator", "-"))
            evidence_links = _evidence_links(it)
            src_file = _esc(it.get("source_file", "-"))
            raw_rid = it.get("canonical_id", "").split("/")[-1]
            row_id_attr = f' id="{_esc(raw_rid)}"' if raw_rid else ''
            html_parts.append(f"<tr{row_id_attr}><td><code>{cid}</code></td><td>{proj}</td><td>{kind}</td><td>{badge}</td><td>{curator}</td><td>{evidence_links}</td><td><small>{src_file}</small></td></tr>")
    else:
        html_parts.append("<tr><td colspan=\"7\">Keine weiteren Items vorhanden.</td></tr>")
    html_parts.append("</tbody></table></div></details>")

    page_data = {
        "file": "curation-report.html",
        "title": "Zentraler Kurations- & Review-Bericht",
        "body_class": None,
        "nolang": True,
        "nav_html": "<a href=\"index.html\">Start</a> / <a href=\"process.html\">Prozess</a> / Kurations-Bericht",
        "footer": "extracted",
        "main_lead": "",
        "main": [
            {
                "t": "html",
                "html": "".join(html_parts)
            }
        ]
    }

    os.makedirs(os.path.dirname(PAGE_MODEL), exist_ok=True)
    with open(PAGE_MODEL, "w", encoding="utf-8") as f:
        json.dump(page_data, f, ensure_ascii=False, indent=1)

    return PAGE_MODEL


def main():
    items = collect_all_curation_items()
    page_path = generate_curation_report_page(items)
    print(f"Kurations-Bericht generiert: {page_path} ({len(items)} Items verarbeitet)")


if __name__ == "__main__":
    main()
