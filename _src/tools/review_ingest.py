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

Dieses Werkzeug ist der einzige schreibende Weg zurueck in die Spec-DB.
Standardmaessig arbeitet es lokal (kein Netz, keine nennenswerte CPU-Last)
und darf daher direkt ueber MCP laufen. Der ``-g/--github``-Modus laedt
Review-Pakete direkt aus GitHub-Issues und macht dafuer einen Netzzugriff
(``https://api.github.com``) — dieser Modus MUSS ueber run.sh laufen, nicht
direkt ueber MCP (AGENTS.md: kein Internetzugriff ausserhalb run.sh).

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

Verhalten bei Teilfehlern in grossen Paketen
--------------------------------------------
Die Uebernahme ist **entscheidungsweise isoliert**, nicht transaktional ueber
das gesamte Paket. Das bedeutet:

- Formale Paketfehler (ungueltiges Schema, fehlende Pflichtfelder,
  ``--require-authenticated`` gegen ``self_declared``) stoppen das Paket vor
  dem ersten Schreibversuch komplett.
- Erwartete fachliche Einzelkonflikte (Record fehlt, ``text_hash`` weicht ab,
  kein ``requirement_text``-Block) werden pro Entscheidung als ``conflict``
  berichtet; die restlichen Entscheidungen laufen weiter.
- Unerwartete technische Einzelprobleme (defektes Record-JSON, I/O-Fehler,
  Queue-Aufraeumen scheitert etc.) werden pro Entscheidung als ``error``
  berichtet; auch dann laufen die restlichen Entscheidungen weiter.
- Bereits erfolgreich geschriebene Entscheidungen werden **nicht**
  zurueckgerollt. Der Operator muss nach einem Lauf mit Konflikten/Fehlern nur
  die fehlgeschlagenen IDs nacharbeiten und anschliessend in einem neuen Paket
  erneut einspielen.

Damit gibt es bei grossen Paketen kein "alles oder nichts": maximaler
Fortschritt pro Lauf, aber keine stille Teiluebernahme. Exit-Code 1 bedeutet
mindestens ein Paketfehler, Konflikt oder technischer Einzel-Fehler.

Aufruf (immer vom Repo-Wurzelverzeichnis)
-----------------------------------------
    python3 _src/tools/review_ingest.py --check  paket.json
    python3 _src/tools/review_ingest.py --apply  paket.json
    python3 _src/tools/review_ingest.py --apply --require-authenticated paket.json
    python3 _src/tools/review_ingest.py -g 1 2
    python3 _src/tools/review_ingest.py --apply -g 1 2 --repo 2b-rs/autodocs

Exit-Code 1, wenn Konflikte auftraten oder das Paket abgelehnt wurde.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
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


from canonical_id import parse_canonical_id  # noqa: E402 (0006-02 propagation)


def find_record(rid: str) -> Path | None:
    """Accepts either a bare legacy id or a canonical project/kind/id string;
    falls back to the bare id lookup below when not canonical (0006-02)."""
    parsed = parse_canonical_id(rid)
    if parsed is not None:
        rid = parsed["id"]
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


def _github_headers() -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "review_ingest.py",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = "Bearer %s" % token
    return headers


_FENCE = re.compile(r"^\s*```(?:json)?\s*\n(.*?)\n?\s*```\s*$", re.DOTALL)


def _strip_code_fence(text: str) -> str:
    """GitHub-Issue-Bodies bettten das Paket haeufig in ```json ... ``` ein."""
    m = _FENCE.match(text.strip())
    return m.group(1) if m else text


def fetch_github_issue_package(repo: str, issue_nr: int) -> tuple[dict | None, str | None]:
    url = "https://api.github.com/repos/%s/issues/%d" % (repo, issue_nr)
    req = urllib.request.Request(url, headers=_github_headers())
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        return None, "GitHub-Issue #%d aus %s konnte nicht geladen werden: HTTP %s: %s" % (issue_nr, repo, e.code, detail)
    except urllib.error.URLError as e:
        return None, "GitHub-Issue #%d aus %s konnte nicht geladen werden: %s" % (issue_nr, repo, e)
    except json.JSONDecodeError as e:
        return None, "GitHub-Antwort fuer Issue #%d aus %s ist kein gueltiges JSON: %s" % (issue_nr, repo, e)

    body = payload.get("body")
    if not isinstance(body, str) or not body.strip():
        return None, "GitHub-Issue #%d aus %s enthaelt keinen JSON-Body" % (issue_nr, repo)
    try:
        paket = json.loads(_strip_code_fence(body))
    except json.JSONDecodeError as e:
        return None, "GitHub-Issue #%d aus %s enthaelt kein gueltiges Review-Paket-JSON: %s" % (issue_nr, repo, e)
    return paket, None


def ingest_package(paket: dict, paket_label: str, apply: bool, require_auth: bool) -> dict:
    bericht = {"paket": paket_label, "identity": paket.get("identity"),
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

    for i, d in enumerate(paket["decisions"]):
        try:
            ergebnis = apply_decision(d, paket, apply)
        except Exception as e:  # noqa: BLE001 -- ein Record darf die anderen nicht mitreissen
            ergebnis = {"id": d.get("id") or "decisions[%d]" % i, "status": "error",
                       "grund": "%s: %s" % (type(e).__name__, e)}
        bericht["ergebnisse"].append(ergebnis)
    bericht["konflikte"] = [r for r in bericht["ergebnisse"]
                            if r["status"] == "conflict"]
    bericht["fehlgeschlagen"] = [r for r in bericht["ergebnisse"]
                                 if r["status"] == "error"]
    return bericht


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
    return ingest_package(paket, str(paket_pfad), apply, require_auth)


def _print_bericht(bericht: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(bericht, ensure_ascii=False, indent=1))
        return
    print("Paket:    %s (%s)" % (bericht["paket"], bericht.get("identity")))
    for w in bericht.get("warnungen", []):
        print("WARNUNG:  %s" % w)
    for f in bericht.get("fehler", []):
        print("FEHLER:   %s" % f)
    for r in bericht.get("ergebnisse", []):
        if r["status"] == "ok":
            print("ok        %s -> %s" % (r["id"], r["pfad"]))
        elif r["status"] == "error":
            print("FEHLER    %s: %s" % (r["id"], r["grund"]))
        else:
            print("KONFLIKT  %s: %s" % (r["id"], r["grund"]))
    print("%d Entscheidungen, %d Konflikte, %d Fehler, %s"
          % (len(bericht.get("ergebnisse", [])), len(bericht.get("konflikte", [])),
             len(bericht.get("fehlgeschlagen", [])),
             "geschrieben" if bericht.get("angewandt") else "nur geprueft"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paket", nargs="*", type=Path, help="Review-Paket(e) als JSON-Datei")
    ap.add_argument("--apply", action="store_true",
                    help="Records schreiben (Standard: nur pruefen)")
    ap.add_argument("--require-authenticated", action="store_true",
                    help="Nur Pakete mit belegter GitHub-Identitaet zulassen")
    ap.add_argument("--json", action="store_true", help="Bericht als JSON")
    ap.add_argument("--repo", default="2b-rs/autodocs",
                    help="GitHub-Repo fuer -g/--github-Issues (Standard: %(default)s)")
    ap.add_argument("-g", "--github", nargs="+", type=int, metavar="ISSUE",
                    help="Review-Paket(e) direkt aus GitHub-Issue(s) laden")
    args = ap.parse_args(argv)

    if not args.paket and not args.github:
        ap.error("mindestens ein lokales paket oder -g/--github ISSUE erforderlich")

    berichte = []
    for paket_pfad in args.paket:
        berichte.append(ingest(paket_pfad, args.apply, args.require_authenticated))
    for issue_nr in args.github or []:
        paket, fehler = fetch_github_issue_package(args.repo, issue_nr)
        label = "github:%s#%d" % (args.repo, issue_nr)
        if fehler:
            berichte.append({"paket": label, "identity": None, "angewandt": args.apply,
                             "fehler": [fehler], "ergebnisse": [], "konflikte": []})
            continue
        berichte.append(ingest_package(paket, label, args.apply, args.require_authenticated))

    if args.json:
        print(json.dumps(berichte if len(berichte) != 1 else berichte[0], ensure_ascii=False, indent=1))
    else:
        for i, bericht in enumerate(berichte):
            if i:
                print()
            _print_bericht(bericht, as_json=False)

    return 1 if any(b.get("fehler") or b.get("konflikte") or b.get("fehlgeschlagen")
                    for b in berichte) else 0


if __name__ == "__main__":
    sys.exit(main())
