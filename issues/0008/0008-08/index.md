---
schema_version: "1.0"
id: "0008-08"
level: "task"
parent: "0008"
state: "closed"
visibility: "internal"
prerequisites:
  - "0008-01"
  - "0008-04"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:276"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0008-08:0008-01, 0008-08:0008-04 — fix a second, distinct recurrence of the 0008-01 bug class: the client-side `review.js` (`renderPageNotice()`) unconditionally overwrote `#page-review-title` with a hardcoded German template ("%d API-Element%s mit Review-Bedarf") on every language page at runtime, after page load — invisible to 0008-04's `check_no_hardcoded_german()` because that check only scans generated static HTML, not JS-mutated DOM state (found 2026-08-14 via nl screenshot, `ara::log` namespace page, same page as the original 0008-01/0008-02 reports) -- DONE 2026-08-14: added a `pageReviewTitle` template key (with `%n`/`%s` placeholders) to `review.js`'s `L` translation dictionary for all languages, including a brand-new `nl` block that was entirely missing from `L` (so Dutch pages were also missing every other dynamic review-UI string, not just this title); added a `formatPageReviewTitle(open)` helper and pointed the call site at it instead of the hardcoded string. Verified via `run.sh` (exit 0): all 11 language blocks now carry `pageReviewTitle`, the hardcoded German string is gone from the call site, and `node --check review.js` passes. REMAINING GAP (not yet fixed, tracked as new task 0008-09 below): `check_no_hardcoded_german()` needs to be extended to also cover client-side-rendered/JS-mutated strings (e.g. via a headless-browser DOM snapshot per language, not just static-HTML grep), otherwise this bug class can recur a third time through any other JS file undetected. REF: 98b980dc

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
