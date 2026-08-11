#!/usr/bin/env python3
import json
import sys

d = json.load(sys.stdin)
rows = d.get('traceability', {})
total = sum(len(v) for v in rows.values())
print('documents with traceability rows:', len(rows))
print('total RS rows:', total)
w = d.get('write') or {}
print('written:', len(w.get('written', [])), 'updated:', len(w.get('updated', [])), 'total canonical RS records:', w.get('total'))
