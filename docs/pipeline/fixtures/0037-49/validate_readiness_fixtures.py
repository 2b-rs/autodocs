import json
from pathlib import Path
p = Path('docs/pipeline/fixtures/0037-49/readiness-fixtures.json')
data = json.loads(p.read_text())
assert data['schema'] == '0037-49-readiness-fixtures@v1'
assert data['policy'] == 'deny-on-missing-or-unverifiable-external-prerequisite'
expected = {
 'approve-with-complete-independent-evidence': 'approval-eligible',
 'reject-placeholder-signer': 'blocked:signing',
 'reject-wrong-reviewer-role': 'blocked:reviewer-role',
 'reject-stale-digest': 'blocked:digest',
 'reject-unavailable-credential-handle': 'blocked:credential-handle',
 'reject-no-hosting-admin': 'blocked:hosting-administration',
 'no-op-deploy-health-restart-rollback': 'blocked:service-controls;no-external-mutation',
}
assert {x['id']: x['expected'] for x in data['cases']} == expected
for item in data['cases'][1:]:
    assert item['expected'].startswith('blocked:')
print('PASS: 7 readiness fixtures; six blocking controls and one complete-evidence eligibility control')
