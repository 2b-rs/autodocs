# Record-Page "Flag for Review" UX Contract (0021-04)

Status: drafted for **0021-04**. PREREQ: 0021-01 (process/roles), 0021-02
(package schema). Normative for `0021-05` (browser implementation) and
`0021-06` (history/report rendering).

## Scope and non-goal

This is the **interaction contract**, not the implementation. It defines
what must be true of the UI; `0021-05` decides markup/CSS/JS structure to
satisfy it. Nothing here authorizes any script to write to a record
(0021-01 non-bypass rule 1).

## Action placement

| Record status | Placement | Label |
|---|---|---|
| `valid/*` (any curated variant) | Secondary action, below the primary content, near existing provenance/history links — never adjacent to the record's main value display, to avoid implying the value itself is in question. | "Flag for review" |
| `invalid/*` (`to-be-confirmed`, `hypothesized`, `obsolete`) | Same placement, but label changes to reflect the record is already under active curation. | "Add supporting evidence" (routes through the same schema/ingestion path; `category` defaults are adjusted, not the transport). |
| Records with an already-**open** review-request (per `0021-06` history surfacing) | Action is replaced by a disabled/informational state linking to the existing open request — never a second active button, since duplicate detection would reject it anyway (0021-02 Duplicate rule) and a hard rejection after a full submission flow is a worse experience than preventing it. |

## Form fields (maps 1:1 onto `review-request-package@v1`, `review-request-package-schema.md`)

| Field | UI requirement |
|---|---|
| `category` | Required. Single-select, all 5 enum values shown, no default pre-selected (forces a deliberate choice). |
| `rationale` | Required. Multi-line text, non-empty enforced client-side before submit is enabled; minimum is "non-whitespace," no arbitrary length floor is imposed on the requester. |
| `evidence_refs` | Optional. Repeatable rows of (kind, value, note); a "Add another reference" control; zero rows is valid. |
| `target_canonical_id`, `target_version_id`, `target_content_hash`, `target_status_snapshot`, `source_url` | **Never user-entered.** Bound automatically from the rendered page's own data at open-dialog time (0021-05 concern), but the UX contract requires all five to be **visibly disclosed** to the requester before submit — e.g. "You are flagging: *TSync User Guide*, version R25-11, currently Curator-decided" — so a requester never submits blind against a record they didn't intend. |
| `actor_claim` | Two paths, see Consent/trust disclosure below. |

## Current record/version/status disclosure

The dialog must show, read-only, before any input field: the record's
title/canonical id, current status badge (using the same status vocabulary
as the public page, not raw `status.state` enum strings), and version/release
id if one exists. This satisfies the acceptance criterion literally and
doubles as the visible anchor a screen-reader user can associate with the
form region (`aria-describedby`).

## Consent and trust disclosure

Reuses `review.js`'s existing two-path identity pattern verbatim rather than
inventing a new one:

- **GitHub-authenticated path**: "Signed in as %s via GitHub" — matches
  `idAuthNote` in `review.js`. Selecting this path is what allows
  `trust.identity_kind = "github_authenticated"` once ingested
  (`review-request-package-schema.md`, Two distinct identities).
- **Self-declared path**: name/handle entry plus the existing warning text
  pattern (`review.js`'s `warn` string, adapted): "This request will be
  recorded as self-declared and carries lower trust; the Kurator may weigh
  it accordingly." Shown **before** submit, not after, so it is informed
  consent rather than a post-hoc disclaimer.
- Neither path is hidden behind a default; the requester must pick one
  explicitly, mirroring `review.js`'s existing identity-gate pattern.

## Confirmation behavior

Submit is a two-step interaction: (1) a review screen restating record
identity + category + rationale + evidence + chosen identity path, with an
explicit secondary "Edit" action, then (2) the actual submit. This mirrors
`review.js`'s package-drawer pattern (collect, then submit as a distinct
step) and gives the no-JavaScript fallback a natural two-page-load
equivalent (see below).

## Success / error / stale states

| State | UI requirement |
|---|---|
| `exported` (JSON download offered) | Labeled explicitly as "Downloaded — not yet submitted." Never uses success styling; this is a hand-off, not a completion (0021-05 acceptance criterion: exported must never look submitted/queued). |
| `submitted` (GitHub issue created) | "Submitted as GitHub issue #%n — awaiting review." Shows only the transport receipt (issue link); explicitly does **not** claim queued/ingested state, since ingestion is a separate, later, trusted step (0021-01 lifecycle). |
| `stale` (page's local record state no longer matches what the user is about to submit against — detectable client-side only via a soft page-age check, hard staleness is server-side per `review-request-package-schema.md`) | Non-blocking warning banner in the dialog: "This page may be out of date. Reload before submitting to avoid a rejected request." Does not block submit — hard staleness is authoritatively decided at ingestion, per the Staleness rule; the client can only warn, never authoritatively reject. |
| `duplicate` (surfaced pre-submit per Action placement, or post-submit if a race occurred) | "A review request for this record is already open." Links to the existing request's public reference if available (0021-06 concern); never presented as an error the user caused. |
| submission failure (network/transport error) | Inline, non-dismissive-by-timeout error adjacent to the submit control; preserves all entered field values (no data loss on retry). |

Terminology rule (acceptance criterion, verbatim requirement): every one of
the above states' copy must avoid words like "changed"/"updated"/"corrected"
for the record itself — only the *request* is created/submitted/queued, the
*record* is untouched until a Kurator decision, per `0021-01`'s `valid/*`
re-review rule.

## Keyboard operation and focus management

- The trigger control is a real `<button>` (or `<a>` with `role="button"`
  plus keydown handling), reachable via Tab in normal document order.
- Opening the dialog moves focus to the dialog's first focusable element
  (the category select) and traps focus within the dialog (Escape closes
  and returns focus to the trigger) — standard modal dialog pattern,
  consistent with `review.js`'s existing panel/drawer components.
- The two-step confirmation screen (see Confirmation behavior) moves focus
  to its own heading on transition, so screen-reader users get an
  announced state change rather than a silent DOM swap.
- All error states (see Success/error/stale) move focus to the first
  invalid field or the error banner, not left at the submit button.

## Mobile layout

Dialog becomes a full-viewport sheet below a defined breakpoint (matching
existing responsive breakpoints used by `review.js`'s drawer, not a new
breakpoint); the two-step confirmation screen and the record
identity/status disclosure block remain visible without requiring a
separate scroll-and-recall step — i.e. the record identity banner persists
(sticky or repeated) rather than scrolling out of view before submit.

## No-JavaScript fallback

Mirrors `review.js`'s existing fallback split (`ghSkip`: "export without a
token"): with JavaScript disabled, the record page instead links directly
to a pre-filled GitHub "New Issue" URL (query-string template, same
approach GitHub issue templates use) containing the identity-disclosed
fields the user can still fill in manually in GitHub's own UI; there is no
client-side schema validation in this path, so the ingestion boundary's
server-side validation (`0021-03`) is the only enforcement point.
Fallback confirmation is GitHub's own "Issue submitted" page — explicitly
not re-implemented, since duplicating it would risk making an
unauthoritative page claim ingestion state.

## Testable acceptance scenarios (Definition of Done)

1. **Standard**: `valid/*` record, no open request — action visible, full flow to `submitted`.
2. **Valid-curated**: `valid/curator-decided` record — same flow; disclosure banner correctly shows "Curator-decided" status.
3. **Stale**: page loaded, record changes server-side before submit — client shows non-blocking stale warning; ingestion (0021-03) authoritatively rejects if hard-stale.
4. **Duplicate**: record already has an open request — action replaced by informational link state; no dialog opens.
5. **Submission-failure**: transport/network failure on submit — inline error shown, fields preserved, retry succeeds without re-entry.

## Traceability

Satisfies 0021-04's acceptance criteria and Definition of Done by defining
action placement (valid/non-valid), required fields, disclosure, consent,
confirmation, all named states, keyboard/focus, mobile, and no-JS fallback
in one authoritative document, plus the five required testable scenarios
above. Consistent with `review.js`'s existing identity/consent UI and with
`review-request-package-schema.md` (0021-02) and `website-review-flag.md`
(0021-01).
