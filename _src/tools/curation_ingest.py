#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""curation_ingest.py — Kurationsentscheidungen aus dem Extraktionsbericht uebernehmen.

Der Extraktionsbericht (``extraction_report.py``) zeigt am Seitenanfang
Kurationsanfragen: Faelle, die die Extraktion nicht automatisch entscheiden
konnte, mit Screenshot, aktuellem Extraktionsergebnis und einer
Klartext-Erklaerung, was heute passiert und welche Entscheidung gefragt ist.
Die Person, die den Bericht liest, entscheidet im selben Review-Widget wie
bei normalen Requirement-Reviews (``review.js``) und sendet das Paket als
GitHub-Issue ab — nur mit ``kind: "curation_request"`` statt
``requirement_text``.

Dieses Werkzeug liest ein solches Paket (als JSON-Export ODER direkt aus
einem GitHub-Issue-Body, siehe ``--issue-body``) und legt fuer jede
Entscheidung ein Flag in ``spec/curation-queue/open/`` an
(``curation_flags.write_curation_flag``). Von dort holt sich ein KI-Agent
die Anfrage, schlaegt eine konkrete, belegte Aenderung vor (Diff oder neuer
``RESIDUAL``-Eintrag) und legt sie als Review vor. Angewandt wird sie NICHT
automatisch: Die Person, die die Extraktionsskripte betreibt, hat die letzte
Entscheidung und ruft danach manuell ``curation_flags.complete_flag()`` auf.

Aufruf (immer vom Repo-Wurzelverzeichnis)
-----------------------------------------
    python3 _src/tools/curation_ingest.py --check paket.json
    python3 _src/tools/curation_ingest.py --apply paket.json
    python3 _src/tools/curation_ingest.py --apply --issue-body issue-42.md

Exit-Code 1 bei Formatfehlern.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import curation_flags as cf

PACKAGE_SCHEMA = "review-package@v1"
VALID_OUTCOMES = ("accept", "reject")
VALID_IDENTITY = ("github_authenticated", "self_declared")

CODE_FENCE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.S)


def load_package(pfad: Path, from_issue_body: bool) -> dict:
    raw = pfad.read_text(encoding="utf-8")
    if from_issue_body:
        m = CODE_FENCE_RE.search(raw)
        if not m:
            raise ValueError("Kein ```json ...``` Block im Issue-Body gefunden")
        raw = m.group(1)
    return json.loads(raw)


def validate_package(paket: dict) -> list:
    fehler = []
    if paket.get("schema") != PACKAGE_SCHEMA:
        fehler.append("unbekanntes Paket-Schema: %r" % paket.get("schema"))
    if paket.get("identity") not in VALID_IDENTITY:
        fehler.append("unbekannte identity: %r" % paket.get("identity"))
    decisions = [d for d in (paket.get("decisions") or [])
                 if d.get("kind") == "curation_request"]
    if not decisions:
        fehler.append("Paket enthaelt keine Kurationsanfragen (kind=curation_request)")
        return fehler
    for i, d in enumerate(decisions):
        wo = "decisions[%d]" % i
        for feld in ("id", "outcome", "decided_by", "decided_at", "rationale"):
            if not str(d.get(feld) or "").strip():
                fehler.append("%s: Feld %s fehlt oder ist leer" % (wo, feld))
        if d.get("outcome") not in VALID_OUTCOMES:
            fehler.append("%s: outcome muss accept oder reject sein" % wo)
    return fehler


def ingest(paket_pfad: Path, apply: bool, from_issue_body: bool) -> dict:
    paket = load_package(paket_pfad, from_issue_body)
    bericht = {"paket": str(paket_pfad), "identity": paket.get("identity"),
               "angewandt": apply, "fehler": [], "ergebnisse": []}

    bericht["fehler"] = validate_package(paket)
    if bericht["fehler"]:
        return bericht

    if paket["identity"] == "self_declared":
        bericht.setdefault("warnungen", []).append(
            "Nicht authentifiziertes Paket: decided_by ist Selbstauskunft. "
            "Die Betreiberin/der Betreiber sollte das vor dem Merge inhaltlich pruefen.")

    decisions = [d for d in paket["decisions"] if d.get("kind") == "curation_request"]
    for d in decisions:
        if not apply:
            bericht["ergebnisse"].append({"id": d["id"], "status": "ok", "dry_run": True})
            continue
        pfad = cf.write_curation_flag(d, campaign=paket.get("campaign") or "html-curation")
        if pfad is None:
            bericht["ergebnisse"].append(
                {"id": d["id"], "status": "skipped",
                 "grund": "bereits eine offene Kurationsanfrage fuer diese ID"})
        else:
            bericht["ergebnisse"].append({"id": d["id"], "status": "ok", "pfad": str(pfad)})
    return bericht


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paket", type=Path, help="Review-Paket (JSON) oder Issue-Body (mit --issue-body)")
    ap.add_argument("--apply", action="store_true", help="Flags anlegen (Standard: nur pruefen)")
    ap.add_argument("--issue-body", action="store_true",
                    help="Eingabedatei ist ein GitHub-Issue-Body mit ```json ...``` Block")
    ap.add_argument("--json", action="store_true", help="Bericht als JSON")
    args = ap.parse_args(argv)

    bericht = ingest(args.paket, args.apply, args.issue_body)

    if args.json:
        print(json.dumps(bericht, ensure_ascii=False, indent=1))
    else:
        print("Paket:    %s (%s)" % (bericht["paket"], bericht["identity"]))
        for w in bericht.get("warnungen", []):
            print("WARNUNG:  %s" % w)
        for f in bericht["fehler"]:
            print("FEHLER:   %s" % f)
        for r in bericht["ergebnisse"]:
            print("%-9s %s%s" % (r["status"], r["id"],
                                  (" -> %s" % r["pfad"]) if r.get("pfad") else ""))
        print("%d Kurationsanfragen, %s"
              % (len(bericht["ergebnisse"]), "angelegt" if bericht["angewandt"] else "nur geprueft"))

    return 1 if bericht["fehler"] else 0


if __name__ == "__main__":
    sys.exit(main())
