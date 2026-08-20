# Corrective implementation claim — Feature 0040 target-policy reconciliation

- task_id: `0040-repair`
- owner_token: `agent:worf-k-ehleyr-20260820t001000z:0040-repair:20260820T001000Z-5c2bc79f`
- request_id: `20260820T001000Z-5c2bc79f`
- capability_class: `unprivileged`
- execution_authority: direct execution permitted by explicit user assignment; `run.sh` is prohibited
- branch: `0040`
- worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0040`
- base_commit: `2c2cda22889042aabb936dfc092bce0410d07ccf`
- target_branch: `main`
- target_commit: `c0a274e66fd36516e748a0d309bcd35fa5b7e561`
- startup_review: `SANDBOX.md`, `AGENTS.md`, `TODO.md`, `DONE.md`, `docs/pipeline/branch-workflow.md`, and `docs/pipeline/task-acceptance.md` reviewed; candidate is clean. The assigned rejection review is retained at commit `ebc6c018afe571bf847ddbaa22343e89da937fe4` and must be read from that commit because it is not present in this candidate tree.

## Assigned corrective scope

Reconcile Feature `0040` with the authoritative integration policy on current target `main`, which defines three capability classes (`sandboxed-grunt`, `unprivileged`, `privileged`), without importing policy from any foreign branch. Correct newly authored, non-provenance German documentation touched by the repair into English. Preserve closure, review, rejection, and user-provenance evidence append-only. Do not request or grant acceptance, cross an integration checkpoint, merge `0040` into `main`, move any Feature to `DONE.md`, publish, push, alter remotes/SSH configuration, or use `run.sh`.

## Intended write scope

- `TODO.md` and/or `DONE.md` only for append-only authoritative reopening/corrective history if necessary.
- Feature-0040 documentation and corrective evidence required to remove stale two-class normative assertions and document the repair.
- This claim file.
- A tracked provenance receipt if commit-message capacity makes verbatim user prompts impractical.

## External resources

None. No network, publication, credential, SSH, remote, or runner activity is authorized.

## Initial finding and plan

The rejected integration review identifies a stale two-class capability assertion. Current target `main` is the authoritative policy source under `docs/pipeline/branch-workflow.md` integration-policy precedence. First inspect target-only policy changes and the exact review evidence, then merge only `main` into candidate if required by the policy. Preserve historical two-class prose as historical evidence, but correct any newly authored normative claims and German non-provenance prose in the candidate. Validate structural policy consistency, absence of remaining current-normative two-class assertions, diff scope, and clean final worktree.

## Next action

Read the exact rejection evidence from its recorded commit, inspect `0040...main` history/diff and current target policy files, then perform the smallest target-policy reconciliation.

## Completion record

- Target-policy merge: `c560fbc2fdc5bf39811a545894560f648364f49a` merged
  `main` tip `c0a274e66fd36516e748a0d309bcd35fa5b7e561` into `0040`.
- Substantive corrective REF: `74dbdac90b421128352bfc8afc7bb4b580a4c054`.
- Deliverables: English `docs/pipeline/process-roles.md`; append-only corrective
  evidence `docs/dossiers/0040-main-integration-repair-20260820T001000Z.md`;
  authoritative corrective reopening entry in `TODO.md`.
- Validation: `python3 _src/tools/process_doc_doctor.py` completed with 0 errors
  and 33 existing advisory warnings; focused three-class/English assertion
  passed; `git diff --check` passed; `main` and prior candidate
  `2c2cda22889042aabb936dfc092bce0410d07ccf` are ancestors of the repaired
  candidate.
- Remaining risk: prior `0040-09` acceptance is bound to the pre-repair
  baseline and is not current for this candidate. A separately assigned,
  independent privileged reviewer must review this repaired candidate before any
  Feature-to-`main` integration. This implementation did not request/grant
  acceptance, cross a checkpoint, alter `DONE.md`, publish, push, or change SSH
  configuration.
- Next safe action: dispatch an independent privileged reviewer for exactly the
  repaired `0040` candidate baseline; that reviewer alone decides whether a
  current integration review can pass.
