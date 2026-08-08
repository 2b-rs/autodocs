#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
i18n_extract.py — Deutsches Quellregister der Mehrsprachigkeit aufbauen.

Erzeugt:
  _src/i18n/segments.de.json    {sid: {"m": maskierter Text, "n": Anzahl,
                                       "ctx": ["ai"|"chrome"|"rec", …]}}
  _src/i18n/labels.de.json      {Label-Rohtext: Anzahl}   (dot + seq)
  _src/i18n/kandidaten.json     ausgeschlossene rec-/chrome-Segmente (Kuratierung)
  _src/i18n/kandidaten_labels.json  ausgeschlossene Diagramm-Labels (Kuratierung)

Aufnahmeregeln:
  ai      alle Prosa-Segmente (vollständig selbst verfasst, deutsch)
  chrome  (Seiten-HTML außerhalb <article class="rec">) nur deutsch erkannte
          Segmente + Whitelist — Kartentitel/Namen bleiben unangetastet
  rec     nur deutsch erkannte Segmente + Whitelist — englische Original-
          Spezifikationstexte gelangen so NIE ins Register
  labels  deutsch erkannte Diagrammbeschriftungen + Label-Whitelist

Whitelists (von Hand gepflegt, exakte maskierte Texte bzw. Label-Rohtexte):
  _src/i18n/whitelist.json          ["…", …]
  _src/i18n/whitelist_labels.json   ["…", …]
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import html as LH

from lib_docmodel import SRC, PAGES_DIR, AI_DIR, DIAG_DIR, iter_pages
from lib_i18n import (I18N, leaf_segmente, maskiere, seg_id, ist_deutsch,
                      hat_prosa, dot_labels, seq_strings, span_uebersetzbar,
                      link_uebersetzbar)
from lib_docmodel import esc

_PLATZHALTER = re.compile(r"\u27e6\d+\u27e7")


def _lade_liste(name):
    p = os.path.join(I18N, name)
    return set(json.load(open(p, encoding="utf-8"))) if os.path.exists(p) else set()


def main():
    os.makedirs(I18N, exist_ok=True)
    whitelist = _lade_liste("whitelist.json")
    whitelist_labels = _lade_liste("whitelist_labels.json")

    seg = {}          # sid -> {"m","n","ctx"}
    kandidaten = {}   # masked -> Anzahl (ausgeschlossene rec/chrome-Segmente)

    def nimm(masked, ctx):
        m = masked.strip()
        if not m or not hat_prosa(_PLATZHALTER.sub("", m)):
            return
        if ctx != "ai" and not (ist_deutsch(_PLATZHALTER.sub(" ", m)) or m in whitelist):
            kandidaten[m] = kandidaten.get(m, 0) + 1
            return
        sid = seg_id(m)
        e = seg.setdefault(sid, {"m": m, "n": 0, "ctx": []})
        e["n"] += 1
        if ctx not in e["ctx"]:
            e["ctx"].append(ctx)

    def nimm_html(raw, ctx, zellmodus=False):
        if not raw or not raw.strip():
            return
        wrap = LH.fragment_fromstring(raw, create_parent="x")
        for el in leaf_segmente(wrap, zellmodus=zellmodus):
            masked, _ = maskiere(el)
            nimm(masked, ctx)
        # Geschützte Kurztext-Spans (dim/chip): eigene Segmente, da sie in
        # Eltern-Segmenten nur als Platzhalter erscheinen. Nur deutsch
        # erkannte oder gewhitelistete Texte — englische Spec-Zitate in
        # span.dim gelangen so nie ins Register (und nicht in kandidaten).
        for sp in wrap.iter("span"):
            if span_uebersetzbar(sp):
                masked, _ = maskiere(sp)
                m = masked.strip()
                if m and (ist_deutsch(sp.text_content()) or m in whitelist):
                    nimm(m, ctx)
        # Klassenlose interne Links mit deutschem Linktext (z.B.
        # „Sequenzdiagramm „…““): eigene Segmente, da <a> geschützt ist.
        for a in wrap.iter("a"):
            if link_uebersetzbar(a):
                masked, _ = maskiere(a)
                nimm(masked.strip(), ctx)

    def blocks(bs, ctx):
        for b in bs:
            t = b["t"]
            if t == "html":
                nimm_html(b["html"], ctx)
            elif t == "rec":
                blocks(b["blocks"], "rec")
            elif t == "fold":
                blocks(b["blocks"], ctx)
            elif t == "props":
                for r in b["rows"]:
                    nimm_html(r["th"], ctx, zellmodus=True)
                    nimm_html(r["td"], ctx, zellmodus=True)
            elif t == "params":
                for r in b["rows"]:
                    for c in r["cells"]:
                        nimm_html(c["html"], ctx, zellmodus=True)

    for page in iter_pages():
        blocks(page["main"], "chrome")

    for p in sorted(glob.glob(os.path.join(AI_DIR, "**", "*.html"), recursive=True)):
        nimm_html(open(p, encoding="utf-8").read(), "ai")

    # ---------------------------------------------------------- Diagramme
    lab = {}
    kandidaten_lab = {}

    def nimm_label(s):
        if not s.strip() or not hat_prosa(s):
            return
        pruef = s.replace("\\n", " ")
        if ist_deutsch(pruef) or s in whitelist_labels:
            lab[s] = lab.get(s, 0) + 1
        else:
            kandidaten_lab[s] = kandidaten_lab.get(s, 0) + 1

    dot_dateien = (glob.glob(os.path.join(DIAG_DIR, "**", "*.dot"), recursive=True)
                   + glob.glob(os.path.join(AI_DIR, "**", "*.dot"), recursive=True))
    for p in sorted(dot_dateien):
        for s in dot_labels(open(p, encoding="utf-8").read()):
            nimm_label(s)
    seq_dateien = (glob.glob(os.path.join(DIAG_DIR, "**", "*.seq.json"), recursive=True)
                   + glob.glob(os.path.join(AI_DIR, "**", "*.seq.json"), recursive=True))
    for p in sorted(seq_dateien):
        for s in seq_strings(json.load(open(p, encoding="utf-8"))):
            nimm_label(s)

    def dump(name, obj):
        with open(os.path.join(I18N, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
        print("%-28s %6d Einträge" % (name, len(obj)))

    dump("segments.de.json", seg)
    dump("labels.de.json", lab)
    dump("kandidaten.json", dict(sorted(kandidaten.items(), key=lambda kv: -kv[1])))
    dump("kandidaten_labels.json", dict(sorted(kandidaten_lab.items(), key=lambda kv: -kv[1])))
    print("Prosa-Volumen Register: %.2f MB"
          % (sum(len(e["m"]) * 1 for e in seg.values()) / 1e6))


if __name__ == "__main__":
    main()
