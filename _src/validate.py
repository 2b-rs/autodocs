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
import os
import sys
import urllib.parse

from lxml import html as LH

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_docmodel import (SRC, ROOT, PAGES_DIR, LANGS, RTL, render_page,
                          load_templates, iter_pages)

problems = []


def check_build():
    page_tmpl, footers = load_templates()
    stale = []
    referenced = set()
    referenced_recs = set()
    for page in iter_pages():
        target = os.path.join(ROOT, page["file"])
        gen = render_page(page, footers, page_tmpl)
        cur = open(target, encoding="utf-8").read() if os.path.exists(target) else None
        if gen != cur:
            stale.append(page["file"])
        def collect(blocks):
            for b in blocks:
                if b["t"] in ("ai", "svg"):
                    referenced.add(b["src"])
                if b["t"] == "rec" and b.get("_src"):
                    referenced_recs.add(b["_src"])
                if b["t"] in ("rec", "fold"):
                    collect(b["blocks"])
        collect(page["main"])
    # Spezifikations-DB: verwaiste Record-Dateien melden
    alle_recs = set(os.path.relpath(f, SRC) for f in
                    glob.glob(os.path.join(SRC, "spec", "records", "**", "*.json"),
                              recursive=True))
    rec_waisen = alle_recs - referenced_recs
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


def check_langs():
    from generate import generate_lang
    de_seiten = set()
    for p in glob.glob(os.path.join(PAGES_DIR, "**", "*.json"), recursive=True):
        modell = json.load(open(p, encoding="utf-8"))
        if modell.get("nolang"):
            continue      # nur-deutsche Seite, absichtlich ohne Sprachbaum
        de_seiten.add(modell["file"])
    for lang in LANGS:
        wurzel = os.path.join(ROOT, lang)
        if not os.path.isdir(wurzel):
            problems.append("Sprachbaum fehlt: %s/" % lang)
            continue
        vorhanden = {os.path.relpath(p, wurzel).replace(os.sep, "/") for p in
                     glob.glob(os.path.join(wurzel, "**", "*.html"), recursive=True)}
        if vorhanden != de_seiten:
            problems.append("[%s] Seitenbestand weicht ab: +%s -%s"
                            % (lang, sorted(vorhanden - de_seiten)[:3], sorted(de_seiten - vorhanden)[:3]))
        _n, _stat, stale = generate_lang(lang, check=True)
        if stale:
            problems.append("[%s] Baum nicht aktuell (generate.py --lang=%s): %d Seiten, z.B. %s"
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
            problems.append("[%s] Maskierungs-Platzhalter im Output: %s" % (lang, reste[:5]))
        if falsch_lang:
            problems.append("[%s] falsches lang-/dir-Attribut: %s" % (lang, falsch_lang[:5]))
    for f in ("de", "gb", "es", "fr", "ru", "sa", "in", "kr", "cn"):
        if not os.path.exists(os.path.join(ROOT, "flags", f + ".svg")):
            problems.append("Flagge fehlt: flags/%s.svg" % f)


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
    ohne, unbekannt = [], []
    for ordner, _, dateien in os.walk(wurzel):
        for datei in dateien:
            if not datei.endswith(".json"):
                continue
            pfad = os.path.join(ordner, datei)
            rec = _json.load(open(pfad, encoding="utf-8"))
            ns = rec.get("ns")
            if not isinstance(ns, dict) or "namespace" not in ns:
                ohne.append(rec.get("id", datei))
                continue
            if ns.get("namespace") is None and ns.get("quelle") != "dienst":
                ohne.append(rec.get("id", datei))
                continue
            if ns.get("abweichung") and ns.get("namespace") and ns["namespace"] not in erlaubt:
                unbekannt.append((rec.get("id", datei), ns["namespace"]))
    if ohne:
        problems.append("Records ohne expliziten Namensraum (%d): %s" % (len(ohne), ohne[:5]))
    if unbekannt:
        problems.append("Nicht katalogisierte Namensraum-Abweichung (%d): %s"
                        % (len(unbekannt), unbekannt[:5]))


def main():
    check_build()
    check_links()
    check_langs()
    check_namespaces()
    if problems:
        print("PROBLEME:")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print("OK — Tree aktuell (de + %d Sprachbäume), alle internen Links und Anker gültig, keine Waisen."
          % len(LANGS))


if __name__ == "__main__":
    main()
