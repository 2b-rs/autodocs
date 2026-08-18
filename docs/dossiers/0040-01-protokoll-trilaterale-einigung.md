# Protokoll der trilateralen Einigung zum Prozessrollenmodell `0040-01`

**Datum:** 2026-08-18
**Teilnehmer:** QA-Manager (Verfasser des Vorschlags), Architekt (Bewertung A),
Projektmanagement (Bewertung B)
**Grundlage:** `0040-01-qa-vorschlag-prozessrollen.md`;
`0040-01-bewertungen-architekt-und-projektmanagement.md`
**Ergebnis:** Einigung erzielt. Alle drei Positionen tragen sie mit.

---

## Runde 1 — Unstrittiges

Ohne Aussprache angenommen, weil alle drei zustimmen:

- Das **Blast-Radius-Kriterium** (`RQ-DEC-05`) ist der eigentliche Wirkstoff.
  Der Architekt: „Der Wirkstoff ist `RQ-DEC-05`, nicht die Rollentrennung." Das
  Projektmanagement: „die beste Idee im ganzen Paket […] Prozess, der billiger
  ist als sein Ausfall."
- **„Privileg ist nicht Unabhängigkeit"** wird normativ. Kostenlos, räumt eine
  ganze Fehlerklasse ab.
- **Zwei Achsen**, aber mit **einschränkendem** statt orthogonalem Mapping.
- **Fähigkeitsklassen: zwei, nicht drei.** Der QA-Manager zieht die Angabe
  zurück. Er hat die Kundenprämisse ungeprüft übernommen — die Pflicht, die er
  selbst in Abschnitt 3.1 zur RE-Kernpflicht erklärt hatte. Der Fehler geht
  zulasten des Vorschlags, nicht des Kunden.

## Runde 2 — Die Rollenzahl: Architekt gegen Projektmanagement

Der einzige direkte Widerspruch zwischen den Bewertern.

**Architekt:** sechs Rollen sind **zu wenige**. Für SUP.8 / `RQ-TRACE-01`
(Eigentümer der Evidence Baseline) und für SWE.4 gegen SWE.6/SYS.5 (Verifikation
gegen unabhängige Qualifikation) gibt es keinen Träger. Die ASPICE-Spalte
suggeriert eine Kettenabdeckung, die nicht existiert.

**Projektmanagement:** sechs Rollen sind **zu viele**. Drei genügen — Architekt,
Implementierer, Integrator stehen bereits in `AGENTS.md` und tragen bereits
Regelwirkung. RE und QA-Manager sind Hüte derselben Person in derselben Sitzung.
Management ist nicht Rolle *im* Modell, sondern dessen Umgebung.

**QA-Manager, Vermittlungsvorschlag:** Die beiden reden über verschiedene
Größen. Der Architekt spricht über **Vollständigkeit des Modells**, das
Projektmanagement über **Kosten der Instanziierung**. Beides ist erfüllbar:

> Wenige Rollen **normativ** benennen; die nicht abgedeckten Verantwortungen
> **ausdrücklich als Lücke ausweisen**, statt für jede eine Rolle zu erfinden.

Eine benannte Lücke kostet drei Zeilen und ist ehrlicher als eine Rolle, die
niemand besetzt.

**Angenommen von beiden.** Der Architekt: Vollständigkeit ist gewahrt, weil
nichts stillschweigend fehlt. Das Projektmanagement: die Regelfläche wächst
nicht.

**Beschluss:** Drei normative Rollen (Architekt, Implementierer, Integrator).
Requirements Engineer und QA-Manager als **Funktionen** („Hüte") — benannt,
mit Persona beschrieben, aber ohne eigene Zuweisungsgatterung und ohne eigene
Briefing-Dokumente. Management als **Umgebung**, nicht als Rolle. Dazu ein
Abschnitt „Nicht abgedeckte Verantwortungen".

## Runde 3 — Trennungskern TK-1

**Architekt:** TK-1 ist zugleich zu absolut und zu eng. Zu absolut, weil vier
Autoritätsdokumente einen begrenzten Verzicht vorsehen und ein agentenverfasster
Vorschlag eine protokollierte Managemententscheidung nicht entwerten darf. Zu
eng, weil „wer herstellt" schmaler ist als die vier Identitäten in
`task-acceptance.md:68` — und im Belegfall ist der **Zuschnittsentscheider** die
relevante Identität, der nichts „herstellt".

**Projektmanagement:** TK-1 ist in diesem Betriebsmodell **nicht befolgbar**.
Es gibt eine Person. Eine Regel ohne regelkonformen Ausführungspfad wird
umgangen und erzeugt falsche Sicherheit — genau das Versagen, das der Vorschlag
verhindern will.

**QA-Manager:** Ich gebe beiden recht und ziehe „kein Verzicht möglich" zurück.
Der Architekt hat zudem den härtesten Einzelbefund geliefert: `TODO.md:240`
protokolliert für `0038-03` „Independent blocker/high review was clean". **TK-1
war im Belegfall erfüllt und hat den Mangel nicht gefunden.** Eine Trennung, die
am einzigen belegten Fall nachweislich wirkungslos war, darf nicht als
unverhandelbarer Kern auftreten. Das entwertet TK-1 nicht — es verschiebt es
vom Kern an seinen richtigen Platz.

**Beschluss:** TK-1 wird auf die Bestandsformel gebracht (vier Identitäten aus
`task-acceptance.md:68`), bleibt über den **bestehenden** Waiver-Vertrag
verzichtbar — einschließlich der von `PRIVILEGED.md:107` verlangten **Dauer** —
und erhält die Keine-zweite-Instanz-Klausel des Projektmanagements. Der Absatz
„Konsequenz für den laufenden Fall" entfällt ersatzlos; `DEC-0040-001` und
`TODO.md:158-160` regeln den Fall bereits.

## Runde 4 — TK-2 und der Reichweiten-Schlüssel

**Architekt:** Abschnitt 5.2 Zeile 2 muss weg. Sie erlaubt die Zusammenlegung
von Architekt und Implementierer, „wenn der Task keinen Integrationsknoten
trägt" — und `0038-03` trug keinen, `0040-04` trägt bewusst keinen. Die Regel
erlaubt die Zusammenlegung präzise dort, wo der Vorfall stattfand. Ersatz: TK-2,
geschlüsselt auf Reichweite.

**Projektmanagement:** Einverstanden, sofern TK-2 eine **Aufzeichnungs**pflicht
ist und keine Zweite-Instanz-Pflicht. Letztere kostet je Vorkommen eine
Extrasitzung, und rund jede vierte Task wäre betroffen.

**Beschluss (Kompromiss):** TK-2 ist eine Aufzeichnungspflicht. Eine zweite
Instanz ist nur zu beteiligen, **wenn eine verfügbar ist**; ist keine verfügbar,
trägt der Datensatz das offen. Damit ist der Schlüssel korrigiert (Reichweite
statt Knotenmarkierung) und die Kosten bleiben bei fünf Minuten je Vorkommen.

## Runde 5 — Umfang und Reihenfolge

**Projektmanagement:** Der Adoptionsbefund entscheidet. Abnahmemodell und
Branch-Modell wurden beide am 17.08. eingeführt und haben null Abnahmen und null
Item-Branches erzeugt. Eine dritte Schicht obendrauf ist Bestandsaufbau. Dazu:
`0040-04` dupliziert `0037-17.02/17.03`; `0040-06` hat keinen begrenzten
Zuschnitt; `0040` hat wegen `0039-01` keinen Abschlusspfad; und **der Vorfall,
der das Feature ausgelöst hat, ist unrepariert — keiner der neun Tasks repariert
ihn.**

**Architekt:** Der Duplikatsbefund trifft; ich habe nur gegen `0039-01` geprüft,
nicht gegen `0037`. Meine Auflagen betreffen die Qualität des Modells, nicht
seinen Umfang — sie sind mit einem kleineren Schnitt vereinbar, solange A1 bis
A5 im verbleibenden Text erfüllt werden.

**QA-Manager:** Ich trage die Reihenfolgeforderung mit. Prozess zu schreiben,
während der protokollierte Schaden weiterläuft, ist nicht verteidigbar — und es
wäre exakt das Verhalten, das dieses Feature kritisiert.

**Beschluss:**

| Task | Ergebnis |
|---|---|
| **neu `0040-10`** | Live-Blocker reparieren. Wird **erste** Task des Features. |
| `0040-01` | bleibt, nach Auflagen A1–A5 überarbeitet, inklusive Personas |
| `0040-02` | `[w]` — Briefings gehen als Personas in `0040-01` auf, keine fünf Einzeldokumente |
| `0040-03` | bleibt, auf Minimalformat reduziert |
| `0040-04` | `[w]` — Duplikat; als Anforderung in `0037-17.02/17.03` eingehängt |
| `0040-05` | bleibt, Integrationsprüfung bleibt verpflichtend — die eine Stelle, an der sie ihr Geld wert ist |
| `0040-06` | `[w]` — auf Befund A reduziert, dieser geht in `0040-01`/`0040-03` auf |
| `0040-07` | `[w]` — **Kundenentscheidung**: der Wirksamkeitsnachweis wird „erst deutlich später" beantwortet. Ersetzt durch die Messregel A6. |
| `0040-08` | bleibt |
| `0040-09` | bleibt, Integrationsknoten |

**9 Tasks → 6.** Aufwand nach Schätzung des Projektmanagements von 13–21 auf
etwa 5–8 Sitzungen.

## Runde 6 — Wo das Dokument steht

**Projektmanagement:** kein neues Dokument, ein Abschnitt in `AGENTS.md`.

**Architekt:** die Definition of Done von `0040-01` verlangt
`docs/pipeline/process-roles.md`.

**QA-Manager, entscheidend:** Das Argument des Projektmanagements schlägt hier
gegen es selbst. `AGENTS.md` wird bei **jedem** Agentenzug geladen; der
Autoritätskern liegt bereits bei ~65 KB. Rollentext dorthin zu legen kostet
Kontext in jedem einzelnen Zug — teurer als eine separate Datei, die nur liest,
wer sie braucht.

**Beschluss:** Eine neue Datei `docs/pipeline/process-roles.md`, knapp gehalten,
aus `AGENTS.md` mit **wenigen Zeilen** verwiesen. Beide Positionen sind
gewahrt: der Autoritätskern wächst kaum, die DoD ist erfüllt.

## Runde 7 — Offene Punkte ohne Beschlussbefugnis

Zwei Punkte kann diese Runde nicht entscheiden; sie gehen an das Management:

- **Abschlusspfad (`A5` des Projektmanagements).** `0040:0039-01` ist ein
  Abschlussgatter, `0039-01` steht auf `[u]` unter Reservierungssperre. `0040`
  kann vollständig umgesetzt werden und trotzdem nie nach `DONE.md`. Kein Agent
  darf die Sperre lösen.
- **Dauer des Waivers `DEC-0040-001`.** `PRIVILEGED.md:107` verlangt sie, der
  Datensatz enthält sie nicht. Nachzutragen hat sie die erteilende Instanz.

Beide werden als offene Managementpunkte im Feature vermerkt, nicht agentisch
entschieden.

---

## Die Einigung

Alle drei tragen mit:

1. **Zwei Fähigkeitsklassen** — `sandboxed/grunt` und `privileged`.
2. **Drei normative Rollen** — Architekt, Implementierer, Integrator. **Zwei
   Funktionen** — Requirements Engineer, QA-Manager. **Management als
   Umgebung.** Nicht abgedeckte Verantwortungen werden ausdrücklich benannt.
3. **Zwei Achsen mit einschränkendem Mapping**, nicht orthogonal.
4. **TK-1** auf Bestandsformel, verzichtbar nach bestehendem Waiver-Vertrag
   inklusive Dauer, mit Keine-zweite-Instanz-Klausel.
5. **TK-2** — Aufzeichnungspflicht bei Reichweite über die eigene
   Arbeitseinheit hinaus. Ersetzt die knotenbasierte Tailoring-Regel.
6. **Reihenfolge** — Live-Blocker zuerst.
7. **Umfang** — sechs statt neun Tasks.
8. **Messung statt Nachweis** — nach 20 Tasks wird gezählt. Bei null wird die
   Regel zurückgenommen, nicht ausgebaut.
9. **Verortung** — `docs/pipeline/process-roles.md`, aus `AGENTS.md` knapp
   verwiesen.

**Erklärung des QA-Managers:** Von meinen acht selbst benannten oder von den
Bewertern gefundenen Schwachpunkten sind sechs zulasten meines Entwurfs
entschieden worden. Ich halte das Ergebnis für besser als meinen Vorschlag. Die
beiden Befunde, die ich für die wertvollsten halte, stammen nicht von mir: dass
TK-1 im Belegfall bereits erfüllt war (Architekt), und dass zwei
Governance-Schichten in 48 Stunden null Adoption erreicht haben
(Projektmanagement).

**Erklärung des Architekten:** Auflagen A1 bis A5 sind im Beschlusstext
enthalten. Der reduzierte Umfang berührt sie nicht.

**Erklärung des Projektmanagements:** Auflagen A1 bis A4 und A6 sind enthalten.
A5 (Abschlusspfad) bleibt offen und geht an das Management — das war von
Anfang an kein Punkt, den diese Runde entscheiden konnte.
