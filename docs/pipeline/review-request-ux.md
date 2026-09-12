# Website Review-Request UX Contract — v2 candidate (`0033-04`)

**Status:** Review-ready UX candidate, **not approved**, not a browser/store/
transport implementation, and not authority to submit, ingest, queue, decide,
apply, publish, or modify a record. It is effective only if the combined suite
is approved by `0033-04.01`.

**Depends on:** the process candidate in [website-review-flag.md](website-review-flag.md),
the package contract in [review-request-package-schema.md](review-request-package-schema.md),
and the shared browser contract in [review-browser-transport-v2.md](review-browser-transport-v2.md).
Those contracts control semantics; this document controls user-visible behavior.

## 1. Scope, invariants, and ownership

The UX creates only a credential-blind `review-request-package@v2` client claim
and may stage, export, or transfer its exact bytes. It never creates a queue
item, verified identity, transport receipt, server time, authoritative status,
or a factual record change. A request is not a curator decision.

`0033-10.01` owns the concrete shared IndexedDB collection/migration/drawer;
`0033-10`/`.02` own browser adapters; `0033-11.01` owns transport; `0033-05.01`
owns trusted ingress/receipts; `0033-06` owns live target/trust validation. This
contract does not authorize any of them.

## 2. Where the action appears

| Context | Required presentation | Result |
|---|---|---|
| One published, eligible `valid/*` record with complete immutable metadata and no known active duplicate | Secondary control below record content and beside provenance/history, labelled **Request review** | Opens the draft dialog. |
| `valid/curator-decided` | Same placement and label; read-only status disclosure says “Curator-decided” | Does not imply the value is wrong or reopen it. |
| Known active same-concern request | Replace the control with a privacy-safe informational link/status | No second draft is opened. |
| Missing/inconsistent metadata, excluded `invalid/*`, draft, unpublished, multi-record, index, report, diagram, search, download or process page | No request action; an eligible canonical-record link may be offered where applicable | No package is constructed; implementation reports the inventory finding. |
| Authenticated internal curation/report context | Separate, clearly internal entry point; it must name its different authority and must not masquerade as public intake | Any behavior requires its own approved contract. |

The implementation never exposes an action for historical `invalid/*` pages just
because the legacy draft did. The target context is captured only from the
rendered eligible record; users cannot type or replace it.

## 3. Draft form and immutable disclosure

The dialog begins with an `aria-describedby` target summary containing title,
canonical ID, displayed status, version ID, content SHA-256, and stable source
URL. These are read-only claims bound into the package and revalidated later;
the display is not proof of current freshness.

| UI input | Package field | Rule |
|---|---|---|
| Category | `category` | Required single select over the five v2 values; no silent default. |
| Why should this be reviewed? | `rationale` | Required; validate the v2 3–4000 character, NFC/control-character limits before confirmation. |
| Supporting link | one `evidence_refs` entry with derived `kind=url` | Clearly optional; HTTPS, public-safe URL validation only. No fetch occurs. |
| Additional context | one `evidence_refs` entry with derived `kind=note` | Clearly optional; plain text only. The user never selects internal kinds. |
| Identity choice | `actor_claim` | Explicit `anonymous` or `self-declared` (with display name); no GitHub-authenticated client value exists. |

At most the v2 evidence limit is exposed. Citation support, if approved later,
uses a distinct labelled control and derives `kind=citation`; it is not inferred
from arbitrary free text. Field errors are stable, local, and do not echo unsafe
values.

Before the first input and immediately before confirmation, show: “This submits
a request for review. It does not change this record, its status, or its source.”
The public-GitHub path additionally warns that Issue bodies/comments/attachments
may be public and difficult to delete, that secrets/restricted personal data must
not be entered, and that GitHub identity is transport evidence only after trusted
adapter verification. A signed-in browser state is not a client claim and does
not change export eligibility.

## 4. One byte-bound confirmation and transport choices

Confirmation renders the exact canonical package bytes (or deterministic
field-for-field representation plus displayed SHA-256 and copy/download action)
that export, direct transfer, retry, and later ingress bind. Confirmation is
blocked on local validation failure; it has **Edit**, **Cancel**, **Export JSON**,
and only an approved configured transfer action. There is one package builder for
direct and collected paths. Rebuilding, transport-specific field insertion, or
silent identity upgrade is forbidden.

| Choice/outcome | Truthful copy and boundary |
|---|---|
| Local draft | `local-only`: retained only in the local draft store; no transfer occurred. |
| JSON export | `exported`: “Downloaded — not submitted or queued.” The download is the exact confirmed bytes and remains self-declared/anonymous. |
| Configured GitHub transfer succeeds | `submitted-with-receipt`: show receipt URL/number and exact package digest; say “submitted, awaiting intake”, never “queued”. |
| Transfer outcome is ambiguous/fails | `unknown` or `transport-failure`: preserve exact draft; offer retry of the same bytes; do not claim delivery. |
| Ingress later validates/queues | `ingested/queued`: only an authenticated receipt/status lookup can show this state. |
| Intake refuses/quarantines | Show safe code and channel where a receipt/status lookup supplies it; distinguish invalid, stale, duplicate, rate-limited and governed outcomes. Do not expose unsafe raw diagnostics. |
| Curator outcome | Show accepted/rejected/closed only from an authorised projection. Rejected is retained closure and never means the target changed. |

Server-owned envelope fields (verified actor, Issue/repository/delivery identity,
received time, receipt, route, queue ID and lifecycle result) do not exist in the
form or confirmed package. Display them only after a trusted adapter/status
projection supplies them. A browser cannot infer ingestion from a GitHub page.

## 5. Identity, edit, retry, duplicate, and stale rules

A retry of an ambiguous or failed transfer reuses the exact event ID, package
bytes, digest and concern key. An intentional edit returns to the form and mints
a new event ID/created time/package digest under the v2 contract; evidence-only
edits retain the concern key, while target/category/rationale changes recompute
it. Local copy removal never rewrites an exported/received immutable package.

A pre-open duplicate result prevents opening another draft. A race after
confirmation is resolved only by authoritative ingest: it returns the
privacy-safe leading reference or duplicate result with no new queue item. Page
age, build time and UUID time are not stale detection. The UX may say that a
submission will be rechecked; only live lookup and the queue reservation can
return `stale`/`ineligible`.

## 6. Shared IndexedDB migration and local-data controls

The target design is one physical database `ara-review-browser`, version `2`,
object store `collection`, using `browser-review-store-record@v2`. Feedback
records use exactly `entry_type=feedback` with
`payload_schema=review-request-package@v2`; review/curation/governance records
remain distinct typed pairs. The implementation must not treat a review decision
as a feedback request or keep two writable authorities.

Migration input is allowlisted: the historical `ara-review-package-v1` source
may contain Review/Curation entries, while a declared feedback-draft source is
separately named and mapped only if it yields valid v2 feedback. PAT, token and
identity convenience keys are excluded. Valid sources map deterministically to
entry ID, payload digest, revision and timestamps. Source is preserved until an
explicit verified migration disposition; corrupt, sensitive, oversized, unknown,
conflicting or stale source remains preserved with bounded diagnostics and no
entry write.

Migration is idempotent and transaction-safe: same deterministic ID/digest is a
retry; same ID/different digest aborts; tombstones prevent resurrection. Multi-tab
updates use the monotonic revision/transaction conflict rule rather than last
writer wins. Quota, unavailable storage, interrupted migration and clear-local-
data are visible recoverable states. Clear-local-data first shows affected draft
counts/types, preserves tombstones/required migration evidence per approved
retention policy, and cannot delete server/Issue/queue data. Delayed submission
always uses the exact preserved bytes and still undergoes authoritative stale
validation. Concrete transactions and retention periods remain approval choices
for `0033-04.01` and implementation work for `0033-10.01`.

## 7. Accessibility, responsive behavior, and cancellation

The trigger is a semantic `<button>` with a unique accessible name. Each dialog
has a unique `aria-labelledby` and target summary association; opening places
focus at the dialog heading/first invalid input, traps focus while modal, and
returns focus to its originating trigger on Cancel, Escape, completion, or close.
Visible focus is never removed. Inline errors are associated with fields; a
polite live region announces draft/confirmation state and success, while an
assertive bounded region announces blocking failures without moving focus away
from correction. Cancel confirms discard only if the local draft changed and
never claims remote cancellation.

Desktop is the normal modal at **768 px and above**. At **below 768 px**, use a
full-viewport sheet with a persistent target summary, single-column controls,
44 CSS-pixel minimum targets, no hover-only operation, and no hidden horizontal
confirmation content. Keyboard, touch, zoom, reduced-motion, and screen-reader
flows reach every action without drag, timing, or colour-only cues.

## 8. No-JavaScript GitHub Issue intake

No-JavaScript pages must not use a static URL that pretends to mint package
metadata. The eligible record page offers an Issue-form route carrying only
escaped, prefilling untrusted target context and clear public-data disclosure.
GitHub provides the submission confirmation/Issue receipt; it does not prove
queueing. The trusted ingress adapter refetches the Issue, validates form/body
and repository binding, derives all server-owned request/envelope metadata,
normalizes an allowed package, and performs the same live lookup/duplicate/stale
checks as JavaScript-originated intake.

Signed-out users may use the public route subject to GitHub sign-in and the
approved policy. If GitHub blocks submission, form configuration is unavailable,
or ingress cannot verify/normalize the Issue, show the safe failure/next-contact
path and create no client/server queue claim. No-JS input cannot supply verified
identity, receipt, authority, route or writer fields.

## 9. Open decisions for `0033-04.01`

Approval must select transport profiles and public receipt/status lookup policy;
identity/mismatch handling; exact citation control; eligible internal/report
contexts; migration source key and retention/clear-data/tombstone behavior;
quota limits; moderation wording; no-JS Issue-form repository/template; and
privacy-safe duplicate/curator projection. Until then, controls requiring those
choices remain disabled or unavailable rather than guessed.

## 10. Executable scenario mapping

The complete scenario and later-test mapping is
[`../dossiers/0033-04-ux-scenarios.md`](../dossiers/0033-04-ux-scenarios.md).
`_src/tests/test_review_request_ux_contract.py` verifies this candidate remains
complete, unapproved, type-safe, byte-bound, migration-safe, and traceable; it
does not test a production browser or transport.
