# Independent Architect scope review — `DEC-0037-006` Wave-B governance normalization

**Verdict:** `SUPPORT`

**Reviewer:** `agent:saru:0037-cutover-governance-normalization-review:1788390000710-8d1857fa`, privileged Management-instantiated Architect, Team Discovery. Distinct from author Data (`agent:data:0037-cutover-governance-normalization:1788382508075-dcd89d43`). This is not Acceptance, checkpoint review, implementation, integration, effect authorization, or Feature `0037` closure.

**Award:** offer `1788390000710-8d1857fa` (notice `1788390010632-77e79be6`, execution wake `1788390196198-2a7d9145`). Mail is not additional authority.

**Write scope:** only this artifact. Candidate and claim were not modified.

No `DEC-` identifier is allocated or changed here. No alternative among `DEC-0037-006` ALTs is re-selected.

---

## 1. Pins and digests

| Input | Ref / digest |
| --- | --- |
| Exact review candidate (award pin; this branch cut) | `46d328f351c9ed01d51828953d62e3e117da5637` (`docs(0037): normalize Wave-B authority boundaries`) |
| Management adoption | `decision-1788388143372-f951c9b4` Option `A`, `resolved_at=2026-09-02T22:59:32Z` — amend assignment scope to the existing two-path candidate and actual decision filename |
| Data Architecture award (authoring, not this review) | `1788382508075-dcd89d43` / wake `1788383431170-a516ad6c` |
| Candidate claim | `TODO-data-0037-cutover-governance-normalization-1788382508075-dcd89d43.md` SHA-256 `22aaad599f6b500420d7a58864f3adb2db0270d3fa87a9e6fb2dc8605bb56d92` |
| `docs/dossiers/dec-0037-006-wave-b-governance-normalization.md` | SHA-256 `8a8685f58c92a5438ed8f8c9505e52f3acf10e7b3dc2e1caef419d14b72f7b7a` |
| Data claim `base_commit` | `a0623411bfb3590ae4a3d8d08177064554651401` |
| Observed later `main` at review start | `a0623411bfb3590ae4a3d8d08177064554651401` (same as Data base). **Not absorbed into this review branch.** Candidate is **not** an ancestor of `main`. |
| Identifier uniqueness | `DEC-0037-006` is absent from `main`; next-free after `DEC-0037-005` on this candidate |

This review does **not** silent-retarget a later `main`. Integration remains a separate Integrator act.

---

## 2. Contract the award required this review to verify

Independently remesured on `46d328f351` against `docs/pipeline/decision-record.md` `decision-record@v1` and the four Wave-B contradictions named in the award:

1. **Frozen authoritative issue-store epoch through `0037-40`.** Decision + CON-02: after `0037-34.02` the issue store is the sole authoritative backlog; ordinary issue-item and claim writes stay forbidden until signed `0037-40`. Interim writes are only declared append-only control/provenance refs.
2. **Selector `issue-store-write-frozen` / `write_phase: frozen`.** Decision + CON-01: canonical capability vocabulary is `issue-store-write-frozen` with exact `write_phase: frozen`. `issue-store-frozen` is a legacy input spelling to map and retire; post-switch writers/validators must not emit or accept it as current state. On this candidate, `docs/pipeline/agent-workflow.md` already uses the canonical concept.
3. **Plural approvals namespace.** Decision + CON-03: new Feature `0037` approvals use `refs/autodocs/approvals/...`. Pre-existing singular `refs/autodocs/approval/...` objects stay immutable historical evidence and grant no Wave-B credit without an exact authorized migration binding.
4. **Native CAS excludes `refs/heads/main`.** Decision + CON-04/CON-05: Authority-Ref-CAS targets only dedicated non-source refs declared by the transaction and MUST NOT verify/update/create/delete/move `refs/heads/main`. Reviewed source-history integration remains a separate privileged Integrator root-checkout `git merge --ff-only <candidate>` after candidate hygiene and pre/post root preflights. A successful dedicated-ref CAS is not source integration, Task Acceptance, or a hygiene bypass.

**Exactly-one-writable-authority:** Decision closing sentence and CON-02/CON-06: one authoritative backlog per epoch; exactly one declared write domain (legacy before cutover; control/provenance during freeze; issue-store items only after `0037-40`); no dual-writable interval; `main` is not an Authority-Ref-CAS resource.

**Rollback:** CON-06/CON-07 match `docs/pipeline/issue-cutover-rollback.md` on this candidate: abandon prepared candidate before `0037-34.02`; after switch and before `0037-40`, authorized control/provenance restore of the coherent legacy selector without dual-writable domains; after `0037-40`, no routine reverse migration — emergency re-enters write-frozen and follows `0037-44`.

**Affected gates:** named `task-start` / `validation` / `integration` / `feature-closure` entries cover `0037-34.02`, selector/policy validation, `0037-35.*`, `0037-36`, `0037-40`, and Feature `0037` closure. CON-05 forbids treating CAS success as those gates.

**No force bypass / no effect authorization:** CON-05 and CON-08; Data claim status `[x]` as Architecture record only. This review authorizes none of: selector mutation, effect commands, ref moves, `TODO.md`/`DONE.md` marker changes, Acceptance, `main` advance, push, or Feature closure.

---

## 3. `decision-record@v1` schema/provenance

Independently checked against section 3 of `docs/pipeline/decision-record.md`:

- Required fields occur once in the required order from **Record format** through **Waiver**.
- ID `DEC-0037-006` matches `^DEC-[0-9]{4}-[0-9]{3}$`.
- Timestamp `2026-09-03T00:04:12+02:00` is a complete offset timestamp.
- Deciding identity matches the agent grammar; Role is `Architekt`.
- Triggers are from the closed set (`cross-item-blast-radius`, `material-architecture-or-repository-behavior`, `security-or-credential-boundary`, `material-risk-decision`).
- Four alternatives; exactly one `selected` (ALT-01); others `rejected` with reasons.
- Nine consequences; affected work units and gates use the permitted reference syntax.
- **Review participation:** `none` with immediate **No-review reason**. That is form-valid for authoring. It does not substitute for this distinct independent review.
- **Waiver:** `none`.

`python3 _src/tools/process_doc_doctor.py --json --root <this-worktree>`: `ok=true`; corpus `errors=2` are unrelated `DOC001` links (`0044-03-gate-scope-proposal.md`, `man5-risk-register.md`). The only finding on the assigned decision path is non-blocking `DOC005` (decision cited by no other document yet). Data's claim already recorded that expected first-citation gap.

Claim path population on `46d328f351` vs its parent is exactly the two Management Option A paths (167 lines added). `git diff --check` is clean on this worktree at the pin.

---

## 4. Bounded adjacent findings (do not reopen SUPPORT)

- **F-1 — `0037-44` named in CON-07, omitted from Affected work units.** CON-07 points emergency post-`0037-40` handling at Task `0037-44` / forward repair. That task is not listed under **Affected work units**. This does not reverse ALT-01 or the four contradictions. An additive later amendment may add `task:0037-44` if an authorized editor extends the record; this review does not mutate the candidate.
- **F-2 — First operative citation still missing.** `DOC005` remains until a Wave-B consumer or landed review cites `DEC-0037-006`. This artifact is the first independent citation on the review branch; it is not an implementation citation and does not activate effects.
- **F-3 — Historical singular approval refs remain in live docs on the pin.** `TODO.md` Feature `0037` already documents plural `refs/autodocs/approvals/<decision-id>` for human approvals, while `0037-07` history and `docs/pipeline/issue-approval-setup.md` still show singular `refs/autodocs/approval/...`. CON-03/CON-08 already require fail-closed migration rather than grandfathering. Adjacent confirmation, not a schema defect.

---

## 5. What this review does not do

- Does not modify `docs/dossiers/dec-0037-006-wave-b-governance-normalization.md` or the Data claim.
- Does not implement selectors, CAS, approval refs, or effect commands.
- Does not integrate, merge to `main`, push, accept Tasks, or move Feature `0037` to `DONE.md`.
- Does not treat Management Option A as permission to expand write scope beyond this review path.

**Next:** distinct Integrator/hygiene admission of `46d328f351` plus this review commit, if separately awarded. This SUPPORT is not that act.

---

## 6. Completion

| Field | Value |
| --- | --- |
| Verdict | `SUPPORT` |
| Candidate | `46d328f351c9ed01d51828953d62e3e117da5637` |
| Review branch | `0037-cutover-governance-normalization-review-20260903` |
| Review worktree | `/Users/tobias.anton/devel/autodocs/.worktrees/0037-cutover-governance-normalization-review-20260903` |
| Review path | `docs/dossiers/0037-wave-b-governance-normalization-scope-review.md` |
