# Entscheidungsdatensatz: Fähigkeitsklassen

**Format** nach `RQ-DEC-01/02/03` (Zeitpunkt, entscheidende Identität, fachliche
Rechtfertigung), append-only. Aufzeichnungspflichtig nach `TK-2`: die
Entscheidung wirkt auf jede Session im Projekt.

**Eigene ID-Serie.** Bewusst nicht als `DEC-0041-00x` geführt: der Gegenstand
gehört keinem der laufenden Features, und die Datei
`0041-entscheidungen-und-base-ref-analyse.md` wird derzeit auf dem Branch `0041`
fortgeschrieben (`DEC-0041-005`). Eine eigene Datei vermeidet den Konflikt und
die falsche Zuordnung. Sie ist an das Feature anzuhängen, das die
Fähigkeitsklassen künftig fachlich besitzt.

---

## `DEC-CAP-001` — Dritte Fähigkeitsklasse `unprivileged`

- **Zeitpunkt:** 2026-08-18
- **Entscheidende Instanz:** aktueller Benutzer (Management)
- **Gegenstand:** `SANDBOX.md` kannte nur `sandboxed/grunt` und `privileged`. Im
  Betrieb existiert seit jeher ein dritter Typ: direkt ausführend, aber ohne
  Abnahme-, Integrations- oder `DONE.md`-Befugnis.
- **Entscheidung:** Die dritte Klasse heißt **`unprivileged`**. Sie führt direkt
  aus wie `privileged` und hat die Autorität von `sandboxed-grunt`, nämlich
  keine.

### Belegter Anlass

Eine Session, der genau diese Klasse zugewiesen wurde, verweigerte den
Arbeitsbeginn und forderte eine Entscheidung zwischen den beiden dokumentierten
Klassen. Das war **korrektes** Verhalten: sie durfte ihre Git- und
Commit-Befugnis nicht raten. Der Defekt lag in der Definition, nicht im Agenten.

### Fachliche Rechtfertigung

`SANDBOX.md` definierte die beiden Klassen über **nicht parallele** Kriterien:

| | Ausführung | Autorität |
|---|---|---|
| Sandboxed/grunt | ausdrücklich geregelt | ausdrücklich geregelt |
| Privileged | ausdrücklich geregelt | **nicht erwähnt** |

Die Abnahmebefugnis hing bei `privileged` nur implizit über `AGENTS.md` und
`task-acceptance.md` daran. Damit vermischte ein einzelnes Enum zwei
unabhängige Dimensionen, und der besetzte Punkt „direkt ausführend, ohne
Autorität" hatte keinen Namen.

Das ist derselbe Befund wie C/D der Anforderungsanalyse zu Feature `0040`
(„Privileg ist nicht Unabhängigkeit"). Der vorliegende Fall ist sein
empirischer Beleg.

### Ergänzende Architektenentscheidung: die Fallback-Regel

`SANDBOX.md` fing bisher nur den Fall „absent or ambiguous" ab. Eine
**ausdrücklich zugewiesene, aber unbekannte** Bezeichnung fiel durch das Raster —
genau die Lücke des Belegfalls. Die Regel deckt jetzt zusätzlich *unrecognized*
und *contradictory* ab und schreibt vor: **nicht anhalten, nicht rückfragen** —
als sandboxed handeln, die erhaltene Bezeichnung samt Konflikt wörtlich im Claim
vermerken, weiterarbeiten. Der Rückfall ist immer sicher, weil `sandboxed-grunt`
die restriktivste Klasse ist.

### Verworfene Namensalternativen

- `local-grunt` — vom Verfasser vorgeschlagen, weil „grunt" im vorhandenen
  Vokabular bereits „keine Abnahmebefugnis" markiert. Vom Kunden nicht gewählt.
- `local` — irreführend, weil `privileged` ebenfalls lokal ausführt.

### Umgesetzte Fundstellen

| Datei | Änderung |
|---|---|
| `SANDBOX.md` | Zwei Dimensionen benannt, drei Klassen definiert, Autorität bei `privileged` ausdrücklich hingeschrieben, Fallback-Regel erweitert |
| `_src/tools/legacy_task_doctor.py` | `unprivileged` in `required_capability` und in die akzeptierten `capability_class`-Werte aufgenommen |
| `docs/pipeline/process-roles.md` | Abschnitt 2 von „genau zwei" auf drei korrigiert, mit Korrekturvermerk; Mapping-Tabelle in Abschnitt 4 nachgezogen |
| `PRIVILEGED.md` | Direkte Ausführung ist ausdrücklich **kein** Alleinstellungsmerkmal mehr; unterscheidend ist die Autorität |

Rein additiv: `sandboxed/grunt` und `sandboxed-grunt` bleiben gültig, bestehende
Claims brechen nicht.

### Offen

Ob `unprivileged` auch für den Runner-Pfad Bedeutung hat — ein direkt
ausführender Agent braucht ihn nicht — ist bei der nächsten Überarbeitung des
Runner-Protokolls zu klären. Diese Entscheidung trifft dazu keine Aussage.

---

## `DEC-CAP-002` — Die Fähigkeitsklasse gehört verpflichtend in den Subagenten-Auftrag

- **Zeitpunkt:** 2026-08-19
- **Entscheidende Instanz:** aktueller Benutzer (Management)
- **Gegenstand:** Zwei Subagenten (`grace-riker` an `0033-04`, `sol-ada` an
  `0042-02.01`) trugen beide `capability_class: sandboxed-grunt` ein, obwohl
  beide direkt ausführen dürfen, und serialisierten sich am `run.sh`-Singleton.
- **Entscheidung:** Jeder Subagenten-Auftrag nennt die Fähigkeitsklasse
  ausdrücklich. Fehlt sie, ist der Auftrag unvollständig.

### Belegte Ursache

Die Agenten haben **nicht** falsch gehandelt. Das Dispatch-Briefing von
`grace-riker` verlangt wörtlich „merge required done-but-unintegrated
branches/tips" und „Commit substantive … then separate `[x]` bookkeeping" — also
direkte Git-Ausführung —, nennt aber **keine Fähigkeitsklasse**. Damit greift
`AGENTS.md` Schritt 1 („default to sandboxed/grunt") und die Fallback-Regel in
`SANDBOX.md`. Der Agent hat den dokumentierten Default korrekt angewandt.

Vor dieser Entscheidung existierte **keine einzige Regel** darüber, was ein
Subagenten-Auftrag enthalten muss: eine Suche über `AGENTS.md`, `SANDBOX.md`,
`PRIVILEGED.md`, `CLAUDE.md` und `docs/pipeline/` nach
`subagent|dispatch|briefing|delegat` lieferte als einzigen sachlichen Treffer
die `run.sh`-Warteschlange. Die Lücke war vollständig.

### Schadensbild

Der Default ist fail-closed und deshalb sicher — aber er ist teuer. Er routet
einen direkt ausführenden Agenten auf das Runner-Protokoll, wo er auf einen
Ein-Slot-Mutex wartet, den er nicht braucht. `grace-riker` notierte als nächsten
Schritt „when the runner removes the foreign request …" und blockierte damit
hinter `sol-ada`. Bei zweistelliger Worktree-Zahl skaliert das zum globalen
Stillstand und sieht von außen wie ein hängender Runner aus.

### Umsetzung

Neuer Abschnitt **„Dispatching a subagent"** in `AGENTS.md` mit vier
Pflichtangaben (Klasse, Item-ID und Branch/Worktree, Schreibbereich, Verbote),
der Klarstellung, dass der Default kein Ersatz für eine unterlassene Zuweisung
ist, der Behandlung widersprüchlicher Briefings, und der ausdrücklichen Regel,
dass nur eine Session mit runner-pflichtiger Klasse je auf `run.sh` wartet.

### Bewusst nicht geändert

Der Default selbst bleibt `sandboxed-grunt`. Er ist die restriktivste Klasse und
damit die einzige, die man gefahrlos annehmen kann, wenn nichts bekannt ist.

---

## `DEC-CAP-003` — Agenten ändern niemals einen Dienst, der sie kontrolliert

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-22T20:40:00+02:00`
- **Deciding identity:** `authority:repository-owner`
- **Role:** `Management`
- **Authority reference:** Direkte Anweisung des aktuellen Users, 2026-08-22, im Wortlaut: „Ich erlaube Agenten generell nicht sie kontrollierende Dienste zu verändern, sondern bitte sie stattdessen mich zu beauftragen, damit ich die änderung am dienst prüfen und selbst durchführen kann."
- **Aufgezeichnet von:** Projektleiter `kathryn` (`DEC-ROLE-001`), der die Entscheidung nicht selbst trifft.
- **Subject:** Änderungen an Diensten, Prozessen und Konfigurationen, die die Ausführung von Agenten selbst steuern.
- **Decision:** Kein Agent — unabhängig von Kapazitätsklasse, auch privilegiert — verändert einen Dienst, der ihn oder andere Agenten **kontrolliert**. Das umfasst mindestens den Runner-Dienst und sein Startskript, die Startmechanik, Health-, Restart-, Rollback- und Revocation-Pfade sowie jede Konfiguration, die bestimmt, ob und wie Agenten überhaupt ausgeführt werden. Ein Agent, der eine solche Änderung für nötig hält, **beauftragt stattdessen den Repository-Eigentümer**: er beschreibt die gewünschte Änderung, ihren Zweck, die erwartete Wirkung, die Rücksetzung und die Prüfung. Der Eigentümer prüft und führt sie **selbst** durch. Unberührt bleiben die *Beschreibungen* solcher Dienste im Repository — sie dürfen bearbeitet werden, aber eine Beschreibung darf niemals ein Verhalten behaupten, das am Dienst nicht hergestellt wurde.
- **Technical justification:** Ein Agent, der den Dienst ändert, der ihn ausführt, kann sich im Fehlerfall nicht selbst zurückholen — die Rücksetzung liefe über genau den Mechanismus, den er beschädigt hat. Der Fall ist am 2026-08-22 unter Task `0037-46.02` konkret geworden: `issues/_policy/runner-service.json` beschreibt einen Dienst unter `/tmp/autodocs/runner-host/run-loop.sh`, der **zum Zeitpunkt dieser Aufzeichnung gar nicht existiert**, und ein Agent hatte die Beschreibung bereits auf ein `--once`-Verhalten umgestellt, das am Skript niemand hergestellt hat. Beschreibung und Wirklichkeit waren damit auseinandergelaufen, ohne dass es jemandem auffiel.
- **Triggers:**
  - `cross-item-blast-radius`
- **Considered alternatives:**
  - **ALT-01:** Agenten dürfen kontrollierende Dienste ändern, wenn sie einen bewiesenen Rollback mitliefern.
    - **Disposition:** `rejected`
    - **Reason:** Der Rollback läuft im Zweifel über denselben Dienst. Ein Beweis vor der Änderung sagt nichts über den Zustand nach einer fehlgeschlagenen Änderung.
  - **ALT-02:** Beauftragung des Eigentümers; Agenten liefern Beschreibung, Zweck, Wirkung, Rücksetzung und Prüfung.
    - **Disposition:** `selected`
    - **Reason:** Trennt die Stelle, die den Bedarf erkennt, von der Stelle, die den Eingriff verantwortet — ohne den Bedarf zu unterdrücken.
- **Consequences:**
  - **CON-01:** Für Task `0037-46.02` ist der Host-Anteil damit dauerhaft eine Auftragsleistung an den Eigentümer, kein Agentenschritt. Der gemeldete Blocker ist damit kein Ausnahmefall, sondern der Regelfall.
  - **CON-02:** Eine Dienstbeschreibung, die ein noch nicht hergestelltes Verhalten behauptet, ist ein Befund und keine Vorbereitung.
- **Affected work units:** `task:0037-46.02`, `task:0037-46`, `feature:0037`, `repository:autodocs`
- **Affected gates:** Runner-Ausführung insgesamt; jede künftige Aktivierung, Stilllegung oder Umkonfiguration eines steuernden Dienstes.
- **Waiver:** keiner.
