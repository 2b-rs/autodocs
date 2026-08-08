#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_indexes.py — Erzeugt kondensierte CSV-Sichten unter _src/data/ aus den
Quellen (_src/sources/pages/**.json + Fragmente).

Diese CSVs sind GENERIERTE INDIZES (Lesesichten für Analyse, QA und als
kompakter Kontext für KI-Werkzeuge) — Änderungen daran fließen NICHT in den
HTML-Tree zurück. Maßgebliche Quellen: sources/, content/, diagrams/, templates/.

    python3 _src/build_indexes.py
"""
import csv
import glob
import json
import os
import re
import sys

from lxml import html as LH

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_docmodel import (SRC, ROOT, PAGES_DIR, DATA_DIR, BEREICHE, iter_pages,
                          record_relpath)


def frag(html_text):
    return LH.fragment_fromstring(html_text)


def text_of(el):
    return re.sub(r"\s+", " ", el.text_content()).strip()


def page_type(f):
    if "/" not in f:
        return "index"
    return BEREICHE.get(f.split("/")[0], f.split("/")[0])


def walk_blocks(blocks, rec=None):
    for b in blocks:
        yield b, rec
        if b["t"] == "rec":
            yield from walk_blocks(b["blocks"], rec=b)
        if b["t"] == "fold":
            yield from walk_blocks(b["blocks"], rec=rec)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    pages, records, links, aiblocks, diagrams = [], [], [], [], []

    for page in iter_pages():
        f = page["file"]
        nav = frag("<nav>%s</nav>" % page["nav_html"])
        vis_tag = nav.find(".//span[@class]")
        badge = text_of(vis_tag) if vis_tag is not None and "vis-tag" in (vis_tag.get("class") or "") else ""
        module = ""
        for a in nav.findall(".//a"):
            m = re.search(r"modules/(\w+)\.html", a.get("href") or "")
            if m:
                module = m.group(1)
        if f.startswith("modules/"):
            module = f.split("/")[1].replace(".html", "")

        n_rec = n_ai = n_svg = 0
        cur = {"kind": "", "name": "", "sws_id": "", "sws_url": "", "upstream": "",
               "syntax": "", "desc": "", "scope": "", "header": "",
               "exception_safety": "", "thread_safety": "", "ai_fragments": []}

        for b, rec in walk_blocks(page["main"]):
            t = b["t"]
            if t == "rec":
                n_rec += 1
                cur = {"kind": "", "name": "", "sws_id": "", "sws_url": "", "upstream": "",
                       "syntax": "", "desc": "", "scope": "", "header": "",
                       "exception_safety": "", "thread_safety": "", "ai_fragments": []}
                b["_cur"] = cur
                continue
            cur_ = rec["_cur"] if rec is not None else None
            if t == "ai":
                n_ai += 1
                fp = os.path.join(SRC, b["src"])
                with open(fp, encoding="utf-8") as fh:
                    ael = frag(fh.read())
                h4 = ael.find(".//h4")
                head = text_of(h4) if h4 is not None else ""
                aiblocks.append([f, (rec["attrs"][1][1] if rec is not None and len(rec["attrs"]) > 1 else "(Seite)"),
                                 b["src"], head, len(text_of(ael))])
                if cur_ is not None:
                    cur_["ai_fragments"].append(b["src"])
            elif t == "svg":
                n_svg += 1
                diagrams.append([f, b["src"], next((v for k, v in b["wrap_attrs"] if k == "class"), "")])
            elif t == "html" and rec is not None:
                el = frag(b["html"])
                cls = (el.get("class") or "").split(" ")[0]
                if el.tag == "h3" and cls == "recname":
                    kind = el.find("span[@class='kind']")
                    cur_["kind"] = text_of(kind) if kind is not None else ""
                    sws = el.find("span[@class='sws']/a")
                    if sws is not None:
                        cur_["sws_id"] = text_of(sws).strip("[]")
                        cur_["sws_url"] = sws.get("href") or ""
                    ups = el.find("span[@class='ups']")
                    if ups is not None:
                        cur_["upstream"] = ";".join(text_of(a) for a in ups.findall("a"))
                    name = "".join(
                        ([el.text or ""] + [(c.tail or "") for c in el
                                            if (c.get("class") or "") not in ("sws", "ups")])
                    ) if False else ""
                    parts = [el.text or ""]
                    for c in el:
                        if (c.get("class") or "").split(" ")[0] in ("sws", "ups"):
                            break
                        if (c.get("class") or "") != "kind":
                            parts.append(text_of(c))
                        parts.append(c.tail or "")
                    cur_["name"] = re.sub(r"\s+", " ", "".join(parts)).strip()
                elif el.tag == "pre" and cls == "syntax":
                    cur_["syntax"] = text_of(el)
                elif el.tag == "div" and cls == "desc":
                    cur_["desc"] = text_of(el)
            elif t == "props" and rec is not None:
                for r in b["rows"]:
                    th = text_of(frag("<th>%s</th>" % r["th"]))
                    td = text_of(frag("<td>%s</td>" % r["td"]))
                    key = {"Exception-Sicherheit": "exception_safety",
                           "Thread-Sicherheit": "thread_safety",
                           "Scope": "scope", "Header-Datei": "header"}.get(th)
                    if key:
                        cur_[key] = td

        # Records einsammeln (nach Durchlauf, da _cur gefüllt wird)
        for b, rec in walk_blocks(page["main"]):
            if b["t"] == "rec" and "_cur" in b:
                c = b["_cur"]
                rid = next((v for k, v in b["attrs"] if k == "id"), "")
                records.append([f, rid, record_relpath(rid) if rid else "",
                                c["kind"], c["name"], c["sws_id"], c["sws_url"],
                                c["upstream"], c["scope"], c["header"],
                                c["exception_safety"], c["thread_safety"],
                                c["desc"][:300], ";".join(c["ai_fragments"])])

        pages.append([f, page_type(f), page["title"], page.get("body_class") or "",
                      badge, module, page["footer"], n_rec, n_ai, n_svg])

    # Externe Links aus dem generierten HTML (inkl. Fragmente): Occurrence-Liste
    from lib_docmodel import LANGS
    for hf in sorted(glob.glob(os.path.join(ROOT, "*.html")) +
                     glob.glob(os.path.join(ROOT, "*", "*.html"))):
        if os.path.basename(os.path.dirname(hf)) in LANGS:
            continue  # Sprachbäume: reine Ableitungen, nicht indexieren
        rel = os.path.relpath(hf, ROOT)
        doc = LH.parse(hf).getroot()
        for a in doc.iter("a"):
            href = a.get("href") or ""
            if href.startswith("http"):
                links.append([rel, text_of(a), href, a.get("class") or ""])

    def write(name, header, rows):
        with open(os.path.join(DATA_DIR, name), "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(header)
            w.writerows(rows)
        print("%-22s %6d Zeilen" % (name, len(rows)))

    write("pages.csv",
          ["datei", "typ", "titel", "interface_typ", "nav_badge", "modul", "footer",
           "n_records", "n_ki_bloecke", "n_diagramme"], pages)
    write("records.csv",
          ["datei", "record_id", "quelle", "art", "name", "sws_id", "sws_url", "upstream",
           "scope", "header", "exception_sicherheit", "thread_sicherheit",
           "beschreibung_kurz", "ki_fragmente"], records)
    write("links_extern.csv", ["datei", "linktext", "url", "css_klasse"], links)
    write("ki_bloecke.csv", ["datei", "anker", "fragment", "erste_ueberschrift", "textlaenge"], aiblocks)
    write("diagramme.csv", ["datei", "svg_quelle", "wrapper_klasse"], diagrams)


if __name__ == "__main__":
    main()
