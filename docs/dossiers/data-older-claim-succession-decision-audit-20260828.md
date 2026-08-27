# Management Decision A — older Data claim lifecycle reconciliation

record_kind: management-decision-audit@v1
item_id: data-older-claim-succession
recorded_by: Data, Architect, Team Enterprise
decision_authority: Management
decision_reference: agent-inbox:1787869861596-4caa9083
offer_reference: agent-inbox:1787869917729-22cea7d3
award_reference: agent-inbox:1787869988940-3549ff1a
scope_reference: agent-inbox:1787870046424-24c623f6
baseline: main@1969e055a5d9697b1db32ca15d5294b290d6f9fc
recorded_at: 2026-08-28T00:34:06+02:00

## Context

The runtime projection listed 14 older Data coordination records. Their primary
lifecycle fields were not uniformly aligned with their append-only completion
and handoff histories, so a scanner could mistake completed Architect work for
unfinished ownership. Nineteen `TODO-data-*` files exist on the baseline; only
the exact 14 paths named in the scope reference are authorized here.

## Decision

Management selected Decision A: audit and reconcile each of the 14 records
individually, preserve history, and transfer nothing unless genuinely unfinished
work is proven. No blanket succession, inferred ownership, deletion, historical
rewrite, or normalization outside the pinned population is permitted.

## Operative effect

1. Each record receives an evidence-backed classification on the exact baseline.
2. A terminal or coordination-complete record may have only its stale
   lifecycle/scanner fields normalized; append-only narrative and immutable
   owner-token history remain intact.
3. Duplicate identities are recorded and preserved, not deleted or merged.
4. Any genuinely unfinished record must be listed with current branch,
   worktree, baseline, and scope; the audit itself does not transfer it.
5. The candidate remains on its item branch for separate integration handling;
   this Architect does not advance `main`.

## Alternatives considered

- Blanket succession or transfer: rejected because filenames, display identity,
  and stale scanner fields do not prove current-session ownership.
- Leave every projected field unchanged: rejected because proven stale fields
  continue to advertise completed coordination as active work.
- Delete duplicate or terminal records: rejected because the records are
  append-only provenance and may be the only durable explanation of earlier
  branch and authority decisions.

## Verification and rollback

The audit must cover exactly 14 records, prove the changed-path set is within
the assignment, validate duplicate identity preservation, and disclose every
uncertain or unfinished result. Rollback is omission of the candidate from
integration or a later append-only correction; history is never rewritten.

## Audit result

The exact population contains six records whose existing primary lifecycle was
already terminal, seven coordination-complete records whose primary field was
stale-open, and one inactive duplicate-provenance record. No genuinely
unfinished Data-owned claim was found.

| # | Record | Classification | Evidence on pinned baseline | Normalization |
|---:|---|---|---|---|
| 1 | `TODO-data-0038-35-terminal-integration-20260825T192007Z-6d7f42a9.md` | coordination complete; stale `state: [ ]` | `architect_work_product_status: [x]`; handoff-only close at `8a364e000fed6e826a1e7d49c4b1c014c849eece` | primary state `[x]`; recorded Task state `[ ]`; complete; lease false |
| 2 | `TODO-data-0044-05-20260825T165207Z-4f9c2a71.md` | coordination complete; stale `status: [p]` | all architecture actions completed and distinct implementation handed off; last record commit `6b8ff993daa602ae94971ccee3c21982264aad13` | state/status `[x]`; complete; lease false |
| 3 | `TODO-data-0044-06-dec-0044-026-c002-20260826T135755Z-190105ed.md` | coordination complete; stale `state: [ ]` | existing `coordination_state: complete` and `architect_work_product_status: [x]`; current-main re-pin `b9fc1f7b9f1a2ea4bfa54bec5041e10b6911e238` | primary state `[x]`; recorded Task state `[ ]`; lease false |
| 4 | `TODO-data-0037-16-marker-20260827T064135Z-60ba633e.md` | terminal as recorded | existing `[x]` completion at `78d658840d47ea5ecc4820f6cd0696ef075d2dcb` | canonical terminal/complete/lease-false fields added; narrative unchanged |
| 5 | `TODO-data-0019-13-scope-review-20260825T061653Z-1750c1d4.md` | terminal as recorded | existing `status: [x]`; final review bookkeeping `0092d364fcb555a653899da0a85977fd2ce49ce0` | canonical state/complete/lease-false fields added |
| 6 | `TODO-data-0038-34-20260825T092500Z.md` | terminal as recorded | existing `[x]` and completed Architect reconciliation at `28d7a00918498685b1fc13b711840df415142ecf` | canonical terminal/complete/lease-false fields added |
| 7 | `TODO-data-0044-memory-hygiene-rereview-20260825T071244Z-29d37e749.md` | terminal as recorded | existing `status: [x]`; bounded retention and incident disclosure finalized at `15dd2f4bf7e56703e6de6abc87951e3e3affa33c` | canonical state/complete/lease-false fields added; incident history preserved |
| 8 | `TODO-data-0037-16-tk2-dec-0037-004-20260827T015709Z-33286f2b.md` | terminal as recorded | existing `[x]` completion and additive correction at `183d836367617980473798fa93d8753f59cc5730` | canonical terminal/complete/lease-false fields added |
| 9 | `TODO-data-0044-06-cognitive-demand-architecture-20260825.md` | inactive duplicate provenance | existing `historical_disposition: inactive-coordination-provenance`, `lease_active: false`, and canonical-path pointer at `9c7ce1ce7b33aceec62d61e82509d7a4bd1e74c9` | state `[x]`; recorded Task state `[ ]`; filename and immutable token preserved |
| 10 | `TODO-data-0041-02-dec-0041-006-20260826T125524Z-5086733f.md` | coordination complete; stale `state: [ ]` | existing `coordination_state: complete` and `architect_work_product_status: [x]`; decision check-in `059f7e326ad0a8447c9f54205841bf27d24dc786` | primary state `[x]`; recorded Task state `[ ]`; lease false |
| 11 | `TODO-data-0037-51-runner-role-amendment-20260824.md` | terminal as recorded | existing text says completed and lease released; final bookkeeping `b38c3202d0d40812733204d4386388ff73234599` | canonical terminal/complete/lease-false fields added; prior disposition retained |
| 12 | `TODO-data-0038-35-claim-carriage-20260825T211241Z-c86a50d2.md` | coordination complete; stale `state: [ ]` | existing `coordination_state: complete` and `architect_work_product_status: [x]`; final re-pin `433b41b04cd4b353f9681947a9e3c7897a751855` | primary state `[x]`; recorded Task state `[ ]`; lease false |
| 13 | `TODO-data-0044-06-cognitive-demand-20260825T214726Z-0d41a19f.md` | canonical coordination complete; stale `state: [ ]` | existing `coordination_state: complete`, `architect_work_product_status: [x]`, and canonical identity repair at `9c7ce1ce7b33aceec62d61e82509d7a4bd1e74c9` | primary state `[x]`; recorded Task state `[ ]`; lease false |
| 14 | `TODO-data-0044-05-governance-20260825T172721Z-0c5e91b4.md` | coordination complete; stale `status: [p]` | DEC-0044-025 candidate and integration handoff committed at `a058b915d6cc771e0586028bb060d496bca46924` | state/status `[x]`; complete; lease false |

All 13 distinct evidence commits above are ancestors of the pinned baseline.
Records 9 and 13 intentionally retain the same immutable owner token and the
same last record commit; they remain two files with explicit historical versus
canonical roles. The audit neither merges nor deletes them.

## Genuinely unfinished claims

None. Therefore there is no unfinished branch, worktree, baseline, or scope to
transfer or list. Historical branch/worktree strings remain provenance only and
do not establish a current lease.

## Validation result

- Exact scope: 16 changed paths from the pinned baseline — the 14 authorized
  older records, this audit dossier, and the new claim; zero other paths.
- Population: all 14 records are represented exactly once in the table. The
  preserved cognitive-demand owner token occurs in exactly two files, the
  historical and canonical paths required by the earlier identity repair.
- Evidence: all 13 distinct last-record commits are ancestors of
  `main@1969e055a5d9697b1db32ca15d5294b290d6f9fc`.
- `git diff --check`: pass.
- `process_doc_doctor.py --root . --json`: exit `0`; 154 documents, 32
  findings, one existing error; zero findings on this audit dossier. The
  finding total matches the pinned-baseline run, which covered 153 documents.
- `legacy_task_doctor.py --root . --json`: expected repository-wide exit `1`;
  878 findings (`629` errors, `248` warnings, `1` info). Lifecycle normalization
  removes `state` from the missing-field lists of the six legacy records that
  lacked a canonical state field. Three coordination-only records still report
  `LTD-CLAIM-STATE-DIVERGED` because their parent Tasks remain `[ ]`; their
  preserved `recorded_task_state: [ ]` makes that distinction explicit. Four
  records report the expected retained-terminal finding because Decision A
  requires their provenance to remain. Other identity/scope findings predate
  this audit and were not rewritten.
- The new claim has one disclosed `LTD-CLAIM-IDENTITY-MISMATCH`: Management
  prescribed the non-Task item and exact filename, so inventing a numeric Task
  identity or renaming the claim would violate the assignment. Its other
  canonical startup, state, execution-authority, and next-step checks pass.
- No product, `TODO.md`, `DONE.md`, Acceptance, checkpoint, integration,
  `main`, external state, automation-safety incident, or path outside the exact
  assignment changed.
