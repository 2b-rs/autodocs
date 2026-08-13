#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""migriere_status_backfill.py — status/history mechanisch nachtragen (0006-04).

Viele produktive Records tragen bislang nur additive Felder wie ``upstream``
/ ``namespace_meta``, aber kein ``status``/``history`` (im Gegensatz zum
Pilotmodul SWS_LOG). Dieses Skript ergaenzt fuer jeden Record OHNE
``status``-Schluessel einen minimalen, EHRLICHEN Status: ``valid/unmigrated``
-- es wird bewusst KEINE tatsaechliche Kuration/Freigabe behauptet, die nie
stattgefunden hat (anders als SWS_LOGs ``valid/auto-approved``, das aus einer
realen Kampagne stammt). Feld-Ebene (``fields.<name>.state/reason/trace``)
wird in diesem Durchlauf bewusst NICHT nachgetragen, da dafuer echte
Abstimmungsdaten (votes) fehlen, die es nur fuer das Pilotmodul gibt --
das bleibt Folgearbeit.

Idempotent: Records, die bereits ``status`` tragen, werden nicht veraendert.

    python3 _src/tools/migriere_status_backfill.py            # nur Bericht
    python3 _src/tools/migriere_status_backfill.py --apply    # schreiben
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

RECORDS = Path(__file__).resolve().parents[1] / "spec" / "records"
CAMPAIGN = "2026-08-13-status-backfill"
REASON = (
    "mechanically backfilled by migriere_status_backfill.py -- no per-field "
    "curation history exists yet for this record"
)


def backfill(rec: dict, today: str) -> dict:
    rec = dict(rec)
    rec["status"] = {"state": "valid/unmigrated", "reason": REASON, "campaign": CAMPAIGN}
    history = list(rec.get("history") or [])
    history.append({
        "campaign": CAMPAIGN, "date": today, "from": None,
        "to": "valid/unmigrated", "reason": REASON, "actor": "tool",
    })
    rec["history"] = history
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="Aenderungen schreiben")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args(argv)

    today = date.today().isoformat()
    stat = Counter()
    for path in sorted(RECORDS.rglob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        if "status" in rec:
            stat["bereits_vorhanden"] += 1
            continue
        stat["nachgetragen"] += 1
        if args.apply:
            neu = backfill(rec, today)
            path.write_text(json.dumps(neu, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        if args.limit and stat["nachgetragen"] >= args.limit:
            break

    print("Modus:", "schreibend" if args.apply else "nur Bericht")
    for key in sorted(stat):
        print(f"  {key:20s} {stat[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
