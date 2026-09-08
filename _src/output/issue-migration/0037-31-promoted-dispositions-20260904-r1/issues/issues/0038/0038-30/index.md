---
schema_version: "1.0"
id: "0038-30"
level: "task"
parent: "0038"
state: "open"
visibility: "internal"
prerequisites:
  - "0038-16.01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1845"
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

PREREQ: 0038-30:0038-16.01 Narrow the legacy handoff manifest's activation precondition from "registry exists" to "queue is live". REF: `f6789e512`.

## Scope

- **Context (found 2026-08-22 by `Seven`, flagged not hidden):** Implementing `0037-46.01` required creating `_src/runner/` — that directory is inside that Task's own declared write scope. `_src/tools/legacy_handoff_manifest.py` treats the mere existence of `_src/runner` as "queue active" and therefore raises finding `LHM035`, while the manifest's own text still states — correctly, for now — that the queue is not active. Rerunning `_src/tests/test_legacy_handoff_manifest.py` shows 2 of 34 tests failing (`test_verdict_is_pass` plus one report assertion). This is the transition `0038-16.01`'s manifest itself predicted would occur once `0037-46.01` landed: a stale precondition in the checker, not a defect in `0037-46.01`'s work.
  - **Why it is a separate Task:** `_src/tools/legacy_handoff_manifest.py` and `docs/pipeline/legacy-handoff-manifest-v1.json` were outside `0037-46.01`'s write scope. `Seven` correctly did not edit them and did not mark the finding `[u]`: narrowing one checker's precondition is agentically determinable from the manifest's own text and needs no human decision — it needs someone with write scope there.
  - **Urgency:** low **while `0037-46.01` is unmerged**. Branch `0037-46.01` is at rest and `main` is unaffected, so nothing is broken today. It becomes blocking the moment `0037-46.01` integrates, because the manifest gate would then fail on `main` for a reason that is not a real regression.
  - **Integration review: mandatory.** **Rationale (provisional — conservative default, not an architect decision):** the contract offers only *mandatory* or an architect **no-checkpoint justification**, and only an architect may record the latter. Set by Projektleiter `kathryn`, who does not set checkpoints. **Explicit downgrade recommendation for the architect:** this Task narrows one checker's precondition to match a text that already exists; it grants no authority, touches no irreversible migration, external effect, credential boundary or public release, and its failure mode is a visible failing gate rather than a silent pass. It is a strong candidate for a recorded no-checkpoint justification — but that judgement is the architect's, not the Projektleitung's, at the latest at Feature `0038` closure.
    - **Architect checkpoint decision (2026-08-24, Architect `seven`, Seven of Nine; recorded per `process-roles.md` §Architect and the `AGENTS.md` checkpoint contract):** **confirmed — mandatory; the downgrade recommendation is declined.** The recommendation weighed only the too-wide direction, whose failure is a visible failing gate. The consequential direction is the narrowing itself misclassifying "live": then `LHM035` stays silent at the protocol switch — the precise moment `0037-46.02` relies on it firing (see that node's BEFUND 3) — a silent pass on the activation path of a hard-to-reverse migration. The checkpoint was exercised and passed (REF `f6789e512`) and stands.
  - **Acceptance:** ✓ (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `tobias.anton (0038-30-Commit)` und vom Architekten `seven`). Mandatory Integrationscheckpoint **bestanden**. Abgenommene Baseline `f6789e512f90056764d63fea335fe13db2c73c26`; kein Merge nötig (REF war bereits vor Beginn dieser Prüfung Vorfahre von `main`). Prerequisite-closed Batch aller 17 induzierten Knoten vollständig abgenommen (siehe deren jeweilige Acceptance-Zeilen); ein echter Befund (`0038-05.01`) gefunden, korrigiert (Branch `0038-05.01-correction`, Tip `8ddc0fffa0823e9d598f122779c59b8a870584e1`, auf `main` integriert) und erneut geprüft, nicht stillschweigend übergangen. Eigene Verifikation: 41/41 Tests (34 vorbestehend + 7 neue Fixtures, alle sechs von der Acceptance criteria geforderten Positiv-/Negativfälle namentlich vorhanden); Korrekturlogik selbst gelesen — unterscheidet sauber Laufzeit-Wurzel/Live-Selector-Protokollsprung (Liveness) von der Typed-Action-Registry (niemals ein Signal), begründet aus dem Manifesttext selbst statt erfunden; py_compile sauber; automation_safety PASS 0 Funde; Live-Checker PASS gegen den aktuellen Baum. Review-REF `a995f9047`, vollständiger Record `docs/campaign-evidence/review-0038-30-belanna-20260825/checkpoint-review.md` auf Branch `acceptance-0038-30-batch-belanna-20260825`. Kein stiller Fix durch die Integratorin an irgendeinem Punkt dieser Kette.

## Acceptance criteria

- **AC-001** The activation precondition distinguishes "a typed-action registry exists on disk" from "the queue is live and dispatching", and `LHM035` fires only for the latter
- **AC-002** the distinguishing signal is named and justified against the manifest's own definition of activation rather than invented. `_src/tests/test_legacy_handoff_manifest.py` passes in full, with an added test that a present-but-inactive `_src/runner/` does not trip the finding, and one that a genuinely active queue still does. The manifest text and the checker agree afterwards
- **AC-003** if the manifest text is what is wrong, that is corrected instead — with the reason recorded

## Definition of Done

Committed with the tests above green (real numbers reported, not asserted); no weakening of any other `legacy_handoff_manifest` finding; the relationship to `0037-46.01`/`0037-46.02` is documented so the next person does not re-diagnose it. If `0037-46.01` has already integrated when this is picked up, verify against `main` rather than the branch.
