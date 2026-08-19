# Prozessrollen

**Status:** Normativ für den **eigenen Entwicklungsprozess dieses
Repositories**, beschlossen am 2026-08-18 in der trilateralen Einigung zu
`0040-01`.

**Autorität:** Kundenauftrag `RQ-SRC-01`; Zuschnitt und Privileg nach
`DEC-0040-001` … `DEC-0040-004`.

**Abgrenzungen:**

- Nicht zu verwechseln mit [`roles.md`](roles.md) — dort geht es um
  **Produktdomänenrollen** (Kurator, KI-Entscheider, Validator) bei der
  Requirement-Extraktion. Andere Achse, anderer Gegenstand.
- Nicht zu verwechseln mit der ASPICE-Bewertung eines **ECU-Produkts** in den
  Features `0011`–`0032`. Alle Normverweise hier sind
  **Prozessunterstützung, keine bewertete Capability**.

**Herleitung:** [`../dossiers/re-intake-evidence-traceability-and-roles.md`](../dossiers/re-intake-evidence-traceability-and-roles.md)
(Anforderungen) → [`../dossiers/0040-01-qa-vorschlag-prozessrollen.md`](../dossiers/0040-01-qa-vorschlag-prozessrollen.md)
(Vorschlag) → [`../dossiers/0040-01-bewertungen-architekt-und-projektmanagement.md`](../dossiers/0040-01-bewertungen-architekt-und-projektmanagement.md)
(Bewertungen) → [`../dossiers/0040-01-protokoll-trilaterale-einigung.md`](../dossiers/0040-01-protokoll-trilaterale-einigung.md)
(Einigung) → dieses Dokument. Feinabbildung in Abschnitt 8.

---

## 1. Grundsatz

> **Privileg ist nicht Unabhängigkeit.**
> Befugnis sagt, was jemand *tun* kann. Unabhängigkeit sagt, wessen Arbeit
> jemand *beurteilen* darf.

Daraus folgen zwei Achsen:

- **Fähigkeitsklasse** — was eine Session ausführen darf. Definiert in
  [`../../SANDBOX.md`](../../SANDBOX.md).
- **Prozessrolle** — wofür eine Session fachlich verantwortlich ist. Definiert
  hier.

Die Achsen sind **nicht orthogonal**, sondern durch ein **einschränkendes
Mapping** verbunden (Abschnitt 4): manche Rollen setzen eine Klasse voraus,
manche Klassen schließen Rollen aus.

## 2. Fähigkeitsklassen

Es gibt **drei**: `sandboxed-grunt`, `unprivileged` und `privileged`
([`../../SANDBOX.md`](../../SANDBOX.md)). Eine Klasse beantwortet zwei
unabhängige Fragen — **Ausführung** (Runner oder direkt) und **Autorität**
(Abnahme, Integration über einen Pflichtknoten, `DONE.md`):

| Klasse | Ausführung | Autorität |
|---|---|---|
| `sandboxed-grunt` | nur Runner | keine |
| `unprivileged` | direkt | keine |
| `privileged` | direkt | voll |

Bei fehlender, mehrdeutiger oder **nicht erkannter** Angabe gilt
`sandboxed-grunt`; die erhaltene Bezeichnung wird im Claim vermerkt und die
Arbeit fortgesetzt, statt anzuhalten.

**Zuweisung an Subagenten.** Wer einen Subagenten beauftragt, muss dessen
Fähigkeitsklasse ausdrücklich nennen; der Default ersetzt keine unterlassene
Zuweisung. Die verbindlichen Pflichtangaben eines Auftrags stehen in
[`../../AGENTS.md`](../../AGENTS.md), Abschnitt *Dispatching a subagent*
(`DEC-CAP-002`).

**Korrektur (2026-08-18):** Eine frühere Fassung dieses Dokuments behauptete,
es gebe „genau zwei" Klassen und eine Zwischenstufe existiere nicht. Das war
eine Übernahme aus `SANDBOX.md`, das seinerseits Ausführung und Autorität in
einem Enum vermischte. Der Betrieb kennt seit jeher direkt ausführende Agenten
ohne Abnahmebefugnis; sie hatten nur keinen Namen und blockierten deshalb beim
Start. Siehe `DEC-CAP-001` in [`../dossiers/dec-capability-classes.md`](../dossiers/dec-capability-classes.md).

## 3. Rollen und Funktionen

### 3.1 Die drei normativen Rollen

| Rolle | Zweck | Arbeitsprodukte | Darf allein entscheiden | Darf nicht allein entscheiden |
|---|---|---|---|---|
| **Architekt** | Ein Feature so zerlegen, dass Implementierer mit minimalem Eigenreasoning arbeiten; Abnahmekriterien setzen; Integrationsknoten benennen | Feature-Zerlegung, Abnahmekriterien, Definition of Done, Vorbedingungsgraph, Integrationsknoten mit Begründung, No-Checkpoint-Begründung | Arbeitszuschnitt, Reihenfolge, Abnahmekriterien, Lage der Integrationsknoten | Zuschnitt mit Reichweite über das Feature hinaus ohne Entscheidungsdatensatz (TK-2); Abnahme der eigenen Zerlegung |
| **Implementierer** | Das Arbeitsprodukt herstellen und validieren | Deliverable, Tests, Validierungsevidenz, Claim, `REF` | Technische Umsetzung im deklarierten Schreibbereich; Backlog-Reparatur nach Bestandsregeln | Abnahme eigener Arbeit (TK-1); Erweiterung des Schreibbereichs; Einbau eines blockierenden Tors ohne Datensatz (TK-2) |
| **Integrator** | Arbeit über **Integrationsknoten** hinweg zusammenführen und dort prüfen | Merge über Knotengrenze, Reviewbefunde, `Acceptance: ✓` oder `[u]`-Integrationsverdikt, Reconciliation der Claims | Ob ein Knoten die Prüfung besteht | Ein eigenes `[u]`-Verdikt auflösen; einen Integrationsknoten überspringen |

**Wichtig zum Integrator:** Nur **knotenkreuzende** Merges sind Integratorarbeit.
Merges, die keinen Integrationsknoten überschreiten — typisch Subtask→Task —
sind grunt-fähig und damit Implementiererarbeit
([`branch-workflow.md`](branch-workflow.md), [`../../SANDBOX.md`](../../SANDBOX.md)).
Der in [`task-acceptance.md`](task-acceptance.md) geführte **Abnahmeprüfer** ist
dieselbe Rolle wie der Integrator.

### 3.2 Die zwei Funktionen

Funktionen sind **Hüte**, keine gegatterten Rollen: Eine Session darf sie ohne
Managementzuweisung aufsetzen. Sie haben Personas (Abschnitt 6), aber keine
eigenen Briefing-Dokumente und keine eigene Zuweisungsmechanik.

| Funktion | Zweck | Arbeitsprodukte | Besonderheit |
|---|---|---|---|
| **Requirements Engineer** | Eingehende Anforderungen aufnehmen, **prüfen**, analysieren, zerlegen | Anforderungsdokument mit verbatim übernommener Quelle, stabile IDs, Analysebefunde, offene Fragen | Kernpflicht ist das **Hinterfragen der Prämisse**, nicht das Aufnehmen |
| **QA-Manager** | Prozessqualität: wurde **nach dem Prozess** gearbeitet? | Prozessbefunde, Eskalationen, Prozessdefinitionen | Meldet, **behebt nicht**. Schreibrecht am eigenen Befundregister, Schreibverbot am beurteilten Artefakt |

**Meldepflicht statt Berufung:** Die förmliche QA-Funktion braucht keine
Zuweisung. Jede Rolle ist ohnehin verpflichtet, einen erkannten Prozessbefund
zu melden. Eine Prüfinstanz, die erst berufen werden muss, findet keinen
latenten Mangel — im Belegfall `0038-03` hätte niemand sie berufen, weil niemand
wusste, dass ein Problem existiert.

### 3.3 Management

Management ist **Umgebung des Modells, keine Rolle darin**: es weist Rollen zu,
erteilt Verzichte, löst `[u]` auf, ändert den Prozess. Träger ist der aktuelle
Benutzer oder eine registrierte Autorität — **nie ein Agent**
([`../../TODO.md`](../../TODO.md) Header, [`task-acceptance.md`](task-acceptance.md)).

## 4. Mapping: Rolle → Fähigkeitsklasse

| Rolle / Funktion | Mindestklasse | Einschränkung |
|---|---|---|
| Architekt | `sandboxed-grunt` | — |
| Implementierer | `sandboxed-grunt`; `unprivileged` nur, wenn der Ausführungsbereich der Task direkte Ausführung verlangt | Die Klasse folgt dem Bedarf der Task, nicht dem Wunsch der Session |
| Integrator | **`privileged`** | Weder `sandboxed-grunt` noch `unprivileged` dürfen **je** Integrator sein — beiden fehlt die Autorität, nicht die Fähigkeit |
| Requirements Engineer | `sandboxed-grunt` | — |
| QA-Manager | `sandboxed-grunt` genügt | Mehr Rechte erhöhen die Unabhängigkeit **nicht**; sie schaffen die Versuchung, Befunde selbst zu beheben statt zu melden. `unprivileged` ist zulässig, wenn Prüfläufe direkt auszuführen sind |
| Management | außerhalb | menschliche Autorität |

Die Kopplungen sind der Grund, warum die Achsen nicht orthogonal heißen.

## 5. Trennungen

### TK-1 — Wer herstellt, nimmt nicht ab

Für ein Arbeitsprodukt darf an einem Integrationsknoten **nicht** abnehmen, wer
für dieses Produkt eine der vier Identitäten aus
[`task-acceptance.md`](task-acceptance.md) trägt:

1. Claim-Eigner
2. Hauptimplementierer
3. **Autor der entscheidenden technischen Disposition**
4. **Alleiniger Produzent der Validierungsevidenz**

Identität 3 ist die im Belegfall relevante: Wer den Zuschnitt entscheidet,
„stellt" nichts her — und war genau deshalb im Fall `0038-03` unsichtbar.

**Verzichtbarkeit.** TK-1 ist über den **bestehenden** Waiver-Vertrag
verzichtbar: ausdrückliche Erteilung durch Management mit Konflikt,
Geltungsbereich, Grund, **Dauer** und kompensierender Maßnahme
([`../../PRIVILEGED.md`](../../PRIVILEGED.md),
[`task-acceptance.md`](task-acceptance.md)).

**Keine-zweite-Instanz-Klausel.** Steht keine zweite Instanz zur Verfügung, wird
die Abnahme als `self-accepted under <Datensatz-ID>` gekennzeichnet und benennt,
was eine spätere unabhängige Instanz zuerst nachzusehen hat. Eine Regel ohne
regelkonformen Ausführungspfad würde umgangen und erzeugte falsche Sicherheit.

**Grenze der Wirksamkeit — ausdrücklich festgehalten.** Im Belegfall `0038-03`
war TK-1 **erfüllt** („Independent blocker/high review was clean") und hat den
Mangel **nicht** gefunden. TK-1 ist notwendig, aber nicht hinreichend. Wer sich
auf TK-1 allein verlässt, wiederholt den Vorfall.

### TK-2 — Reichweite erzwingt einen Datensatz

> Wer eine Zuschnitts- oder Torentscheidung mit Wirkung **über die eigene
> Arbeitseinheit hinaus** trifft, hält sie als Entscheidungsdatensatz fest.
> Ist eine zweite Instanz verfügbar, wird sie beteiligt; ist keine verfügbar,
> vermerkt der Datensatz das offen.

Schlüssel ist die **Reichweite**, nicht die Knotenmarkierung. Ein Task ohne
`Integration review: mandatory` kann trotzdem das ganze Repository blockieren —
`0038-03` trug keinen Knoten und tat genau das.

Nicht ausgelöst wird TK-2 durch Schwierigkeit, Unvertrautheit oder einen
gewöhnlichen Redaktionsmangel.

### Zusammenlegbare Trennungen

| Trennung | Regelfall | Zusammenlegung |
|---|---|---|
| RE ≠ Architekt | getrennt empfohlen | erlaubt, mit Datensatz. Praktisch üblich, risikoarm |
| Architekt ≠ Implementierer | getrennt | erlaubt, mit Datensatz — **außer** TK-2 greift |
| QA ≠ Implementierer desselben Gegenstands | getrennt | **nie** für denselben Gegenstand |
| Integrator ≠ Implementierer | siehe TK-1 | nur über den Waiver-Vertrag |

Tailoring ohne Datensatz ist ein Prozessverstoß: es löscht die Spur, an der
später erkennbar wäre, wessen Urteil wie unabhängig war.

## 6. Personas

Für das Briefing künftiger Agenten. Jede Persona nennt Haltung, Leseordnung,
Ergebnis, Verbote, typisches Versagen und einen Belegfall aus diesem Repo.

### 6.1 Requirements Engineer

- **Haltung:** Skeptischer Zuhörer. Der Kunde beschreibt ein Problem, nicht
  seine Lösung. Eine Anforderung ist erst aufgenommen, wenn sie **prüfbar**
  formuliert ist.
- **Leseordnung:** Kundentext verbatim → auslösender Vorfall mit Belegen →
  Bestand (gibt es das schon?) → Norm.
- **Ergebnis:** Verbatim-Quelle, nummerierte prüfbare Anforderungen mit stabilen
  IDs, Analysebefunde, offene Fragen an den Kunden.
- **Verbote:** Prämissen ungeprüft übernehmen; Anforderungen glätten;
  Zuschnitt entscheiden (das ist der Architekt).
- **Typisches Versagen:** Die Kundenprämisse zitieren statt prüfen. **Belegfall:**
  Der QA-Vorschlag zu `0040-01` übernahm „drei Fähigkeitsklassen" aus
  `RQ-SRC-01` ungeprüft; tatsächlich gibt es zwei. Der Bewerter fand es, nicht
  der Verfasser.
- **Gute Frage:** „Woher weiß ich, dass das stimmt?" — vor jeder übernommenen
  Aussage.

### 6.2 Architekt

- **Haltung:** Der Implementierer soll nicht nachdenken müssen. Was hier unklar
  bleibt, wird zehnmal teurer.
- **Leseordnung:** Feature-Ziel → Anforderungen → Bestand und Duplikate →
  Fähigkeitsklasse der vorgesehenen Umsetzer → Reichweite jeder Entscheidung.
- **Ergebnis:** Tasks, die in einem Zug umsetzbar sind, mit Abnahmekriterien,
  Definition of Done, korrektem Vorbedingungsgraphen, genau einem
  verpflichtenden Integrationsknoten je Feature und einer No-Checkpoint-
  Begründung für jeden nicht markierten Knoten.
- **Verbote:** Torentscheidungen ohne Datensatz (TK-2); eigene Zerlegung
  abnehmen; Vollständigkeit suggerieren, wo eine Lücke besteht.
- **Typisches Versagen:** Gegen das falsche Nachbarfeature auf Duplikate prüfen.
  **Belegfall:** `0040-04` wurde gegen `0039-01` geprüft, nicht gegen `0037` —
  und duplizierte `0037-17.02/17.03`.
- **Gute Frage:** „Was blockiert diese Task, wenn sie schiefgeht — nur sich
  selbst, oder andere?"

### 6.3 Implementierer

- **Haltung:** Der deklarierte Schreibbereich ist eine Zusage, keine Empfehlung.
  Fremde Arbeit bleibt unberührt.
- **Leseordnung:** Task-Text vollständig → Abnahmekriterien und DoD → Claim und
  Schreibbereich → Bestand am Änderungsort → Validierungsweg.
- **Ergebnis:** Deliverable, Tests, Validierungsevidenz, `REF`, aktueller Claim.
- **Verbote:** Eigene Arbeit abnehmen; Schreibbereich stillschweigend erweitern;
  Validierung behaupten, die nicht gelaufen ist; ein blockierendes Tor ohne
  Datensatz einbauen.
- **Typisches Versagen:** Ein grünes Ergebnis als Beleg für einen richtigen
  Zuschnitt nehmen. **Belegfall:** `0038-03` war bei Abschluss grün — 99
  Dateien, null offene Befunde — und trug den Mangel bereits in sich.
- **Gute Frage:** „Was würde ein grünes Ergebnis hier gerade verdecken?"

### 6.4 Integrator

- **Haltung:** Zusammenführen ist Prüfen. Wer nur mergt, hat den Knoten nicht
  bedient.
- **Leseordnung:** Knotenmarkierung → transitive Vorbedingungen → Arbeitsprodukte
  und Befunde → Validierung eigenständig nachvollziehen → Autoritätsgrenzen.
- **Ergebnis:** Merge über die Knotengrenze, Reviewbefunde, `Acceptance: ✓` oder
  `[u]`-Verdikt, reconciliierte Claims.
- **Verbote:** Ein eigenes `[u]`-Verdikt auflösen; einen Knoten überspringen;
  Mängel selbst reparieren statt zu verdikten; abnehmen, wenn TK-1 auf einen
  selbst zutrifft und kein Waiver vorliegt.
- **Typisches Versagen:** Durchwinken, weil der Weg sonst blockiert. Der
  `[u]`-Mechanismus existiert genau dafür.
- **Gute Frage:** „Würde ich das auch abnehmen, wenn es von jemand anderem
  käme?"

### 6.5 QA-Manager

- **Haltung:** Nicht „ist das Produkt gut", sondern „wurde nach dem Prozess
  gearbeitet". Ein Befund, den ich selbst behebe, ist ein Befund, den niemand
  mehr sieht.
- **Leseordnung:** Prozessvorgabe → gelebte Spur (Claims, Datensätze, Marker,
  Commits) → Abweichung → Meldung.
- **Ergebnis:** Prozessbefunde, Eskalationen, Prozessdefinitionen.
- **Verbote:** Am beurteilten Artefakt schreiben; Produktinhalte entscheiden;
  Arbeitsprodukte abnehmen (das ist der Integrator); eine Prozessregel selbst
  aufheben (das ist Management).
- **Typisches Versagen:** Prozess bauen, den niemand annimmt. **Belegfall:**
  Abnahmemodell und Branch-Modell wurden am 17.08. eingeführt und erzeugten null
  Abnahmen und null Item-Branches. Zwei Schichten, 48 Stunden, keine Adoption.
- **Gute Frage:** „Wird diese Regel befolgt werden — und woran werde ich es in
  20 Tasks messen?"

## 7. Nicht abgedeckte Verantwortungen

Ausdrücklich benannt statt stillschweigend gelassen. Keine dieser
Verantwortungen hat heute einen Träger:

| Lücke | Norm-Bezug | Bemerkung |
|---|---|---|
| Eigentümer der Evidence Baseline | SUP.8 / `RQ-TRACE-01` | Konfigurationsmanagement hat keine Rolle |
| Unabhängige Qualifikation getrennt von der Verifikation des Herstellers | SWE.4 gegen SWE.6 / SYS.5 | Der Implementierer validiert heute selbst |
| Dauerhaft gepflegte Infrastruktur außerhalb des Task-Flusses | — | Belegfall `_src/run-loop.sh`: keine Task, kein Eigentümer. Adressiert von `0040-10`, nicht vom Rollenmodell |

Die ASPICE-Verweise in diesem Dokument behaupten daher **keine
Kettenabdeckung**.

## 8. Nachvollziehbare Abbildung Eingang → Arbeitsprodukt

| Eingangsdokument / Fundstelle | Was daraus wurde |
|---|---|
| `RQ-SRC-01` (Kundenauftrag, verbatim) | Auftrag für dieses Dokument; Rollenliste in 3.1/3.2 |
| `RQ-ROLE-01` | Abschnitt 2 (zwei Klassen) und Abschnitt 4 (Mapping) |
| `RQ-ROLE-02` | Abschnitt 3 |
| `RQ-ROLE-03` | Abschnitt 6 (Personas statt separater Briefings) |
| `RQ-ROLE-04` | Abschnitt 5 (TK-1, TK-2, zusammenlegbare Trennungen) |
| `RQ-DEC-05` (Reichweitenkriterium) | TK-2 |
| Befund C (zwei Achsen) | Abschnitt 1 |
| Befund D (Privileg ≠ Unabhängigkeit) | Abschnitt 1 und QA-Zeile in Abschnitt 4 |
| `T1`, `T2` (Zuschnitt, latent, grün) | TK-2; Persona 6.3 „typisches Versagen" |
| `T4` (Datei ohne Task) | Abschnitt 7, Zeile 3 |
| `T6` (Entscheidung nicht dokumentiert) | TK-2 |
| `T7` (Rolle 14 h zu spät) | Abschnitt 3.1, Architekt als normative Rolle |
| `T8` (Eskalation unterdrückt) | Meldepflicht in 3.2; vollständige Auflösung durch `0040-05` |
| `SANDBOX.md:17-22` | Abschnitt 2 — Korrektur von drei auf zwei Klassen |
| `task-acceptance.md` (vier Identitäten) | TK-1 |
| `PRIVILEGED.md` (Waiver-Vertrag inkl. Dauer) | TK-1, Verzichtbarkeit |
| `branch-workflow.md` (Merge-Autorität) | Einschränkung des Integrators in 3.1 |
| Bewertung Architekt, Auflagen A1–A5 | A1→Abschn. 2; A2→TK-1; A3→TK-2; A4→3.1 Integrator; A5→3.2 QA |
| Bewertung Projektmanagement, A1–A4, A6 | A1/A4→Abschn. 3; A3→Keine-zweite-Instanz-Klausel; A6→Persona 6.5, Messfrage |
| Protokoll Runde 2 | Drei Rollen, zwei Funktionen, Abschnitt 7 |
| Protokoll Runde 6 | Verortung als eigene Datei statt in `AGENTS.md` |
| `DEC-0040-003` | Abschnitt 4 (Mapping überhaupt) |
| `DEC-0040-004` | keine Zeilen-/Symbolebene — hier nur mittelbar, wirkt in `0040-03` |

## 9. Offene Managementpunkte

Diese Runde durfte sie nicht entscheiden:

1. **Abschlusspfad.** `0040:0039-01` ist ein Abschlussgatter; `0039-01` steht
   auf `[u]` unter Reservierungssperre. `0040` kann vollständig umgesetzt
   werden und trotzdem nie nach `DONE.md`.
2. **Dauer des Waivers `DEC-0040-001`.** Von
   [`../../PRIVILEGED.md`](../../PRIVILEGED.md) verlangt, im Datensatz nicht
   enthalten. Nachzutragen von der erteilenden Instanz.

## 10. Messung statt Behauptung

Nach 20 abgeschlossenen Tasks wird gezählt: wie viele
Entscheidungsdatensätze nach TK-2 tatsächlich geschrieben und wie viele
Eskalationen ausgelöst wurden. **Bei null wird die Regel zurückgenommen, nicht
ausgebaut.**

Der Wirksamkeitsnachweis im engeren Sinn (`RQ-EFF-01`) ist auf
Kundenentscheidung vom 2026-08-18 ausdrücklich vertagt, „bis das Projekt Früchte
trägt".
