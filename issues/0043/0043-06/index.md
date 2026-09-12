---
schema_version: "1.0"
id: "0043-06"
level: "task"
parent: "0043"
state: "open"
visibility: "internal"
prerequisites:
  - "0043-02"
  - "0043-05"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:731"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0043-06:0043-02, 0043-06:0043-05 Document the ASPICE evidence map for the report landscape. **Implementierung abgeschlossen (2026-08-22):** Dispatcher `seven`, owner_token `agent:seven:0043-06:20260822T190021Z`. REF `be0f82281` (substanziell), Branch-Tip/Buchhaltung `ace9066dd`, Claim `abe7a9098`, Vorleistungs-Merge `5c20c6883` (`0043-05`). Neu: `docs/pipeline/aspice-report-evidence-map.md` — bildet die fuenf `0043-05`-Berichtsseiten und das `0043-02`-Build-Ledger auf die ASPICE-Prozessergebnisse ab, die sie belegen koennten, benennt je Zeile, was einem Assessor zu zeigen ist, **und die ehrlichen Luecken** — darunter, dass rohe Kombinationsberichte und Run-Archive-Logs nach `DEC-0043-001` bewusst git-ignoriert und damit selbst nicht konfigurationsverwaltet sind. Verweist auf die in `process-roles.md` bereits aufgezeichnete SWE.4/SWE.6/SYS.5-Luecke bei unabhaengigen Reviewern, statt sie zu wiederholen. **Kein Capability-Level-Anspruch** an irgendeiner Stelle, passend zur Disclaimer-Fuehrung von `aspice-level1-score-import.md` und den Wortlautgrenzen aus `0011-03`/`0019-10`. Verlinkt aus `docs/pipeline/README.md`; jedes interne Linkziel vor dem Commit als existierende Datei geprueft. Kein Checkpoint gekreuzt (Architekten-No-Checkpoint-Begruendung, Wiedervorlage `0043-07`). **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `agent:seven:0043-06:20260822T190021Z`). Abgenommen als Teil der durch Checkpoint `0043-07` induzierten prerequisite-closed Batch; Review-REF `218ca607d` (`review-0043-07-belanna-20260824T163500Z`, Feature-Floor-Review §8): Evidenzkarte vorhanden und aus `docs/pipeline/README.md` verlinkt, kein Capability-Level-Anspruch, Lücken ehrlich benannt, kein gebrochenes internes Linkziel.

## Scope

- **Claimed (2026-08-22T19:00:21Z, `agent:seven:0043-06:20260822T190021Z`, Dispatcher Seven, unprivileged):** Both prerequisites `[x]`. `0043-02` already an ancestor of `main`; `0043-05` (tip `c897899c4`) merged in directly (`5c20c6883`). Claim: `TODO-Seven-0043-06-20260822T190021Z.md`.
  - **Requirements covered:** `RQ-BR-07`.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** documentation whose honesty constraints are themselves acceptance criteria; reviewed at `0043-07`.
  - **Implementation completion (2026-08-22, Dispatcher `Seven`, unprivileged):** REF `be0f82281` on branch `0043-06` (based off `main` at `64b53c7b3`; prerequisite branch `0043-05`, tip `c897899c4`, merged in directly since not yet on `main` — one TODO.md conflict, resolved by hand, single duplicate-content hunk). New `docs/pipeline/aspice-report-evidence-map.md`: maps `build-ledger.jsonl` (SUP.8-adjacent CM/baselines), `build-reports.html` (MAN.3-adjacent status reporting), `curation-report.html`/`open-reviews.html`/`traceability.html`/`extraction-reports.html` (SWE.6-adjacent verification/consistency evidence) to the process outcomes they could evidence, names what an assessor should be shown per row, and states the honest gaps per row (git-ignored raw evidence under `output/` per `DEC-0043-001`, point-in-time traceability snapshot, no independent-reviewer requirement in the curation schema — cross-referenced to `process-roles.md`'s own recorded SWE.4/SWE.6/SYS.5 gap rather than restated). No capability-level claim anywhere in the document; carries the same disclaimer framing as `aspice-level1-score-import.md`. Linked from `docs/pipeline/README.md`. **Validation:** every internal link target verified to exist as a file before commit; no report-generator code, no other `docs/pipeline/` file, and no capability-level wording touched. **Not done, deliberately:** no PAM capability rating, no independence claim between producers and reviewers, no coverage of report types outside the five `0043-05` pages plus the `0043-02` ledger (other types remain cataloged only in `reports.md`). Claim `TODO-Seven-0043-06-20260822T190021Z.md` travels on the branch.

## Acceptance criteria

- **AC-001** A `docs/pipeline/` document maps each report page and the ledger to the ASPICE process outcome it evidences (at minimum SUP.8 baselines/CM for the ledger, MAN.3 status reporting, SWE.6-adjacent verification evidence), states what an assessor should be shown for each claim, and names the known gaps honestly (e.g. evidence that remains git-ignored by design) rather than overclaiming

## Definition of Done

Committed and linked from `docs/pipeline/README.md`; no capability-level claim is made (consistent with the `0011-03`/`0019-10` wording constraints).
