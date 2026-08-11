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
from pathlib import Path

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
     "current_result": "Die Extraktion legt aktuell einen Record unter der Schreibweise "
                        "„RS_DIAG_04005“ an (Grossbuchstaben, wie im Index-Muster erwartet).",
     "simple_explanation": "Auf dieser Seite steht die ID im Fliesstext einmal anders geschrieben "
                            "als „RS_Diag_04006“ (gemischte Gross-/Kleinschreibung). Das Werkzeug kann "
                            "nicht automatisch entscheiden, welche Schreibweise die eigentliche, "
                            "gueltige Kennung des Requirements ist — das steht so im Original-PDF.",
     "decision_ask": "Soll die Kennung als „RS_DIAG_04005“ (aktuelle Extraktion) oder als "
                      "„RS_Diag_04006“ (abweichende Schreibweise im Fliesstext) gefuehrt werden?"},
    {"id": "RS_SAF_21101", "document": "AUTOSAR_AP_RS_PlatformHealthManagement", "page": 9,
     "current_result": "Kein Record wird angelegt; die Extraktion verwirft die ID, weil auf dieser "
                        "und der Folgeseite keine zugehoerige Definition (Ueberschrift + Beschreibung) "
                        "gefunden wird.",
     "simple_explanation": "Die ID taucht hier nur als Verweis in eckigen Klammern auf, z. B. "
                            "„[RS_SAF_21101]“ — wie eine Fussnote, die auf ein Requirement an anderer "
                            "Stelle zeigt. Es gibt an dieser Stelle keinen eigenen Beschreibungstext.",
     "decision_ask": "Ist es richtig, diese reine Zitierstelle zu ignorieren, oder soll trotzdem ein "
                      "leerer Platzhalter-Record angelegt werden, damit die ID nicht ganz fehlt?"},
    {"id": "RS_LT_00001", "document": "AUTOSAR_FO_RS_LogAndTrace", "page": 41,
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
</style>"""


def esc(v):
    return html.escape(str(v), quote=True)


def all_pdf_paths():
    return sorted(glob.glob(os.path.join(PDF_DIR, "AUTOSAR_*_RS_*.pdf")))


def page_text(doc_stem, pageno):
    f = os.path.join(PDF_DIR, doc_stem + ".pdf")
    pages = ss.pdf_pages(Path(f), "pypdf")
    return pages[pageno - 1] if pageno - 1 < len(pages) else ""


def collect_history_continuation():
    out = []
    for f in all_pdf_paths():
        doc = Path(f).stem
        pages = [ss.strip_noise(x) for x in ss.pdf_pages(Path(f), "pypdf")]
        for i, t in enumerate(pages):
            if ss.HISTORY_CONTINUATION_RE.search(t):
                for m in ss.DEF_RE.finditer(t):
                    out.append({"id": m.group(1).upper(), "document": doc, "page": i + 1})
    return out


def collect_traceability():
    out = []
    for f in all_pdf_paths():
        doc = Path(f).stem
        pages = [ss.strip_noise(x) for x in ss.pdf_pages(Path(f), "pypdf")]
        for i, t in enumerate(pages):
            if ss.TRACEABILITY_HEADING_RE.search(t):
                for m in ss.DEF_RE.finditer(t):
                    out.append({"id": m.group(1).upper(), "document": doc, "page": i + 1})
    return out


def collect_number_heading():
    out = []
    for f in all_pdf_paths():
        doc = Path(f).stem
        pages = [ss.strip_noise(x) for x in ss.pdf_pages(Path(f), "pypdf")]
        for i, t in enumerate(pages):
            if ss.HISTORY_NUMBER_HEADING_CONTINUATION_RE.search(t) and ss.HISTORY_TABLE_CAPTION_RE.search(t):
                for m in ss.DEF_RE.finditer(t):
                    out.append({"id": m.group(1).upper(), "document": doc, "page": i + 1})
    return out


def collect_heading_label():
    old_label_re = re.compile(r"^(%s)\s*:?\s*(.*)$" % "|".join(re.escape(x) for x in ss.LABELS))

    def old_heading(chunk):
        head_part = re.split(r"(?:⌈|(?:^|\n)\s*(?:Status|Upstream requirements?|Kind)\s*:?)", chunk.lstrip("\n"), maxsplit=1)[0]
        head = ss._clean_value(" ".join(line.strip() for line in head_part.split("\n") if line.strip()))
        if head and not old_label_re.match(head):
            return head[:120]
        return None

    out = []
    for f in all_pdf_paths():
        doc = Path(f).stem
        idx = ss.phase_ids([Path(f)], pattern="^RS_", include_refs=False, backend="pypdf")
        info = idx[doc + ".pdf"]
        pages = [ss.strip_noise(x) for x in ss.pdf_pages(Path(f), "pypdf")]
        for rid, pagenos in info["ids"].items():
            if not pagenos:
                continue
            pageno = pagenos[0]
            chunk = ss._record_slice(ss.normalize_layout(pages[pageno - 1]), rid)
            if not chunk:
                continue
            old_h = old_heading(chunk)
            new_rec = ss.parse_record(pages[pageno - 1], rid)
            new_h = new_rec["heading"]
            if old_h != new_h and (old_h is None) != (new_h is None):
                out.append({"id": rid, "document": doc, "page": pageno, "old_heading": old_h, "new_heading": new_h})
    return out


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
        pdf = os.path.join(PDF_DIR, doc + ".pdf")
        os.makedirs(ASSET_DIR, exist_ok=True)
        prefix = os.path.join(ASSET_DIR, "%s_p%d" % (doc, pageno))
        subprocess.run(["pdftoppm", "-png", "-f", str(pageno), "-l", str(pageno), "-r", "110", pdf, prefix], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for produced in glob.glob(prefix + "-*.png"):
            os.rename(produced, dest)
    return "extraction-report-assets/%s" % name


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
    if category == "heading_label":
        blocks = "".join(record_block(r, '<p><strong>Vorher (Ueberschrift):</strong> %s<br><strong>Nachher (Ueberschrift):</strong> %s</p>' % ((esc(r["old_heading"]) if r["old_heading"] else "<em>leer</em>"), esc(r["new_heading"]))) for r in records)
    else:
        blocks = "".join(record_block(r) for r in records)
    return ('<div class="tr-page-group"><h4><code>%s</code> — Seite %d (%d betroffene ID%s)</h4><div class="tr-screenshot"><a href="%s" target="_blank" rel="noopener"><img src="%s" alt="Quellseite %s Seite %d" loading="lazy"></a></div><div class="tr-record-list">%s</div></div>' % (esc(doc), pageno, len(records), "" if len(records) == 1 else "s", esc(img_path), esc(img_path), esc(doc), pageno, blocks))


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
    payload = curation_request_payload(r)
    rid = esc(r["id"])
    img_html = ""
    if r.get("page"):
        img = esc(ensure_screenshot(r["document"], r["page"]))
        img_html = '<div class="tr-screenshot"><a href="%s" target="_blank" rel="noopener"><img src="%s" alt="Quellseite %s Seite %s" loading="lazy"></a></div>' % (img, img, esc(r["document"]), esc(r["page"]))
    return (
        '<section class="tr-curation" id="curation-%s">'
        '<h3><code>%s</code> — %s</h3>'
        '<div class="tr-curation-grid">'
        '<div>%s</div>'
        '<div class="tr-curation-copy">'
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
        % (rid, rid, esc(r["document"]), img_html, esc(r["current_result"]), esc(r["simple_explanation"]), esc(r["decision_ask"]), rid, esc(r["decision_ask"]), json.dumps(payload, ensure_ascii=False).replace("</", "<\\/"))
    )


def residual_zeile(r):
    return ("<tr><td><code>%s</code></td><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(r["id"]), esc(r.get("document", "")), esc(r.get("page", "")), esc(r.get("decision_ask", ""))))


def kennzahl(titel, wert, hinweis=""):
    hz = "<small>%s</small>" % esc(hinweis) if hinweis else ""
    return "<article><span>%s</span><strong>%s</strong>%s</article>" % (esc(titel), esc(wert), hz)


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


def baue(datum, gesamt_zaehlung):
    sections_html = "".join(category_section(k, v) for k, v in gesamt_zaehlung["records"].items())
    curation_html = "".join(curation_request_html(r) for r in RESIDUAL)
    residual_html = ('<table class="tr-table"><thead><tr><th>Record-ID</th><th>Dokument</th><th>Seite</th><th>Entscheidungsfrage</th></tr></thead><tbody>%s</tbody></table>' % "".join(residual_zeile(r) for r in RESIDUAL))
    total_ids = sum(len(v) for v in gesamt_zaehlung["records"].values())
    total_pages = len(set((r["document"], r["page"]) for v in gesamt_zaehlung["records"].values() for r in v))
    karten = "".join([
        kennzahl("Behobene Fehlerklassen", len(CATEGORIES), "seit der letzten Berichtsaenderung dokumentiert"),
        kennzahl("Betroffene Record-IDs gesamt", total_ids, "vollstaendig unten aufgelistet"),
        kennzahl("Betroffene Quellseiten", total_pages, "je mit Seiten-Screenshot"),
        kennzahl("Offene Kurationsanfragen", len(RESIDUAL), "oben priorisiert, mit Review-Widget"),
    ])
    inhalt = "\n".join([
        STIL,
        '<section class="tr-head"><p>Dieser Extraktions-Bericht beschreibt die Aenderungen an der Pipeline seit der letzten Berichtsaenderung. Oben stehen die <strong>wichtigsten offenen Kurationsanfragen</strong>; darunter folgen die bereits umgesetzten Fixes, standardmaessig eingeklappt, jeweils mit Screenshot und aktuellem Extraktionsergebnis.</p><p class="tr-meta"><span>Stand: <strong>%s</strong></span><span>Dokumente: <strong>18</strong></span><span>Backends: <strong>pypdf, builtin</strong></span></p></section>' % esc(datum),
        '<h2 class="sect">Kennzahlen</h2><div class="tr-grid">%s</div>' % karten,
        '<h2 class="sect">Kurationsanfragen — bitte zuerst entscheiden</h2>',
        '<p class="dim">Jeder Fall zeigt den heutigen Extraktionsstand, eine kompakte Screenshot-Vorschau der Quelle und in einfacher Sprache, welche Entscheidung benoetigt wird. Deine Antwort landet im vorhandenen Review-Framework und kann spaeter aus dem GitHub-Issue in einen umsetzbaren Aenderungsvorschlag fuer die Pipeline ueberfuehrt werden.</p>',
        curation_html,
        '<details class="tr-section"><summary><strong>Alle offenen Kurationsfragen als Liste</strong><span>%d Eintraege</span></summary><div class="tr-table-wrap">%s</div></details>' % (len(RESIDUAL), residual_html),
        '<h2 class="sect">Fixes seit der letzten Aenderung — vollstaendige Extraktionsergebnisse</h2>%s' % sections_html,
        '<p class="dim">Erzeugt mit <code>_src/tools/extraction_report.py</code> direkt aus dem versionierten PDF-Cache. Antworten auf Kurationsanfragen werden ueber das bestehende Review-Framework als Paket gespeichert; wenn zur Umsetzung KI noetig ist, darf sie nur einen Vorschlag aus den zugehoerigen Dokumenten ableiten. Die Person, die die Extraktionsskripte ausfuehrt, hat immer das letzte Wort und uebernimmt Aenderungen erst nach eigener Pruefung.</p>',
    ])
    return {"file": "extraction-report.html", "title": "Extraktions-Bericht %s — AUTOSAR R25-11" % datum[:10], "body_class": None, "nolang": True, "nav_html": '<a href="index.html">Start</a> / Extraktions-Bericht', "footer": "extracted", "main_lead": "", "main": [{"t": "html", "html": inhalt, "tail": "\n"}]}


def verlinke_startseite(datum):
    idx = json.load(open(INDEX, encoding="utf-8"))
    block = {"t": "html", "nolang": True, "html": '<aside class="tr-home-link"><h2 class="sect">Extraktions-Qualitaet</h2><p>Vollstaendige Abweichungsliste (Volltext + Seiten-Screenshot) heute behobener Extraktions-Fehlerklassen, Stand %s: <a href="extraction-report.html">Extraktions-Bericht öffnen</a>.</p></aside>' % html.escape(datum), "tail": "\n"}
    idx["main"] = [b for b in idx["main"] if "extraction-report.html" not in b.get("html", "")]
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


def cmd_render_shots(inputs):
    pages = set()
    for inp in inputs:
        records = json.load(open(inp, encoding="utf-8"))
        for r in records:
            pages.add((r["document"], int(r["page"])))
    for r in RESIDUAL:
        if r.get("page"):
            pages.add((r["document"], int(r["page"])))
    for doc, pageno in sorted(pages):
        ensure_screenshot(doc, pageno)
    print("screenshots: %d" % len(pages))


def cmd_assemble(input_dir):
    import datetime
    raw = load_raw_records(input_dir)
    datum = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    seite = baue(datum, {"records": raw})
    with open(PAGE, "w", encoding="utf-8") as f:
        json.dump(seite, f, ensure_ascii=False, indent=1)
        f.write("\n")
    verlinke_startseite(datum)
    total = sum(len(v) for v in raw.values())
    print("Extraktions-Bericht: Stand %s, %d Abweichungen ueber %d Fehlerklassen" % (datum, total, len(CATEGORIES)))


def cmd_build():
    tmp = os.path.join(ROOT, "output", "extraction-report-work")
    os.makedirs(tmp, exist_ok=True)
    for key in CATEGORIES:
        cmd_collect_one(key, os.path.join(tmp, key + ".json"))
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
