---
schema_version: "1.0"
id: "0043-07"
level: "task"
parent: "0043"
state: "open"
visibility: "internal"
prerequisites:
  - "0043-01"
  - "0043-02"
  - "0043-03"
  - "0043-04"
  - "0043-05"
  - "0043-06"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:739"
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

PREREQ: 0043-07:0043-01, 0043-07:0043-02, 0043-07:0043-03, 0043-07:0043-04, 0043-07:0043-05, 0043-07:0043-06 Integrate the Feature and prove one publication run end to end. **Claim (2026-08-24):** `Tom-Okonkwo-20260824T101000Z` (Dispatcher `tom`, unprivilegiert), `TODO-Tom-Okonkwo-0043-07-20260824T101000Z.md`, owner_token `agent:tom-okonkwo-20260824t101000z:0043-07:20260824T101000Z`. Vierter Claim, siebte Session; Vorgaengerclaims `Tom-Sabine-20260824T013000Z`, `Tom-Rivera-20260824T042500Z`, `Tom-Vasquez-20260824T084000Z` bleiben als Provenienz auf dem Branch. Fortgesetzte Kohorte `manual-20260824T072259Z-d6eece5d` (Stufen 10-13 committet). Strukturaenderung `F-TOM-OKONKWO-001`: `validate.py` laeuft **detached** (`setsid nohup`), da zwei Sessions genau an dieser Stufe gestorben sind; die Berechnung ueberlebt den Sessiontod, das Evidenzfile ist selbstbeschreibend mit echtem Exit-Status und Abschlussmarker. **Claim (2026-08-24):** `Tom-Adeyemi-20260824T133000Z` (Dispatcher `tom`, unprivilegiert), `TODO-Tom-Adeyemi-0043-07-20260824T133000Z.md`, owner_token `agent:tom-adeyemi-20260824t133000z:0043-07:20260824T133000Z`. Fuenfter Claim, achte Session; Vorgaengerclaims `Tom-Sabine-20260824T013000Z`, `Tom-Rivera-20260824T042500Z`, `Tom-Vasquez-20260824T084000Z`, `Tom-Okonkwo-20260824T101000Z` bleiben als Provenienz auf dem Branch. **Implementierung abgeschlossen (2026-08-24):** REF `5bfe836f6` (substanziell), Branch-Tip siehe Buchhaltungscommit. Kohorte `manual-20260824T072259Z-d6eece5d` end-to-end gefahren: korrelierte Subreports (4/4 Stufen, ein geteilter nicht-nuller `run_archive_ref`), erfolgreiches `combine` mit **erstem echten Ledger-Eintrag** (`docs/evidence/build-ledger.jsonl` 1 -> 2 Zeilen, Zeile 1 byte-identisch, `backfilled: false`, `repo_commit 7a0cce8d2`), `publish` + `generate.py` (428 Seiten, nur ueber Generatoren), Lauf in der Historienliste sichtbar, und **`validate.py` gruen (exit 0)** — alle internen Links und Anker gueltig, keine Waisen. **Dreiweg-Nachweis des Staleness-Gates, live statt hermetisch:** Stufe 15 exit 1 = Feuerbedingung **(b)** `unrecorded-publication-run`, Stufe 17 exit 1 = Feuerbedingung **(a)** `stale-build-report`, Stufe 20 exit 0 = beide erfuellt, Gate **loest aus und raeumt aus dem richtigen Grund ab**; die drei Zustaende schliessen einander aus und entstanden je aus dem echten Baumzustand. Damit ist die **Auflage `F-TOM-BAXTER-003` aus der `0043-04`-Abnahme erfuellt**; (a) ist als nicht geforderte Zugabe ebenfalls live belegt. Ledger-Idempotenz zweifach belegt (`publish` und erneutes `combine` liessen das Ledger byte-identisch, 'ein Eintrag je Lauf'). Alle sieben `RQ-BR-*` mit Evidenz disponiert (`docs/campaign-evidence/0043-07-publication-run/21-rq-br-dispositions.md`); Evidenz Stufen 10-21 aufbewahrt. **Ehrlich vermerkt:** `overall_success: false` — 107 taskfremde `i18n_merge`-Rejects in den getrackten englischen Uebersetzungsbatches, vorbestehend, ausserhalb des Schreibscopes, **nicht** umgangen (`F-TOM-ADEYEMI-001`, bestaetigt `F-TOM-OKONKWO-003`); die zweite `0043-04`-Auflage (`process.html`-Deadlink) ist erledigt, **aber nicht durch Reparatur** — das Ziel fehlt weiterhin, die Seite verweist nach Regenerierung nur nicht mehr darauf; die dritte Feuerbedingung `malformed-build-ledger` wurde **nicht** live ausgeloest (weiter nur hermetisch abgedeckt); `0019-06` bleibt sichtbar, aber unverlinkt; und diese Session hat **zwei eigene Messfehler** protokolliert statt sie zu bereinigen (`F-TOM-ADEYEMI-002`, Stufen 16a und 19). Kein Integrationscheckpoint gekreuzt (der verpflichtende `0043-07`-Checkpoint liegt bei `belanna`), keine Acceptance erzeugt, `refs/heads/main` nicht bewegt, `DONE.md` unberuehrt. Abnahme steht aus.

## Scope

- **Integration review: mandatory.** **Rationale (architect):** the Feature's integrating task and review floor. The trigger defect was a composition failure — every part worked, the chain did not — so the chain itself is what must be reviewed.

## Acceptance criteria

- **AC-001** One real publication run is carried end to end: correlated subreports, successful `combine`, appended ledger entry, regenerated pages showing the run in the history list, `validate.py` green including the new staleness check
- **AC-002** every `RQ-BR-*` requirement has a disposition
- **AC-003** the run evidence is retained

## Definition of Done

Committed; the end-to-end evidence is retained; no report page is older than the run that built it. **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierern `Tom-Sabine-20260824T013000Z`/`Tom-Rivera-20260824T042500Z`/`Tom-Vasquez-20260824T084000Z`/`Tom-Okonkwo-20260824T101000Z`/`Tom-Adeyemi-20260824T133000Z`). Mandatory Feature-Floor-Checkpoint **bestanden**. Abgenommene Baseline: Kandidat `5bfe836f6`, integrierter Stand `13635f3e0`; Review-REFs `218ca607d` (Drei-Wege-Demonstration der B-02-Feuerbedingungen live verifiziert; Schlussorakel `validate.py` selbst nachgefahren, EXIT 0) und `2d96dd751` (erste scharfe Ausführung der Integrationstest-Auflage aus `integration-test-obligation.md`, alle fünf Ableitungskategorien ausgeführt, keine unexaminiert). Induzierte prerequisite-closed Batch `{0043-06}` separat abgenommen (siehe dortige Acceptance-Zeile). Auflage aus `F-TOM-BAXTER-003` erledigt: beide B-02-Feuerbedingungen live statt hermetisch bewiesen.
