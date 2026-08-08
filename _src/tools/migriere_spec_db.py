#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EINMALWERKZEUG (August 2026): Migration der Spezifikations-Records aus den
Seitenmodellen in die eigenständige Spezifikations-DB (_src/spec/records/).

Alle rec-Blöcke mit ID werden als Einzeldateien
    _src/spec/records/<GRUPPE>/<ID>.json
abgelegt und in den Seitenmodellen durch rec-ref-Blöcke ersetzt. Die
Generierung ist davon byte-neutral (load_page löst die Verweise auf).

    python3 _src/tools/migriere_spec_db.py

Danach: python3 _src/generate.py --check   (muss „Abweichungen: 0“ melden)
        python3 _src/validate.py
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib_docmodel import PAGES_DIR, externalize_recs


def main():
    n_pages, n_recs = 0, 0
    for p in sorted(glob.glob(os.path.join(PAGES_DIR, "**", "*.json"), recursive=True)):
        with open(p, encoding="utf-8") as f:
            page = json.load(f)
        rels = externalize_recs(page)
        if not rels:
            continue
        n_pages += 1
        n_recs += len(rels)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(page, f, ensure_ascii=False, indent=1)
            f.write("\n")
    print("migriert: %d Records aus %d Seiten nach spec/records/" % (n_recs, n_pages))


if __name__ == "__main__":
    main()
