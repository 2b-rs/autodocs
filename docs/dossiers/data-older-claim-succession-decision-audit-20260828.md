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

Pending per-record classification and validation on the pinned baseline.

