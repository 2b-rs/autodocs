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
for item in d['flagged'][:15]:
    print(' -', item['issue'], item['record'], item['rs_id'], '|', item['detail'][:100])
