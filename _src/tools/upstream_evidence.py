#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""upstream_evidence.py — Rohbeobachtungen je Dokument/ID/Backend persistieren.

Umsetzung des in ``NEXTSTEPS.md`` beschriebenen Prinzips "Preserve raw
evidence at every stage": Bevor eine Aenderung an ``spec_scrape.py``
(Parser, Regionen, Heuristiken) beurteilt werden kann, muss der VORHER-
Zustand als unveraenderliche Beobachtung vorliegen — sonst laesst sich eine
Regression nicht von einer Verbesserung unterscheiden.

Schreibt fuer jede lokal definierte ID pro Dokument und Backend eine Datei
unter ``_src/spec/upstream/evidence/<document>/<id>/<backend>.json`` mit:

  * dem rohen Text-Ausschnitt, den ``_record_slice`` fuer diese ID liefert
    (unveraendert, VOR jeder Normalisierung/Reparatur),
  * dem daraus geparsten Record (``parse_record``),
  * Seiten- und Commit-Provenienz (git rev, Zeitpunkt).

Beobachtungen werden additiv unter dem aktuellen Commit abgelegt
(``observations`` Liste, neueste zuerst) — bestehende Beobachtungen werden
NICHT ueberschrieben. So bleibt nachvollziehbar, wie sich die Extraktion
einer ID ueber mehrere Parser-Aenderungen hinweg entwickelt hat.

Aufruf (immer vom Repo-Wurzelverzeichnis)
-----------------------------------------
    python3 _src/tools/upstream_evidence.py --doc AUTOSAR_FO_RS_Diagnostics
    python3 _src/tools/upstream_evidence.py --doc AUTOSAR_FO_RS_Diagnostics --id RS_Diag_04005
    python3 _src/tools/upstream_evidence.py --all-rs-docs --backend pypdf

Fuer Parallelisierung ueber mehrere Dokumente: mehrere Prozesse mit je
einem ``--doc`` starten (Jobkontrolle im Shell-Skript, nicht in diesem
Werkzeug). Jeder Prozess schreibt nur in seinen eigenen Dokument-Unterbaum,
daher sind parallele Läufe ueber verschiedene Dokumente kollisionsfrei.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
TOOLS = SRC / "tools"
sys.path.insert(0, str(TOOLS))
import spec_scrape as ss

EVIDENCE = SRC / "spec" / "upstream" / "evidence"


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _git_rev():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              cwd=str(SRC.parent), capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return None


def _atomic_write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp-%d" % os.getpid())
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def local_ids_for_doc(doc_stem, pattern="^RS_", backend="pypdf"):
    pdf = ss.PDF_CACHE / (doc_stem + ".pdf")
    idx = ss.phase_ids([pdf], pattern=pattern, include_refs=False, backend=backend)
    info = idx[doc_stem + ".pdf"]
    return info, ss.pdf_pages(pdf, backend)


def capture_one(doc_stem, rid, pageno, pages, backend, rev, ts):
    raw_page = ss.strip_noise(pages[pageno - 1])
    normalized = ss.normalize_layout(raw_page)
    chunk = ss._record_slice(normalized, rid)
    parsed = ss.parse_record(pages[pageno - 1], rid)
    return {
        "schema": "upstream-evidence-observation@v1",
        "captured_at": ts,
        "git_rev": rev,
        "backend": backend,
        "document": doc_stem,
        "page": pageno,
        "id": rid,
        "raw_slice": chunk,
        "parsed": parsed,
    }


def write_evidence(doc_stem, rid, observation):
    path = EVIDENCE / doc_stem / rid / (observation["backend"] + ".json")
    existing = {"schema": "upstream-evidence@v1", "document": doc_stem, "id": rid,
                "backend": observation["backend"], "observations": []}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    obs = existing.setdefault("observations", [])
    last = obs[0] if obs else None
    if last and last.get("raw_slice") == observation["raw_slice"] \
            and last.get("parsed") == observation["parsed"]:
        # Kein Unterschied zur letzten Beobachtung — kein neuer Eintrag noetig,
        # nur der Zeitstempel/Commit der letzten Bestaetigung wird ergaenzt.
        last.setdefault("confirmed_at", []).append(
            {"captured_at": observation["captured_at"], "git_rev": observation["git_rev"]})
        _atomic_write(path, existing)
        return "confirmed"
    obs.insert(0, observation)
    _atomic_write(path, existing)
    return "new" if last is None else "changed"


def capture_document(doc_stem, backend="pypdf", pattern="^RS_", only_id=None):
    info, pages = local_ids_for_doc(doc_stem, pattern, backend)
    rev, ts = _git_rev(), _now()
    results = []
    for rid, pagenos in sorted(info["ids"].items()):
        if only_id and rid.upper() != only_id.upper():
            continue
        if not pagenos:
            continue
        obs = capture_one(doc_stem, rid, pagenos[0], pages, backend, rev, ts)
        status = write_evidence(doc_stem, rid, obs)
        results.append({"id": rid, "page": pagenos[0], "status": status})
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--doc", help="Dokument-Stem, z. B. AUTOSAR_FO_RS_Diagnostics")
    ap.add_argument("--all-rs-docs", action="store_true",
                    help="Alle 18 kanonischen RS_DOCS erfassen (ein Prozess, sequenziell)")
    ap.add_argument("--id", help="Nur diese ID erfassen (sonst alle lokal definierten der Seite)")
    ap.add_argument("--backend", default="pypdf", choices=["pypdf", "builtin"])
    ap.add_argument("--pattern", default="^RS_")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if not args.doc and not args.all_rs_docs:
        ap.error("--doc oder --all-rs-docs angeben")

    docs = [args.doc] if args.doc else [stem for _, stem, _ in ss.RS_DOCS.values()]
    report = {}
    for doc_stem in docs:
        report[doc_stem] = capture_document(doc_stem, args.backend, args.pattern, args.id)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        for doc_stem, results in report.items():
            changed = [r for r in results if r["status"] == "changed"]
            new = [r for r in results if r["status"] == "new"]
            print("%s: %d IDs erfasst (%d neu, %d geaendert, %d bestaetigt)"
                  % (doc_stem, len(results), len(new), len(changed),
                     len(results) - len(new) - len(changed)))
            for r in changed:
                print("  geaendert: %s (Seite %s)" % (r["id"], r["page"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
