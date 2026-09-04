---
schema_version: "1.0"
id: "0037-07"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-37"
  - "0037-49"
  - "0038-15"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2107"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0037-07:0037-37, 0037-07:0037-49, 0037-07:0038-15 Obtain authorized approval of the exact architecture review package before implementation. REF: approval commit `b4f03bf88c6d8b1adb45f29b10c27974cb8dfdf1` (`refs/autodocs/approval/0037-07`) plus integration commit `2f83441870936cfce1236fa4d549d6eac3afff45`. **Acceptance: ✓** (2026-08-27, Integrator `paul`, unabhängig von Implementierer `Seven-Icheb`). Abgenommene Baseline `2f83441870936cfce1236fa4d549d6eac3afff45` with approval `b4f03bf88c6d8b1adb45f29b10c27974cb8dfdf1`; Review-REF `b6d2bfdfe4850ad2cf7c1d898105088409e01378`; AWARD `1787865994204-934c578e`.

## Scope

- **Successor recheck (2026-08-21, Seven, per `AGENTS.md` "Completing implementation work" step 5):** `0037-49` closed `[x]` at REF `9d4815c6b`. All three prerequisites of this Task are now terminal: `0037-37` `[x]`, `0037-49` `[x]`, `0038-15` `[x]` (REF `f818542c6`). Marker correctly remains `[ ]` (open/unclaimed) — implementation start prerequisites are satisfied, so this Task is now globally eligible, but implementation of `0037-07` itself was explicitly not undertaken in this pass per assignment.
  - **Rescoping applied (2026-08-21, Seven-Naomi, unprivileged, `TODO-seven-naomi-0037-07-20260821T210000Z.md`, per `0037-49` closure and `DEC-0044-014`):** Rescoped the acceptance criteria and Definition of Done below from a distributed process/security/release-authority model to the single-authority model `0037-49` established: the repository owner (`tobias.anton`) is the sole named authority holding all five roles (`architecture-approver`, `security`, `privacy`, `release`, `repository-owner`). Only role-cardinality language changed; the substantive security bar (SSH-signed commit on a dedicated immutable approval ref, bootstrap verifier + owner fingerprint confirmation, and every named field) is unchanged. Verified `python3 _src/tools/manage_approval_readiness.py --check --json` → `all_ok: true`, all six checks `OK`, `authorities.json` roles resolve `['architecture-approver', 'privacy', 'release', 'repository-owner', 'security']` to the single owner identity.
  - **Package verification (2026-08-21, Seven-Naomi):** Re-verified all 17 contract digests in `docs/pipeline/issue-store-review-package.json` (base commit `e3a176aeb8e10a0d08a977e08db1aaec6d69cb4f`, committed by `0037-37` REF `927da0690a964249f7ca0b83719601b849be801f`) by recomputing `sha256(git show <base_commit>:<path>)` for each of the 17 listed paths against the current tree — all 17 recompute exactly matching (`ALL_OK`). Ran `python3 _src/tools/verify_issue_approval_bootstrap.py` against a structurally-valid sample approval record (schema-conformant, `signature_verified: true`, well-formed `sha256:`-prefixed digest) — passed: "structural approval record validation passed; run git verify-commit separately" (the tool is a stdlib-only structural/shape checker; it does not itself verify a real signature — that is `git verify-commit` on the actual signed approval commit, to be run by the owner or a later verifier once the real signed commit exists).
  - **`[u]` set (2026-08-21, Seven-Naomi):** Per this Task's own Definition of Done ("set `[u]` only after `0037-37` is complete and the sole next action is human signature/decision"): `0037-37` is `[x]` (REF `927da0690a964249f7ca0b83719601b849be801f`), rescoping is applied above, all 17 package digests reverify, and the bootstrap-readiness/structural verifiers are green. The sole remaining action is the repository owner's own SSH-signed approval commit — an act `AGENTS.md` explicitly reserves to the owner ("implementation authors do not self-approve"; autonomous-repair authority "does not permit an agent to ... invent approval, accept security/privacy/release risk"). **Path note:** the dispatching briefing asked for a draft file under `docs/pipeline/`; that conflicts with `AGENTS.md`'s `DEC-0044-012` rule that everything under `docs/pipeline/` is a governance artifact that must never sit on a branch, so this claim keeps the draft inline below (within this Task's declared `TODO.md` write scope) instead, and reports the conflict to the dispatcher rather than silently creating the branch-resident `docs/pipeline/` file.
  - **Draft approval content (2026-08-21, Seven-Naomi) — NOT an approval, prepared for the owner's own review/signing, no ref or signed commit created by this session:**
    - Intended target ref: `refs/autodocs/approval/0037-07` (dedicated, immutable, append-only, matches the `issue-approval@v1` schema's `approval_ref` pattern `^refs/autodocs/approval/`).
    - Candidate `issue-approval@v1` record (schema at `issues/_schema/issue-approval-v1.schema.json`, structurally checked by `_src/tools/verify_issue_approval_bootstrap.py`):
      `{"schema":"issue-approval@v1","package_commit":"e3a176aeb8e10a0d08a977e08db1aaec6d69cb4f","package_digest":"sha256:bf98dffe33da51c29e8952e7cfe10e0bb172d1d50ddb191282ea5c3330909a5f","approval_ref":"refs/autodocs/approval/0037-07","approver_role":"repository-owner","signature_verified":true}`
      — `package_commit` is `0037-37`'s package base commit (REF `927da0690a964249f7ca0b83719601b849be801f` records its closure); `package_digest` is `sha256` of the current `docs/pipeline/issue-store-review-package.json` manifest file content, independently recomputed by this session (if the owner prefers a different digest scope, e.g. over the concatenation of the 17 contract digests instead of the manifest file, that choice is the owner's to make and record before signing); `signature_verified` is shown as `true` only to illustrate required shape — this session cannot set it truthfully since no signature exists yet.
    - Beyond the schema minimum, the signed commit message (or an adjacent tracked field) should also record: **decision** (approve / reject / approve-with-conditions, in the owner's own words); **signer identity** — the owner's SSH public-key fingerprint as registered in `issues/_policy/allowed_signers` (already `verified` per the readiness check below); **validity/revocation** — how long the approval is valid and how it would be revoked (e.g. a follow-up append-only record on the same ref, or an `allowed_signers`/`authorities.json` revocation); **accepted residual limitations** — carried from `docs/pipeline/issue-store-review-package.json`'s `residual_risks`: "external approval/signing/hosting credential readiness is deferred to 0037-49" (now closed, REF `9d4815c6b`) and "implementation is forbidden until architecture approval" (this approval is what lifts it); **closed findings** — all three entries in `docs/pipeline/issue-store-findings.md` (`BLOCKING-EXTERNAL-001` closed by `0037-49` REF `9d4815c6b`; `CLOSED-LOCAL-001` and `CLOSED-LOCAL-002` closed by `0037-37`).
    - Rerun for the owner (or a later verifier): `python3 _src/tools/manage_approval_readiness.py --check --json`; `python3 _src/tools/verify_issue_approval_bootstrap.py <real-signed-record.json>`; `git verify-commit <the-real-signed-commit>`.
  - **Closure (2026-08-22, Seven-Icheb, unprivileged, subagent of Seven, `TODO-seven-icheb-0037-07-<request-id>.md`):** The repository owner personally ran the signing script and produced a signed approval commit at `refs/autodocs/approval/0037-07` (commit `b4f03bf88c6d8b1adb45f29b10c27974cb8dfdf1`), committing `docs/pipeline/0037-07-approval.json`. Independently re-verified all three gates before closing: (1) `git verify-commit refs/autodocs/approval/0037-07` (with `issues/_policy/allowed_signers` from this same branch tip supplied explicitly, since the check ran from a worktree without that file checked out at the default relative path) → `Good "git" signature for tobias.anton@accenture.com with ED25519 key SHA256:ciGUV68+0uuJGw+HsDQmur/ZO0INAtZbg5M0A+zydl4`, matching the `repository-owner` fingerprint in `issues/_policy/authorities.json` exactly; (2) `python3 _src/tools/verify_issue_approval_bootstrap.py docs/pipeline/0037-07-approval.json` (as committed at that ref) → `structural approval record validation passed; run git verify-commit separately`; (3) recomputed `sha256(docs/pipeline/issue-store-review-package.json)` at this branch tip independently → `bf98dffe33da51c29e8952e7cfe10e0bb172d1d50ddb191282ea5c3330909a5f`, matching the `package_digest` field in the committed approval record exactly. All three closed findings recorded in the approval record (`BLOCKING-EXTERNAL-001`, `CLOSED-LOCAL-001`, `CLOSED-LOCAL-002`) are therefore confirmed closed per the signed record. No `Acceptance: ✓` added — Implementer role only; this is Task implementation completion (Definition of Done: "Verified approval ref, integration record, and closed finding log are committed/reachable"), not privileged acceptance.

### Campaign B — Issue Store, Validation, Rendering, and Migration Tooling

## Acceptance criteria

- **AC-001** The repository owner, as the single named authority holding the `architecture-approver`, `security`, `privacy`, `release`, and `repository-owner` roles (per `0037-49`'s single-authority model), reviews the same package commit/digests, sandboxed-grunt execution profile/runner contract, zero-privileged-agent dependency result, and finding log
- **AC-002** a machine-readable approval names decision, package/policy commit and artifact digest, accepted residual limitations, the owner's signer role/public-key fingerprint, validity/revocation information, and all closed findings. The approval is an SSH-signed commit on a dedicated immutable approval ref, passes the bootstrap verifier and owner fingerprint confirmation, and is then referenced by a normal integration commit that closes this Task
- **AC-003** implementation authors do not self-approve

## Definition of Done

Verified approval ref, integration record, and closed finding log are committed/reachable. Keep Campaigns B–E implementation blocked until this gate passes; the first implementation sequence is `0037-46.01`→`0037-46.02`→`0037-46`→`0037-47`, executed by the designated sandboxed bootstrap agent through the qualified legacy runner until queue activation.
