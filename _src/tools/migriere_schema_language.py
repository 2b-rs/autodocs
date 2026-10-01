#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""migriere_schema_language.py — vereinheitlicht maschinenlesbare Schema-Sprache.

Aktuell tragen Records ein legacy-Objekt ``ns`` mit teils deutschen Schluesseln
(``modul``, ``quelle``, ``generiert``, ``abweichung``). Ziel ist ein kanonisches
Objekt ``namespace_meta`` mit englischen Schluesseln.

    python3 _src/tools/migriere_schema_language.py            # nur Bericht
    python3 _src/tools/migriere_schema_language.py --apply    # schreiben
"""
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path

RECORDS = Path(__file__).resolve().parents[1] / 'spec' / 'records'
DEVIATION_MAP = {
    'std-spezialisierung': 'std-specialization',
    'modulfremder-namensraum': 'foreign-module-namespace',
    'dienst-namensraum': 'service-namespace',
    'modellgenerierter-namensraum': 'model-generated-namespace',
}


def canonicalize(meta: dict) -> dict:
    out = {}
    if not meta:
        return out
    out['namespace'] = meta.get('namespace')
    if meta.get('enclosing') is not None:
        out['enclosing'] = meta.get('enclosing')
    out['module'] = meta.get('module', meta.get('modul'))
    out['source'] = meta.get('source', meta.get('quelle'))
    if 'generated' in meta or 'generiert' in meta:
        out['generated'] = meta.get('generated', meta.get('generiert'))
    dev = meta.get('deviation', meta.get('abweichung'))
    out['deviation'] = DEVIATION_MAP.get(dev, dev)
    return {k:v for k,v in out.items() if v is not None}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args(argv)
    stat=Counter()
    examples=[]
    for path in sorted(RECORDS.rglob('*.json')):
        rec=json.loads(path.read_text(encoding='utf-8'))
        legacy=rec.get('namespace_meta') or rec.get('ns') or {}
        new=canonicalize(legacy)
        if not new:
            stat['empty'] += 1
            continue
        if rec.get('namespace_meta') == new and 'ns' not in rec:
            stat['unchanged'] += 1
            continue
        if 'ns' in rec:
            stat['legacy_ns_removed'] += 1
        if legacy.get('modul') and new.get('module') == legacy.get('modul'):
            stat['module_key_migrated'] += 1
        if legacy.get('quelle') and new.get('source') == legacy.get('quelle'):
            stat['source_key_migrated'] += 1
        if 'generiert' in legacy:
            stat['generated_key_migrated'] += 1
        if legacy.get('abweichung') != new.get('deviation'):
            stat['deviation_value_normalized'] += 1
        rec['namespace_meta']=new
        rec.pop('ns', None)
        stat['changed'] += 1
        if len(examples) < 8:
            examples.append((rec.get('id'), legacy, new))
        if args.apply:
            path.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('Mode:', 'write' if args.apply else 'report')
    for k in sorted(stat):
        print(f'  {k:28s} {stat[k]}')
    print('\nExamples:')
    for rid, old, new in examples:
        print(rid)
        print('  old =', old)
        print('  new =', new)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
