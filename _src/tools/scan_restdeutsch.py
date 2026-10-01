#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QA-Scan (WARTUNG.md → „QA der Sprachbäume“, Punkt 2): Rest-Deutsch-Scan.

Sucht in den Übersetzungsregistern (i18n/<lang>/segments.json, labels.json)
nach deutschen Überbleibseln — nicht nur Umlaute/ß und „…“-Anführungszeichen,
sondern auch umlautfreie deutsche Stoppwörter (zeigt, zur, zum, nicht, wird,
sowie, bzw., …), weil deutsche Teilsätze sonst unbemerkt in Übersetzungen
überleben. API-Bezeichner und ⟦…⟧-Platzhalter werden vor dem Test entfernt.

    python3 _src/tools/scan_restdeutsch.py [sprache …]  # Default: alle Ziele

Funde sind Verdachtsfälle für manuelle Durchsicht (Wörter wie „die“ existieren
auch anderswo); die Stoppwortliste ist bewusst auf eindeutig deutsche Formen
beschränkt. Exit-Code 1, wenn Funde vorliegen.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib_docmodel import SRC, LANGS, KANONISCH

I18N = os.path.join(SRC, "i18n")

STOPP = re.compile(
    r"\b(zeigt|zur|zum|nicht|wird|werden|sowie|bzw|jedoch|dabei|dafür|dadurch"
    r"|hierzu|außerdem|zunächst|anschließend|über|für|können|müssen|erzeugt"
    r"|liefert|verwendet|erlaubt|beschreibt|gehört|zwischen|innerhalb"
    r"|Verwendung|Hinweis|Beispiel|Rückgabe|Fehlerfall)\b")
UMLAUT = re.compile(r"[äöüÄÖÜß]|„")  # „…“: nur das deutsche „ ist eindeutig
MASKE = re.compile(r"⟦\d+⟧")
IDENT = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*(::[A-Za-z_][A-Za-z0-9_~]*)+\b"
                   r"|\b[a-z]+[A-Z][A-Za-z0-9]*\b")


def verdaechtig(text):
    t = IDENT.sub(" ", MASKE.sub(" ", text))
    m = UMLAUT.search(t) or STOPP.search(t)
    return m.group(0) if m else None


def main():
    ziele = sys.argv[1:] or [l for l in LANGS if l != KANONISCH]
    funde = 0
    for lang in ziele:
        treffer = []
        for name in ("segments.json", "labels.json"):
            eintraege = json.load(open(os.path.join(I18N, lang, name), encoding="utf-8"))
            for k, txt in sorted(eintraege.items()):
                grund = verdaechtig(txt)
                if grund:
                    treffer.append((name, k, grund, txt))
        funde += len(treffer)
        print("%s: %d Verdachtsfälle" % (lang, len(treffer)))
        for name, k, grund, txt in treffer[:15]:
            print("   [%s] %s (%s): %.70s" % (name, k, grund, txt))
        if len(treffer) > 15:
            print("   … und %d weitere" % (len(treffer) - 15))
    sys.exit(1 if funde else 0)


if __name__ == "__main__":
    main()
