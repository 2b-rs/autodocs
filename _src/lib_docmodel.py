#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lib_docmodel.py — Gemeinsames Datenmodell für Extraktion (extract.py) und
Generierung (generate.py). Projektspezifika (Bereiche, Sprachen, Flaggen)
stehen im Manifest _src/site.json — dieses Modul und alle Skripte sind
projektneutral gehalten (siehe ARCHITEKTUR.md).

Seitenmodell (JSON, _src/sources/pages/<pfad>.json):
  {
    "file":       "classes/cl_….html",   Zielpfad relativ zur Doku-Wurzel
    "title":      "…",                    <title>-Text (unkodiert)
    "body_class": "vis-app" | null,
    "nav_html":   "…",                    inneres HTML von <nav class="crumbs">
    "footer":     "extracted" | …,        Schlüssel in _src/templates/footers.json
    "main_lead":  "\n",                   führender Text in <main>
    "main":       [ Block, … ]
  }

Blocktypen (jeder Block hat "tail": Text NACH dem Element, meist "\n" oder ""):
  html   {"html": "<h2 …>…</h2>"}                     beliebiges Element, verbatim
  svg    {"wrap_class","wrap_attrs","pre","src","inner_tail"}
                                                       Diagramm-Wrapper; SVG liegt
                                                       als Datei unter _src/diagrams/
  ai     {"src": "content/ai/…/x.html"}                KI-Block als Fragmentdatei
  rec    {"attrs","lead","blocks":[…]}                 <article class="rec"> mit
                                                       rekursiven Unterblöcken
  rec-ref {"src": "spec/records/SWS_CORE/SWS_….json"}   Verweis auf einen Record
                                                       der Spezifikations-DB; wird
                                                       beim Laden (load_page) zu
                                                       einem rec-Block aufgelöst
                                                       (Merkfeld "_src" = Quelle)
  fold   {"attrs","summary","lead","blocks":[…]}       klappbarer Abschnitt:
                                                       <details><summary>H2</summary>…>;
                                                       "summary" = H2-Element verbatim,
                                                       "lead" = Text nach </summary>
  props  {"attrs","rows":[{"th","th_attrs","td","td_attrs"},…]}
                                                       Eigenschafts-Tabelle
  params {"attrs","rows":[{"cells":[{"tag","attrs","html"},…],"tail"},…],"lead"}
                                                       Parameter-/Rückgabe-Tabelle
"""
import hashlib
import json
import os
import re
from lxml import etree, html as LH

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SRC)

PAGES_DIR = os.path.join(SRC, "sources", "pages")
AI_DIR = os.path.join(SRC, "content", "ai")
DIAG_DIR = os.path.join(SRC, "diagrams")
TMPL_DIR = os.path.join(SRC, "templates")
DATA_DIR = os.path.join(SRC, "data")
SPEC_DIR = os.path.join(SRC, "spec", "records")

VOID_TAGS = {"meta", "link", "br", "hr", "img", "input"}

# ------------------------------------------------- Projektmanifest (site.json)
# Alle projektspezifischen Konstanten (Bereiche, Sprachen) kommen aus dem
# Manifest; ein neues Projekt braucht nur ein eigenes site.json + Templates.
with open(os.path.join(SRC, "site.json"), encoding="utf-8") as _f:
    SITE = json.load(_f)

BEREICHE = SITE["bereiche"]              # Unterverzeichnis -> Seitentyp

# ------------------------------------------------------------- Sprachen
# Die kanonische Sprache liegt an der Wurzel; jede Zielsprache erhält einen
# Spiegelbaum unter <lang>/ (siehe lib_i18n.py, WARTUNG.md).
KANONISCH = SITE["sprachen"]["kanonisch"]
LANGS = list(SITE["sprachen"]["ziele"])
RTL = set(SITE["sprachen"]["rtl"])
FLAGGE = SITE["sprachen"]["flaggen"]
SPRACHNAME = SITE["sprachen"]["namen"]


def langswitch_html(page_file, lang):
    """Flaggenleiste (Sprachumschalter) für eine Seite.
    page_file ist der Pfad relativ zur Doku-Wurzel (ohne Sprachpräfix)."""
    depth = page_file.count("/") + (1 if lang != KANONISCH else 0)
    prefix = "../" * depth
    teile = []
    for l in [KANONISCH] + LANGS:
        ziel = page_file if l == KANONISCH else "%s/%s" % (l, page_file)
        cls = ' class="cur"' if l == lang else ""
        teile.append(
            '<a%s href="%s" title="%s" hreflang="%s"><img src="%sflags/%s.svg" alt="%s"></a>'
            % (cls, prefix + ziel, SPRACHNAME[l], l, prefix, FLAGGE[l], l.upper()))
    return '<div class="langs">%s</div>' % "".join(teile)


def esc(t):
    return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def esc_attr(t):
    return esc(t).replace('"', "&quot;")


def serialize(el):
    """Element ohne tail serialisieren (HTML-Serialisierung, UTF-8-Text)."""
    s = etree.tostring(el, encoding="unicode", method="html")
    # tostring hängt den tail an — abschneiden:
    if el.tail:
        assert s.endswith(el.tail)
        s = s[: -len(el.tail)]
    return s


def inner_html(el):
    parts = [esc(el.text) if el.text else ""]
    for c in el:
        parts.append(etree.tostring(c, encoding="unicode", method="html"))
    return "".join(parts)


def open_tag(tag, attrs):
    a = "".join(' %s="%s"' % (k, esc_attr(v)) for k, v in attrs)
    return "<%s%s>" % (tag, a)


def attrs_list(el):
    return [[k, v] for k, v in el.items()]


# ------------------------------------------- Spezifikations-DB (spec/records)
# Jeder Spezifikations-Record (<article class="rec">) liegt als eigene
# JSON-Datei unter _src/spec/records/<GRUPPE>/<ID>.json (Gruppe = die ersten
# beiden Namensbestandteile der ID, z.B. SWS_CORE). Seitenmodelle referenzieren
# Records über rec-ref-Blöcke; load_page() löst sie auf. So bleiben die
# Spezifikationselemente eine eigenständige, seitenunabhängig adressierbare
# Plain-Text-Datenbank (Schlüssel: SWS-ID).

def record_gruppe(rid):
    teile = rid.split("_")
    return "_".join(teile[:2]) if len(teile) >= 3 else "_SONSTIGE"


def record_relpath(rid):
    """Ablagepfad eines Records relativ zu _src/."""
    return "spec/records/%s/%s.json" % (record_gruppe(rid), rid)


def record_hash(rid):
    """SHA1 der Record-Datei (für Veraltet-Erkennung in ai/traces), sonst None."""
    p = os.path.join(SRC, record_relpath(rid))
    if not os.path.exists(p):
        return None
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def load_record(relsrc, srcdir=SRC):
    with open(os.path.join(srcdir, relsrc), encoding="utf-8") as f:
        return json.load(f)


def save_record(rec, srcdir=SRC):
    """rec-Block (ohne tail) als Record-Datei schreiben; liefert relpath."""
    rid = dict(rec["attrs"])["id"]
    rel = record_relpath(rid)
    inhalt = {"id": rid, "attrs": rec["attrs"], "lead": rec.get("lead", ""),
              "blocks": rec["blocks"]}
    pfad = os.path.join(srcdir, rel)
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(inhalt, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return rel


def resolve_recs(blocks, srcdir=SRC):
    """rec-ref-Blöcke in-place zu rec-Blöcken auflösen (rekursiv).
    Das Merkfeld "_src" hält die Herkunftsdatei (für extract/validate)."""
    out = []
    for b in blocks:
        if b["t"] == "rec-ref":
            r = load_record(b["src"], srcdir)
            b = {"t": "rec", "attrs": r["attrs"], "lead": r.get("lead", ""),
                 "blocks": r["blocks"], "tail": b.get("tail", ""),
                 "_src": b["src"]}
        if b["t"] in ("rec", "fold"):
            b = dict(b, blocks=resolve_recs(b["blocks"], srcdir))
        out.append(b)
    return out


def externalize_recs(page, srcdir=SRC):
    """Inverse zu resolve_recs: rec-Blöcke mit Record-ID in die Spezifikations-DB
    schreiben und im Seitenmodell durch rec-ref ersetzen. Nur für Blöcke, deren
    attrs eine id tragen; andere bleiben inline."""
    geschrieben = []

    def walk(blocks):
        out = []
        for b in blocks:
            if b["t"] == "rec" and dict(b["attrs"]).get("id"):
                rel = save_record(b, srcdir)
                geschrieben.append(rel)
                out.append({"t": "rec-ref", "src": rel, "tail": b.get("tail", "")})
            elif b["t"] == "fold":
                out.append(dict(b, blocks=walk(b["blocks"])))
            else:
                out.append(b)
        return out

    page["main"] = walk(page["main"])
    return geschrieben


def load_page(path, srcdir=SRC):
    """Seitenmodell laden, rec-ref-Verweise auflösen. Alle lesenden Skripte
    (generate, validate, build_indexes, i18n_extract) nutzen diesen Weg."""
    with open(path, encoding="utf-8") as f:
        page = json.load(f)
    page["main"] = resolve_recs(page["main"], srcdir)
    return page


def save_page(page, srcdir=SRC):
    """Seitenmodell kanonisch schreiben (Records ausgelagert, ohne Merkfelder)."""
    import copy
    p = copy.deepcopy(page)
    externalize_recs(p, srcdir)
    out = os.path.join(srcdir, "sources", "pages", re.sub(r"\.html$", ".json", p["file"]))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return out


def iter_pages(only=None, srcdir=SRC):
    """Alle Seitenmodelle (aufgelöst) in stabiler Reihenfolge liefern."""
    import glob as _glob
    pages_dir = os.path.join(srcdir, "sources", "pages")
    for p in sorted(_glob.glob(os.path.join(pages_dir, "**", "*.json"), recursive=True)):
        page = load_page(p, srcdir)
        if only and page["file"] not in only:
            continue
        yield page


# ---------------------------------------------------------------- Rendering

def render_blocks(blocks, page_dir_depth, srcdir=SRC):
    out = []
    for b in blocks:
        t = b["t"]
        if t == "html":
            out.append(b["html"])
        elif t == "ai":
            with open(os.path.join(srcdir, b["src"]), encoding="utf-8") as f:
                out.append(f.read().rstrip("\n"))
        elif t == "svg":
            attrs = [[k, v] for k, v in b["wrap_attrs"]]
            out.append(open_tag("div", attrs))
            out.append(b.get("pre", ""))
            with open(os.path.join(srcdir, b["src"]), encoding="utf-8") as f:
                out.append(f.read().rstrip("\n"))
            out.append(b.get("inner_tail", ""))
            out.append("</div>")
        elif t == "rec":
            out.append(open_tag("article", b["attrs"]))
            out.append(esc(b.get("lead", "")))
            out.append(render_blocks(b["blocks"], page_dir_depth, srcdir))
            out.append("</article>")
        elif t == "fold":
            out.append(open_tag("details", b["attrs"]))
            out.append("<summary>")
            out.append(b["summary"])
            out.append("</summary>")
            out.append(esc(b.get("lead", "")))
            out.append(render_blocks(b["blocks"], page_dir_depth, srcdir))
            out.append("</details>")
        elif t == "props":
            out.append(open_tag("table", b["attrs"]))
            for r in b["rows"]:
                out.append("<tr>")
                out.append(open_tag("th", r.get("th_attrs", [])))
                out.append(r["th"])
                out.append("</th>")
                out.append(open_tag("td", r.get("td_attrs", [])))
                out.append(r["td"])
                out.append("</td></tr>")
            out.append("</table>")
        elif t == "params":
            out.append(open_tag("table", b["attrs"]))
            for r in b["rows"]:
                out.append("<tr>")
                for c in r["cells"]:
                    out.append(open_tag(c["tag"], c.get("attrs", [])))
                    out.append(c["html"])
                    out.append("</%s>" % c["tag"])
                out.append("</tr>")
            out.append("</table>")
        else:
            raise ValueError("unbekannter Blocktyp: %r" % t)
        out.append(b.get("tail", ""))
    return "".join(out)


def render_page(page, footers, page_tmpl, srcdir=SRC, lang=KANONISCH):
    """Seite rendern. lang steuert nur das Chrome (html-lang, dir, Umschalter);
    für Sprachbäume muss das Seitenmodell bereits übersetzt und page["file"]
    der Pfad OHNE Sprachpräfix sein (der Aufrufer schreibt nach <lang>/…)."""
    depth = page["file"].count("/") + (1 if lang != KANONISCH else 0)
    prefix = "../" * depth
    body_cls = ' class="%s"' % esc_attr(page["body_class"]) if page.get("body_class") else ""
    main = render_blocks(page["main"], depth, srcdir)
    return page_tmpl % {
        "title": esc(page["title"]),
        "htmllang": lang,
        "dir": ' dir="rtl"' if lang in RTL else "",
        "langswitch": langswitch_html(page["file"], lang),
        "css": prefix + "style.css",
        "js": prefix + "fold.js",
        "home": prefix + "index.html",
        "body_class": body_cls,
        "nav": page["nav_html"],
        "main_lead": esc(page.get("main_lead", "")),
        "main": main,
        "footer": footers[page["footer"]],
    }


PAGE_TEMPLATE_FILE = os.path.join(TMPL_DIR, "page.html.tmpl")


def load_templates(srcdir=SRC):
    with open(os.path.join(srcdir, "templates", "page.html.tmpl"), encoding="utf-8") as f:
        page_tmpl = f.read()
    with open(os.path.join(srcdir, "templates", "footers.json"), encoding="utf-8") as f:
        footers = json.load(f)
    return page_tmpl, footers


# ---------------------------------------------------------------- Vergleich

def _norm_ws(s):
    if s is None:
        return ""
    return s


def dom_equal(e1, e2, path="", lenient=False, errors=None):
    """Strukturvergleich zweier Elementbäume. lenient: Whitespace-only-Texte
    werden auf Ebene von body/header/footer normalisiert."""
    if errors is None:
        errors = []

    def txt(t, lenient_here):
        t = t or ""
        if lenient_here and (t.strip() == ""):
            return ""
        return t

    if e1.tag != e2.tag:
        errors.append("%s: tag %r != %r" % (path, e1.tag, e2.tag))
        return errors
    def norm_attrs(d):
        # lxml serialisiert Leerzeichen in URLs als %20 — äquivalent behandeln
        return {k: (v.replace(" ", "%20") if k == "href" else v) for k, v in d.items()}

    if norm_attrs(dict(e1.attrib)) != norm_attrs(dict(e2.attrib)):
        errors.append("%s<%s>: attrs %r != %r" % (path, e1.tag, dict(e1.attrib), dict(e2.attrib)))
    lenient_here = lenient or (isinstance(e1.tag, str) and e1.tag in ("body", "header", "footer", "html", "head"))
    if txt(e1.text, lenient_here) != txt(e2.text, lenient_here):
        errors.append("%s<%s>: text %r != %r" % (path, e1.tag, (e1.text or "")[:80], (e2.text or "")[:80]))
    c1 = list(e1)
    c2 = list(e2)
    if len(c1) != len(c2):
        errors.append("%s<%s>: children %d != %d" % (path, e1.tag, len(c1), len(c2)))
        return errors
    for i, (a, b) in enumerate(zip(c1, c2)):
        if txt(a.tail, lenient_here) != txt(b.tail, lenient_here):
            errors.append("%s<%s>[%d]: tail %r != %r" % (path, e1.tag, i, (a.tail or "")[:80], (b.tail or "")[:80]))
        dom_equal(a, b, "%s/%s[%d]" % (path, str(a.tag)[:20], i), lenient, errors)
    return errors


def compare_html(file1, html2_text):
    d1 = LH.parse(file1).getroot()
    d2 = LH.document_fromstring(html2_text)
    return dom_equal(d1, d2)
