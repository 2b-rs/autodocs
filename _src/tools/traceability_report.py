#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""traceability_report.py — Traceability-Bericht aus einem Scraping-Lauf bauen.

Liest das Ergebnis eines ``spec_scrape.py crosscheck --json``-Laufs (JSON) samt
zugehoerigem Lauf-Log und erzeugt daraus das Seitenmodell
``_src/sources/pages/traceability.html``. Gefundene Record-IDs werden, soweit
sie im deutschen HTML-Baum vorkommen, auf ihre Dokumentationsseite verlinkt.
Der Bericht traegt das Datum des Scraping-Laufs.

    python3 _src/tools/traceability_report.py \\
        --json output/spec-validation/R25-11/crosscheck-current.json \\
        --log  output/spec-validation/R25-11/crosscheck-current.log

Der Bericht ist bewusst nur deutsch (Seitenmodell-Flag ``nolang``); er wird
nicht in die Sprachbaeume uebersetzt.
"""
import argparse, datetime, glob, html, json, os, re, sys

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(SRC)
PAGE = os.path.join(SRC, "sources", "pages", "traceability.json")
INDEX = os.path.join(SRC, "sources", "pages", "index.json")
ID_ATTR = re.compile(r'id="((?:AP_)?(?:SWS|RS|PRS|TPS)_[A-Z][A-Z0-9]*_\d{4,5})"')


def record_index():
    """Record-ID -> Dokumentationsseite (deutscher Baum, relativ zur Wurzel)."""
    treffer = {}
    seiten = glob.glob(os.path.join(ROOT, "*.html"))
    for d in ("classes", "namespaces", "modules", "services"):
        seiten += glob.glob(os.path.join(ROOT, d, "*.html"))
    for p in sorted(seiten):
        rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
        if rel == "traceability.html":
            continue
        with open(p, encoding="utf-8") as f:
            for rid in ID_ATTR.findall(f.read()):
                treffer.setdefault(rid, "%s#%s" % (rel, rid))
    return treffer


def lauf_datum(logpfad, jsonpfad):
    """Datum des Scraping-Laufs: aus dem Log, sonst Mtime des JSON."""
    if logpfad and os.path.exists(logpfad):
        txt = open(logpfad, encoding="utf-8", errors="replace").read()
        m = re.findall(r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})", txt)
        if m:
            return m[-1].replace("T", " ")
    ts = os.path.getmtime(jsonpfad)
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def esc(v):
    return html.escape(str(v), quote=True)


def anzahl(v):
    return len(v) if isinstance(v, list) else int(v)


def id_link(rid, idx):
    ziel = idx.get(rid)
    if ziel:
        return '<a href="%s"><code>%s</code></a>' % (esc(ziel), esc(rid))
    return '<code class="nolink" title="keine Dokumentationsseite">%s</code>' % esc(rid)


def abschnitt(titel, n, inhalt, hinweis=""):
    kopf = '<p class="dim">%s</p>' % esc(hinweis) if hinweis else ""
    return ('<details class="tr-section"><summary><strong>%s</strong>'
            '<span>%s</span></summary>%s<div class="tr-table-wrap">%s</div>'
            '</details>' % (esc(titel), format(n, ",").replace(",", "."), kopf, inhalt))


def id_tabelle(werte, idx):
    zeilen = "".join("<tr><td>%s</td></tr>" % id_link(r, idx) for r in werte)
    return ('<table class="tr-table"><thead><tr><th>Record-ID</th></tr></thead>'
            '<tbody>%s</tbody></table>' % zeilen)


def diff_tabelle(werte, idx, feldspalte=True):
    if feldspalte:
        kopf = "<tr><th>Record-ID</th><th>Feld</th><th>Standarddokument</th><th>Datenbank</th></tr>"
        zeilen = "".join(
            "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (id_link(i["id"], idx), esc(i.get("field", "")),
               esc(i.get("pdf", "")), esc(i.get("db", ""))) for i in werte)
    else:
        kopf = "<tr><th>Record-ID</th><th>Standarddokument</th><th>Datenbank</th></tr>"
        zeilen = "".join(
            "<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (id_link(i["id"], idx), esc(i.get("pdf", "")), esc(i.get("db", "")))
            for i in werte)
    return ('<table class="tr-table"><thead>%s</thead><tbody>%s</tbody></table>'
            % (kopf, zeilen))


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
.tr-table-wrap{overflow:auto;max-height:42rem}
.tr-table{border-collapse:collapse;width:100%;font-size:.9rem}
.tr-table th{position:sticky;top:0;background:#eef1f6;text-align:left;z-index:1}
.tr-table th,.tr-table td{padding:.5rem .7rem;border-bottom:1px solid #e4e7ec;vertical-align:top}
.tr-table tbody tr:nth-child(even){background:#fafbfc}
.tr-table td:nth-last-child(-n+2){max-width:32rem;overflow-wrap:anywhere}
.tr-table code.nolink{color:#6b7280}
.tr-docs{columns:2;column-gap:2rem}@media(max-width:700px){.tr-docs{columns:1}}
</style>"""


def baue(daten, datum, idx, quelle):
    backends = daten["backends"]
    primaer = "builtin" if "builtin" in backends else backends[0]
    x = daten["database"][primaer]
    kennzahlen = [
        ("PDF-Records", daten["record_counts"][primaer], "aus den Standarddokumenten extrahiert"),
        ("Verglichen", anzahl(x["checked"]), "Records mit Gegenstück in DB und PDF"),
        ("Nur im PDF", anzahl(x["only_in_pdf"]), "nicht in der Spec-Datenbank"),
        ("Nur in der DB", anzahl(x["only_in_db"]), "ohne Gegenstück im PDF"),
        ("Feldabweichungen", anzahl(x["diffs"]), "abweichende Feldwerte"),
        ("Namespace-Abweichungen", anzahl(x["namespace_diffs"]), "abweichender Namespace"),
        ("Leere Extraktion", anzahl(x["empty_extraction"]), "ID erkannt, keine Felder"),
    ]
    karten = "".join(
        "<article><span>%s</span><strong>%s</strong><small>%s</small></article>"
        % (esc(k), format(v, ",").replace(",", "."), esc(h)) for k, v, h in kennzahlen)
    backend_zeilen = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (esc(b), daten["record_counts"][b], anzahl(daten["database"][b]["checked"]),
           anzahl(daten["database"][b]["diffs"]),
           anzahl(daten["database"][b]["namespace_diffs"]),
           anzahl(daten["database"][b]["empty_extraction"])) for b in backends)
    docs = "".join("<li><code>%s</code></li>" % esc(v) for v in daten["documents"])
    verlinkt = sum(1 for r in x["only_in_db"] if r in idx)
    inhalt = "".join([
        STIL,
        "<h1>Traceability-Bericht — Spec-Datenbank gegen AUTOSAR %s</h1>" % esc(daten["release"]),
        '<section class="tr-head"><p>Abgleich der lokalen Spezifikations-Records mit den '
        'gecachten normativen AUTOSAR-Standarddokumenten. Abweichungen sind Prüfhinweise: '
        'Artefakte der PDF-Textextraktion können wie Datenfehler aussehen. Record-IDs sind, '
        'soweit dokumentiert, mit ihrer Referenzseite verlinkt.</p>'
        '<p class="tr-meta"><span>Scraping-Lauf: <strong>%s</strong></span>'
        '<span>Release: <strong>%s</strong></span>'
        '<span>Primäransicht: <strong>%s</strong></span>'
        '<span>Dokumente: <strong>%d</strong></span>'
        '<span>Backend-Abweichungen: <strong>%s</strong></span>'
        '<span>Verlinkte DB-Records: <strong>%d</strong></span></p></section>'
        % (esc(datum), esc(daten["release"]), esc(primaer), len(daten["documents"]),
           format(len(daten.get("backend_deviations", [])), ",").replace(",", "."), verlinkt),
        '<h2 class="sect">Kennzahlen</h2><div class="tr-grid">%s</div>' % karten,
        '<h2 class="sect">Befunde</h2>',
        abschnitt("Feldabweichungen", anzahl(x["diffs"]),
                  diff_tabelle(x["diffs"], idx),
                  "Extrahierter Wert weicht vom Datenbankwert ab."),
        abschnitt("Namespace-Abweichungen", anzahl(x["namespace_diffs"]),
                  diff_tabelle(x["namespace_diffs"], idx, False)),
        abschnitt("Nur in der Datenbank", anzahl(x["only_in_db"]),
                  id_tabelle(x["only_in_db"], idx),
                  "Records ohne Gegenstück in den geprüften Standarddokumenten."),
        abschnitt("Nur in den Standarddokumenten", anzahl(x["only_in_pdf"]),
                  id_tabelle(x["only_in_pdf"], idx),
                  "Extrahierte IDs ohne lokalen Record."),
        abschnitt("Leere strukturierte Extraktion", anzahl(x["empty_extraction"]),
                  id_tabelle(x["empty_extraction"], idx),
                  "ID erkannt, Felder nicht zuverlässig extrahiert."),
        '<h2 class="sect">Extraktions-Backends</h2><div class="tr-table-wrap">'
        '<table class="tr-table"><thead><tr><th>Backend</th><th>PDF-Records</th>'
        '<th>Verglichen</th><th>Feldabweichungen</th><th>Namespace</th><th>Leer</th>'
        '</tr></thead><tbody>%s</tbody></table></div>' % backend_zeilen,
        abschnitt("Geprüfte Standarddokumente", len(daten["documents"]),
                  '<ul class="tr-docs">%s</ul>' % docs),
        '<p class="dim">Erzeugt aus <code>%s</code> mit '
        '<code>_src/tools/traceability_report.py</code>. Der Bericht verändert keine '
        'Spec-Records und wird nicht in die Sprachbäume übersetzt.</p>' % esc(quelle),
    ])
    return {
        "file": "traceability.html",
        "title": "Traceability-Bericht %s — AUTOSAR %s" % (datum[:10], daten["release"]),
        "body_class": None,
        "nolang": True,
        "nav_html": '<a href="index.html">Start</a> / Traceability-Bericht',
        "footer": "extracted",
        "main_lead": "",
        "main": [{"t": "html", "html": inhalt, "tail": "\n"}],
    }


def verlinke_startseite(datum):
    idx = json.load(open(INDEX, encoding="utf-8"))
    block = {
        "t": "html",
        "nolang": True,
        "html": '<aside class="tr-home-link"><h2 class="sect">Qualität &amp; Traceability</h2>'
                '<p>Abgleich der Spezifikations-Datenbank mit den normativen '
                'AUTOSAR-R25-11-Standarddokumenten, Stand %s: '
                '<a href="traceability.html">Traceability-Bericht öffnen</a>.</p></aside>' % html.escape(datum),
        "tail": "\n",
    }
    idx["main"] = [b for b in idx["main"] if "traceability.html" not in b.get("html", "")]
    idx["main"].insert(2, block)
    with open(INDEX, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=1)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", required=True, help="crosscheck-JSON des Scraping-Laufs")
    ap.add_argument("--log", default=None, help="Lauf-Log (liefert das Datum)")
    a = ap.parse_args()
    daten = json.load(open(a.json, encoding="utf-8"))
    datum = lauf_datum(a.log, a.json)
    idx = record_index()
    seite = baue(daten, datum, idx, os.path.relpath(os.path.abspath(a.json), ROOT))
    with open(PAGE, "w", encoding="utf-8") as f:
        json.dump(seite, f, ensure_ascii=False, indent=1)
        f.write("\n")
    verlinke_startseite(datum)
    print("Traceability-Bericht: Stand %s, %d Record-IDs verlinkbar" % (datum, len(idx)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
