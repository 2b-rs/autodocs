#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""migriere_ns_enclosing.py — ns-Block der Spec-DB auf zwei Fakten trennen.

Altschema: ``ns.namespace`` trug teils den umschliessenden Typ
(z. B. ``ara::diag::SovdSwUpdate``). Neuschema: ``ns.namespace`` ist der
echte Namespace (``ara::diag``), ``ns.enclosing`` der umschliessende Typ
(``ara::diag::SovdSwUpdate::...``). Quelle beider Werte ist das Feld
``Scope`` des jeweiligen Records; die Ableitung nutzt dieselbe Funktion
wie der Scraper (``namespace_from_scope``).

    python3 _src/tools/migriere_ns_enclosing.py            # nur berichten
    python3 _src/tools/migriere_ns_enclosing.py --apply    # schreiben
"""
from __future__ import annotations
import argparse, json, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spec_scrape import RECORDS, namespace_from_scope, _strip_html  # noqa: E402

SCOPE_TH = ("scope", "geltungsbereich")


def scope_of(rec: dict):
    for block in rec.get("blocks", []):
        if block.get("t") != "props":
            continue
        for row in block.get("rows", []):
            if _strip_html(row.get("th", "")).lower().rstrip(":") in SCOPE_TH:
                return _strip_html(row.get("td", ""))
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="Aenderungen schreiben")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args(argv)

    stat = Counter()
    beispiele = []
    for path in sorted(RECORDS.rglob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        scope = scope_of(rec)
        if not scope:
            stat["ohne_scope"] += 1
            continue
        ns_neu, enc_neu = namespace_from_scope(scope)
        if not ns_neu:
            stat["nicht_ableitbar"] += 1
            continue
        ns = dict(rec.get("ns") or {})
        ns_alt, enc_alt = ns.get("namespace"), ns.get("enclosing")
        if ns_alt == ns_neu and enc_alt == enc_neu:
            stat["unveraendert"] += 1
            continue
        if ns_alt and ns_alt != ns_neu:
            stat["namespace_korrigiert"] += 1
            if len(beispiele) < 12:
                beispiele.append((rec.get("id"), ns_alt, ns_neu, enc_neu))
        if enc_neu and enc_alt is None:
            stat["enclosing_ergaenzt"] += 1
        ns["namespace"] = ns_neu
        if enc_neu:
            ns["enclosing"] = enc_neu
        elif "enclosing" in ns:
            del ns["enclosing"]
        ns.setdefault("quelle", "scope")
        stat["geaendert"] += 1
        if args.apply:
            rec["ns"] = ns
            path.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n",
                            encoding="utf-8")
        if args.limit and stat["geaendert"] >= args.limit:
            break

    print("Modus:", "schreibend" if args.apply else "nur Bericht")
    for key in sorted(stat):
        print(f"  {key:24s} {stat[key]}")
    if beispiele:
        print("\nBeispiele (id | ns alt -> ns neu | enclosing):")
        for i, a, n, e in beispiele:
            print(f"  {i} | {a} -> {n} | {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
