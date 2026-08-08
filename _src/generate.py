#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — Erzeugt den kompletten HTML-Tree aus den Quellen unter _src/.

    python3 _src/generate.py            # schreibt alle deutschen Seiten nach ../
    python3 _src/generate.py --check    # schreibt nichts, vergleicht nur (DOM)
    python3 _src/generate.py classes/cl_ara_core_Future_420ba8.html   # einzelne Seite(n)
    python3 _src/generate.py --lang=en  # zusätzlich Sprachbaum ../en/ erzeugen
    python3 _src/generate.py --lang=alle   # alle Sprachbäume (en es fr ru ar hi ko zh)

Sprachbäume (Details in lib_i18n.py): Deutsch ist kanonisch; Übersetzungen
kommen aus _src/i18n/. Segmente ohne Übersetzung bleiben deutsch (Fallback,
wird gezählt und gemeldet).

Quellen: _src/sources/pages/**.json  (Seitenmodelle / Komposition)
         _src/spec/records/**.json   (Spezifikations-DB, via rec-ref referenziert)
         _src/content/ai/**          (KI-Fragmente, referenziert aus den Modellen)
         _src/diagrams/**            (SVG-Diagramme, referenziert aus den Modellen)
         _src/templates/             (Seiten-Chrome, Footer-Varianten)
         _src/site.json              (Projektmanifest: Bereiche, Sprachen)
Danach:  python3 _src/validate.py    (Prüfungen, siehe WARTUNG.md)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_docmodel import (SRC, ROOT, LANGS, render_page, load_templates,
                          compare_html, iter_pages)


def generate_lang(lang, only=None, check=False):
    """Einen Sprachbaum ../<lang>/ erzeugen (oder mit check=True nur byte-genau
    vergleichen). Liefert (Seitenzahl, Statistik, Liste abweichender Dateien)."""
    from lib_i18n import lade_register, lade_soll, uebersetze_seite, globale_ersetzungen, Statistik
    seg, _lab, ui = lade_register(lang)
    page_tmpl, footers = load_templates()
    footers = dict(footers, **ui.get("footers", {}))
    stat = Statistik(soll=lade_soll())
    n, stale = 0, []
    for page in iter_pages(only):
        uebers = uebersetze_seite(page, lang, seg, ui, stat)
        html_text = render_page(uebers, footers, page_tmpl, lang=lang)
        html_text = globale_ersetzungen(html_text, ui)
        target = os.path.join(ROOT, lang, page["file"])
        if check:
            cur = open(target, encoding="utf-8").read() if os.path.exists(target) else None
            if cur != html_text:
                stale.append("%s/%s" % (lang, page["file"]))
        else:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(html_text)
        n += 1
    if not check:
        print("generiert [%s]: %d Seiten, Treffer %d, fehlende Übersetzungen (Fallback deutsch): %d eindeutige Segmente"
              % (lang, n, stat.treffer, len(stat.fehlend)))
    return n, stat, stale


def main():
    args = [a for a in sys.argv[1:]]
    check = "--check" in args
    langs = []
    for a in args:
        if a.startswith("--lang="):
            w = a.split("=", 1)[1]
            langs = list(LANGS) if w in ("alle", "all") else w.split(",")
    only = set(a for a in args if not a.startswith("--")) or None

    page_tmpl, footers = load_templates()
    n, bad = 0, 0
    for page in iter_pages(only):
        html_text = render_page(page, footers, page_tmpl)
        target = os.path.join(ROOT, page["file"])
        if check:
            errs = compare_html(target, html_text) if os.path.exists(target) else ["Datei fehlt"]
            if errs:
                bad += 1
                print("ABWEICHUNG %s" % page["file"])
                for e in errs[:5]:
                    print("   ", e)
        else:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(html_text)
        n += 1
    print(("geprüft" if check else "generiert") + ": %d Seiten" % n + (", Abweichungen: %d" % bad if check else ""))
    if not check:
        for lang in langs:
            generate_lang(lang, only)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
