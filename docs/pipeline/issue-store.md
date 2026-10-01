# Issue-Store — kanonische Pfade, Identität, Hierarchie, Autorität, Privatsphäre

**Status:** Entwurf, review-bereit (Task `0037-01`, Feature `0037`). Bis zum autorisierten
Cutover bleiben `TODO.md`, `DONE.md` und aktive Claim-Dateien maßgeblich; `issues/` ist eine
wegwerfbare Schatten-Datenbank ohne eigene Autorität (siehe Feature-`0037`-Abschnitt in
`TODO.md`).

## 1. Zweck und Geltungsbereich

Dieses Dokument fixiert den kanonischen Datei-Layout-, Identitäts- und Autoritätsvertrag für
den Git-nativen Issue-Store, der `TODO.md`/`DONE.md` nach dem Cutover ablösen soll. Es ist
normativ für alle Werkzeuge, Schemata und Migrationsschritte in Feature `0037`.

## 2. Kanonische Pfade

| Pfad | Inhalt | Wer schreibt? | Autorität |
|---|---|---|---|
| `issues/XXXX/index.md` | Kanonisches, maßgebliches Feature-Dokument (`XXXX` = 4-stellige Feature-ID) | Werkzeuge/Agenten via geprüftem Commit | Nach Cutover: maßgeblich. Vorher: Schatten. |
| `issues/XXXX/XXXX-YY[.ZZ]/index.md` | Kanonisches, maßgebliches Task- bzw. Subtask-Dokument (`YY` = 2-stellige Task-Nr., `ZZ` = optionale 2-stellige Subtask-Nr.) | dito | dito |
| `issues/XXXX/XXXX-YY[.ZZ]/claim.json` | Item-lokaler, aktiver Claim (Besitz, Owner-Token, Runner-Scope) | claimender Agent | Retained state, kein globaler Mutex (siehe §5) |
| `issues/XXXX/XXXX-YY[.ZZ]/closure.json` | Terminaler Abschlussdatensatz (nur bei `[x]`/`[w]`) | abschließender Agent, einmalig | Unveränderlich nach Commit |
| `issues/XXXX/XXXX-YY[.ZZ]/decisions/` | Entscheidungsprotokolle (z. B. Architektur-, Scope-Entscheidungen) zu diesem Item | Agenten/Reviewer | Anhängend, nie retrospektiv verändert |
| `issues/XXXX/XXXX-YY[.ZZ]/attachments/` | Item-lokale Anhänge (Diagramme, Evidenz-Snippets, Referenzdateien) | Agenten | Content-adressiert oder ID-referenziert, nie geraten |
| `issues/_schema/` | Maschinenlesbare Schemata für `index.md`-Frontmatter, `claim.json`, `closure.json`, Entscheidungsdateien | Feature-`0037`-Werkzeuge | Maßgeblich für Validierung |
| `provenance/_schema/` | Schemata für typisierte Provenienz-Events, Runs, Findings, Artefakt-Sets (siehe `docs/pipeline/issue-derived-artifacts.md`, Task `0037-04`) | dito | Maßgeblich für Validierung |
| `issues/_views/` | Interne, generierte Sichten (Abfragekataloge, Abhängigkeitsgraphen) über den gesamten Issue-Store, inkl. privater Felder | Build-Werkzeuge | **Nur generiert.** Niemals Parser-Input, niemals zweite Autorität. |
| `_src/data/issue-graph-public.json` | Locale-neutrale, allowlisted öffentliche Projektion (siehe §6) | Publikationswerkzeug | Nur generiert |
| `_src/sources/pages/issues.json` | Öffentliches Seiten-Modell für die generierte Website | Publikationswerkzeug | Nur generiert |

**Grundregel:** Generierte oder Schatten-Dateien (`issues/_views/`, `_src/data/issue-graph-public.json`,
`_src/sources/pages/issues.json`, jede Datei unterhalb von `output/`) dürfen niemals als
Parser-Eingabe verwendet werden und werden niemals selbst zu einer zweiten Autorität. Genau
ein Pfad pro Item besitzt Schreibautorität für dessen Kerninhalt.

## 3. Verzeichnisstruktur — flach, ID-bestimmt

Item-Verzeichnisse liegen **flach** unterhalb ihres Feature-Verzeichnisses; Hierarchie wird
ausschließlich über die ID selbst und ein strukturiertes `parent`-Feld im Frontmatter
kodiert, niemals über Dateisystem-Verschachtelung:

```text
issues/
  0037/
    index.md                     # Feature 0037
    0037-01/
      index.md                   # Task 0037-01, parent: 0037
      claim.json
    0037-02/
      index.md                   # Task 0037-02, parent: 0037
    0037-02.01/
      index.md                   # Subtask 0037-02.01, parent: 0037-02
      decisions/
        0001-yaml-profile.md
```

**Begründung (Entscheidung, 2026-08-16, nutzerseitig bestätigt):** Ein gemeinsames
`feature.md` plus viele `task-*.md`-Dateien im selben Verzeichnis wurde verworfen, weil es
keinen isolierten Namensraum für Claims/Closures/Evidenz je Item bietet und die
Feature-Verzeichnis-Kontention erhöht. Tiefe Subtask-Verschachtelung wurde verworfen, weil
die Hierarchie bereits durch IDs kodiert ist und Verschachtelung Reklassifizierungen/Verschiebungen
unnötig erschweren würde.

**ID-Ableitbarkeit (Definition of Done, Fixture-Pflicht):** Aus jedem kanonischen Pfad muss
sich die Item-ID und die Hierarchie-Ebene (Feature/Task/Subtask) allein aus dem Pfad ableiten
lassen — ohne Titel- oder Status-Heuristik. Formal:

- `issues/XXXX/index.md` → Ebene `feature`, ID `XXXX`.
- `issues/XXXX/XXXX-YY/index.md` → Ebene `task`, ID `XXXX-YY`, `parent = XXXX`.
- `issues/XXXX/XXXX-YY.ZZ/index.md` → Ebene `subtask`, ID `XXXX-YY.ZZ`, `parent = XXXX-YY`.
- Jeder andere Pfad unterhalb von `issues/XXXX/` (außer `_schema/`) ist ungültig und muss vom
  Parser mit einem harten Fehler abgelehnt werden, nicht mit einer Best-Effort-Vermutung.

## 4. Frontmatter-Identitätsfelder (Kurzreferenz)

Die vollständige `issue-item@v1`-Formatdefinition ist Gegenstand von Task `0037-02` und ihren
Subtasks (YAML-Profil, Markdown-Profil, Fixtures); dieses Dokument fixiert nur die für
Pfad/Identität/Autorität relevanten Pflichtfelder:

| Feld | Pflicht | Bedeutung |
|---|---|---|
| `id` | ja | Muss exakt der aus dem Pfad abgeleiteten ID entsprechen (§3); Parser lehnt Abweichung hart ab. |
| `parent` | nur bei Task/Subtask | Muss exakt der aus dem Pfad abgeleiteten Parent-ID entsprechen. |
| `level` | ja | `feature` \| `task` \| `subtask`, muss mit dem Pfad übereinstimmen. |
| `state` | ja | Lifecycle-Zustand (siehe `docs/pipeline/issue-lifecycle.md`, Task `0037-03.01`); hier nur referenziert, nicht definiert. |
| `visibility` | ja | `internal` (Default) \| `public-summary` (siehe §6). Fehlendes Feld gilt als `internal`. |

## 5. Claims — retained state, kein globaler Mutex

Ein committetes item-lokales `claim.json` ist **retained state**, nicht ein globaler Mutex:

- Innerhalb desselben Clones/Worktrees erwerben Worktrees `refs/autodocs/claims/<item-id>`
  per Compare-and-Swap.
- Unabhängige Clones konkurrieren um einen geschützten, serialisierten Integrationsbranch;
  dessen Validator lehnt Claims mit veraltetem Base, überlappendem Scope, Duplikaten oder
  Konflikten ab.
- Lease-Ablauf überträgt Besitz **niemals** stillschweigend; eine registrierte Autorität muss
  eine Übernahme genehmigen und Claim-/Freigabe-/Recovery-Events erhalten bleiben.

Dies ist konsistent mit dem in `SANDBOX.md`/`AGENTS.md` beschriebenen Legacy-Claim-Modell
(`TODO-<agent-id>.md`) und wird in Task `0037-03.02` vollständig spezifiziert.

## 6. Sichtbarkeit, Publikation, Redaktion

Der vollständige Issue-Store und der Maintainer-Graph sind **standardmäßig intern**
(`visibility: internal`). Publikation erzeugt zunächst eine locale-neutrale, allowlisted
Projektion, die ausschließlich Items mit `visibility: public-summary` und genehmigte Felder
enthält:

- ID, Ebene, Titel-Schlüssel/Quell-Hash, groblastiger Zustand, öffentliche Prerequisites,
  öffentliche Zusammenfassung/Link.
- **Ausgeschlossen:** Claims, Personen, private Pfade, detaillierte Findings/Entscheidungen/Evidenz,
  Sicherheits-Label, unveröffentlichte Items, sowie Kanten zu ausgeschlossenen Knoten.
- Die Ausgabe berichtet nur eine aggregierte Anzahl eingeschränkter Items, niemals deren
  Identität.

Erst danach werden genehmigte Titel-/UI-Übersetzungen je Sprache eingebunden. Issue-Bodies
selbst bleiben ausschließlich kanonisch und werden nicht automatisch veröffentlicht oder
übersetzt. IDs, Referenzen, Pfade, Hashes, Code und Kriterien-IDs werden niemals übersetzt.
Fehlende Pflichtübersetzungen lassen die Publikation fehlschlagen (fail-closed), niemals
Best-Effort mit Lücken.

## 7. Provenienz und Migrationspfade (Verweis)

Typisierte Referenzen, Provenienz-Events, Runs, Findings und Artefakt-Sets werden in
`docs/pipeline/issue-derived-artifacts.md` (Task `0037-05`) und den zugehörigen
JSON-Schemata unter `provenance/_schema/` (Task `0037-04`) definiert. Dieses Dokument grenzt
nur ab, **wo** diese Daten liegen (`provenance/_schema/`, item-lokale `attachments/`), nicht
**was** sie enthalten.

## 8. Autorität und Cutover-Regeln (Verweis)

Bis zum autorisierten Cutover bleiben `TODO.md`, `DONE.md` und aktive Legacy-Claim-Dateien
maßgeblich; `issues/` ist eine wegwerfbare, nicht-autoritative Schatten-Datenbank. Agenten
dürfen beide Repräsentationen nicht parallel handpflegen und dürfen aus der bloßen Anwesenheit
von `issues/` keinen Cutover ableiten (siehe `SANDBOX.md`, Abschnitt „Current backlog
authority", und den Feature-`0037`-Abschnitt in `TODO.md`). Der eigentliche
Cutover-Mechanismus (ein reviewter Commit, der `issues/**/index.md` atomar maßgeblich macht)
ist Gegenstand von Task `0037-06.03` und wird hier nur referenziert.

## 9. Fixtures (Pflicht für Definition of Done)

Die folgenden Positiv-/Negativ-Fixtures sind vor Abschluss dieses Tasks zu committen (Pfade
vorbehaltlich Feinabstimmung mit Task `0037-02.03`):

| Fixture | Erwartung |
|---|---|
| `issues/_schema/fixtures/valid-feature-path.txt` = `issues/0099/index.md` | Ableitung: Ebene `feature`, ID `0099` |
| `issues/_schema/fixtures/valid-task-path.txt` = `issues/0099/0099-01/index.md` | Ableitung: Ebene `task`, ID `0099-01`, `parent=0099` |
| `issues/_schema/fixtures/valid-subtask-path.txt` = `issues/0099/0099-01.02/index.md` | Ableitung: Ebene `subtask`, ID `0099-01.02`, `parent=0099-01` |
| `issues/_schema/fixtures/invalid-nested-path.txt` = `issues/0099/0099-01/0099-01.02/index.md` | Harter Parser-Fehler (verschachtelter Subtask-Pfad ist ungültig, siehe §3) |
| `issues/_schema/fixtures/invalid-view-as-input.txt` = `issues/_views/0099.md` | Harter Parser-Fehler (generierte Sicht darf nie Eingabe sein) |
| Projektionsfixture: `_src/data/issue-graph-public.json` (Beispielausgabe) | Enthält nur `public-summary`-Items und genehmigte Felder; kein Claim-, Personen- oder Sicherheitsfeld |

## 11. Constrained-Markdown-Profil und AC-Lifecycle (Task `0037-02.02`)

### 11.1 Ziel

Dieser Abschnitt fixiert die Markdown-Körperstruktur jedes `index.md` und den vollständig
deterministischen Lebenszyklus item-lokaler Acceptance-Criteria (`AC-NNN`), damit Parser,
Writer und Migrationswerkzeuge dieselbe, eindeutige Interpretation jeder Datei teilen.

### 11.2 Geltungsbereich

Gilt für den Markdown-Körper (nach dem YAML-Frontmatter, siehe
`docs/pipeline/issue-yaml-profile.md`) jeder `issues/XXXX[/XXXX-YY[.ZZ]]/index.md`-Datei, auf
allen drei Ebenen (Feature/Task/Subtask).

### 11.3 Normative Abschnitte

Genau vier Überschriften der Ebene `##` sind **normativ** und müssen, sofern für die Ebene
zutreffend, in dieser Reihenfolge erscheinen:

1. `## Goal` — ein bis wenige Sätze, das Ziel des Items.
2. `## Scope` — was eingeschlossen/ausgeschlossen ist.
3. `## Acceptance criteria` — die Liste der `AC-NNN`-Einträge (siehe §11.4).
4. `## Definition of Done` — Abschlussbedingungen.

Alle anderen Überschriften (`## Findings`, `## History`, `## Decisions`, `## Progress`, etc.)
sind **informativ** und müssen strukturell von den vier normativen Abschnitten getrennt
bleiben — typischerweise nach `## Definition of Done`. Ein Parser darf informative
Abschnitte niemals als Quelle für normative Felder (Scope, Kriterien, DoD) heranziehen.

### 11.4 Acceptance-Criteria (`AC-NNN`) — Lebenszyklus

Jedes Kriterium besitzt eine item-lokale, **unveränderliche** ID der Form `AC-NNN` (3-stellig,
z. B. `AC-001`), formatiert als:

```markdown
- **AC-001** Der Parser lehnt doppelte Frontmatter-Schlüssel hart ab.
```

Regeln:

- **Allokation:** Append-only. Die nächste neue ID ist stets `max(vorhandene AC-NNN) + 1`;
  IDs werden niemals wiederverwendet, auch nicht nach Zurückziehung.
- **Keine Umnummerierung:** Bestehende IDs ändern sich nie, unabhängig von Sortierung,
  Löschungen anderer Kriterien oder Formatierungsänderungen.
- **Zurückziehung (Tombstone):** Ein zurückgezogenes Kriterium wird nicht gelöscht, sondern
  als Tombstone erhalten:
  ```markdown
  - **AC-002** ~~Der Writer validiert Zeilenlängen.~~ (zurückgezogen, 2026-08-16: keine
    Zeilenlängenbeschränkung im finalen Profil)
  ```
- **Bedeutungserhaltende Bearbeitung:** Eine Textkorrektur, die Absicht und
  Verifikationsmethode unverändert lässt (Tippfehler, Klarheit), behält dieselbe ID.
- **Supersession (neue ID):** Ändert sich Absicht oder Verifikationsmethode, wird das alte
  Kriterium als Tombstone erhalten und ein neues mit der nächsten freien ID angelegt, das auf
  das alte per `supersedes: AC-NNN` verweist:
  ```markdown
  - **AC-002** ~~...~~ (ersetzt durch AC-005, 2026-08-16: Verifikationsmethode geändert)
  - **AC-005** Der Parser meldet einen Zeilenlängen-Warnhinweis statt Ablehnung.
    (supersedes: AC-002)
  ```
- **Verschiebung (neue ID + `derived-from`):** Wird ein Kriterium auf ein anderes Item
  verschoben, erhält es dort eine neue ID mit `derived-from: <item-id>#AC-NNN`; am
  Ursprungsort bleibt ein Tombstone mit Verweis auf die neue Adresse.

### 11.5 Kanonische Kriterien-Referenzen

Eine Referenz auf ein Kriterium eines anderen Items lautet immer `<item-id>#AC-NNN`
(z. B. `0037-02.01#AC-003`); eine Referenz innerhalb desselben Items lautet einfach
`AC-NNN`. Referenzen sind niemals Freitext-Beschreibungen des Kriteriums.

### 11.6 Einfügen/Löschen/Verschieben/Text-Bearbeitung — Algorithmus

1. **Einfügen:** Neue ID = `max(vorhandene AC-NNN im Item) + 1`; angehängt an das Ende der
   `## Acceptance criteria`-Liste (Position in der Liste hat keine semantische Bedeutung;
   Reihenfolge ist chronologisch, nicht priorisiert).
2. **Bedeutungserhaltende Bearbeitung:** Text am Ort ersetzt, ID unverändert, kein neuer
   Eintrag.
3. **Löschen (= Zurückziehung):** Text wird durchgestrichen (`~~...~~`) und mit einem
   `(zurückgezogen, <Datum>: <Grund>)`-Suffix versehen; die Zeile bleibt an ihrer Position.
4. **Supersession:** Wie §11.4; alte Zeile bleibt als Tombstone, neue Zeile wird angehängt.
5. **Verschiebung:** Tombstone am Ursprungsitem, neuer Eintrag mit `derived-from` am
   Zielitem; beide Änderungen werden in einem einzigen atomaren Commit vorgenommen, niemals
   getrennt (sonst existiert zwischenzeitlich kein gültiger Owner des Kriteriums).

### 11.7 Quell-Locators

Jedes Kriterium kann optional einen `source:`-Locator tragen, der auf die Herkunft verweist
(z. B. `source: legacy-todo-md#L108` für migrierte Kriterien, oder `source: decision:0001`
für aus einer Decision abgeleitete Kriterien). Locators sind rein informativ und niemals
parser-kritisch.

### 11.8 Unicode-, Mehrzeilen- und Größenregeln

- Kriterientext ist UTF-8, NFC-normalisiert.
- Mehrzeiliger Kriterientext ist erlaubt; Folgezeilen werden um mindestens 2 Leerzeichen
  gegenüber dem `- **AC-NNN**`-Marker eingezogen (Markdown-Listenfortsetzung).
- Ein einzelnes Kriterium (Text plus optionale Tombstone-/Supersession-Anmerkung) überschreitet
  nicht 4 KiB; längere Inhalte gehören in `## Scope`/`## Definition of Done` oder eine
  `decisions/`-Datei, referenziert per `source:`.

### 11.9 Migrations-Zuordnung nach Legacy-Dokumentreihenfolge

Beim einmaligen Import aus `TODO.md`/`DONE.md` (Task `0037-06.01`ff.) werden Kriterien in der
Reihenfolge zugeordnet, in der sie in der Legacy-Datei erscheinen: das erste
**Acceptance-criteria**-Bullet eines Legacy-Tasks wird `AC-001`, das zweite `AC-002`, usw.,
unabhängig von etwaiger späterer Umsortierung im Quelldokument. Diese Zuordnung ist
deterministisch und einmalig; nach dem Import gelten ausschließlich die Regeln aus §11.4.

## 12. Offene Anschlusspunkte

- Vollständiges `issue-item@v1`-Format (restliche Felder): Task `0037-02.03`.
- Lifecycle-Zustände, Kriterien-Evidenz, Entscheidungen, Terminal-Records: Task `0037-03.01`.
- Vollständiges Claim-/Recovery-Protokoll über Worktrees/Clones: Task `0037-03.02`.
- Provenienz-/Artefaktmodell: Task `0037-04`, `0037-04.01`, `0037-04.02`.
- Source/Derived-Matrix und Regenerierungs-DAG: Task `0037-05`.
- Migrations-/Cutover-Mechanik: Task `0037-06`, `0037-06.01`–`.03`.
