#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate.py — Qualitätsprüfungen für den HTML-Tree und die Quellen.

    python3 _src/validate.py

Prüft:
  1. Tree == generate(Quellen)   (byte-genau; Tree ist reines Build-Artefakt)
  2. Interne Links: Zieldateien existieren, Anker (#…) existieren im Ziel
  3. Keine Platzhalter-Links href="#"
  4. Alle referenzierten Fragmente/SVGs existieren; verwaiste Dateien melden
  5. Sprachbäume (en es pt fr ru ar hi ko zh): byte-genau reproduzierbar,
     gleicher Seitenbestand wie Deutsch, korrekte lang-/dir-Attribute,
     keine Maskierungs-Platzhalter (⟦…⟧) im Output, Flaggen vorhanden
Exit-Code 0 = alles in Ordnung.
"""
import glob
import json
import multiprocessing
import re
import os
import sys
import urllib.parse
from concurrent.futures import ProcessPoolExecutor

from lxml import html as LH

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_docmodel import (SRC, ROOT, PAGES_DIR, LANGS, RTL, render_page,
                          load_templates, iter_pages)

problems = []
WORKERS = min(12, os.cpu_count() or 12)
# 'fork' avoids re-importing lxml/lib_docmodel per worker on macOS (default
# 'spawn' pays that cost on every worker, which dominates wall-clock time for
# many small per-page tasks and effectively serializes the workload).
_MP_CTX = multiprocessing.get_context("fork")


def _check_one_page(args):
    page, footers, page_tmpl = args
    target = os.path.join(ROOT, page["file"])
    gen = render_page(page, footers, page_tmpl)
    cur = open(target, encoding="utf-8").read() if os.path.exists(target) else None
    is_stale = gen != cur

    referenced = set()
    referenced_recs = set()

    def collect(blocks):
        for b in blocks:
            if b["t"] in ("ai", "svg"):
                referenced.add(b["src"])
            if b["t"] == "rec" and b.get("_src"):
                referenced_recs.add(b["_src"])
            if b["t"] in ("rec", "fold"):
                collect(b["blocks"])
    collect(page["main"])
    return page["file"], is_stale, referenced, referenced_recs


def check_build():
    page_tmpl, footers = load_templates()
    stale = []
    referenced = set()
    referenced_recs = set()
    pages = list(iter_pages())
    tasks = [(page, footers, page_tmpl) for page in pages]
    chunksize = max(1, len(tasks) // (WORKERS * 4)) if tasks else 1
    if len(tasks) < WORKERS * 2:
        results = [_check_one_page(t) for t in tasks]
    else:
        with ProcessPoolExecutor(max_workers=WORKERS, mp_context=_MP_CTX) as ex:
            results = list(ex.map(_check_one_page, tasks, chunksize=chunksize))
    for file, is_stale, refs, refs_recs in results:
        if is_stale:
            stale.append(file)
        referenced |= refs
        referenced_recs |= refs_recs
    stale.sort()
    # Spezifikations-DB: verwaiste Record-Dateien melden
    #
    # Ausnahme PRS_E2E: Diese Requirements beschreiben Verhalten/Protokollregeln
    # des E2E-Schutzes, besitzen keine eigenstaendige C++-API und werden daher
    # absichtlich NICHT einzeln per rec-ref in Klassen-/Namespace-Seiten
    # eingebaut, sondern gesammelt als Uebersichtstabelle auf
    # e2e-requirements.html dargestellt (siehe deren Einleitungstext). Sie sind
    # damit erwartungsgemaess "unreferenziert" im rec-ref-Sinn und werden hier
    # bewusst von der Waisen-Meldung ausgenommen, statt kuenstlich in
    # Einzelpanels gepresst zu werden.
    PRS_E2E_PREFIX = os.path.join("spec", "records", "PRS_E2E") + os.sep
    alle_recs = set(os.path.relpath(f, SRC) for f in
                    glob.glob(os.path.join(SRC, "spec", "records", "**", "*.json"),
                              recursive=True))
    rec_waisen = {r for r in (alle_recs - referenced_recs)
                 if not r.startswith(PRS_E2E_PREFIX)}
    if rec_waisen:
        problems.append("verwaiste Records in spec/records (auf keiner Seite referenziert): %s"
                        % sorted(rec_waisen)[:10])
    if stale:
        problems.append("Tree nicht aktuell (bitte generate.py laufen lassen): %d Seiten, z.B. %s"
                        % (len(stale), stale[:3]))
    # Waisen / fehlende Fragmente
    have = set()
    for d in ("content", "diagrams"):
        for f in glob.glob(os.path.join(SRC, d, "**", "*.*"), recursive=True):
            if os.path.isfile(f):
                have.add(os.path.relpath(f, SRC))
    missing = referenced - have
    orphans = set()
    for f in have - referenced:
        # Diagrammquellen gelten als referenziert, wenn ihr Ziel es ist:
        #   diagrams/**/svg_NN.dot|.seq.json  -> diagrams/**/svg_NN.svg
        #   content/ai/**/<stem>.<id>.dot|.seq.json -> content/ai/**/<stem>.html
        base = None
        for suf in (".seq.json", ".dot"):
            if f.endswith(suf):
                base = f[:-len(suf)]
                break
        if base is not None:
            if f.startswith("diagrams") and base + ".svg" in referenced:
                continue
            if f.startswith("content") and "." in os.path.basename(base):
                stem = base.rsplit(".", 1)[0]
                if stem + ".html" in referenced:
                    continue
        orphans.add(f)
    if missing:
        problems.append("fehlende Fragment-/SVG-Dateien: %s" % sorted(missing)[:5])
    if orphans:
        problems.append("verwaiste Fragment-/SVG-Dateien (nirgends referenziert): %s"
                        % sorted(orphans)[:10])


def check_links():
    ids = {}      # datei -> set(anker)
    pages = sorted(os.path.relpath(p, ROOT) for p in
                   glob.glob(os.path.join(ROOT, "*.html"))
                   + glob.glob(os.path.join(ROOT, "*", "*.html"))
                   + [p for lang in LANGS for p in
                      glob.glob(os.path.join(ROOT, lang, "**", "*.html"), recursive=True)])
    docs = {}
    for rel in pages:
        doc = LH.parse(os.path.join(ROOT, rel)).getroot()
        docs[rel] = doc
        ids[rel] = {e.get("id") for e in doc.iter() if e.get("id")}
    dead, placeholder, bilder = [], [], []
    for rel, doc in docs.items():
        base = os.path.dirname(rel)
        for img in doc.iter("img"):
            src = img.get("src") or ""
            if src and not src.startswith(("http://", "https://", "data:")):
                ziel = os.path.normpath(os.path.join(base, urllib.parse.unquote(src)))
                if not os.path.exists(os.path.join(ROOT, ziel)):
                    bilder.append((rel, src))
        for a in doc.iter("a"):
            href = a.get("href") or ""
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            if href == "#":
                placeholder.append((rel, a.text_content()[:40]))
                continue
            path, _, anchor = href.partition("#")
            target = rel if not path else os.path.normpath(os.path.join(base, urllib.parse.unquote(path)))
            if path and not os.path.exists(os.path.join(ROOT, target)):
                dead.append((rel, href, "Datei fehlt"))
            elif anchor and target in ids and anchor not in ids[target]:
                dead.append((rel, href, "Anker fehlt"))
    if placeholder:
        problems.append('Platzhalter-Links href="#": %d, z.B. %s' % (len(placeholder), placeholder[:5]))
    if dead:
        problems.append("tote interne Links: %d, z.B. %s" % (len(dead), dead[:8]))
    if bilder:
        problems.append("fehlende Bilddateien: %d, z.B. %s" % (len(bilder), bilder[:5]))


def _check_one_lang(args):
    lang, de_seiten = args
    from generate import generate_lang

    local_problems = []
    wurzel = os.path.join(ROOT, lang)
    if not os.path.isdir(wurzel):
        local_problems.append("Sprachbaum fehlt: %s/" % lang)
        return local_problems

    vorhanden = {os.path.relpath(p, wurzel).replace(os.sep, "/") for p in
                 glob.glob(os.path.join(wurzel, "**", "*.html"), recursive=True)}
    if vorhanden != de_seiten:
        local_problems.append("[%s] Seitenbestand weicht ab: +%s -%s"
                              % (lang, sorted(vorhanden - de_seiten)[:3], sorted(de_seiten - vorhanden)[:3]))

    _n, _stat, stale = generate_lang(lang, check=True)
    if stale:
        local_problems.append("[%s] Baum nicht aktuell (generate.py --lang=%s): %d Seiten, z.B. %s"
                              % (lang, lang, len(stale), stale[:3]))

    reste, falsch_lang = [], []
    soll_html = '<html lang="%s"%s>' % (lang, ' dir="rtl"' if lang in RTL else "")
    for rel in sorted(vorhanden):
        text = open(os.path.join(wurzel, rel), encoding="utf-8").read()
        if "\u27e6" in text:
            reste.append(rel)
        if soll_html not in text.split("\n", 2)[1]:
            falsch_lang.append(rel)
    if reste:
        local_problems.append("[%s] Maskierungs-Platzhalter im Output: %s" % (lang, reste[:5]))
    if falsch_lang:
        local_problems.append("[%s] falsches lang-/dir-Attribut: %s" % (lang, falsch_lang[:5]))
    return local_problems


def check_langs():
    de_seiten = set()
    for p in glob.glob(os.path.join(PAGES_DIR, "**", "*.json"), recursive=True):
        modell = json.load(open(p, encoding="utf-8"))
        if modell.get("nolang"):
            continue      # nur-deutsche Seite, absichtlich ohne Sprachbaum
        de_seiten.add(modell["file"])
    tasks = [(lang, de_seiten) for lang in LANGS]
    if len(tasks) < 2:
        lang_problem_lists = [_check_one_lang(t) for t in tasks]
    else:
        with ProcessPoolExecutor(max_workers=min(WORKERS, len(tasks)), mp_context=_MP_CTX) as ex:
            lang_problem_lists = list(ex.map(_check_one_lang, tasks, chunksize=1))
    for local in lang_problem_lists:
        problems.extend(local)
    for f in ("de", "gb", "es", "fr", "ru", "sa", "in", "kr", "cn"):
        if not os.path.exists(os.path.join(ROOT, "flags", f + ".svg")):
            problems.append("Flagge fehlt: flags/%s.svg" % f)



def check_requirement_review_schema():
    """Schema-Gate fuer review-faehige Requirement-Records.

    Bevor aus offenen Review-Befunden echte Prosa-Requirements im Tree landen,
    muss die Quelle denselben Mindestvertrag erfuellen wie der HTML-Workflow und
    review_ingest.py. Diese Pruefung blockiert Schreiblaeufe frueh, wenn
    requirement_text-Bloecke oder review_flags nur halb erweitert wurden.
    """
    import json as _json
    wurzel = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spec', 'records')
    if not os.path.isdir(wurzel):
        return
    fehler = []
    for ordner, _, dateien in os.walk(wurzel):
        for datei in dateien:
            if not datei.endswith('.json'):
                continue
            pfad = os.path.join(ordner, datei)
            rec = _json.load(open(pfad, encoding='utf-8'))
            rid = rec.get('id', datei)
            rmeta = rec.get('requirement_meta')
            for i, block in enumerate(rec.get('blocks', [])):
                if block.get('t') != 'requirement_text':
                    continue
                wo = '%s:block[%d]' % (rid, i)
                for feld in ('text_en', 'text_raw', 'repairs', 'suspects'):
                    if feld not in block:
                        fehler.append('%s fehlt %s' % (wo, feld))
                if not isinstance(block.get('repairs', []), list):
                    fehler.append('%s repairs muss Liste sein' % wo)
                if not isinstance(block.get('suspects', []), list):
                    fehler.append('%s suspects muss Liste sein' % wo)
                if rmeta is None:
                    fehler.append('%s hat requirement_text ohne requirement_meta' % wo)
                else:
                    for feld in ('confidence', 'review_status', 'review_reason'):
                        if not str(rmeta.get(feld) or '').strip():
                            fehler.append('%s requirement_meta.%s fehlt' % (wo, feld))
                flags = block.get('review_flags') or []
                if not isinstance(flags, list):
                    fehler.append('%s review_flags muss Liste sein' % wo)
                    continue
                for j, flag in enumerate(flags):
                    wf = '%s.review_flags[%d]' % (wo, j)
                    for feld in ('id', 'status'):
                        if not str(flag.get(feld) or '').strip():
                            fehler.append('%s %s fehlt' % (wf, feld))
                    if flag.get('status', 'open') == 'open':
                        finding = (flag.get('decision_basis') or {}).get('finding')
                        if finding is None:
                            if not str(flag.get('reason') or '').strip():
                                fehler.append('%s offenes Flag ohne reason' % wf)
                        else:
                            if not isinstance(finding.get('suspects', []), list):
                                fehler.append('%s decision_basis.finding.suspects muss Liste sein' % wf)
                            if not isinstance(finding.get('repairs', []), list):
                                fehler.append('%s decision_basis.finding.repairs muss Liste sein' % wf)
                    else:
                        for feld in ('decided_by', 'decided_at', 'rationale', 'identity', 'text_hash', 'decision_basis'):
                            if feld not in flag or (feld != 'decision_basis' and not str(flag.get(feld) or '').strip()):
                                fehler.append('%s resolved/rejected Flag ohne %s' % (wf, feld))
                        basis = flag.get('decision_basis') or {}
                        if not basis.get('finding'):
                            fehler.append('%s decision_basis.finding fehlt' % wf)
                        if flag.get('identity') not in ('github_authenticated', 'self_declared'):
                            fehler.append('%s identity ungueltig: %r' % (wf, flag.get('identity')))
    if fehler:
        problems.append('Schema-Gate review-faehige Requirements verletzt (%d), z.B. %s'
                        % (len(fehler), fehler[:10]))

def check_namespaces():
    """Jeder Spec-Record traegt einen expliziten, konsistenten ns-Block.

    Die Modulzugehoerigkeit darf implizit aus dem Ablageort kommen, der
    Namensraum jedoch nicht: er steht als Klartextfeld im Record. Erlaubte
    Abweichungen von "ara::<modul>" sind in spec/namespaces.json katalogisiert.
    """
    import json as _json
    wurzel = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spec", "records")
    katalog = os.path.join(os.path.dirname(wurzel), "namespaces.json")
    if not os.path.isdir(wurzel):
        return
    erlaubt = set()
    if os.path.exists(katalog):
        for gruppe in _json.load(open(katalog, encoding="utf-8")).get("abweichungen", {}).values():
            erlaubt.update(gruppe)
    # Ausnahme PRS_E2E: wie beim Waisen-Check oben beschrieben beschreiben
    # diese Requirements Protokollregeln ohne eigene C++-API und tragen
    # daher bewusst keinen Namensraum -- keine Modellierungsluecke.
    PRS_E2E_PREFIX = "PRS_E2E_"

    ohne, unbekannt = [], []
    for ordner, _, dateien in os.walk(wurzel):
        for datei in dateien:
            if not datei.endswith(".json"):
                continue
            pfad = os.path.join(ordner, datei)
            rec = _json.load(open(pfad, encoding="utf-8"))
            rid = rec.get("id", datei)
            if isinstance(rid, str) and rid.startswith(PRS_E2E_PREFIX):
                continue
            # namespace_meta ist das aktuelle Schema (ersetzt das aeltere
            # "ns"-Feld nach einer Migration); beide Formen tragen dieselben
            # Unterfelder (namespace, enclosing/umschliessend, module,
            # source/quelle, generated). Rueckwaertskompatibel beide lesen,
            # damit noch nicht migrierte Legacy-Records weiter greifen.
            ns = rec.get("namespace_meta")
            if not isinstance(ns, dict):
                ns = rec.get("ns")
            if not isinstance(ns, dict) or "namespace" not in ns:
                ohne.append(rid)
                continue
            quelle = ns.get("source") or ns.get("quelle")
            if ns.get("namespace") is None and quelle != "dienst":
                ohne.append(rid)
                continue
            if ns.get("abweichung") and ns.get("namespace") and ns["namespace"] not in erlaubt:
                unbekannt.append((rid, ns["namespace"]))
    if ohne:
        problems.append("Records ohne expliziten Namensraum (%d): %s" % (len(ohne), ohne[:5]))
    if unbekannt:
        problems.append("Nicht katalogisierte Namensraum-Abweichung (%d): %s"
                        % (len(unbekannt), unbekannt[:5]))


def _check_home_links_one_lang(lang):
    """0008-03: header-logo (a.home) und Breadcrumb-"Start"-Link muessen innerhalb
    des eigenen Sprachbaums bleiben (bzw. beim kanonischen Baum im Wurzel-index.html),
    duerfen also nicht in den deutschen Wurzelbaum eines anderen Sprachbaums springen."""
    local_problems = []
    wurzel = os.path.join(ROOT, lang) if lang != "de" else ROOT
    if not os.path.isdir(wurzel):
        return local_problems
    for full in glob.glob(os.path.join(wurzel, "**", "*.html"), recursive=True):
        rel = os.path.relpath(full, wurzel)
        if lang == "de" and rel.split(os.sep, 1)[0] in LANGS:
            continue  # ROOT also directly contains the language subtrees; skip them here
        text = open(full, encoding="utf-8").read()
        m = re.search(r'<a class="home" href="([^"]+)"', text)
        if not m:
            continue
        home_href = m.group(1)
        page_dir = os.path.dirname(full)
        home_target = os.path.normpath(os.path.join(page_dir, home_href))
        expected = os.path.join(wurzel, "index.html")
        if home_target != expected:
            local_problems.append("[%s] home-Link zeigt aus dem Sprachbaum heraus: %s -> %s (erwartet %s)"
                                  % (lang, rel, home_href, os.path.relpath(expected, wurzel)))
        nav_m = re.search(r'<nav class="crumbs">(.*?)</nav>', text, re.S)
        if nav_m:
            crumb_m = re.search(r'<a[^>]+href="([^"]+)"[^>]*>', nav_m.group(1))
            if crumb_m:
                crumb_href = crumb_m.group(1)
                crumb_target = os.path.normpath(os.path.join(page_dir, crumb_href))
                if crumb_target != expected:
                    local_problems.append("[%s] Breadcrumb-Start-Link zeigt aus dem Sprachbaum heraus: %s -> %s (erwartet %s)"
                                          % (lang, rel, crumb_href, os.path.relpath(expected, wurzel)))
    return local_problems


def check_home_links():
    """0008-03: Regressionspruefung fuer den Header-Logo- und Breadcrumb-"Start"-Link
    in allen Sprachbaeumen (gefunden 2026-08-13, behoben in 0008-02)."""
    for lang in ["de"] + LANGS:
        problems.extend(_check_home_links_one_lang(lang))


_GERMAN_CHROME_STRINGS = None


def _german_chrome_strings():
    """0008-04: die deutschen Quelltexte aus ui.json["global"] (feste, per
    globale_ersetzungen() zu ersetzende Chrome-/Badge-Texte) plus die hartcodierten
    Default-Strings aus lib_docmodel._review_page_enhancements(), die durch die
    i18n-Pipeline laufen MUESSEN und in keinem Sprachbaum unuebersetzt ueberleben duerfen."""
    global _GERMAN_CHROME_STRINGS
    if _GERMAN_CHROME_STRINGS is None:
        ui_all = json.load(open(os.path.join(SRC, "i18n", "ui.json"), encoding="utf-8"))
        de_ui = ui_all.get("de", {})
        strings = set(de_ui.get("global", {}).keys())
        strings.add("mit Review-Bedarf")
        strings.add("Vor der Freigabe müssen Requirement-Text und Zuordnung geprüft werden.")
        _GERMAN_CHROME_STRINGS = sorted(s for s in strings if s)
    return _GERMAN_CHROME_STRINGS


def _check_no_hardcoded_german_one_lang(lang):
    local_problems = []
    wurzel = os.path.join(ROOT, lang)
    if not os.path.isdir(wurzel):
        return local_problems
    strings = _german_chrome_strings()
    hits = {}
    for full in glob.glob(os.path.join(wurzel, "**", "*.html"), recursive=True):
        text = open(full, encoding="utf-8").read()
        for s in strings:
            if s in text:
                hits.setdefault(s, []).append(os.path.relpath(full, wurzel))
    for s, files in hits.items():
        local_problems.append("[%s] unuebersetzter deutscher Chrome-Text %r in %d Datei(en), z.B. %s"
                              % (lang, s, len(files), files[:3]))
    return local_problems


def check_no_hardcoded_german():
    """0008-04: erkennt hartcodierte deutsche UI-Strings in generiertem
    nicht-deutschem HTML, damit zukuenftige Chrome-/Badge-Texte nicht mehr
    stillschweigend an der i18n-Pipeline vorbeigehen (gefunden 2026-08-13, 0008-01)."""
    for lang in LANGS:
        problems.extend(_check_no_hardcoded_german_one_lang(lang))



def check_workflow_lifecycle():
    """0006-13: curation-item@v1s status vocabulary (0006-03) and the
    unified workflow lifecycle's state vocabulary (0006-06) are maintained
    in two separate modules and must not silently drift apart. Also spot-
    checks that every currently-persisted queue-flag-shaped payload on disk
    (review-queue/, curation-queue/, if present) normalizes into a
    curation-item@v1 item whose status maps to a real lifecycle state."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
    import curation_item_lifecycle_check as cilc
    vocab_problems = cilc.validate_vocabularies()
    if vocab_problems:
        problems.extend("0006-13 vocabulary drift: %s" % p for p in vocab_problems)
        return
    import curation_item as ci
    import glob as _glob
    for queue_dir in ("review-queue", "curation-queue"):
        base = os.path.join(SRC, "..", queue_dir)
        if not os.path.isdir(base):
            continue
        for pfad in _glob.glob(os.path.join(base, "**", "*.json"), recursive=True):
            payload = json.load(open(pfad, encoding="utf-8"))
            adapter = ci.from_review_flag if queue_dir == "review-queue" else ci.from_curation_flag
            item = adapter(payload)
            if not ci.is_conformant(item):
                problems.append("%s: normalized curation-item is not conformant" % pfad)
                continue
            if cilc.item_lifecycle_state(item) is None:
                problems.append("%s: status %r has no mapped lifecycle state" % (pfad, item.get("status")))


def check_record_status():
    """0006-04: jeder Spec-Record muss einen 'status'-Schluessel tragen
    (Zustand/Historie), damit Kurations-Sichtbarkeit nicht mehr auf das
    SWS_LOG-Pilotmodul beschraenkt bleibt. Nach dem einmaligen Backfill
    (migriere_status_backfill.py) darf kein neuer Schreibpfad hierhinter
    zurueckfallen."""
    import json as _json
    wurzel = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spec", "records")
    if not os.path.isdir(wurzel):
        return
    ohne = []
    for ordner, _, dateien in os.walk(wurzel):
        for datei in dateien:
            if not datei.endswith(".json"):
                continue
            pfad = os.path.join(ordner, datei)
            rec = _json.load(open(pfad, encoding="utf-8"))
            if "status" not in rec:
                ohne.append(rec.get("id", datei))
    if ohne:
        problems.append("Records ohne 'status' (%d): %s" % (len(ohne), ohne[:5]))



def main():
    check_build()
    check_links()
    check_langs()
    check_requirement_review_schema()
    check_namespaces()
    check_home_links()
    check_no_hardcoded_german()
    check_record_status()
    check_workflow_lifecycle()
    if problems:
        print("PROBLEME:")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print("OK — Tree aktuell (de + %d Sprachbäume), alle internen Links und Anker gültig, keine Waisen."
          % len(LANGS))


if __name__ == "__main__":
    main()
