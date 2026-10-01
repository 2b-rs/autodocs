#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QA-Scan (WARTUNG.md → „QA der Sprachbäume“, Punkt 3): Bezeichner-Scan.

Label-Einträge, deren Schlüssel wie ein API-Identifier aussieht (CamelCase,
`::`, `()`, reine Typ-/Funktionsnamen), dürfen in keiner Sprache verändert
werden — sie müssen identisch „übersetzt“ sein. Findet Einträge, bei denen
ein Übersetzungslauf trotzdem eingegriffen hat.

    python3 _src/tools/scan_bezeichner.py [sprache …]   # Default: alle Ziele

Exit-Code 1, wenn Funde vorliegen.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib_docmodel import SRC, LANGS, KANONISCH

I18N = os.path.join(SRC, "i18n")

IDENTIFIER = re.compile(
    r"^(?:[A-Za-z_][A-Za-z0-9_]*::)+~?[A-Za-z_][A-Za-z0-9_]*(?:\(\))?$"   # ns::Name
    r"|^[a-z]+[A-Z][A-Za-z0-9_]*(?:\(\))?$"                               # camelCase
    r"|^[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+(?:\(\))?$"                      # CamelCase
    r"|^[A-Z0-9_]{3,}$")                                                  # MAKRO_NAME


def main():
    ziele = sys.argv[1:] or [l for l in LANGS if l != KANONISCH]
    funde = 0
    for lang in ziele:
        lab = json.load(open(os.path.join(I18N, lang, "labels.json"), encoding="utf-8"))
        treffer = [(k, txt) for k, txt in sorted(lab.items())
                   if IDENTIFIER.match(k) and txt != k]
        funde += len(treffer)
        print("%s: %d veränderte Bezeichner" % (lang, len(treffer)))
        for k, txt in treffer[:15]:
            print("   %r → %r" % (k, txt))
        if len(treffer) > 15:
            print("   … und %d weitere" % (len(treffer) - 15))
    sys.exit(1 if funde else 0)


if __name__ == "__main__":
    main()
