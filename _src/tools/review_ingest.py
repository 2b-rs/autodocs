#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""review_ingest.py — Review-Pakete aus dem HTML-Workflow in die Records schreiben.

Der statische Review-Workflow (``review.js``) sammelt Entscheidungen im Browser
und gibt sie als Paket ab:

  * Variante A — authentifiziert als GitHub-Issue, ``identity`` =
    ``github_authenticated``. Der Autor ist durch GitHub belegt.
  * Variante B — JSON-Download ohne Anmeldung, ``identity`` =
    ``self_declared``. Die Person ist Selbstauskunft; solche Pakete werden
    strenger geprueft (siehe ``--require-authenticated``).

Dieses Werkzeug ist der einzige schreibende Weg zurueck in die Spec-DB. Es
arbeitet rein lokal (kein Netz, keine nennenswerte CPU-Last) und darf daher
direkt ueber MCP laufen; eine ``run.sh`` ist nicht noetig (AGENTS.md).

Grundsatz
---------
Der Record ist die fuehrende, revisionssichere Ablage. Die Flag-Dateien unter
``spec/review-queue/`` dienen ausschliesslich der Jobkontrolle und werden nach
Abschluss geloescht. Deshalb wandert die vollstaendige Entscheidungsgrundlage
— Befund, vorgelegte Anweisung, Evidenz — vor dem Loeschen in den Record.
Dokumentiert wird der Entscheidungsprozess: WER, WANN, WIE und WELCHE
INFORMATIONEN vorlagen.

Schutz gegen veralteten Text
----------------------------
Jede Entscheidung traegt ``text_hash`` ueber ``text_raw`` + geordnete
``repairs``-Liste. Weicht der Hash vom aktuellen Record ab, wurde der Text seit
der Anzeige im Browser veraendert: Die Entscheidung wird dann NICHT angewandt,
sondern als Konflikt gemeldet. Stilles Uebernehmen waere eine nicht belegte
Aenderung am Normtext.

Aufruf (immer vom Repo-Wurzelverzeichnis)
-----------------------------------------
    python3 _src/tools/review_ingest.py --check  paket.json
    python3 _src/tools/review_ingest.py --apply  paket.json
    python3 _src/tools/review_ingest.py --apply --require-authenticated paket.json

Exit-Code 1, wenn Konflikte auftraten oder das Paket abgelehnt wurde.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
RECORDS = SRC / "spec" / "records"
QUEUE = SRC / "spec" / "review-queue"

PACKAGE_SCHEMA = "review-package@v1"
DECISION_SCHEMA = "review-decision@v1"
VALID_OUTCOMES = ("accept", "reject")
VALID_IDENTITY = ("github_authenticated", "self_declared")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def text_hash(text_raw, repairs) -> str:
    """Bindung der Entscheidung an genau den angezeigten Textstand.

    Muss zeichengleich zu der Berechnung in ``lib_docmodel.render_blocks``
    sein, sonst schlaegt jede Uebernahme fehl.
    """
    payload = json.dumps({"raw": text_raw, "repairs": repairs or []},
                         sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def find_record(rid: str) -> Path | None:
    prefix = rid.rsplit("_", 1)[0]
    direkt = RECORDS / prefix / (rid + ".json")
    if direkt.exists():
        return direkt
    treffer = sorted(RECORDS.glob("**/%s.json" % rid))
    return treffer[0] if treffer else None


def requirement_block(record: dict) -> dict | None:
    for block in record.get("blocks", []):
        if block.get("t") == "requirement_text":
            return block
    return None


def validate_package(paket: dict) -> list:
    """Formale Pruefung des Pakets, bevor irgendetwas geschrieben wird."""
    fehler = []
    if paket.get("schema") != PACKAGE_SCHEMA:
        fehler.append("unbekanntes Paket-Schema: %r" % paket.get("schema"))
    if paket.get("identity") not in VALID_IDENTITY:
        fehler.append("unbekannte identity: %r" % paket.get("identity"))
    if not isinstance(paket.get("decisions"), list) or not paket["decisions"]:
        fehler.append("Paket enthaelt keine Entscheidungen")
        return fehler
    for i, d in enumerate(paket["decisions"]):
        wo = "decisions[%d]" % i
        for feld in ("id", "text_hash", "outcome", "decided_by", "decided_at",
                     "rationale"):
            if not str(d.get(feld) or "").strip():
                fehler.append("%s: Feld %s fehlt oder ist leer" % (wo, feld))
        if d.get("outcome") not in VALID_OUTCOMES:
            fehler.append("%s: outcome muss accept oder reject sein" % wo)
        basis = d.get("decision_basis") or {}
        if not basis.get("finding"):
            # Abgelehnte Flags brauchen dieselbe Begruendungstiefe wie umgesetzte.
            fehler.append("%s: decision_basis.finding fehlt" % wo)
    return fehler


def apply_decision(d: dict, paket: dict, apply: bool) -> dict:
    """Eine Entscheidung pruefen und — bei ``apply`` — in den Record schreiben."""
    rid = d["id"]
    pfad = find_record(rid)
    if pfad is None:
        return {"id": rid, "status": "conflict", "grund": "Record nicht gefunden"}
    record = json.loads(pfad.read_text(encoding="utf-8"))
    block = requirement_block(record)
    if block is None:
        return {"id": rid, "status": "conflict",
                "grund": "Record hat keinen requirement_text-Block"}

    ist = text_hash(block.get("text_raw"), block.get("repairs"))
    if ist != d["text_hash"]:
        return {"id": rid, "status": "conflict",
                "grund": "text_hash weicht ab — Text wurde seit der Anzeige geaendert",
                "erwartet": d["text_hash"], "aktuell": ist}

    eintrag = {
        "schema": DECISION_SCHEMA,
        "status": "resolved" if d["outcome"] == "accept" else "rejected",
        "outcome": d["outcome"],
        "decided_by": d["decided_by"],
        "decided_at": d["decided_at"],
        "rationale": d["rationale"],
        "identity": paket["identity"],
        "text_hash": d["text_hash"],
        "ingested_at": _now(),
        "decision_basis": d.get("decision_basis") or {},
    }
    if d.get("flag_id"):
        eintrag["resolves_flag"] = d["flag_id"]

    if not apply:
        return {"id": rid, "status": "ok", "pfad": str(pfad), "dry_run": True}

    flags = block.setdefault("review_flags", [])
    ziel = next((f for f in flags if f.get("id") == d.get("flag_id")), None)
    if ziel is None:
        ziel = {"id": d.get("flag_id") or rid}
        flags.append(ziel)
    ziel.update(eintrag)

    offen = [f for f in flags if f.get("status", "open") == "open"]
    zustand = record.setdefault("status", {})
    if not offen and str(zustand.get("state", "")).startswith("proposed/"):
        zustand["state"] = "valid/reviewed"
        zustand["reason"] = "review"
    record.setdefault("history", []).append({
        "campaign": paket.get("campaign") or "html-review",
        "date": _now(),
        "to": zustand.get("state"),
        "reason": "Review %s durch %s (%s)" % (d["outcome"], d["decided_by"],
                                               paket["identity"]),
        "actor": d["decided_by"],
        "review_ref": d.get("flag_id") or rid,
    })

    tmp = pfad.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    tmp.replace(pfad)

    # Jobkontrolle aufraeumen: Das Flag hat seinen Zweck erfuellt, die
    # Dokumentation liegt jetzt vollstaendig im Record.
    geloescht = []
    for unterordner in ("open", "claimed"):
        for f in (QUEUE / unterordner).glob("%s*.json" % rid):
            f.unlink()
            geloescht.append(str(f))
    return {"id": rid, "status": "ok", "pfad": str(pfad),
            "flags_geloescht": geloescht}


def ingest(paket_pfad: Path, apply: bool, require_auth: bool) -> dict:
    paket = json.loads(paket_pfad.read_text(encoding="utf-8"))
    bericht = {"paket": str(paket_pfad), "identity": paket.get("identity"),
               "angewandt": apply, "fehler": [], "ergebnisse": []}

    bericht["fehler"] = validate_package(paket)
    if bericht["fehler"]:
        return bericht

    if paket["identity"] == "self_declared":
        bericht.setdefault("warnungen", []).append(
            "Nicht authentifiziertes Paket: decided_by ist Selbstauskunft. "
            "Vor der Uebernahme inhaltlich pruefen.")
        if require_auth:
            bericht["fehler"].append(
                "--require-authenticated: Paket ohne GitHub-Identitaet abgelehnt")
            return bericht

    for d in paket["decisions"]:
        bericht["ergebnisse"].append(apply_decision(d, paket, apply))
    bericht["konflikte"] = [r for r in bericht["ergebnisse"]
                            if r["status"] == "conflict"]
    return bericht


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paket", type=Path, help="Review-Paket (JSON)")
    ap.add_argument("--apply", action="store_true",
                    help="Records schreiben (Standard: nur pruefen)")
    ap.add_argument("--require-authenticated", action="store_true",
                    help="Nur Pakete mit belegter GitHub-Identitaet zulassen")
    ap.add_argument("--json", action="store_true", help="Bericht als JSON")
    args = ap.parse_args(argv)

    bericht = ingest(args.paket, args.apply, args.require_authenticated)

    if args.json:
        print(json.dumps(bericht, ensure_ascii=False, indent=1))
    else:
        print("Paket:    %s (%s)" % (bericht["paket"], bericht["identity"]))
        for w in bericht.get("warnungen", []):
            print("WARNUNG:  %s" % w)
        for f in bericht["fehler"]:
            print("FEHLER:   %s" % f)
        for r in bericht["ergebnisse"]:
            if r["status"] == "ok":
                print("ok        %s -> %s" % (r["id"], r["pfad"]))
            else:
                print("KONFLIKT  %s: %s" % (r["id"], r["grund"]))
        print("%d Entscheidungen, %d Konflikte, %s"
              % (len(bericht["ergebnisse"]), len(bericht.get("konflikte", [])),
                 "geschrieben" if bericht["angewandt"] else "nur geprueft"))

    return 1 if bericht["fehler"] or bericht.get("konflikte") else 0


if __name__ == "__main__":
    sys.exit(main())
