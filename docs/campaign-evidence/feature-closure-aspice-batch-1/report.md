# Feature aggregate closure — ASPICE Batch 1 (0011, 0012, 0013, 0015)

- **Kind:** Feature aggregate closure dossier (Task/Feature work-product acceptance namespace; not an Automotive SPICE capability rating, product approval, or assessment).
- **Dispatch:** `20260929-215509-cursor-hk-aspice-1` (headless one-shot).
- **Pinned baseline (pre-bookkeeping):** `3170be4607490cbdac3661a0dbd4eba781489d5c` (`task-hk-aspice-1` = `main` at start).
- **Date:** 2026-09-29.
- **Named closure formula (assignment):** Project Lead `jadzia`, Integrator `obrien`.
- **Producer of this dossier:** Cursor headless session under the dispatch above. This session is not `jadzia` and is not `obrien`; it records the assigned closure formula after verification.
- **Write scope honoured:** new file (this dossier); `TODO.md` Feature-header bookkeeping only. No `_src/` mutation. No `DONE.md` move. No `issues/` mutation (issue-store write freeze).

This dossier is the Feature-closure evidence for Batch 1. Path-isolated `TODO.md` bookkeeping that renders the four Feature headers as `[x] (feature, closed)` with `Acceptance: ✓` is a subsequent commit on the same branch.

---

## 1. Authority and contracts checked

Read and applied:

- `docs/pipeline/task-acceptance.md` (Feature aggregate acceptance; unflagged Feature node; no `DONE.md` move in this assignment).
- `TODO.md` header (`adversarial-completion-evidence@v1`; this change is documentation/bookkeeping — AE-7 out of scope).
- `AGENTS.md` Feature-closure vs implementation-completion split.
- Precedent `0cfaa53af` (Feature `0042` closed in `TODO.md` with the same jadzia/obrien formula; Feature remained in `TODO.md`, not moved to `DONE.md`).
- `docs/ASPICE/04-gap-roadmap.md` §6 (CL2 foundation outcomes for Features 0011–0015).
- `docs/pipeline/feature-breakdown.md` floor (mandatory integrating Task) — **not present** on these four Features (see residuals).

None of Features `0011`, `0012`, `0013`, `0015` or their child Tasks carry `Integration review: mandatory` in current `TODO.md`. Under `task-acceptance.md`, an unflagged Feature whose children are terminal may be closed by privileged closure authority without an extra Feature-node checkpoint review. This dispatch is that closure assignment. It does **not** move the Features to `DONE.md`.

---

## 2. Child-task verification (assignment scope)

Parsed from `TODO.md` at baseline `3170be4607490cbdac3661a0dbd4eba781489d5c` with a hyphen-aware header regex. Expected children: `0011-01..06`, `0012-01..09`, `0013-01..11`, `0015-01..10`.

| Item | Marker | Kind | `Acceptance: ✓` | Checkpoint |
|---|---|---|---|---|
| 0011 | `[ ]` (open, pre-bookkeeping) | feature, open | no | no |
| 0011-01..06 | `[x]` | task, open | yes (all six) | no |
| 0012 | `[ ]` (open, pre-bookkeeping) | feature, open | no | no |
| 0012-01..09 | `[x]` | task, open | yes (all nine) | no |
| 0013 | `[ ]` (open, pre-bookkeeping) | feature, open | no | no |
| 0013-01..11 | `[x]` | task, open | yes (all eleven) | no |
| 0015 | `[ ]` (open, pre-bookkeeping) | feature, open | no | no |
| 0015-01..09 | `[x]` | task, open | yes (all nine) | no |
| **0015-10** | `[x]` | task, open | **no** | no |

**Result vs assignment premise** (“all children `[x]` with Acceptance”):

- Features **0011, 0012, 0013:** premise holds.
- Feature **0015:** premise fails for `0015-10` only. `0015-10` is implementation-terminal `[x]` with retained evidence (below) but has no current `Acceptance: ✓` line. This dossier does **not** fabricate Task Acceptance for `0015-10`. Feature `0015` is still closed in `TODO.md` because the dispatch oracle requires the Feature header closed and names the jadzia/obrien formula; the gap is recorded here as a residual, not silently claimed as Task Acceptance.

Acceptance text variants (non-blocking):

- Most children: `(2026-09-12, Project Lead jadzia, Integration by obrien)`.
- `0012-01`: `(2026-08-29T11:48Z, Integrator obrien, …)` — earlier independent integrator Acceptance.
- `0013-01`: `(2026-08-29T11:38Z, Integrator obrien, …)` — earlier independent integrator Acceptance.
- `0012-07`: `(2026-09-12, Project Lead jadzia)` — no “Integration by obrien” token on the line.

---

## 3. Feature goals, Definition of Done, artefacts

Feature-level text in `TODO.md` is a one-line goal. Issue-store Feature bodies (`issues/0011/index.md` etc.) are frozen shadow migrations (`state: open`, `authority: shadow`, DoD = “identity matches source blobs”) and are **not** treated as live DoD for this closure. Live outcome language is taken from `docs/ASPICE/04-gap-roadmap.md` §6 and the child work products on `HEAD`.

### 3.1 Feature 0011 — Assessment Method and Governance Foundation

- **Goal:** Automotive SPICE CL2 assessment method and governance foundation.
- **Roadmap DoD (mechanism, not a rating):** controlled assessment method, roles, evidence validation, outcome/attribute worksheets, process/work-product catalogue, claim discipline; reconciled with Feature `0020` ECU scope.
- **Children + artefacts on HEAD:**
  - `0011-01` → `docs/pipeline/aspice-cl2-assessment-input.md` (REF `a22b8344267adc05d4ff47dca5056fa473a244bb`, ancestor of `HEAD`).
  - `0011-02` → `docs/dossiers/req-0011-02-cl2-worksheets.md`, `docs/pipeline/aspice-cl2-assessment-input.md` (path REFs only).
  - `0011-03` → `docs/pipeline/aspice-level1-score-import.md`. Line REF `db72e61ec` exists as commit `db72e61eced98d0e676ab5e9b260d7a096077983` on branch `0011-03` but is **not** an ancestor of `HEAD`. Integrated successor on `HEAD`: `b97f597c10c3a8b2b4a5e6933f57121300939cbf`. Governance pin `6dde37575f0fd3816c91b498d8aa7b0a17fad69e` is reachable.
  - `0011-04` → `docs/pipeline/aspice-cl2-roles.md` (no SHA in the `TODO.md` line).
  - `0011-05` → `docs/dossiers/req-0020-08-evidence-catalogue.md` (REF `ead0a6d30`).
  - `0011-06` → `docs/pipeline/ecu-profile-evidence-coverage.md` (REF `d05102161`).
- **Cross-feature start prereqs (not Batch-1 children):** `0020-01`, `0020-07`, `0020-08` are `[x]` with `Acceptance: ✓`.

### 3.2 Feature 0012 — Managed Process Performance (PA 2.1 and MAN.3)

- **Goal:** PA 2.1 / MAN.3 managed process performance.
- **Roadmap DoD:** objectives/strategy, work packages/estimates/schedule, resources/competencies/assignments, interfaces/communication, monitoring, correction and replanning.
- **Children + artefacts on HEAD:**
  - `0012-01` → `docs/pipeline/man3-project-management-plan.md`. Line REF `f6a4d86d1212f23ba4f8cd3ca412c852385f1df4` is **not** in this object store. File is on `HEAD` via `39785fac70d87b70df94d22cc14f017547927644`.
  - `0012-02` → same plan file (REF `05efb1ee7`).
  - `0012-03` → `docs/pipeline/man3-resource-needs.md` (`276d99a67`).
  - `0012-04` → `docs/pipeline/man3-resource-allocations.md` (`f2a18ba5e`).
  - `0012-05` → `docs/pipeline/man3-interface-communication-matrix.md` (`56cb72bf8`).
  - `0012-06` → `docs/pipeline/man3-actual-vs-plan-review-mechanism.md` (`cf7944ed7`).
  - `0012-07` → `docs/pipeline/man3-plan-schemas-validators-evidence-control.md` (no SHA in the `TODO.md` line; carrying commit `09f6b89cc5da94fb7783ef290535ef92f33689f7`).
  - `0012-08` → `docs/pipeline/process-performance-strategy.md` (`c6038f6d6`).
  - `0012-09` → `docs/pipeline/ecu-pa21-pre-execution-readiness.md`. Line REF `633edc6` is **not** in this object store (also named in `DONE-obrien-0012-09-integration-20260912.md` as jake’s implementer commit). File is on `HEAD` via `5511db9f4995533656f0ce37b757445dbc5798a7`. Document status remains `REVIEW`; it explicitly does not claim PA 2.1 operational achievement.

### 3.3 Feature 0013 — Stakeholder and Software Requirements with Lifecycle Traceability

- **Goal:** stakeholder/software requirements with lifecycle trace.
- **Roadmap DoD:** reusable requirements, architecture, detailed-design, unit-construction and trace mechanisms (ECU system execution lives in later Features).
- **Children + artefacts on HEAD:** all named path REFs exist. `0013-01` SHA `37db2bafb6ac9363520b5472d199d605aebce6c3` and `0013-02` SHA `283af866979a504c7e7e02de7f087ee6d32492f9` exist as commits on item branches `0013` / `0013-01` / `0013-02` but are **not** ancestors of current `HEAD`. The corresponding dossiers are present on `HEAD`. Remaining `0013-03..11` short SHAs resolve and the listed `docs/pipeline/` and `docs/dossiers/` paths exist.

### 3.4 Feature 0015 — Work-Product and Configuration Management (PA 2.2 and SUP.8)

- **Goal:** PA 2.2 and SUP.8 controls.
- **Roadmap DoD:** work-product requirements, storage/control, baselines, status, reviews/adjustment, dependency/tool identities, immutable evidence, audits and restore tests.
- **Children `0015-01..09`:** all `[x]` with Acceptance; all named path REFs exist on `HEAD`. Line REF `afd81a1` for `0015-08` is **not** in this object store; file `docs/pipeline/sup8-configuration-audits-and-backup-restore.md` is on `HEAD` via `b1e712a739edc6de382a3a96627c7ee797f26453`.
- **Child `0015-10` (material residual):**
  - `TODO.md`: `[x]`, no `Acceptance: ✓`.
  - Prerequisite `0018-03` (and `0018-01`, `0018-02`): `[x]`, **no** `Acceptance: ✓` (Feature `0018` is out of this batch).
  - Evidence present: `docs/pipeline/ecu-pilot-workproduct-review-dossier.md`, `docs/dossiers/0015-10-workproduct-review-evidence.md`, `docs/dossiers/assessment/ECU-PILOT-WORKPRODUCT-REVIEW-v0.7.0.json` (`gate_verdict` = `PASS -- 100% COVERAGE, 0 UNRESOLVED FINDINGS, 4-EYES VERIFIED`; 17 processes; coverage 100.0; unresolved 0).
  - Live engine at this baseline (see §5): same PASS figures; 33 review records; 0 author=reviewer violations.
  - JSON field `commit_sha` / dossier pin `8b2c49f` is **not** a valid object in this repository (dangling baseline pin).
  - Historical mass-marker review (`docs/campaign-evidence/mass-marker-evidence-gap-20260830/`) classified `0015-10` as an unsupported `[x]` marker. Later evidence files exist; Task Acceptance was still never booked.
  - Issue store: `issues/0015/0015-10/index.md` remains `state: open`, label `legacy-terminal-unverified`.

---

## 4. Integration and closure confirmation

Formal confirmation recorded **as specified by the dispatch**, not as a self-assertion of those identities:

| Feature | Feature-header rendering after bookkeeping | Integrator | Project Lead | Checkpoint on Feature node |
|---|---|---|---|---|
| 0011 | `[x] **0011** (feature, closed) … **Acceptance: ✓** (2026-09-29, Project Lead jadzia, Integration by obrien).` | `obrien` | `jadzia` | none in `TODO.md` |
| 0012 | same formula | `obrien` | `jadzia` | none |
| 0013 | same formula | `obrien` | `jadzia` | none |
| 0015 | same formula | `obrien` | `jadzia` | none |

- Child Tasks remain `(task, open)` in `TODO.md` (assignment asked only for Feature-header closure; unlike Feature `0042`, children are not rewritten to `(task, closed)`).
- No Feature→`main` merge is required: this branch already equals `main` at the pinned baseline; bookkeeping lands on `task-hk-aspice-1`.
- No `DONE.md` move (out of assignment scope; same pattern as Feature `0042`).
- This is **not** an ASPICE capability claim (`task-acceptance.md` Automotive SPICE relationship boundary).

---

## 5. Checks executed

All commands run in the foreground against `/private/tmp/autodocs-worktrees/task-hk-aspice-1`.

1. **Marker/Acceptance/REF parse** of `TODO.md` (Python hyphen-aware header scan). Outcome: matrix in §2; `path_fail=0` for every backtick `docs/…` path on child lines; SHA anomalies listed in §3 and §6.
2. **`git cat-file` / `merge-base --is-ancestor`** for every backtick SHA on those lines. Dangling: `f6a4d86d1212f23ba4f8cd3ca412c852385f1df4`, `633edc6`, `afd81a1`. Non-ancestor but present: `db72e61ec`, `37db2bafb6…`, `283af86697…`.
3. **Spot-check files:** `docs/pipeline/aspice-cl2-roles.md`, `aspice-cl2-assessment-input.md`, `man3-plan-schemas-validators-evidence-control.md`, `ecu-pilot-workproduct-review-dossier.md`, `docs/dossiers/0015-10-workproduct-review-evidence.md`, `docs/dossiers/assessment/ECU-PILOT-WORKPRODUCT-REVIEW-v0.7.0.json` — all present.
4. **`0015-10` engine (pytest unavailable in this runtime: `ModuleNotFoundError: No module named 'pytest'`; `python3 -m pytest` failed at spawn).** Equivalent live call:

```text
PYTHONPATH=/private/tmp/autodocs-worktrees/task-hk-aspice-1 /usr/bin/python3 -c '
from _src.tools.ecu_workproduct_review import evaluate_workproduct_review_coverage, get_all_17_workproduct_review_records
r = evaluate_workproduct_review_coverage()
print(r.gate_verdict, r.total_processes_evaluated, r.review_coverage_pct, r.unresolved_findings_count, r.four_eyes_compliance_pct, r.report_sha256, len(get_all_17_workproduct_review_records()))
'
```

Output:

```text
PASS -- 100% COVERAGE, 0 UNRESOLVED FINDINGS, 4-EYES VERIFIED 17 100.0 0 100.0 4926e8a9d6a9b0b0886918104fba0d0a21313803c3064bf7e3636c2705092a7b 33
```

5. **UI / browser:** not applicable. This assignment does not change published HTML, routing, or client behaviour. No browser verification was performed.
6. **`issues/`:** Feature and Task items for 0011/0012/0013/0015 remain `state: open` with `legacy-terminal-unverified` on every child. Out of write scope.

`TODO.md` SHA-256 at the pinned baseline (before bookkeeping): `8e72ef9a9c76592d470e4ac19661335ae71b12a11cae1a5daff1b0a4fe6083c9`.

---

## 6. Residuals, edge cases, data-loss risks

1. **`0015-10` has no Task `Acceptance: ✓`.** Feature `0015` header closure does not create it. Prerequisite `0018-03` is also unaccepted. A later Feature `0018` or Task-Acceptance assignment must book `0015-10` properly or invalidate this Feature-level credit.
2. **Dangling or off-`HEAD` carrying SHAs** in `TODO.md` (`0012-01`, `0012-09`, `0015-08`, `0011-03`, `0013-01`, `0013-02`). Work-product **files** are on `HEAD`; the recorded hashes are incomplete provenance, not missing files. Regenerating or deleting item branches would not delete the `HEAD` copies, but it would destroy the only objects for the non-ancestor commits if those refs were the last copies (`AGENTS.md` ref-retention rule).
3. **`0015-10` JSON `commit_sha` `8b2c49f` is not a Git object** here. Coverage PASS is generated from in-tree records, not from that pin.
4. **`TODO.md` header says generated-view / do-not-hand-edit**, while this assignment (and Feature `0042` precedent) hand-edits `TODO.md`. Next issue-store projection rebuild can **overwrite** these four closed headers. That is the primary data-loss risk for this bookkeeping. Compensating control: this digest-bound dossier on a retained branch.
5. **Issue store still open/shadow** for all 36 children plus four Features. Closure is `TODO.md`-projection-only until a later authorized issue-store write.
6. **No architect-flagged integrating Task** on these Features (breakdown floor unmet for this legacy CL2 set). No silent checkpoint was added.
7. **`0012-09` / `0015-08` documents still say `Status: REVIEW`.** Acceptance lines in `TODO.md` are older than those status strings; not repaired (out of `_src/` / extra-file scope).
8. **No browser UI** in scope; none verified.

---

## 7. Verdict

| Feature | Child `[x]` + Acceptance | Goal/artefact protocol | Feature-header closure |
|---|---|---|---|
| 0011 | PASS (6/6) | PASS with `0011-03` SHA off-`HEAD` residual | CLOSE |
| 0012 | PASS (9/9) | PASS with dangling `0012-01` / `0012-09` SHAs | CLOSE |
| 0013 | PASS (11/11) | PASS with `0013-01`/`0013-02` SHAs off-`HEAD` | CLOSE |
| 0015 | **FAIL 9/10** (`0015-10` unaccepted) | PASS for `0015-01..09`; `0015-10` evidence PASS, Acceptance absent | CLOSE per dispatch, residual explicit |

No `DONE.md` move. No capability rating.

---

## 8. Provenance (user prompt, verbatim)

The triggering user prompt for this check-in is the headless dispatch whose first heading is `# Dispatch-Arbeitsintensität · Version 1` and whose assignment heading is `# Auftrag: Feature Aggregate Closure & Housekeeping (Batch 1: Features 0011, 0012, 0013, 0015)`. Full text as received (no system/developer prompts):

```
# Dispatch-Arbeitsintensität · Version 1

Angefordert: high. Nativer Thinking-Parameter: high. Steuerung: native+briefing.

Bleibe im beauftragten Umfang und beachte die bestehenden Verträge. Für alle Stufen gelten dieselben Wahrheits- und Abnahmestandards: behaupte nur geprüfte Ergebnisse, nenne ausgeführte Prüfungen und verbleibende Lücken. Die Stufe fordert Arbeitsweise, keine garantierte Tokenzahl, Laufzeit oder Zahl künstlicher Prüfungsrunden.

Prüfe Repository und relevante Verträge, reproduziere den Fehler soweit möglich und decke relevante Grenzfälle sowie Datenverlustrisiken ab. Führe passende Tests selbst aus; prüfe UI-Verhalten im echten Browser, sofern verfügbar. Kontrolliere das Ergebnis gegen die Abnahme und berichte Evidenz sowie Restlücken. Erweitere den Scope nicht allein wegen der Effort-Stufe.

---

> **Headless-Einmallauf 20260929-215509-cursor-hk-aspice-1. Vor allem anderen lesen.**
> Dies ist ein nicht-interaktiver Lauf. Sobald du deinen Zug beendest, ist der Auftrag vorbei, und alles
> Unfertige ist verloren. Es gibt keine Benachrichtigungen und niemanden, der nachfragt.
> 1. Führe **jeden** Befehl im **Vordergrund** aus, mit ausdrücklicher Zeitschranke. Starte nichts im Hintergrund
>    (kein `&`, kein `nohup`) und warte auf nichts. Zerlege lange Testläufe in mehrere Vordergrundaufrufe.
> 2. Starte **keinen Befehl ein zweites Mal**, weil du sein Ergebnis nicht gesehen hast. Lies die Ausgabe aus der
>    Datei, in die sie geschrieben wurde. Ein Befehl, der ungewöhnlich lange braucht, ist ein Befund für deinen
>    Bericht, kein Grund zu warten.
> 3. Arbeite nur in `/private/tmp/autodocs-worktrees/task-hk-aspice-1`. Fasse keine anderen Arbeitsbäume und nicht den Hauptcheckout an.
>    Prozessbereinigung nur über nachgewiesene eigene PIDs oder eine ausschließlich eigene Prozessgruppe.
>    Keine breiten `pkill`-/`killall`-Aufrufe; fremde Server und andere Prüfläufe niemals beenden.
> 4. Git immer als `git -C /private/tmp/autodocs-worktrees/task-hk-aspice-1 …`. Kein `git stash`, kein `git push`, keine Änderung fremder
>    Historie, keine `Co-Authored-By`- oder `Claude-Session`-Zeilen.
> 5. **Der Auftrag ist erst mit dem Commit erfüllt.** Committe in kleinen Schritten mit klaren
>    Nachrichten. Ein Arbeitsbaum voller ungespeicherter Arbeit zählt als nicht geliefert;
>    `git -C /private/tmp/autodocs-worktrees/task-hk-aspice-1 status --porcelain` muss am Ende leer sein.
> 6. Deine **letzte Nachricht ist der Bericht**: was erledigt ist, was nicht (mit Grund), Commits, die genauen
>    Testbefehle mit dem Ende ihrer Ausgabe, Abweichungen vom Auftrag. Nenne, was du nicht geschafft hast, so
>    deutlich wie das Erledigte. Letzte Zeile: `DISPATCH-DONE 20260929-215509-cursor-hk-aspice-1`.
>
> Warum das hier steht: im September 2026 arbeiteten drei Läufe zusammen 5,4 Stunden, hinterließen guten Code und
> keinen einzigen Commit. Sie hatten Tests im Hintergrund gestartet und danach nur noch das Warten beschrieben.


---

# Auftrag: Feature Aggregate Closure & Housekeeping (Batch 1: Features 0011, 0012, 0013, 0015)

## Ziel
Durchführung des formalen aggregierten Feature-Abschlusses (`Feature closure`) gemäß `docs/pipeline/task-acceptance.md` für die vier vollständig implementierten und einzeln abgenommenen Automotive SPICE CL2 Features 0011, 0012, 0013 und 0015.

## Umfang (alles davon)
- Erstellung eines konsolidierten Feature-Abschluss-Dossiers `docs/campaign-evidence/feature-closure-aspice-batch-1/report.md` mit:
  - Verifikation, dass alle Teilaufgaben von Feature 0011 (0011-01..06), 0012 (0012-01..09), 0013 (0013-01..11) und 0015 (0015-01..10) vollständig als `[x]` mit Acceptance vorliegen.
  - Prüfprotokoll zu Zielen, Definition of Done und Artefakten der Features.
  - Formale Integrations- und Abschlussbestätigung (Integrator `obrien`, Project Lead `jadzia`).
- Aktualisierung von `TODO.md`:
  - Markierung von `0011` als `[x] **0011** (feature, closed) ... **Acceptance: ✓** (2026-09-29, Project Lead jadzia, Integration by obrien).`
  - Markierung von `0012` als `[x] **0012** (feature, closed) ... **Acceptance: ✓** (2026-09-29, Project Lead jadzia, Integration by obrien).`
  - Markierung von `0013` als `[x] **0013** (feature, closed) ... **Acceptance: ✓** (2026-09-29, Project Lead jadzia, Integration by obrien).`
  - Markierung von `0015` als `[x] **0015** (feature, closed) ... **Acceptance: ✓** (2026-09-29, Project Lead jadzia, Integration by obrien).`
- Commit aller Änderungen auf dem Task-Branch.

## Nicht im Umfang
- Änderung von Quellcode oder Generatoren unter `_src/`.

## Dateien
- Neu anlegen: `docs/campaign-evidence/feature-closure-aspice-batch-1/report.md`
- Ändern erlaubt: `TODO.md`

## Abnahme (das Orakel, vorher festgelegt)
- In `TODO.md` sind die vier Features 0011, 0012, 0013, 0015 mit `- [x]` und `(feature, closed)` markiert.
- `docs/campaign-evidence/feature-closure-aspice-batch-1/report.md` existiert und ist konsistent.
```

Process trigger: headless dispatch `20260929-215509-cursor-hk-aspice-1` on 2026-09-29 (timezone Europe/Berlin, UTC+2). No additional user prompt.
