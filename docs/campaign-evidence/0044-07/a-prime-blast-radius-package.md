# `0044-07` — Entscheidungs- und Blast-Radius-Paket für A-prime

**Status: Vorbereitung, keine Aktivierung.** Dieses Dokument ist selbst keine der vier
Vorbedingungen (globale Entscheidung, unabhängige Architect-Scope-Review, additive
Auswirkungsanalyse mit Invalidierung, erneute unabhängige Prüfung) — es bereitet sie vor,
indem es benennt, was jede von ihnen betreffen muss.

**Auftraggeberin:** `kathryn`, Feature-Eigentümerin `0044`, im Rahmen des Management-delegierten
Dreierkonsenses. **Ausführende Session:** `harry`, `unprivileged`, Rolle Dispatcher für diese
Aufgabe. **Gepinnte Basis:** `main` @ `8a364e000fed6e826a1e7d49c4b1c014c849eece`.

---

## 1. Entscheidungslage (wörtlich übernommen, nicht meine Bewertung)

- **Unterstützen A-prime:** `jean-luc`, `seven`, `geordi` (Dreierkonsens).
- **`data` widerspricht, empfiehlt B.** Dissens-Evidenz: `data` `1787695011574-453e01f6`,
  `geordi` `1787694996430-ffbec4ef`, `seven` im `0044-07`-Thread. Ich habe diese Nachrichten
  selbst nicht gesehen (fremde Postfächer) — Existenz und Positionen sind mir nur über kathryns
  Weitergabe bekannt, hier so wiedergegeben, nicht verifiziert.
- **Operative Richtung A-prime, im Wortlaut:**
  - Runner bleibt als normalerweise unprivilegierte **direkte Ausführungsrolle**.
  - Runner-**Dienst**, **Queue** und **Transport** werden für das Zukunftssystem ausgemustert.
  - `sandboxed-grunt` wird **global aus zukünftiger Planung entfernt**.
  - Sicherheitsregeln werden auf direkte Ausführung / Runner-Rolle übertragen.
  - Unverändert: historische Evidenz, Rollen-/Privilegientrennung, Annahmeverbote,
    Wiederherstellbarkeit.

## 2. Datas Gegenposition (B) — als gleichrangiger Teil des Pakets, nicht Fußnote

Ich habe den Inhalt von `data`s B-Empfehlung selbst **nicht** einsehen können (Nachricht
`1787695011574-453e01f6`, fremdes Postfach, kein Repository-Datensatz gefunden). Ich kann daher
nicht sagen, worin B sich von A-prime unterscheidet. **Das ist eine Lücke in diesem Paket, keine
Neutralisierung des Dissenses** — ich trage ihn als offen und ungelöst weiter, statt ihn
kommentarlos wegzulassen. Wer dieses Paket weiterverwendet, muss `data`s Position wörtlich
nachreichen, bevor (a)–(d) unten sinnvoll ausgeführt werden können: eine Architect-Scope-Review
kann zwei Optionen nicht gegeneinander abwägen, wenn nur eine davon dokumentiert ist.

**Ich sage hier ausdrücklich, was mir aus dem Repository-Befund auffällt, ohne für data
Stellung zu beziehen:** `sandboxed-grunt` ist kein Nebendetail, sondern trägt einen aktiven
Sicherheitsmechanismus (siehe §3.2, Fallback-Regel). Eine Entscheidung, die diese Klasse **aus
der Planung entfernt**, muss zeigen, wohin der heutige Fallback-Pfad wandert, sonst verliert das
System eine Instanz seines eigenen fail-safe-Verhaltens. Ob das durch A-prime bereits geklärt
ist, weiß ich nicht — ich habe A-primes vollen Text nicht, nur kathryns Zusammenfassung. Das ist
genau die Art Frage, bei der `data`s Gegenposition zählen könnte.

## 3. Betroffene Verträge und Arbeitseinheiten — mit Reichweite

### 3.1 Direkt normativ, vermutlich invalidierungspflichtig

- **`SANDBOX.md`** — Abschnitt „Agent capability classes" (Z. 19–61). Definiert `sandboxed-grunt`
  als eine der drei Klassen mit eigener Execution/Authority-Zeile in der Tabelle. **Enthält den
  aktiven Fallback-Sicherheitsmechanismus:** „If the class is absent, ambiguous, unrecognized, or
  contradicts these definitions … act as a sandboxed agent" — das ist die Ausweichinstanz für
  jeden unklaren Fall, repository-weit. Enthält zusätzlich den Satz „Feature `0037` is designed to
  be implemented entirely by sandboxed/grunt agents" — eine historische Tatsachenbehauptung, die
  unter A-prime nicht mehr zukunftsgültig wäre.
- **`docs/pipeline/process-roles.md`** — Abschnitt 4 „Mapping: role → capability class" (Z. 120–130).
  Vier von fünf Rollen (Architect, Implementer-Default, Requirements Engineer, QA Manager) haben
  `sandboxed-grunt` als **Mindestklasse**. Ohne diese Klasse braucht jede Zeile eine neue
  Mindestklasse — vermutlich `unprivileged`, aber das ist eine Entscheidung, keine Ableitung, die
  ich hier treffen darf.
- **`docs/pipeline/feature-breakdown.md`** — Abschnitt 2 „Required task record" (Z. 66:
  `capability_class: sandboxed-grunt | unprivileged | privileged`), abgenommen als `361f0ce44`.
  **Geordis Feststellung (kathryns Wiedergabe, von mir nicht selbst nachgeprüft):** §7 „Pilot and
  applicability" schützt nur die Bindungskraft der neuen A1/A2-Pilotregeln, nicht die normative
  Aufzählung in §2. Ich habe §7 selbst gelesen (unten, §3.3) und finde diese Lesart plausibel: §7
  spricht ausschließlich vom „A1/A2 behavior", nicht vom Schema selbst. Wenn das zutrifft, ist die
  Abnahme `361f0ce44` unter A-prime **materiell veraltet**, sobald A-prime breit gilt — nicht nur
  in einem nicht-bindenden Sinn.
- **`docs/pipeline/capability-matching.md`** — definiert das Schema und die Matcher-Kreuzregeln
  hart gegen `sandboxed-grunt` (z. B. „`sandboxed-grunt`+`runner` required → only `sandboxed-grunt`
  with `runner`"). Diese Regeln würden unter A-prime nicht mehr feuern können, weil die Klasse aus
  der Planung fehlt — das ist kein Löschen einer Textstelle, sondern das Wegfallen eines aktiven
  Matcher-Zweigs.

### 3.2 Aktive Übergänge — Prozessschritte, die auf der Klasse aufbauen

- Der oben zitierte **Fallback-Mechanismus** in `SANDBOX.md` ist der wichtigste einzelne Fund
  dieses Abschnitts: er ist keine Dokumentationszeile, sondern ein Verhalten, das jede Session mit
  unklarer Zuweisung *heute* tatsächlich ausführt. A-prime muss entweder einen Ersatz-Fallback
  benennen oder explizit erklären, warum keiner mehr nötig ist.
- **Runner-Queue-Dispatch** (`SANDBOX.md` „Runner protocol for sandboxed agents", ab Z. 86, 38
  Erwähnungen von „runner" allein in dieser Datei): beschreibt Dienst, Queue (`.runner/drafts`,
  `.runner/requests`, `.runner/results`) und Transport im Detail für sandboxed/grunt-Sessions. Das
  ist exakt das, was A-prime laut Wortlaut „für das Zukunftssystem ausmustert" — dieser gesamte
  Abschnitt ist der unmittelbare Zielbereich der operativen Richtung, nicht nur mittelbar
  betroffen.
- **`_src/tools/capability_match.py`**, **`legacy_task_doctor.py`**, **`legacy_task_editor.py`**,
  **`provision_tmp_worktree.sh`**, **`runner_transaction.py`** — Werkzeuge mit Code-Pfaden, die
  `sandboxed-grunt` als Wert kennen (Klassifikation, Validierung, Provisionierung). Ich habe nicht
  geprüft, wie tief diese Abhängigkeit reicht (Konstante vs. verzweigte Logik) — das ist
  Implementierungsarbeit, außerhalb dieses Vorbereitungspakets.
- **Historisch/evidenziell, vermutlich NICHT invalidierungspflichtig** (zur Abgrenzung, damit das
  Paket nicht übergreift): `docs/campaign-evidence/0038-34-analysis/*`,
  `docs/campaign-evidence/0044-05/*`, `docs/design/ui-ux-task-decomposition*.md`,
  `docs/dossiers/0037-51-de-sandboxing-scope-review.md`,
  `docs/dossiers/0037-ticket-modernization-execution-plan*.md`,
  `docs/dossiers/0040-main-integration-repair-20260820T001000Z.md`,
  `docs/dossiers/dec-0037-future-direct-execution.md`,
  `docs/dossiers/dec-0044-015-provenance.txt`, `docs/dossiers/dec-capability-classes.md`,
  `docs/dossiers/re-intake-prozessverbesserung-integration-und-capabilities.md`,
  `docs/pipeline/agent-execution.md`, `docs/pipeline/approvals/*`,
  `docs/pipeline/branch-merge-actions.md`, `docs/pipeline/runner-transaction.md`. Diese
  dokumentieren vergangene Entscheidungen und Zustände; sie ändern sich nicht rückwirkend, aber
  einige (`dec-0037-future-direct-execution.md`, `dec-capability-classes.md`) könnten als
  Kontext/Präzedenz für die A-prime-Entscheidung selbst relevant sein — nicht als zu ändernder
  Vertrag. **Ich habe keine dieser Dateien inhaltlich geprüft**, nur ihre Fundstelle notiert; diese
  Einordnung ist meine Einschätzung, kein abschließender Befund.

### 3.3 Eigene Nachprüfung von §7 `feature-breakdown.md` (read-only)

Gelesen (Zitat, gekürzt): „The source/dependency/test/profile record shape is binding for
breakdowns. The new A1/A2 behavior is binding first for the named pilot Tasks, and general
effectiveness is claimed only after the pilot is evaluated, at the latest by the mandatory
`0044-08` review." — Der Abschnitt scoped ausdrücklich nur das **A1/A2-Verhalten** (Prozessregel
für Architekten-Fehlervermeidung), nicht die in §2 aufgezählten Enum-Werte des
`capability_profile`-Schemas. Meine Lesart: §7 gibt dem `capability_class`-Enum in §2 **keinen**
Schutzraum. Das deckt sich mit Geordis in kathryns Nachricht wiedergegebener Feststellung. Ich
habe dies selbst am Text verifiziert, nicht nur übernommen.

## 4. Aktivierungspunkt

Nicht von mir festgelegt — das ist Teil der zu erst erforderlichen globalen Entscheidung (a). Was
ich nachprüfbar beitragen kann: `0044-07` selbst trägt aktuell (main, `8a364e000`)
**`Integration review: nicht mandatory`**, mit Architekten-Begründung „role adoption itself is
decision-record-gated; this Task produces reviewed proposals, not live authority changes.
Re-examined at `0044-08`." Das bedeutet: der **Vorschlag** (dieses Paket, die spätere
`0044-07`-Ausarbeitung) selbst löst keinen Checkpoint aus — aber die **Aktivierung** einer
Rollenkatalog-/Klassenänderung ist laut demselben Satz spätestens bei `0044-08` erneut zu prüfen,
und laut den vier Vorbedingungen (a)–(d) frühestens nach einer eigenen, hier noch nicht
existierenden Architect-Scope-Review. Der Aktivierungspunkt ist damit **nicht `0044-07` selbst**,
sondern liegt danach — wo genau, ist Teil dessen, was (a) festlegen muss.

## 5. Migration historischer Profile

Nicht von mir bewertet — braucht `data`s B-Inhalt und die vier Vorbedingungen zuerst. Nachprüfbar
ist nur: Task-Profile mit `capability_class: sandboxed-grunt` existieren bereits in committeten
Task-Records (z. B. `docs/campaign-evidence/*`, historische `TODO-*.md`-Claims). Diese sind
`AGENTS.md`s eigener Regel nach unveränderliche Historie („history is never rewritten"/„history is
never deleted" — mehrfach so formuliert in `AGENTS.md`). Eine Migration kann also nur **additiv**
erfolgen (neue Kandidatenwerte für künftige Profile), nicht durch Rückwirkung auf bestehende
Records. Das ist eine Ableitung aus bestehender Regel, keine neue Entscheidung von mir.

## 6. Prüfungen (was eine spätere Architect-Scope-Review/Prüfung mindestens ansehen sollte)

- Ob der Fallback-Mechanismus in `SANDBOX.md` unter A-prime einen definierten Nachfolger hat.
- Ob `capability-matching.md`s Matcher-Kreuzregeln unter A-prime noch deterministisch sind (das
  Schema verlangt „exactly one value" pro Feld — ein Enum-Wert weniger ändert das Matching, nicht
  nur die Doku).
- Ob `process-roles.md` §4 für alle fünf Rollen neu bestimmt wird, oder ob eine implizite
  Ersetzung (`sandboxed-grunt` → `unprivileged`) angenommen wird, ohne das explizit zu entscheiden.
- Ob `feature-breakdown.md`s Abnahme `361f0ce44` additiv invalidiert und neu geprüft wird, bevor
  A-prime breit gilt — nicht nur bei Gelegenheit.
- `data`s B-Position, sobald verfügbar, gegen dieselben Punkte.

## 7. Recovery

Nicht von mir festgelegt. Was ich als Randbedingung nachprüfbar beitragen kann: `AGENTS.md`s
„Cross-item gate-scope review exception" verlangt bereits, dass die qualifizierende Mutation
**nicht** beginnt, solange (a)/(b) fehlen, und dass der betroffene Task `[p]`/vorbereitend bleibt.
Ein Recovery-Pfad für den Fall, dass A-prime nach Teilaktivierung zurückgenommen werden müsste,
ist damit indirekt durch dieselbe Regel geschützt — solange niemand vor Erfüllung von (a)–(d)
mutiert, gibt es nichts zurückzunehmen. Ein expliziter Recovery-Plan **für den Aktivierungsschritt
selbst** (falls A-prime aktiviert und dann falsch befunden wird) ist nicht Teil dieses
Vorbereitungspakets und müsste von der Architect-Scope-Review gefordert werden.

## 8. Ausdrücklich nicht geleistet

Keine Implementierung, keine Mutation an einem der genannten abgenommenen Verträge, kein
`Acceptance: ✓`, kein Checkpoint-Übertritt, kein Merge. `data`s B-Inhalt ist nicht wiedergegeben,
weil ich ihn nicht einsehen konnte — als offene Lücke benannt, nicht stillschweigend
übergangen. Die Tiefe der Werkzeug-Code-Abhängigkeiten (§3.2) ist nur benannt, nicht analysiert.
