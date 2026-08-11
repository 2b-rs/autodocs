#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""open_reviews_report.py — Uebersichtsseite fuer alle offenen Reviews.

TODO.md, Level 1: "Overview page for all open reviews across the entire
Baum". Sammelt alle Requirement-Records mit offenem Review-Bedarf --
dieselbe Bedingung wie in lib_docmodel.render_blocks() (Zeilen ~372-374):
offenes review_flags-Element ODER suspects ODER review_status/status in
(pending, review, open) bzw. status.state beginnt mit "proposed/".

Baut daraus das Seitenmodell ``_src/sources/pages/open-reviews.json`` nach
demselben nolang-Muster wie ``extraction_report.py`` / ``e2e-requirements.json``
(rein deutsch, kein Uebersetzungsbaum, siehe AGENTS.md/Generierte Inhalte).

CLI:
    python3 _src/tools/open_reviews_report.py build

Anschliessend regenerieren + validieren:
    python3 _src/generate.py && python3 _src/validate.py

Dieses Werkzeug liest nur (spec/records/, data/records.csv) und schreibt nur
ein Seitenmodell unter sources/pages/ -- kein Netzzugriff, keine nennenswerte
CPU-Last, daher direkt ueber MCP ausfuehrbar (AGENTS.md).
"""
import csv
import html
import json
import os
import sys
from pathlib import Path

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(SRC)
RECORDS = Path(SRC) / "spec" / "records"
PAGE = Path(SRC) / "sources" / "pages" / "open-reviews.json"
RECORDS_CSV = Path(SRC) / "data" / "records.csv"
INDEX_PAGE = Path(SRC) / "sources" / "pages" / "index.json"

OUT_FILE = "open-reviews.html"

_REASON_LABELS = {
    "legacy_desc_import": "Legacy-Beschreibung pruefen",
    "text_repair": "Textkorrektur pruefen",
    "ambiguous_import": "Mehrdeutigen Import pruefen",
    "low_confidence": "Unsichere Zuordnung pruefen",
    "missing_space_suspects": "Fehlende Leerzeichen pruefen",
    "backend_mismatch": "Backend-Abweichung pruefen",
    "single_backend": "Nur ein Backend verfuegbar",
}


def _esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def _load_page_index():
    """record_id -> veroeffentlichte Seiten-Datei, aus data/records.csv."""
    mapping = {}
    if RECORDS_CSV.exists():
        with open(RECORDS_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rid = row.get("record_id")
                if rid:
                    mapping[rid] = row.get("datei")
    return mapping


def _is_reviewable(block, record):
    """Dieselbe Bedingung wie lib_docmodel.render_blocks() fuer requirement_text."""
    flags = [f for f in block.get("review_flags", []) if f.get("status", "open") == "open"]
    meta = record.get("requirement_meta") or {}
    review_state = str(block.get("review_status") or block.get("status")
                       or meta.get("review_status") or "").strip().lower()
    state = str((record.get("status") or {}).get("state") or "")
    return bool(flags or block.get("suspects") or review_state in ("pending", "review", "open")
               or state.startswith("proposed/")), flags


def collect_open_reviews():
    page_of = _load_page_index()
    items = []
    for f in sorted(RECORDS.glob("**/*.json")):
        try:
            record = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for block in record.get("blocks", []):
            if block.get("t") != "requirement_text":
                continue
            reviewable, flags = _is_reviewable(block, record)
            if not reviewable:
                continue
            rid = record.get("id")
            meta = record.get("requirement_meta") or {}
            items.append({
                "id": rid,
                "heading": meta.get("heading") or rid,
                "document": meta.get("document"),
                "page": meta.get("page"),
                "module": meta.get("module"),
                "confidence": meta.get("confidence"),
                "review_reason": meta.get("review_reason"),
                "status_state": (record.get("status") or {}).get("state"),
                "upstream": meta.get("upstream") or [],
                "page_file": page_of.get(rid),
                "has_flag": bool(flags),
                "suspects": bool(block.get("suspects")),
                "text_en": block.get("text_en") or "",
                "record_path": str(f.relative_to(Path(ROOT))),
            })
    items.sort(key=lambda it: (it["document"] or "", it["page"] or 0, it["id"] or ""))
    return items


def _row_html(it):
    if it["page_file"]:
        link = '<a href="%s#review-%s">%s</a>' % (_esc(it["page_file"]), _esc(it["id"]), _esc(it["id"]))
    else:
        link = '<code class="nolink">%s</code>' % _esc(it["id"])
    reason_label = _REASON_LABELS.get(it["review_reason"], it["review_reason"] or "Review angefordert")
    src = "%s S.%s" % (it["document"], it["page"]) if it["document"] else "—"
    upstream = ", ".join(it["upstream"]) if it["upstream"] else "—"
    text = it["text_en"]
    if len(text) > 160:
        text = text[:157] + "…"
    return (
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (link, _esc(it["heading"]), _esc(src), _esc(it["confidence"] or "—"),
           _esc(reason_label), _esc(upstream), _esc(text))
    )


def build_page(items):
    n = len(items)
    n_with_page = sum(1 for it in items if it["page_file"])
    n_orphan = n - n_with_page
    docs = sorted({it["document"] for it in items if it["document"]})
    stats_html = (
        '<p class="or-stats"><span>Offene Reviews: <strong>%d</strong></span>'
        '<span>Mit veroeffentlichter Seite: <strong>%d</strong></span>'
        '<span>Ohne veroeffentlichte Seite: <strong>%d</strong></span>'
        '<span>Quelldokumente: <strong>%d</strong></span></p>'
        % (n, n_with_page, n_orphan, len(docs))
    )
    intro = (
        '<section class="or-head"><p>Sammelt jedes Requirement mit offenem Review-Bedarf '
        '(offenes <code>review_flag</code>, unbestaetigte <code>suspects</code> oder Status '
        'ausstehend/proposed) unabhaengig vom Bereich. Ein Eintrag ohne veroeffentlichte Seite '
        'ist ein Testfixture oder eine bislang nicht in die API-Referenz aufgenommene Anforderung '
        '(z.\u00a0B. <code>PRS_E2E_*</code>) und wird nur als Record-ID angezeigt.</p>%s</section>'
        % stats_html
    )
    style = (
        "<style>\n"
        ".or-head{padding:1.15rem 1.35rem;border:1px solid #d9dce3;border-radius:14px;"
        "background:linear-gradient(135deg,#fff7f0,#fff1e8);margin:1rem 0 1.4rem}\n"
        ".or-stats{display:flex;gap:.5rem;flex-wrap:wrap;margin:.6rem 0 0}\n"
        ".or-stats span{background:#fff;border:1px solid #ecd9c8;border-radius:999px;"
        "padding:.28rem .66rem;font-size:.88rem}\n"
        ".or-table-wrap{overflow:auto;max-height:64rem;border:1px solid #d9dce3;border-radius:10px}\n"
        ".or-table{border-collapse:collapse;width:100%;font-size:.87rem}\n"
        ".or-table th{position:sticky;top:0;background:#eef1f6;text-align:left;z-index:1}\n"
        ".or-table th,.or-table td{padding:.5rem .7rem;border-bottom:1px solid #e4e7ec;"
        "vertical-align:top}\n"
        ".or-table tbody tr:nth-child(even){background:#fafbfc}\n"
        ".or-table code.nolink{color:#6b7280}\n"
        "</style>"
    )
    rows = "".join(_row_html(it) for it in items)
    table = (
        '<div class="or-table-wrap"><table class="or-table"><thead><tr>'
        "<th>Requirement-ID</th><th>Ueberschrift</th><th>Quelle</th><th>Konfidenz</th>"
        "<th>Review-Grund</th><th>Upstream</th><th>Anforderungstext</th>"
        "</tr></thead><tbody>%s</tbody></table></div>" % rows
    )
    return {
        "file": OUT_FILE,
        "title": "Offene Reviews — Gesamtuebersicht",
        "body_class": None,
        "nolang": True,
        "nav_html": '<a href="index.html">Start</a> / Offene Reviews',
        "footer": "extracted",
        "main_lead": "",
        "main": [
            {"t": "html", "html": "<h1>Offene Reviews — Gesamtuebersicht</h1>", "tail": "\n"},
            {"t": "html", "html": style + intro, "tail": "\n"},
            {"t": "html", "html": table, "tail": "\n"},
        ],
    }


def cmd_build():
    items = collect_open_reviews()
    page = build_page(items)
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(json.dumps(page, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("open-reviews.json geschrieben: %d offene Reviews, %d ohne veroeffentlichte Seite"
          % (len(items), sum(1 for it in items if not it["page_file"])))


def main(argv=None):
    args = argv if argv is not None else sys.argv[1:]
    if not args or args[0] != "build":
        print(__doc__.splitlines()[0])
        return 1
    cmd_build()
    return 0


if __name__ == "__main__":
    sys.exit(main())
