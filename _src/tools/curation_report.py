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
            item = curation_item.from_curation_flag(raw)
            if state_dir == "claimed":
                item["status"] = "claimed"
            elif state_dir == "done":
                item["status"] = "applied"
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
            item = curation_item.from_review_flag(raw)
            if state_dir == "claimed":
                item["status"] = "claimed"
            elif state_dir == "done":
                item["status"] = "applied"
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
    open_count = sum(1 for x in items if x.get("status") == "open")
    claimed_count = sum(1 for x in items if x.get("status") == "claimed")
    applied_count = sum(1 for x in items if x.get("status") == "applied")

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
</style>""")

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
<thead><tr><th>Kanonische ID</th><th>Projekt</th><th>Art</th><th>Feld</th><th>Status</th><th>Quelle / Seite</th><th>Vorschlag / Rationale</th></tr></thead>
<tbody>""")

    open_items = [x for x in items if x.get("status") == "open"]
    if open_items:
        for it in open_items:
            cid = _esc(it.get("canonical_id", "-"))
            proj = _esc(it.get("project", "-"))
            kind = _esc(it.get("item_kind", "-"))
            fld = _esc(it.get("field", "-"))
            st = it.get("status", "open")
            badge = f'<span class="cr-badge-{st}">{_esc(st)}</span>'
            tpage = it.get("target_page")
            link_html = f'<a href="{_esc(tpage)}">{_esc(cid)}</a>' if tpage else cid
            src_file = _esc(it.get("source_file", "-"))
            prop_val = _esc(it.get("proposed_value") or it.get("current_value") or "-")
            if len(prop_val) > 120:
                prop_val = prop_val[:117] + "..."
            raw_rid = it.get("canonical_id", "").split("/")[-1]
            row_id_attr = f' id="{_esc(raw_rid)}"' if raw_rid else ''
            html_parts.append(f"<tr{row_id_attr}><td><code>{link_html}</code></td><td>{proj}</td><td>{kind}</td><td><code>{fld}</code></td><td>{badge}</td><td><small>{src_file}</small></td><td>{prop_val}</td></tr>")
    else:
        html_parts.append("<tr><td colspan=\"7\">Keine offenen Kurations-Items vorhanden.</td></tr>")
    html_parts.append("</tbody></table></div></details>")

    # Claimed & applied items summary
    other_items = [x for x in items if x.get("status") in ("claimed", "applied")]
    html_parts.append(f"""<details class="cr-section">
<summary><strong>In Bearbeitung & Abgeschlossen ({len(other_items)})</strong></summary>
<div class="cr-table-wrap">
<table class="cr-table">
<thead><tr><th>Kanonische ID</th><th>Projekt</th><th>Art</th><th>Status</th><th>Bearbeiter</th><th>Quelle</th></tr></thead>
<tbody>""")
    if other_items:
        for it in other_items:
            cid = _esc(it.get("canonical_id", "-"))
            proj = _esc(it.get("project", "-"))
            kind = _esc(it.get("item_kind", "-"))
            st = it.get("status", "-")
            badge = f'<span class="cr-badge-{st}">{_esc(st)}</span>'
            curator = _esc(it.get("curator", "-"))
            src_file = _esc(it.get("source_file", "-"))
            raw_rid = it.get("canonical_id", "").split("/")[-1]
            row_id_attr = f' id="{_esc(raw_rid)}"' if raw_rid else ''
            html_parts.append(f"<tr{row_id_attr}><td><code>{cid}</code></td><td>{proj}</td><td>{kind}</td><td>{badge}</td><td>{curator}</td><td><small>{src_file}</small></td></tr>")
    else:
        html_parts.append("<tr><td colspan=\"6\">Keine weiteren Items vorhanden.</td></tr>")
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
