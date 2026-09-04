---
schema_version: "1.0"
id: "0038-31"
level: "task"
parent: "0038"
state: "closed"
visibility: "internal"
prerequisites:
  - "0038-14"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1826"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0038-31:0038-14 Stop `automation_safety.py` from silently double-counting a moved finding on an uncommitted tree. REF: `94bab196df7786f57e97994dd73f822cb50556e0`; candidate tip `7ab79af32ec3d1fd83964049b773cad9e8c077e4`. Claims: `TODO-Kathryn-Neelix-0038-31-20260822T144500Z.md`, `TODO-Harry-Dax-0038-31-20260822T183800Z.md`. Prior review `0db2a4fd9de266519c3aea75845256588126f137` remains append-only `rejected`; corrective independent re-review `61d3e486bd14defff03711bc009ba236c23ad68a` is `accepted`.

## Scope

- **Context (found 2026-08-22, `Kathryn-Chakotay-20260822T124000Z`; independently reproduced by privileged integrator `Kathryn-Kolos-20260822T115500Z` during the `0038-29` checkpoint review):** Run against a working tree whose files differ from the index, `_src/tools/automation_safety.py` reports the same physical code site twice. Measured on the same commit: clean tree `findings 73 / advisory 38`, one `AUTO010` at `:491`; dirty tree `findings 74 / advisory 39`, `AUTO010` at **both** `:491` and `:494` with an **identical** `evidence_sha256` (`ba10f4fccc3b…`). Diagnosed cause: `_read_tracked_sources()` (`_src/tools/automation_safety.py:2649`) scans the index version **and** the worktree version when they differ, while `_dedupe()` keys on the line number — so one finding that merely moved lines survives deduplication as two.
  - **Why it matters more than the count suggests:** these are exactly the numbers agents copy into completion evidence. Task `0038-29` was **rejected** at its integration checkpoint for a completion-evidence statement that did not match the gate's actual output; a gate that silently reports a different number depending on whether the tree happens to be committed makes that failure mode easy to walk into honestly. The error direction is inflation, not concealment — it hides nothing — but a number that changes with an irrelevant condition cannot serve as evidence.
  - **Integration review: mandatory.** **Rationale (provisional — conservative default, not an architect decision):** `automation_safety.py` is a gate other Tasks are measured against, and this change touches how findings are counted; a mistake here can suppress a finding rather than merely duplicate one, which is the opposite and far worse error direction. Set by Projektleiter `kathryn`, who does not set checkpoints. **Downgrade note for the architect:** if the fix turns out to be confined to the deduplication key with no reachable path to dropping a finding, this is a plausible candidate for a recorded no-checkpoint justification — that judgement is the architect's, at the latest at Feature `0038` closure.
    - **Architect checkpoint decision (2026-08-24, Architect `seven`, Seven of Nine; recorded per `process-roles.md` §Architect and the `AGENTS.md` checkpoint contract):** **confirmed — mandatory; downgrade declined on evidence.** The offered downgrade condition — "confined to the deduplication key with no reachable path to dropping a finding" — was empirically refuted by this very node's history: the round-1 review found the new deduplication *did* drop a real finding on a line-number collision, the exact reachable path the condition postulated away, and it was closed only by 10,000 property cases at re-review. The checkpoint demonstrably earned its keep here.
  - **Integration re-review (2026-08-22, `Data-Geordi-20260822T203511Z`, privileged Integrator, independent of dispatcher Data and implementer `Harry-Dax-20260822T183800Z`):** verdict `accepted` against exact candidate `7ab79af32ec3d1fd83964049b773cad9e8c077e4`. Independently proved the prior F1 red before green (old 1, corrected 2), tested required neighbors plus two simultaneous collision groups (old 2, corrected 4), and ran 10,000 deterministic multiplicity/line-collision property cases. Focused 14/14 passed; full module 135 tests with only the byte-proven pre-existing `0038-33` failure; live gate `PASS` with 73 findings / 38 advisory / 24 disposed critical / 0 unresolved / 0 policy errors; clean old/new finding-identity set unchanged. Report: `docs/campaign-evidence/review-0038-31-20260822-data-geordi/report.md`, Review REF `61d3e486bd14defff03711bc009ba236c23ad68a`.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `Data-Geordi-20260822T203511Z` (Geordi persona, privileged Integrator)
    - **Authority reference:** `dispatch:Data→Data-Geordi-20260822T203511Z:0038-31-re-review:20260822T203511Z`; verbatim briefing recorded under `DEC-0044-013` in the review report.
    - **Accepted at:** `2026-08-22T20:57:31Z`
    - **Accepted baseline:** `7ab79af32ec3d1fd83964049b773cad9e8c077e4` (substantive `94bab196df7786f57e97994dd73f822cb50556e0`)
    - **Contract SHA-256:** `5333dc95dfb6b48dc4b9e1968506f10fb9d03dff860ee1c9caaa03ea96b72067`
    - **Work-product manifest SHA-256:** `3b280ec5e9b2072e153355f1004c850bfb455b228028f427cfa56f8bd6d36e74`
    - **Prerequisite-acceptance SHA-256:** `70d563a79cfe6134a8cbefd7d6819d5f1fbf2a8c5914dd886d877589785a2d8d`
    - **Review REF:** `61d3e486bd14defff03711bc009ba236c23ad68a`

## Acceptance criteria

- **AC-001** A finding that exists once in the code is reported once, regardless of whether the working tree matches the index. The deduplication key no longer relies on the line number alone for this case
- **AC-002** `evidence_sha256` already identifies the finding across a line move and is the obvious anchor, but the chosen key is justified rather than assumed. Which source version the gate authoritatively measures — index, worktree, or both with an explicit distinction — is **decided and documented**, not left implicit: an agent reading the report must be able to tell what was actually scanned. A regression test reproduces the reported case (same code site, differing line numbers between index and worktree) and asserts a single finding
- **AC-003** it uses a hermetic fixture, not the live repository. No existing finding is lost, suppressed or re-classified by the fix, and the disposition mechanism is untouched

## Definition of Done

Committed with the regression test green and the full existing suite unchanged; the counts on a clean tree are unchanged from before the fix (stated with real numbers, measured, not asserted); the documented answer to "what does the gate scan" lands wherever `automation_safety.py` is described. If the investigation shows the diagnosis above is wrong, the true cause is recorded and this Task's text is corrected rather than quietly re-scoped.
