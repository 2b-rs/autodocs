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
TITLE: EVIDENCE GATHERING FOR RS_SAF_21101 / RS_CM_00211 + BOOKKEEPING REPAIR
==============================================================================

WHY THIS RUN DOES NOT ALSO WRITE THE TRUTHED VALUES
  Truthing means comparing the draft fixture against the words actually
  printed in the source PDF and deciding what is correct. That judgement
  cannot be delegated to a script: a script that "corrected" fields without a
  human-or-agent reading of the source would be inventing data, which is
  exactly the class of error this benchmark exists to catch.
  Therefore this run is READ-ONLY with respect to the fixture. It extracts the
  evidence; the next run applies the reviewed edits.

STRUCTURE
  Step 0  Preflight: repo, identity, log dir, script snapshot.
  Step 1  BOOKKEEPING REPAIR. The previous run logged
            "WARN working-copy reference not on the task line"
          The [p] marker landed correctly but the reference to
          TODO-agent-0007-01.md did not attach to the 0007-01 line (the old
          script computed an insertion offset against the pre-substitution
          string). Locate any stray reference, remove it, and re-attach it to
          the real 0007-01 bullet. SANDBOX.md requires that reference.
  Step 2  Locate the two source PDFs for RS_SAF_21101 and RS_CM_00211,
          deriving document names from the fixture rather than guessing.
  Step 3  Dump the draft's current expected values for both records.
  Step 4  Extract, IN PARALLEL (2 jobs), every page of each PDF that mentions
          the ID in any case variant, printing full page text plus a
          lookahead/lookbehind probe for the block-opening marker. The probe
          matters because defect 0034-02 showed the marker can precede the ID.
  Step 5  Commit the bookkeeping repair and the evidence logs. The fixture is
          NOT touched, so it is not staged.

GOAL HIERARCHY
  PRIMARY  Put me in a position to truth the last two unblocked records
           correctly on the next turn, with the source text in hand.
    SUB-1  Close the SANDBOX.md working-copy-reference gap left by the WARN.
    SUB-2  Capture evidence in a form that shows mixed-case IDs (as seen with
           RS_Diag_04005/04006) and marker-before-ID anchoring, so I do not
           repeat the false-negative grep from earlier in this session.
    SUB-3  Keep the unrelated 17 modified files out of the commit.
  NON-GOAL No fixture edits. No extractor changes. Nothing touching Feature
           0021 or TODO-perplexity.md, which belong to another agent.

RESOURCE ESTIMATE
  Data traffic .... none (no network; local PDFs already cached on disk)
  CPU load ........ light. Two pypdf full-document text extractions run
                    concurrently; each RS PDF is 50-100 pages, roughly 2-5 s
                    of CPU apiece.
  Workers ......... 2 parallel extraction jobs. Only two documents are in
                    scope, so 2 is the natural width; spawning more of the 12
                    available CPUs would leave them idle.
  Wall-clock ...... < 30 seconds expected
  Writes .......... TODO.md (one line repaired), logs/<purpose>/<ts>/ (new),
                    one git commit. Fixture untouched.
==============================================================================
BANNER
set -x

# --- Step 0: preflight -----------------------------------------------------
{ set +x; } 2>/dev/null; echo "[$(date +%H:%M:%S)] STEP 0: preflight"; set -x

cd /tmp/autodocs || { echo "FATAL: /tmp/autodocs not found" >&2; exit 90; }

PURPOSE="spec-truthing-evidence"
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

# --- Step 1: bookkeeping repair --------------------------------------------
{ set +x; } 2>/dev/null; echo "[$(date +%H:%M:%S)] STEP 1: repair working-copy reference"; set -x

python3 - <<'PY' 2>&1 | tee "$LOGDIR/01-repair-reference.txt"
import re

path = 'TODO.md'
src  = open(path, encoding='utf-8').read()
lines = src.splitlines()
REF = '(in progress by agent-0007-01, see `TODO-agent-0007-01.md`)'

print('--- BEFORE: every line mentioning the working copy or 0007-01 ---')
for i, l in enumerate(lines):
    if 'TODO-agent-0007-01' in l or '0007-01' in l:
        print('  %4d | %s' % (i + 1, l[:150]))

# 1. strip any stray/misplaced reference anywhere in the file
stray = 0
for i, l in enumerate(lines):
    if 'TODO-agent-0007-01.md' in l and not re.search(r'\*\*0007-01\*\*', l):
        cleaned = l.replace(' ' + REF, '').replace(REF, '')
        cleaned = re.sub(r'\s*\(in progress by agent-0007-01[^)]*\)', '', cleaned)
        if cleaned != l:
            lines[i] = cleaned
            stray += 1
            print('  stripped stray reference from line %d' % (i + 1))
            if not cleaned.strip():
                print('  NOTE line %d is now blank; leaving it in place' % (i + 1))
print('stray references removed:', stray)

# 2. attach the reference to the real 0007-01 bullet
idx = next((i for i, l in enumerate(lines) if '**0007-01**' in l), None)
if idx is None:
    raise SystemExit('FAIL: no 0007-01 bullet found')

line = lines[idx]
if not re.search(r'\[p\]', line):
    line = re.sub(r'^(\s*-\s*)\[[ x]\]', r'\1[p]', line, count=1)
    print('  re-applied [p] marker')

if 'TODO-agent-0007-01.md' in line:
    print('  reference already on the task line; nothing to add')
else:
    line = line.rstrip() + ' ' + REF
    print('  appended reference to the 0007-01 line')

lines[idx] = line
open(path, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

print('--- AFTER ---')
for i, l in enumerate(open(path, encoding='utf-8').read().splitlines()):
    if 'TODO-agent-0007-01' in l or '0007-01' in l:
        print('  %4d | %s' % (i + 1, l[:200]))

final = open(path, encoding='utf-8').read()
tl = next(l for l in final.splitlines() if '**0007-01**' in l)
assert '[p]' in tl, 'FAIL: [p] lost'
assert 'TODO-agent-0007-01.md' in tl, 'FAIL: reference not attached'
print('OK: 0007-01 is [p] and carries the working-copy reference')
PY
RC_REPAIR=${PIPESTATUS[0]}
{ set +x; } 2>/dev/null
[ "$RC_REPAIR" -eq 0 ] || { echo "FATAL: bookkeeping repair failed" >&2; exit 94; }
set -x

# --- Step 2 + 3: locate PDFs and dump draft expectations --------------------
{ set +x; } 2>/dev/null; echo "[$(date +%H:%M:%S)] STEP 2+3: locate PDFs, dump draft expectations"; set -x

python3 - "$FIXTURE" <<'PY' 2>&1 | tee "$LOGDIR/02-targets-and-draft.txt"
import json, sys, os, glob

doc = json.load(open(sys.argv[1], encoding='utf-8'))
targets = ['RS_SAF_21101', 'RS_CM_00211']
mapping = {}

for rid in targets:
    rec = next((r for r in doc['records'] if r['id'] == rid), None)
    print('=' * 74)
    if rec is None:
        print(rid, '-> NOT PRESENT IN FIXTURE'); continue
    print('RECORD :', rid)
    print('DOCUMENT:', rec['document'])
    print('STATUS  :', rec['review']['status'])
    print('CATEGORIES:', rec.get('categories'))
    print('DRAFT EXPECTED:')
    print(json.dumps(rec['expected'], indent=2, ensure_ascii=False))

    hits = glob.glob('_src/spec/pdf-cache/**/%s.pdf' % rec['document'], recursive=True)
    print('PDF CANDIDATES:', hits)
    if hits:
        mapping[rid] = hits[0]
    else:
        print('WARN no PDF found for', rec['document'])

with open('/tmp/truthing-targets.json', 'w') as fh:
    json.dump(mapping, fh, indent=2)
print('=' * 74)
print('resolved mapping:', json.dumps(mapping, indent=2))
PY
RC_TARGETS=${PIPESTATUS[0]}
{ set +x; } 2>/dev/null
[ "$RC_TARGETS" -eq 0 ] || { echo "FATAL: could not resolve targets" >&2; exit 95; }
set -x

# --- Step 4: parallel PDF evidence extraction -------------------------------
{ set +x; } 2>/dev/null; echo "[$(date +%H:%M:%S)] STEP 4: extract PDF evidence (2 parallel jobs)"; set -x

cat > /tmp/extract_evidence.py <<'PY'
import json, re, sys, pypdf

rid = sys.argv[1]
mapping = json.load(open('/tmp/truthing-targets.json'))
path = mapping.get(rid)
if not path:
    print('NO PDF MAPPED FOR', rid); raise SystemExit(0)

print('RECORD :', rid)
print('PDF    :', path)
reader = pypdf.PdfReader(path)
print('PAGES  :', len(reader.pages))

# Case-insensitive: this document family mixes RS_DIAG_ and RS_Diag_ forms,
# and an exact-case grep produced a false negative earlier in this session.
stem = rid.replace('RS_', '').replace('_', '')
pat = re.compile(re.escape(rid).replace('_', '_'), re.I)
loose = re.compile(r'RS[_ ]?' + rid.split('_', 1)[1].replace('_', '[_ ]?'), re.I)

texts = []
for i, p in enumerate(reader.pages):
    try:
        t = p.extract_text() or ''
    except Exception as exc:                      # noqa: BLE001
        t = ''
        print('  WARN extract failed on page %d: %s' % (i + 1, exc))
    texts.append(t)

hits = [i for i, t in enumerate(texts) if pat.search(t) or loose.search(t)]
print('PAGES MENTIONING ID (1-based):', [i + 1 for i in hits])

full = '\n'.join(texts)
variants = sorted(set(m.group() for m in loose.finditer(full)))
print('ID SPELLINGS SEEN:', variants)

# Anchor probe: 0034-02 showed the opening marker can PRECEDE the ID line.
for m in loose.finditer(full):
    s, e = m.start(), m.end()
    before = full[max(0, s - 120):s]
    after  = full[e:e + 200]
    print('-' * 70)
    print('occurrence at offset', s)
    print('  marker in 120 chars BEFORE:', '\u2308' in before)
    print('  marker in 200 chars AFTER :', '\u2308' in after)
    print('  context before:', repr(before[-90:]))
    print('  context after :', repr(after[:120]))

print('=' * 74)
for i in hits:
    print('########## PAGE %d ##########' % (i + 1))
    print(texts[i])
    print()
PY

{ set +x; } 2>/dev/null
pids=()
for rid in RS_SAF_21101 RS_CM_00211; do
  ( python3 /tmp/extract_evidence.py "$rid" > "$LOGDIR/03-evidence-$rid.txt" 2>&1 ) &
  pids+=($!)
  echo "    launched extraction job for $rid (pid ${pids[-1]})"
done

# progress heartbeat at least every 5 s (SANDBOX.md)
while :; do
  running=0
  for p in "${pids[@]}"; do kill -0 "$p" 2>/dev/null && running=$((running+1)); done
  [ "$running" -eq 0 ] && break
  echo "    [$(date +%H:%M:%S)] $running extraction job(s) still running..."
  sleep 3
done

RC_EXTRACT=0
for p in "${pids[@]}"; do wait "$p" || RC_EXTRACT=1; done
echo "    extraction rc: $RC_EXTRACT"
for rid in RS_SAF_21101 RS_CM_00211; do
  f="$LOGDIR/03-evidence-$rid.txt"
  echo "    $f : $(wc -l < "$f" | tr -d ' ') lines"
  echo "    ---- summary head for $rid ----"
  head -n 12 "$f"
done
set -x

# --- Step 5: commit the repair + evidence (fixture NOT touched) -------------
{ set +x; } 2>/dev/null; echo "[$(date +%H:%M:%S)] STEP 5: commit"; set -x

python3 -m pytest -q _src/tests/test_spec_extraction_campaign.py \
  2>&1 | tee "$LOGDIR/04-pytest-campaign.txt"
RC_CAMPAIGN=${PIPESTATUS[0]}

{ set +x; } 2>/dev/null
[ "$RC_CAMPAIGN" -eq 0 ] || { echo "FATAL: campaign suite failed" >&2; exit 96; }

for p in "TODO.md" "$LOGDIR"; do
  if [ -e "$p" ]; then
    git add -A -- "$p" && echo "    staged  : $p" || echo "    ADD FAIL: $p"
  else
    echo "    MISSING : $p (skipped)"
  fi
done
set -x

git diff --cached --stat 2>&1 | tee "$LOGDIR/05-staged-diffstat.txt"
STAGED="$(git diff --cached --name-only | wc -l | tr -d ' ')"
{ set +x; } 2>/dev/null
echo "    staged file count: $STAGED"
[ "$STAGED" -gt 0 ] || { echo "FATAL: nothing staged" >&2; exit 97; }
set -x

git -c user.name="${GIT_NAME:-$GIT_EMAIL}" -c user.email="$GIT_EMAIL" \
  commit --author="${GIT_NAME:-$GIT_EMAIL} <$GIT_EMAIL>" -F - <<'MSG' 2>&1 | tee "$LOGDIR/06-git-commit.txt"
Task 0007-01: repair working-copy reference, gather source evidence for the last two unblocked records

BOOKKEEPING REPAIR:
  The preceding run (REF 71b1ead5) logged "WARN working-copy reference not on
  the task line". The [p] marker was applied correctly, but the reference to
  TODO-agent-0007-01.md did not attach to the 0007-01 bullet because the
  script computed an insertion offset against the pre-substitution string.
  SANDBOX.md requires the task to carry a reference to the per-agent working
  copy, so this commit strips any stray reference and re-attaches it to the
  real bullet, with an assertion that both [p] and the reference are present.

EVIDENCE GATHERING (no fixture changes in this commit):
  Captures source-PDF text for RS_SAF_21101 and RS_CM_00211, the two records
  still truthable without first fixing the extractor. For each: the draft's
  current expected values, every page mentioning the ID, the exact ID
  spellings found, and a probe recording whether the block-opening marker
  falls before or after each ID occurrence.

  Both probes are deliberate, and both were learned from earlier defects in
  this same task:
    - case-insensitive ID matching, because AUTOSAR_FO_RS_Diagnostics spells
      the IDs RS_Diag_04005 / RS_Diag_04006 and an exact-case search returned
      a false negative during that record's review;
    - marker-before-ID detection, because 0034-02 showed _record_slice()
      mis-anchors precisely when the opening marker precedes the [ID] line.

  The fixture is intentionally NOT modified here. Deciding what a record's
  correct field values are requires reading the source text; a script that
  wrote "corrections" unread would fabricate exactly the kind of error this
  benchmark exists to detect. The reviewed edits follow in the next commit.

STATUS: 0007-01 remains [p] and open, 19/200 reviewed. ~179 of the 181
  pending records stay blocked behind 0034-01/02/03.

SCOPE: unrelated working-tree modifications from earlier sessions, and
  TODO-perplexity.md / Feature 0021 which belong to another agent, are
  deliberately excluded.
MSG
RC_COMMIT=${PIPESTATUS[0]}

# --- summary ---------------------------------------------------------------
{ set +x; } 2>/dev/null
git log --oneline -3 2>&1 | tee "$LOGDIR/07-log-after.txt"
echo "=============================================================================="
echo "commit rc: $RC_COMMIT"
echo "DONE. Logs in: $LOGDIR"
echo "  Evidence files to review next turn:"
echo "    $LOGDIR/02-targets-and-draft.txt"
echo "    $LOGDIR/03-evidence-RS_SAF_21101.txt"
echo "    $LOGDIR/03-evidence-RS_CM_00211.txt"
echo "=============================================================================="
exit "$RC_COMMIT"
