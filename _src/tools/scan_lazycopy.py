#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QA-Scan (WARTUNG.md → „QA der Sprachbäume“, Punkt 1): Lazy-Copy-Scan.

Findet Übersetzungseinträge, die identisch zum deutschen Original sind —
typisch, wenn ein Übersetzungslauf Zeilen ungefüllt durchgereicht hat.
Legitim identische Einträge stehen in i18n/whitelist.json (Segmente) bzw.
i18n/whitelist_labels.json (Labels) und werden übersprungen; ebenso Labels,
die wie API-Bezeichner aussehen (dürfen sich nie ändern, siehe
scan_bezeichner.py).

    python3 _src/tools/scan_lazycopy.py [sprache …]     # Default: alle Ziele

Exit-Code 1, wenn Funde vorliegen.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib_docmodel import SRC, LANGS, KANONISCH

I18N = os.path.join(SRC, "i18n")
IDENT_RE = re.compile(r"^[A-Za-z0-9_:~<>,() \[\]&*.+=-]+$")


def lade(pfad):
    with open(pfad, encoding="utf-8") as f:
        return json.load(f)


def main():
    ziele = sys.argv[1:] or [l for l in LANGS if l != KANONISCH]
    seg_de = lade(os.path.join(I18N, "segments.%s.json" % KANONISCH))
    wl_seg = set(lade(os.path.join(I18N, "whitelist.json")))
    wl_lab = set(lade(os.path.join(I18N, "whitelist_labels.json")))
    funde = 0
    for lang in ziele:
        seg = lade(os.path.join(I18N, lang, "segments.json"))
        lab = lade(os.path.join(I18N, lang, "labels.json"))
        treffer = []
        for sid, txt in sorted(seg.items()):
            de = seg_de.get(sid, {}).get("m")
            if de is not None and txt == de and de not in wl_seg:
                treffer.append(("segment", sid, de))
        for key, txt in sorted(lab.items()):
            if txt == key and key not in wl_lab and not IDENT_RE.match(key):
                treffer.append(("label", key, key))
        funde += len(treffer)
        print("%s: %d Lazy-Copies" % (lang, len(treffer)))
        for art, k, de in treffer[:15]:
            print("   [%s] %s: %.70s" % (art, k, de))
        if len(treffer) > 15:
            print("   … und %d weitere" % (len(treffer) - 15))
    sys.exit(1 if funde else 0)


if __name__ == "__main__":
    main()
