# Entscheidungsdatensätze (`decision-record@v1`)

**Status:** Normativ für prozessrelevante Entscheidungen im eigenen
Entwicklungsprozess dieses Repositories.

**Anforderungsbasis:** `RQ-DEC-01` … `RQ-DEC-05` aus
[`../dossiers/re-intake-evidence-traceability-and-roles.md`](../dossiers/re-intake-evidence-traceability-and-roles.md).

**Geltungsgrenze:** Dieses Dokument definiert ein Markdown-Arbeitsprodukt und
seine Auslöseschwelle. Es implementiert keinen Validator, verleiht keine
Autorität und ersetzt weder Task-Abnahme noch Integrationsverdikt.

## 1. Normative Begriffe

Die Schlüsselwörter **MUSS**, **DARF NICHT**, **SOLL** und **DARF** sind
normativ. Ein Datensatz ist genau dann `decision-record@v1`-konform, wenn seine
Felder und Unterfelder in der Reihenfolge und mit der Kardinalität aus Abschnitt
3 vorliegen und die semantischen Regeln dieses Dokuments erfüllen.

Ein Entscheidungsdatensatz hält fest, **wer** unter **welcher Autorität** zu
**welchem Zeitpunkt** welche prozessrelevante Entscheidung getroffen hat, warum
sie getroffen wurde, welche Alternativen betrachtet wurden und welche
Arbeitseinheiten oder Tore davon betroffen sind. Er ist keine nachträgliche
Erfolgserzählung: Er SOLL vor Umsetzung der Entscheidung entstehen, spätestens
aber bevor ein davon betroffenes Tor passiert wird.

## 2. Wann ein Datensatz verpflichtend ist

Eine Entscheidung MUSS als `decision-record@v1` festgehalten werden, sobald
mindestens einer der folgenden Trigger zutrifft. Unter **Triggers** wird jeder
zutreffende Wert aus dieser geschlossenen Liste aufgeführt:

| Triggerwert | Verpflichtendes Kriterium |
|---|---|
| `cross-item-blast-radius` | Die Entscheidung kann Start, Validierung, Abnahme, Integration, Veröffentlichung oder Abschluss mindestens einer **anderen** Arbeitseinheit blockieren oder deren Vertrag verändern. Das gilt unabhängig davon, ob der entscheidende Knoten als Integrationscheckpoint markiert ist. |
| `authority-tailoring-or-waiver` | Eine Rollen-, Unabhängigkeits-, Zuständigkeits-, Freigabe- oder sonstige Autoritätsregel wird zugeschnitten, zusammengelegt, ausgesetzt, übersteuert oder mit einem Waiver versehen. |
| `material-architecture-or-repository-behavior` | Es wird zwischen materiell verschiedenen Architekturen gewählt oder repository-weites Verhalten, eine kanonische oder geteilte Schnittstelle, ein persistiertes oder Grenzen überschreitendes Datenformat oder eine dauerhafte Prozessregel festgelegt. Rein task-lokale Zwischenformen ohne persistierte, geteilte oder grenzüberschreitende Wirkung lösen diesen Trigger nicht aus. |
| `irreversible-or-external-effect` | Die Entscheidung löst eine irreversible Migration/Löschung oder eine Wirkung außerhalb des isolierten Arbeitsbaums aus. |
| `security-or-credential-boundary` | Sicherheitsgrenzen, Zugangsdaten, Signaturen, Identitätsprüfung, Berechtigungen oder Geheimnishandhabung werden festgelegt oder verändert. |
| `public-release` | Eine öffentliche Veröffentlichung, Auslieferung oder deren Freigabebedingungen werden entschieden. |
| `material-risk-decision` | Ein materielles technisches, betriebliches, Datenschutz-, Sicherheits-, Safety-, Rechts- oder Restrisiko wird angenommen, abgelehnt, verschoben oder kompensiert. |

Die Trigger sind **alternativ**, nicht kumulativ: Ein einziger Treffer genügt.
Insbesondere ist `cross-item-blast-radius` das normative Reichweitenkriterium aus
TK-2. Schwierigkeit, Neuheit, Zeitaufwand, Privileg oder eine grüne Validierung
sind für sich allein weder Trigger noch Befreiung.

Kein Datensatz ist erforderlich, wenn **kein** Trigger zutrifft. Typische
Negativfälle stehen in Abschnitt 8. Wer einen Pflichtfall als lokalen
Implementierungsdetailfall einstuft, obwohl er fremde Einheiten oder Tore
beeinflussen kann, verstößt gegen TK-2.

## 3. Kanonisches Markdown-Format

### 3.1 Lexikalische und semantische Regeln

- **Stable ID:** `DEC-` plus vier Dezimalziffern, Bindestrich und drei
  Dezimalziffern; regulärer Ausdruck `^DEC-[0-9]{4}-[0-9]{3}$`. Die ID ist im
  Repository eindeutig, wird nie wiederverwendet und bleibt bei Korrektur,
  Verschiebung oder Ablösung unverändert.
- **Zeitpunkt:** vollständiger ISO-8601-Zeitpunkt mit Sekunden und Zeitzone;
  zulässig ist die RFC-3339-Teilmenge `YYYY-MM-DDTHH:MM:SS`, optional gefolgt
  von `.fraction`, und abschließend `Z`, `+HH:MM` oder `-HH:MM`. Datum, Uhrzeit
  und Offset müssen semantisch gültig sein. Ein lokaler Zeitpunkt ohne Offset
  ist ungültig.
- **Identität:** ein unveränderlicher Session-Token oder eine stabile Referenz
  auf eine registrierte menschliche/organisatorische Autorität. Genau eine der
  folgenden vollständigen Grammatiken ist zulässig:
  - Agent/Session:
    `^agent:[A-Za-z0-9][A-Za-z0-9._-]*(?::[A-Za-z0-9][A-Za-z0-9._-]*){2,}$`;
  - registrierte Autorität:
    `^authority:[A-Za-z0-9][A-Za-z0-9._-]*(?::[A-Za-z0-9][A-Za-z0-9._-]*)+$`;
  - additive historische Autoritätsreferenz:
    `^legacy-authority:[A-Za-z0-9][A-Za-z0-9._-]*(?::[A-Za-z0-9][A-Za-z0-9._-]*)+$`.
  Jede durch Doppelpunkt getrennte Payload-Komponente beginnt alphanumerisch
  und enthält danach nur ASCII-Buchstaben, Ziffern, Punkt, Unterstrich oder
  Bindestrich. Leere Komponenten, Leerraum, `/`, `\\`, `#`, `..` als eigene
  Komponente und pfadähnliche Relativsegmente sind damit unzulässig. Die
  Agent-Grammatik erlaubt die aktuellen Owner-Token-Formen einschließlich
  Task-/Subtask-ID und beliebiger kollisionsresistenter Request-ID. Anzeigenamen,
  Modellnamen, „aktueller Benutzer“, „privileged“ oder eine Git-Autorenzeile
  allein sind keine Identität.
- **Rolle:** genau einer der Werte `Requirements Engineer`, `Architekt`,
  `Implementierer`, `Integrator`, `QA-Manager`, `Management` oder eine
  Spezialistenrolle nach
  `^registered specialist:[a-z0-9][a-z0-9._-]*$`. Die stabile Rollen-ID ist
  nicht leer, enthält keinen Leerraum oder Pfadtrenner und beginnt mit einer
  ASCII-Kleinbuchstaben- oder Ziffernkomponente.
- **Autoritätsreferenz:** stabile ID oder Pfad-und-Anker-Referenz auf Auftrag,
  Zuweisung, Richtlinie oder registrierte Autorität. Eine Fähigkeitsklasse oder
  selbst behauptete Rolle ist keine Autoritätsreferenz.
- **Referenzen auf Arbeitseinheiten:** `feature:<ID>`, `task:<ID>`,
  `subtask:<ID>`, `path:<repository-relative-path>`, `repository:<name>` oder
  `external:<stable-id>`. Mindestens ein Eintrag ist erforderlich; `none` ist nur
  zulässig, wenn die Entscheidung trotz Pflichttrigger nachweislich keiner
  einzelnen Arbeitseinheit zugeordnet werden kann.
- **Torreferenzen:** `task-start:<ID>`, `validation:<stable-id-or-path>`,
  `integration:<ID>`, `feature-closure:<ID>`, `release:<stable-id>`,
  `external:<stable-id>` oder der alleinige Wert `none`.
- Freitextfelder sind nicht leer und enthalten keine Platzhalter wie `TBD`,
  `unknown` oder `n/a`. Eine tatsächlich fehlende menschliche Entscheidung wird
  als Nichtkonformität festgehalten, nicht erfunden.

### 3.2 Pflichtfelder und Reihenfolge

Ein Datensatz verwendet exakt diese Struktur. Listen-IDs beginnen bei `01`, sind
innerhalb ihrer Liste lückenlos und werden nicht umnummeriert:

```markdown
### `DEC-1234-001` — <kurzer Titel>

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-18T12:34:56+02:00`
- **Deciding identity:** `agent:<immutable-session-token>`
- **Role:** `Architekt`
- **Authority reference:** `<stable authority reference>`
- **Subject:** <eindeutig abgegrenzter Entscheidungsgegenstand>
- **Decision:** <getroffene Entscheidung>
- **Technical justification:** <technische/fachliche Begründung>
- **Triggers:**
  - `cross-item-blast-radius`
- **Considered alternatives:**
  - **ALT-01:** <Alternative>
    - **Disposition:** `selected`
    - **Reason:** <Grund>
  - **ALT-02:** <Alternative>
    - **Disposition:** `rejected`
    - **Reason:** <Grund>
- **Consequences:**
  - **CON-01:** <positive, negative oder neutrale Folge>
- **Affected work units:**
  - `task:1234-01`
- **Affected gates:**
  - `validation:_src/validate.py`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `authority:<immutable-authority-id>`
    - **Role:** `registered specialist:<stable-role-id>`
    - **Participation:** `consulted`
    - **Position:** `supports`
    - **Note:** <nichtleere Zusammenfassung>
- **Waiver:** `none`
```

Dabei gelten folgende Kardinalitäten:

- `Record format` bis `Technical justification` kommen genau einmal vor.
- `Triggers` enthält mindestens einen eindeutigen Wert aus Abschnitt 2.
- `Considered alternatives` enthält mindestens zwei Alternativen. Genau eine
  trägt `selected`; jede weitere trägt `rejected` oder `deferred`. Jede
  Alternative hat genau eine nichtleere Begründung.
- `Consequences` enthält mindestens einen Eintrag. Auch Kosten, Bindungen,
  Rückrollgrenzen und bewusst verbleibende Risiken werden genannt.
- `Affected work units` und `Affected gates` enthalten jeweils mindestens einen
  Eintrag nach Abschnitt 3.1; `none` darf nicht mit weiteren Einträgen gemischt
  werden.
- `Review participation` enthält entweder mindestens einen `PART-NN`-Block oder
  exakt den Wert `none`. Bei `none` folgt unmittelbar das Pflichtfeld
  `No-review reason`. Beteiligungswerte sind `consulted`, `reviewed` oder
  `dissented`; Positionswerte sind `supports`, `opposes` oder `no-position`.
  Die entscheidende Instanz darf zusätzlich als Teilnehmer erscheinen, ersetzt
  aber keine verfügbare zweite Instanz.
- `Waiver` ist entweder `none` oder der Block aus Abschnitt 4.

Dieses Format verlangt dokumentierte Beteiligung, aber nicht automatisch ein
positives Review. Dissens bleibt sichtbar; fehlende zweite Instanz wird offen
mit `Review participation: none` und Begründung festgehalten.

## 4. Autoritätszuschnitt und Waiver

Jeder Autoritätszuschnitt und jeder Waiver löst
`authority-tailoring-or-waiver` aus. Ein begrenzter Waiver ersetzt die letzte
Zeile des Grundformats durch exakt diesen Block:

```markdown
- **Waiver:** `bounded`
  - **Conflict:** <welche Rollen-, Unabhängigkeits- oder Autoritätsregel kollidiert>
  - **Reason:** <warum der Waiver erforderlich ist>
  - **Scope:** <abschließend benannte Arbeitseinheiten, Handlungen und Tore>
  - **Duration:** `from <ISO-8601 timestamp with timezone> until <ISO-8601 timestamp with timezone>`
  - **Compensating controls:**
    - **CTRL-01:** <Kontrolle>
```

Statt des Endzeitpunkts ist `event:<stable-reference>` zulässig. Beginn und Ende
müssen eindeutig sein; `indefinite`, ein fehlendes Ende und eine nur implizite
Task-/Feature-Laufzeit sind ungültig. `Compensating controls` enthält mindestens
einen Eintrag. Konflikt, Grund, Geltungsbereich, Dauer und kompensierende
Kontrollen sind unabhängig voneinander verpflichtend. Nur die zuständige
Management- oder registrierte Autorität darf fehlende Waiver-Angaben ergänzen;
ein Implementierer darf sie nicht ableiten oder erfinden.

## 5. Append-only-Historie und Korrekturen

Veröffentlichte Datensätze werden nicht umgeschrieben, gelöscht oder still
„bereinigt“. Eine Korrektur behebt einen Aufzeichnungsfehler; eine später anders
getroffene Sachentscheidung ist dagegen ein **neuer** `DEC-…`-Datensatz, der den
früheren Datensatz unter `Subject`, `Technical justification` und
`Consequences` referenziert.

Eine Korrektur wird unmittelbar nach dem bisherigen Datensatz oder seinen
vorherigen Korrekturereignissen angehängt. Jedes Ereignis ändert genau ein Feld,
damit Reihenfolge und wirksamer Wert deterministisch sind:

````markdown
#### `DEC-1234-001-C001`

- **Event format:** `decision-record-correction@v1`
- **Target record:** `DEC-1234-001`
- **Recorded at:** `2026-08-18T13:00:00+02:00`
- **Correcting identity:** `agent:example:architect:1234-01:session-a1`
- **Role:** `Architekt`
- **Authority reference:** `<stable authority reference>`
- **Correction reason:** <welcher Aufzeichnungsfehler berichtigt wird>
- **Target field:** `Technical justification`
- **Previous effective block SHA-256:** `<64 lowercase hexadecimal digits>`
- **Replacement block:**
  ```markdown
  - **Technical justification:** <vollständiger neuer Feldblock>
  ```
````

Ereignis-IDs folgen `^DEC-[0-9]{4}-[0-9]{3}-C[0-9]{3}$`, beginnen bei `C001`
und sind je Datensatz lückenlos. `Target field` bezeichnet genau ein
Top-Level-Feld des Grundformats. Eine Änderung eines Unterfelds ersetzt daher
den vollständigen umschließenden Top-Level-Block, zum Beispiel den ganzen
`Waiver`- oder `Considered alternatives`-Block. Mehrere Top-Level-Feldänderungen
erfordern mehrere Ereignisse.

Die Digest-Präimagedefinition ist exakt:

1. Der Datensatz liegt als UTF-8 ohne BOM mit ausschließlich LF (`0x0a`) als
   Zeilenende vor. Für den Digest findet **keine** Unicode-, Leerraum-,
   Zeilenende-, Einrückungs- oder Markdown-Normalisierung statt.
2. Der Feldblock beginnt beim ersten Byte `-` der Top-Level-Zeile
   `- **<Target field>:**` in Spalte 1. Label, Doppelpunkt, Markdown-Markierung,
   Leerzeichen und jede Einrückung sind Teil der Präimage.
3. Der Feldblock endet unmittelbar nach dem LF der letzten zum Feld gehörenden
   physischen Zeile. Zum Feld gehören nach der Labelzeile nur nichtleere
   Fortsetzungs- oder Kindzeilen mit mindestens zwei führenden ASCII-Leerzeichen.
   Die erste leere Zeile, die nächste Zeile in Spalte 1 mit `- **`, die nächste
   Überschrift oder das Dateiende beendet den Block und gehört nicht dazu. Eine
   trennende Leerzeile vor Überschrift oder Korrekturereignis ist daher niemals
   Teil der Präimage. Die Präimage enthält das terminierende LF der letzten
   eingeschlossenen Zeile.
4. Für ein skalares Feld umfasst die Präimage damit die Labelzeile, alle
   eingerückten physischen Fortsetzungszeilen und deren terminierendes LF. Für
   ein Listenfeld umfasst sie zusätzlich alle Listeneinträge und Nachkommen mit
   ihrer originalen Einrückung bis zur vorgenannten Blockgrenze.
5. `Previous effective block SHA-256` ist SHA-256 genau dieser Bytefolge. Nach
   einer früheren Korrektur ist die Präimage der wirksame `Replacement block`
   jener Korrektur, nicht der historische Ursprungsblock.
6. Der innere `markdown`-Fence unter `Replacement block` ist nur Transport. Die
   wirksamen Ersatzbytes beginnen beim ersten `-` der enthaltenen Feldzeile und
   enden mit genau einem LF unmittelbar vor dem schließenden Fence; Fence,
   dessen Einrückung und die zwei Transport-Leerzeichen vor den dargestellten
   Zeilen gehören nicht zur Ersatzbytefolge. Der deindentierte Ersatzblock MUSS
   mit demselben Top-Level-Label beginnen und die Regeln 2–4 erfüllen.

Der Digest verhindert das Anwenden auf eine überholte Historie. Kein Ereignis
darf ID, ursprünglichen Zeitpunkt oder ursprüngliche entscheidende Identität
unsichtbar machen; deren fehlerhafte Erfassung kann nur durch einen sichtbaren
Korrektureintrag berichtigt werden.

## 6. Additive Abbildung strukturell abweichender Bestandsdatensätze

Ein historischer Datensatz, der nicht exakt Abschnitt 3 entspricht, bleibt
**strukturell nicht konform**, auch wenn seine Semantik vollständig rekonstruierbar
ist. Weder Original plus Freitext noch Original plus Map werden dadurch zu einem
`decision-record@v1`. Für die explizite, maschinenlesbare Abweichungsdisposition
gilt das getrennte Format `decision-record-legacy-map@v1`:

````markdown
#### `DEC-1234-001-LM001`

- **Map format:** `decision-record-legacy-map@v1`
- **Target record:** `DEC-1234-001`
- **Source path:** `docs/path/file.md#stable-heading`
- **Map recorded at:** `2026-08-18T14:00:00Z`
- **Mapping identity:** `agent:example:implementer:1234-01:session-b2`
- **Mapping role:** `Implementierer`
- **Mapping authority reference:** `task:1234-01`
- **Structural disposition:** `legacy-structurally-nonconforming`
- **Semantic disposition:** `complete`
- **Missing semantic fields:** `none`
- **Deviation:** <warum das historische Layout nicht v1-parsebar ist>
- **Semantic projection JSON:**
  ```json
  {"recorded_at":"2026-08-18T12:00:00Z","deciding_identity":"legacy-authority:example:review:2026-08-18T12.00.00Z","role":"Management","authority_reference":"RQ-EXAMPLE-01","subject":"<text>","decision":"<text>","technical_justification":"<text>","triggers":["material-architecture-or-repository-behavior"],"considered_alternatives":[{"id":"ALT-01","text":"<text>","disposition":"selected","reason":"<text>"},{"id":"ALT-02","text":"<text>","disposition":"rejected","reason":"<text>"}],"consequences":[{"id":"CON-01","text":"<text>"}],"affected_work_units":["task:1234-01"],"affected_gates":["none"],"review_participation":[{"id":"PART-01","identity":"agent:example:reviewer:1234-01:session-c3","role":"Requirements Engineer","participation":"consulted","position":"supports","note":"<text>"}],"no_review_reason":null,"waiver":{"type":"none"}}
  ```
- **Source bindings JSON:**
  ```json
  {"recorded_at":["legacy:Zeitpunkt"],"deciding_identity":["additive:historical-authority-anchor"],"role":["additive:recorded-management-context"],"authority_reference":["legacy:review-context"],"subject":["legacy:Gegenstand"],"decision":["legacy:Entscheidung"],"technical_justification":["legacy:Fachliche Rechtfertigung"],"triggers":["additive:trigger-classification"],"considered_alternatives":["legacy:Gegenstand","legacy:Fachliche Rechtfertigung"],"consequences":["legacy:Folge"],"affected_work_units":["additive:scope-classification"],"affected_gates":["additive:gate-classification"],"review_participation":["legacy:review-context"],"no_review_reason":["additive:not-applicable"],"waiver":["additive:none"]}
  ```
````

Map-IDs folgen `^DEC-[0-9]{4}-[0-9]{3}-LM[0-9]{3}$` und sind je Ziel lückenlos.
Die Feldreihenfolge ist exakt wie im Muster. `Source path` ist ein nichtleerer,
repository-relativer Markdown-Pfad mit Anker, ohne Leerraum, `..`, absoluten
Pfad oder Backslash. Beide Fence-Inhalte sind RFC-8259-JSON ohne doppelte
Schlüssel. Die Projektion besitzt exakt die im Muster gezeigten Schlüssel und
verwendet die Feldsemantik aus Abschnitten 2–4; `Source bindings JSON` besitzt
exakt dieselben Schlüssel und je Schlüssel ein nichtleeres Array aus
`legacy:<exact-field-label-or-stable-source-anchor>` oder
`additive:<stable-reason-id>`. Der Payload ist jeweils eine nichtleere
Einzeilen-Zeichenfolge ohne führenden/nachlaufenden Leerraum; `legacy:` benennt
ein wörtliches Legacy-Feldlabel oder einen stabilen Abschnittsanker,
`additive:` einen stabilen Grund für die ergänzte Klassifikation.

`Semantic disposition: complete` verlangt `Missing semantic fields: none`,
keinen `null`-Wert in einem semantisch verpflichtenden Feld und eine vollständig
v1-validierbare Projektion. Bei `incomplete` enthält `Missing semantic fields`
eine komma-separierte Liste kanonischer Feldpfade, und genau diese Werte stehen
in der Projektion auf `null`; alle übrigen Felder bleiben vollständig. Ein
fehlender Waiver-Endpunkt wird als `Waiver.Duration` benannt. Die Map ist eine
Deviation-/Migrationsspur, keine Korrektur und keine nachträgliche Entscheidung.
Ein tatsächlich migrierter v1-Datensatz benötigt eine neue append-only
Aufzeichnung unter zuständiger Autorität und darf das historische Original
nicht ersetzen.

## 7. Abnahme und Integrationsverdikt sind spezialisierte Formate

Ein `Acceptance: ✓`-Datensatz nach
[`task-acceptance.md`](task-acceptance.md) ist ein spezialisiertes Format für die
Abnahme einer exakt gebundenen Arbeitsprodukt-Baseline. Ein `[u]`-Integrationsverdikt
nach [`branch-workflow.md`](branch-workflow.md) ist ein spezialisiertes Format für
einen blockierten Integrationscheckpoint. Beide sind **keine**
`decision-record@v1`-Datensätze und werden nicht in dieses Layout umgeschrieben.
Ihre eigenen Autoritäts-, Identitäts-, Zeit- und Append-only-Regeln bleiben
maßgeblich.

Die Spezialisierung befreit jedoch nicht von TK-2: Beruht Abnahme oder Verdikt
auf einer Architekturwahl, einem Autoritätswaiver, einer Sicherheits-/Release-
oder materiellen Risikoentscheidung, MUSS dafür ein separater `DEC-…`-Datensatz
existieren. Der Acceptance-Datensatz verweist ihn in seiner
`Authority reference` oder in der gebundenen Review-Evidenz; das
Integrationsverdikt verweist ihn im Feld `Reason` oder in seiner append-only
Auflösung. Ein Reviewresultat allein erteilt keine fehlende Fachautorität.

## 8. Durchgearbeitete Beispiele

Die IDs `DEC-9000-901` … `DEC-9000-903` sind ausschließlich didaktische,
nicht registrierte Beispiele.

### Positiv 1 — repository-weites Validierungstor

```markdown
### `DEC-9000-901` — Hostskripte erhalten ein getrenntes Validierungsprofil

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-18T09:15:00Z`
- **Deciding identity:** `agent:example:architect:9000-01:session-a1`
- **Role:** `Architekt`
- **Authority reference:** `task:9000-01`
- **Subject:** Geltungsbereich eines blockierenden Skriptprüfers
- **Decision:** Hostseitige Privilegskripte werden nicht durch das sandboxinterne Standardprofil blockiert, sondern durch ein eigenes gleichwertiges Profil geprüft.
- **Technical justification:** Host- und Sandboxskripte haben verschiedene Vertrauens- und Ausführungsgrenzen; ein gemeinsames Tor erzeugt repo-weite Blockaden ohne passende Reparaturautorität.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
  - `security-or-credential-boundary`
- **Considered alternatives:**
  - **ALT-01:** Getrennte Profile mit gemeinsamem Mindestvertrag
    - **Disposition:** `selected`
    - **Reason:** Erhält vollständige Prüfung und trennt Autoritätsgrenzen.
  - **ALT-02:** Alle Skripte durch dasselbe Profil blockieren
    - **Disposition:** `rejected`
    - **Reason:** Ein Befund an Hostinfrastruktur könnte jede fremde Task sperren.
- **Consequences:**
  - **CON-01:** Beide Profile müssen vor Feature-Abschluss grün sein.
  - **CON-02:** Das Standardtor kann keine Hostdatei allein wegen sandboxfremder Regeln blockieren.
- **Affected work units:**
  - `repository:autodocs`
  - `task:9000-01`
- **Affected gates:**
  - `validation:_src/validate.py`
  - `feature-closure:9000`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `authority:example:security-owner-01`
    - **Role:** `registered specialist:security-owner`
    - **Participation:** `reviewed`
    - **Position:** `supports`
    - **Note:** Getrennte Profile schwächen die Hostprüfung nicht.
- **Waiver:** `none`
```

**Warum positiv:** Schon die mögliche Blockade fremder Tasks löst TK-2 aus; die
Sicherheitsgrenze und das repository-weite Verhalten sind zusätzliche Trigger.

### Positiv 2 — materiell verschiedene Architekturen

```markdown
### `DEC-9000-902` — Ein Datensatz pro Arbeitseinheit statt gemeinsamer Zustandsdatei

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-18T11:20:30+02:00`
- **Deciding identity:** `agent:example:architecture:9000-02:session-b2`
- **Role:** `Architekt`
- **Authority reference:** `feature:9000`
- **Subject:** Persistenzarchitektur für den Arbeitsstatus
- **Decision:** Jede Arbeitseinheit erhält einen eigenen Datensatz unter einem stabilen Pfad.
- **Technical justification:** Pfadisolation reduziert Mergekonflikte und erlaubt atomare Validierung je Einheit; eine gemeinsame Datei koppelt unabhängige Autoren.
- **Triggers:**
  - `material-architecture-or-repository-behavior`
  - `cross-item-blast-radius`
- **Considered alternatives:**
  - **ALT-01:** Ein Datensatz pro Arbeitseinheit
    - **Disposition:** `selected`
    - **Reason:** Isolierte Eigentümerschaft und deterministische Zusammenführung.
  - **ALT-02:** Eine repository-weite Zustandsdatei
    - **Disposition:** `rejected`
    - **Reason:** Konflikte und Teilaktualisierungen hätten Feature-übergreifende Wirkung.
  - **ALT-03:** Externer Datenbankdienst
    - **Disposition:** `deferred`
    - **Reason:** Zusätzliche Betriebs- und Zugangsdatenabhängigkeit ist für den aktuellen Umfang nicht gerechtfertigt.
- **Consequences:**
  - **CON-01:** Leser müssen mehrere Datensätze deterministisch aggregieren.
  - **CON-02:** Schreibtransaktionen bleiben auf eine Arbeitseinheit begrenzt.
- **Affected work units:**
  - `feature:9000`
  - `repository:autodocs`
- **Affected gates:**
  - `integration:9000`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:example:implementer:9000-02:session-c3`
    - **Role:** `Implementierer`
    - **Participation:** `consulted`
    - **Position:** `supports`
    - **Note:** Der isolierte Pfad ist mit den vorhandenen Dateitransaktionen umsetzbar.
- **Waiver:** `none`
```

**Warum positiv:** Die Alternativen unterscheiden Persistenz, Konfliktmodell und
Betrieb materiell; die Wahl prägt repository-weites Verhalten.

### Positiv 3 — zeitlich begrenzter Waiver für eine öffentliche Notfallfreigabe

```markdown
### `DEC-9000-903` — Vier-Augen-Konflikt für Notfallfreigabe begrenzt übersteuern

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-18T14:00:00Z`
- **Deciding identity:** `authority:example:management-on-call-07`
- **Role:** `Management`
- **Authority reference:** `authority:example:incident-INC-9000`
- **Subject:** Einmalige öffentliche Notfallfreigabe bei Ausfall der unabhängigen Instanz
- **Decision:** Der Implementierer darf genau Release 9.0.1 zusätzlich integrieren; die Signatur bleibt bei der registrierten Release-Autorität.
- **Technical justification:** Die Korrektur schließt eine aktive externe Sicherheitslücke; Warten bis zur Rückkehr des Integrators erhöht das dokumentierte Risiko.
- **Triggers:**
  - `authority-tailoring-or-waiver`
  - `irreversible-or-external-effect`
  - `security-or-credential-boundary`
  - `public-release`
  - `material-risk-decision`
- **Considered alternatives:**
  - **ALT-01:** Begrenzte Rollenübersteuerung mit unabhängiger Signatur und Nachprüfung
    - **Disposition:** `selected`
    - **Reason:** Minimiert Expositionsdauer ohne Signaturautorität zu übertragen.
  - **ALT-02:** Veröffentlichung bis zur Rückkehr des Integrators aufschieben
    - **Disposition:** `rejected`
    - **Reason:** Das externe Sicherheitsrisiko bleibt länger offen.
  - **ALT-03:** Signaturzugangsdaten an den Implementierer übertragen
    - **Disposition:** `rejected`
    - **Reason:** Würde eine zusätzliche Credential-Grenze ohne Not aufheben.
- **Consequences:**
  - **CON-01:** Release 9.0.1 wird extern sichtbar und ist nicht vollständig rückholbar.
  - **CON-02:** Eine unabhängige Nachprüfung ist vor dem nächsten Release zwingend.
- **Affected work units:**
  - `task:9000-03`
  - `external:release-9.0.1`
- **Affected gates:**
  - `integration:9000-03`
  - `release:9.0.1`
- **Review participation:** `none`
- **No-review reason:** Die unabhängige Integratorinstanz ist während des dokumentierten Incident-Zeitfensters nicht verfügbar.
- **Waiver:** `bounded`
  - **Conflict:** Implementierer und Integrator derselben Arbeitsprodukt-Baseline wären personenidentisch.
  - **Reason:** Aktive externe Sicherheitslücke bei nicht verfügbarer unabhängiger Instanz.
  - **Scope:** Ausschließlich Integration von task:9000-03 in release:9.0.1; keine Signatur- oder Credential-Autorität.
  - **Duration:** `from 2026-08-18T14:00:00Z until 2026-08-18T18:00:00Z`
  - **Compensating controls:**
    - **CTRL-01:** Die registrierte Release-Autorität prüft Manifest und signiert selbst.
    - **CTRL-02:** Eine unabhängige nachgelagerte Prüfung blockiert jedes Folgerelease.
```

**Warum positiv:** Der Datensatz ist bereits wegen des Waivers Pflicht; externe
Wirkung, Sicherheitsgrenze, öffentliche Freigabe und Risikoannahme verstärken
die Pflicht. Konflikt, Grund, Scope, Dauer und Kontrollen sind vollständig.

### Negativ 1 — lokale Helper-Wahl

Ein Implementierer wählt innerhalb von `task:9000-04` für eine neue private
Funktion eine Schleife statt einer lokalen Comprehension. Signatur, Ausgabe,
Laufzeitgrenze, persistiertes Format, fremde Pfade und alle Tore bleiben
unverändert. **Ergebnis:** kein Trigger, daher kein Entscheidungsdatensatz. Die
Wahl kann im normalen Review beurteilt werden. Würde daraus eine
repository-weite Stilregel oder ein fremde Tasks blockierendes Lint-Tor, träfe
hingegen `material-architecture-or-repository-behavior` beziehungsweise
`cross-item-blast-radius` zu.

### Negativ 2 — eindeutig bestimmte Tippfehler-/Linkreparatur

Ein Dokument verweist auf `task-aceptance.md`; im selben Verzeichnis existiert
nur `task-acceptance.md`, und alle benachbarten Verweise bestätigen dieses Ziel.
Die Reparatur ändert ausschließlich den defekten Link und keine Normsemantik.
**Ergebnis:** eindeutig bestimmte redaktionelle Reparatur, kein Trigger und kein
Entscheidungsdatensatz. Gibt es mehrere plausible Ziele oder ändert die Wahl den
normativen Prozess, ist sie nicht mehr eindeutig und wird erneut gegen Abschnitt
2 geprüft.

## 9. Prüfung in Prinzip

Ein späterer Validator kann ohne fachliche Heuristik mindestens prüfen:

1. eindeutige ID und geschlossene Feldreihenfolge;
2. gültigen ISO-8601-Zeitpunkt mit Zeitzone;
3. zulässige Identitätspräfixe, Rolle und Triggerwerte;
4. Listen-Kardinalität, lückenlose IDs und genau eine ausgewählte Alternative;
5. Referenzsyntax für Arbeitseinheiten und Tore;
6. vollständige Review- oder No-review-Variante;
7. bei `bounded` die fünf Waiver-Bestandteile einschließlich endlicher Dauer;
8. lückenlose Korrekturereignisse und Bindung an den vorher wirksamen Feldwert.

Ob eine technische Rechtfertigung sachlich trägt, eine Alternative wirklich
materiell ist oder eine angegebene Autorität zuständig war, bleibt Gegenstand
des Reviews. Maschinenprüfbarkeit der Form ist keine automatische Genehmigung.
