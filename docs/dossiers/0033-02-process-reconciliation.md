# 0033-02 — Website review-request process reconciliation (Class R candidate)

**Class:** R (reconstructed proposal). Not operative. Not `docs/pipeline/` content.
May only become Class O through `0033-04.01` approval, per
`docs/dossiers/0033-02-04-architect-scope-review.md` §2/§3.2. This document is the
review-ready candidate that `0033-04.01` reviews; it is not itself an approval.

**Status:** review-ready, unapproved, awaiting `0033-04.01`.

**Task:** `0033-02`. **Chain:** `chain-0033-chakotay`.

**Base pin:** `main@3736170586e85047ab68691f0596689610688d9c`.

**Baseline findings addressed:** `RRB-PROC-001`, `RRB-AUTH-001`, `RRB-PRIV-001`
(`docs/pipeline/review-request-baseline-audit.md`).

**Informed by (Class E, cited only, never merged):** historical substantive commit
`ac4b2579a5` (`docs/pipeline/website-review-flag.md` at that ref) and its dossier
`ee3dfe99c096:docs/dossiers/0033-02-process-reconciliation.md`. This document is a
fresh reconstruction against the current baseline, not a copy: structure, wording,
and several boundary decisions below differ from the Class E source, and every
claim here is re-derived from the baseline findings and the current `TODO.md`
acceptance criteria rather than assumed from the historical text.

---

## 1. Purpose and non-goals

This candidate defines the review-request *process* — who may do what, when a
submission is eligible, what happens on abuse, and what is retained — for the
website's "flag a published record/page for review" feature. It does not define
the wire schema (`0033-03`), the UX flows (`0033-04`), or approve anything
(`0033-04.01`). It supersedes the Feature `0036` protocol as the single normative
process source once landed to `docs/pipeline/website-review-flag.md`; until then
it is Class R only.

## 2. Non-optional structural boundaries

These are treated as fixed by this candidate — not open for `0033-04.01` to
reverse, only to approve the wording — because relaxing any of them reopens a
baseline defect (`RRB-PROC-001`/`RRB-AUTH-001`):

1. A submission is a **request**, never a curator decision or a factual mutation
   of the target record.
2. Three axes are kept separate and never collapsed into one status field:
   client/transport state, request/intake state, and target-record state.
3. Browser code, no-JavaScript ingestion, AI/automation, and report generation
   can never perform a human-only decision (accept/reject/apply/publish).
4. Only an authenticated human curator may accept or reject a request.
5. `rejected` is a **retained terminal closure**: the audit/result state stays
   visible, but no factual record change is ever applied or published from a
   rejected request. There is no `rejected → applied` or `rejected → published`
   transition, ever.
6. Queue *location* (e.g. `active/` vs `done/`) is storage, not status; status is
   an explicit field, never inferred from directory.
7. Nine distinct action identities are never merged: requester (unauthenticated
   claim), verified transport actor (GitHub/webhook identity), claimant (curator
   who takes ownership), proposer, decider (accept/reject), applier (writes the
   factual change), closer (finalizes the queue item), moderator (abuse/quarantine
   actions), publisher (makes an applied change externally visible).
8. Reports and dashboards consume classified projections of a request, never the
   raw payload (which may carry an evidence URL, free-text rationale, or PII).
9. Abuse/security-relevant intake is written to a separate, minimum-audience,
   restricted audit channel distinct from the ordinary request queue.
10. Any public-GitHub-transport path carries explicit data-minimization and
    "we cannot guarantee deletion on GitHub's side" disclosure to the submitter
    before submission.

## 3. Eligibility and exclusions

**Eligible targets:** any generated, published `<record>`/`<class>`/`<namespace>`
page that carries a stable `target_canonical_id` (the corpus's canonical
identifier for that page) at submission time. Concretely: pages under
`modules/`, `namespaces/`, `classes/`, `services/` and their per-language mirrors
that resolve to a real generated artifact.

**Excluded, with reasons:**

- Pages under any `invalid/*` tree — these are diagnostic placeholders, not
  published facts; there is nothing a review can change on them, and offering a
  control there previously produced silent no-ops (`RRB-UX-001`, cross-referenced
  from `0033-04`).
- The site index, search, and navigation chrome — not "records" in the reviewable
  sense; no `target_canonical_id` exists to attach a request to.
- Internal tooling/report output (`docs/pipeline/**`, `_src/**` build artifacts) —
  not public-facing published content, and no review-request UI is ever rendered
  there.
- A target with **no resolvable `target_canonical_id`** at submission time (e.g. a
  page that has since been removed from the corpus) — the request is refused at
  intake with a specific "target no longer resolvable" disposition, not silently
  accepted against a dangling reference (this closes `RRB-PROC-001`'s "missing
  immutable target metadata" gap).
- A target that already has an **active** (open or claimed) request for the same
  concern — see §4.4 duplicate handling; this does not exclude a *new distinct*
  concern against the same target.

## 4. Lifecycle and authority

### 4.1 States (request axis)

`local-only` (drafted, not yet submitted) → `submitted` (client believes it sent
it) → `open` (durably queued, unclaimed) → `claimed` (a curator has taken
ownership) → **terminal**: `applied` (curator accepted and the factual change was
made) | `rejected` (curator declined; no change made) | `refused`/`quarantined`
(pre-queue intake disposition — never conflated with curator `rejected`) |
`stale` (superseded by the target changing before decision) | `superseded`
(duplicate collapsed into an earlier active request for the same concern).

`open`/`claimed` are **active**; every other state is terminal or pre-queue.
There is no route from any terminal state back to `open`/`claimed`, and no route
from `rejected` to `applied`.

### 4.2 Per-action authority matrix

| Action | Who | Notes |
|---|---|---|
| submit | anyone (may be anonymous/unauthenticated) | produces a request, not a decision |
| ingest | trusted transport adapter (GitHub webhook, authenticated API refetch, or the no-JS ingestion path) | validates envelope trust before the request becomes `open`; never a human action |
| claim | authenticated human curator | moves `open` → `claimed`; exclusive — a second claim attempt is refused |
| propose | authenticated human curator (may be the claimant) | records the intended disposition before decision, for audit |
| accept / reject | authenticated human curator (the decider) | terminal decision; may differ from the claimant only under an explicit reassignment record |
| apply | authenticated human curator, only from `accept` | writes the factual record change; never automatic, never from `reject` |
| close | authenticated human curator or automated closer once terminal | finalizes the queue item; physical, not semantic |
| moderate (quarantine/release/refuse/escalate) | authenticated human moderator | pre-queue and abuse-path actions; distinct from curator decision authority |
| publish | authenticated human curator/release authority | makes an `applied` change externally visible; may be deferred from `apply` |

### 4.3 Rejected-no-apply invariant

`rejected` never leads to `apply` or `publish` under any circumstance, including
moderator override, batch reprocessing, or later resubmission of the identical
concern (a later resubmission is a *new* request, evaluated independently; it
does not resurrect the rejected one). This closes the historical defect where
"rejected closure conflicted with the terminal lifecycle" (`RRB-PROC-001`).

### 4.4 Duplicate/recurrence handling (process view; canonical identity is `0033-03`'s)

A new submission against a target that already has an **active** request for the
same concern is not queued as an independent second item: it is recorded as
`superseded` and linked to the active request, and the submitter is told a
request already exists (exact transport-level mechanics — deterministic concern
key, digest binding — are `0033-03`'s scope, not repeated here). Two submissions
against the *same target* but *different* concerns are independent active
requests. A submission against a target that has a **terminal** request for the
same concern is treated as new (not blocked), because circumstances may have
changed since the terminal decision.

## 5. Abuse, moderation, and escalation

| Case | Disposition | Authority |
|---|---|---|
| Repeated submissions from the same unauthenticated origin exceeding a rate/quota | quarantine at intake, no queue entry created | moderator (automated pre-queue check, human review on escalation) |
| Sensitive-category content (self-harm, harassment targets, legal) in the free-text rationale | quarantine, restricted-audience review only | moderator |
| Malicious-link evidence URL (known-bad scheme/host pattern) | refuse at intake, log to restricted abuse channel, no queue entry | automated intake check + moderator audit |
| Attribution-policy conflict (submitter claims authority they cannot demonstrate) | queued normally but flagged; curator decides with the flag visible | curator, informed by moderator flag |
| Suspected coordinated abuse (volume pattern across origins) | temporary submission suspension for the pattern, escalation to moderator | moderator, with defined suspension window (owned by `0033-07.04`) |

Every moderation action is itself audit-logged to the restricted channel (§2
item 9), separate from the ordinary request queue, so moderation history is
reviewable without exposing it in public/operator projections.

## 6. Retention, redaction, disposal (candidate schedule — not yet approved clocks)

The following are proposed default clocks so `0033-04.01` can approve, adjust, or
reject exact values rather than approve a placeholder "as needed":

| Data class | Location | Proposed retention |
|---|---|---|
| local, unsubmitted draft | browser `localStorage` | 30 days since last edit, then auto-cleared |
| active raw request (payload, rationale, evidence URL) | request queue | until terminal; alert at 30 days open, escalate at 90 days open |
| quarantined raw content | restricted moderation store | 30 days, unless released or placed under a named, reasoned, time-bounded hold |
| terminal raw request (closed) | queue `done/` | closure + 90 days, then redact free-text/evidence fields, retain structured audit fields |
| ordinary diagnostics/logs | operational logs | 30 days |
| restricted abuse/security audit trail | restricted audit store | 180 days rolling |
| sanitized, non-personal audit summary | project records | project records retention (unbounded, non-personal) |
| backups | backup rotation | max 90-day candidate rotation, tombstoned on deletion request where technically possible |
| GitHub Issue/comment/attachment (public transport) | GitHub | **no guaranteed project-controlled erasure** — disclosed to submitter before submission (§2 item 10) |

**These clocks are not effective policy before `0033-04.01` approves them.** A
hold that extends any clock is valid only with a named authority, a stated
reason, the exact fields covered, a start time, and a review/expiry date.

## 7. Open decision axes reserved for `0033-04.01` (`PROC-0033-02-01`–`17`)

Per the architect scope review §7, this candidate states a position on every axis
but treats none as binding until `0033-04.01` approves it. Axes `-01`, `-02`,
`-03` are this Task's own implementation-owned axes; the remainder are owned by
later Tasks but are listed here because `0033-02` is where they are first framed
process-wise.

| Axis | Subject | This candidate's position |
|---|---|---|
| `PROC-0033-02-01` | Canonical process source and supersession | This document (once landed to `docs/pipeline/website-review-flag.md`) is the single source; Feature 0036 protocol becomes non-normative historical overview only |
| `PROC-0033-02-02` | Eligible record/page/status inventory, `invalid/*` exceptions | §3 above |
| `PROC-0033-02-03` | Null/unversioned legacy target rule | A request against a target with no resolvable `target_canonical_id` is refused at intake with an explicit disposition, never silently accepted (§3) |
| `PROC-0033-02-04`–`17` | (owned by later Tasks per scope review §7) | Framed in §4–§6 above; final wording and approval is those Tasks' and `0033-04.01`'s |

## 8. Requirement-to-section matrix (acceptance criteria traceability)

| `0033-02` acceptance criterion (verbatim from `TODO.md`) | Section |
|---|---|
| eligible record/page kinds and exclusion reasons | §3 |
| behavior for missing immutable target metadata / already-open/claimed requests | §3, §4.4 |
| request vs. curator decision separation | §2 item 1, §4.2 |
| submit/ingest/claim/propose/accept/reject/apply/close/publish authority | §4.2 |
| `rejected` retained terminal, no apply/publish | §4.3 |
| repeated/abusive/sensitive/malicious/attribution cases + moderation/escalation | §5 |
| actor claim, trusted envelope, rationale, evidence, diagnostics, receipts, queue/history retention | §6 |
| browser/AI/ingestion cannot mutate facts or perform human-only decisions | §2 item 3, §4.2 |

## 9. Scope statement (this candidate)

This dossier is the entire Class R deliverable for `0033-02` at this stage. It
does not write to `docs/pipeline/**` — landing it there (byte-identical or
adapted) is a distinct, later act gated by `0033-04.01` approval and performed
through that Task's own governed route, per architect scope review §2/§6.

## 10. Validation performed

- Manual cross-check: every `0033-02` acceptance-criterion clause in current
  `TODO.md` (line 1727–1731) has a corresponding section above (§8 matrix).
- Manual cross-check: no clause here permits `rejected → applied`/`published`
  (§4.3), no clause equates request ingest with a curator decision (§2 item 1,
  §4.1), all nine actions in §4.2 carry an authority and non-capability boundary,
  every data class in §6 has a location/clock, and axes `-01`–`-03` are stated.
- `git diff --name-only main...chain-0033-chakotay` (run after this commit):
  confirmed no touched path under `docs/pipeline/**`, `AGENTS.md`, `SANDBOX.md`,
  `PRIVILEGED.md`, `CLAUDE.md`, `DONE.md`, or
  `docs/pipeline/{branch-workflow,process-roles,task-acceptance}.md`.
- Not run: `_src/validate.py` (this Task touches no generated-tree source; no
  `_src/` content changed).

## 11. Provenance

Requested by dispatch briefing (Dispatcher `chakotay`, atomic AWARD
`1787970210735-b3950909`, thread `0033-chain`), executed under claim
`TODO-Chakotay-Paris-0033-chain-20260830T113000Z.md`,
owner_token `agent:chakotay-paris:0033-chain:20260830T113000Z`. Authored
2026-08-30 against `main@3736170586e85047ab68691f0596689610688d9c`.
