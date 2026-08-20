# Requirements-Analyse: Integrations-Policy, Architekturprozess und Capability-basiertes Task-Matching

**Status:** RE-Arbeitsprodukt. Informativ bis zur Umsetzung durch Feature `0044`.
**Erhoben:** 2026-08-20, Requirements-Engineer-Funktion nach `docs/pipeline/process-roles.md`.
**Anlass:** Der Kunde kann nicht nachvollziehen, woraus sich Architekturentscheidungen, Task-Abhängigkeiten und Testfälle speisen; die Integrations-Policy-Semantik ist ungeregelt; die Agentenauswahl je Aufgabe hat keine maschinenlesbare Grundlage.

## 1. Anforderung im Originalwortlaut (`RQ-SRC-04`)

Nachricht des Kunden (aktueller Benutzer), 2026-08-20, vollständig und unverändert:

> Ledger einchecken passt. Mach daraus gerne ein TODO-Feature. Vorher wollte ich noch einen Punkt mit dir besprechen, der mir bisschen unwohlsein bereitet. Ich weiß nicht, wie gut die Arhcitektur-, Requirements-Engineering- und Integrationsprozesse ausgestaltet sind. Die Kollegen machen zwar überwiegend sinnvolle Sachen, aber ich kann nicht nachvollziehen, woraus sich die Architekturentscheidungen speisen, woraus die Abhängigkeiten zwischen Tasks und Umfang und Art der Test cases abgeleitet werden. Zudem wäre es gut, wenn die Architektur Festlegungen darüber treffen könnte, welche "Arten" von Aufgaben es gibt, am besten über ein Konzept von Capabilities. Der Architekt könnte dann definieren, welche Capabilities ein Implementierer besitzen muss, während der Implementierer dann selbst checken kann, ob er die hat. Ich habe dazu einen Aufsatz verfasst. Bitte nimm die Infos auf und definiere noch ein Feature zur Prozessverbesserung. RE und Architektur wäre den Spezialisten zu überlassen, sofern du welche an der Hand hast. Hier also das Brainstorming:
>
> Zunächst einmal möchte ich zwei Dinge klarstellen: Bei der Integration ist immer die Policy des Branch maßgeblich, auf den integriert wird. Es sollte eine klare Festlegung dazu geben. Die Frage ist, ob man mit dem Fall, dass sich ein Change von B nach A nicht integrieren lässt, weil die Policy von A es nicht erlaubt; Hier brauchen wir eine Fallunterscheidung: Wenn die Policy von A es schon zum Branch-Zeitpunkt nicht erlaubt hätte B zu integrieren, dann ist das ein Planungsfehler des Feature-Breakdown-Verantwortlichen. D.h. wir müssen den entsprechenden Prozess so gestalten, dass das sicher verhindert wird. Wenn B sich dagegen nicht auf A integrieren lässt, weil sich die Policy auf A zwischenzeitlich geändert hat, dann ist das KEIN Planungsfehler, sondern etwas, das der Architekt nicht vorhersehen konnte. Auch hier muss wieder unterschieden werden: Ist der Fehler aufgetreten, weil die Implementierung in einer anderen Reihenfolge erfolgt ist als vom Architekten vorgesehen? -> Planungsfehler, müssen wir verhindern. Ist nachträglich ein Feature hinzugekommen oder eine Abweicherlaubnis erteilt worden und das ist der Grund? Kein Planungsfehler. Für solche Fällen soll der Integrator grundsätzlich die Möglichkeit haben eine Policy für die Integration zu ersetzen gegen eine beliebige andere, die jemals seit dem herausbranchen auf einem der beiden zu integrierenden Branches gültig war. Es ist Agenten nicht erlaubt auf einen Branch Policy-Änderungen zu committen, die auf einem anderen Branch entstanden sind als auf dem zu integrierenden oder dem Integrationsziel. Am Ende des langen Gedankengangs steht die Erkenntnis, dass Policy-Änderungen von dem Branch, auf den integriert werden soll, reingezogen werden dürfen. Das bitte ab sofort so handhaben und auch im Prozessmodell verankern.
>
> Integrationstests?
>
> Sollte auch dadurch die Rückintegration eines Branches nicht möglich sein, handelt es sich um eine Risikointegration. Diese kann der Integrator nach Review mit zwei weiteren Agenten - QA und Architekt - bei Einstimmigkeit genehmigen, und dafür auch Policies vorübergehend außer Kraft setzen. Bei nicht-Einstimmigkeit ist Eskalation und Entscheidung durch einen User erforderlich.
>
> 2\. Lass uns diskutieren, wie wir den Architekturprozess optimieren können. Aktuell ist mir nicht klar, wie die Instruktionen für Implementierer zustandekommen. Ich möchte, dass wir dem Featurebreakdown-Verantwortlichen (dem Architekten?) eine Prozessanweisung geben, oder sie, falls es sie schon gibt, verfeinern. Mir schwebt vor, dass er die Aufgaben grob danach bewerten soll, welche Skills ein Implementierer dafür braucht, damit der Orchestrator nachher den richtigen Agenten für die Aufgabe auswählen kann. Die Kriterien sollten beinhalten, welche Rechte, Daten und Fähigkeiten der Implementierer für seine Aufgabe braucht. Dann sollten wir ein Mapping dieser Anforderungen auf unsere Rollen haben. Der Orchestrator soll anhanddessen den richtigne Agenten auswählen können. Der Architekt soll das nciht direkt auswählen, weil zum Spezifikationszeitpunkt nicht klar ist, welche Modelle und Personae zum Umsetzungszeitpunkt im welchem Umfang zur Verfügung stehen, es handelt sich also um ein Scheduling-Problem, das wir nicht schon in der Architekturphase lösen. Manche Aufgaben können auch Zugriff auf besondere Daten benötigen, z.B. PGP-Schlüssel oder Daten außerhalb des git. Eine andere Dimension betrifft die kognitiven Fähigkeiten, die bei der Umsetzung benötigt werden. Ich habe keine Ahnung, wie ma die Anforderungen eines Umsetzungspakets an einen KI-Agenten sinnvoll abschätzen kann, unc ich möchte, dass du diese Frage im Projekt für mich beantwortest. Die Zuweisung von Tasks an Rollen sollte selbst keine KI benötigen, d.h. die Anforderungsprofile und die Fähigkeitsbeschreibungen der Agenten müssen maschinenlesbar sein, Ich möchte, dass du dir die bestehenden Rollen ansiehst und bei Lücken gern auch neue Rollen vorschlägst, die eine handhabbare Granularitätsebene bilden, dass man durch die gezielte Auswahl von Agenten für Umsetzungsaufgaben Tokens sparen oder Aufgaben parallelisieren kann. Die Sandbox-Agenten beispielsweise haben die Limitierung mit dem Runner-Protokoll. Falls ihre Tätigkeit aber lediglich Textänderungen sind, die keine Ausführung von Tools braucht, dann könnte man auf das Runner-Protokoll bei ihnen evtl. auch verzichten. Es könnte in Zukunft Agenten geben, die ein Token-Limit haben, also nur eine bestimmte Menge Text in einem Rutsch verarbeiten können. Sowohl diese Limits, als auch die Fähigkeiten eines Agenten können nichtdeterministisch sein und von der Vorhersage abweichen. Es kann daher sein, dass ein einem Agenten zugewiesener Job fehlschläg, weil der Agent schlicht überfordert ist. Im besten Fall kann der Agent das selbst erkennen und den Job flaggen; im ungünstigeren Fall liefert er aber einfach Mist und der Orchestrator muss die Ergebnisfähigkeit beitragen. einfach ihr Ergebnis  dass es einfacher ist Sandboxed-Agenten nur für Arbeiten zu verwenden, bei denen sie nichts ausführen müssen.  Während des Featurebreakdowns soll festgelegt werden, wie ein Branch vom Implementierer zu erstellen ist.
> Ich denke, dass an 0042 und 0019 gerade Integratoren arbeiten.
>
> Ein Koordinator hat mir vorhein gesagt:
> Feature `0039` remains open: reserved Tasks `0039-02`, `0039-03`, and `0039-05` remain `[u]`. This integration nonetheless makes `0039-01` available for evaluating `0040:0039-01`. Was hier also passiert ist ist, dass ein Architekt irgendwann mal festgelegt hat, dass das Feature 0040 von 0039-01 abhängig ist, aber nicht von den anderen. Die Features 0039-02ff sind also noch nicht erledigt. An Feature 0039 ist Data aber gerade ab arbeiten, ich gehe davon aus, dass er irgendwann abgeschlossen wird..
>
> `0019-02` is now complete, publication remains an SSH authorization failure even with the explicit key, and the `0040-03` corrective rework is complete. The reports disagree about `0039-01`, so I'm reconciling the authoritative backlog and canonical branches before deciding whether integration is permitted.

Redaktionelle Anmerkung: Ein Satz des Originals ist erkennbar verstümmelt
(„… einfach ihr Ergebnis  dass es einfacher ist Sandboxed-Agenten nur für
Arbeiten zu verwenden, bei denen sie nichts ausführen müssen."). Er wird
unverändert bewahrt; die RE-Lesart in `RQ-CB-06`/`RQ-CB-07` ist als
Interpretation gekennzeichnet und vom Kunden zu bestätigen.

## 2. Strukturierung

Die Nachricht enthält zwei Themenblöcke und Kontextnotizen:

- **Block A — Integrations-Policy-Semantik** (Klarstellung, „ab sofort so
  handhaben"): Präzedenz der Ziel-Branch-Policy, Fallunterscheidung
  Planungsfehler/nicht vorhersehbar, Policy-Ersetzung, Herkunftsverbot,
  Pull-in-Erlaubnis, Risikointegration, offene Frage „Integrationstests?".
- **Block B — Architekturprozess und Capabilities** (Diskussions- und
  Untersuchungsauftrag): Prozessanweisung für den Feature-Breakdown,
  Capability-Anforderungsprofile je Task, maschinenlesbares Matching durch den
  Orchestrator, Rollenüberprüfung, kognitive Abschätzung, Umgang mit
  Nichtdeterminismus.
- **Kontextnotizen** (nicht anforderungsbildend, als Lagebild bewahrt):
  Integratoren arbeiten an `0042` und `0019`; `0039` bleibt offen mit `[u]` auf
  `0039-02/03/05`, `0039-01` wird für das Gate `0040:0039-01` verfügbar;
  `0019-02` komplett, Publikation scheitert an SSH-Autorisierung; `0040-03`
  Nacharbeit komplett; Berichtslage zu `0039-01` widersprüchlich, Abgleich läuft.

### 2.1 Fallunterscheidung Integrations-Policy (Block A, normalisiert)

Change von `B` nach `A` nicht integrierbar, weil die Policy von `A` es nicht
erlaubt:

| Fall | Ursache | Bewertung | Konsequenz |
|---|---|---|---|
| A1 | Policy von `A` hätte die Integration schon zum Branch-Zeitpunkt nicht erlaubt | **Planungsfehler** des Feature-Breakdown-Verantwortlichen | Prozess muss das sicher verhindern (Prüfung bei Breakdown/Branch-Anlage) |
| A2 | Policy von `A` hat sich zwischenzeitlich geändert, weil in anderer Reihenfolge implementiert wurde als vom Architekten vorgesehen | **Planungsfehler** | Prozess muss die Reihenfolgetreue sichern oder Abweichung als Entscheidung erfassen |
| A3 | Policy von `A` hat sich geändert, weil nachträglich ein Feature hinzukam oder eine Abweicherlaubnis erteilt wurde | **Kein Planungsfehler** | Integrator darf die Integrations-Policy ersetzen (`RQ-IP-03`) |
| A4 | Auch mit Ersetzung nicht integrierbar | **Risikointegration** | Dreier-Review Integrator+QA+Architekt, Einstimmigkeit oder Eskalation (`RQ-IP-06`) |

## 3. Abgeleitete Anforderungen

### Block A — Integrations-Policy

- **RQ-IP-01** Bei jeder Integration ist die Policy des **Ziel-Branches**
  maßgeblich; das ist als klare Festlegung im Prozessmodell verankert.
- **RQ-IP-02** Der Feature-Breakdown-Prozess verhindert die Planungsfehlerfälle
  A1/A2 (Tabelle §2.1) mechanisch prüfbar: Integrierbarkeit unter der
  Ziel-Policy wird zum Branch-Zeitpunkt geprüft; die vorgesehene
  Implementierungsreihenfolge ist erfasst, Abweichungen sind erfassungspflichtig.
- **RQ-IP-03** Im Fall A3 darf der Integrator die für die Integration
  maßgebliche Policy ersetzen — gegen eine beliebige Policy, die seit dem
  Herausbranchen auf einem der beiden zu integrierenden Branches gültig war.
  Die Wahl ist eine `TK-2`-pflichtige Entscheidung (welche Policy-Version,
  warum) und wird als Decision Record festgehalten.
- **RQ-IP-04** Kein Agent committet auf einen Branch Policy-Änderungen, die auf
  einem anderen Branch entstanden sind als dem zu integrierenden oder dem
  Integrationsziel. (Damit bleibt Policy-Herkunft mechanisch prüfbar.)
- **RQ-IP-05** Policy-Änderungen des Integrationsziels dürfen in den zu
  integrierenden Branch **hereingezogen** werden. Gilt per Kundenentscheidung
  **ab sofort** (`DEC-0044-001`).
- **RQ-IP-06** Scheitert die Rückintegration auch nach `RQ-IP-03`/`RQ-IP-05`,
  liegt eine **Risikointegration** vor: Der Integrator kann sie nach Review mit
  zwei weiteren Agenten (QA und Architekt) **bei Einstimmigkeit** genehmigen und
  dafür Policies vorübergehend außer Kraft setzen; bei Nicht-Einstimmigkeit ist
  Eskalation und Entscheidung durch einen User erforderlich.
- **RQ-IP-07** Die offene Frage „Integrationstests?" ist zu beantworten: welche
  Integrationstests an Checkpoints verlangt werden und wie ihr Umfang und ihre
  Art aus der Architektur abgeleitet werden.

### Block B — Architekturprozess und Capabilities

- **RQ-AP-01** Der Feature-Breakdown-Verantwortliche (Architekt) erhält eine
  Prozessanweisung (bzw. die bestehende wird verfeinert), die nachvollziehbar
  macht, **woraus** Architekturentscheidungen, Task-Abhängigkeiten sowie Umfang
  und Art der Testfälle abgeleitet werden.
- **RQ-AP-02** Der Breakdown bewertet jede Aufgabe nach den Anforderungen an den
  Implementierer: benötigte **Rechte**, **Daten** (z. B. PGP-Schlüssel, Daten
  außerhalb des Git) und **Fähigkeiten** — als Capability-Anforderungsprofil.
- **RQ-AP-03** Der Breakdown legt je Arbeitspaket fest, wie der Implementierer
  den Branch zu erstellen hat.
- **RQ-CB-01** Es gibt ein Mapping der Anforderungsprofile auf die Rollen; der
  **Orchestrator** wählt anhand dessen den Agenten aus. Der Architekt wählt
  **nicht** direkt (Scheduling-Problem; Modelle/Personae zum
  Umsetzungszeitpunkt unbekannt) — `DEC-0044-004`.
- **RQ-CB-02** Anforderungsprofile und Agenten-Fähigkeitsbeschreibungen sind
  **maschinenlesbar**; die Task-Rollen-Zuweisung benötigt selbst **keine KI**.
- **RQ-CB-03** Der Implementierer kann selbst prüfen, ob er die geforderten
  Capabilities besitzt (Selbstcheck vor Annahme).
- **RQ-CB-04** Die bestehenden Rollen werden überprüft; bei Lücken werden neue
  Rollen handhabbarer Granularität vorgeschlagen, sodass gezielte Agentenwahl
  Tokens spart oder Parallelisierung ermöglicht (Beispiel: sandboxed Agent für
  reine Textänderungen ohne Werkzeugausführung, dann ggf. ohne Runner-Protokoll).
- **RQ-CB-05** Das Projekt beantwortet die Frage, wie die **kognitiven
  Anforderungen** eines Umsetzungspakets an einen KI-Agenten sinnvoll
  abgeschätzt werden können.
- **RQ-CB-06** *(Interpretation, s. redaktionelle Anmerkung §1)* Limits (z. B.
  Token-Budgets) und Fähigkeiten von Agenten können nichtdeterministisch sein
  und von der Vorhersage abweichen. Ein überforderter Agent soll den Job im
  besten Fall **selbst erkennen und flaggen**; für den ungünstigeren Fall
  (unbrauchbares Ergebnis ohne Selbsterkenntnis) muss der Orchestrator die
  Ergebnisqualität sichern.
- **RQ-CB-07** *(Interpretation)* Bis das Capability-Matching trägt, werden
  Sandboxed-Agenten bevorzugt nur für Arbeiten eingesetzt, bei denen sie nichts
  ausführen müssen.

## 4. Entscheidungsdatensätze

Format nach `RQ-DEC-01/02/03`; Aufzeichnungspflicht nach `TK-2`
(`docs/pipeline/process-roles.md`). Alle Entscheidungen: aktueller Benutzer
(Management/Kunde), 2026-08-20, Wortlaut in `RQ-SRC-04`.

### `DEC-0044-001` — Ziel-Branch-Policy ist maßgeblich; Pull-in erlaubt — ab sofort

- **Entscheidung:** Bei der Integration ist immer die Policy des Branches
  maßgeblich, auf den integriert wird. Policy-Änderungen dieses Ziel-Branches
  dürfen in den zu integrierenden Branch hereingezogen werden. Gilt ab sofort
  und wird im Prozessmodell verankert.
- **Fachliche Rechtfertigung:** Ohne Präzedenzregel ist unentscheidbar, welche
  Policy einen Merge regiert; der Pull-in ist die einzige Richtung, die die
  Herkunftsprüfbarkeit (`DEC-0044-002`) nicht verletzt und den Quell-Branch
  integrierfähig hält.
- **Umsetzung:** Sofortverankerung in `docs/pipeline/branch-workflow.md`
  (Abschnitt „Integration policy precedence", bei Intake ergänzt);
  vollständige Ausarbeitung und mechanische Prüfung: `0044-01`.

### `DEC-0044-002` — Herkunftsverbot für Policy-Commits

- **Entscheidung:** Agenten dürfen auf einen Branch keine Policy-Änderungen
  committen, die auf einem anderen Branch entstanden sind als dem zu
  integrierenden oder dem Integrationsziel.
- **Fachliche Rechtfertigung:** Nur so bleibt für jede Policy-Version
  feststellbar, auf welchem Branch sie entstand — Voraussetzung für die
  Ersetzungsregel (`RQ-IP-03`) und jede mechanische Herkunftsprüfung.
- **Umsetzung:** `0044-01` (Verankerung + Prüfwerkzeug).

### `DEC-0044-003` — Risikointegration nur einstimmig oder per User-Entscheidung

- **Entscheidung:** Eine Risikointegration (Fall A4, §2.1) kann der Integrator
  nach Review mit QA und Architekt bei Einstimmigkeit genehmigen und dafür
  Policies vorübergehend außer Kraft setzen; bei Nicht-Einstimmigkeit
  entscheidet ein User.
- **Fachliche Rechtfertigung:** Temporäre Policy-Außerkraftsetzung ist der
  stärkste Eingriff des Modells; Einstimmigkeit dreier unabhängiger Rollen oder
  menschliche Entscheidung begrenzen ihn. Kompatibel mit dem bestehenden
  `[u]`-Integrationsverdikt.
- **Umsetzung:** `0044-02`.

### `DEC-0044-004` — Der Orchestrator wählt den Agenten, nicht der Architekt

- **Entscheidung:** Die Agentenauswahl je Aufgabe trifft der Orchestrator zur
  Laufzeit anhand maschinenlesbarer Profile; der Architekt spezifiziert nur das
  Anforderungsprofil. Das Matching benötigt selbst keine KI.
- **Fachliche Rechtfertigung:** Zum Spezifikationszeitpunkt ist unbekannt,
  welche Modelle/Personae zum Umsetzungszeitpunkt in welchem Umfang verfügbar
  sind — ein Scheduling-Problem, das nicht in der Architekturphase gelöst wird.
  Deterministisches Matching hält die Zuweisung auditierbar und billig.
- **Umsetzung:** `0044-05`.

## 5. Bezug zum Bestand

- `docs/pipeline/process-roles.md` definiert Rollen, Personas und `TK-1`/`TK-2`,
  aber **keine Ableitungsquellen** für Architekturentscheidungen,
  Abhängigkeiten oder Testumfang (Lücke → `RQ-AP-01`).
- Die Capability-**Klassen** (`SANDBOX.md`: `sandboxed-grunt`, `unprivileged`,
  `privileged`) sind eine Grobdimension (Ausführung/Autorität). Der hier
  geforderte Capability-**Vektor** (Rechte, Daten, Werkzeuge, kognitive
  Anforderung, Token-Budget) ist feiner und orthogonal; er ersetzt die Klassen
  nicht (`DEC-CAP-001` bleibt unberührt).
- Das Subagenten-Briefing (`AGENTS.md`, „Dispatching a subagent",
  `DEC-CAP-002`) nennt heute die Capability-Klasse; das Anforderungsprofil aus
  `RQ-AP-02` ist die natürliche Erweiterung dieses Briefings.
- Branch-Policy-Semantik: `docs/pipeline/branch-workflow.md` regelte bisher
  Merge-**Autorität** und -Richtung, nicht die maßgebliche **Policy**; die
  Sofortverankerung schließt diese Lücke.

## 6. Rollenzuordnung der Umsetzung

Auftrag des Kunden: „RE und Architektur wäre den Spezialisten zu überlassen."
Die Ausarbeitung der Tasks `0044-03` … `0044-07` ist daher der Architekt- bzw.
RE-Persona nach `docs/pipeline/process-roles.md` zuzuweisen; dieses Dossier ist
der RE-Intake, nicht die Architekturausarbeitung.
