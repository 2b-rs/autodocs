#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""migriere_dienst_namespace.py -- Namensraum fuer Dienstschnittstellen-Methoden
wirklich nachtragen (0008-07, korrigiert 0004-02's nie geschriebenen Backfill).

Grundwahrheit (verifiziert per git log/blame 2026-08-13): 0004-02 behauptete,
34 SWS_UCM_*/SWS_CM_*/SWS_SM_*-Records mit
``namespace_meta.source='ai-derived-from-service-interface'`` versehen zu
haben -- dieser Wert existierte zu KEINEM Zeitpunkt in der Historie dieses
Repos. Diese Migration holt die tatsaechliche Schreibung nach, basierend auf
0004-02's eigener (korrekter) Recherche: Dienstmethoden erben den Namensraum
ihrer umschliessenden Dienstschnittstelle.

Ableitung: aus der 'Scope'-Zeile ('service interface <a ...>NAME</a>') wird
der Schnittstellenname extrahiert; Namespace = 'ara::<modul>' (aus dem
bestehenden namespace_meta.module), Enclosing = 'ara::<modul>::<NAME>'.
Die bisherige 'deviation'-Notiz bleibt als historischer Kontext erhalten.
source wird auf 'ai-derived-from-service-interface' gesetzt,
review_status auf 'pending' (Kurator muss noch bestaetigen, wie von
0004-02 urspruenglich vorgesehen).

Idempotent: Records, die bereits ein 'namespace' tragen, werden ignoriert.

    python3 _src/tools/migriere_dienst_namespace.py            # nur Bericht
    python3 _src/tools/migriere_dienst_namespace.py --apply    # schreiben
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

RECORDS = Path(__file__).resolve().parents[1] / "spec" / "records"
DEVIATION_MARKER = "dienstschnittstelle-ohne-namensraum"
SCOPE_TH = ("scope", "geltungsbereich")
SERVICE_IFACE_RE = re.compile(r"service interface.*?>([A-Za-z0-9_]+)<")


def _scope_of(rec: dict):
    for block in rec.get("blocks", []):
        for row in block.get("rows", []) or []:
            th = str(row.get("th", "")).strip().rstrip(":").lower()
            if th in SCOPE_TH:
                return row.get("td")
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="Aenderungen schreiben")
    args = ap.parse_args(argv)

    stat = Counter()
    beispiele = []
    for path in sorted(RECORDS.rglob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        ns = rec.get("namespace_meta")
        if not isinstance(ns, dict) or ns.get("deviation") != DEVIATION_MARKER:
            continue
        if ns.get("namespace"):
            stat["bereits_versehen"] += 1
            continue
        scope = _scope_of(rec)
        m = SERVICE_IFACE_RE.search(scope or "")
        if not m:
            stat["nicht_ableitbar"] += 1
            continue
        iface = m.group(1)
        module = ns.get("module")
        if not module:
            stat["kein_modul"] += 1
            continue
        namespace = f"ara::{module}"
        enclosing = f"{namespace}::{iface}"
        ns = dict(ns)
        ns["namespace"] = namespace
        ns["enclosing"] = enclosing
        ns["source"] = "ai-derived-from-service-interface"
        ns["review_status"] = "pending"
        stat["nachgetragen"] += 1
        beispiele.append((rec.get("id"), namespace, enclosing))
        if args.apply:
            rec["namespace_meta"] = ns
            path.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print("Modus:", "schreibend" if args.apply else "nur Bericht")
    for key in sorted(stat):
        print(f"  {key:20s} {stat[key]}")
    if beispiele:
        print("\nBeispiele (id | namespace | enclosing):")
        for i, n, e in beispiele:
            print(f"  {i} | {n} | {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
