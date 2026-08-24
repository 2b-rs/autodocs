# Entscheidungsdatensatz: Abschluss von Altfeatures ohne Review-Floor

**Format** nach `RQ-DEC-01/02/03` (Zeitpunkt, entscheidende Identität, fachliche
Rechtfertigung), append-only. Aufzeichnungspflichtig nach `TK-2`: die
Entscheidung wirkt auf jedes Feature, dessen Zerlegung älter ist als die
Checkpoint-Regel, und damit auf jede spätere Abschluss-Session.

**Eigene ID-Serie.** Bewusst nicht als `DEC-0034-00x` geführt: der Gegenstand
gehört keinem einzelnen Feature, sondern regelt eine Klasse von Altfeatures.
Eine eigene Datei vermeidet die falsche Zuordnung und den Konflikt mit
Feature-Branches, auf denen die jeweiligen Feature-Dossiers fortgeschrieben
werden.

---

## `DEC-LEG-001` — Verzicht auf den Review-Floor bei Features ohne integrierende Task

- **Zeitpunkt:** 2026-08-20T08:02:27Z
- **Entscheidende Instanz:** aktueller Benutzer (Management)
- **Identität:** `authority:current-user:legacy-feature-closure:20260820T080227Z`
- **Rolle:** `Management`
- **Autoritätsreferenz:** verbatim Auswahl in Abschnitt „Provenienz" unten
- **Vorlegende Session:** `agent:picard:0040-closure:20260820T080227Z` (Integrator; hat die Optionen samt Folgen vorgelegt und nicht entschieden)

### Gegenstand

Der `TODO.md`-Header und [`task-acceptance.md`](../pipeline/task-acceptance.md)
verlangen, dass jede Feature-Zerlegung **genau eine integrierende Task** enthält,
die als `Integration review: mandatory` markiert ist und den Review-Floor des
Features bildet: „Absent an override, no Feature closes without this review."

Diese Regel wurde mit Commit `98fa57ce1` am **2026-08-17T20:32:40+02:00**
eingeführt. Features, deren Zerlegung älter ist, konnten sie nicht erfüllen. Sie
tragen keinen vom Architekten erklärten Integrationsknoten — nicht aus
Nachlässigkeit, sondern weil das Attribut zum Zeitpunkt ihrer Zerlegung nicht
existierte. Ohne Regelung wären sie dauerhaft nicht abschließbar, obwohl ihre
Arbeit vollständig terminal ist. Betroffen ist unter anderem Feature `0034`
(vier Tasks, alle `[x]`/`[w]`, alle REFs von `main` erreichbar, keine
Feature-Vorbedingung).

### Entscheidung

Management verzichtet für diese Klasse von Altfeatures auf den Review-Floor —
ausdrücklich, protokolliert und begrenzt:

1. **Geltungsbereich.** Der Verzicht gilt für ein Feature genau dann, wenn seine
   Zerlegung vor `98fa57ce1` (2026-08-17T20:32:40+02:00) committet wurde **und**
   es keinen Knoten trägt, der `Integration review: mandatory` markiert ist. Beide
   Bedingungen sind am Repository überprüfbar. Er gilt **nicht** für Features, die
   nach diesem Commit zerlegt wurden, und **nicht** für Knoten, die tatsächlich als
   Checkpoint markiert sind — dort bleibt die Abnahme unverändert erforderlich.
2. **Ersatzkontrolle statt Wegfall.** Der Verzicht ersetzt den Floor durch eine
   verpflichtende **Closure-Notiz** je Feature. Sie benennt: den fehlenden
   Review-Floor und diesen Verzicht als Grund, den terminalen Zustand jeder Task
   mit ihrem `REF`, jedes bekannte offene Residuum mit seinem Eigentümer, und die
   abschließende privilegierte Identität. Ein Feature ohne diese Notiz fällt nicht
   unter den Verzicht.
3. **Residuen bleiben sichtbar.** Ein bekanntes, nicht ausgeführtes Arbeitsstück
   darf beim `DONE.md`-Move nicht als erledigt erscheinen. Es wird in der
   Closure-Notiz ausdrücklich als offen geführt. Für Feature `0034` betrifft das
   die blockierte Regeneration von
   `_src/tests/fixtures/spec_extraction/benchmark-draft.json`, die
   `blocked-on-input` ist, weil die Kampagnen-Rohdaten fehlen.
4. **Was der Verzicht nicht berührt.** Der `DONE.md`-Move bleibt ein
   privilegierter Akt. Bestehende `Acceptance: ✓`-Records bleiben unveränderlich.
   Historische `DONE.md`-Einträge behalten ihren aufgezeichneten
   Vor-Prozess-Beweisstatus und werden nicht rückwirkend umetikettiert. Der
   Verzicht erzeugt **keine** Abnahme und **kein** Qualitätsurteil über die
   Arbeit; er stellt nur fest, dass ein zum Zerlegungszeitpunkt nicht
   existierendes Verfahren nicht rückwirkend gefordert wird.
5. **Dauer.** Unbefristet für die abschließend definierte Altmenge, die durch das
   Datumskriterium in Punkt 1 fest und nicht erweiterbar ist. Für neue Features
   ist der Verzicht wirkungslos.

### Fachliche Rechtfertigung

Ein Prozess, der eine Anforderung rückwirkend auf Arbeitseinheiten anwendet, die
sie nicht erfüllen konnten, erzeugt entweder Stillstand oder — schlimmer — die
Gewohnheit, Gates stillschweigend zu überspringen. Genau diese Gewohnheit ist der
Fehlertyp, gegen den Feature `0040` geschrieben wurde. Der ausdrückliche,
protokollierte Verzicht ist der vom Prozess selbst vorgesehene Weg
(„Management override"): Er hält sichtbar, dass ein Gate fehlt, statt es zu
verbergen.

Die gewählte Ersatzkontrolle ist nicht kosmetisch. Die Closure-Notiz erzwingt,
dass jemand den terminalen Zustand jeder Task, ihre `REF` und die offenen
Residuen ausdrücklich niederschreibt — also genau die Prüfung, die der Floor
leisten sollte, nur ohne die Fiktion einer nachträglich erfundenen integrierenden
Task.

### Erwogene Alternativen

- **ALT-01 — genereller Verzicht mit Closure-Notiz je Feature.**
  `ausgewählt`. Einmalige Entscheidung, überprüfbarer Geltungsbereich,
  Ersatzkontrolle bleibt wirksam, kein Präzedenzfall für neue Features.
- **ALT-02 — je Altfeature ein vollständiges Aggregat-Review.**
  `abgelehnt`. Prüft Arbeitsprodukte gegen einen Vertrag, der zu ihrer Entstehung
  nicht galt, bindet erheblichen Aufwand pro Feature und erzeugt keinen
  Erkenntnisgewinn, der die Verzögerung des gesamten Altbestands rechtfertigt.
- **ALT-03 — rückwirkend eine integrierende Task in jedes Altfeature einziehen.**
  `abgelehnt`. Erfände Historie: eine Task, die niemand zerlegt, geplant oder
  ausgeführt hat, und einen Architektenentscheid, den es nie gab. Das ist genau
  die Art von Rückdatierung, die der Entscheidungsrecord-Vertrag verbietet.

### Folgen

- **CON-01:** Terminale Altfeatures sind abschließbar, ohne dass ein Gate
  stillschweigend übersprungen wird.
- **CON-02:** Jeder Abschluss unter diesem Verzicht ist an der Closure-Notiz
  erkennbar und gezielt nachprüfbar; der Verzicht ist im `DONE.md`-Eintrag
  sichtbar und nicht nur in diesem Dossier.
- **CON-03:** Für die Altmenge existiert dauerhaft kein Integrations-Review. Das
  ist der bewusst getragene Preis; er ist durch das feste Datumskriterium
  begrenzt und wächst nicht.
- **CON-04:** Neue Features erhalten dadurch keinerlei Erleichterung; ein
  fehlender Floor dort bleibt ein Defekt der Zerlegung.

### Betroffene Arbeitseinheiten und Gates

- `feature:0034` und jedes weitere Feature, das beide Bedingungen aus Punkt 1
  erfüllt
- `feature-closure:<jedes solche Feature>`
- `repository:autodocs`

### Provenienz

Die Entscheidung wurde vom aktuellen Benutzer über eine strukturierte Auswahl
getroffen. Fragetext wörtlich:

> Feature 0034 (und alle Altfeatures vor der Checkpoint-Regel) haben keine integrierende Task als Review-Floor. Wie sollen sie geschlossen werden?

Vorgelegte Optionen, wörtlich:

1. `Floor generell waiven, Closure-Notiz je Feature (Empfohlen)` — Eine einmalige, protokollierte Management-Autorisierung für Features, die vor Einführung der Regel entstanden sind. Jedes schließt mit einer Notiz, die den fehlenden Floor und offene Residuen (bei 0034: die blockierte Fixture-Regeneration) benennt. Ich kann 0034 danach sofort abschließen.
2. `Nur 0034: volles Aggregat-Review durch mich` — Ich prüfe 0034 als Feature vollständig — Werkprodukte, Validierung neu gefahren, Digests — und schließe es erst danach. Gründlicher, aber pro Altfeature erheblicher Aufwand.
3. `0034 vorerst offen lassen` — Wir vertagen die Grundsatzfrage und konzentrieren uns nur auf 0040.

**Auswahl des Benutzers, wörtlich:** `Floor generell waiven, Closure-Notiz je Feature (Empfohlen)`

Auslösende Anweisung, wörtlich:

> Schreib den Waiver.
