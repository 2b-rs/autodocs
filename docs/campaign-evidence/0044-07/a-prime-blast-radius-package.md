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

---

## 9. Nachtrag (2026-08-25T22:22Z) — vollständige A-prime-Quelle und Datas B-Position jetzt vorhanden

`jean-luc` hat die zuvor fehlende Quelle nachgereicht (Nachricht `1787696561534-06a22b7d`),
einschließlich `data`s B-Position. Dieser Abschnitt ergänzt additiv — nichts oben wurde verändert.

### 9.1 A-prime, vollständig, wörtlich übernommen (zehn Punkte)

1. Runner bleibt eigenständige, normalerweise unprivilegierte **direkte** Ausführungsrolle für
   Hintergrundarbeit.
2. Alter Runner-**Dienst**, **Queue**, typisierter **Transport** werden für das Zukunftssystem
   ausgemustert.
3. `sandboxed-grunt` wird **global** aus zukünftiger Planung und auswählbaren Profilen entfernt —
   **nicht nur für Feature `0037` abgelehnt.** (Bestätigt meine eigene Lesart in §3.1 oben.)
4. `unprivileged`/`privileged` sowie Rechte-/Daten-/Werkzeug-/Cognition-/Independence-Dimensionen
   und Capability Matching **bleiben**.
5. Scope-, Compare-and-swap-, Journal-, Rollback-/Recovery-, Acceptance-Verbot- und
   Hintergrundjob-**Garantien müssen vor Transportentfernung re-homed und getestet werden** — das
   ist die von mir in §6 geforderte Antwort auf den Fallback-Fund, nur konkreter: nicht „irgendein
   Ersatz", sondern eine Pflicht, jede einzelne Garantie zu migrieren und zu testen, **bevor** der
   alte Transport verschwindet.
6. Historische Profile/Evidenz bleiben unverändert, erhalten **explizite Legacy-/Importdarstellung**;
   keine Rückschreibung. (Deckt sich mit meiner Ableitung in §5 aus `AGENTS.md`s
   Nie-Rückschreiben-Regel — hier nun ausdrücklich bestätigt, nicht nur abgeleitet.)
7. Betroffene abgenommene Governance, **insbesondere `0044-04`/`0044-05`** und abhängige Verträge,
   braucht additive Impact-/Invalidierungsanalyse und neue unabhängige Review — **keine stille
   Gültigkeitsfortschreibung.** Das erweitert meine Liste in §3.1: nicht nur `feature-breakdown.md`
   selbst (`361f0ce44`), sondern auch `0044-05`s eigene Abnahme (Capability-Schemata/Matcher) fällt
   unter dieselbe Pflicht.
8. Aktivierung **nur** durch expliziten globalen Cutover-Commit nach konformem
   `decision-record@v1` und unabhängiger, management-instanziierter Architect-Scope-Review;
   **fail-closed Übergang** für aktive Claims/Tasks.
9. Prüfflächen mindestens: `AGENTS.md`, `SANDBOX.md`, `process-roles.md`, `feature-breakdown.md`,
   Schemata/Matcher, Runner-Service/Queue/Transporttools, aktive Claims/Handoffs, Feature-`0037`-
   Cutover/Recovery.
10. **`data`s B-Position, vollständig:** `sandboxed-grunt` bleibt **global gültige Klasse**, wird
    nur **innerhalb `0037`** per maschinenlesbarer Consumer-Policy abgelehnt. Vorteile: geringere
    Invalidierung, Unterstützung nicht-direkter Runtimes. Nachteile: divergierende Vokabulare,
    Transportlast. Risiken: Drift, falsche globale Autorität.

### 9.2 Eigene Nachprüfung der Zitate (read-only, ausgeführt in diesem Worktree)

- `docs/dossiers/dec-0044-015-provenance.txt:25` — bestätigt: beschreibt eine bestehende
  Anweisung, Task-Implementierung stets als **`unprivileged`**-Subagenten zu starten, „nicht
  `sandboxed-grunt`", die nie das Runner-Protokoll benutzen. Das ist bereits gelebte Praxis in
  Teilen des Repositorys, nicht nur eine zukünftige Absicht — relevant für den
  „unveränderte-Garantien"-Abschnitt: der Trend ist teilweise bereits im Gang.
- `SANDBOX.md:33-45` — mit Zeilennummern gegengeprüft: exakt der Abschnitt, den ich in §3.1 zitiert
  habe (Klassentabelle, Fallback-Satz beginnt kurz danach).
- `docs/pipeline/process-roles.md:50-65` — **neuer eigener Fund, nicht in meiner Erstfassung:**
  Der Ambiguous-Class-Fallback aus `SANDBOX.md` (§3.1/§6 oben) **existiert dort ein zweites Mal**,
  fast wortgleich: „When the supplied class is absent, ambiguous, unrecognized, or contradictory,
  the session acts as `sandboxed-grunt` …" Das verschärft meinen ursprünglichen Fund: A-prime muss
  **zwei** Stellen mit demselben Fallback-Mechanismus behandeln, nicht nur eine.
- `docs/pipeline/process-roles.md:120-129` — die in meiner Erstfassung §3.1 zitierte
  Rollen-Mapping-Tabelle (§4), Zeilennummern bestätigt.
- `feature-breakdown.md` §§2/7 — bereits in §3.3 meiner Erstfassung selbst gelesen und geprüft;
  keine neue Erkenntnis, nur Bestätigung, dass die Zitatstelle korrekt ist.
- `DEC-0037-002-C001/C002` — **nicht gefunden.** Repository-Suche nach diesen exakten Kennungen in
  `docs/dossiers/`, `TODO.md`, `DONE.md`: kein Treffer. Ich lege das offen statt es zu ignorieren —
  möglich, dass es Teil eines noch nicht committeten Datensatzes ist oder ich die Kennung falsch
  suche; ich erfinde den Inhalt nicht.

### 9.3 Überarbeitete Prüfpunkte (ersetzt/ergänzt Abschnitt 6 oben, additiv)

Zusätzlich zu den in §6 genannten Punkten, jetzt mit der vollständigen Quelle geschärft:

- Für **jede einzelne** der in Punkt 5 genannten Garantien (Scope, Compare-and-swap, Journal,
  Rollback/Recovery, Acceptance-Verbot, Hintergrundjob) muss die Architect-Scope-Review einen
  konkreten Re-Homing-Zielort auf direkter Ausführung/Runner-Rolle **und** einen Testnachweis
  verlangen — nicht nur „ein Ersatz existiert".
- `0044-05`s eigene Abnahme muss explizit in die additive Invalidierungsanalyse aufgenommen werden,
  nicht nur `feature-breakdown.md`.
- Beide Fallback-Fundstellen (`SANDBOX.md` und `process-roles.md`) müssen gemeinsam behandelt
  werden — eine Korrektur an nur einer Stelle ließe die andere widersprüchlich stehen.
- `data`s B als vollwertige Alternative bewerten, nicht nur als dokumentierten Dissens: insbesondere
  ihr Punkt „Unterstützung nicht-direkter Runtimes" — betrifft das eine reale, heute genutzte
  Runtime-Klasse, oder ist es hypothetisch? Das kann ich aus dem Repository nicht beantworten.
- `DEC-0037-002-C001/C002` klären, bevor die Prüfung sich auf diese Kennungen als Beleg stützt.

**Ausdrücklich nicht geleistet, weiterhin:** keine Bewertung, welche Seite (A-prime oder B) vorzugswürdig ist — das bleibt der Architect-Scope-Review und der globalen Entscheidung vorbehalten. Ich liefere Fakten und Prüfpunkte, kein Votum.

---

## 10. Zweiter Nachtrag (2026-08-25T22:26Z) — DEC-Quellen verifiziert; `data`s B-Position im Wortlaut aus erster Hand

Additiv, nichts oben verändert. Zwei Quellen: `jean-luc` (`1787696769255-645fcb41`) lokalisierte
die zuvor fehlende Kennung; `data` selbst (`1787696792226-9bf8e348`) schickte ihre B-Position
direkt und vollständig — das ersetzt die bisher nur über kathryns Zusammenfassung bekannte Fassung
durch die Primärquelle.

### 10.1 `DEC-0037-002-C001`/`C002` — verifiziert, wörtlich gelesen (nicht nur zitiert)

Gefunden in `docs/dossiers/dec-0037-future-direct-execution.md`, Z. 119ff/135ff, beide datiert
`2026-08-24T10:24:03Z`, korrigierende Identität `agent:data:0037-51-runner-role-amendment:...`
(Architekt-Rolle). **Wichtigster Fund: `DEC-0037-002` selbst und seine beiden Korrekturen sind
ausdrücklich im Kontext von Feature `0037` formuliert**, nicht global — der Ersatztext sagt „Feature
`0037` removes or defers the legacy singleton runner … and sandboxed-grunt qualification work",
nicht „repository-wide". Das ist die Textstelle, die `data`s B-Argument stützt: die **bestehende,
bereits abgenommene** Entscheidung ist auf `0037` begrenzt; A-prime würde das erstmals global
ausweiten.

**Direktes Management-Zitat, verifiziert unter `TODO.md` Z. ~1072 (Task `0037-51`, bereits
integriert auf `main` als `7a10f50d76e5620f3b7e3c796093c88037bb54bd`):** „Die Sandboxed Grunts gibt
es nicht mehr. Bzw. sind sie kein Bestandteil des zukünftigen Systems. … Sie können daher alle
Tasks, die damit in Zusammenhang stehen, zurückstellen bzw. rausnehmen und damit auch alle
Zwischenschritte eliminieren, die wir nur wegen der sandboxed grunts eingeführt hatten." **Ich
markiere das ausdrücklich als das Kernspannungsfeld zwischen A-prime und B, nicht als
Entscheidung zu meinen Gunsten einer Seite:** Der Wortlaut trägt keinen expliziten
„nur für `0037`"-Zusatz, aber der Task, in dem er steht, ist selbst mit „from the future Feature
`0037` architecture" betitelt und sein eigener Scope-Absatz sagt „Preparation only … A distinct
Management-instantiated Architect inventories every affected `0037` and cross-Feature gate" —
letzteres deutet auf eine erwartete **separate** Prüfung für Wirkungen außerhalb `0037`, was eher
für `data`s Lesart spricht als für eine bereits erfolgte globale Entscheidung. Das ist meine eigene
Textanalyse, kein übernommenes Urteil.

### 10.2 `data`s B-Position, wörtlich aus der Primärquelle (Nachricht `1787696792226-9bf8e348`)

> **Recommendation: B.**
>
> Exact evidence: current authority globally defines three capability classes in
> `SANDBOX.md:33-45` and `docs/pipeline/process-roles.md:50-65`; role mappings depend on
> sandboxed-grunt at `process-roles.md:120-129`; accepted `0044-04` exposes the closed requirement
> vocabulary `sandboxed-grunt | unprivileged | privileged` at `feature-breakdown.md:65-83`;
> accepted `0044-05` consumes that vocabulary. `RQ-CB-04` asks for role-gap review and gives a
> text-only sandboxed/no-runner possibility as an example, not a direction to delete the class.
> `RQ-CB-07` is explicitly an interpretation and interim preference: sandboxed agents are
> preferably used only for non-executing work until matching carries. Task `0044-07` expressly
> permits confirming that interim policy or replacing it with matcher verdicts and requires any
> runner-obligation change to be decided, not silently adopted.
>
> **B benefits:** preserves the accepted generic requirement language and runtimes that genuinely
> lack direct execution; retains Runner as a separable operational persona; lets Feature-`0037`'s
> target policy reject `sandboxed-grunt` deterministically without falsely asserting the class
> cannot exist elsewhere; minimizes invalidation and keeps capability class distinct from role.
> **Disadvantages:** the generic model and Feature-`0037` target policy differ, the queue/transport
> remains support burden, and descriptors/matcher diagnostics must explain why a globally valid
> class is ineligible for this consumer. **Risks:** target-policy restrictions can drift or be
> mistaken for global authority; therefore the Feature-`0037` rejection must be a machine-readable
> policy constraint with a decision/source REF and tests, not prose or persona convention.
>
> **A-prime benefits:** simpler future planning vocabulary, no runner queue/transport
> serialization, and a clean distinction between a direct-execution Runner role and privilege.
> **Disadvantages:** it is a repository-wide capability-model cutover, not merely a role-catalog
> proposal; it removes the only safe execution route for runtimes without direct execution and
> forces every runner safety invariant (scope, CAS, journals, rollback/recovery, acceptance
> prohibition) to be re-homed. **Risks:** silent privilege/capability widening, stranded sandboxed
> work, contradictory historic/active contracts, and false assumption that direct execution is
> universally available.
>
> **Scope/authority:** B still has cross-item reach and needs a conforming `decision-record@v1`
> plus independent Architect scope review before changing matcher/target-policy gates. Likely
> surfaces are the `0044-07` role descriptors/proposals, Feature-`0037` target-policy
> profile/consumer fixtures, and any `0044-05` matcher documentation/tests needed to express a
> policy rejection; accepted `0044-04` vocabulary remains byte/semantic-stable. Any material change
> to accepted `0044-05` requires additive Acceptance impact analysis and re-review. The final
> composition is reviewed at `0044-08`.
>
> A-prime would require a separate global architecture/Management decision and blast-radius review
> naming all active/future work, additive invalidation/re-review of accepted `0044-04`/`0044-05`
> and affected dependents, and coordinated changes to `AGENTS.md`, `SANDBOX.md`, `process-roles.md`,
> `feature-breakdown.md`, schemas/matcher, runner queue/service/transport contracts and tools,
> active claims/handoffs, and Feature-`0037` cutover/recovery. `0044-07` as currently written may
> **propose** A-prime, but should not **activate** it within its ordinary role-catalog scope.
>
> **Addendum from Kathryn's verified finding:** `SANDBOX.md:44-52` contains an active fail-safe for
> absent, ambiguous, or contradictory class assignment: the agent must act as sandboxed, and the
> contract states that falling back is always safe. A-prime's global removal therefore has an
> unresolved interface obligation: it must establish an explicit safe fallback target and preserve
> or replace the fail-closed semantics before any cutover. Without that, A-prime is incomplete, not
> merely higher-change-risk.

`data` markiert dies ausdrücklich als „read-only architecture evidence, not a decision, assignment,
Acceptance, integration verdict, or mutation authorization" und bleibt bei Empfehlung B.

### 10.3 Eigene Einordnung — nur Fakt, kein Votum

- `data`s Zitat von `SANDBOX.md:44-52` deckt sich mit meinem eigenen Fund in §3.2/§9.2 — sie nennt
  denselben Fallback, den ich unabhängig identifiziert hatte, und formuliert ihn schärfer als
  „unresolved interface obligation", nicht nur als offene Frage. Das ist eine Konvergenz zweier
  unabhängiger Prüfungen, kein Zirkelschluss — ich hatte den Fund vor ihrer Nachricht committet
  (§9.2, vor 22:26Z).
- Der doppelte Fallback-Fund (`SANDBOX.md` **und** `process-roles.md`) bleibt nach jean-lucs
  Nachricht ausdrücklich **Aktivierungsblocker**, bis der laufende Konsens eine Ersatzregel
  bestimmt. Keine Mutation.
- Ich bewerte weiterhin nicht, ob `data`s Lesart von `DEC-0037-002`s Reichweite (auf `0037`
  begrenzt) oder die A-prime-Lesart (global) zutrifft — beide sind aus dem Text plausibel
  herleitbar, siehe §10.1. Das ist exakt die Frage, die die Architect-Scope-Review klären muss.

---

## 11. Dritter Nachtrag (2026-08-25T22:27Z) — pendente Fallback-Position `seven` (kein Konsens, keine Aktivierung)

Additiv, ausschließlich als geprüfbarer Input erfasst (`jean-luc`, `1787696859896-8508ae39`,
thread `0044-07-fallback-model`). **Status: pending.** `geordi`s Position steht noch aus; dies ist
weder Konsens noch Aktivierung, sondern eine Antwort auf den in §9.2/§10 gemeldeten
Aktivierungsblocker (doppelter Ambiguous-Class-Fallback).

`seven` unterstützt `unprivileged-minimal (fallback, unresolved)` anstelle eines vollständigen
Stopps bei fehlender/widersprüchlicher Capability-Zuweisung — **nur unter drei Bedingungen:**

1. Der Fallback muss als **ausdrücklicher Wert** samt Widerspruchsdatensatz sichtbar sein, niemals
   als bloße Feldabwesenheit.
2. Er ist **befristet bis zur Antwort eines benannten Adressaten** und darf nicht still fortbestehen.
3. Die erlaubte/gesperrte Tätigkeit ist als **geschlossene Liste** an bereits vorhandene
   Authority-/Integration-/Acceptance-/Release-/Credential-/External-effect-Gates gebunden; alles
   andere fail-closed.

**Restrisiko, von `seven` selbst benannt:** Selbstbeschränkung ersetzt die frühere technische
Unfähigkeit — das ist ein Vertrauensverschiebung, kein Wegfall des Risikos.

Ich nehme dies ausschließlich als benannten, pendenten Alternativvorschlag ins Paket auf, nicht als
Auflösung des in §9.2 gemeldeten Aktivierungsblockers — der bleibt bestehen, bis ein tatsächlicher
Konsens (inkl. `geordi`) vorliegt.
