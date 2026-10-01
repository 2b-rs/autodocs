#!/usr/bin/env python3
import json
import sys
from collections import Counter

d = json.load(sys.stdin)
print('checked_records:', d['checked_records'])
print('traceability_rs_count:', d['traceability_rs_count'])
print('flagged_count:', d['flagged_count'])
c = Counter(item['issue'] for item in d['flagged'])
print('by issue type:', dict(c))
reason_counts = Counter(
    ((item.get('issue'), (item.get('provenance') or {}).get('traceability', {}).get('reason')))
    for item in d['flagged']
)
print('by provenance reason:', dict(reason_counts))

sig = Counter()
for item in d['flagged']:
    prov = item.get('provenance') or {}
    t = prov.get('traceability') or {}
    db = prov.get('db_upstream') or {}
    source_docs = tuple(t.get('source_documents') or [])
    matched_rows = t.get('matched_source_rows') or []
    row_pages = tuple(sorted({row.get('page') for row in matched_rows if row.get('page') is not None}))
    sig[(item.get('issue'), t.get('reason'), tuple(source_docs), row_pages, tuple(u.get('id') for u in (db.get('all_upstream') or [])))] += 1
print('top signatures:')
for key, n in sig.most_common(10):
    print(' -', n, key)

for item in d['flagged'][:15]:
    print(' -', item['issue'], item['record'], item['rs_id'], '|', item['detail'][:100])
    prov = item.get('provenance') or {}
    db = prov.get('db_upstream') or {}
    t = prov.get('traceability') or {}
    print('   db_upstream:', db.get('matched_upstream') or db.get('all_upstream') or [])
    print('   traceability:', {'reason': t.get('reason'), 'record_path': t.get('record_path'), 'matched_source_rows': t.get('matched_source_rows') or []})
