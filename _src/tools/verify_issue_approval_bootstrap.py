#!/usr/bin/env python3
"""Stdlib-only structural verifier for an approval record."""
import hashlib, json, sys
from pathlib import Path
if len(sys.argv) != 2:
    raise SystemExit('usage: verify_issue_approval_bootstrap.py APPROVAL.json')
d=json.loads(Path(sys.argv[1]).read_text())
required={'schema','package_commit','package_digest','approval_ref','approver_role','signature_verified'}
if set(d) < required or d.get('schema')!='issue-approval@v1' or d.get('signature_verified') is not True:
    raise SystemExit('invalid approval record')
if not d['package_digest'].startswith('sha256:') or len(d['package_digest']) != 71:
    raise SystemExit('invalid package digest')
print('structural approval record validation passed; run git verify-commit separately')
