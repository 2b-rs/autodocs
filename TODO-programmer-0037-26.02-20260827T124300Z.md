# Claim: Subtask 0037-26.02

owner_token: agent:programmer-0037-26-02:0037-26.02:20260827T124300Z
agent: programmer-0037-26-02
persona: unprivileged Programmer (distinct from dispatcher gabriel)
capability_class: unprivileged
execution_authority: direct git/test execution in own worktree; no runner queue
task: 0037-26.02
feature: 0037
branch: 0037-26.02
worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0037-26.02
state: [x]

## Completion (2026-08-27)

Substantive REF `6eb4f9296034b79cf6d6ebcbb2b2fa7590da0375`.
Validation: `python3 -m unittest _src.tests.test_campaign_manifest` 13/13 OK in
`/Users/tobias.anton/devel/autodocs/.worktrees/0037-26.02`.

AE-2 baselines: pre-change `2064704457f98c66fb6f77ad3c263415864fe2ff`; candidate `6eb4f9296`.
AE-3 falsification (mtime-only must not change evidence identity): red on baseline
`corpus_hash` `f0710015` → `58795203`; green on candidate `content_set_digest`
`sha256:f188902d1cea496763bcc6c1b78bca40d2a403f24bf2f551d40f305012d86b9a` unchanged.
AE-4 adjacent: (1) record byte change alters `content_set_digest`; (2) adding a
record alters both hint and identity; (3) legacy listing files keep original bytes
and get `disposition.kind=legacy`.
AE-5: `test_content_set_identity_property_independent_of_mtime_and_walk_order`
25 cases, seed `20260827`, invariant sorted (path, digest, size) independent of mtime.


## Start / base discovery

- Dispatcher-named start tip: `2064704457f98c66fb6f77ad3c263415864fe2ff`
  (`bookkeeping(0037-19): mark [x], record REF c2f198e19 and validation`)
- Independently remesured on that tip:
  - `0037-19` `[x]` with REF `c2f198e19`
  - `0037-17` `[x]`
- Parent Task branch `0037-26` does not exist; this Subtask branch is cut from
  the named start tip (which already contains 0037-19). Merged prerequisite
  tips: `0037-19` is an ancestor of HEAD (`2064704457f98c66fb6f77ad3c263415864fe2ff`).
- Caveat (R2): this line sits on the 0037-16 candidate base. If checkpoint
  `F-0037-16-R2-01` is later rejected, rebase.

## Task text (verbatim)

- [ ] **0037-26.02** PREREQ: 0037-26.02:0037-17, 0037-26.02:0037-19 Extend `_src/spec/campaigns/*.json` writers with immutable campaign snapshots and content manifests.
  - **Acceptance criteria:** Adapt `campaign-manifest@v1` without rewriting history; replace listing/mtime `corpus_hash` as evidence identity with a sorted content artifact set while retaining it only as a staleness hint; link trigger issue/criterion, runs, queue snapshot, decisions, published reports, source/tool/config commits, and scope.
  - **Definition of Done:** Migration and producer tests prove old manifests receive explicit legacy disposition, new snapshots are immutable/queryable, content changes alter identity, and mtime-only changes do not.

## Write scope

- `_src/tools/campaign_manifest.py` (writers for `_src/spec/campaigns/*.json`)
- `_src/tests/test_campaign_manifest.py` (focused migration/producer tests)
- this claim file
- `TODO.md` 0037-26.02 block only

## Must not

Acceptance; main; DONE.md; 0037-16 STOP lift; sibling 26.*/27.*;
0037-16/19/20/38/42 product; shared root checkout; memory_append; push;
foreign claims.

## Assumptions

- Existing on-disk `campaign-manifest@v1` files that identify the corpus via
  listing/mtime `corpus_hash` are legacy; they are adapted in-memory with an
  explicit legacy disposition and are not rewritten.
- Evidence identity is the sorted content artifact set (path, content digest,
  size). `corpus_hash()` remains a listing/mtime staleness hint only.
- New snapshot files are exclusive-create / replay; content-identical writes
  do not mutate bytes; a content change yields a new snapshot identity.
