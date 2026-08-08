#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EINMALWERKZEUG (August 2026): Rückwirkendes Anlegen der Trace-Dateien
(_src/ai/traces/**) und des Quellenregisters (_src/ai/quellen.json) für den
KI-Bestand.

Für jedes KI-Fragment unter _src/content/ai/ wird eine Trace-Datei erzeugt
(Schema: siehe ai/RICHTLINIEN.md, Abschnitt „Trace-Dateien“). Automatisch
ableitbar sind: Seite, Art, assoziierte/zitierte Spezifikationselemente,
verwendete Quelldokumente, Inline-Diagrammquellen und der Stand der
assoziierten Records (Hash für Veraltet-Erkennung). NICHT rekonstruierbar
sind Prompt, Modell, Wissens-/Annahmenliste und Denk-Transkripte der
ursprünglichen Generierung — diese Felder bleiben null/leer, status="legacy".
Sie füllen sich bei der ersten Regenerierung über ai_workflow.py.

    python3 _src/tools/backfill_traces.py            # legt nur FEHLENDE Traces an
    python3 _src/tools/backfill_traces.py --force    # überschreibt vorhandene
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib_docmodel import SRC, AI_DIR, record_hash as rec_hash

TRACES = os.path.join(SRC, "ai", "traces")
QUELLEN = os.path.join(SRC, "ai", "quellen.json")

ID_RE = re.compile(r"\[((?:SWS|RS|EXP|TR|FO|PRS|TPS)_[A-Za-z0-9_]+)\]")
PDF_RE = re.compile(r'href="(https?://[^"]+?\.pdf)')


def doc_id(url):
    return os.path.basename(url).rsplit(".pdf", 1)[0]


def doc_typ(did):
    for t in ("SWS", "RS", "EXP", "TR", "TPS", "PRS"):
        if "_%s_" % t in did:
            return t
    return "sonstig"


def main():
    force = "--force" in sys.argv
    quellen = {}
    if os.path.exists(QUELLEN):
        quellen = json.load(open(QUELLEN, encoding="utf-8"))
    n_neu, n_uebersprungen = 0, 0

    for frag in sorted(glob.glob(os.path.join(AI_DIR, "**", "*.html"), recursive=True)):
        rel = os.path.relpath(frag, SRC)                  # content/ai/<dir>/<stem>.html
        unter = os.path.relpath(frag, AI_DIR)             # <dir>/<stem>.html
        stem = unter[:-len(".html")]
        trace_pfad = os.path.join(TRACES, stem + ".json")
        if os.path.exists(trace_pfad) and not force:
            n_uebersprungen += 1
            continue

        html = open(frag, encoding="utf-8").read()
        seite = os.path.dirname(unter) + ".html"
        name = os.path.basename(stem)

        # Art + direkt assoziiertes Element aus dem Namensschema
        m = re.match(r"^rec_(.+)_\d+$", name)
        direkt = [m.group(1)] if m else []
        cls = re.search(r'^<div class="([^"]*)"', html)
        art = "usage" if m else ("guide" if "guide" in (cls.group(1) if cls else "")
                                 else "abschnitt")

        zitate = sorted(set(ID_RE.findall(html)))
        elemente = sorted(set(direkt) | {z for z in zitate if rec_hash(z)})

        # Quelldokumente registrieren
        frag_quellen = set()
        for url in PDF_RE.findall(html):
            basis = url.split("#")[0]
            did = doc_id(basis)
            frag_quellen.add(did)
            eintrag = quellen.setdefault(did, {
                "titel": None, "typ": doc_typ(did), "url": basis,
                "status": "belegt (automatisch registriert)"})
            eintrag.setdefault("url", basis)

        # Inline-Diagrammquellen (<stem>.<diag-id>.dot|.seq.json)
        diagramme = {}
        basis = frag[:-len(".html")]
        for q in sorted(glob.glob(basis + ".*.dot") + glob.glob(basis + ".*.seq.json")):
            diagramme[os.path.relpath(q, SRC)] = {
                "entscheidung": None, "annahmen": [], "transkript": None}

        trace = {
            "fragment": rel,
            "seite": seite,
            "art": art,
            "elemente": elemente,
            "zitate": zitate,
            "quellen": sorted(frag_quellen),
            "wissen": [],
            "annahmen": [],
            "prompt": None,
            "modell": None,
            "policy_version": None,
            "laeufe": [],
            "diagramme": diagramme,
            "status": "legacy",
            "elemente_stand": {e: rec_hash(e) for e in elemente},
        }
        os.makedirs(os.path.dirname(trace_pfad), exist_ok=True)
        with open(trace_pfad, "w", encoding="utf-8") as f:
            json.dump(trace, f, ensure_ascii=False, indent=1)
            f.write("\n")
        n_neu += 1

    os.makedirs(os.path.dirname(QUELLEN), exist_ok=True)
    with open(QUELLEN, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(quellen.items())), f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("Traces angelegt: %d, übersprungen (vorhanden): %d, Quellenregister: %d Dokumente"
          % (n_neu, n_uebersprungen, len(quellen)))


if __name__ == "__main__":
    main()
