#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract.py — Zerlegt den generierten HTML-Tree in editierbare Quelldateien.

Normalfall ist dieser Weg NICHT nötig: Quellen unter _src/ ändern und
generate.py laufen lassen. extract.py dient dem Resync, falls doch einmal
direkt im HTML editiert wurde (bitte nur mit XML-Werkzeugen, s. WARTUNG.md):

    python3 _src/extract.py          # liest ../ (Doku-Wurzel), schreibt _src/sources etc.

Es gilt: extract(generate(sources)) == sources (modulo Whitespace im Chrome).
"""
import glob
import json
import os
import re
import shutil
import sys

from lxml import etree, html as LH

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_docmodel import (SRC, ROOT, PAGES_DIR, AI_DIR, DIAG_DIR, TMPL_DIR,
                          SPEC_DIR, BEREICHE,
                          serialize, inner_html, attrs_list, render_blocks,
                          dom_equal, externalize_recs)


def is_comment(el):
    return isinstance(el, etree._Comment)


def cls_of(el):
    return (el.get("class") or "") if not is_comment(el) else ""


class PageExtractor:
    def __init__(self, relfile):
        self.relfile = relfile                       # z.B. classes/cl_x.html
        self.stem = re.sub(r"\.html$", "", relfile)  # classes/cl_x
        self.ai_n = 0
        self.svg_n = 0
        self.fallbacks = []

    # ---------------------------------------------------------- Hilfen
    def _write_fragment(self, base, name, el):
        path = os.path.join(base, self.stem, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(serialize(el) + "\n")
        return os.path.relpath(path, SRC)

    def _verified(self, block, el):
        """Strukturierten Block probeweise rendern und mit Original vergleichen;
        bei Abweichung Verbatim-Fallback."""
        tail = block.pop("tail", "")
        rendered = render_blocks([dict(block, tail="")], 0)
        try:
            e2 = LH.fragment_fromstring(rendered)
            errs = dom_equal(el, e2)
        except Exception as ex:  # noqa
            errs = [repr(ex)]
        block["tail"] = tail
        if errs:
            self.fallbacks.append((self.relfile, block["t"], errs[:2]))
            return {"t": "html", "html": serialize(el), "tail": tail}
        return block

    # ---------------------------------------------------------- Blöcke
    def block_of(self, el, rec_ctx=None):
        tail = el.tail or ""
        if is_comment(el):
            return {"t": "html", "html": serialize(el), "tail": tail}
        cls = cls_of(el)
        cls0 = cls.split(" ")[0] if cls else ""
        if el.tag == "div" and cls0 == "ai":
            self.ai_n += 1
            name = "rec_%s_%02d.html" % (rec_ctx, self.ai_n) if rec_ctx else "main_%02d.html" % self.ai_n
            src = self._write_fragment(AI_DIR, name, el)
            return {"t": "ai", "src": src, "tail": tail}
        if el.tag == "div" and cls0 in ("umlwrap", "diagram"):
            svgs = [c for c in el if str(c.tag) == "svg"]
            if len(svgs) == 1:
                svg = svgs[0]
                idx = list(el).index(svg)
                pre = (el.text or "") + "".join(serialize(c) + (c.tail or "") for c in list(el)[:idx])
                inner_tail = (svg.tail or "") + "".join(serialize(c) + (c.tail or "") for c in list(el)[idx + 1:])
                self.svg_n += 1
                src = self._write_fragment(DIAG_DIR, "svg_%02d.svg" % self.svg_n, svg)
                block = {"t": "svg", "wrap_attrs": attrs_list(el), "pre": pre,
                         "src": src, "inner_tail": inner_tail, "tail": tail}
                return self._verified(block, el)
        if el.tag == "details" and cls0 == "fold":
            kids = list(el)
            if kids and kids[0].tag == "summary" and not (el.text or "").strip():
                summ = kids[0]
                blocks = [self.block_of(c, rec_ctx=rec_ctx) for c in kids[1:]]
                return {"t": "fold", "attrs": attrs_list(el),
                        "summary": inner_html(summ), "lead": summ.tail or "",
                        "blocks": blocks, "tail": tail}
        if el.tag == "article" and cls0 == "rec":
            rid = el.get("id") or ("art%d" % (self.ai_n + 1))
            blocks = [self.block_of(c, rec_ctx=rid) for c in el]
            block = {"t": "rec", "attrs": attrs_list(el), "lead": el.text or "",
                     "blocks": blocks, "tail": tail}
            # rec selbst nicht via _verified (Fragmente sind schon geschrieben);
            # Unterblöcke wurden einzeln verifiziert, Rahmen ist trivial.
            return block
        if el.tag == "table" and cls0 == "props":
            rows = []
            ok = not (el.text or "").strip()
            for tr in el:
                kids = list(tr)
                if (is_comment(tr) or tr.tag != "tr" or len(kids) != 2
                        or kids[0].tag != "th" or kids[1].tag != "td"
                        or (tr.text or "").strip() or (tr.tail or "").strip()
                        or (kids[0].tail or "").strip() or (kids[1].tail or "").strip()):
                    ok = False
                    break
                rows.append({"th": inner_html(kids[0]), "th_attrs": attrs_list(kids[0]),
                             "td": inner_html(kids[1]), "td_attrs": attrs_list(kids[1])})
            if ok:
                return self._verified({"t": "props", "attrs": attrs_list(el),
                                       "rows": rows, "tail": tail}, el)
        if el.tag == "table" and cls0 == "params":
            rows = []
            ok = not (el.text or "").strip()
            for tr in el:
                if is_comment(tr) or tr.tag != "tr" or (tr.text or "").strip() or (tr.tail or "").strip():
                    ok = False
                    break
                cells = []
                for c in tr:
                    if c.tag not in ("th", "td") or (c.tail or "").strip():
                        ok = False
                        break
                    cells.append({"tag": c.tag, "attrs": attrs_list(c), "html": inner_html(c)})
                if not ok:
                    break
                rows.append({"cells": cells})
            if ok:
                return self._verified({"t": "params", "attrs": attrs_list(el),
                                       "rows": rows, "tail": tail}, el)
        return {"t": "html", "html": serialize(el), "tail": tail}


def extract_page(relfile, footers):
    doc = LH.parse(os.path.join(ROOT, relfile)).getroot()
    body = doc.find("body")
    main = body.find("main")
    nav = body.find("nav")
    footer = body.find("footer")

    # Altfehler-Normalisierung: Inhalt zwischen </main> und <footer> nach <main>
    for stray in [c for c in body if c.tag not in ("header", "nav", "main", "footer")]:
        if len(main):
            list(main)[-1].tail = (list(main)[-1].tail or "") + "\n"
        main.append(stray)

    fser = serialize(footer)
    fkey = None
    for k, v in footers.items():
        if v == fser:
            fkey = k
    if fkey is None:
        for kw, name in (("extrahiert", "extracted"), ("abgeleitet", "derived"),
                         ("erg\u00e4nzt", "supplemented")):
            if kw in fser and name not in footers:
                fkey = name
                break
        if fkey is None:
            fkey = "footer_%d" % (len(footers) + 1)
        footers[fkey] = fser

    px = PageExtractor(relfile)
    page = {
        "file": relfile,
        "title": doc.find("head/title").text or "",
        "body_class": body.get("class"),
        "nav_html": inner_html(nav),
        "footer": fkey,
        "main_lead": main.text or "",
        "main": [px.block_of(c) for c in main],
    }
    return page, px.fallbacks


def main():
    files = sorted(
        os.path.relpath(p, ROOT)
        for pat in ["*.html"] + ["%s/*.html" % b for b in BEREICHE]
        for p in glob.glob(os.path.join(ROOT, pat))
    )
    tmpl_path = os.path.join(TMPL_DIR, "page.html.tmpl")
    if not os.path.exists(tmpl_path):
        sys.exit("templates/page.html.tmpl fehlt — extract.py leitet das "
                 "Seiten-Chrome nicht mehr selbst ab. Template aus einem "
                 "bestehenden Projekt übernehmen bzw. aus einer Beispielseite "
                 "herauslösen (siehe WARTUNG.md, Abschnitt Templates).")
    # Alte Extraktion räumen — Diagrammquellen (.dot, .seq.json) bleiben
    # erhalten, denn sie sind Quelldateien und nicht aus dem Tree ableitbar.
    quellen = {}
    for d in (AI_DIR, DIAG_DIR):
        for pat in ("*.dot", "*.seq.json"):
            for p in glob.glob(os.path.join(d, "**", pat), recursive=True):
                quellen[p] = open(p, encoding="utf-8").read()
    for d in (PAGES_DIR, AI_DIR, DIAG_DIR, SPEC_DIR):
        shutil.rmtree(d, ignore_errors=True)
    os.makedirs(TMPL_DIR, exist_ok=True)

    footers = {}
    all_fallbacks = []
    n_records = 0
    for rel in files:
        page, fb = extract_page(rel, footers)
        all_fallbacks += fb
        # Records mit ID in die Spezifikations-DB auslagern (rec-ref)
        n_records += len(externalize_recs(page))
        out = os.path.join(PAGES_DIR, re.sub(r"\.html$", ".json", rel))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(page, f, ensure_ascii=False, indent=1)
            f.write("\n")

    with open(os.path.join(TMPL_DIR, "footers.json"), "w", encoding="utf-8") as f:
        json.dump(footers, f, ensure_ascii=False, indent=1)

    # Diagrammquellen zurücklegen (nur wenn ihr Zielort noch existiert)
    verworfen = []
    for p, inhalt in quellen.items():
        if os.path.isdir(os.path.dirname(p)):
            with open(p, "w", encoding="utf-8") as f:
                f.write(inhalt)
        else:
            verworfen.append(os.path.relpath(p, SRC))
    if verworfen:
        print("Diagrammquellen ohne Zielort verworfen: %s" % verworfen[:10])

    print("Seiten extrahiert: %d, Records in spec/records: %d, Footer-Varianten: %d"
          % (len(files), n_records, len(footers)))
    if all_fallbacks:
        print("Verbatim-Fallbacks (strukturierte Extraktion fehlgeschlagen): %d" % len(all_fallbacks))
        for f_ in all_fallbacks[:20]:
            print("  ", f_)


if __name__ == "__main__":
    main()
