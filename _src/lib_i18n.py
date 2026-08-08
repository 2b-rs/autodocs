#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lib_i18n.py — Gemeinsame Bausteine der Mehrsprachigkeit (siehe WARTUNG.md, Kap. i18n).

Sprachmodell:
  Deutsch (de) ist die kanonische Quellsprache und liegt an der Doku-Wurzel.
  Jede weitere Sprache erhält einen vollständigen Spiegelbaum unter <lang>/
  (en/, es/, fr/, ru/, ar/, hi/, ko/, zh/). Alle relativen Links funktionieren
  dort unverändert, weil die Baumstruktur identisch ist.

Übersetzt wird ausschließlich selbst erzeugter Inhalt:
  - Segment-Register  _src/i18n/segments.de.json   (maskierte Block-Prosa)
                      _src/i18n/<lang>/segments.json
  - Diagramm-Register _src/i18n/labels.de.json     (dot-/seq-Beschriftungen)
                      _src/i18n/<lang>/labels.json
  - UI-Register       _src/i18n/ui.json            (Abschnittstitel, Kind-Labels,
                                                    Footer, Header, Badges)
NICHT übersetzt werden: englische Original-Spezifikationstexte (rec-Inhalte ohne
deutschen Text), Linktexte (in Platzhaltern geschützt), Code, Namen von
Spezifikationselementen, SWS-Kennungen.

Maskierung: In jedem Block-Segment werden geschützte Inline-Elemente
(<a>, <code>, <span>, <svg>, <br>, <img>) positionsgetreu durch ⟦k⟧ ersetzt.
Der Segmentschlüssel ist sha1(maskierter Text)[:12]. Beim Einsetzen einer
Übersetzung werden die Platzhalter durch die Original-Tags DES JEWEILIGEN
Elements ersetzt — Linkziele bleiben dadurch je Fundstelle korrekt.
"""
import hashlib
import json
import os
import re

from lxml import html as LH

from lib_docmodel import (SRC, ROOT, esc, LANGS, RTL, FLAGGE, SPRACHNAME,  # noqa: F401
                          langswitch_html)  # noqa: F401 — Re-Export

I18N = os.path.join(SRC, "i18n")

PROTECT = {"a", "code", "svg", "br", "span", "img"}
# span-Klassen, deren deutscher Textinhalt trotz Schutz übersetzt wird
# (als eigenständige Segmente; vis-*-Badges und englische Spec-Zitate
# bleiben unberührt, da nur deutsch erkannter Text aufgenommen wird):
SPAN_UEBERSETZBAR = {"dim", "chip", "interp"}
BLOCKTAGS = {"p", "li", "h3", "h4", "h5", "h6", "figcaption", "dt", "dd", "caption"}
# Tabellenzellen in rohen html-Blöcken (z.B. eingebettete props-Tabellen)
# sind eigene Segmente; in props/params-Zellfragmenten greift zellmodus.
ZELLTAGS = {"td", "th"}

_DE_WORT = re.compile(
    r"(?i)(?<![\w:])(der|die|das|den|dem|des|ein|eine|einer|eines|und|oder|nicht|"
    r"wird|werden|ist|sind|kann|können|muss|müssen|soll|sollen|nur|auch|mit|auf|"
    r"aus|bei|nach|über|unter|ohne|zwischen|sowie|bzw|zurück|liefert|gibt|siehe|"
    r"gemäß|laut|dieser|diese|dieses|alle|keine|wenn|dann|wie|vom|zum|zur|im|am|"
    r"Funktionen|Klassen|Seiten|freie|KI-generierte?|Strukturen|Verzeichnis|Spezifikation|Mitglieder|"
    r"beim|dabei|dazu|dafür|hier|noch|bereits|jeweils|sonst|z\.\u2009?B\.)(?![\w:])")


def ist_deutsch(text):
    """Heuristik: enthält der Text deutsche Sprache? (Umlaute oder Stoppwörter)"""
    return bool(re.search(r"[äöüßÄÖÜ]", text) or _DE_WORT.search(text))


def span_uebersetzbar(el):
    """span, dessen Inhalt als eigenes Segment übersetzt wird: Klasse in
    SPAN_UEBERSETZBAR, keine geschützten Kinder (em/strong bleiben als
    Markup im Segment), deutscher Textinhalt."""
    if el.tag != "span" or (el.get("class") or "") not in SPAN_UEBERSETZBAR:
        return False
    if any(isinstance(k.tag, str) and k.tag in PROTECT
           for k in el.iterdescendants()):
        return False
    return bool(el.text_content().strip())


def link_uebersetzbar(el):
    """Klassenloser interner Link mit selbst verfasstem deutschem Linktext
    (z.B. „Sequenzdiagramm „…““). swsref/docref/cppref tragen Klassen und
    bleiben unberührt; deutsch heißt hier: Detektor ODER deutsche
    Anführungszeichen (Titel wie „Anwendungskontext“ ohne Stoppwort).
    Kinder sind erlaubt, sofern sie in PROTECT liegen (z.B. <code>) —
    sie werden über maskiere() zu Platzhaltern."""
    if el.tag != "a" or el.get("class"):
        return False
    if any(not isinstance(k.tag, str) or k.tag not in PROTECT for k in el):
        return False
    t = el.text_content()
    return bool(t and (ist_deutsch(t) or "„" in t))


def hat_prosa(text):
    return bool(re.search(r"[A-Za-zÄÖÜäöüß]{2}", text))


# ------------------------------------------------------------- Maskierung

def maskiere(el):
    """Element -> (maskierter innerHTML-Text, Liste der geschützten Tags).
    Textknoten werden HTML-escaped, damit der maskierte Text gültiges
    innerHTML ist (wichtig für Prosa wie „&lt;SampleType const&gt;“)."""
    tags = []
    out = [esc(el.text) if el.text else ""]
    for k in el:
        if isinstance(k.tag, str) and k.tag in PROTECT:
            tags.append(LH.tostring(k, encoding="unicode", with_tail=False))
            out.append("\u27e6%d\u27e7" % (len(tags) - 1))
        else:
            # em/strong/i/u/sub/sup … bleiben als Markup im Segmenttext
            out.append(LH.tostring(k, encoding="unicode", with_tail=False))
        out.append(esc(k.tail) if k.tail else "")
    return "".join(out), tags


def seg_id(masked):
    return hashlib.sha1(masked.encode("utf-8")).hexdigest()[:12]


def entmaskiere(masked, tags):
    """Übersetzten maskierten Text + Original-Tags -> innerHTML-Text."""
    def repl(m):
        i = int(m.group(1))
        return tags[i] if i < len(tags) else m.group(0)
    return re.sub(r"\u27e6(\d+)\u27e7", repl, masked)


def setze_inner(el, inner_html):
    """innerHTML eines Elements ersetzen (Text + Kinder)."""
    for k in list(el):
        el.remove(k)
    el.text = None
    if not inner_html:
        return
    frag = LH.fragment_fromstring(inner_html, create_parent="x")
    el.text = frag.text
    for k in list(frag):
        el.append(k)


def leaf_segmente(wrapper, zellmodus=False):
    """Elemente liefern, deren innerHTML als Segment behandelt wird."""
    leaves = []
    for el in wrapper.iter():
        if el is wrapper or not isinstance(el.tag, str):
            continue
        if (el.tag in BLOCKTAGS or el.tag in ZELLTAGS) and not any(
                isinstance(k.tag, str)
                and (k.tag in BLOCKTAGS or k.tag in ZELLTAGS)
                for k in el.iterdescendants()):
            leaves.append(el)
    if not leaves and zellmodus:
        leaves = [wrapper]
    return leaves


# ------------------------------------------------------------- Register

def lade_register(lang):
    """(segmente, labels, ui) der Sprache laden; fehlende Teile leer."""
    def _lade(p):
        return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    seg = _lade(os.path.join(I18N, lang, "segments.json"))
    lab = _lade(os.path.join(I18N, lang, "labels.json"))
    ui_all = _lade(os.path.join(I18N, "ui.json"))
    return seg, lab, ui_all.get(lang, {})


def lade_soll():
    """Segment-IDs, die übersetzt werden sollen (deutsches Quellregister)."""
    p = os.path.join(I18N, "segments.de.json")
    return set(json.load(open(p, encoding="utf-8"))) if os.path.exists(p) else set()


# ------------------------------------------------------------- Transformation

class Statistik:
    """Zählt Treffer und fehlende Übersetzungen. soll = Menge der Segment-IDs,
    die übersetzt werden SOLLEN (segments.de.json) — nur diese zählen als
    fehlend; englische Original-Spezifikationstexte bleiben unberücksichtigt."""

    def __init__(self, soll=None):
        self.treffer = 0
        self.soll = soll
        self.fehlend = {}

    def fehlt(self, sid, masked):
        if self.soll is None or sid in self.soll:
            self.fehlend.setdefault(sid, masked)


# Kapitel-/Quellen-Linktexte (a.docref): deutsche Verpackung lokalisieren,
# Original-Kapiteltitel innerhalb der Anführungszeichen bleiben wörtlich.
_RE_DR_ZITAT = re.compile(r"\u201e([^\u201c\u201d\"]*)[\u201c\u201d\"]")
_RE_DR_KAPITEL = re.compile(r"\bKapitel\s+(\d+)")
_RE_DR_KAP = re.compile(r"\bKap\.\s*(\d+)")


def lokalisiere_docref(text, dr):
    """Zitatzeichen, „Kapitel n“/„Kap. n“ und [verknüpfte API] je Sprache."""
    if text.strip() == "[verknüpfte API]":
        return text.replace("[verknüpfte API]", dr["api_link"])
    text = _RE_DR_ZITAT.sub(
        lambda m: dr["zitat_a"] + m.group(1) + dr["zitat_z"], text)
    text = _RE_DR_KAPITEL.sub(
        lambda m: dr["kapitel_fmt"].replace("{n}", m.group(1)), text)
    text = _RE_DR_KAP.sub(
        lambda m: dr["kap_fmt"].replace("{n}", m.group(1)), text)
    return text


def uebersetze_wrapper(wrapper, seg, ui, stat, zellmodus=False):
    """Segmente + strukturelle UI-Teile in einem geparsten Fragment ersetzen."""
    # Strukturell: h1/h2-Abschnittstitel, Fold-lose h2, span.kind
    sect = ui.get("sect", {})
    kind = ui.get("kind", {})
    dr = ui.get("docref")
    for el in wrapper.iter():
        if not isinstance(el.tag, str):
            continue
        if el.tag == "span" and el.get("class") == "kind":
            neu = kind.get((el.text or "").strip())
            if neu:
                el.text = neu
        elif el.tag == "h2" and "sect" in (el.get("class") or ""):
            kern = (el.text or "").strip()
            neu = sect.get(kern)
            if neu:
                el.text = neu + (" " if len(el) else "")
        elif span_uebersetzbar(el) and ist_deutsch(el.text_content()):
            # Geschützte Kurztext-Spans (Statistiken, Chips, Interpretationen):
            # eigener Registereintrag, da sie in Eltern-Segmenten nur als
            # Platzhalter erscheinen (siehe PROTECT/maskiere).
            masked, _tags = maskiere(el)
            m = masked.strip()
            sid = seg_id(m)
            if sid in seg:
                setze_inner(el, seg[sid])
                stat.treffer += 1
            else:
                stat.fehlt(sid, m)
        elif link_uebersetzbar(el):
            # Klassenlose interne Links mit deutschem Linktext: ebenfalls
            # eigene Registereinträge (in Eltern-Segmenten Platzhalter).
            # Geschützte Kinder (<code> …) werden maskiert und nach der
            # Übersetzung wieder eingesetzt.
            masked, tags = maskiere(el)
            m = masked.strip()
            sid = seg_id(m)
            if sid in seg:
                setze_inner(el, entmaskiere(seg[sid], tags))
                stat.treffer += 1
            else:
                stat.fehlt(sid, m)
        elif (el.tag == "a" and "docref" in (el.get("class") or "")
              and dr and el.text and not len(el)):
            el.text = lokalisiere_docref(el.text, dr)
    # Segmente
    for el in leaf_segmente(wrapper, zellmodus=zellmodus):
        masked, tags = maskiere(el)
        m = masked.strip()
        if not m or not hat_prosa(re.sub(r"\u27e6\d+\u27e7", "", m)):
            continue
        sid = seg_id(m)
        if sid in seg:
            fuehrend = masked[: len(masked) - len(masked.lstrip())]
            folgend = masked[len(masked.rstrip()):]
            setze_inner(el, fuehrend + entmaskiere(seg[sid], tags) + folgend)
            stat.treffer += 1
        else:
            stat.fehlt(sid, m)


def uebersetze_html(raw, seg, ui, stat, zellmodus=False):
    """HTML-String (Block/Zelle/Fragment) übersetzen -> HTML-String."""
    if not raw or not raw.strip():
        return raw
    wrap = LH.fragment_fromstring(raw, create_parent="x")
    uebersetze_wrapper(wrap, seg, ui, stat, zellmodus=zellmodus)
    out = esc(wrap.text) if wrap.text else ""
    for k in wrap:
        out += LH.tostring(k, encoding="unicode", with_tail=True)
    return out


def globale_ersetzungen(text, ui):
    """Feste Zeichenketten (Badge-Texte u. ä.) im fertigen HTML ersetzen."""
    for alt, neu in ui.get("global", {}).items():
        text = text.replace(alt, neu)
    return text


# ------------------------------------------------------------- Diagramme

_DOT_ATTR = re.compile(r'\b(label|xlabel|tooltip|labeltooltip|headlabel|taillabel)\s*=\s*"((?:[^"\\]|\\.)*)"')


def dot_labels(dot_text):
    """Alle Beschriftungswerte einer dot-Quelle (roh, mit \\n-Escapes)."""
    return [m.group(2) for m in _DOT_ATTR.finditer(dot_text)]


def uebersetze_dot(dot_text, lab):
    def repl(m):
        neu = lab.get(m.group(2))
        return '%s="%s"' % (m.group(1), neu) if neu else m.group(0)
    return _DOT_ATTR.sub(repl, dot_text)


# Nicht übersetzbare seq-Schlüssel: Links und Renderer-Schlüsselwörter
# (art/typ/pfeil sind Enums, klasse ist eine CSS-Klasse). Indizes
# (von/nach/teilnehmer/ueber) sind Zahlen und fallen von selbst durch.
_SEQ_SKIP = {"href", "art", "typ", "pfeil", "klasse"}


def seq_strings(spec):
    """Alle übersetzbaren Strings einer seq-Spezifikation (rekursiv)."""
    SKIP = _SEQ_SKIP
    out = []

    def walk(x, key=None):
        if isinstance(x, dict):
            for k, v in x.items():
                if k not in SKIP:
                    walk(v, k)
        elif isinstance(x, list):
            for v in x:
                walk(v, key)
        elif isinstance(x, str):
            out.append(x)
    walk(spec)
    return out


def uebersetze_seq(spec, lab):
    SKIP = _SEQ_SKIP

    def walk(x, key=None):
        if isinstance(x, dict):
            return {k: (v if k in SKIP else walk(v, k)) for k, v in x.items()}
        if isinstance(x, list):
            return [walk(v, key) for v in x]
        if isinstance(x, str):
            return lab.get(x, x)
        return x
    return walk(spec)


# ------------------------------------------------------------- Seitenmodell

def uebersetze_nav(nav_html, ui):
    """Brotkrumen: nur das Wort „Start“ (Link oder blanker Text) übersetzen."""
    start = ui.get("nav_start")
    if not start or "Start" not in nav_html:
        return nav_html
    wrap = LH.fragment_fromstring(nav_html, create_parent="x")
    if wrap.text and wrap.text.strip() == "Start":
        wrap.text = wrap.text.replace("Start", start)
    for a in wrap.iter("a"):
        if (a.text or "").strip() == "Start" and (a.get("href") or "").endswith("index.html"):
            a.text = a.text.replace("Start", start)
    out = esc(wrap.text) if wrap.text else ""
    for k in wrap:
        out += LH.tostring(k, encoding="unicode", with_tail=True)
    return out


def _uebersetze_fragment(raw, lang, seg, ui, stat, inline_svgs):
    """KI-Fragment übersetzen; ggf. übersetzte Inline-Diagramme einsetzen."""
    wrap = LH.fragment_fromstring(raw, create_parent="x")
    for did, svg_text in inline_svgs.items():
        for el in wrap.iterdescendants():
            if el.get("id") == did:
                alte = [k for k in el
                        if isinstance(k.tag, str) and k.tag.split("}")[-1] == "svg"]
                if len(alte) == 1:
                    neu = LH.fragment_fromstring(svg_text)
                    neu.tail = alte[0].tail
                    el.replace(alte[0], neu)
                break
    uebersetze_wrapper(wrap, seg, ui, stat)
    out = esc(wrap.text) if wrap.text else ""
    for k in wrap:
        out += LH.tostring(k, encoding="unicode", with_tail=True)
    return out


def uebersetze_seite(page, lang, seg, ui, stat, srcdir=SRC):
    """Übersetzte Kopie eines Seitenmodells erzeugen (Original bleibt unberührt).
    ai-Blöcke werden zu html-Blöcken materialisiert; svg-Blöcke zeigen auf
    übersetzte Diagramme unter i18n/<lang>/, sofern vorhanden (sonst Fallback)."""
    import copy
    p = copy.deepcopy(page)
    p["nav_html"] = uebersetze_nav(p["nav_html"], ui)

    def inline_svgs_fuer(src):
        # content/ai/<dir>/<stem>.html -> i18n/<lang>/inline/<dir>/<stem>.<did>.svg
        rel = os.path.relpath(src, "content/ai")
        stem = os.path.splitext(os.path.basename(rel))[0]
        d = os.path.join(I18N, lang, "inline", os.path.dirname(rel))
        out = {}
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.startswith(stem + ".") and f.endswith(".svg"):
                    did = f[len(stem) + 1:-len(".svg")]
                    out[did] = open(os.path.join(d, f), encoding="utf-8").read().rstrip("\n")
        return out

    def blocks(bs):
        for b in bs:
            t = b["t"]
            if t == "html":
                b["html"] = uebersetze_html(b["html"], seg, ui, stat)
            elif t == "ai":
                raw = open(os.path.join(srcdir, b["src"]), encoding="utf-8").read().rstrip("\n")
                neu = _uebersetze_fragment(raw, lang, seg, ui, stat,
                                           inline_svgs_fuer(b["src"]))
                tail = b.get("tail", "")
                b.clear()
                b.update({"t": "html", "html": neu, "tail": tail})
            elif t == "svg":
                kand = os.path.join("i18n", lang, b["src"])
                if os.path.exists(os.path.join(srcdir, kand)):
                    b["src"] = kand
            elif t in ("rec", "fold"):
                if t == "fold":
                    b["summary"] = uebersetze_html(b["summary"], seg, ui, stat)
                blocks(b["blocks"])
            elif t == "props":
                for r in b["rows"]:
                    r["th"] = uebersetze_html(r["th"], seg, ui, stat, zellmodus=True)
                    r["td"] = uebersetze_html(r["td"], seg, ui, stat, zellmodus=True)
            elif t == "params":
                for r in b["rows"]:
                    for c in r["cells"]:
                        c["html"] = uebersetze_html(c["html"], seg, ui, stat, zellmodus=True)

    blocks(p["main"])
    return p
