# Bewertungen des QA-Vorschlags `0040-01` — Architekt und Projektmanagement

**Gegenstand:** `docs/dossiers/0040-01-qa-vorschlag-prozessrollen.md`
**Datum:** 2026-08-18
**Aufzeichnung:** QA-Manager. Inhaltlich vollständig, sprachlich gestrafft.
Verdikte, Auflagen, Fundstellen und Zahlen sind unverändert.
**Unabhängigkeit:** Beide Bewertungen entstanden parallel und ohne Kenntnis der
jeweils anderen.

---

## Teil A — Bewertung durch den Architekten

**Verdikt: zustimmungsfähig mit Auflagen.**

> „Der Grundsatz und die Bauform sind richtig und sollten erhalten bleiben; kein
> Mangel ist strukturell unheilbar, alle Korrekturen sind lokal. In der
> vorliegenden Fassung widerspricht das Dokument jedoch vier
> Autoritätsdokumenten, benennt eine nicht existierende Fähigkeitsklasse und
> würde die eigene Definition of Done verfehlen. Es darf so nicht normativ
> werden."

### Was der Architekt stützt

- Die Zwei-Achsen-Trennung ist **keine Scheinlösung**. Sie liegt im Bestand
  bereits latent vor und wird nur nicht als Struktur geführt: `AGENTS.md:82`
  („privilege alone is not authority or independence"),
  `task-acceptance.md:66`, `PRIVILEGED.md:32`. Der Vorschlag hebt drei
  verstreute Prosa-Sätze auf Grundsatzebene. Das ist die richtige Antwort auf
  `RQ-ROLE-01`.
- **Trennungskern plus Tailoring ist die richtige Bauform** für ein
  Ein-Personen-Projekt. Ein Modell, das fünf Sessions je Feature verlangt,
  würde umgangen — und ein umgangenes Modell ist schlechter als keines.
- Das Rollenschema (Zweck / Arbeitsprodukte / darf allein / darf nicht allein)
  ist **briefingfähig** und spart `0040-02` Arbeit.
- Die Aufnahme des Managements als sichtbare Rolle ist eine Verbesserung.
- `process_role` im Claim ist **heute additiv umsetzbar**: `legacy_task_doctor.py:1095`
  verlangt nur fünf Felder, unbekannte Zusatzfelder werden nicht abgelehnt.

### Mängel nach Schwere

1. **Abschnitt 5.2 Zeile 2 weicht genau die Trennung auf, um die es geht.**
   Zusammenlegung Architekt/Implementierer erlaubt, „wenn der Task keinen
   Integrationsknoten trägt". `0038-03` trug keinen; `0040-04` trägt bewusst
   keinen. Die Regel erlaubt die Zusammenlegung **präzise in der Task-Klasse, in
   der der Vorfall stattfand**. Der richtige Schlüssel ist die Reichweite
   (`RQ-DEC-05`), nicht die Knotenmarkierung. Widerspricht zudem `AGENTS.md:86`,
   `TODO.md:67`, `task-acceptance.md:17` und unterschreitet die eigene
   Abnahmebedingung in `TODO.md:96`.
2. **TK-1 „kein Verzicht möglich" widerspricht vier Autoritätsdokumenten.**
   `AGENTS.md:82`, `task-acceptance.md:68` und `:22`, `PRIVILEGED.md:107` sehen
   durchgängig einen begrenzten Verzicht vor; `TODO.md:96` sagt „**normally**
   independent". Abschnitt 5.1 widerlegt sich außerdem im Folgesatz selbst: ein
   offengelegter Vermerk *ist* die Ausnahme. Ein agentenverfasster Vorschlag
   kann eine protokollierte Managemententscheidung nicht rückwirkend entwerten.
3. **TK-1 ist zugleich zu eng.** „Wer herstellt" ist schmaler als
   `task-acceptance.md:68`, das **vier** Identitäten disqualifiziert:
   Claim-Eigner, Hauptimplementierer, **Autor der entscheidenden technischen
   Disposition**, **alleiniger Produzent der Validierungsevidenz**. Im
   `0038-03`-Fall ist der Zuschnittsentscheider die relevante Identität — und
   der „stellt" nichts her. Netto eine **Absenkung** des Bestands.
4. **Achse 1 beschreibt einen Bestand, den es nicht gibt.** `SANDBOX.md:17`:
   „There are two agent classes"; `:22` kollabiert die Zwischenstufe
   ausdrücklich. Maschinell verankert in `legacy_task_doctor.py:90` und
   `:1130-1135`. Die drei Klassen stammen aus der Kundenprämisse `RQ-SRC-01`;
   der RE hat sie korrekt zitiert, **der QA-Manager hat sie ungeprüft als
   Bestand übernommen** — genau die Prämissenprüfung, die er in 3.1 zur
   RE-Kernpflicht erklärt. Folge: Ein Claim mit `lokal-nichtprivilegiert`
   erzeugt heute `LTD-CLAIM-IDENTITY-MISMATCH` (Severity `error`).
5. **Das Eskalationsrecht des QA-Managers hat keinen Kanal.** Der einzige
   Mechanismus ist `[u]`, und `AGENTS.md:58` schließt Drafting-Defekte
   ausdrücklich aus (`T8`). Auflösung liegt bei `0040-05`, worauf `0040-01`
   keine Vorbedingung hat. Verschärfend: die Managementzuweisung in 6.3 —
   „eine Rolle, die latente Mängel finden soll, kann nur handeln, wenn das
   Management sie beruft. Im `0038-03`-Fall hätte niemand sie berufen, weil
   niemand wusste, dass ein Problem existiert."
6. **Der Integrator ist zu weit definiert.** Subtask→Task-Merges sind
   grunt-fähig (`branch-workflow.md:119-123`, `TODO.md:61`, `SANDBOX.md:98`).
   Nach dem Vorschlagswortlaut bräuchte jeder solche Merge Managementzuweisung
   und Privileg — unbeabsichtigte Verschärfung mit Betriebskosten.
7. **„Orthogonal" ist überzogen.** Abschnitt 4 widerlegt Abschnitt 2: Der
   Integrator ist konstruktiv privilegiert; ein Grunt darf nie Integrator sein.
   Korrekt: zwei Achsen mit **einschränkendem** Mapping.
8. **Fehlende Verantwortungen:** SUP.8 / `RQ-TRACE-01` (Eigentümer der Evidence
   Baseline), SWE.4 vs. SWE.6/SYS.5 (unabhängige Qualifikation), `T4`
   (Infrastruktur ohne Task und Eigentümer).
9. Kleineres: „einzige Rolle, deren Wirksamkeit sinkt" ist auch für Architekt
   und Integrator wahr; innerer Widerspruch zwischen Arbeitsprodukt
   „Prozessdefinitionen" und „keine Schreibprivilegien"; Autoritätsangabe im
   Kopf müsste `RQ-SRC-01` sein, nicht `DEC-0040-001`; Wortkollision
   „Zerlegung"; 5.2 Zeilen 3/4 gehören nach 5.1; `DEC-0040-001` fehlt die von
   `PRIVILEGED.md:107` verlangte **Dauer**.

### Der `0038-03`-Durchlauf des Architekten

> **Rollenzuweisung:** Selbstzuweisung Architekt *und* Implementierer war
> zulässig; `0038-03` trug keinen Knoten → 5.2 Zeile 2 erlaubt Zusammenlegung.
> **Das Modell greift hier nicht.**
> **Zuschnitt:** Aufzeichnungspflicht greift — aber der Datensatz stammt von
> derselben Instanz. Wirkstoff ist `RQ-DEC-05`, nicht die Rollentrennung.
> **TK-1:** `TODO.md:240` protokolliert für `0038-03` „Independent blocker/high
> review was clean". **TK-1 war faktisch erfüllt und hat den Mangel nicht
> gefunden.**
> **T7:** Die Rolle entsteht — aber Selbstzuweisung plus Tailoring hätten dazu
> geführt, dass sie dieselbe Session gewesen wäre.
> **Ergebnis:** Das Modell greift an genau einer Stelle wirklich, und diese
> Wirkung stammt aus dem Entscheidungsdatensatz, nicht aus der Rollentrennung.

### Auflagen des Architekten

- **A1** Achse 1 auf zwei Klassen korrigieren oder die dritte als eigenen,
  begründeten Antrag führen.
- **A2** TK-1 an `task-acceptance.md:68` angleichen, Waiver-Vertrag inklusive
  Dauer übernehmen, „Konsequenz für den laufenden Fall" streichen.
- **A3** 5.2 Zeile 2 streichen, ersetzen durch **TK-2 mit Reichweiten-Schlüssel**.
- **A4** Integrator-Zweck auf knotenkreuzende Merges begrenzen.
- **A5** QA-Manager: Schreibbereich präzisieren (eigenes append-only
  Befundregister, Schreibverbot am beurteilten Artefakt) und Eskalationskanal
  benennen oder als bis `0040-05` unwirksam markieren.

Stark empfohlen, nicht blockierend: Terminologie entkoppeln (RE:
„Anforderungszerlegung", Architekt: „Arbeitszuschnitt"); nicht abgedeckte
Verantwortungen benennen; `process_role` als heute unerzwungen kennzeichnen;
Abschnitt 8 um falsifizierbare Vorhersagen je Rolle erweitern.

---

## Teil B — Bewertung durch das Projektmanagement

**Verdikt: zustimmungsfähig mit Auflagen.**

> „Die **Substanz** ist richtig und billig zu haben […]. Die **Verpackung** —
> neun Tasks, sechs Rollen, zwei neue Werkzeuge, ASPICE-Verweise über den
> gesamten Dokumentenbestand — steht in keinem vertretbaren Verhältnis zum
> belegten Nutzen und wird an derselben Stelle scheitern wie die beiden
> Governance-Schichten davor."

### Der Adoptionsbefund

Der stärkste Einzelbefund der gesamten Bewertung, vom QA-Manager nachgeprüft
und bestätigt:

> Das Abnahmemodell (eingeführt 17.08.) hat **0 von 34** möglichen
> `Acceptance: ✓`-Einträgen erzeugt. Das Branch-Modell (305 Zeilen, eingeführt
> 17.08.) hat **0 Item-Branches** erzeugt — `git branch -a` kennt nur `main` und
> `tmp-work`. Zwei Prozessschichten aus den letzten 48 Stunden haben eine
> Adoptionsrate von exakt null. Eine dritte obendrauf ist keine
> Prozessverbesserung, sondern Bestandsaufbau.

### Aufwandsschätzung

Hergeleitet aus Referenzpunkten im Repo: `task-acceptance.md` 192 Zeilen,
`branch-workflow.md` 305 Zeilen, Werkzeuge in `_src/tools/` im Mittel ~360
Zeilen.

| Task | Sitzungen |
|---|---|
| 0040-01 Rollenmodell + Verankerung | 1,5–2 |
| 0040-02 fünf Briefings | 1–1,5 |
| 0040-03 Entscheidungsdatensatz | 1–1,5 |
| 0040-04 Traceability-Werkzeug | 3–4 |
| 0040-05 Eskalationssemantik | 2–3 |
| 0040-06 ASPICE-Verweise (71 Dateien) | 1–3 |
| 0040-07 Wirksamkeitsnachweis | 2–3 |
| 0040-08 Pilot | 0,5–1 |
| 0040-09 Integration | 1–2 |
| **Summe** | **13–21** |

Laufender Betrieb: **+8 bis +12 neue normative Dokumente** (~1.200–1.800 Zeilen
bindender Text); der ständig geladene Autoritätskern (≈65 KB) wächst um 15–20 %.
Rund **jede vierte Task** wird dokumentationspflichtig. Grobe Wirkung:
**+10–15 % auf jede künftige Task, +30–50 % auf jede Governance-Änderung** —
gegen einen Nutzen von **n = 1**.

### Was das Projektmanagement mitträgt

- **Das Blast-Radius-Kriterium ist die beste Idee im Paket** und spart
  nachweislich Geld: Der Vorfall blockiert seit dem 17.08. den Abschlusspfad
  aller Tasks. „Ein Entscheidungsdatensatz von fünf Minuten hätte den Zuschnitt
  vor ein Review gebracht. Das ist Prozess, der billiger ist als sein Ausfall."
- „Privileg ist nicht Unabhängigkeit" — ein Satz, der eine ganze Fehlerklasse
  abräumt, kostenlos.
- QA bewusst nicht privilegiert: „kontraintuitiv und richtig".
- `DEC-0040-004` (Ablehnung der Zeilen-/Symbolebene): „vorbildliche
  Kostendisziplin".
- 7 von 9 Tasks tragen eine No-Checkpoint-Begründung: „Der Architekt hat nicht
  überall ein Tor gesetzt. Das rechne ich hoch an."
- Abschnitt 8 selbst als Qualitätssignal.

### Was das Projektmanagement nicht mitträgt

1. **`0040-04` dupliziert Feature `0037`** — größter Einzelposten. `0037-17.02`
   (Provenance-Graph und Reverse-Indexe), `0037-17.03` (begrenzte
   Vorwärts-/Rückwärts-Trace-Query-APIs), `0037-10.04` (`issuectl … trace`)
   decken `RQ-TRACE-02/03/04` bereits ab. Befund E prüfte nur gegen `0039-01`.
2. **`0040-06` hat keinen begrenzten Zuschnitt** — 71 Dateien in
   `docs/pipeline/`; operativer Ertrag ohne Assessment-Absicht null. Wertvoll
   ist nur Befund A: fünf Zeilen.
3. **`0040-02`, fünf Briefings** — „Papier für einen Leser, der den Inhalt
   bereits geschrieben hat."
4. **`0040-07` skaliert mit der Korpusgröße** — bei 80 statt 1.500
   hinzugefügten Zeilen unverhältnismäßig.
5. **Sechs Rollen** — Kostentreiber ist nicht die Rollenzahl, sondern die vier
   Tailoring-Zeilen mit je eigener Datensatzpflicht.
6. **`0040` hat keinen Abschlusspfad.** `0040:0039-01` ist Abschlussgatter,
   `0039-01` steht auf `[u]` mit einer Reservierungssperre, die kein Agent lösen
   darf. „Das ist wissentlich ein Feature ohne Abschlusspfad."
7. **Opportunitätskosten und Reihenfolge.** 34 Tasks warten auf eine Abnahme,
   die es null Mal gab; 24 Claim-Dateien zu abgeschlossenen Tasks warten auf
   eine Reconciliation, die nie stattfand; zwei rote Testsuiten. Und:
   **„der Vorfall, der dieses Feature ausgelöst hat, ist unrepariert — keiner
   der neun Tasks repariert ihn."** `0040-08` schließt das ausdrücklich aus.
   „Neun Tasks Prozessdokumentation zu schreiben, während der dokumentierte
   Schaden weiterläuft, ist die falsche Reihenfolge."

### Gegenvorschlag des Projektmanagements

**Sofortpaket (~3 Sitzungen):** (1) Live-Blocker reparieren —
`automation_safety` aus der privilegierten Wirtsumgebung nehmen oder die
Kopplung in `_src/validate.py:640` auf beratend zurückstufen. (2) `0040-03-min`:
Blast-Radius-Kriterium plus Minimalformat, ~50 Zeilen. (3) `0040-05-min`: nur
die `AGENTS.md`-Änderung, ~20 Zeilen, Integrationsprüfung beibehalten.

**Danach (~1,5 Sitzungen):** (4) `0040-01-min`: ein **Abschnitt in `AGENTS.md`**,
keine neue Datei; drei Rollen; „Privileg ist nicht Unabhängigkeit";
Mindestklassen-Tabelle; TK-1 mit Klausel. RE und QA-Manager als **Hüte**, nicht
als Rollen. (5) `0040-08` bleibt.

**Streichen/verschieben:** `0040-02` streichen; `0040-04` in `0037-17.02/17.03`
einhängen; `0040-06` auf Befund A reduzieren; `0040-07` verschieben.

**Bilanz: 9 Tasks → 4 + 1 Reparatur; 13–21 → 3–5 Sitzungen (~25–30 %).**

### Auflagen des Projektmanagements

- **A1** Zuschnitt: nur das kleine Paket.
- **A2** Reihenfolge: Live-Blocker vor der ersten `0040`-Task.
- **A3** TK-1 erhält die Keine-zweite-Instanz-Klausel.
- **A4** Rollen auf drei reduziert; RE und QA als Hüte.
- **A5** Abschlusspfad: `0040:0039-01` auflösen oder `0039-01` freigeben.
- **A6** Wirksamkeits**messung** statt -**nachweis**: nach 20 Tasks zählen, wie
  viele Entscheidungsdatensätze geschrieben und wie viele Eskalationen
  ausgelöst wurden. „Bei null wird die Regel zurückgenommen, nicht ausgebaut."

K.-o.-Kriterien gegen die Umsetzung wie entworfen: A2, A3, A5.

---

## Vom QA-Manager nachgeprüfte Behauptungen

| Behauptung | Prüfung | Ergebnis |
|---|---|---|
| Zwei Fähigkeitsklassen, nicht drei | `SANDBOX.md:17-22`; `legacy_task_doctor.py:90,1132` | **bestätigt** |
| Null Item-Branches | `git branch -a` → nur `main`, `tmp-work` | **bestätigt** |
| Praktisch keine Abnahmen | ein einziger Acceptance-Treffer in `TODO.md` | **bestätigt** |
| `0037-17.02/17.03` decken Trace-APIs ab | `TODO.md:563,567,587` | **bestätigt** |
| `0038-03` hatte ein unabhängiges Review | `TODO.md:240` | **bestätigt** |

Damit sind alle tragenden Kritikpunkte belegt und keiner beruht auf einem
Missverständnis des Vorschlags.
