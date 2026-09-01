#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
"""curation_flags.py — Warteschlange fuer KI-gestuetzte Kurations-Anfragen.

Eine Kurations-Anfrage entsteht, wenn die Extraktion einen Fall nicht
automatisch entscheiden kann (siehe ``extraction_report.py``, Abschnitt
"Kurationsanfragen"). Die Person, die die Extraktionsskripte betreibt, trifft
die Entscheidung im Browser (Freigeben/Ablehnen + Begruendung) und sendet sie
als GitHub-Issue ab (``review.js``, gleicher Mechanismus wie normale
Requirement-Reviews, aber mit ``kind: "curation_request"``).

Weil eine Kurationsentscheidung oft eine Freitext-Begruendung ist ("benutze
die Schreibweise aus Zeile X", "schliesse diese ID dauerhaft aus"), kann ihre
Umsetzung eine Codeaenderung an ``spec_scrape.py`` oder eine neue Ausnahme in
``RESIDUAL`` erfordern. Das ist Textverstehen, keine reine Datenuebernahme —
dafuer ist ein KI-Agent zustaendig, nicht ``curation_ingest.py`` selbst.

Ablauf
------
1. ``curation_ingest.py --apply`` schreibt fuer jede Entscheidung ein Flag
   hierhin (offen, mit voller Entscheidungsgrundlage: Begruendung, Person,
   betroffene ID, Screenshot-Pfad).
2. Ein KI-Agent uebernimmt das Flag atomar (wie bei ``review_flags.py``),
   schlaegt eine konkrete Aenderung vor (Diff oder neuer RESIDUAL-Eintrag)
   und legt sie als PR oder Patch-Datei ab. Der Agent WENDET NICHTS SELBST AN.
3. Die Person, die die Extraktionsskripte betreibt, hat die letzte
   Entscheidung: Sie prueft den Vorschlag, mergt ihn (oder verwirft ihn) und
   ruft danach ``complete_flag`` auf. Ohne diesen manuellen Schritt bleibt
   das Flag offen.
"""
from __future__ import annotations

import json
import os
import socket
import uuid
from datetime import datetime, timezone
from pathlib import Path

QUEUE = Path(__file__).resolve().parents[1] / "spec" / "curation-queue"
OPEN_DIR = QUEUE / "open"
CLAIMED_DIR = QUEUE / "claimed"
DONE_DIR = QUEUE / "done"

SCHEMA = "curation-flag@v1"


from canonical_id import resolve_legacy  # noqa: E402 (0006-02 propagation)


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ensure_dirs():
    for d in (OPEN_DIR, CLAIMED_DIR, DONE_DIR):
        d.mkdir(parents=True, exist_ok=True)


def _atomic_write(path, payload):
    tmp = path.with_suffix(path.suffix + ".tmp-%s" % uuid.uuid4().hex[:8])
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def write_curation_flag(decision, campaign="html-curation", project=None, kind=None):
    """Flag additiv anlegen; eine bereits offene Anfrage zur selben ID bleibt fuehrend.

    project/kind optional, default AUTOSAR/AP/record (0006-02).
    """
    if isinstance(decision, dict) and decision.get("id"):
        decision.setdefault("canonical_id", resolve_legacy(decision["id"], project, kind))
    _ensure_dirs()
    rid = decision["id"]
    path = OPEN_DIR / (rid + ".json")
    if path.exists():
        return None
    _atomic_write(path, {
        "schema": SCHEMA,
        "id": rid,
        "created": _now(),
        "campaign": campaign,
        "outcome": decision["outcome"],
        "decided_by": decision["decided_by"],
        "identity": decision.get("identity"),
        "decided_at": decision["decided_at"],
        "rationale": decision["rationale"],
        "decision_basis": decision.get("decision_basis") or {},
        "instruction": {
            "goal": "Kurationsentscheidung fuer %s in eine konkrete Aenderung uebersetzen." % rid,
            "forbidden": [
                "Die Aenderung direkt committen oder mergen",
                "Den Normtext ohne Beleg aendern",
                "complete_flag() aufrufen (das macht nur die Betreiberin/der Betreiber)",
            ],
            "steps": [
                "Lies rationale und decision_basis; sie enthalten den Kurations-Wunsch im Klartext.",
                "Schlage eine minimale, belegte Aenderung vor (Code-Diff in spec_scrape.py oder "
                "neuer RESIDUAL-Eintrag in extraction_report.py) und lege sie als Patch- oder PR-Entwurf ab.",
                "Verweise im Vorschlag auf diese Flag-Datei und auf den Screenshot-Pfad aus decision_basis.",
                "Uebergib den Vorschlag zur Pruefung; wende ihn nicht selbst an.",
            ],
        },
    })
    return path


def list_open_flags():
    _ensure_dirs()
    return sorted(OPEN_DIR.glob("*.json"))


def list_claimed_flags():
    _ensure_dirs()
    return sorted(CLAIMED_DIR.glob("*.json"))


def list_active_flags():
    """List all flags in open and claimed directories."""
    return list_open_flags() + list_claimed_flags()


def write_review_request_flag(item: dict, reservation_id: str | None = None) -> Path | None:
    """Atomically write a conformant review-request queue item to open/.

    Top-level fields match the authoritative curation-item schema with:
    - schema: "curation-flag@v1"
    - canonical_id: matching target record
    - id: request/event identity
    - item_kind: "review-request"
    - origin: "browser"
    - outcome: "requested" (status="open")
    - created: UTC timestamp
    - decided_by: None (never fabricated before a decision)
    - decided_at: None (never fabricated before a decision)
    - decision_basis: validated client/envelope details
    """
    _ensure_dirs()
    rid = item["id"]
    filename = f"{rid}.json"
    path = OPEN_DIR / filename
    if path.exists():
        return None
    _atomic_write(path, item)
    return path


def claim_flag(path, agent=None):
    _ensure_dirs()
    path = Path(path)
    agent = agent or "%s-%s" % (socket.gethostname(), os.getpid())
    target = CLAIMED_DIR / ("%s.%s.json" % (path.stem, agent))
    try:
        os.rename(path, target)
    except OSError:
        return None
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["claimed_by"] = agent
    payload["claimed_at"] = _now()
    _atomic_write(target, payload)
    return target


def complete_flag(path, note=None, outcome_class=None, outcome_detail=None):
    """Nur von der Person aufzurufen, die die Aenderung final gemergt/verworfen hat.

    outcome_class (0006-07, optional): one of decision_outcome.OUTCOME_CLASSES,
    naming what kind of follow-up work this decision implies (DB value update,
    migration, parser change, allowlist exception, new fixture, or none).
    Defaults to "no_action" when omitted so existing callers are unaffected.
    outcome_detail (optional): free-form string/dict with specifics (e.g. which
    file/line the allowlist exception was added to). After the flag is written,
    any hooks registered for outcome_class (decision_outcome.register_hook) run
    against the completed payload; hook exceptions are collected onto the
    returned Path's associated flag file as "_outcome_hook_errors" rather than
    raised, so a broken future hook can never block completing a decision.
    """
    import sys as _sys
    _tools_dir = str(Path(__file__).resolve().parent)
    if _tools_dir not in _sys.path:
        _sys.path.insert(0, _tools_dir)
    import decision_outcome as _do

    _ensure_dirs()
    path = Path(path)
    target = DONE_DIR / path.name
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["completed_at"] = _now()
    if note:
        payload["operator_note"] = note
    payload["outcome_class"] = outcome_class or "no_action"
    if outcome_detail is not None:
        payload["outcome_detail"] = outcome_detail
    errors = _do.run_hooks(payload["outcome_class"], payload)
    if errors:
        payload["_outcome_hook_errors"] = [repr(e) for e in errors]
    _atomic_write(target, payload)
    path.unlink()
    return target


def release_flag(path):
    path = Path(path)
    rid = path.stem.split(".")[0]
    target = OPEN_DIR / (rid + ".json")
    os.rename(path, target)
    return target
