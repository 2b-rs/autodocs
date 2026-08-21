import hashlib,json,subprocess
from pathlib import Path
R=Path.cwd(); O=R/'docs/pipeline/approvals/0019-acceptance-packages'; E='docs/pipeline/approvals/0019-acceptance-packages/evidence-20260821T011000Z'
T=[('0019-01','111a5b90527cb6cb5f2b5bdcf8fad3a0237c41dd','af91b40a715d8caef56c24bd5379bc2cd20f969d',[], 'BOM completeness, pin rejection, and reproducibility-boundary validation.'),('0019-02','70eed7eb047f169817ac8bc2b16ac0cf5d203239','3b92a9cd059e6ff0e356c31ca8bd1a019c379c72',['0019-01'],'Offline retained-archive/inventory reconstruction and tamper rejection.'),('0019-03','81a2f03ee8505cbcfbd323bae183de0ef5403abe','b08a4a362cce7192017a7d245650cb61e12b60cc',['0019-01'],'Profile checks for all four kinds and declared reject/review/queue conditions.'),('0019-04','6f1007fbb549f762cb90b95cefcc9c3d4b9e5f3c','f2795a1eb496ffb99b48b6606bb77b266d103a3f',['0019-02','0019-03'],'Pinned offline extraction, deterministic output, and negative/atomic-failure checks.'),('0019-05','6e420c1ed930743e8f533e72c18bb02701afb4f1','47f5e76f95cf7c3a7ae6db583d46e2056cfbae6a',['0019-04'],'Canonical identity/provenance/hash materialization, repeatability, collision and contradiction handling.'),('0019-06','43968b25fb23bb26e236bd3f420fce0cc1eef9af','e50a3db8d153bf5a682618a64a19b0e4f2c5d6c7',['0019-05'],'Machine/human report generation plus negative fixture for every validation class.')]
def g(*a): return subprocess.check_output(['git',*a],cwd=R)
def h(x): return hashlib.sha256(x).hexdigest()
def rl(p):
 if p.startswith('_src/tests/'): return 'test/fixture','application/json' if p.endswith('.json') else 'text/x-python'
 if p.startswith('_src/tools/'): return 'implementation tool','text/x-python'
 if '/snapshots/' in p: return 'retained immutable source snapshot','application/x-tar' if p.endswith('.tar') else 'application/json'
 if p.startswith('_src/spec/'): return 'campaign/profile/report artifact','application/json'
 if p.startswith('docs/'): return 'normative/supporting documentation','text/markdown'
 if p.startswith('provenance/'): return 'verbatim user-prompt provenance','text/plain'
 if p.startswith('TODO-'): return 'implementation claim/provenance','text/markdown'
 return 'authoritative task bookkeeping snapshot','text/markdown'
def contract(task):
 s=(R/'TODO.md').read_text(); a=s.index('- [x] **'+task+'**'); b=s.find('\n- [',a+1); z=s[a:b if b>0 else None].splitlines(); return '\n'.join([z[0]]+[x for x in z if '**Acceptance criteria:**' in x or '**Definition of Done:**' in x])+'\n'
head=g('rev-parse','HEAD').decode().strip(); fresh=h((R/E/'focused-suite.txt').read_bytes()); prompt=h((O/'20260821T011000Z-user-prompt.txt').read_bytes())
for task,ref,book,pre,focus in T:
 c=contract(task); parent=g('rev-parse',ref+'^').decode().strip(); tree=g('rev-parse',ref+'^{tree}').decode().strip(); A=[]
 for p in g('diff-tree','--no-commit-id','--name-only','-r',ref).decode().splitlines():
  data=g('show',ref+':'+p); role,media=rl(p); A.append({'path':p,'role':role,'classification':'source' if role in ('implementation tool','normative/supporting documentation','authoritative task bookkeeping snapshot') else 'generated/retained evidence','media_type':media,'git_blob':g('rev-parse',ref+':'+p).decode().strip(),'bytes':len(data),'sha256':h(data)})
 M={'schema':'0019-acceptance-work-product-manifest@v1','task':task,'candidate_substantive_ref':ref,'candidate_parent':parent,'candidate_tree':tree,'observed_direct_scope':[x['path'] for x in A],'artifacts':A}; mp=O/(task+'-work-product-manifest.json'); mp.write_text(json.dumps(M,indent=2,sort_keys=True)+'\n'); mh=h(mp.read_bytes())
 ps='None (first package in upstream chain).' if not pre else ', '.join('`'+x+'` implementation `[x]`, no current acceptance record (batch review inconclusive)' for x in pre)+'.'
 rows='\n'.join('| '+x.split('**',2)[1]+' | Candidate manifest plus focused tests | `evidence-20260821T011000Z/focused-suite.txt` | Evidence prepared; no decision |' for x in c.splitlines()[1:])
 md=f'''# Review-handoff package — {task}

**Status:** append-only evidence preparation only; this is not an acceptance review or an `Acceptance: ✓` record.

## Identity and immutable baseline

| Field | Value |
| --- | --- |
| Feature / Task | `0019` / `{task}` |
| Candidate substantive REF | `{ref}` |
| Candidate parent / tree | `{parent}` / `{tree}` |
| Separate bookkeeping REF | `{book}` |
| Exact contract SHA-256 | `{h(c.encode())}` |
| Manifest / SHA-256 | [`{mp.name}`]({mp.name}) / `{mh}` |
| Authority epoch | Legacy `TODO.md`/`DONE.md`; no acceptance authority exercised |
| Batch finding | `c7f384497972cf703ae34b2571563b804b03d63f`: missing package information |

### Exact normative task contract
```text
{c}```

## Authoritative manifest and scope

The manifest lists every direct path changed by the exact substantive commit with role, source/generated-retained class, media type, Git blob, byte count, and SHA-256.

- **Declared scope:** task-local implementation/evidence only; no queue, acceptance, integration, publication, remote, configuration, or `DONE.md` operation.
- **Observed scope:** exact `git diff-tree --no-commit-id --name-only -r {ref}` paths only; no assertion about uncommitted, external, or later-branch content.
- **Derived prerequisite state:** {ps}
- **External/evidence scope:** no fresh network/external mutation; retained archive bytes are manifest-bound and checked offline. Evidence is this package and `{E}`.

## Criterion matrix
| Normative condition | Implementation / validation mapping | Immutable evidence | Disposition |
| --- | --- | --- | --- |
{rows}

## Prerequisite and review state

The transitive implementation chain is `0019-01` → `0019-02`/`0019-03` → `0019-04` → `0019-05` → `0019-06`; all are `[x]`. None has a current acceptance record. The independent batch at `c7f384497972cf703ae34b2571563b804b03d63f` is `inconclusive`; this package neither alters nor supersedes it.

## Validation profile and immutable results

- Fresh bounded offline profile on evidence-preparation tree `{head}`: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v _src.tests.test_score_campaign_manifest _src.tests.test_score_source_snapshot _src.tests.test_score_import_profile _src.tests.test_score_extraction_adapter _src.tests.test_score_normalization _src.tests.test_validate_score`.
  - **PASS:** 34 tests in 14.497s; output [`focused-suite.txt`](evidence-20260821T011000Z/focused-suite.txt), SHA-256 `{fresh}`. Relevant coverage: {focus}
- Fresh checks: [`manifest-complete.txt`](evidence-20260821T011000Z/manifest-complete.txt), SHA-256 `1a067230f1dd4edcec13b1d193558d10797fcab4ca89adc1cec3a26721c17da3`; [`snapshot-verify.txt`](evidence-20260821T011000Z/snapshot-verify.txt), SHA-256 `53402b50048e2d18bf14885d75141a86d16689131af43fc3359e38f2d34a6c75`.
- Fresh checks are supplementary descendant-tree evidence, not a statement that an acceptance reviewer independently reproduced each historical candidate environment.

## Findings, risks, and provenance

1. **Open acceptance gate:** no prerequisite has a current accepted boundary. An independently assigned privileged reviewer must inspect packages bottom-up and decide each task.
2. **Bounded execution:** validation was local/offline; it did not contact upstream or mutate records, queues, generated HTML, configuration, keys, remotes, or publication state.
3. **Lifecycle boundary:** candidates remain discovered/unqueued where applicable; `0019-07` and later own curation, curator decision, and publication.
4. Management prompt: [`20260821T011000Z-user-prompt.txt`](20260821T011000Z-user-prompt.txt), SHA-256 `{prompt}`. Candidate claims/commit provenance are manifest-enumerated when changed by that candidate. The prior batch remains immutable inconclusive evidence.
'''
 (O/(task+'.md')).write_text(md)
