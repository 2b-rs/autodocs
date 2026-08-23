# 0037-49 External Readiness Evidence

## Scope and boundary

This evidence package establishes only whether the externally controlled prerequisites for the issue-store architecture-approval bootstrap are present and independently verifiable. It neither requests nor records private credentials, performs signing, creates a review, changes hosting settings, publishes artifacts, deploys software, or restarts a service.

## Regeneration note (2026-08-21)

This report supersedes the 2026-08-16 16:08 version, which was written before the owner provisioned the prerequisites below and was left uncorrected through two subsequent marker reviews (`[d]` → `[u]`). The owner completed provisioning on 2026-08-16 16:42 (commit `e0c969976`, message: "All 6 readiness checks pass (EXIT=0)"). `python3 _src/tools/manage_approval_readiness.py --check --json` was re-run against the current configuration on 2026-08-21 and independently confirms `all_ok: true` for all six checks; the tool required no change. This report also applies the single-authority rescoping (`DEC-0044-014`, commit `1fe11e28e`): one named authority holds all five roles, evidenced by a documented self-attestation rather than five separate reviewer identities.

## Evidence basis

- Discovery request: `0037-49-readiness-discovery-20260816-1448`; provisioning commit `e0c969976` (2026-08-16 16:42:50 +0200); regeneration verification 2026-08-21 on branch `0037-49` at `1fe11e28e`.
- Policy basis: `docs/pipeline/issue-approval.md` requires exact-commit policy, `git verify-commit`, and independent repository-owner fingerprint confirmation; `DEC-0044-014` (single-authority self-attestation) governs role assignment.
- Live check: `python3 _src/tools/manage_approval_readiness.py --check --json` → `all_ok: true`, EXIT=0, all six checks `OK`.

## Readiness matrix

| Prerequisite | Required independent proof | Current finding | Result |
| --- | --- | --- | --- |
| Approval authority (single authority, `DEC-0044-014`) | Named authority for all five roles (process/architecture-approver, security, privacy, release, repository-owner), documented self-attestation | `issues/_policy/authorities.json`: all five roles resolve to `tobias.anton <tobias.anton@accenture.com>`; repository-owner key `github-master-key` (`SHA256:ciGUV68+0uuJGw+HsDQmur/ZO0INAtZbg5M0A+zydl4`), other four roles share `agent-commit-key` (`SHA256:YWg/nPlBol+BkcbC/S0yIDBaw7xpKmfSjreQM8rgDjU`); self-approval constraint noted in the role record (approval ref must be a separate signing occasion from any implementation commit) | READY |
| Commit signing | Public fingerprint registry, no placeholders, plus valid `git verify-commit` chain | `issues/_policy/allowed_signers` carries two real `ssh-ed25519` principals (`agent-commit-key`, `tobias.anton@accenture.com` manual key); Git SSH signing configured and present | READY |
| Repository administration | Verified remote and repository-owner confirmation channel | Remote `git@github.com:2b-rs/autodocs.git` configured; owner fingerprint confirmation channel `https://github.com/tobias-anton.keys` recorded in `authorities.json` | READY |
| Credential handle | Non-secret handle metadata, scope, expiry, revocation and audit route | `issues/_policy/credential-handles.json`: `autodocs-deploy-key` (`SHA256:wtCFvdCIurWZj2NT4deL9Rg9uwqsL5nj17jlaoTW7a0`), scope "write access to 2b-rs/autodocs only", registered 2026-08-16, no expiry, revocation path (remove deploy key from GitHub settings), audit path (last-used date shown per key entry) | READY |
| Hosting publication | Verified permission and bounded publication target | Same deploy-key handle above bounds publication to `2b-rs/autodocs`; no broader hosting-org access granted | READY |
| Service controls | Verified health, restart and rollback endpoints plus operator authorization | `issues/_policy/runner-service.json`: manual-launch `run-loop.sh`, `health_check` = `pgrep -f 'run-loop.sh run.sh'`, `restart_path` and `rollback_path` recorded with notes, operator `tobias.anton <tobias.anton@accenture.com>` named. This is a manual-operator control interface, not an automated service; Campaign-B deferral (`0037-46`/`0037-46.01`/`0037-46.02`) was not invoked because the manual interface already satisfies the acceptance criterion as recorded | READY |

## Fixture verdicts

Fixtures are deterministic negative/control records. Each prohibits approval or external mutation when a prerequisite is missing, stale, wrong-role, unavailable, or digest-mismatched. The service-control fixture further proves that a no-op local probe cannot be confused with a deployment, restart, or rollback. `docs/pipeline/fixtures/0037-49/readiness-fixtures.json` (seven cases, unchanged) continues to pass against `validate_readiness_fixtures.py`; none of the seven negative cases match the current live configuration, i.e. none of them fire.

## Decision

`0037-49` certifies external readiness under the single-authority model (`DEC-0044-014`). All six prerequisites are independently verified present and correctly scoped: signing key and `allowed_signers`, repository-owner hosting-administration capability, `authorities.json` single-authority role record, credential handle, and a named manual runner-service control interface. Architecture approval (`0037-07`) may proceed to its own review procedure; this report does not itself grant approval, sign an approval ref, or evaluate the architecture package — it only establishes that the external prerequisites for conducting that review exist and are verifiable.
