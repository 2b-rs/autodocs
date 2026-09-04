---
schema_version: "1.0"
id: "0037-49"
level: "task"
parent: "0037"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-37"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2098"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
---

## Goal

PREREQ: 0037-49:0037-37 Single-authority external-readiness evidence: the repository owner, acting as the sole named authority for every role this Task previously distributed, provisions and self-attests approval, signing, hosting-administration, credential-handle, and service-control evidence. Architecture approval remains forbidden until that attestation is recorded. REF: 9d4815c6b **Acceptance: ✓** (2026-08-27, Integrator `paul`, unabhängig von Implementierer Seven / `agent:perplexity:0037-49:0037-49-20260816-1447`). Abgenommene Baseline `9d4815c6b`; Review-REF `b6d2bfdfe4850ad2cf7c1d898105088409e01378`; AWARD `1787865994204-934c578e`.

## Scope

- **Provenance of the marker correction (recorded 2026-08-21 by Projektleiter Kathryn, management-directed):** The same correction had already been made once, user-directed, on 2026-08-19 ("State correction (2026-08-19, user-directed): Replaced undefined marker `[d]` with the contract-defined `[u]`"). That note lived only in the shared root checkout's working tree, never reached `HEAD`, and was preserved in tag `preserved/root-worktree-20260821-kathryn` when the checkout was restored. It is restored here because **ticket state must not be bound to branches — backlog state belongs on `main` for transparency** (management, 2026-08-21). Recorded additively: Seven's independent repair note below stands unchanged. Open question for management, not decided here: `[d]` was introduced by the user in commit `4dc9d9166` (2026-08-16) meaning *deferred*, but was never added to this file's marker legend (`[ ]`, `[u]`, `[p]`, `[?]`, `[w]`, `[x]`). Whether `[d]` should become a defined marker — "deferred" is not the same as "unclear" — remains open.
  - **Marker repair (2026-08-21, Seven, autonomous backlog repair per `AGENTS.md`):** Corrected from `[d]`, which is not a marker defined in this file's own header (only `[ ]`/`[u]`/`[p]`/`[w]`/`[x]` exist — `legacy_task_doctor.py` already flagged this as `LTD-MARKER-UNDEFINED`). This Task's sibling `0037-07` states its own precise threshold in terms: `0037-49` "set `[u]` only after `0037-37` is complete and the sole next action is human signature/decision." `0037-37` closed `[x]` at REF `927da0690a964249f7ca0b83719601b849be801f` (this same integration). All local evidence is already complete (see below); the sole remaining action is exactly the human/external authorization this Task's own acceptance criteria describe — SSH signing, credential handles, hosting/runner-service administration, out-of-band owner confirmation — none of which an agent can supply. `[u]` is therefore the correct marker, not a repair that changes scope or invents approval.
  - **Evidence (2026-08-16):** `docs/pipeline/0037-49-external-readiness.md`; fixtures `docs/pipeline/fixtures/0037-49/readiness-fixtures.json` and `validate_readiness_fixtures.py` passed (seven cases). Claim record: `TODO-perplexity-0037-49-20260816-1447.md`; owner token `agent:perplexity:0037-49:0037-49-20260816-1447`; discovery base `1e8e9cfcecbf450c849ed23a11774f44027442d8`.
  - **Rescoping (2026-08-21, `DEC-0044-014`, management-directed):** This Task's original acceptance criteria assumed distinct human occupants of process, security/privacy, release, independent-quality, and translation-review roles, an out-of-band confirmation channel separate from the repository owner, and a permanently running runner service. That model answers a multi-contributor question this repository does not currently ask — it is operated by one person with agents, so the five roles are the same person. `DEC-0044-014` replaces distributed-identity assurance with **single-authority self-attestation**: one named authority, one signing key, roles recorded as a documented statement rather than cryptographically separated identities. What is *not* reduced: the attestation is still a real, digest-bound, signed record on an immutable ref, still independently verified by the bootstrap tooling, and still blocks approval early rather than failing during implementation.
  - **Closure (2026-08-21, Seven, task directly assigned by Kathryn per agent-inbox msg `1787340043459-90fb5bba`, thread `0037-49`):** The `[u]` marker was based on a stale 2026-08-16 16:08 readiness report that predated the owner's own provisioning commit `e0c969976` (2026-08-16 16:42, "All 6 readiness checks pass (EXIT=0)"). Independently re-verified before closing: `python3 _src/tools/manage_approval_readiness.py --check --json` → `all_ok: true`, EXIT=0, all six checks `OK` — no tool change needed, single-authority shape already matched by `authorities.json` ("Solo project: approver is also implementer"). Regenerated `docs/pipeline/0037-49-external-readiness.md` against live state (READY for all six prerequisites); fixture suite re-run and still passes 7/7. REF `9d4815c6b`, branch `0037-49` (worktree `.worktrees/0037-49`, based on `main` at `1fe11e28e`). No `Acceptance: ✓` added — Implementer role only.

## Acceptance criteria

- **AC-001** The repository owner is recorded as the sole named authority for every role this Task previously distributed (process, security/privacy, release, independent-quality, translation-review). Provision: an SSH signing key under the owner's control, registered in `issues/_policy/allowed_signers` with a real fingerprint (no placeholder)
- **AC-002** the owner's repository-administration capability on the actual hosting remote (verified, not asserted)
- **AC-003** a narrowly scoped credential handle for approval-ref publication and hosting branch policy, with recorded scope/expiry/revocation route
- **AC-004** and, for the runner-service and protocol-selector controls, either a working health/restart/rollback interface or an explicit recorded decision to defer runner-service readiness to Campaign B (`0037-46`/`0037-46.01`/`0037-46.02`) and gate only the parts of `0037-07` that do not require it. The owner supplies one self-attestation statement — a single signed commit naming the identity, the key fingerprint, and confirmation that all five roles are exercised by that identity — in place of the previously required out-of-band confirmation from a separate channel. `_src/tools/manage_approval_readiness.py --check --json` is updated to check this single-authority shape and re-run against the actual configuration

## Definition of Done

Signed readiness report, under the single-authority model, records the owner's key fingerprint, `allowed_signers` entry, verified hosting-administration capability, credential-handle metadata, and either working service-control endpoints or the recorded Campaign-B deferral, for `0037-07`, `0037-38`, `0037-43`, `0037-32`, `0037-33`, and `0037-36`; each of those Tasks is rescoped to name the repository owner as its sole signer/reviewer/authority when its own turn comes, rather than requiring separate role occupants — a one-line note at each Task records this pending rescoping until it is carried out in full when that Task is next worked. Any prerequisite still genuinely unavailable (for example, a hosting remote not yet configured) blocks approval early as `[u]`, named specifically, rather than the prior five-role list.
