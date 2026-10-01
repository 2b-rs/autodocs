# Requirements-Analyse: Evidenz-Rückverfolgbarkeit, Entscheidungsumstände und Prozessrollen

**Status:** Informative Requirements-Analyse (RE-Arbeitsprodukt). **Keine
genehmigte Prozessdefinition und keine Automotive-SPICE-Capability-Aussage.**
Verbindlich wird hieraus erst, was über Feature `0039` (bzw. eine daraus
abgeleitete Task) beschlossen, dokumentiert und abgenommen wird.

- **Erhoben von:** Requirements-Engineer-Rolle, Session `agent:claude:re-intake:20260818T003223Z-845170c0e4da`
- **Erhoben am:** 2026-08-18T00:32:23Z (UTC)
- **Auftraggeber:** aktueller Benutzer (Kundenrolle)
- **Koordinationssatz:** `TODO-claude-re-intake-20260818T003223Z-845170c0e4da.md`
- **Auslösender Befund:** siehe [Abschnitt 2](#2-auslösender-befund-trigger)

---

## 1. Anforderung im Originalwortlaut

Verbatim übernommen, ungekürzt, als Rückverfolgbarkeitsanker (`RQ-SRC-01`):

> Ich habe hier ein neues Feature für dich. Ich bin Kunde, du bist Requirements
> Engineer bzw. Architekt. Bitte direkt mit Engineering anfangen und
> entsprechendes Bookkeeping sowie sonstige Prozesse berücksichtigen. Hier die
> Anforderung: ASPICE fordert (glaube ich), dass die Evidence Baseline erhalten
> bleibt und beidseitig rückverfolgbar ist, also auch von der Evidence Baseline
> in den Code. Die Umstände der Entscheidungsfindung (Zeitpunkt, Identität,
> fachilche Rechtfertigung) müssen ebenfalls dokumentiert werden. Deshlab meine
> Bitte: Erweitere die Beschreigung des Feature Breakdown-Prozeses, damit sowas
> nicht mehr passieren kann. Definiere nach Bedarf neue Rollen, z.B.
> Requirements Engineer und Architekt. Füge in die Prozessdokumentation wo
> möglich auch Verweise auf die zugrundeliegenden Normen (ASPICE) ein. Passe
> insbesondere die Agenteninstruktionen auf die neue Anforderung an. Stelle
> sicher, dass die Agenteninstruktionen die Prozessen auch tatsächlich
> verwirklichen. Prüfe, ob die Rollen Sandboxed/grunt, lokaler
> nichtprivilegierter Agent, und lokaler privilegierter Agent ausreichend für
> die Abbildung der ASPICE-Norm auf das hiesige technische Umfeld sind, oder ob
> für die Rollen Architekt(Verantwortlich für Acceptance Criteria),
> Integrator(Verantwortlicher für Review der Implementierung und des
> Integrationstests, Requirements Engineer (Verantwortlich für Prüfung und
> Analyse/Dekomposition eingehender Anforderungen) und QA-Manager
> (Verantwortlich für die Prozessqualität) evtl. noch zusätzliche
> Agentenprofile benötigt werden. Die Agenten müssen ja alle für ihre Rolle
> entsprechend gebrieft werden. Ich bitte dich hier die Rolle des
> Requirements-Engineers zu schlüpfen, meine Anforderungen also zu
> dokumentieren, zu analysieren, im Review mit mir zu hinterfragen, das
> Ergebnis zu dokumentieren und die Rückverfolgbarkeit sicherzustellen.
> Schlüpfe dann in die Rolle des QA-Managers und und halte den hier gelebten
> Prozess auch als allgemeine Regel für die Zukunft an geeigneten Stellen fest.
> Verweise auf geeignete Stellen in der ASPICE-Norm nicht vergessen. Los
> geht's!

Tippfehler des Originals sind bewusst nicht korrigiert; die Textidentität ist
Teil der Provenienz (`AGENTS.md` → *Check-in provenance*).

## 2. Auslösender Befund (Trigger)

Die Anforderung entstand aus einer Untersuchung am 2026-08-17/18. Der Befund ist
Teil der Anforderung, weil er den Zielzustand definiert („damit sowas nicht mehr
passieren kann"):

| Nr. | Beobachtung | Beleg |
|---|---|---|
| T1 | Task `0038-03` legte einen Skript-Prüfer über **alle** versionierten Skripte (aktuell 104) und koppelte ihn hart blockierend an `_src/validate.py`. Der Geltungsbereich war eine Zuschnittsentscheidung mit repo-weiter Blockadewirkung. | `TODO.md` Task `0038-03`; `_src/tools/automation_safety.py:2595` (`tracked_automation_paths`); `_src/validate.py:640` |
| T2 | Zum Umsetzungszeitpunkt war das Ergebnis grün (99 Dateien, null offene Befunde). Der Mangel war **latent** und durch das grüne Ergebnis verdeckt. | `TODO.md` Task `0038-03`, Closed-Eintrag; REF `ec251f2a6` |
| T3 | `_src/run-loop.sh` — die privilegierte Wirtsumgebung, die die Sandbox überhaupt erst herstellt — wurde in denselben Prüfmaßstab einbezogen wie sandboxinterne Automatisierung. | Scan-Ergebnis: 10 kritische Befunde, alle in `_src/run-loop.sh` |
| T4 | `_src/run-loop.sh` erscheint **in keiner Task und in keinem Claim**. Die zentralste Infrastrukturdatei des Repos wird ohne Zielzustand, Abnahmekriterien oder Eigentümer weiterentwickelt. | `grep "run-loop" TODO.md` → 0 Treffer; `grep -l "run-loop" TODO-*.md` → 0 Treffer |
| T5 | Änderungen an `run-loop.sh` (17.08., 15:21) machten die digest-gebundenen Freigaben ungültig und sperrten damit den Abschlusspfad **aller** Tasks. | 3 × `POLICY_STALE`; 10 × kritisch unresolved |
| T6 | Die Zuschnittsentscheidung aus T1 ist nirgends als Entscheidung dokumentiert: kein Zeitpunkt, keine entscheidende Identität, keine fachliche Rechtfertigung, keine Alternativenbetrachtung. | Kein Entscheidungsdatensatz in `TODO.md`, `docs/pipeline/automation-safety.md` oder Claim |
| T7 | Die Rolle, die einen solchen Zuschnitt hätte prüfen sollen (**Architekt**), wurde erst am 17.08. um 20:32 eingeführt — 14 Stunden nach der Umsetzung um 06:12. | `98fa57ce1` vs. `ec251f2a6` |
| T8 | Die Agenteninstruktionen **verhinderten** eine Eskalation aktiv: `AGENTS.md` schließt „a drafting defect" ausdrücklich als `[u]`-Grund aus und weist an, ohne Rückfrage fortzufahren. | `AGENTS.md` → *Autonomous backlog repair* |

**RE-Bewertung:** T6 und T8 sind die eigentlichen Prozessdefekte. T1–T5 sind
deren Symptome. Eine Prozesserweiterung, die nur T1 adressiert (Geltungsbereich
des Prüfers), würde die Wiederholung nicht verhindern.

## 3. Zerlegte Anforderungen mit stabilen IDs

Stabile IDs nach dem von Task `0039-01` geforderten Prinzip („stable acceptance
IDs"). Jede Anforderung ist einzeln prüfbar formuliert.

### 3.1 Evidenz und Rückverfolgbarkeit

| ID | Anforderung | Herkunft |
|---|---|---|
| `RQ-TRACE-01` | Die Evidence Baseline eines Features/Tasks bleibt über den Abschluss hinaus erhalten und wird nicht durch Nachfolgearbeit überschrieben oder gelöscht. | `RQ-SRC-01` |
| `RQ-TRACE-02` | Rückverfolgbarkeit ist **beidseitig**: von der Anforderung zur Evidenz *und* von der Evidenz zurück zur Anforderung. | `RQ-SRC-01` |
| `RQ-TRACE-03` | Rückverfolgbarkeit reicht bis **in den Code**: von der Evidenz auf die konkrete Codestelle (Datei, Bereich, Commit) und zurück. | `RQ-SRC-01` |
| `RQ-TRACE-04` | Die Verknüpfung ist maschinell prüfbar; fehlende oder gebrochene Enden werden als Befund gemeldet, nicht stillschweigend toleriert. | abgeleitet aus T2 |

### 3.2 Entscheidungsumstände

| ID | Anforderung | Herkunft |
|---|---|---|
| `RQ-DEC-01` | Jede prozessrelevante Entscheidung wird mit **Zeitpunkt** (ISO-8601 mit Zeitzone) festgehalten. | `RQ-SRC-01` |
| `RQ-DEC-02` | Jede solche Entscheidung wird mit der **Identität** der entscheidenden Instanz festgehalten (Session-/Rollenidentität, nicht bloß ein Anzeigename). | `RQ-SRC-01` |
| `RQ-DEC-03` | Jede solche Entscheidung wird mit ihrer **fachlichen Rechtfertigung** festgehalten. | `RQ-SRC-01` |
| `RQ-DEC-04` | Der Entscheidungsdatensatz ist append-only; Korrekturen ergänzen, ersetzen nicht. | abgeleitet, konsistent mit `task-acceptance.md` |
| `RQ-DEC-05` | Definiert ist, **welche** Entscheidungen dokumentationspflichtig sind. Ein Kriterium ist die **Reichweite**: Entscheidungen, die andere Arbeitseinheiten blockieren können, sind stets pflichtig. | abgeleitet aus T1/T6 |

### 3.3 Feature-Breakdown-Prozess

| ID | Anforderung | Herkunft |
|---|---|---|
| `RQ-PROC-01` | Die Beschreibung des Feature-Breakdown-Prozesses wird so erweitert, dass der Defekttyp aus Abschnitt 2 erkannt wird, bevor er umgesetzt wird. | `RQ-SRC-01` |
| `RQ-PROC-02` | Ein Task, der ein Tor einbaut, das andere Tasks blockieren kann, deklariert seinen Geltungsbereich als benannte, begründete Entscheidung. | abgeleitet aus T1 |
| `RQ-PROC-03` | Der Prozess benennt, wer den Zuschnitt prüft, und stellt sicher, dass diese Instanz **vor** der Umsetzung existiert und beteiligt ist. | abgeleitet aus T7 |
| `RQ-PROC-04` | Es existiert ein Eskalationspfad für latente Zuschnittsmängel, der nicht durch die Autonomieregel unterdrückt wird. | abgeleitet aus T8 |

### 3.4 Rollen

| ID | Anforderung | Herkunft |
|---|---|---|
| `RQ-ROLE-01` | Geprüft wird, ob Sandboxed/Grunt, lokal-nichtprivilegiert und lokal-privilegiert zur ASPICE-Abbildung genügen. | `RQ-SRC-01` |
| `RQ-ROLE-02` | Bei Bedarf werden Rollen definiert: Requirements Engineer, Architekt, Integrator, QA-Manager. | `RQ-SRC-01` |
| `RQ-ROLE-03` | Jede Rolle erhält ein **Briefing** — eine Instruktion, die sie befähigt, ihre Verantwortung tatsächlich wahrzunehmen. | `RQ-SRC-01` |
| `RQ-ROLE-04` | Verantwortungsgrenzen und Unabhängigkeitsanforderungen zwischen den Rollen sind explizit. | abgeleitet, konsistent mit `task-acceptance.md` |

### 3.5 Normbezug und Wirksamkeit

| ID | Anforderung | Herkunft |
|---|---|---|
| `RQ-STD-01` | Die Prozessdokumentation verweist an geeigneten Stellen auf die zugrundeliegende ASPICE-Systematik. | `RQ-SRC-01` |
| `RQ-STD-02` | Verweise unterscheiden **Prozessunterstützung** von **bewerteter Capability**; es wird keine Konformität behauptet, die nicht bewertet wurde. | Task `0039-01` DoD; Feature `0039` Study baseline |
| `RQ-EFF-01` | Die Agenteninstruktionen **verwirklichen** die Prozesse tatsächlich — Prozessdoku und Instruktion widersprechen sich nicht und die Instruktion ist für die Rolle handlungsleitend. | `RQ-SRC-01` |

## 4. RE-Analyse: Prüfung der Anforderungsprämisse

Ein Requirements Engineer nimmt die Kundenprämisse auf, prüft sie aber. Der
Kunde hat sie selbst als unsicher markiert („glaube ich"). Ergebnis:

### Befund A — „Evidence Baseline" ist hier ein Eigenbegriff, kein ASPICE-Begriff

„Evidence baseline" stammt aus dem Ziel von Feature `0038` dieses Repos und
bezeichnet dort eine **Liste belegter Vorfälle**, die eine Verbesserung
begründet. Automotive SPICE kennt den Begriff so nicht.

Was der Kunde inhaltlich meint, verteilt sich auf zwei ASPICE-Konzepte:

- **Baseline** im Sinne von **SUP.8 Configuration Management** (BP „Establish
  baselines"): ein eingefrorener, identifizierter, wiederherstellbarer Stand von
  Arbeitsprodukten.
- **Bidirektionale Rückverfolgbarkeit** im Sinne der Basispraktiken von
  **SWE.1–SWE.6** bzw. **SYS.2–SYS.5**: zwischen Anforderung, Architektur, Code
  und Verifikationsergebnis.

**Konsequenz:** Der Begriff muss im Prozess sauber getrennt werden, sonst baut
man zwei verschiedene Dinge unter einem Namen. Vorschlag zur Trennung:

- *Evidence Baseline* (Repo-Begriff, beibehalten) = eingefrorene Belegmenge zu
  einem Abschluss.
- *Traceability* = die beidseitige Verknüpfung, die `RQ-TRACE-02/03` fordert.

### Befund B — Die Prämisse ist im Kern richtig

ASPICE fordert bidirektionale Rückverfolgbarkeit tatsächlich, und zwar
durchgängig als Basispraktik in den Engineering-Prozessen (jeweils eine BP der
Form „Establish bidirectional traceability" plus eine BP „Ensure consistency").
Die Forderung „auch von der Evidenz in den Code" entspricht genau der
Rückrichtung, die ASPICE ausdrücklich mitverlangt — Rückverfolgbarkeit nur
vorwärts erfüllt die Praktik nicht.

Ebenso richtig: Entscheidungen mit Zeitpunkt, verantwortlicher Instanz und
Begründung festzuhalten, ist in ASPICE über **SUP.10 Change Request Management**
(Genehmigung vor Umsetzung, Statusverfolgung) und über die
Capability-Level-2-Attribute (**PA 2.1**, definierte Verantwortlichkeiten und
Befugnisse; **PA 2.2**, kontrollierte Arbeitsprodukte) verankert.

### Befund C — Die vorhandenen drei Klassen sind keine Rollen

Das ist die zentrale RE-Erkenntnis zu `RQ-ROLE-01`.

Sandboxed/Grunt, lokal-nichtprivilegiert und lokal-privilegiert sind
**Fähigkeitsklassen**: sie beschreiben, *was eine Session technisch ausführen
darf* (Shell, Git, Netz, Anmeldedaten). ASPICE-Rollen beschreiben, *wofür jemand
fachlich verantwortlich ist*.

Das sind **zwei orthogonale Achsen**, nicht eine unvollständige. Die Frage
„reichen die drei Klassen aus" hat daher die Antwort: sie sind nicht zu wenige,
sie sind die falsche Achse für diesen Zweck. Benötigt wird eine Zuordnung
**Fähigkeitsklasse × Prozessrolle**, in der beide Angaben unabhängig geführt
werden.

Belegend im Bestand: `AGENTS.md` sagt bereits „privilege alone is not authority
or independence" und trennt Architekt, Implementierer und Integrator als
„distinct roles" — die Trennung ist also angelegt, aber noch nicht als eigene
Achse ausgeführt. `docs/pipeline/roles.md` beschreibt eine **dritte**, wieder
andere Achse (Produktdomäne: Kurator, KI-Entscheider, Validator) und ist für
diese Frage nicht einschlägig.

### Befund D — Der QA-Manager braucht Unabhängigkeit, nicht Privilegien

**SUP.1 Quality Assurance** verlangt, dass die Qualitätssicherung mit
Unabhängigkeit und Eskalationsbefugnis gegenüber der Projektdurchführung agiert.
Das ist im vorliegenden Modell nicht durch eine Fähigkeitsklasse abbildbar — ein
privilegierter Agent ist mächtig, aber nicht dadurch unabhängig. `AGENTS.md`
enthält dazu bereits die passende Formulierung für den Abnahmeprüfer
(„normally independent of the claim owner"), aber keine entsprechende Regel für
Prozessqualität.

### Befund E — Es existiert bereits eine reservierte Task für diesen Auftrag

`0039-01` („Define, pilot, and baseline the standard Feature definition and
breakdown process") deckt große Teile von `RQ-PROC-*`, `RQ-ROLE-*` und
`RQ-STD-*` bereits ab, einschließlich „bidirectional implementation-and-
verification coverage" und „role/action tables". Ihre Vorbedingung `0039-04` ist
terminal (`[x]`, REF `924eeaf59`).

Neu gegenüber `0039-01` sind ausschließlich:

- `RQ-TRACE-03` (Rückverfolgbarkeit bis in den Code, Rückrichtung explizit),
- `RQ-DEC-01/02/03/05` (Entscheidungsumstände als eigenes Artefakt),
- `RQ-ROLE-03` (Rollen-Briefings als Instruktionsartefakt),
- `RQ-EFF-01` (Nachweis, dass Instruktionen den Prozess wirklich verwirklichen).

**Konsequenz:** Es sollte kein neues Feature entstehen, das `0039-01` dupliziert.
Entweder werden die vier neuen Punkte in `0039-01` aufgenommen, oder sie werden
ein eigenes Feature mit `0039-01` als Vorbedingung. Diese Entscheidung liegt
beim Kunden (siehe offene Frage OQ-2).

### Befund F — Harte Autoritätssperre

Feature `0039` trägt eine ausdrückliche Reservierung:

> „No agent may autonomously claim or start this Feature or any of its Tasks. A
> current user must explicitly select the Task and designate the owning session
> as privileged before its marker may leave `[u]`."

Diese Sperre kann eine Agentensession nicht selbst aufheben; `AGENTS.md`
verbietet ausdrücklich, Genehmigung zu erfinden. Die Benennung der Session als
privilegiert ist daher ein eigener, ausdrücklicher Akt des Benutzers (OQ-1).

## 5. Vorläufige ASPICE-Zuordnung

Zuordnung als **Prozessunterstützung**, nicht als bewertete Capability
(`RQ-STD-02`). Sie ist als Analysegrundlage zu lesen und vor Übernahme in
normative Dokumente gegen die jeweils gültige Fassung des PAM zu prüfen.

| Anforderung | ASPICE-Bezug | Art des Bezugs |
|---|---|---|
| `RQ-TRACE-01` | SUP.8 (Baselines etablieren, Änderungskontrolle an Arbeitsprodukten) | direkt |
| `RQ-TRACE-02`, `RQ-TRACE-03` | SWE.1–SWE.6 / SYS.2–SYS.5, jeweils BP „bidirectional traceability" + BP „consistency" | direkt |
| `RQ-TRACE-04` | PA 2.2 (kontrollierte Arbeitsprodukte); SUP.1 (Prüfung auf Einhaltung) | unterstützend |
| `RQ-DEC-01/02/03` | SUP.10 (Genehmigung und Statusverfolgung von Änderungen); PA 2.1 (Verantwortlichkeiten/Befugnisse) | direkt |
| `RQ-DEC-04` | SUP.8 (Auditierbarkeit, Wiederherstellbarkeit) | unterstützend |
| `RQ-PROC-01/02/03` | MAN.3 (Arbeitspakete, Schnittstellen); SWE.2/SYS.3 (Architekturentscheidungen) | direkt |
| `RQ-PROC-04` | SUP.9 (Problemlösung mit Eskalation) | direkt |
| `RQ-ROLE-01/02/04` | PA 2.1 GP „Verantwortlichkeiten und Befugnisse definieren und zuweisen" | direkt |
| `RQ-ROLE-03` | PA 2.1 (Kompetenz/Vorbereitung der Beteiligten) | unterstützend |
| QA-Manager-Rolle | **SUP.1**, insbesondere Unabhängigkeit und Eskalationsrecht | direkt |
| RE-Rolle | SWE.1 / SYS.2 | direkt |
| Architekt-Rolle | SWE.2 / SYS.3 | direkt |
| Integrator-Rolle | SWE.5 / SYS.4 (Integration und Integrationsverifikation) | direkt |

**Vorbehalt:** Dieses Repository führt unter den Features `0011`–`0032` bereits
eine ASPICE-Bewertung für ein **ECU-Produkt**. Die hier behandelte Anwendung von
ASPICE auf den **eigenen Entwicklungsprozess des Repos** ist ein davon
getrennter Gegenstand. Beide dürfen nicht vermischt werden; insbesondere darf
aus dieser Analyse keine Aussage über die ECU-Bewertung abgeleitet werden und
umgekehrt.

## 6. Offene Fragen an den Kunden (Review)

| ID | Frage | Warum sie blockiert |
|---|---|---|
| `OQ-1` | Benennt der Kunde diese Session ausdrücklich als privilegierte Eignersession für die betroffene `0039`-Task? | Feature `0039` trägt eine Reservierungssperre, die eine Agentensession nicht selbst aufheben darf (Befund F). |
| `OQ-2` | Werden die vier neuen Punkte in `0039-01` aufgenommen, oder entstehen sie als eigenes Feature mit `0039-01` als Vorbedingung? | Bestimmt, ob eine bestehende Task geändert oder ein neues Feature angelegt wird (Befund E). |
| `OQ-3` | Wie weit soll die Rückverfolgbarkeit „in den Code" reichen — Commit-Ebene, Dateiebene oder Zeilen-/Symbolebene? | Bestimmt Aufwand und Werkzeugbedarf für `RQ-TRACE-03` um Größenordnungen. |
| `OQ-4` | Sollen die neuen Rollen als **zusätzliche Achse** neben den Fähigkeitsklassen geführt werden (Befund C), oder wünscht der Kunde ausdrücklich neue Agentenprofile als eigene Klassen? | Bestimmt die Grundstruktur des Rollenmodells und damit alle Folgedokumente. |
| `OQ-5` | Soll der Vorfall aus Abschnitt 2 (`0038-03`) als **Pilot** rückwirkend mit dem neuen Prozess bewertet werden? | `0039-01` verlangt ohnehin zwei Pilotanwendungen; der Vorfall wäre ein belastbarer, bereits belegter Kandidat. |

## 6a. Review-Ergebnis und Entscheidungsdatensätze

Das Review mit dem Kunden fand am 2026-08-18 statt. Die vier Entscheidungen
sind unten im **vorläufigen** Entscheidungsdatensatz-Format festgehalten. Dieses
Format ist bewusst die erste Anwendung von `RQ-DEC-01/02/03` auf den eigenen
Vorgang; Task `0040-03` formalisiert es normativ und darf es dabei ändern.
Bestandsschutz hat der Inhalt, nicht die Form.

---

### `DEC-0040-001` — Autoritätsbenennung für Feature `0039`/`0040`

- **Zeitpunkt:** 2026-08-18T00:32:23Z (Reviewzeitpunkt; Aufnahme unmittelbar danach)
- **Entscheidende Instanz:** aktueller Benutzer (Managementautorität im Sinne des `TODO.md`-Headers)
- **Gegenstand:** `OQ-1` — Reservierungssperre Feature `0039`
- **Entscheidung:** Die Session `agent:claude:re-intake:20260818T003223Z-845170c0e4da` wird **vollprivilegiert** als Eignersession benannt, einschließlich Abnahmebefugnis.
- **Fachliche Rechtfertigung (Benutzer):** ausdrückliche Auswahl der Option „Vollprivilegiert benennen" im Review.
- **Abweichung und Kompensation:** Der RE hat vorab darauf hingewiesen, dass damit Entwurf und Abnahme in einer Hand liegen und dies der in `AGENTS.md` geforderten Unabhängigkeit (`normally independent of the claim owner, principal implementer, decisive technical author`) sowie der SUP.1-Unabhängigkeit widerspricht. Der Kunde hat die Option in Kenntnis dieses Hinweises gewählt. Dies ist damit ein **ausdrücklicher, begrenzter Autoritätsverzicht** („bounded authority waiver") im Sinne von `AGENTS.md`, nicht eine stillschweigende Selbstermächtigung.
  - **Geltungsbereich des Verzichts:** Feature `0040` und die zu seiner Umsetzung nötigen Änderungen; **nicht** Feature `0039` selbst, dessen Tasks `0039-01/02/03/05` `[u]` bleiben.
  - **Kompensierende Maßnahme:** Jede Abnahme, die diese Session an eigener Arbeit vornimmt, wird als solche gekennzeichnet und benennt `DEC-0040-001` als Autoritätsreferenz, sodass eine spätere unabhängige Instanz sie gezielt nachprüfen kann.

### `DEC-0040-002` — Zuschnitt: eigenes Feature `0040`

- **Zeitpunkt:** 2026-08-18T00:32:23Z
- **Entscheidende Instanz:** aktueller Benutzer
- **Gegenstand:** `OQ-2` — Aufnahme in `0039-01` oder eigenes Feature
- **Entscheidung:** Eigenes **Feature `0040`**; die Arbeit wird dort als mehrere Tasks geführt („Die Arbeit soll als weitere Tasks zu Feature 40 hinzukommen").
- **Fachliche Rechtfertigung:** `0039-01` ist bereits sehr umfangreich und trägt die Reservierungssperre; eine Aufnahme dort würde die neue Anforderung mitsperren und erst mit dem Gesamtpaket fertig werden lassen. Ein eigenes Feature macht sie eigenständig planbar und sichtbar.
- **Architekturfolge (RE/Architekt):** `0040:0039-01` wird als **Feature-Abschluss-Vorbedingung** geführt, nicht als Startsperre. Damit kann `0040` sofort beginnen, kann aber nicht nach `DONE.md`, bevor die Basisprozessdefinition aus `0039-01` steht — das verhindert zwei konkurrierende Prozessdefinitionen.

### `DEC-0040-003` — Rollenmodell: zwei Achsen **mit** Mapping

- **Zeitpunkt:** 2026-08-18T00:32:23Z
- **Entscheidende Instanz:** aktueller Benutzer
- **Gegenstand:** `OQ-4` — Rollen als eigene Achse oder als neue Agentenprofile
- **Entscheidung:** Zwei getrennte Achsen (Fähigkeitsklasse × Prozessrolle), **zusätzlich** eine verbindliche Mapping-Tabelle von Prozessrollen auf Agentenprofile („Trotzdem soll es natürlich ein Mapping geben von Rollen auf Agentenprofile").
- **Fachliche Rechtfertigung:** Die Achsentrennung bildet ASPICE korrekt ab und erklärt, warum „privilegiert" nicht „unabhängig" bedeutet (Befund C/D). Das geforderte Mapping verhindert zugleich, dass die Trennung praktisch folgenlos bleibt: Ohne Zuordnung wüsste keine Session, welches Profil sie für eine Rolle braucht.
- **Präzisierung durch den RE:** Das Mapping ist keine 1:1-Zuordnung, sondern legt je Rolle die **Mindest-Fähigkeitsklasse** und etwaige **Unvereinbarkeiten** fest (z. B. QA-Manager darf nicht zugleich Implementierer desselben Gegenstands sein).

### `DEC-0040-004` — Rückverfolgbarkeitstiefe: Datei- und Commit-Ebene

- **Zeitpunkt:** 2026-08-18T00:32:23Z
- **Entscheidende Instanz:** aktueller Benutzer
- **Gegenstand:** `OQ-3` — Tiefe der Evidenz-zu-Code-Verknüpfung
- **Entscheidung:** **Datei- und Commit-Ebene.**
- **Fachliche Rechtfertigung:** Mit Git-Bordmitteln und einem Prüfskript umsetzbar, bleibt bei Refactorings stabil und erfüllt die ASPICE-Praktik in der Regel. Zeilen-/Symbolebene wurde ausdrücklich verworfen, weil sie dieselbe Sprengfalle erzeugt wie die digest-gebundenen Freigaben aus Befund T5.
- **Folge für `RQ-TRACE-03`:** Die Anforderung ist auf Datei- und Commit-Auflösung zu präzisieren; Zeilen-/Symbolgenauigkeit ist ausdrücklich **kein** Abnahmekriterium.

---

### Additive Legacy-Map-/Abweichungsdisposition

Alle vier vorstehenden historischen Datensätze bleiben bytegetreu erhalten und
sind **strukturell nicht konform** zur exakten Grammatik von
[`decision-record@v1`](../pipeline/decision-record.md). Weder ihre Originalform
noch Original plus folgende Map sind als `decision-record@v1` parsebar oder so
zu bezeichnen. Die Maps verwenden stattdessen das getrennte, normative Format
`decision-record-legacy-map@v1`: Sie dokumentieren die Abweichung und projizieren
die rekonstruierbare Semantik, ohne Geschichte zu ersetzen oder eine neue
Managemententscheidung zu erfinden.

Der additive Identitätsanker
`legacy-authority:re-intake-review:RQ-SRC-01:2026-08-18T00:32:23Z` bezeichnet
stabil das bereits protokollierte historische Kundenreview. Er erfindet keine
persönliche Identität. Map-Autor ist die bestehende Task-Koordination
`agent:zed:0040-03:20260818T154851Z-1d9d90dcf61d`; dadurch wird keine
Entscheidungsautorität über den historischen Inhalt beansprucht.

#### `DEC-0040-001-LM001`

- **Map format:** `decision-record-legacy-map@v1`
- **Target record:** `DEC-0040-001`
- **Source path:** `docs/dossiers/re-intake-evidence-traceability-and-roles.md#dec-0040-001`
- **Map recorded at:** `2026-08-18T18:09:02+02:00`
- **Mapping identity:** `agent:zed:0040-03:20260818T154851Z-1d9d90dcf61d`
- **Mapping role:** `Implementierer`
- **Mapping authority reference:** `task:0040-03`
- **Structural disposition:** `legacy-structurally-nonconforming`
- **Semantic disposition:** `incomplete`
- **Missing semantic fields:** `Waiver.Duration`
- **Deviation:** Der historische Block verwendet deutsche, unvollständige Legacy-Felder statt der geschlossenen v1-Feldfolge; zusätzlich fehlt die ausschließlich von Management festzulegende Waiver-Dauer.
- **Semantic projection JSON:**
  ```json
  {"recorded_at":"2026-08-18T00:32:23Z","deciding_identity":"legacy-authority:re-intake-review:RQ-SRC-01:2026-08-18T00:32:23Z","role":"Management","authority_reference":"RQ-SRC-01;section-6a-customer-review","subject":"OQ-1 — Reservierungssperre Feature 0039","decision":"Die benannte RE-Session wird für Feature 0040 vollprivilegierte Eignersession einschließlich Abnahmebefugnis.","technical_justification":"Management wählte im Review ausdrücklich die Option Vollprivilegiert benennen, nachdem der Unabhängigkeitskonflikt offengelegt worden war.","triggers":["authority-tailoring-or-waiver","cross-item-blast-radius"],"considered_alternatives":[{"id":"ALT-01","text":"Vollprivileg einschließlich Abnahmebefugnis","disposition":"selected","reason":"Ausdrückliche Managementauswahl im Review."},{"id":"ALT-02","text":"Keine privilegierte Benennung","disposition":"rejected","reason":"Nicht vom Management ausgewählte binäre Gegenoption."}],"consequences":[{"id":"CON-01","text":"Selbstabnahmen im Scope sind als solche zu kennzeichnen und später unabhängig nachzuprüfen."}],"affected_work_units":["feature:0040"],"affected_gates":["integration:0040","feature-closure:0040"],"review_participation":[{"id":"PART-01","identity":"agent:claude:re-intake:20260818T003223Z-845170c0e4da","role":"Requirements Engineer","participation":"reviewed","position":"no-position","note":"Legte den Unabhängigkeitskonflikt vor der Managementauswahl offen."}],"no_review_reason":null,"waiver":{"type":"bounded","conflict":"Entwurf und Abnahme liegen innerhalb des Scopes in derselben Session.","reason":"Ausdrückliche Managementauswahl der vollprivilegierten Option.","scope":"Feature 0040 und nötige Änderungen; nicht Feature 0039.","duration":null,"compensating_controls":[{"id":"CTRL-01","text":"Jede Selbstabnahme nennt DEC-0040-001 und einen gezielten unabhängigen Nachprüfauftrag."}]}}
  ```
- **Source bindings JSON:**
  ```json
  {"recorded_at":["legacy:Zeitpunkt"],"deciding_identity":["additive:historical-authority-anchor"],"role":["legacy:Entscheidende Instanz"],"authority_reference":["legacy:review-context"],"subject":["legacy:Gegenstand"],"decision":["legacy:Entscheidung"],"technical_justification":["legacy:Fachliche Rechtfertigung (Benutzer)","legacy:Abweichung und Kompensation"],"triggers":["legacy:Abweichung und Kompensation","additive:trigger-classification"],"considered_alternatives":["legacy:Gegenstand","legacy:Fachliche Rechtfertigung (Benutzer)"],"consequences":["legacy:Kompensierende Maßnahme"],"affected_work_units":["legacy:Geltungsbereich des Verzichts"],"affected_gates":["additive:gate-classification"],"review_participation":["legacy:Abweichung und Kompensation"],"no_review_reason":["additive:not-applicable"],"waiver":["legacy:Abweichung und Kompensation","legacy:Geltungsbereich des Verzichts","legacy:Kompensierende Maßnahme","additive:missing-management-owned-duration"]}
  ```

#### `DEC-0040-002-LM001`

- **Map format:** `decision-record-legacy-map@v1`
- **Target record:** `DEC-0040-002`
- **Source path:** `docs/dossiers/re-intake-evidence-traceability-and-roles.md#dec-0040-002`
- **Map recorded at:** `2026-08-18T18:09:02+02:00`
- **Mapping identity:** `agent:zed:0040-03:20260818T154851Z-1d9d90dcf61d`
- **Mapping role:** `Implementierer`
- **Mapping authority reference:** `task:0040-03`
- **Structural disposition:** `legacy-structurally-nonconforming`
- **Semantic disposition:** `complete`
- **Missing semantic fields:** `none`
- **Deviation:** Der historische Block ist semantisch vollständig rekonstruierbar, verwendet aber deutsche Legacy-Felder statt der geschlossenen v1-Feldfolge und bleibt deshalb strukturell nicht konform.
- **Semantic projection JSON:**
  ```json
  {"recorded_at":"2026-08-18T00:32:23Z","deciding_identity":"legacy-authority:re-intake-review:RQ-SRC-01:2026-08-18T00:32:23Z","role":"Management","authority_reference":"RQ-SRC-01;section-6a-customer-review","subject":"OQ-2 — Aufnahme in 0039-01 oder eigenes Feature","decision":"Die Arbeit wird als eigenes Feature 0040 mit mehreren Tasks geführt.","technical_justification":"0039-01 ist umfangreich und reserviert; ein eigenes Feature macht die neue Anforderung eigenständig planbar, während die Abschlussvorbedingung konkurrierende Prozessdefinitionen verhindert.","triggers":["material-architecture-or-repository-behavior","cross-item-blast-radius"],"considered_alternatives":[{"id":"ALT-01","text":"Eigenes Feature 0040","disposition":"selected","reason":"Eigenständig planbar und sichtbar bei erhaltener Abschlusskopplung."},{"id":"ALT-02","text":"Aufnahme in 0039-01","disposition":"rejected","reason":"Würde die neue Anforderung mit der umfangreichen reservierten Task mitsperren."}],"consequences":[{"id":"CON-01","text":"0040 kann beginnen, aber erst nach 0039-01 abschließen."}],"affected_work_units":["feature:0039","task:0039-01","feature:0040"],"affected_gates":["feature-closure:0040"],"review_participation":[{"id":"PART-01","identity":"agent:claude:re-intake:20260818T003223Z-845170c0e4da","role":"Requirements Engineer","participation":"consulted","position":"supports","note":"Analysierte die Reservierung und leitete die Abschlusskopplung ab."}],"no_review_reason":null,"waiver":{"type":"none"}}
  ```
- **Source bindings JSON:**
  ```json
  {"recorded_at":["legacy:Zeitpunkt"],"deciding_identity":["additive:historical-authority-anchor"],"role":["legacy:Entscheidende Instanz"],"authority_reference":["legacy:review-context"],"subject":["legacy:Gegenstand"],"decision":["legacy:Entscheidung"],"technical_justification":["legacy:Fachliche Rechtfertigung","legacy:Architekturfolge (RE/Architekt)"],"triggers":["legacy:Architekturfolge (RE/Architekt)","additive:trigger-classification"],"considered_alternatives":["legacy:Gegenstand","legacy:Fachliche Rechtfertigung"],"consequences":["legacy:Architekturfolge (RE/Architekt)"],"affected_work_units":["legacy:Entscheidung","legacy:Architekturfolge (RE/Architekt)"],"affected_gates":["legacy:Architekturfolge (RE/Architekt)"],"review_participation":["legacy:Architekturfolge (RE/Architekt)"],"no_review_reason":["additive:not-applicable"],"waiver":["additive:no-waiver-required"]}
  ```

#### `DEC-0040-003-LM001`

- **Map format:** `decision-record-legacy-map@v1`
- **Target record:** `DEC-0040-003`
- **Source path:** `docs/dossiers/re-intake-evidence-traceability-and-roles.md#dec-0040-003`
- **Map recorded at:** `2026-08-18T18:09:02+02:00`
- **Mapping identity:** `agent:zed:0040-03:20260818T154851Z-1d9d90dcf61d`
- **Mapping role:** `Implementierer`
- **Mapping authority reference:** `task:0040-03`
- **Structural disposition:** `legacy-structurally-nonconforming`
- **Semantic disposition:** `complete`
- **Missing semantic fields:** `none`
- **Deviation:** Der historische Block ist semantisch vollständig rekonstruierbar, verwendet aber deutsche Legacy-Felder statt der geschlossenen v1-Feldfolge und bleibt deshalb strukturell nicht konform.
- **Semantic projection JSON:**
  ```json
  {"recorded_at":"2026-08-18T00:32:23Z","deciding_identity":"legacy-authority:re-intake-review:RQ-SRC-01:2026-08-18T00:32:23Z","role":"Management","authority_reference":"RQ-SRC-01;section-6a-customer-review","subject":"OQ-4 — Rollenachse oder neue Agentenprofile","decision":"Fähigkeitsklasse und Prozessrolle bleiben getrennte Achsen mit verbindlichem Mapping.","technical_justification":"Die Achsentrennung bildet Verantwortung und technische Befugnis korrekt getrennt ab; das Mapping macht die Trennung praktisch handlungsleitend.","triggers":["material-architecture-or-repository-behavior"],"considered_alternatives":[{"id":"ALT-01","text":"Getrennte Achsen mit verbindlichem Mapping","disposition":"selected","reason":"Trennt Privileg von Verantwortung und bleibt operativ eindeutig."},{"id":"ALT-02","text":"Neue Agentenprofile als Rollenklassen","disposition":"rejected","reason":"Vermischt technische Fähigkeit und fachliche Verantwortung."}],"consequences":[{"id":"CON-01","text":"Jede Prozessrolle erhält Mindestklasse und Unvereinbarkeiten."}],"affected_work_units":["feature:0040","task:0040-01","path:docs/pipeline/process-roles.md"],"affected_gates":["none"],"review_participation":[{"id":"PART-01","identity":"agent:claude:re-intake:20260818T003223Z-845170c0e4da","role":"Requirements Engineer","participation":"consulted","position":"supports","note":"Präzisierte das Mapping als Mindestklasse plus Unvereinbarkeiten."}],"no_review_reason":null,"waiver":{"type":"none"}}
  ```
- **Source bindings JSON:**
  ```json
  {"recorded_at":["legacy:Zeitpunkt"],"deciding_identity":["additive:historical-authority-anchor"],"role":["legacy:Entscheidende Instanz"],"authority_reference":["legacy:review-context"],"subject":["legacy:Gegenstand"],"decision":["legacy:Entscheidung"],"technical_justification":["legacy:Fachliche Rechtfertigung","legacy:Präzisierung durch den RE"],"triggers":["legacy:Entscheidung","additive:trigger-classification"],"considered_alternatives":["legacy:Gegenstand","legacy:Fachliche Rechtfertigung"],"consequences":["legacy:Präzisierung durch den RE"],"affected_work_units":["legacy:Entscheidung","additive:scope-classification"],"affected_gates":["additive:no-affected-gate"],"review_participation":["legacy:Präzisierung durch den RE"],"no_review_reason":["additive:not-applicable"],"waiver":["additive:no-waiver-required"]}
  ```

#### `DEC-0040-004-LM001`

- **Map format:** `decision-record-legacy-map@v1`
- **Target record:** `DEC-0040-004`
- **Source path:** `docs/dossiers/re-intake-evidence-traceability-and-roles.md#dec-0040-004`
- **Map recorded at:** `2026-08-18T18:09:02+02:00`
- **Mapping identity:** `agent:zed:0040-03:20260818T154851Z-1d9d90dcf61d`
- **Mapping role:** `Implementierer`
- **Mapping authority reference:** `task:0040-03`
- **Structural disposition:** `legacy-structurally-nonconforming`
- **Semantic disposition:** `complete`
- **Missing semantic fields:** `none`
- **Deviation:** Der historische Block ist semantisch vollständig rekonstruierbar, verwendet aber deutsche Legacy-Felder statt der geschlossenen v1-Feldfolge und bleibt deshalb strukturell nicht konform.
- **Semantic projection JSON:**
  ```json
  {"recorded_at":"2026-08-18T00:32:23Z","deciding_identity":"legacy-authority:re-intake-review:RQ-SRC-01:2026-08-18T00:32:23Z","role":"Management","authority_reference":"RQ-SRC-01;section-6a-customer-review","subject":"OQ-3 — Tiefe der Evidenz-zu-Code-Verknüpfung","decision":"Rückverfolgbarkeit wird auf Datei- und Commit-Ebene geführt.","technical_justification":"Diese Tiefe ist mit vorhandenen Mitteln umsetzbar und refactoringstabil; Zeilen- oder Symbolbindung würde spröde Freigabekopplungen wiederholen.","triggers":["material-architecture-or-repository-behavior"],"considered_alternatives":[{"id":"ALT-01","text":"Datei- und Commit-Ebene","disposition":"selected","reason":"Umsetzbar, stabil und für die geforderte Rückverfolgbarkeit ausreichend."},{"id":"ALT-02","text":"Zeilen- und Symbolebene","disposition":"rejected","reason":"Zu spröde bei Refactorings und vergleichbar mit den problematischen digest-gebundenen Freigaben."}],"consequences":[{"id":"CON-01","text":"RQ-TRACE-03 verlangt keine Zeilen- oder Symbolgenauigkeit."}],"affected_work_units":["feature:0040","task:0040-04"],"affected_gates":["none"],"review_participation":[{"id":"PART-01","identity":"agent:claude:re-intake:20260818T003223Z-845170c0e4da","role":"Requirements Engineer","participation":"consulted","position":"supports","note":"Präzisierte RQ-TRACE-03 entsprechend der ausgewählten Tiefe."}],"no_review_reason":null,"waiver":{"type":"none"}}
  ```
- **Source bindings JSON:**
  ```json
  {"recorded_at":["legacy:Zeitpunkt"],"deciding_identity":["additive:historical-authority-anchor"],"role":["legacy:Entscheidende Instanz"],"authority_reference":["legacy:review-context"],"subject":["legacy:Gegenstand"],"decision":["legacy:Entscheidung"],"technical_justification":["legacy:Fachliche Rechtfertigung"],"triggers":["legacy:Fachliche Rechtfertigung","additive:trigger-classification"],"considered_alternatives":["legacy:Gegenstand","legacy:Fachliche Rechtfertigung"],"consequences":["legacy:Folge für RQ-TRACE-03"],"affected_work_units":["legacy:Folge für RQ-TRACE-03","additive:scope-classification"],"affected_gates":["additive:no-affected-gate"],"review_participation":["legacy:Folge für RQ-TRACE-03"],"no_review_reason":["additive:not-applicable"],"waiver":["additive:no-waiver-required"]}
  ```

Damit bleiben `DEC-0040-001` … `DEC-0040-004` sämtlich strukturell
nicht konform zu `decision-record@v1`. Die Legacy-Maps weisen
`DEC-0040-002` … `DEC-0040-004` als **semantisch vollständig** aus, ohne
Formatkonformität zu behaupten. `DEC-0040-001` ist zusätzlich semantisch
unvollständig, ausschließlich weil `Waiver.Duration` fehlt; nur Management darf
diese Dauer in einem neuen append-only Autoritätsereignis festlegen.

**Offen geblieben:** `OQ-5` (Rückwirkende Pilotbewertung des Vorfalls `0038-03`)
wurde im Review nicht beantwortet. Der Architekt nimmt sie als Task `0040-08`
auf, weil `0039-01` ohnehin zwei Pilotanwendungen verlangt und der Vorfall ein
bereits vollständig belegter Kandidat ist. Diese Aufnahme ist eine
Architektenentscheidung, keine Kundenentscheidung; sie ist als solche in
`TODO.md` gekennzeichnet und kann folgenlos gestrichen werden.

## 7. Nächste Schritte nach Klärung

1. Bookkeeping gemäß `OQ-2` anlegen (Task-Änderung oder neues Feature), mit
   Rückverweis auf dieses Dokument und `RQ-SRC-01`.
2. Rollenmodell gemäß `OQ-4` entwerfen und in `AGENTS.md`, `SANDBOX.md`,
   `PRIVILEGED.md` sowie `docs/pipeline/` konsistent verankern.
3. Rollen-Briefings als eigene Artefakte unter
   `docs/pipeline/agent-instructions/` erstellen (`RQ-ROLE-03`).
4. Entscheidungsdatensatz-Format definieren (`RQ-DEC-*`) und an den bestehenden
   append-only-Konventionen aus `task-acceptance.md` ausrichten.
5. QA-Manager-Regelwerk festhalten (`SUP.1`-Unabhängigkeit, Eskalationsrecht).
6. Wirksamkeitsnachweis `RQ-EFF-01` als prüfbare Bedingung formulieren.

## 8. Rückverfolgbarkeit dieses Dokuments

| Richtung | Verweis |
|---|---|
| Anforderung → Quelle | `RQ-SRC-01` (Abschnitt 1, verbatim) |
| Anforderung → Auslöser | T1–T8 (Abschnitt 2), je mit Repo-Beleg |
| Anforderung → Norm | Abschnitt 5 |
| Anforderung → Bestand | Befund E (`0039-01`), Befund F (Reservierung) |
| Dokument → Koordination | `TODO-claude-re-intake-20260818T003223Z-845170c0e4da.md` |
| Dokument → Prozess | `RQ-DEC-01` … `RQ-DEC-05` sind in [`decision-record@v1`](../pipeline/decision-record.md) umgesetzt; TK-2 und die Rollentrennung verweisen darauf in [`process-roles.md`](../pipeline/process-roles.md). |

---

## Nachgetragene Waiver-Dauer zu `DEC-0040-001` (append-only)

`DEC-0040-001` und seine Legacy-Projektion `DEC-0040-001-LM001` bleiben unverändert;
`DEC-0040-001-LM001` weist `Waiver.Duration` weiterhin wahrheitsgemäß als fehlend aus.
Der folgende Record ergänzt die fehlende Angabe additiv durch die gewährende
Autorität. Er ersetzt und korrigiert den historischen Record nicht.

### `DEC-0040-008` — Endpunkt des begrenzten Autoritätsverzichts aus `DEC-0040-001`

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-20T08:02:27Z`
- **Deciding identity:** `authority:current-user:0040-closure-decisions:20260820T080227Z`
- **Role:** `Management`
- **Authority reference:** `docs/dossiers/0040-management-closure-provenance.md#dec-0040-008`
- **Subject:** Fehlende, nach `PRIVILEGED.md` und `decision-record@v1` zwingende Dauer des mit `DEC-0040-001` gewährten begrenzten Autoritätsverzichts
- **Decision:** Der mit `DEC-0040-001` gewährte begrenzte Autoritätsverzicht erhält als Endpunkt das stabile Ereignis `feature-closure:0040`. Er gilt damit vom ursprünglichen Gewährungszeitpunkt `2026-08-18T00:32:23Z` bis zum Abschluss von Feature `0040` und endet mit dessen Verschiebung nach `DONE.md` automatisch. Geltungsbereich und kompensierende Maßnahme aus `DEC-0040-001` bleiben unverändert; insbesondere erstreckt sich der Verzicht weiterhin nicht auf Feature `0039`. Eine Verlängerung über den Feature-Abschluss hinaus wird nicht erteilt; späterer Nacharbeitsbedarf erfordert eine neue Autoritätsentscheidung.
- **Technical justification:** `PRIVILEGED.md` und Abschnitt 4 von `decision-record@v1` verlangen eine unzweideutige Dauer; ein fehlendes Ende ist ausdrücklich ungültig, und nur die gewährende Autorität darf es nachtragen. Das Ereignis `feature-closure:0040` deckt exakt den Zweck ab, für den der Verzicht erteilt wurde, ist im Repository eindeutig beobachtbar und verhindert ein stilles Überlaufen auf andere Features. Ein rückwirkender Widerruf wurde erwogen und verworfen, weil er unter dem Verzicht erteilte Abnahmen angreifbar machen würde, ohne dass ein inhaltlicher Mangel belegt ist.
- **Triggers:**
  - `authority-tailoring-or-waiver`
- **Considered alternatives:**
  - **ALT-01:** Endpunkt `event:feature-closure:0040`
    - **Disposition:** `selected`
    - **Reason:** Deckt genau den Gewährungszweck ab, endet automatisch und beobachtbar und kann nicht auf andere Features überlaufen.
  - **ALT-02:** Festes ISO-Enddatum
    - **Disposition:** `rejected`
    - **Reason:** Ein kalendarisches Datum ist vom Arbeitsfortschritt entkoppelt und liefe entweder zu früh ab oder gewährte Autorität über den Zweck hinaus.
  - **ALT-03:** Rückwirkender Widerruf des Verzichts
    - **Disposition:** `rejected`
    - **Reason:** Würde die unter dem Verzicht erteilten Abnahmen ohne belegten inhaltlichen Mangel angreifbar machen und Nachprüfungen ohne Erkenntnisgewinn erzwingen.
- **Consequences:**
  - **CON-01:** `DEC-0040-001` ist ab diesem Record hinsichtlich `Waiver.Duration` vollständig; die zugehörige semantische Unvollständigkeit in `DEC-0040-001-LM001` ist damit durch eine Autoritätsentscheidung aufgelöst und nicht länger ein offener Managementpunkt.
  - **CON-02:** Mit dem `DONE.md`-Move von Feature `0040` erlischt die Abnahmebefugnis der benannten Eignersession automatisch; weitere Selbstabnahmen sind danach ohne neue Entscheidung unzulässig.
  - **CON-03:** Die kompensierende Maßnahme bleibt bestehen: Jede unter dem Verzicht erteilte Selbstabnahme muss `DEC-0040-001` als Autoritätsreferenz nennen und bleibt gezielt nachprüfbar.
  - **CON-04:** Der historische Record und seine Legacy-Projektion bleiben unverändert sichtbar; die Unvollständigkeit wird nicht aus der Historie entfernt, sondern additiv geschlossen.
- **Affected work units:**
  - `feature:0040`
  - `task:0040-09`
  - `repository:autodocs`
- **Affected gates:**
  - `integration:0040-09`
  - `feature-closure:0040`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:picard:0040-closure:20260820T080227Z`
    - **Role:** `Integrator`
    - **Participation:** `consulted`
    - **Position:** `supports`
    - **Note:** Legte die Formatanforderung aus `decision-record@v1` Abschnitt 4 und `PRIVILEGED.md` dar und stellte Ereignis-Endpunkt, festes Datum und rückwirkenden Widerruf als Optionen samt Folgen zur Wahl. Traf die Entscheidung nicht.
- **Waiver:** `bounded`
  - **Conflict:** Entwurf und Abnahme liegen innerhalb des Geltungsbereichs in derselben Session; das widerspricht der in `AGENTS.md` geforderten Unabhängigkeit und der SUP.1-Unabhängigkeit.
  - **Reason:** Ausdrückliche Managementauswahl der vollprivilegierten Option in Kenntnis des vom RE offengelegten Unabhängigkeitskonflikts.
  - **Scope:** Feature `0040` und die zu seiner Umsetzung nötigen Änderungen; ausdrücklich nicht Feature `0039` und nicht dessen Tasks.
  - **Duration:** `from 2026-08-18T00:32:23Z until event:feature-closure:0040`
  - **Compensating controls:**
    - **CTRL-01:** Jede Selbstabnahme im Geltungsbereich nennt `DEC-0040-001` als Autoritätsreferenz und bleibt damit gezielt unabhängig nachprüfbar.
    - **CTRL-02:** Mit `feature-closure:0040` erlischt der Verzicht automatisch; jede spätere Nacharbeit erfordert eine neue Autoritätsentscheidung.
