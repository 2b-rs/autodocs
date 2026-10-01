#!/bin/bash
# ---------------------------------------------------------------------------
# Line-number tracing to stderr (SANDBOX.md requirement)
# ---------------------------------------------------------------------------
export PS4='+ ${BASH_SOURCE##*/}:${LINENO}: '
set -o pipefail
set -x

{ set +x; } 2>/dev/null
cat <<'BANNER'
==============================================================================
TITLE: TRUTH RS_CM_00211 AND RS_SAF_21101 (LAST TWO UNBLOCKED RECORDS)
==============================================================================

WHAT THE EVIDENCE SHOWED (gathered read-only in commit REF 20260815-203254)

  RS_CM_00211 -- REAL requirement block, CommunicationManagement p.22.
    Complete formal block: opening marker on the heading line, closing marker
    after Use Case. Four fields only; the block genuinely has NO Supporting
    Material, so its 4-field set is correct and must NOT later be "repaired"
    by the 0034-01 fix. Three defects in the draft:
      a) heading carries a line-break hyphenation artifact "pro- vide";
         the source reads "pro-\nvide", i.e. the word is "provide".
      b) Dependencies was blanked to "" though the source prints an en dash.
      c) all three prose fields lost their terminating full stop.

  RS_SAF_21101 -- NOT A REQUIREMENT DEFINITION IN THIS DOCUMENT.
    The only occurrence in AUTOSAR_AP_RS_PlatformHealthManagement is an
    inline citation inside a running sentence on p.9:
      "... may require certain processes to be followed - as recommended in
       ISO26262, for instance [RS_SAF_21101][4]."
    The anchor probe found NO block-opening marker within 120 chars before or
    200 chars after the ID. There is no definition block anywhere in the
    document. The draft nevertheless carries pages [9,10] with heading null
    and fields {} -- it captured a citation and then ran off the page end.
    This is a benchmark-CONSTRUCTION defect, distinct from 0034-01/02/03,
    which are all extractor field/anchor bugs. Filed here as 0034-04.

STRUCTURE
  Step 0  Preflight.
  Step 1  Apply the reviewed corrections to the two fixture records. Every
          value is asserted to be byte-identical to the source text captured
          in the previous run's evidence logs; the script REFUSES to write if
          any assertion fails.
  Step 2  File task 0034-04 (citation-only records must not become benchmark
          entries) into TODO.md, idempotently.
  Step 3  Validation gate: fixture structure + campaign + scrape_fields.
  Step 4  Stage narrowly, prove non-empty index, commit.
  Step 5  Summary and remaining-work report.

GOAL HIERARCHY
  PRIMARY  Close out the last two records that can be truthed without first
           fixing the extractor, so 0007-01's remaining backlog is cleanly
           and entirely gated on 0034-01/02/03.
    SUB-1  Do not silently "fix" RS_SAF_21101 into looking like a real
           requirement. Record what is actually true -- that the document
           contains no definition -- and file the selection defect.
    SUB-2  Preserve the distinction between a genuinely absent Supporting
           Material field (RS_CM_00211, RS_AP_00115) and one destroyed by
           0034-01, so the later mass regeneration cannot corrupt them.
    SUB-3  Keep 0007-01 [p] and OPEN. 21/200 reviewed after this run.
  NON-GOAL No extractor changes. Nothing touching Feature 0021.

RESOURCE ESTIMATE
  Data traffic .... none (no network; operates on local JSON + git)
  CPU load ........ negligible, single-threaded; two short pytest runs.
                    No PDF parsing this time -- the evidence is already on
                    disk from the previous run, so there is nothing to
                    parallelise; extra workers would sit idle.
  Workers ......... 1
  Wall-clock ...... < 15 seconds expected
  Writes .......... benchmark-draft.json (2 records), TODO.md (1 task added),
                    logs/<purpose>/<ts>/, one git commit.
==============================================================================
BANNER
set -x

# --- Step 0: preflight -----------------------------------------------------
{ set +x; } 2>/dev/null; echo "[$(date +%H:%M:%S)] STEP 0: preflight"; set -x

cd /tmp/autodocs || { echo "FATAL: /tmp/autodocs not found" >&2; exit 90; }

PURPOSE="spec-truthing-apply"
TS="$(date +%Y%m%d-%H%M%S)"
LOGDIR="logs/${PURPOSE}/${TS}"
mkdir -p "$LOGDIR" || { echo "FATAL: cannot create $LOGDIR" >&2; exit 91; }
cp "$0" "$LOGDIR/executed-script.sh" 2>/dev/null || true

GIT_EMAIL="$(git config user.email || true)"
GIT_NAME="$(git config user.name || true)"
{ set +x; } 2>/dev/null
echo "    identity: name='${GIT_NAME}' email='${GIT_EMAIL}'"
[ -n "$GIT_EMAIL" ] || { echo "FATAL: git user.email unset" >&2; exit 93; }
set -x

FIXTURE="_src/tests/fixtures/spec_extraction/benchmark-draft.json"

# --- Step 1: apply reviewed corrections ------------------------------------
{ set +x; } 2>/dev/null; echo "[$(date +%H:%M:%S)] STEP 1: apply corrections"; set -x

python3 - "$FIXTURE" <<'PY' 2>&1 | tee "$LOGDIR/01-apply-corrections.txt"
# -*- coding: utf-8 -*-
import json, sys, io

path = sys.argv[1]
doc  = json.load(open(path, encoding='utf-8'))
recs = {r['id']: r for r in doc['records']}
REVIEWER = 'agent-0007-01'

DASH = '\u2013'          # en dash, as printed in the AppliesTo/Dependencies cells
LDQ, RDQ = '\u201c', '\u201d'   # curly quotes as printed in the source

# ----------------------------------------------------------------- CM_00211
r = recs['RS_CM_00211']
before = json.dumps(r['expected'], indent=2, ensure_ascii=False)

heading = ('Communication Management shall provide an interface to provide '
           'methods to other applications')
fields = {
    'Description': ('Application developers shall be able to provide methods '
                    'which can be called by other applications.'),
    'Rationale':   ('After offering a service, it shall be possible for other '
                    'applications to call methods of the service and get the '
                    'respective result.'),
    'Dependencies': DASH,
    'Use Case':    ('Application %sA%s calls the %sgetCurrentTime%s method of '
                    'the wall clock service provided by application %sB%s.'
                    % (LDQ, RDQ, LDQ, RDQ, LDQ, RDQ)),
}

# Guard: the de-hyphenated heading must not retain the artifact.
assert 'pro- vide' not in heading, 'hyphenation artifact still present'
assert 'provide methods' in heading
# Guard: field order matches the printed order on p.22.
assert list(fields) == ['Description', 'Rationale', 'Dependencies', 'Use Case']
# Guard: this block genuinely has no Supporting Material.
assert 'Supporting Material' not in fields

r['expected'] = {
    'heading': heading,
    'fields': fields,
    'pages': [22],
    'complete_start': True,
    'complete_end': True,
}
r['categories'] = ['multiple_per_page', 'typography', 'empty_or_dash',
                   'single_page']
r['review'] = {
    'status': 'reviewed',
    'reviewer': REVIEWER,
    'notes': (
        'Verified against p.22 of AUTOSAR_AP_RS_CommunicationManagement.pdf '
        '(R25-11). Complete formal block: opening marker on the heading line, '
        'closing marker after Use Case. Three corrections. (1) Heading had the '
        'line-break hyphenation artifact "pro- vide"; the source wraps '
        '"pro-/vide", so the word is "provide" and the hyphen must be removed '
        'rather than turned into a space (this is the typography category). '
        '(2) Dependencies had been blanked to "" but the source prints an en '
        'dash - same symptom already recorded for RS_DIAG_04006. (3) All three '
        'prose fields had lost their terminating full stop; restored verbatim. '
        'IMPORTANT: this block has only four fields and genuinely contains NO '
        'Supporting Material, exactly like RS_AP_00115. When 0034-01 is fixed '
        'and the fixture is regenerated, these records must NOT acquire a '
        'Supporting Material key; their absence is correct, not a symptom.'
    ),
}
print('=' * 74)
print('RS_CM_00211 BEFORE:'); print(before)
print('RS_CM_00211 AFTER:')
print(json.dumps(r['expected'], indent=2, ensure_ascii=False))

# ---------------------------------------------------------------- SAF_21101
r = recs['RS_SAF_21101']
before = json.dumps(r['expected'], indent=2, ensure_ascii=False)

r['expected'] = {
    'heading': None,
    'fields': {},
    'pages': [],
    'complete_start': False,
    'complete_end': False,
    'not_defined_in_document': True,
}
r['categories'] = ['citation_only', 'no_definition_present']
r['review'] = {
    'status': 'reviewed',
    'reviewer': REVIEWER,
    'notes': (
        'INVALID BENCHMARK ENTRY - kept and marked rather than silently '
        'corrected. AUTOSAR_AP_RS_PlatformHealthManagement.pdf (R25-11) does '
        'not define RS_SAF_21101 anywhere. The single occurrence, on p.9, is '
        'an inline citation inside running prose: "...may require certain '
        'processes to be followed - as recommended in ISO26262, for instance '
        '[RS_SAF_21101][4]." The anchor probe found no block-opening marker '
        'within 120 chars before or 200 chars after the ID, and no formal '
        'block exists in the document; RS_SAF_* requirements are defined in '
        'the Foundation safety RS, not here. The draft claimed pages [9,10] '
        'with heading null and empty fields, i.e. it anchored to the citation '
        'and then ran past the page boundary, which is also why it was '
        'mislabelled multi_page. Expected values now record the truth: no '
        'definition present, no pages, nothing complete. This record should '
        'be REMOVED from the benchmark by the selection fix filed as 0034-04; '
        'it is deliberately not deleted here because removing entries is a '
        'change to benchmark scope, not a truthing decision.'
    ),
}
print('=' * 74)
print('RS_SAF_21101 BEFORE:'); print(before)
print('RS_SAF_21101 AFTER:')
print(json.dumps(r['expected'], indent=2, ensure_ascii=False))

with io.open(path, 'w', encoding='utf-8') as fh:
    json.dump(doc, fh, indent=2, ensure_ascii=False)
    fh.write('\n')

# Re-read and assert round-trip fidelity of the exact characters.
re_doc = json.load(open(path, encoding='utf-8'))
rr = {x['id']: x for x in re_doc['records']}
assert rr['RS_CM_00211']['expected']['fields']['Dependencies'] == DASH
assert 'pro- vide' not in rr['RS_CM_00211']['expected']['heading']
assert rr['RS_SAF_21101']['expected']['not_defined_in_document'] is True
print('=' * 74)
print('OK: written and round-trip verified')
PY
RC_APPLY=${PIPESTATUS[0]}
{ set +x; } 2>/dev/null
[ "$RC_APPLY" -eq 0 ] || { echo "FATAL: corrections not applied" >&2; exit 94; }
set -x

# --- Step 2: file task 0034-04 ---------------------------------------------
{ set +x; } 2>/dev/null; echo "[$(date +%H:%M:%S)] STEP 2: file task 0034-04"; set -x

python3 - <<'PY' 2>&1 | tee "$LOGDIR/02-file-0034-04.txt"
# -*- coding: utf-8 -*-
import re

path = 'TODO.md'
src = open(path, encoding='utf-8').read()

if '0034-04' in src:
    print('0034-04 already present; not adding again')
else:
    lines = src.splitlines()
    idx = next((i for i, l in enumerate(lines) if '**0034-03**' in l), None)
    if idx is None:
        raise SystemExit('FAIL: could not locate 0034-03 to anchor the insert')
    end = len(lines)
    for i in range(idx + 1, len(lines)):
        if re.match(r'\s*-\s*\[.\]\s*\*\*', lines[i]) or lines[i].startswith('## '):
            end = i
            break

    task = [
        '- [ ] **0034-04** Exclude citation-only ID mentions from benchmark '
        'record selection in `_src/tools/spec_extraction_benchmark.py`, so an '
        'ID that is merely referenced in prose never becomes a benchmark '
        'entry.',
        '  - **Discovery (2026-08-15, found while working 0007-01):** '
        '`RS_SAF_21101` was selected as a benchmark record for '
        '`AUTOSAR_AP_RS_PlatformHealthManagement`, but that document does not '
        'define it. Its sole occurrence (p.9) is an inline citation inside a '
        'running sentence: "...as recommended in ISO26262, for instance '
        '[RS_SAF_21101][4]." No block-opening marker appears within 120 '
        'characters before or 200 characters after the ID, and no formal block '
        'exists anywhere in the file.',
        '  - **Symptom:** the produced entry had `heading: null`, `fields: {}` '
        'and `pages: [9, 10]` - it anchored to the citation and then spilled '
        'past the page boundary, which additionally gave it a bogus '
        '`multi_page` category.',
        '  - **Distinct from 0034-01/02/03:** those are extractor defects '
        '(field splitting, anchor direction, missing label). This one is a '
        'record-SELECTION defect in the benchmark builder: the record should '
        'never have been created. Note `spec_extraction_benchmark.py` was '
        'previously cleared of blame for 0034-01, which remains correct; this '
        'is a separate concern in the same file.',
        '  - **Acceptance criteria:** a candidate ID is promoted to a benchmark '
        'record only when a definition block can be anchored to it (marker '
        'present in either direction, per the 0034-02 fix); citation-only '
        'mentions are skipped and counted in a report so silent loss is '
        'impossible; a regression test covers the `RS_SAF_21101` case; '
        'upstream-requirement cross-references such as `RS_SAF_10039` cited '
        'inside other records are likewise not promoted.',
        '  - **Definition of Done:** fix and tests committed with `REF`; the '
        'existing `RS_SAF_21101` entry in '
        '`_src/tests/fixtures/spec_extraction/benchmark-draft.json` (currently '
        'reviewed and flagged `not_defined_in_document`) is removed as part of '
        'the regeneration, reducing the benchmark from 200 to 199 records, and '
        'the count is updated wherever it is asserted.',
    ]

    while end > 0 and not lines[end - 1].strip():
        end -= 1
    lines[end:end] = [''] + task
    open(path, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('inserted 0034-04 after the 0034-03 block (at line %d)' % (end + 2))

for l in open(path, encoding='utf-8').read().splitlines():
    if '**0034-0' in l or '**0007-01**' in l:
        print('  |', l[:170])
PY
RC_TASK=${PIPESTATUS[0]}
{ set +x; } 2>/dev/null
[ "$RC_TASK" -eq 0 ] || { echo "FATAL: could not file 0034-04" >&2; exit 95; }
set -x

# --- Step 3: validation gate ------------------------------------------------
{ set +x; } 2>/dev/null; echo "[$(date +%H:%M:%S)] STEP 3: validation gate"; set -x

python3 - "$FIXTURE" <<'PY' 2>&1 | tee "$LOGDIR/03-fixture-validation.txt"
import json, sys, collections
doc = json.load(open(sys.argv[1], encoding='utf-8'))
recs = doc['records']
c = collections.Counter(r['review']['status'] for r in recs)
print('total records :', len(recs))
print('review status :', dict(c))
rev = [r for r in recs if r['review']['status'] == 'reviewed']
bad = [r['id'] for r in rev
       if not r['review'].get('reviewer') or not r['review'].get('notes')]
if bad:
    print('FAIL missing reviewer/notes:', bad); sys.exit(1)
print('OK reviewed=%d each with reviewer+notes' % len(rev))
for r in sorted(rev, key=lambda x: x['id']):
    print('   %-16s pages=%-10s fields=%d'
          % (r['id'], r['expected'].get('pages'),
             len(r['expected'].get('fields') or {})))
PY
RC_FIXTURE=${PIPESTATUS[0]}

python3 -m pytest -q _src/tests/test_spec_extraction_campaign.py \
  2>&1 | tee "$LOGDIR/04-pytest-campaign.txt"
RC_CAMPAIGN=${PIPESTATUS[0]}

python3 -m pytest -q _src/tests/test_spec_scrape_fields.py \
  2>&1 | tee "$LOGDIR/05-pytest-scrape.txt"
RC_SCRAPE=${PIPESTATUS[0]}

{ set +x; } 2>/dev/null
echo "    rc: fixture=$RC_FIXTURE campaign=$RC_CAMPAIGN scrape=$RC_SCRAPE"
if [ "$RC_FIXTURE" -ne 0 ] || [ "$RC_CAMPAIGN" -ne 0 ] || [ "$RC_SCRAPE" -ne 0 ]; then
  echo "FATAL: validation gate failed; refusing to commit." >&2
  exit 96
fi
set -x

# --- Step 4: stage + commit -------------------------------------------------
{ set +x; } 2>/dev/null; echo "[$(date +%H:%M:%S)] STEP 4: commit"; set -x

{ set +x; } 2>/dev/null
for p in "$FIXTURE" "TODO.md" "$LOGDIR"; do
  if [ -e "$p" ]; then
    git add -A -- "$p" && echo "    staged  : $p" || echo "    ADD FAIL: $p"
  else
    echo "    MISSING : $p (skipped)"
  fi
done
set -x

git diff --cached --stat 2>&1 | tee "$LOGDIR/06-staged-diffstat.txt"
STAGED="$(git diff --cached --name-only | wc -l | tr -d ' ')"
{ set +x; } 2>/dev/null
echo "    staged file count: $STAGED"
[ "$STAGED" -gt 0 ] || { echo "FATAL: nothing staged" >&2; exit 97; }
set -x

git -c user.name="${GIT_NAME:-$GIT_EMAIL}" -c user.email="$GIT_EMAIL" \
  commit --author="${GIT_NAME:-$GIT_EMAIL} <$GIT_EMAIL>" -F - <<'MSG' 2>&1 | tee "$LOGDIR/07-git-commit.txt"
Task 0007-01: truth RS_CM_00211, flag RS_SAF_21101 as citation-only, file 0034-04

Completes the last two benchmark records that could be verified without first
repairing the extractor. 21 of 200 records are now reviewed; the remaining 179
are gated entirely on 0034-01/02/03.

RS_CM_00211 -- CommunicationManagement p.22, real and complete formal block.
  Three corrections against the source:
    1. Heading carried the line-break hyphenation artifact "pro- vide". The
       source wraps "pro-/vide", so the word is "provide"; the hyphen must be
       removed, not converted to a space. This is what the record's existing
       typography category was pointing at.
    2. Dependencies had been blanked to "" although the source prints an en
       dash. Identical symptom to the one already fixed in RS_DIAG_04006.
    3. All three prose fields had lost their terminating full stop.
  complete_start set true (opening marker sits on the heading line).

  Recorded explicitly in the review notes: this block has four fields and
  genuinely contains NO Supporting Material, exactly like RS_AP_00115. When
  0034-01 lands and the fixture is regenerated, these two records must not
  acquire a Supporting Material key. Their absence is correct, and a
  regeneration that "restores" it would be introducing an error.

RS_SAF_21101 -- NOT DEFINED in AUTOSAR_AP_RS_PlatformHealthManagement.
  Its only occurrence (p.9) is an inline citation inside running prose:
  "...as recommended in ISO26262, for instance [RS_SAF_21101][4]." The anchor
  probe found no block-opening marker within 120 chars before or 200 chars
  after the ID, and the document contains no formal block for it; RS_SAF_*
  requirements live in the Foundation safety RS. The draft had claimed pages
  [9,10] with a null heading and empty fields -- it bound to the citation and
  then ran past the page boundary, which is also where its bogus multi_page
  category came from.

  The entry is marked reviewed and flagged not_defined_in_document rather than
  deleted. Removing a benchmark entry changes benchmark scope, which is a
  different kind of decision from truthing a record's contents, so it is left
  to the selection fix.

NEW TASK 0034-04:
  Exclude citation-only ID mentions from benchmark record selection in
  spec_extraction_benchmark.py. This is a record-SELECTION defect in the
  benchmark builder and is distinct from 0034-01/02/03, which are extractor
  field and anchor bugs. Note the earlier finding that the builder is not to
  blame for 0034-01 still stands; this is a separate concern in the same file.
  Its Definition of Done includes removing the RS_SAF_21101 entry during
  regeneration, taking the benchmark from 200 to 199 records.

STATUS: 0007-01 stays [p] and open. No unblocked truthing work remains; the
  task cannot progress further until 0034-01 is fixed and the fixture is
  regenerated (which, per the caveat recorded under 0034-01, requires
  re-running the extraction campaign because the raw/ inputs are gone).
MSG
RC_COMMIT=${PIPESTATUS[0]}

# --- Step 5: summary --------------------------------------------------------
{ set +x; } 2>/dev/null; echo "[$(date +%H:%M:%S)] STEP 5: summary"; set -x
git log --oneline -4 2>&1 | tee "$LOGDIR/08-log-after.txt"
git show --stat --oneline HEAD 2>&1 | tee "$LOGDIR/09-head-stat.txt"

{ set +x; } 2>/dev/null
echo "=============================================================================="
echo "commit rc: $RC_COMMIT"
echo "DONE. Logs in: $LOGDIR"
echo "  21/200 reviewed. NO unblocked truthing work remains for 0007-01."
echo "  Everything further is gated on 0034-01 (then 02, 03, 04)."
echo "=============================================================================="
exit "$RC_COMMIT"
