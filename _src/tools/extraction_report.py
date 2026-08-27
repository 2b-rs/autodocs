#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extraction_report.py — Extraktions-Bericht mit vollstaendiger Abweichungsliste.

Fasst die vier am 2026-08-11 behobenen Extraktions-Fehlerklassen in
``_src/tools/spec_scrape.py`` zusammen und listet JEDE betroffene Record-ID im
Volltext, gruppiert nach Quellseite, zusammen mit einem Seiten-Screenshot des
PDFs. Baut daraus das Seitenmodell ``_src/sources/pages/extraction-report.json``
sowie einen Startseiten-Link, nach demselben Muster wie ``traceability_report.py``.

CLI:
    python3 _src/tools/extraction_report.py build
    python3 _src/tools/extraction_report.py collect-one traceability output.json
    python3 _src/tools/extraction_report.py render-shots output/records/*.json
    python3 _src/tools/extraction_report.py assemble output/records

Screenshots werden per ``pdftoppm`` aus dem versionierten PDF-Cache gerendert
und unter ``extraction-report-assets/`` (Website-Wurzel) abgelegt. Der Bericht
ist bewusst nur deutsch (Seitenmodell-Flag ``nolang``); er wird nicht in die
Sprachbaeume uebersetzt.
"""
import argparse, glob, html, json, os, re, subprocess, sys
from report_page_header import report_page_header
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path

WORKERS = min(12, os.cpu_count() or 12)

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(SRC)
TOOLS = os.path.join(SRC, "tools")
sys.path.insert(0, TOOLS)
import spec_scrape as ss

PAGE = os.path.join(SRC, "sources", "pages", "extraction-report.json")
INDEX = os.path.join(SRC, "sources", "pages", "index.json")
PDF_DIR = os.path.join(SRC, "spec", "pdf-cache", "R25-11")
ASSET_DIR = os.path.join(ROOT, "extraction-report-assets")

CATEGORIES = {
    "history_continuation": {
        "title": "Mehrseitige „Document Change History“-Fortsetzung",
        "commit": "bae18b1c",
        "problem": "Mehrseitige Changelog-Tabellen (datiertes „AUTOSAR / Release / Management“-Format) wurden auf Folgeseiten nicht mehr als Historie erkannt, weil dort keine neue Ueberschrift auftrat. IDs, die dort nur als Aenderungshistorie referenziert werden, wurden als lokale Definitionen fehlinterpretiert.",
        "fix": "Zustandsbehafteter Fortsetzungs-Check: Endet eine Seite in einer Historie-Region, gilt die naechste Seite als Fortsetzung, solange sie mit dem bekannten Changelog-Muster beginnt.",
    },
    "traceability": {
        "title": "„Requirements Tracing“-Tabellen",
        "commit": "c2334c43 / ffa42b17",
        "problem": "Seiten, die mit „N Requirements Tracing“ beginnen, listen Upstream- oder fremde Requirement-IDs auf, keine lokalen Definitionen. Diese IDs wurden trotzdem als Definitionskandidaten fuer das aktuelle Dokument gezaehlt.",
        "fix": "Neue „traceability“-Region ab der Ueberschrift bis zum Seitenende; IDs darin zaehlen nicht mehr als lokale Definition. Backend-symmetrisch (toleriert fuehrende Leerzeilen des builtin-Backends).",
    },
    "number_heading": {
        "title": "Anhangs-Tabellen „Number Heading“",
        "commit": "e554a1a8",
        "problem": "Mehrseitige Anhangs-Tabellen „Added/Changed/Deleted Requirements“ beginnen mit „Number Heading“ und tragen ihre Beschriftung erst am Ende der Tabelle. Ohne erneute Ueberschrift auf Folgeseiten wurden solche Zeilen als normaler Fliesstext behandelt und ihre IDs als lokale Definitionen gezaehlt.",
        "fix": "Zweites Fortsetzungsmuster: Eine Seite gilt als Historie-Fortsetzung, wenn sie mit „Number Heading“ beginnt UND eine „Added/Changed/Deleted Requirements|Constraints“-Beschriftung traegt. Die Kombination verhindert Fehltreffer bei regulaeren SWS-Schnittstellentabellen im gleichen Layout ohne diese Beschriftung.",
    },
    "heading_label": {
        "title": "Ueberschrift faelschlich als Label-Zeile verworfen",
        "commit": "751013a2",
        "problem": "Die Ueberschriften-Erkennung nutzte einen ungebundenen Praefix-Abgleich gegen bekannte Feldbezeichner. Echte Requirement-Titel, die zufaellig mit denselben Woertern beginnen wie ein Feldname („Header file“, „Type“, „Return value“), wurden dadurch verworfen und ergaben eine leere Ueberschrift.",
        "fix": "Eigenes, strengeres Muster nur fuer die Ueberschriften-Pruefung: ein Feldbezeichner zaehlt nur als Label-Zeile, wenn ihm ein Doppelpunkt folgt oder er die gesamte Zeile bildet.",
    },
}

# Kurationsanfragen: Faelle, die die Extraktion NICHT automatisch entscheiden
# kann. Jeder Eintrag erscheint am Seitenanfang mit Screenshot (falls page
# gesetzt ist), aktuellem Extraktionsergebnis und Klartext-Erklaerung, was
# heute passiert und welche Entscheidung von der Kuratorin/dem Kurator
# gefragt ist. Die Entscheidung selbst wird ueber das bestehende
# Review-Widget (review.js) als GitHub-Issue abgegeben; siehe
# ``curation_ingest.py`` fuer die Weiterverarbeitung.
RESIDUAL = [
    {"id": "RS_DIAG_04005", "document": "AUTOSAR_FO_RS_Diagnostics", "page": 15,
     "status": "resolved",
     "resolution": {"git_rev": "cfcf23a3", "resolved_at": "2026-08-11",
                     "note": "Parser-Fix in spec_scrape.py::_record_slice: bevorzugt echten "
                             "Definitionsanker „[ID] ... ⌈“ statt Inline-Zitat. RS_DIAG_04005 und "
                             "RS_Diag_04006 werden seither korrekt als zwei getrennte Requirements "
                             "extrahiert (Security Access Handling bzw. Session Handling)."},
     "current_result": "Die Extraktion verwechselte zwei benachbarte Requirements auf derselben Seite: "
                        "Beim Record RS_DIAG_04005 landete der Rest des vorherigen Items, weil die "
                        "Inline-Referenz „Dependencies: [RS_Diag_04005] ...“ aus RS_Diag_04006 als Start "
                        "des Records erkannt wurde.",
     "simple_explanation": "Auf der Seite stehen zwei verschiedene Requirements direkt hintereinander: "
                            "RS_Diag_04006 zu Session Handling und RS_Diag_04005 zu Security Access Handling. "
                            "Das Werkzeug sprang beim zweiten faelschlich schon auf die Verweisstelle im "
                            "ersten und nicht erst auf die echte Definition darunter.",
     "decision_ask": "War ein Parser-Fehler, kein Kurationsentscheid — behoben, siehe Aufloesung."},
    {"id": "RS_SAF_21101", "document": "AUTOSAR_AP_RS_PlatformHealthManagement", "page": 9,
     "status": "open",
     "current_result": "Kein Record wird angelegt; die Extraktion verwirft die ID, weil auf dieser "
                        "und der Folgeseite keine zugehoerige Definition (Ueberschrift + Beschreibung) "
                        "gefunden wird.",
     "simple_explanation": "Die ID taucht hier nur als Verweis in eckigen Klammern auf, z. B. "
                            "„[RS_SAF_21101]“ — wie eine Fussnote, die auf ein Requirement an anderer "
                            "Stelle zeigt. Es gibt an dieser Stelle keinen eigenen Beschreibungstext.",
     "decision_ask": "Ist es richtig, diese reine Zitierstelle zu ignorieren, oder soll trotzdem ein "
                      "leerer Platzhalter-Record angelegt werden, damit die ID nicht ganz fehlt?"},
    {"id": "RS_LT_00001", "document": "AUTOSAR_FO_RS_LogAndTrace", "page": 41,
     "status": "open",
     "current_result": "Die Extraktion legt den Record ohne eigene Ueberschrift an (Feld „heading“ "
                        "bleibt leer); Beschreibungstext und Metadaten werden trotzdem uebernommen.",
     "simple_explanation": "Bei diesem und rund einem Dutzend weiterer Requirements in diesem "
                            "Dokument fehlt im Original-PDF die sonst uebliche Titelzeile zwischen "
                            "der eckigen ID und dem Beschreibungstext — das Layout dieser Tabelle hat "
                            "schlicht keine eigene Spalte dafuer vorgesehen.",
     "decision_ask": "Soll fuer diese Faelle dauerhaft eine leere Ueberschrift akzeptiert werden, "
                      "oder soll das Werkzeug ersatzweise die erste Textzeile als Ueberschrift "
                      "uebernehmen?"},
]

STIL = """<style>
.tr-head{padding:1.15rem 1.35rem;border:1px solid #d9dce3;border-radius:14px;background:linear-gradient(135deg,#f7f8ff,#eef5ff);margin:1rem 0 1.4rem}
.tr-meta{display:flex;gap:.5rem;flex-wrap:wrap;margin:.6rem 0 0}
.tr-meta span{background:#fff;border:1px solid #d7dcea;border-radius:999px;padding:.28rem .66rem;font-size:.88rem}
.tr-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:.8rem;margin:1rem 0 1.5rem}
.tr-grid article{border:1px solid #d9dce3;border-radius:12px;padding:.95rem;background:#fff;box-shadow:0 3px 14px rgba(20,40,80,.06)}
.tr-grid span,.tr-grid small{display:block;color:#596274}
.tr-grid strong{display:block;font-size:1.7rem;margin:.18rem 0;font-variant-numeric:tabular-nums}
.tr-section{border:1px solid #d9dce3;border-radius:10px;margin:.8rem 0;background:#fff;overflow:hidden}
.tr-section summary{display:flex;justify-content:space-between;gap:1rem;padding:.8rem 1rem;cursor:pointer;background:#f7f8fa}
.tr-section summary span{font-variant-numeric:tabular-nums;background:#e7ecf6;border-radius:999px;padding:.1rem .55rem}
.tr-table-wrap{overflow:auto;max-height:52rem}
.tr-table{border-collapse:collapse;width:100%;font-size:.9rem}
.tr-table th{position:sticky;top:0;background:#eef1f6;text-align:left;z-index:1}
.tr-table th,.tr-table td{padding:.5rem .7rem;border-bottom:1px solid #e4e7ec;vertical-align:top}
.tr-table tbody tr:nth-child(even){background:#fafbfc}
.tr-table code.nolink{color:#6b7280}
.tr-page-group{border:1px dashed #d0d5e0;border-radius:10px;padding:.8rem 1rem;margin:.9rem 0;background:#fdfdff}
.tr-page-group h4{margin:.1rem 0 .6rem;font-size:.95rem}
.tr-screenshot{margin:.4rem 0 .8rem;max-width:22rem}
.tr-screenshot a{display:block;border:1px solid #d9dce3;border-radius:8px;overflow:hidden;background:#fff;box-shadow:0 2px 8px rgba(20,40,80,.06)}
.tr-screenshot img{display:block;width:100%;height:auto}
.tr-record-list details{border:1px solid #e4e7ec;border-radius:8px;margin:.4rem 0;background:#fff}
.tr-record-list summary{padding:.5rem .75rem;cursor:pointer;display:flex;justify-content:space-between;gap:1rem}
.tr-pdf-context{white-space:pre-wrap;word-break:break-word;background:#f7f8fa;border-radius:6px;padding:.6rem .75rem;font-size:.83rem;margin:.5rem .75rem .75rem;border:1px solid #eceef2}
.tr-curation{border:1px solid #d6dbe8;border-radius:14px;background:linear-gradient(180deg,#fff,#f8fbff);padding:1rem 1.05rem;margin:1rem 0 1.25rem;box-shadow:0 5px 18px rgba(20,40,80,.07)}
.tr-curation h3{margin:.1rem 0 .7rem;font-size:1.02rem}
.tr-curation-grid{display:grid;grid-template-columns:minmax(0,22rem) minmax(0,1fr);gap:1rem;align-items:start}
.tr-curation-copy p{margin:.45rem 0}
.tr-curation-copy .label{font-weight:700;color:#24344d}
.tr-curation .review-panel{margin-top:.9rem}
.tr-curation .review-panel summary{background:#eef5ff}
.tr-curation-note{background:#eef6ff;border:1px solid #cfe0ff;border-radius:10px;padding:.8rem .9rem;margin:.65rem 0 0}
.tr-curation-note p{margin:.35rem 0}
.tr-curation-resolved{opacity:.88;background:linear-gradient(180deg,#fff,#f7fbf5)}
.tr-curation-badge{display:inline-block;background:#dff3e2;color:#1f6b34;border-radius:999px;padding:.1rem .55rem;font-size:.72rem;font-weight:700;letter-spacing:.02em;margin-right:.4rem;vertical-align:middle}
.tr-curation-resolved .tr-curation-note{background:#eef8ef;border-color:#cdead2}
.tr-version-note{margin:.5rem 0 0;font-size:.82rem;color:#425064}
</style>"""


def esc(v):
    return html.escape(str(v), quote=True)


def all_pdf_paths():
    return sorted(glob.glob(os.path.join(PDF_DIR, "**", "AUTOSAR_*_RS_*.pdf"), recursive=True))


@lru_cache(maxsize=None)
def resolve_pdf_path(doc_stem):
    matches = glob.glob(os.path.join(PDF_DIR, "**", doc_stem + ".pdf"), recursive=True)
    if not matches:
        raise FileNotFoundError("PDF nicht im Cache gefunden: %s.pdf unter %s" % (doc_stem, PDF_DIR))
    if len(matches) > 1:
        raise RuntimeError("mehrdeutiger PDF-Name im Cache: %s.pdf -> %s" % (doc_stem, matches))
    return matches[0]


@lru_cache(maxsize=None)
def _pdf_pages_cached(pdf_path):
    return tuple(ss.strip_noise(x) for x in ss.pdf_pages(Path(pdf_path), "pypdf"))


@lru_cache(maxsize=None)
def _page_text_cached(doc_stem, pageno):
    pages = _pdf_pages_cached(resolve_pdf_path(doc_stem))
    idx = pageno - 1
    return pages[idx] if idx < len(pages) else ""


def page_text(doc_stem, pageno):
    return _page_text_cached(doc_stem, pageno)


def _collect_from_pdf(pdf_path):
    doc = Path(pdf_path).stem
    pages = _pdf_pages_cached(pdf_path)
    history = []
    traceability = []
    number_heading = []
    heading_label = []

    for i, t in enumerate(pages, start=1):
        if ss.HISTORY_CONTINUATION_RE.search(t):
            for m in ss.DEF_RE.finditer(t):
                history.append({"id": m.group(1).upper(), "document": doc, "page": i})
        if ss.TRACEABILITY_HEADING_RE.search(t):
            for m in ss.DEF_RE.finditer(t):
                traceability.append({"id": m.group(1).upper(), "document": doc, "page": i})
        if ss.HISTORY_NUMBER_HEADING_CONTINUATION_RE.search(t) and ss.HISTORY_TABLE_CAPTION_RE.search(t):
            for m in ss.DEF_RE.finditer(t):
                number_heading.append({"id": m.group(1).upper(), "document": doc, "page": i})

    old_label_re = re.compile(r"^(%s)\s*:?\s*(.*)$" % "|".join(re.escape(x) for x in ss.LABELS))

    def old_heading(chunk):
        head_part = re.split(r"(?:⌈|(?:^|\n)\s*(?:Status|Upstream requirements?|Kind)\s*:?)", chunk.lstrip("\n"), maxsplit=1)[0]
        head = ss._clean_value(" ".join(line.strip() for line in head_part.split("\n") if line.strip()))
        if head and not old_label_re.match(head):
            return head[:120]
        return None

    idx = ss.phase_ids([Path(pdf_path)], pattern="^RS_", include_refs=False, backend="pypdf")
    info = idx.get(doc + ".pdf", {"ids": {}})
    for rid, pagenos in info["ids"].items():
        if not pagenos:
            continue
        pageno = pagenos[0]
        page = pages[pageno - 1] if pageno - 1 < len(pages) else ""
        chunk = ss._record_slice(ss.normalize_layout(page), rid)
        if not chunk:
            continue
        old_h = old_heading(chunk)
        new_rec = ss.parse_record(page, rid)
        new_h = new_rec["heading"]
        if old_h != new_h and (old_h is None) != (new_h is None):
            heading_label.append({"id": rid, "document": doc, "page": pageno, "old_heading": old_h, "new_heading": new_h})

    return {
        "history_continuation": history,
        "traceability": traceability,
        "number_heading": number_heading,
        "heading_label": heading_label,
    }


def _collect_all_categories():
    merged = {key: [] for key in CATEGORIES}
    with ProcessPoolExecutor(max_workers=WORKERS) as ex:
        futures = [ex.submit(_collect_from_pdf, pdf_path) for pdf_path in all_pdf_paths()]
        for fut in as_completed(futures):
            chunk = fut.result()
            for key, rows in chunk.items():
                merged[key].extend(rows)
    return merged


def collect_history_continuation():
    return _collect_all_categories()["history_continuation"]


def collect_traceability():
    return _collect_all_categories()["traceability"]


def collect_number_heading():
    return _collect_all_categories()["number_heading"]


def collect_heading_label():
    return _collect_all_categories()["heading_label"]


def collector_for(category):
    return {
        "history_continuation": collect_history_continuation,
        "traceability": collect_traceability,
        "number_heading": collect_number_heading,
        "heading_label": collect_heading_label,
    }[category]


def dedupe(records):
    seen = {}
    for r in records:
        key = (r["document"], r["id"])
        seen.setdefault(key, r)
    return list(seen.values())


def context_for(doc, pageno, rid, window=350):
    raw = page_text(doc, pageno)
    idx = raw.find(rid)
    if idx == -1:
        idx = raw.upper().find(rid.upper())
    if idx == -1:
        return raw[:window]
    start = max(0, idx - 40)
    return raw[start: idx + window]


def ensure_screenshot(doc, pageno):
    name = "%s_p%d.png" % (doc, pageno)
    dest = os.path.join(ASSET_DIR, name)
    if not os.path.exists(dest):
        pdf = resolve_pdf_path(doc)
        os.makedirs(ASSET_DIR, exist_ok=True)
        prefix = os.path.join(ASSET_DIR, "%s_p%d" % (doc, pageno))
        subprocess.run(["pdftoppm", "-png", "-f", str(pageno), "-l", str(pageno), "-r", "110", pdf, prefix], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for produced in glob.glob(prefix + "-*.png"):
            os.rename(produced, dest)
    return "extraction-report-assets/%s" % name


def original_document_url(document, rid=None):
    branch = next((branch for branch, stem, _ in list(ss.DOCS.values()) + list(ss.RS_DOCS.values())
                   if stem == document), None)
    if branch is None:
        return None
    url = "%s/%s/%s.pdf" % (ss.BASE_URL, branch, document)
    if rid:
        return "%s#nameddest=%s" % (url, rid)
    return url


def document_link(document, rid=None):
    url = original_document_url(document, rid)
    label = '<code>%s</code>' % esc(document)
    if not url:
        return label
    return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(url), label)


def group_by_page(records):
    by_page = {}
    for r in records:
        key = (r["document"], r["page"])
        by_page.setdefault(key, []).append(r)
    return dict(sorted(by_page.items()))


def record_block(r, extra=""):
    ctx = esc(r.get("context", ""))
    return ('<details class="tr-section"><summary><strong><code>%s</code></strong><span>Seite %s</span></summary><div class="tr-table-wrap">%s<pre class="tr-pdf-context">%s</pre></div></details>' % (esc(r["id"]), esc(r["page"]), extra, ctx))


def page_group_html(doc, pageno, records, category):
    img_path = ensure_screenshot(doc, pageno)
    title_link = document_link(doc, records[0]["id"] if records else None)
    if category == "heading_label":
        blocks = "".join(record_block(r, '<p><strong>Vorher (Ueberschrift):</strong> %s<br><strong>Nachher (Ueberschrift):</strong> %s</p>' % ((esc(r["old_heading"]) if r["old_heading"] else "<em>leer</em>"), esc(r["new_heading"]))) for r in records)
    else:
        blocks = "".join(record_block(r) for r in records)
    return ('<div class="tr-page-group"><h4>%s — Seite %d (%d betroffene ID%s)</h4><div class="tr-screenshot"><a href="%s" target="_blank" rel="noopener"><img src="%s" alt="Quellseite %s Seite %d" loading="lazy"></a></div><div class="tr-record-list">%s</div></div>' % (title_link, pageno, len(records), "" if len(records) == 1 else "s", esc(img_path), esc(img_path), esc(doc), pageno, blocks))


def category_section(key, records):
    meta = CATEGORIES[key]
    by_page = group_by_page(records)
    groups_html = "".join(page_group_html(doc, pageno, recs, key) for (doc, pageno), recs in by_page.items())
    unique_ids = len(records)
    unique_pages = len(by_page)
    return ('<details class="tr-section"><summary><strong>%s</strong><span><code>%s</code> — %d ID%s auf %d Seite%s</span></summary><div class="tr-table-wrap"><p><strong>Problem:</strong> %s</p><p><strong>Fix:</strong> %s</p>%s</div></details>' % (esc(meta["title"]), esc(meta["commit"]), unique_ids, "" if unique_ids == 1 else "s", unique_pages, "" if unique_pages == 1 else "n", esc(meta["problem"]), esc(meta["fix"]), groups_html))


def curation_request_payload(r):
    doc = r["document"]
    page = r.get("page")
    screenshot = ensure_screenshot(doc, page) if page else None
    rid = r["id"]
    result_text = r.get("current_result", "")
    if rid.startswith("RS_LT_"):
        basis_id = "RS_LT_00001-group"
    else:
        basis_id = rid
    return {
        "id": rid,
        "flag_id": "curation-%s" % basis_id,
        "kind": "curation_request",
        "text_hash": "curation-request:%s" % basis_id,
        "decision_basis": {
            "finding": {
                "document": doc,
                "page": page,
                "current_result": result_text,
                "simple_explanation": r.get("simple_explanation"),
                "decision_ask": r.get("decision_ask"),
                "screenshot": screenshot,
            },
            "instruction": {
                "goal": "Kurationsentscheidung fuer %s treffen." % rid,
                "forbidden": [
                    "Die Aenderung ungeprueft automatisch uebernehmen",
                    "Den Normtext ohne Beleg umformulieren",
                ],
                "steps": [
                    "Vergleiche Screenshot und aktuelles Extraktionsergebnis.",
                    "Entscheide, welche fachliche Behandlung kuenftig gelten soll.",
                    "Begruende die Entscheidung so, dass daraus spaeter eine konkrete Code- oder Regel-Aenderung abgeleitet werden kann.",
                ],
            },
        },
        "meta": {
            "heading": r.get("decision_ask"),
            "document": doc,
            "page": page,
            "origin": "extraction_report",
            "review_reason": "curation_request",
            "review_status": "pending",
            "text_en": result_text,
            "text_raw": result_text,
        },
    }


def curation_request_html(r):
    rid = esc(r["id"])
    title_link = document_link(r["document"], r.get("id"))
    img_html = ""
    if r.get("page"):
        img = esc(ensure_screenshot(r["document"], r["page"]))
        img_html = '<div class="tr-screenshot"><a href="%s" target="_blank" rel="noopener"><img src="%s" alt="Quellseite %s Seite %s" loading="lazy"></a></div>' % (img, img, esc(r["document"]), esc(r["page"]))

    if r.get("status") == "resolved":
        res = r.get("resolution", {})
        note = (
            '<div class="tr-curation-note tr-curation-resolved">'
            '<p><strong>Status:</strong> Aufgeloest seit Commit <code>%s</code> (%s) — keine Kurator-Entscheidung mehr noetig.</p>'
            '<p>%s</p>'
            '</div>'
            % (esc(res.get("git_rev", "?")), esc(res.get("resolved_at", "?")), esc(res.get("note", "")))
        )
        return (
            '<section class="tr-curation tr-curation-resolved" id="curation-%s">'
            '<h3><span class="tr-curation-badge">Aufgeloest</span> <code>%s</code> — %s</h3>'
            '<div class="tr-curation-grid">'
            '<div>%s</div>'
            '<div class="tr-curation-copy">'
            '<p><span class="label">Originaldokument:</span> %s</p>'
            '<p><span class="label">Was zuvor beobachtet wurde:</span> %s</p>'
            '%s'
            '</div></div></section>'
            % (rid, rid, esc(r["document"]), img_html, title_link, esc(r["current_result"]), note)
        )

    payload = curation_request_payload(r)
    return (
        '<section class="tr-curation" id="curation-%s">'
        '<h3><code>%s</code> — %s</h3>'
        '<div class="tr-curation-grid">'
        '<div>%s</div>'
        '<div class="tr-curation-copy">'
        '<p><span class="label">Originaldokument:</span> %s</p>'
        '<p><span class="label">So verarbeitet das Werkzeug die Daten heute:</span> %s</p>'
        '<p><span class="label">Warum es hier nicht automatisch entscheiden kann:</span> %s</p>'
        '<p><span class="label">Welche Entscheidung wir von der Kuratorin / dem Kurator brauchen:</span> %s</p>'
        '<div class="tr-curation-note">'
        '<p><strong>Was mit deiner Antwort passiert:</strong> Deine Antwort wird im bestehenden Review-Framework gespeichert und als GitHub-Issue-Paket abgegeben. Daraus kann spaeter eine konkrete Aenderung fuer die Extraktions-Pipeline abgeleitet werden.</p>'
        '<p><strong>Wichtig:</strong> Wenn fuer die Umsetzung Textverstehen oder Regelableitung noetig ist, darf ein KI-Agent einen Aenderungsvorschlag aus den zugehoerigen Dokumenten erstellen — aber die Person, die die Extraktionsskripte ausfuehrt, hat immer das letzte Wort und uebernimmt die Aenderung nur nach eigener Pruefung.</p>'
        '</div>'
        '<details class="review-panel" id="review-%s"><summary><span class="review-summary-mark" aria-hidden="true">?</span><span><span data-i18n="review">Validate requirement</span><small>%s</small></span><span class="review-summary-state" aria-hidden="true"></span></summary>'
        '<script type="application/json" class="review-data">%s</script>'
        '<div class="review-panel-body"><div class="review-fields">'
        '<div class="review-form"><label class="review-field review-field-wide"><span data-i18n="why">Rationale</span><textarea class="review-why" required></textarea></label></div><div class="review-actions"><p class="review-identity" data-review-identity hidden></p><div class="review-decision" role="group" aria-label="Decision"><button type="button" class="review-choice review-choice-accept" data-review-outcome="accept"><span class="review-choice-icon" aria-hidden="true">✓</span><span data-i18n="accept">Approve</span></button><button type="button" class="review-choice review-choice-reject" data-review-outcome="reject"><span class="review-choice-icon" aria-hidden="true">×</span><span data-i18n="reject">Reject</span></button></div></div></div></div></details>'
        '</div></div></section>'
        % (rid, rid, esc(r["document"]), img_html, title_link, esc(r["current_result"]), esc(r["simple_explanation"]), esc(r["decision_ask"]), rid, esc(r["decision_ask"]), json.dumps(payload, ensure_ascii=False).replace("</", "<\\/"))
    )


def residual_zeile(r):
    return ("<tr><td><code>%s</code></td><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(r["id"]), esc(r.get("document", "")), esc(r.get("page", "")), esc(r.get("decision_ask", ""))))


def kennzahl(titel, wert, hinweis=""):
    hz = "<small>%s</small>" % esc(hinweis) if hinweis else ""
    return "<article><span>%s</span><strong>%s</strong>%s</article>" % (esc(titel), esc(wert), hz)


VERSIONS_DIR = os.path.join(SRC, "spec", "campaigns", "extraction-report-versions")
VERSION_PAGES_DIR = os.path.join(SRC, "sources", "pages", "reports")


def _git_rev():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


def _git_file_version(relpath):
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%h %cI", "--", relpath],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        if not out:
            return {"path": relpath, "git_rev": None, "checked_in_at": None}
        rev, checked_in_at = out.split(" ", 1)
        return {"path": relpath, "git_rev": rev, "checked_in_at": checked_in_at}
    except Exception:
        return {"path": relpath, "git_rev": None, "checked_in_at": None}


def _script_versions():
    return {
        "spec_scrape": _git_file_version("_src/tools/spec_scrape.py"),
        "extraction_report": _git_file_version("_src/tools/extraction_report.py"),
    }


def _script_delta(prev_scripts, cur_scripts):
    msgs = []
    for key, cur in cur_scripts.items():
        prev = (prev_scripts or {}).get(key) or {}
        if prev.get("git_rev") != cur.get("git_rev"):
            msgs.append("%s: %s → %s" % (cur.get("path"), prev.get("git_rev") or "∅", cur.get("git_rev") or "∅"))
    if not msgs:
        return "Keine Aenderung an den maßgeblichen Extraktionsskripten seit der vorherigen Berichtsversion."
    return "Aenderungen an Extraktionsskripten seit der vorherigen Berichtsversion: " + "; ".join(msgs)


def _load_versions():
    if not os.path.isdir(VERSIONS_DIR):
        return []
    out = []
    for name in sorted(os.listdir(VERSIONS_DIR)):
        if name.endswith(".json"):
            out.append(json.load(open(os.path.join(VERSIONS_DIR, name), encoding="utf-8")))
    return sorted(out, key=lambda v: v["version"])


def _residual_snapshot():
    return {r["id"]: {"status": r.get("status", "open"),
                      "document": r["document"], "page": r.get("page")}
           for r in RESIDUAL}


def _documents_parsed_count():
    """Anzahl der AUTOSAR-Dokumente, aus denen die Spec-DB gespeist wird."""
    return len(ss.DOCS)


def _elements_extracted_count():
    """Anzahl aller Spec-Records (Requirements/Constraints) in der internen DB."""
    n = 0
    for root, _dirs, files in os.walk(ss.RECORDS):
        n += sum(1 for f in files if f.endswith(".json"))
    return n


def record_version(datum, total_ids, total_pages, issues_count=None, curation_open=None):
    """Neue Berichtsversion anlegen und gegen die letzte abgleichen.

    Jede Version haelt den RESIDUAL-Zustand zum Zeitpunkt der Erzeugung fest.
    So lassen sich Kurationsanfragen ueber Laeufe hinweg nachverfolgen: neu
    aufgetreten, weiterhin offen, oder seither aufgeloest — unabhaengig davon,
    ob eine im Browser abgegebene Review-Entscheidung dazu vorliegt.

    Wenn sich gegenueber der letzten Version weder Kennzahlen noch Residual- oder
    Script-Stand geaendert haben, wird keine neue Version angelegt; stattdessen
    wird die vorhandene letzte Version wiederverwendet. So bleiben reine
    Publikationslaeufe (z. B. nachtraegliches HTML-Rendering via generate.py)
    versionsneutral.
    """
    os.makedirs(VERSIONS_DIR, exist_ok=True)
    prev_versions = _load_versions()
    prev = prev_versions[-1] if prev_versions else None
    version = (prev["version"] + 1) if prev else 1
    snapshot = _residual_snapshot()
    scripts = _script_versions()

    diff = {"neu_aufgetreten": [], "weiterhin_offen": [], "neu_aufgeloest": [], "weiterhin_aufgeloest": []}
    prev_snapshot = prev["residual"] if prev else {}
    for rid, cur in snapshot.items():
        was = prev_snapshot.get(rid)
        if was is None:
            diff["neu_aufgetreten"].append(rid) if cur["status"] == "open" else None
        elif was["status"] == "open" and cur["status"] == "open":
            diff["weiterhin_offen"].append(rid)
        elif was["status"] == "open" and cur["status"] == "resolved":
            diff["neu_aufgeloest"].append(rid)
        elif was["status"] == "resolved" and cur["status"] == "resolved":
            diff["weiterhin_aufgeloest"].append(rid)

    if prev and prev.get("total_ids") == total_ids and prev.get("total_pages") == total_pages \
       and prev.get("issues_count") == issues_count and prev.get("curation_open") == curation_open \
       and prev.get("residual") == snapshot and (prev.get("scripts") or {}) == scripts:
        return prev

    entry = {
        "schema": "extraction-report-version@v2",
        "version": version,
        "built_at": datum,
        "git_rev": _git_rev(),
        "total_ids": total_ids,
        "total_pages": total_pages,
        "documents_parsed": _documents_parsed_count(),
        "elements_extracted": _elements_extracted_count(),
        "issues_count": issues_count,
        "curation_open": curation_open,
        "residual": snapshot,
        "diff_vs_previous": diff,
        "previous_version": prev["version"] if prev else None,
        "scripts": scripts,
        "script_delta": _script_delta((prev or {}).get("scripts"), scripts),
        "report_file": "extraction-report-v%04d.html" % version,
        "predecessor_file": ("extraction-report-v%04d.html" % prev["version"]) if prev else None,
    }
    _atomic_write_json(os.path.join(VERSIONS_DIR, "v%04d.json" % version), entry)
    return entry


def _atomic_write_json(path, payload):
    tmp = path + ".tmp-%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, path)


def load_raw_records(input_dir):
    raw = {}
    for key in CATEGORIES:
        path = os.path.join(input_dir, key + ".json")
        raw[key] = json.load(open(path, encoding="utf-8"))
    return raw


def all_pages_from_raw(raw):
    pages = set()
    for records in raw.values():
        for r in records:
            pages.add((r["document"], r["page"]))
    return sorted(pages)


def enrich_records(records):
    for r in records:
        if "context" not in r:
            r["context"] = context_for(r["document"], r["page"], r["id"])
    return records


def _version_row_html(v):
    version_no = int(v.get("version", 0))
    report_file = v.get("report_file") or ("extraction-report-v%04d.html" % version_no)
    predecessor_file = v.get("predecessor_file")
    if not predecessor_file and v.get("previous_version"):
        predecessor_file = "extraction-report-v%04d.html" % int(v["previous_version"])
    pred = ('<a href="%s">Vorgaenger</a>' % esc(predecessor_file)) if predecessor_file else '–'
    scripts = v.get("scripts", {})
    er = scripts.get("extraction_report", {})
    ssv = scripts.get("spec_scrape", {})
    return (
        '<tr data-report-version="%d" data-report-file="%s" data-built-at="%s" data-total-ids="%s" data-total-pages="%s">'
        '<td><a href="%s">v%d</a></td>'
        '<td>%s</td>'
        '<td>%s</td>'
        '<td><code>%s</code> (%s)<br><code>%s</code> (%s)</td>'
        '<td>%s</td>'
        '<td>%s</td>'
        '</tr>'
        % (version_no, esc(report_file), esc(v.get("built_at", "")), esc(v.get("total_ids", "")), esc(v.get("total_pages", "")),
           esc(report_file), version_no, esc(v.get("built_at", "")),
           esc(v.get("git_rev", "")), esc(er.get("git_rev", "")), esc(er.get("checked_in_at", "")),
           esc(ssv.get("git_rev", "")), esc(ssv.get("checked_in_at", "")),
           pred, esc(v.get("script_delta", "")))
    )


def _versions_table_html(versions):
    if not versions:
        return '<p class="dim">Noch keine versionierten Extraktions-Berichte vorhanden.</p>'
    rows = "".join(_version_row_html(v) for v in versions)
    return ('<div class="tr-table-wrap"><table class="tr-table"><thead><tr><th>Bericht</th><th>Ausgefuehrt am</th><th>Repo-Stand</th><th>Extraktionsskripte</th><th>Vorgaenger</th><th>Delta zur vorigen Script-Version</th></tr></thead><tbody>%s</tbody></table></div>'
            % rows)


ARCHIVE_PAGE = os.path.join(SRC, "sources", "pages", "extraction-reports.json")
ARCHIVE_DATA_JS = os.path.join(ROOT, "extraction-reports-data.js")


def write_archive_data_js(versions):
    """Maschinenlesbare Kopie der Berichtshistorie als JS-Datei.

    Wird per <script src> statt fetch() eingebunden, weil fetch() beim
    lokalen Oeffnen der Seite ueber file:// von Browsern aus Sicherheitsgruenden
    blockiert wird (keine CORS-Freigabe fuer lokale Dateien). Ein <script>-Tag
    unterliegt dieser Einschraenkung nicht, daher funktioniert diese Variante
    sowohl lokal als auch auf einem Webserver.
    """
    rows = []
    for v in versions:
        version_no = int(v.get("version", 0))
        rows.append({
            "version": version_no,
            "report_file": v.get("report_file") or ("extraction-report-v%04d.html" % version_no),
            "built_at": v.get("built_at", ""),
            "total_ids": v.get("total_ids"),
            "total_pages": v.get("total_pages"),
            "documents_parsed": v.get("documents_parsed"),
            "elements_extracted": v.get("elements_extracted"),
            "issues_count": v.get("issues_count"),
            "curation_open": v.get("curation_open"),
        })
    payload = "window.EXTRACTION_REPORTS = %s;\n" % json.dumps(rows, ensure_ascii=False)
    tmp = ARCHIVE_DATA_JS + ".tmp-%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(payload)
    os.replace(tmp, ARCHIVE_DATA_JS)


def write_archive_page(versions):
    write_archive_data_js(versions)
    tabelle = _versions_table_html(versions)
    inhalt = "\n".join([
        STIL,
        report_page_header(generator="_src/tools/extraction_report.py", data_source="_src/spec/campaigns/extraction-report-versions/", purpose="Zeigt die Versionen der Extraktionsberichte; Ausführungszeitpunkt, Script-Stand und Delta erklären, was sich zwischen Läufen geändert hat."),
        '<section class="tr-head"><p>Vollstaendige Historie aller Extraktions-Berichtsversionen, jeweils mit Ausfuehrungszeitpunkt, Vorgaenger-Verweis, Extraktionsskript-Version (Git-Hash + Checkin-Datum von <code>extraction_report.py</code> und <code>spec_scrape.py</code>) und Delta zur vorigen Script-Version.</p></section>',
        tabelle,
    ])
    seite = {"file": "extraction-reports.html", "title": "Extraktions-Berichte — Versionshistorie",
            "body_class": None, "nolang": True,
            "nav_html": '<a href="index.html">Start</a> / Extraktions-Berichte',
            "footer": "extracted", "main_lead": "", "main": [{"t": "html", "html": inhalt, "tail": "\n"}]}
    with open(ARCHIVE_PAGE, "w", encoding="utf-8") as f:
        json.dump(seite, f, ensure_ascii=False, indent=1)
        f.write("\n")


def _versions_summary_html():
    versions = list(reversed(_load_versions()))
    write_archive_page(versions)
    return ('<style>.tr-mini-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:.6rem;margin:.6rem 0}'
            '.tr-mini-kennzahl{border:1px solid #d9dce3;border-radius:10px;padding:.6rem .7rem;background:#fff}'
            '.tr-mini-kennzahl strong{display:block;font-size:1.3rem;font-variant-numeric:tabular-nums}'
            '.tr-mini-kennzahl span{display:block;color:#596274;font-size:.85rem}</style>'
            '<div class="tr-home-brief" data-extraction-quality>'
            '<p class="dim">Extraktions-Qualitaet wird geladen …</p>'
            '<p><a href="extraction-reports.html">Berichtsverzeichnis öffnen</a></p>'
            '</div>'
            '<script src="extraction-reports-data.js"></script>'
            "<script>(function(){var host=document.querySelector('[data-extraction-quality]');if(!host)return;var open=function(html){host.innerHTML=html;};var val=function(x){return x!=null?x:'?';};try{var rows=window.EXTRACTION_REPORTS||[];var row=rows[0];if(!row){open('<p class=\"dim\">Keine Extraktions-Berichte gefunden.</p><p><a href=\"extraction-reports.html\">Berichtsverzeichnis öffnen</a></p>');return;}var href=row.report_file||'extraction-reports.html';var v=row.version||'?';var kennzahl=function(label,wert){return '<div class=\"tr-mini-kennzahl\"><strong>'+val(wert)+'</strong><span>'+label+'</span></div>';};var grid='<div class=\"tr-mini-grid\">'+kennzahl('Dokumente geparst',row.documents_parsed)+kennzahl('Elemente extrahiert',row.elements_extracted)+kennzahl('Fehlerklassen',row.issues_count)+kennzahl('Offene Kurationsanfragen',row.curation_open)+'</div>';open('<p>Neuester Extraktions-Bericht: <a href=\"'+href+'\">v'+v+' öffnen</a>.</p>'+grid);}catch(e){open('<p class=\"dim\">Extraktions-Qualitaet derzeit nicht verfügbar. <a href=\"extraction-reports.html\">Berichtsverzeichnis öffnen</a>.</p>');}})();</script>")


def write_version_page(page, version_entry):
    """Create a versioned page model once; preserve existing history by default."""
    os.makedirs(VERSION_PAGES_DIR, exist_ok=True)
    path = os.path.join(VERSION_PAGES_DIR, "extraction-report-v%04d.json" % version_entry["version"])
    if os.path.exists(path):
        return False
    _atomic_write_json(path, page)
    return True


def _archive_stub_page(v):
    version_no = int(v.get("version", 0))
    predecessor_file = v.get("predecessor_file")
    if not predecessor_file and v.get("previous_version"):
        predecessor_file = "extraction-report-v%04d.html" % int(v["previous_version"])
    scripts = v.get("scripts", {})
    er = scripts.get("extraction_report", {})
    ssv = scripts.get("spec_scrape", {})
    links = ['<p><a href="extraction-report.html">Neueste Live-Version öffnen</a></p>']
    if predecessor_file:
        links.append('<p><a href="%s">Vorgaenger dieser Berichtsversion</a></p>' % esc(predecessor_file))
    body = "\n".join([
        STIL,
        '<section class="tr-head"><p>Archivierte Extraktions-Berichtsversion v%d.</p><p class="tr-meta"><span>Ausgefuehrt: <strong>%s</strong></span><span>Repo-Stand: <strong>%s</strong></span></p><p class="tr-version-note">%s</p></section>' % (version_no, esc(v.get("built_at", "")), esc(v.get("git_rev", "")), esc(v.get("script_delta", ""))),
        '<div class="tr-table-wrap"><table class="tr-table"><tbody>'
        '<tr><th>Berichtsdatei</th><td><code>%s</code></td></tr>'
        '<tr><th>Extraction report script</th><td><code>%s</code> (%s)</td></tr>'
        '<tr><th>Spec scrape script</th><td><code>%s</code> (%s)</td></tr>'
        '<tr><th>Vorgaenger</th><td>%s</td></tr>'
        '</tbody></table></div>' % (
            esc(v.get("report_file") or ("extraction-report-v%04d.html" % version_no)),
            esc(er.get("git_rev", "")), esc(er.get("checked_in_at", "")),
            esc(ssv.get("git_rev", "")), esc(ssv.get("checked_in_at", "")),
            ('<a href="%s">%s</a>' % (esc(predecessor_file), esc(predecessor_file))) if predecessor_file else '–'),
        *links,
    ])
    return {"file": v.get("report_file") or ("extraction-report-v%04d.html" % version_no),
            "title": "Extraktions-Bericht Archiv v%d — AUTOSAR R25-11" % version_no,
            "body_class": None, "nolang": True,
            "nav_html": '<a href="index.html">Start</a> / <a href="extraction-report.html">Extraktions-Bericht</a> / Archiv v%d' % version_no,
            "footer": "extracted", "main_lead": "",
            "main": [{"t": "html", "html": body, "tail": "\n"}]}


def ensure_version_pages():
    os.makedirs(VERSION_PAGES_DIR, exist_ok=True)
    for v in _load_versions():
        path = os.path.join(VERSION_PAGES_DIR, "extraction-report-v%04d.json" % int(v.get("version", 0)))
        if not os.path.exists(path):
            _atomic_write_json(path, _archive_stub_page(v))


def baue(datum, gesamt_zaehlung):
    sections_html = "".join(category_section(k, v) for k, v in gesamt_zaehlung["records"].items())
    offene = [r for r in RESIDUAL if r.get("status", "open") != "resolved"]
    aufgeloeste = [r for r in RESIDUAL if r.get("status") == "resolved"]
    curation_html = "".join(curation_request_html(r) for r in offene)
    resolved_html = "".join(curation_request_html(r) for r in aufgeloeste)
    residual_html = ('<table class="tr-table"><thead><tr><th>Record-ID</th><th>Dokument</th><th>Seite</th><th>Entscheidungsfrage</th></tr></thead><tbody>%s</tbody></table>' % "".join(residual_zeile(r) for r in offene))
    total_ids = sum(len(v) for v in gesamt_zaehlung["records"].values())
    total_pages = len(set((r["document"], r["page"]) for v in gesamt_zaehlung["records"].values() for r in v))

    version_entry = record_version(datum, total_ids, total_pages,
                                    issues_count=len(CATEGORIES), curation_open=len(offene))
    diff = version_entry["diff_vs_previous"]
    version_note = (
        '<p class="tr-version-note">Berichtsversion <strong>v%d</strong>%s'
        % (version_entry["version"],
           " (vorherige: <a href=\"%s\">v%d</a>)" % (esc(version_entry["predecessor_file"]), version_entry["previous_version"]) if version_entry["previous_version"] else " (erste Version)"))
    if version_entry["previous_version"]:
        teile = []
        if diff["neu_aufgeloest"]:
            teile.append("seit v%d aufgeloest: %s" % (version_entry["previous_version"], ", ".join(diff["neu_aufgeloest"])))
        if diff["neu_aufgetreten"]:
            teile.append("seit v%d neu aufgetreten: %s" % (version_entry["previous_version"], ", ".join(diff["neu_aufgetreten"])))
        if teile:
            version_note += " — " + "; ".join(esc(t) for t in teile)
    version_note += '</p>'
    script_meta = version_entry["scripts"]
    script_note = ('<p class="tr-version-note">Script-Stand: <code>%s</code> (%s), <code>%s</code> (%s). %s</p>'
                   % (esc(script_meta["extraction_report"].get("git_rev", "")), esc(script_meta["extraction_report"].get("checked_in_at", "")),
                      esc(script_meta["spec_scrape"].get("git_rev", "")), esc(script_meta["spec_scrape"].get("checked_in_at", "")),
                      esc(version_entry.get("script_delta", ""))))

    karten = "".join([
        kennzahl("Behobene Fehlerklassen", len(CATEGORIES), "seit der letzten Berichtsaenderung dokumentiert"),
        kennzahl("Betroffene Record-IDs gesamt", total_ids, "vollstaendig unten aufgelistet"),
        kennzahl("Betroffene Quellseiten", total_pages, "je mit Seiten-Screenshot"),
        kennzahl("Offene Kurationsanfragen", len(offene), "oben priorisiert, mit Review-Widget"),
    ])
    inhalt = "\n".join([
        STIL,
        '<section class="tr-head"><p>Dieser Extraktions-Bericht beschreibt die Aenderungen an der Pipeline seit der letzten Berichtsaenderung. Oben stehen die <strong>wichtigsten offenen Kurationsanfragen</strong>; darunter folgen die bereits umgesetzten Fixes, standardmaessig eingeklappt, jeweils mit Screenshot und aktuellem Extraktionsergebnis.</p><p class="tr-meta"><span>Stand: <strong>%s</strong></span><span>Dokumente: <strong>18</strong></span><span>Backends: <strong>pypdf, builtin</strong></span></p>%s%s</section>' % (esc(datum), version_note, script_note),
        '<h2 class="sect">Kennzahlen</h2><div class="tr-grid">%s</div>' % karten,
        '<h2 class="sect">Kurationsanfragen — bitte zuerst entscheiden</h2>',
        '<p class="dim">Jeder Fall zeigt den heutigen Extraktionsstand, eine kompakte Screenshot-Vorschau der Quelle und in einfacher Sprache, welche Entscheidung benoetigt wird. Deine Antwort landet im vorhandenen Review-Framework und kann spaeter aus dem GitHub-Issue in einen umsetzbaren Aenderungsvorschlag fuer die Pipeline ueberfuehrt werden.</p>',
        curation_html if curation_html else '<p class="dim">Keine offenen Kurationsanfragen.</p>',
        '<details class="tr-section"><summary><strong>Alle offenen Kurationsfragen als Liste</strong><span>%d Eintraege</span></summary><div class="tr-table-wrap">%s</div></details>' % (len(offene), residual_html) if offene else "",
        ('<details class="tr-section"><summary><strong>Aufgeloeste Kurationsanfragen (seit fruehreren Versionen)</strong><span>%d Eintraege</span></summary>%s</details>'
         % (len(aufgeloeste), resolved_html)) if aufgeloeste else "",
        '<h2 class="sect">Fixes seit der letzten Aenderung — vollstaendige Extraktionsergebnisse</h2>%s' % sections_html,
        '<p class="dim">Erzeugt mit <code>_src/tools/extraction_report.py</code> direkt aus dem versionierten PDF-Cache. Antworten auf Kurationsanfragen werden ueber das bestehende Review-Framework als Paket gespeichert; wenn zur Umsetzung KI noetig ist, darf sie nur einen Vorschlag aus den zugehoerigen Dokumenten ableiten. Die Person, die die Extraktionsskripte ausfuehrt, hat immer das letzte Wort und uebernimmt Aenderungen erst nach eigener Pruefung.</p>',
    ])
    latest_file = version_entry["report_file"]
    live_page = {"file": latest_file, "title": "Extraktions-Bericht %s — AUTOSAR R25-11 (v%d)" % (datum[:10], version_entry["version"]), "body_class": None, "nolang": True, "nav_html": '<a href="index.html">Start</a> / <a href="extraction-reports.html">Extraktions-Berichte</a> / v%d' % version_entry["version"], "footer": "extracted", "main_lead": "", "main": [{"t": "html", "html": inhalt, "tail": "\n"}]}
    write_version_page(dict(live_page), version_entry)
    return live_page


def verlinke_startseite(datum):
    idx = json.load(open(INDEX, encoding="utf-8"))
    block = {"t": "html", "nolang": True, "html": '<aside class="tr-home-link"><h2 class="sect">Extraktions-Qualitaet</h2><p>Aktueller Status aus dem <a href="extraction-reports.html">Berichtsverzeichnis</a>:</p>%s</aside>' % _versions_summary_html(), "tail": "\n"}
    idx["main"] = [b for b in idx["main"] if "tr-home-link" not in b.get("html", "")]
    pos = 3 if any("traceability.html" in b.get("html", "") for b in idx["main"]) else 2
    idx["main"].insert(pos, block)
    with open(INDEX, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=1)
        f.write("\n")


def cmd_collect_one(category, output_path):
    records = collector_for(category)()
    if category != "heading_label":
        records = dedupe(records)
    records = enrich_records(records)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("%s: %d records" % (category, len(records)))


def cmd_render_shot(doc, pageno):
    path = ensure_screenshot(doc, int(pageno))
    print(path)


def _render_one_screenshot(args):
    doc, pageno = args
    return ensure_screenshot(doc, pageno)


def cmd_render_shots(inputs):
    pages = set()
    for inp in inputs:
        records = json.load(open(inp, encoding="utf-8"))
        for r in records:
            pages.add((r["document"], int(r["page"])))
    for r in RESIDUAL:
        if r.get("page"):
            pages.add((r["document"], int(r["page"])))
    ordered = sorted(pages)
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = [ex.submit(_render_one_screenshot, item) for item in ordered]
        for fut in as_completed(futures):
            fut.result()
    print("screenshots: %d" % len(ordered))


def cmd_assemble(input_dir):
    import datetime
    raw = load_raw_records(input_dir)
    datum = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    seite = baue(datum, {"records": raw})
    # PAGE is the current working model, not the historical archive. ``baue``
    # already created the missing version model once; keep this current copy
    # and the overview/index aligned with that newest version.
    _atomic_write_json(PAGE, seite)
    ensure_version_pages()
    verlinke_startseite(datum)
    total = sum(len(v) for v in raw.values())
    print("Extraktions-Bericht: Stand %s, %d Abweichungen ueber %d Fehlerklassen" % (datum, total, len(CATEGORIES)))


def cmd_build():
    tmp = os.path.join(ROOT, "output", "extraction-report-work")
    os.makedirs(tmp, exist_ok=True)
    collected = _collect_all_categories()
    for key in CATEGORIES:
        path = os.path.join(tmp, key + ".json")
        records = dedupe(collected[key])
        records = enrich_records(records)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print("%s: %d records" % (key, len(records)))
    cmd_render_shots([os.path.join(tmp, key + ".json") for key in CATEGORIES])
    cmd_assemble(tmp)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("collect-one")
    p.add_argument("category", choices=sorted(CATEGORIES))
    p.add_argument("output")

    p = sub.add_parser("render-shot")
    p.add_argument("document")
    p.add_argument("page", type=int)

    p = sub.add_parser("render-shots")
    p.add_argument("inputs", nargs="+")

    p = sub.add_parser("assemble")
    p.add_argument("input_dir")

    sub.add_parser("build")
    ns = ap.parse_args(argv)

    if ns.cmd in (None, "build"):
        cmd_build()
    elif ns.cmd == "collect-one":
        cmd_collect_one(ns.category, ns.output)
    elif ns.cmd == "render-shot":
        cmd_render_shot(ns.document, ns.page)
    elif ns.cmd == "render-shots":
        cmd_render_shots(ns.inputs)
    elif ns.cmd == "assemble":
        cmd_assemble(ns.input_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
