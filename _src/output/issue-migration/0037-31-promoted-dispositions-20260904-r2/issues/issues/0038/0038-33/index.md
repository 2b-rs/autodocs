---
schema_version: "1.0"
id: "0038-33"
level: "task"
parent: "0038"
state: "open"
visibility: "internal"
prerequisites:
  - "0038-14"
  - "2026"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1807"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0038-33:0038-14 Resolve the failing `automation_safety` aggregate control on `_src/tools/runner_transaction.py`. **Claim (2026-08-22):** `Harry-Bashir-20260822T152700Z` (Dispatcher `harry`, unprivilegiert), read-only bis zum Entscheidungsdatensatz. **Autoritaets-Gate:** erfuellt das kanonische `cross-item-blast-radius`-Praedikat. Unabhaengige Architekten-Scope-Pruefung liegt vor (`Harry-Seven-20260822T153500Z`, Branch `review-0038-33-scope-harry-seven-20260822T153500Z`, `966442b10`). Bezeichner **`DEC-0038-002`** reserviert, vorgesehener Pfad `docs/dossiers/dec-0038-automation-safety-aggregate-control.md`. Bindende Grenze aus der Architektenpruefung: **keine pauschale Datei- oder Regelausnahme**; zulaessiges Minimum ist eine exakt geschlossene Allow-Set-Bindung an Zeile, Symbol und vollen Hash mit asserted Gleichheit; alle uebrigen `AUTO010` sowie `AUTO001`/`AUTO002`/`AUTO009` bleiben verboten; keine Policy-, Scanner- oder Laufzeitaenderung. **Übernahme (2026-08-22):** `Harry-Dax-20260822T183800Z`, neuer Claim `TODO-Harry-Dax-0038-33-20260822T191500Z.md`, owner token `agent:harry-dax-20260822t183800z:0038-33:20260822T191500Z`, Branch/Worktree `0038-33`. Der im Backlog genannte Bashir-Claim wurde repositoryweit gesucht, existiert aber nicht als Datei; deshalb gibt es keinen fremden Claim umzuschreiben. Die Bashir-Historie bleibt in dieser Kopfzeile sichtbar. **Implementierung abgeschlossen:** REF `0607d15b76f8b179db7e898252680983c9d187a1`; unabhängiges Review am bestätigten Pflicht-Checkpoint bleibt erforderlich; keine Acceptance durch den Implementierer.

## Scope

- **Implementierung (Harry-Dax, 2026-08-22):** Ausschließlich `_src/tests/test_automation_safety.py` geändert. `AUTO001`/`AUTO002`/`AUTO009` bleiben für `runner_transaction.py` bedingungslos verboten; beobachtete `AUTO010` werden per Equality exakt an die fünf von `DEC-0038-002` autorisierten `(line,symbol,full evidence_sha256)`-Tupel gebunden. Vier negative Tests beweisen Fail-Closed-Verhalten für einen sechsten, verschobenen, umbenannten und evidence-byte-veränderten Befund. Baseline fokussiert 1/1 rot; nachher fokussiert 5/5 OK und Gesamtmodul 125/125 OK. `py_compile`/`git diff --check` PASS. Live-Gate PASS: 73 Findings, 38 Advisory, 24 dispositionierte kritische, 0 unresolved, 0 Policy-Fehler; alle fünf AUTO010 bleiben maschinell sichtbar, keine AUTO001/2/9. Keine Scanner-, Runtime-, Policy-, Severity-, Live-Gate- oder Dispositionsänderung; kein Blanket Exemption.
  - **Context (found 2026-08-22 by `Kathryn-Neelix-20260822T144500Z` during `0038-31`; reported, not repaired, because it lay outside that Task's write scope):** `test_current_safe_aggregate_controls_do_not_regress` (`_src/tests/test_automation_safety.py:1181`) fails. The control set forbids `AUTO010` in `_src/tools/runner_transaction.py`, but that file carries **five** `AUTO010` findings, at lines 240, 1698, 1839, 3295 and 3922.
  - **Proven pre-existing, not caused by `0038-31`:** the finder restored the pristine `HEAD` (`9601f1934`) version of the changed file and reran the suite — identical single failure. Before: 121 tests / 1 failure. After `0038-31`: 131 tests / the same 1 failure. The existing suite is otherwise unchanged.
  - **The question is which side is wrong, and that is not yet determined.** Either `runner_transaction.py` regressed against a control it is supposed to hold, or the control is stale and was never updated when the file legitimately gained those constructs. **Do not assume.** Establish which by evidence — when the five findings entered the file, whether the control predates or postdates them, and what `AUTO010` actually asserts — and record the answer.
  - **Integration review: mandatory.** **Rationale (provisional — conservative default, not an architect decision):** a failing aggregate control is either a live safety regression in the transaction tool or a gate that no longer means what it claims, and the cheap resolution of both — relax the control — is the wrong one. Set by Projektleiter `kathryn`, who does not set checkpoints; the architect confirms or downgrades it with a recorded justification, at the latest at Feature `0038` closure.
    - **Architect checkpoint decision (2026-08-24, Architect `seven`, Seven of Nine; recorded per `process-roles.md` §Architect and the `AGENTS.md` checkpoint contract):** **confirmed — mandatory.** The node adjudicates between a live safety regression and a stale gate, and the cheap wrong resolution — relaxing the control — is silent and repository-wide. The independent architect scope review (`Harry-Seven-20260822T153500Z`, `966442b10`) bounded the permissible minimum; the checkpoint exists to verify that bound actually held in the delivered change.

## Acceptance criteria

- **AC-001** The suite is green with no failure suppressed. If the file regressed, the code is fixed. If the control is stale, it is corrected with a recorded reason **and** the correction does not silently widen the control beyond the five findings actually examined — a blanket exemption for the file would destroy the control's purpose. Whichever way it resolves, a reader can afterwards tell from the repository why `AUTO010` is or is not permitted here. The disposition mechanism in `_src/tools/automation_safety_policy.json` is not used to paper over a genuine regression

## Definition of Done

Committed with the suite green and real numbers reported (not asserted); no other control weakened, verified explicitly rather than in passing; the finding's history and the chosen resolution recorded so the next person does not re-derive it. **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von der gesamten Implementiererkette Harry-Dax/Gabriel-Bryce/Gabriel-Linus/Gabriel-Sato/Tom-Burnham). Mandatory Integrationscheckpoint **bestanden**. Abgenommene Baseline: finaler Kandidat `559a7473d`, substanziell `4ad2365dc` (Zeilenbindungskorrektur) auf `d0311527` (Merge-Zug repair→0038-10→0038-14→0038-33) auf `305f83fba` (ursprünglicher Kandidat). Review-REFs: `97475b1e9` (ursprüngliches Checkpoint-Review, DEC-0038-002 B-01…B-07 erfüllt, adversarialer End-zu-Ende-Test mit echter Dateimutation durch den echten Scanner, 125/125 Suite grün), `c54c2f5e5` (Merge-Zug abgeschlossen, V1/V3/V6 grün, Fix bestätigt im Baum, eigene Testsuite-Regression durch Zeilenverschiebung gefunden und korrekt nicht selbst repariert), unabhängig verifizierte Korrektur `4ad2365dc` (8 Literale exakt, Symbole/Digests unverändert, 125/125 unabhängig nachgefahren, Live-Scan PASS 5/0/0/0). Prerequisite-closed Batch aller 27 induzierten Knoten vollständig abgenommen (siehe deren jeweilige Acceptance-Zeilen). Kein stiller Fix durch die Integratorin an irgendeinem Punkt dieser Kette.
