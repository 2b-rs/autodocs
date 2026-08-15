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

## Open questions carried into 0021-02

- Whether `curation-item@v1`'s `item_kind` enum needs a new value (e.g.
  `review-request`) distinct from `record`/`ai-amendment`, or whether
  existing `item_kind="record"` with `origin="browser"` and a `category`
  field inside `decision_basis` is sufficient. `0021-02` must decide and
  document this before schema work begins.
- Exact retention/redaction rules for `self_declared` requester identity,
  to be defined alongside the schema in `0021-02`.

## Traceability

This document satisfies task **0021-01**'s Definition of Done: it is
internally consistent with `workflow-lifecycle.md`, `roles.md`,
`actions.md`, `status-model.md`, and `curation-item-schema.md`, and states
explicitly that the website never mutates records directly (Non-bypass rule
1). It supersedes no existing document; it is a new, additive specialization
for Feature `0021`.
