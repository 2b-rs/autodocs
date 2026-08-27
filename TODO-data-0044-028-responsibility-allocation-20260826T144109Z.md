# Architect governance record and scope review — `DEC-0044-028`

record_kind: governance-coordination
task_id: 0044-028
feature_id: 0044
decision_id: DEC-0044-028
request_id: responsibility-allocation-20260826T144109Z
owner_token: agent:data:0044-028:responsibility-allocation-20260826T144109Z
base_commit: f423128b4e25def12b28b359d56ea9c5392ab550
capability_class: privileged
execution_authority: direct
state: [x]
coordination_state: complete-role-corrected-clean-candidate
architect_work_product_status: [x]
write_scope: ["TODO-data-0044-028-responsibility-allocation-20260826T144109Z.md", "docs/dossiers/dec-0044-028-responsibility-allocation.md", "docs/dossiers/0044-028-responsibility-allocation-scope-review.md"]

## Assignment and boundary

Project Lead `jean-luc` assigned this decision-record preparation and bound
Architect scope review under
`agent-inbox:1787755235010-2b87af70`, following the read-only audit
`agent-inbox:1787755203069-7965daf0` and the current user's binding decision.
The clean unpublished-candidate reconstruction was assigned under
`agent-inbox:1787756242460-fedfa1a9`; the PART-01 Role correction and renewed
clean rebuild are assigned under `agent-inbox:1787757237536-52386e2a`. Data acts as a Management-instantiated
Architect and is not the Implementer or Integrator. Mail carries the assignment
and decision context; it does not independently grant ownership, Acceptance,
integration, release authority, or a waiver.

Data may author only this claim, the new conforming `decision-record@v1`, and a
formal Architect review bound to the exact decision candidate. Data must not
change policy implementation, backlog markers, authority files, validators,
Acceptance, integration, `main`, `DONE.md`, external state, or foreign work.

## Baseline and startup review

- Exact assigned base and verified current `main`:
  `f423128b4e25def12b28b359d56ea9c5392ab550`.
- Branch: `gov-0044-028-responsibility-allocation-data-20260826-r3`.
- Worktree:
  `/Users/tobias.anton/devel/autodocs/.worktrees/gov-0044-028-responsibility-allocation-data-20260826-r3`.
- `DEC-0044-028` was absent from the assigned base before allocation.
- The original claim with this exact owner token was established before first
  decision/review authoring and committed in the preserved unpublished
  candidate `8712ebf9d39771ca6761fe5cac6b6ba649840ca1`. This exact session retains
  that owner token for the same item; it is not reused for a different Task.
- Applicable authority read from `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`,
  `docs/pipeline/roles/architect.md`, `docs/pipeline/core-rules.md`,
  `docs/pipeline/decision-record.md`, `docs/pipeline/process-roles.md`,
  `docs/pipeline/feature-breakdown.md`,
  `docs/pipeline/capability-matching.md`, and
  `docs/pipeline/branch-workflow.md`.
- Explicit prior user reservations remain append-only and effective unless an
  authority expressly supersedes them; the current decision does not supersede
  Seven's recorded `0039-01` selection.

```yaml
target_policy_check:
  field: A1-target-policy-integrability
  verdict: fits
  checked_target: main
  basis: "current user decision via assignment 1787755235010-2b87af70; clean-rebuild assignment 1787756242460-fedfa1a9; read-only Architect audit 1787755203069-7965daf0; process-roles and capability-matching at f423128b4"
  checked_at: "2026-08-26T15:16:17Z"
  recorded_by: "Architect agent:data:0044-028:responsibility-allocation-20260826T144109Z"
```

## Prior unpublished candidates and STOP disposition

The old branch and commits remain intact as audit evidence and are not carried
into this fresh branch's ancestry:

- `8712ebf9d39771ca6761fe5cac6b6ba649840ca1`: original candidate; the
  independent deciding-identity STOP is
  `agent-inbox:1787755616970-fa5798ce`.
- `8c13456c58e09d54e57c29786c1eff6354e7aebc`: candidate with C001 using the
  non-canonical correction-event role; verified STOP and correction instruction
  `agent-inbox:1787755997495-5ff56a8c`.
- `bfa3149ede790e4df1353204a3431930e0b79deb`: candidate with no-op C002; verified
  STOP 3 and clean-rebuild instruction
  `agent-inbox:1787756242460-fedfa1a9`.
- `7b52b3db5c5bab8706b4b89333c1c47e5c4ec7f1`: clean direct-base candidate
  stopped before renewed review because PART-01 still used non-canonical
  `Role: Architect`; pre-review finding and rebuild instruction
  `agent-inbox:1787757237536-52386e2a`.

None reached `main`; therefore section 5's prohibition against rewriting
published records does not require the invalid candidates to appear in the
clean final product. The fresh DEC contains exactly one correction event:
`DEC-0044-028-C001`, with exact `Role: Architekt`, otherwise preserving the
same deciding-identity correction. PART-01 also uses exact `Role: Architekt`.
It contains no invalid C001 and no C002.

## Intended work product and governance effect

The decision record separates ordinary responsibility allocation from
authority-bearing acts, preserves exact earlier user reservations absent express
supersession, enumerates the affected work units and real gates, and defines the
smallest atomic governance correction. The separate Architect review binds its
verdict to the exact candidate digest and prohibits implementation until the
decision and supporting review are reachable from `main`.

- **Governance activation:** this three-path candidate records the decision and
  scope review only. The six-path policy implementation is not activated here
  and may begin only after the exact DEC and review are reachable from `main`.
- **Affected gates:** `task-start:0039-01`, `task-start:0039-02`,
  `task-start:0039-03`, `task-start:0039-05`, `integration:0039`, and
  `feature-closure:0039`.
- **Self-application:** the responsibility/authority separation is honored in
  this package: the Project Lead assigned ordinary preparation, Data supplies
  Architect scope review, and no Acceptance, integration, release, or policy
  implementation authority is inferred.
- **Rollback:** discard or revert the exact three-path candidate together before
  publication; after publication, preserve DEC/review evidence and revert any
  later six-path implementation atomically under its own authorized change.
- **No implicit grandfathering:** existing exact assignments, claims, accepted
  dispositions, and prior concrete user reservations remain effective unless an
  explicit authoritative handoff, invalidation, or superseding decision says
  otherwise.

## Advisory execution and assurance ranges

Assumptions: documentation-only three-path rebuild, no network or credentials,
no policy implementation, and repository baseline fixed at `f423128b4`.

- Token/test-design effort: approximately 8k–16k reasoning tokens and 4–7
  focused checks (field/event shape, both block digests, full-file digests,
  changed-path guard, document doctor, diff/cleanliness).
- Runtime/CPU: approximately 5–15 minutes wall time, under 2 CPU-minutes, one
  worker, and under 512 MiB memory.
- Cognitive demand: high, because correction-event semantics, unpublished
  history, exact digest preimages, and authority boundaries interact.
- Uncertainty: low-to-medium (10–20%); the main residual is that the repository
  has no dedicated exhaustive decision-record validator beyond normative review
  and general document checks.
- Risk: medium before validation and low after exact digest/path/doctor checks;
  impact would be high if a malformed decision were integrated because it gates
  a cross-item governance implementation.

## Handoff

After a path-limited commit, hand the immutable candidate to Project Lead
`jean-luc`. A distinct Implementer may act only after this record and review are
integrated to `main`; a separately assigned independent privileged reviewer or
Integrator handles later checkpoint Acceptance and integration.

## Validation and disposition

- Base decision-candidate SHA-256 before C001:
  `087bea706118ad43fd3812a0023633550063fa439577499a2da455b0d8303bd5`.
- Original `Deciding identity` block SHA-256:
  `7990d83b2cc9772c177cfe26d0aadaa2ec8433a5555a838b37705f30c919cce9`.
- Corrected effective block SHA-256:
  `37ed6095f0556b7462c0c5b9e3d6d4b0a89af7413725b9ae55642c8f6637fc1f`.
- Final decision-file SHA-256:
  `77d34a7e77d361e26c56dc3d7194095280de200dbacd912c606b2a2890100659`.
- Bound review-file SHA-256:
  `bdb531026a9b0951cb8df2f7e5af40bb688e30ec978500a7bbf553d8e4688070`.
- Expected Role-field population: base `Role: Management`; PART-01
  `Role: Architekt`; C001 `Role: Architekt`.
- Role-population validation finds exactly three Role fields with those exact
  values and zero `Role: Architect` occurrences. The DEC has exactly one
  correction event, C001, and no C002.
- The base/HEAD pin, exact three-path guard, original/effective block digests,
  base/final DEC digests, review digest, preserved-candidate reachability, and
  `git diff --check` all pass.
- `python3 _src/tools/process_doc_doctor.py --root . --json`: exit `0`,
  `ok: true`, 31 repository findings. The sole error remains the pre-existing
  broken link in `docs/dossiers/0044-03-gate-scope-proposal.md:146`; no finding
  is attributed to the new claim, DEC, or review.
- Changed paths are exactly the three declared paths. No policy projection,
  validator, backlog marker, Acceptance record, integration state, external
  state, cleanup, or push was changed.
