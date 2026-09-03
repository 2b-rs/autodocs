# Integration claim — 0037 cutover governance normalization

- **owner_token:** `agent:geordi:0037-cutover-governance-normalization-integration-r3:1788394338466-57cc9f94`
- **assignment:** atomic R3 award `1788394338466-57cc9f94`
- **capability / role:** `privileged` / independent Integrator
- **state:** `[p]`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/integrate-0037-cutover-governance-normalization-geordi-20260903`
- **worktree mode:** detached fresh aggregate; no worktree or ref deletion/recreation
- **target baseline:** `main@a3d55d8de49b1baae71fc9f7b48d2074435da279`
- **architecture candidate:** `46d328f351c9ed01d51828953d62e3e117da5637`
- **independent SUPPORT:** `fd82621a4a88a7e3cfb968dbc7a23915887676c2`
- **management authority:** `decision-1788388143372-f951c9b4`, resolved Option A
- **prior evidence:** R1 `b10c1d4a4b7a11d7dba9f43ab9243d269b72d8ff`; R2 `ef9ff788700751ea841d9bf8776550c73dce84c5`

## Exact R3 scope

- `TODO-data-0037-cutover-governance-normalization-1788382508075-dcd89d43.md`
- `docs/dossiers/dec-0037-006-wave-b-governance-normalization.md`
- `docs/dossiers/0037-wave-b-governance-normalization-scope-review.md`
- this claim

## Contract and boundary

Land only the reviewed Wave-B governance normalization and this Integration
claim. Preserve the exact Architecture and SUPPORT ancestry, later source-main
history, and the four-path target-relative boundary. Run candidate hygiene,
immediate root preflight, guarded root fast-forward merge, immediate postflight,
then record scope, ancestry, and common-directory receipt.

This exact package is exempt from the active cutover quiescence only for its
awarded governance integration. No cutover effect, selector/CAS/approval-ref
implementation, Acceptance, `TODO.md`/`DONE.md` marker change, Feature closure,
push, ref/worktree deletion or recreation, foreign cleanup, or Memory action is
authorized.

## R3 aggregate

- At startup, root `HEAD`, `main`, and `refs/heads/main` equal the exact target
  and the root tracked checkout is clean.
- The existing item worktree was cleanly detached at the exact target; prior
  R1/R2 branches and refs remain preserved.
- Provenance merge `6384993add00516093be5afa8f67ed3a9944afed`
  merges SUPPORT `fd82621a4a` into the target without conflict and changes
  exactly the three reviewed package paths before this claim is added.
- SHA-256 checks match the SUPPORT pins for the Data claim
  (`22aaad599f6b500420d7a58864f3adb2db0270d3fa87a9e6fb2dc8605bb56d92`)
  and decision record
  (`8a8685f58c92a5438ed8f8c9505e52f3acf10e7b3dc2e1caef419d14b72f7b7a`).
  The SUPPORT artifact digest is
  `51f0228407720c4280e20352bb7023b2ab2cf366869c4c43a1082aa52b38abe3`.
- `DEC-0037-006` is unique among candidate decision records. Durable authority
  status is resolved Option A, and Data/Saru/Geordi are distinct identities.
- `git diff --check` passes. `process_doc_doctor.py --root . --json` exits `0`
  with `ok: true`; its two errors are inherited and outside assigned paths.
- Candidate hygiene and the guarded root sequence remain pending.
