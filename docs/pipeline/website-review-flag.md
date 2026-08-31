> [!NOTE]
> **Future/Target State:** The manual operator guidance and limitations described below represent the historical 0021 implementation. Feature 0045 will introduce an automated event-driven architecture that supersedes the manual ingestion and AI proposal steps, while preserving the Kurator's exclusive authority to accept or apply changes. See [score-feedback-loop.md](score-feedback-loop.md) for the target automated process contract.

# Website-Initiated Specification Review Flags — Process Definition (0021-01)

Status: drafted for **0021-01**. Normative for Feature `0021` as a whole;
consumed by `0021-02` (submission schema), `0021-03` (ingestion boundary),
and `0021-04` (record-page UX).

## Purpose

Define the authoritative process, role boundaries, and non-bypass rules for
a website visitor's "Flag for review" action on a published specification
record — including records currently `valid/*` — without granting any
browser, tool, or AI-agent code the ability to change that record directly.

This document specializes the general roles (`roles.md`), status model
(`status-model.md`), unified lifecycle (`workflow-lifecycle.md`), and action
catalogue (`actions.md`) to the one new entry point Feature `0021`
introduces: an unauthenticated-or-authenticated *reader*, as opposed to the
existing *author/reviewer* who has already inspected requirement text in the
`review.js` widget.

## Actors and role boundaries

| Role | May do | May NOT do |
|---|---|---|
| **Requester** (website reader, `github_authenticated` or `self_declared`) | Submit a re-review request for any published record, with rationale, category, and optional external evidence references. | Change record status/content; approve, reject, close, or withdraw the request; submit on behalf of another identity. |
| **Ingestion tool** (`curation_ingest.py` or delegated adapter, role `tool` per `roles.md`) | Validate schema, verify target record/version/hash, de-duplicate, and create an `open` curation-queue item (`discovered -> queued`, per `workflow-lifecycle.md`). | Decide `accepted`/`rejected`; write to any record field; skip validation for any transport (GitHub issue or JSON). |
| **KI-Agent (Review/Kuration)** (role `ai` per `roles.md`) | Claim the queued item, research the cited evidence, and propose a concrete change as a `proposed` curation item. | Call `complete_flag()`; commit or merge; apply the proposal to the record. |
| **Kurator** (human operating the extraction scripts, role `curator` per `roles.md`) | Review the proposal, accept/reject it, and — only if accepted — apply it and call `complete_flag()`, closing the item. | N/A (this is the only role with final authority). |

This mirrors the existing curation-queue role split in `roles.md` exactly;
Feature `0021` adds no new role, only a new *origin* (`browser`, already
present in `curation-item@v1`'s `origin` enum, see `curation-item-schema.md`)
for how an item enters `discovered`.

## Lifecycle semantics

A website-initiated flag follows the existing unified lifecycle
(`workflow-lifecycle.md`) unmodified:

```
discovered -> queued -> claimed -> proposed -> accepted/rejected -> applied -> published
```

- **Entry point**: `curation_ingest.py` (or its Feature-0021 adapter) writes
  `discovered -> queued` via `curation_flags.write_curation_flag`, exactly as
  it does today for browser-submitted curation decisions — the only
  difference is `item_kind` is a new value distinguishing "request a
  re-review" from "decide an existing curation case" (see Open questions).
- **No shortcut edges for this entry point.** Unlike
  `review_ingest.ingest` (`discovered -> applied` direct) or
  `hypothesis_store.record_hypothesis` (`discovered -> proposed` direct),
  a website review-flag MUST NOT skip `queued` or `claimed`: it always
  requires an AI-agent proposal and a human accept/reject step. This is the
  central non-bypass rule for this feature.
- **`valid/*` re-review rule**: flagging a `valid/*` record for review does
  not change its `status.state`. The record stays `valid/*` and continues to
  publish normally while the linked curation item is `queued`/`claimed`/
  `proposed`. Only a Kurator's explicit accept + apply (writing a new
  `history[]` entry per `status-model.md`) may change the record's status.

## Non-bypass rules (normative)

1. No browser code may write to `spec/curation-queue/` directly; it may only
   produce a submission package consumed by the existing
   browser-to-GitHub/JSON boundary (`review.js` transport pattern) and the
   existing `curation_ingest.py` queue-creation path.
2. No AI agent may call `complete_flag()` for a website-initiated item; that
   remains exclusively a Kurator action, consistent with the existing rule
   in `curation_flags.py` docstring.
3. A flag on a `valid/*` record is a **request for re-curation**, never an
   implicit rejection, retraction, or edit of the current publication.
4. Stale submissions (target `content_hash`/version no longer current) and
   duplicate submissions (open item already exists for the same canonical
   ID) must be rejected by the ingestion tool with an actionable diagnostic,
   never silently merged or silently dropped.
5. `self_declared` identity is accepted but must carry a lower-confidence
   warning end-to-end (report views, queue item), mirroring the existing
   `review.js` warning text for unauthenticated review packages.

## Review vs. curation routing

A website review-flag is routed identically to an existing
`kind: "curation_request"` package (see `curation_ingest.py`), not to the
requirement-text review path (`kind: "requirement_text"`, handled by
`review_ingest.py`). Rationale: a reader flagging AI-generated prose is
raising a *curation* question ("should this record's derived content be
re-examined"), not submitting a *requirement-text* correction with a known
target value — matching the distinction already drawn in `roles.md`'s
Rollenbeziehungen diagram between the `Autor` (browser) path and the
queue-based curation path.

## Open questions carried into 0021-02 (resolved)

- Resolved in `curation-item-schema.md` and `curation_item.py`:
  `item_kind` has a dedicated `"review-request"` value, distinct from
  `record`/`ai-amendment`; `decision_basis` carries `transport` and
  `authoritative_actor` for this kind (see `review-request-package-schema.md`).
- Retention/redaction for `self_declared` requester identity: no additional
  redaction beyond the existing lower-trust warning (rule 5 above) is
  applied; the self-declared name/handle is retained verbatim in the queue
  item and report views, exactly as `review.js` already retains
  self-declared identity for requirement-text reviews.

## Operator guidance: submit, triage, decide, follow (0021-08)

This section is the single end-to-end walkthrough for a Kurator handling a
website-originated re-review request, tying together the process rules
above with the concrete tools/reports that implement them.

1. **Submit** (requester, no Kurator action). A reader uses "Flag for
   review" on any record page (`review-request-ux.md`). Depending on
   identity path and network access, the result is either a created GitHub
   issue (`submitted`) or a downloaded JSON package the requester must
   hand-deliver (`exported` — explicitly *not* yet submitted; see
   `review-request-ux.md`, Success/error/stale states).
2. **Discover** (Kurator). Open items surface in two places, kept
   consistent by `curation_item.py`'s shared normalization:
   record pages show an open request inline in the history/provenance area
   (0021-06 rendering), and `curation-report.html` /
   `open-reviews.html` list every open and recently decided item across
   both queues (`reports.md`, Kurationsbericht / Offene-Reviews-Bericht).
3. **Ingest** (Kurator or automation, via `review_request_ingest.py`). Run
   `review_request_ingest.py --apply <paket.json>` for a JSON export, or
   feed a GitHub issue body through the same ingestion path for a
   `submitted` request. This step validates schema, target
   version/content-hash freshness, and duplicate status per Non-bypass
   rule 4 above — a stale or duplicate submission is rejected here and
   never reaches the queue (verified end-to-end by
   `_src/tests/test_review_request_ingest.py`).
4. **Triage/weigh trust** (Kurator). Before acting on the request, check
   `decision_basis.authoritative_actor` and the identity-kind badge
   (`github_authenticated` vs. `self_declared`) surfaced on both the record
   page and in the report. A `self_declared` request is a valid input to
   consider, never a directive — Non-bypass rule 5 and this document's
   Actors table make clear the requester cannot approve, reject, or change
   record status themselves.
5. **Decide** (Kurator, exclusive authority). Exactly as for any other
   curation item: review the linked record/version/rationale/evidence,
   then accept or reject. Accepting still requires the normal
   apply-then-`complete_flag()` step (Actors table, Kurator row); rejecting
   requires only `complete_flag()` with the rejected outcome. Neither the
   requester nor any AI agent may perform this step (Non-bypass rule 2).
6. **Follow** (requester and Kurator). The requester has no push
   notification; they follow progress by revisiting the record page (open
   request state is visible until decided) or the linked GitHub issue if
   `submitted` via that transport. The Kurator's decision is durably
   recorded in `history[]` (status-model.md) and remains visible in
   `curation-report.html` after closure, including `rejected` outcomes,
   which are shown rather than dropped from the report.

### Authority and confidence framing (report views)

Reports must describe *what was submitted and by whom*, never imply that a
submission alone changes anything: `curation-report.html` labels
web-originated items with their `origin: "browser"` and identity-kind badge
precisely so a reader of the report cannot mistake an open, undecided
request for an accepted change. This is the same principle as Non-bypass
rule 3 (a flag is a request, never an implicit rejection/retraction),
applied to the reporting surface rather than the record surface.

### Known limitations (for release notes)

- **No authentication strength guarantee**: `github_authenticated` proves
  only that the requester is signed in to *some* GitHub account at
  submission time, not that the account has any standing relationship to
  the affected specification area; it is a phishing-resistant identity
  signal, not an authorization signal.
- **`self_declared` identity is unverified** by construction; it is a
  free-text name/handle with no cryptographic or account-based backing.
- **No SLA on triage latency**: an open request has no automatic escalation
  or expiry; it remains `open`/`claimed` until a Kurator acts. Long-lived
  open requests are visible in `open-reviews.html` for manual follow-up.
- **Export-not-submitted requests are invisible to the pipeline** until a
  human re-delivers the JSON file; the system cannot know a download
  happened, only that a file was produced (`review-request-ux.md`,
  `exported` state).

## Traceability

This document satisfies task **0021-01**'s Definition of Done: it is
internally consistent with `workflow-lifecycle.md`, `roles.md`,
`actions.md`, `status-model.md`, and `curation-item-schema.md`, and states
explicitly that the website never mutates records directly (Non-bypass rule
1). It supersedes no existing document; it is a new, additive specialization
for Feature `0021`. The Operator guidance section above additionally
satisfies task **0021-08**'s acceptance criteria (submit/triage/decide/follow
guidance, non-overstated report authority, documented limitations).
