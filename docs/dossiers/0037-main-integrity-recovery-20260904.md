# 0037 main-integrity recovery — incident record and forward-only plan

- **item:** `0037-main-integrity-recovery-20260904`
- **process:** Recovery implementation (privileged, bounded)
- **agent:** `belanna` (B'Elanna Torres, Integrator for Team Voyager)
- **AWARD:** priority offer `1788535034906-76b167db`, atomically confirmed via `offer_status` (winner=belanna, scope `TODO.md,docs/dossiers/0037-main-integrity-recovery-20260904.md`). Execution wake `1788535076819-83ab8edc`, supervisor start directive `1788535154246-8971a233`.
- **Integrator reservation:** `geordi` holds it. This claim does **not** integrate or move `main`; it prepares a candidate and a plan only.
- **User trigger (verbatim, as supplied in the AWARD):** `ok, machst du weiter mit 0037?`
- **Workspace:** branch `0037-main-integrity-recovery-20260904`, worktree `/tmp/0037-main-integrity-recovery-20260904` (disposable, per DAG-lifecycle policy). Root checkout read only — no `git add`, `git commit`, `git reset`, `git restore`, or any mutation performed in `/Users/tobias.anton/devel/autodocs`.

## 1. Root-checkout state at investigation time (read-only)

Observed in `/Users/tobias.anton/devel/autodocs` via `git status --porcelain=v1`:

```
 M TODO.md
?? .worktrees/
?? allowed_signers
```

- `HEAD` = `refs/heads/main` = `f3c5b6df31af609f08760f4eaff814a6aeb5a391` (clean ancestry, matches remote/local `main` ref — not itself in question).
- `TODO.md` has an **uncommitted, dirty working-tree modification** — a governance-adjacent authoritative-backlog file edited directly in the shared root checkout, which `DEC-0044-015` point 1 prohibits ("no authoring ... in the root checkout").
- `.worktrees/` and `allowed_signers` are untracked in root. `.worktrees/` was the subject of an earlier same-day remediation commit (`4ecba9a85b`, "chore: untrack .worktrees to fix root contamination") but is untracked again now — no `.gitignore` entry for it was found in this candidate's checkout of `TODO.md`'s sibling files at the time of writing; this dossier does **not** attempt that fix (out of this claim's scope, which is `TODO.md` + this dossier only). `allowed_signers` is a credential-adjacent filename; it is **untracked**, not committed, so no secret has entered history via this incident — flagged here as a finding for the forward-only plan, not remediated by this claim.

## 2. Exact dirty patch, preserved

Full `git diff -- TODO.md` output at investigation time, captured byte-for-byte:

- **Patch SHA-256:** `38621eb65a054a1cf6790575c5510a3831c4d4693ac540b243a37fdae855699e`
- **Dirty working-tree `TODO.md` SHA-256:** `e0257679fbd69b97f44a772d8df85eecfc167e97302a90fa110ba46f295496f6`
- **Clean `HEAD:TODO.md` SHA-256:** `dbf74c0d0f7ee29503ea80ba6fc7dc868e63a0ff49ad887e01ea7cb595f1e0dc`

```diff
diff --git a/TODO.md b/TODO.md
index 8aed6f2fc1..84ba1ec3ad 100644
--- a/TODO.md
+++ b/TODO.md
@@ -246,7 +246,13 @@ work.
   - **Acceptance criteria:** Every team and named failure/race path has observed results; property boundaries and counts are retained; critical/major findings remain blocking and are not converted to Management questions.
   - **Definition of Done:** Reproducible QA evidence committed against exact candidate digests.
 
-- [ ] **0050-09** (P0) Close the `0050-07` QA coverage gaps: implement the missing mixed-provider, privacy/negative-authorization, and abuse/quota cases against the integrated 0050 candidates.
+- [x] **0050-09** (P0) Close the `0050-07` QA coverage gaps: implement the missing mixed-provider, privacy/negative-authorization, and abuse/quota cases against the integrated 0050 candidates.
+  Claim: `DONE-worf-0050-09-20260901.md`; owner_token: `agent:worf:0050-09:1788297130198-9f234064`.
+  - **Acceptance:** ✓
+    - **Disposition:** `completed`
+    - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
+    - **Authority reference:** `agent-inbox:jadzia→obrien:1788297398812-1ccbbe67` (Offer `1788297398812-1ccbbe67` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
+    - **Accepted at:** `2026-09-01T21:21:49Z`
   - **Task record:** `task_id: "0050-09"; feature_id: "0050"; role: implementer`.
   - **Architecture decisions and sources:** `DEC-0050-001`; the `REQ-0050-*` dimensions left unobserved by `0050-07`; QA report `docs/campaign-evidence/0050-07/qa-report.md` findings `Q-01`, `Q-02`, `Q-03`; Management `decision-1788296208431-408cb2cb` option `opt1`, which authorised exactly this task rather than waiving the gaps.
   - **Prerequisites:** `0050-07`; its closure includes `0050-00..06`.
@@ -902,7 +908,9 @@ The DAG has one start node (`0046-00`) and exactly one terminal integrating node
   - **No-checkpoint rationale:** package aggregates non-operative ingress/store candidates; `0046-00` already gates scope and `0046-06` gates integration.
   - **Acceptance criteria:** Both child candidates share the exact schema/baseline and prove bounded, idempotent, append-only ingestion with privacy metadata.
   - **Definition of Done:** aggregation manifest and focused cross-boundary tests are committed; no authoritative profile mutation occurs.
-  - [ ] **0046-01.01** Build feedback UX/API validation and target/baseline preview.
+  - [x] **0046-01.01** Build feedback UX/API validation and target/baseline preview.
+    Claim: `DONE-data-0046-01.01-1788291575795-ae8796e9.md`; owner_token: `agent:data:0046-01.01:1788291575795-ae8796e9`.
+    Integration review: `DONE-obrien-0046-01.01-integration-20260903.md`; owner_token: `agent:obrien:0046-01.01-integration:1788435625132-d294a044`.
     - **Prerequisites:** `0046-00`.
     - **Test scope:** `unit+integration`; accessibility, target resolution, consent/visibility, bounds, injection-safe rendering and error cases.
     - **Capability profile:** `capability_class=unprivileged; execution_needs=direct; cognitive_demand=high`.
```

## 3. Reflog facts (root checkout, read-only `git reflog --date=iso`)

```
f3c5b6df31 HEAD@{2026-09-04 15:22:51 +0200}: commit: claim(jadzia): record redispatch of 0046 items
e52135a285 HEAD@{2026-09-04 15:14:35 +0200}: commit: chore: fix missing 0037-29 acceptance record in TODO.md
574b1c1afb HEAD@{2026-09-04 15:08:49 +0200}: commit: claim: reclaim tasks from michael post quota recovery
bedb1d784b HEAD@{2026-09-04 15:08:44 +0200}: reset: moving to bedb1d784b
4ecba9a85b HEAD@{2026-09-04 15:07:30 +0200}: reset: moving to HEAD
4ecba9a85b HEAD@{2026-09-04 15:07:14 +0200}: reset: moving to HEAD
4ecba9a85b HEAD@{2026-09-04 15:06:50 +0200}: commit: chore: untrack .worktrees to fix root contamination
75a7c595a4 HEAD@{2026-09-04 14:51:10 +0200}: commit: claim: reclaim tasks from michael post quota recovery
```

Three `reset` entries in a 2-minute window (15:06:50–15:08:49), two of them no-op (`4ecba9a85b` → `4ecba9a85b`, moving to the commit already checked out) and one real (`4ecba9a85b` → `bedb1d784b`). `git reset` executed directly against the root checkout is itself the pattern `DEC-0044-015` names as the mechanism this rule exists to prevent (a reset in a worktree other than root cannot leave root stale, but a reset run *in* root can, and did leave root's index/working tree in the dirty state found here). No `main` ref corruption is evident from the reflog alone — `HEAD` == `refs/heads/main` and both point at a normal, reachable commit (`f3c5b6df31`) — the damage is confined to an **uncommitted working-tree edit**, not a rewritten or orphaned ref.

## 4. Independent verification performed (not trusted from the AWARD text alone)

- **`DONE-worf-0050-09-20260901.md`:** searched `main` tree (`git cat-file -e main:...` → does not exist) and every local branch (`git branch --list` enumerated, checked each with `git cat-file -e <branch>:...` → found on none). **Confirmed: exists in no reachable object.** The dirty patch's `0050-09` `[x]` + `Acceptance: ✓` block is **unsubstantiated** — no implementer claim, no reachable REF, nothing to independently verify the accept-authority chain against. **Not included in the candidate.**
- **`DONE-data-0046-01.01-1788291575795-ae8796e9.md`** and **`DONE-obrien-0046-01.01-integration-20260903.md`:** both confirmed present on `main` (`git cat-file -e main:... `→ exists, both). **Included in the candidate** — marker flip to `[x]` with both claim references, matching the dirty patch exactly for this hunk.

## 5. Candidate produced by this claim

Branch `0037-main-integrity-recovery-20260904`, one commit (see claim/commit metadata below), containing **only** the `TODO.md` `0046-01.01` marker+claim-reference hunk from the dirty patch. The `0050-09` hunk is deliberately excluded. No other path touched. No `main`/root mutation. No Acceptance, integration, or Feature-closure action taken by this claim.

## 6. Forward-only root-restoration plan — NOT EXECUTED

Recorded for `geordi` (or whichever privileged Integrator holds the reservation) to execute, exactly as written, after independent review of this dossier and the candidate:

1. Confirm this candidate branch's tip is reachable and its diff matches this dossier's §2/§5 exactly (no drift since this claim closed).
2. Run mandatory pre-integration hygiene against the exact candidate: `python3 _src/tools/check_integration_hygiene.py --repo <root> --candidate-ref <candidate>`.
3. Run root preflight: `python3 _src/tools/check_integration_hygiene.py --repo <root> --root-preflight`. **This step will currently fail** (`MAIN_WORKTREE_DIRTY` or equivalent) because root's `TODO.md` is still dirty as described in §1 — that dirty state must be resolved before preflight can pass, and resolution is itself part of the forward-only plan below, not a precondition assumed away.
4. **Do not `git reset --hard`, `git checkout -- TODO.md`, or `git restore` in root.** Those discard the dirty edit without proof it isn't the only copy of something. Instead: from *outside* root, `git -C <root> diff -- TODO.md > preserved-patch.diff` (already captured in §2 of this dossier — reuse that, do not re-derive), then verify the working-tree `TODO.md` SHA-256 still matches §2's recorded digest before touching anything.
5. Once the candidate branch (§5) is confirmed to contain the fully-reviewed, correct replacement content for the `0046-01.01` hunk, and root preflight is otherwise clean: advance `main` from root via `git -C <root> merge --ff-only <candidate>` (or `--no-ff` if drift requires reconciliation, per this session's established pattern). This ff/no-ff merge naturally supersedes and clears the dirty `TODO.md` working-tree edit in root, because the merge updates root's index and working tree together — this is the *forward* resolution, not a destructive discard.
6. Re-run root preflight immediately after the merge; confirm `git status --porcelain` in root is empty and `TODO.md` matches the merged candidate exactly.
7. Separately and only if warranted: investigate who ran the direct-root `git reset` sequence in §3 and why, and whether `.worktrees/` needs a `.gitignore` entry to stop it recurring as untracked root content. Both are **out of this claim's scope** (`TODO.md` + this dossier only) and are named here as follow-up, not executed.
8. The `0050-09` question (§4) is not resolved by this plan. Whoever owns `0050-09` must either produce the missing `DONE-worf-0050-09-20260901.md` claim and a real Acceptance chain, or the Task stays `[ ]` as it is on current `main` and in this candidate. No agent should re-introduce the unsubstantiated block from the dirty patch without that evidence existing first.

## 7. What this claim did NOT do

No `git reset`, `git restore`, `git checkout --`, force-update, ref deletion, push, publication, Acceptance record, integration verdict, Feature-closure, or `main`/root mutation. No sibling ref, worktree, or claim touched. Root bytes are **exactly as found** — the dirty `TODO.md` in `/Users/tobias.anton/devel/autodocs` is untouched by this claim; its SHA-256 (§2) can be re-checked against the live root file to confirm.
