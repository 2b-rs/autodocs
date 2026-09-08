# 0033-04 — review-request record-page UX contract (Class R candidate)

**Class:** R (reconstructed proposal). Not operative. Not `docs/pipeline/`
content. May only become Class O through `0033-04.01` approval.

**Status:** review-ready, unapproved, awaiting `0033-04.01`.

**Task:** `0033-04`. **Chain:** `chain-0033-chakotay`.

**Base pin:** `main@3736170586e85047ab68691f0596689610688d9c`.

**Inputs:** `0033-02` process candidate
(`docs/dossiers/0033-02-process-reconciliation.md`, REF `99fdc4a2b`) and
`0033-03` package/envelope candidate
(`docs/dossiers/0033-03-schema-reconciliation.md`, REF `f6af48701`), both this
branch.

**Baseline findings addressed:** `RRB-UX-001`, `RRB-IDENT-001`,
`RRB-NOJS-001`.

**Informed by (Class E, cited only, never merged):** historical substantive
commit `d0eca203e3` (`docs/pipeline/review-request-ux.md` at that ref). Fresh
reconstruction: scenario set, field model, and confirmation-model wording
below are re-derived from the baseline findings and the current `0033-04`
acceptance criteria, not copied.

**Explicitly not reinstated:** the historical `0033-04:0033-03.01`
prerequisite edge. `0033-03.01` does not exist on the current baseline; this
candidate is built only on `0033-02` and `0033-03` output, per architect
scope review §3.1.

---

## 1. Eligible surfaces and action placement

The "flag for review" action is offered only on eligible record/page kinds as
defined by `0033-02` §3 (never on `invalid/*` pages, never on chrome/nav/
search, never where no `target_canonical_id` resolves). On an eligible page,
the action is placed as a persistent, keyboard-reachable control near the page
title/breadcrumb — not buried in a footer — with wording that names the
specific page kind ("Report an issue with this class page"), not a generic
"Feedback" label. Internal/report contexts (dashboards, `docs/pipeline/`
tooling output) get a separately specified, differently worded control that
is never rendered on public pages.

## 2. Field model

| Field | Required | User-typed or derived | Notes |
|---|---|---|---|
| `category` | yes | user-selected from closed enum (`factual-error`, `outdated-content`, `broken-link`, `accessibility`, `other`) | matches `0033-03`'s `category` enum exactly |
| `rationale` | yes | free text, max 2000 chars | matches `0033-03`'s `rationale` field |
| `evidence_url` | no | one optional validated link field | client-side scheme/shape validation only; authoritative allowlist enforcement is `0033-06`'s |
| evidence kind | derived | never user-typed | the UI infers "link" vs "no evidence" from whether the URL field is filled; it does not ask the user to classify their own evidence |
| `target_canonical_id` | — | always derived from the current page, never editable | immutable target/status/source disclosure (§3) |

This directly closes `RRB-UX-001`'s "no implementable post-ingestion feedback
channel" and gives the UI exactly one optional evidence field plus one
optional free-text line, as `0033-04`'s acceptance criteria require, with
internal kind derived rather than user-typed.

## 3. Immutable target/status/source disclosure

Before submission, the UI always shows, read-only: the exact
`target_canonical_id` being flagged, the page's current published status
(e.g. "published", not derivable staleness claims), and the source language/
variant of the page the user is on. None of these three are ever editable by
the submitter — they are stamped from the page context, not typed.

## 4. Confirmation model

One confirmation step, shown before submission, that:

1. displays the **exact** client-controlled payload that will later be
   exported/submitted — the literal `category`, `rationale`, and
   `evidence_url` the user entered, not a paraphrase;
2. treats any prefilled no-JavaScript target context (query-string-carried
   target identifiers) as an **untrusted claim** unless it is protected by an
   approved tamper-evident token — closing `RRB-NOJS-001`'s "static no-JS URL
   could not mint required per-request metadata" gap by requiring the token,
   not by trusting the URL;
3. defines signed-out behavior explicitly: a signed-out user may still submit
   (the process candidate `0033-02` §2 item allows anonymous submission); a
   signed-in GitHub user submits through the trusted envelope path instead of
   local-only JSON export;
4. discloses, in the same confirmation view, which authoritative envelope
   fields (e.g. `event_id` minted server-side on ingestion, `concern_key`) do
   **not exist yet** at confirmation time and will only appear after GitHub
   submission or ingestion — those fields are visibly absent/greyed, never
   fabricated client-side and shown as if authoritative.

## 5. Outcome states and feedback channels

| State | Meaning | Feedback shown |
|---|---|---|
| `local-only` | drafted, not yet submitted | "Saved locally. Not yet submitted." with an explicit clear-local-data control |
| `exported` | user downloaded a JSON package for manual/authenticated GitHub submission | "Exported. Submit the downloaded file via GitHub to continue." |
| `submitted with receipt` | trusted transport accepted the submission | shows the `event_id`-derived receipt/status link |
| `ingested/queued` | ingestion adapter validated and queued the request | "Received. Under review." with the same receipt link |
| `duplicate` | `0033-03`'s duplicate policy classified this as `superseded` | "A request for this issue is already open." linking the active request |
| `stale/rejected` | target changed before decision, or curator declined | exact terminal wording per `0033-02` §4.1/§4.3; never implies a factual change was made |
| `transport-failure` | submission attempt failed in transit | retry affordance, explicit "not yet received" wording, never a false success |
| governed outcome (`applied`) | curator accepted and applied | "Reviewed and updated." with no implication that the submitter caused the edit unilaterally |

## 6. localStorage reuse (`review.js` / `ara-review-package-v1`)

Review-request drafts reuse the existing `review.js` /
`ara-review-package-v1` localStorage collection rather than introducing a
second unconnected local store, with explicit discrimination:

- a stored item's `kind` field distinguishes a decision item (existing
  curation review) from a request item (this feature) — never inferred from
  shape;
- **migration:** an existing collection with no `kind` field is treated as
  all-decision-items (the pre-existing shape) and left untouched; new request
  items always carry `kind`;
- **removal:** a submitted/exported request item is removed from local
  storage only after the corresponding remote state (receipt or export
  acknowledgment) is confirmed, never optimistically;
- **clear-local-data:** a single control clears only request-kind items,
  never decision items, from the shared collection;
- **multi-tab/concurrent-update:** writes use the existing collection's
  read-modify-write-with-storage-event-reconciliation pattern; a request item
  is keyed by its local draft ID so two tabs editing the same draft converge
  rather than overwrite silently;
- **delayed-submit staleness:** a draft older than the `0033-02` §6 30-day
  local-draft clock is flagged stale in the UI before submission, prompting
  re-confirmation of target/source rather than silent resubmission;
- **quota/privacy limits:** the shared collection's existing quota handling
  applies unchanged; request items do not get a separate quota;
- **one package builder:** direct submission and collected/delayed submission
  share exactly one package-builder function that produces the canonical
  `review-request-package@v2` object from either input path, so the two
  paths cannot diverge in shape.

## 7. Accessibility and no-JavaScript

- **Keyboard activation:** the "flag for review" control and the confirmation
  dialog are fully operable via keyboard (Enter/Space activation, Tab order
  matching visual order).
- **Unique dialog naming:** the confirmation dialog has a unique
  `aria-labelledby` per invocation (includes the target ID), so assistive
  tech announces which page is being flagged when multiple tabs are open.
- **Focus trap/restoration:** focus is trapped within the open dialog and
  restored to the triggering control on close (cancel or submit).
- **Error and live-region behavior:** validation errors (e.g. malformed
  `evidence_url`) are announced via an `aria-live="polite"` region adjacent
  to the field, not only as a color change.
- **Visible focus:** every interactive element in the flow has a visible
  focus indicator meeting the corpus's existing contrast requirements.
- **Cancellation:** cancel at any point before submission discards the
  in-progress draft without side effects (no partial local write).
- **Mobile breakpoints:** the flow uses the corpus's existing named
  breakpoints; the confirmation dialog becomes a full-screen sheet below the
  existing `mobile` breakpoint rather than a fixed-width modal.
- **No-JavaScript flow:** a no-JS user reaches a GitHub-Issue-template-backed
  intake path. The template prefills `target_canonical_id` and `category` via
  query parameters, but — per §4 item 2 — this prefill is treated as an
  untrusted claim; the trusted ingestion adapter derives the authoritative
  request metadata from the resulting Issue envelope (title/body/labels) at
  ingestion time, never from the query string alone.

## 8. Executable scenario map

Every scenario below maps to a proposed later automated test (owned by the
Campaign B/C implementation Tasks, not authored here):

| Scenario | Outcome state exercised | Proposed test owner |
|---|---|---|
| valid-curated (eligible page, valid category+rationale, no evidence) | `submitted with receipt` → `ingested/queued` | `0033-10`, `0033-11` |
| duplicate-before-open (same concern already `open`) | `duplicate` | `0033-07` |
| duplicate race (two submissions same concern, concurrent) | one `open`, one `duplicate` | `0033-07` |
| stale-at-ingest (target changed between confirm and ingest) | `stale/rejected` | `0033-05`, `0033-11` |
| JSON export (unauthenticated, manual GitHub submission later) | `exported` → later `submitted with receipt` | `0033-10` |
| GitHub receipt (authenticated webhook path) | `submitted with receipt` | `0033-06`, `0033-11` |
| authenticated-user JSON downgrade (signed-in user chooses export instead of direct submit) | `exported`, envelope fields explicitly absent (§4 item 4) | `0033-10` |
| signed-out/no-JS success | `ingested/queued` via Issue template | `0033-06`, `0033-11` |
| signed-out/no-JS failure (malformed Issue body) | `transport-failure`, actionable message | `0033-06` |
| retry (transport-failure then resubmit) | same `event_id` reused; idempotent per `0033-03` §3 | `0033-11` |
| cancel | draft discarded, no local write | `0033-04` scenario only, no server involvement |
| desktop/mobile layout | dialog vs. full-screen sheet (§7) | `0033-12` |
| keyboard/focus | trap/restore/announce (§7) | `0033-12` |
| post-ingestion traceability | receipt link resolves to current request state | `0033-07`, `0033-11` |

## 9. Open UX decisions explicit for `0033-04.01`

- exact wording of the eligible-page action label per page kind;
- exact 30-day local-draft staleness threshold (inherits `0033-02` §6, subject
  to that Task's own approval);
- exact mobile breakpoint name and full-screen-sheet visual spec;
- whether `evidence_url` client-side validation additionally warns (not
  blocks) on a scheme the allowlist is likely to reject, ahead of `0033-06`'s
  authoritative check.

## 10. Requirement-to-artifact matrix

| `0033-04` acceptance criterion (from `TODO.md`) | Section |
|---|---|
| action placement/wording for eligible pages + internal/report contexts | §1 |
| exact required/optional fields, evidence UI, derived-not-typed evidence kind | §2 |
| immutable target/status/source disclosure | §3 |
| privacy/consent and public-GitHub disclosure | `0033-02` §2 item 10, referenced from §4 |
| confirmation model: exact payload, untrusted no-JS prefill, signed-out/login, envelope-field disclosure | §4 |
| outcome states with feedback channels; retry/edit identity | §5 |
| `review.js`/`ara-review-package-v1` reuse, kind discrimination, migration, removal, clear-local-data, multi-tab, staleness, quota, one package builder | §6 |
| keyboard/dialog naming/focus/live-region/visible-focus/cancellation/mobile/no-JS flow | §7 |
| executable scenario map to proposed tests | §8 |

## 11. Scope statement

This dossier is the entire Class R deliverable for `0033-04`. It does not
write to `docs/pipeline/**`; landing it there is `0033-04.01`'s and a later
Task's act.

## 12. Validation performed

- Manual cross-check: every `0033-04` acceptance-criterion clause in current
  `TODO.md` (line 1739–1743) maps to a section above (§10 matrix).
- Manual cross-check: no scenario in §8 implies a factual record mutation
  from any state other than curator `applied` (consistent with `0033-02`
  §2/§4.3).
- `git diff --name-only main...chain-0033-chakotay` (checked after this
  commit): no path under `docs/pipeline/**` or any governance file.
- Not run: `_src/validate.py` (no generated-tree source changed by this
  Task); this dossier defines no runtime code.

## 13. Provenance

Requested by dispatch briefing (Dispatcher `chakotay`, atomic AWARD
`1787970210735-b3950909`, thread `0033-chain`), executed under claim
`TODO-Chakotay-Paris-0033-chain-20260830T113000Z.md`,
owner_token `agent:chakotay-paris:0033-chain:20260830T113000Z`. Authored
2026-08-30 against `main@3736170586e85047ab68691f0596689610688d9c`.
