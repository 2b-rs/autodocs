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
| Dokument → Prozess | offen bis `OQ-2` geklärt ist |
