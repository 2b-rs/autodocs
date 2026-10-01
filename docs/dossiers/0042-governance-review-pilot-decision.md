# Governance-Review-Pilot: Managemententscheidung und Vorab-Architekturreview

**Status:** Verbindliche Scope-Entscheidung für Feature `0042`. Dieser Datensatz
autorisiert die Vorbereitung des Piloten. Er ist weder Task-/Feature-Acceptance
noch Freigabe der späteren öffentlichen Veröffentlichung.

## Managemententscheidung

### `DEC-0042-001` — Erster veröffentlichter Governance-Review-Pilot

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-18T19:30:15Z`
- **Deciding identity:** `authority:current-user:0042-governance-review-pilot:20260818`
- **Role:** `Management`
- **Authority reference:** `docs/dossiers/0042-governance-review-pilot-decision.md#user-provenance`
- **Subject:** Das veröffentlichte Review–Curate–Feedback-Framework soll um einen Governance-Review-Piloten erweitert und für die fünf noch offenen Managemententscheidungen von Task `0040-09` verwendet werden.
- **Decision:** Ein separates Feature `0042` realisiert den Pilot in zwei Schritten. `0042-01` erstellt einen unveröffentlichten, nichtautoritativen Governance-Review-Adapter mit eigenem Schema, Allowlist-Projektion, Validator und Tests. `0042-02` ist der einzige Integrationsknoten; er prüft den Kandidaten vor dem ersten externen Effekt, veröffentlicht den an Commit `30176beae65014efcf661dcb157ad14321964799` gebundenen Fragensatz, verwendet ein GitHub Issue nur als Transport und Evidenz, validiert die Antwort und übergibt sie an den bestehenden privilegierten `0040`-Entscheidungs- und Acceptance-Pfad. Das Issue und der Browser dürfen keine Managementautorität oder Acceptance materialisieren.
- **Technical justification:** Der veröffentlichte Webauftritt ist der vom Kunden gewünschte normale Einstieg für Reviews und Entscheidungshistorie. Das vorhandene Framework liefert bereits Browserdarstellung und GitHub-Transport, sein heutiges Schema und `review_ingest.py` sind jedoch auf Spezifikations-Records ausgerichtet. Eine Erweiterung des bereits gepinnten `0040-09`-Arbeitsprodukts würde dessen Reviewbaseline verändern; eine Wiederverwendung des Requirements-Ingests könnte dagegen fachliche Records verändern und Identität fälschlich als Autorität behandeln. Ein getrenntes Pilot-Feature erhält die Baseline und erprobt nur Darstellung, öffentlichen Transport, Redaction und Rückführung, während der bestehende privilegierte Repository-Pfad alleinige Autorität bleibt.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
  - `irreversible-or-external-effect`
  - `security-or-credential-boundary`
  - `public-release`
  - `material-risk-decision`
- **Considered alternatives:**
  - **ALT-01:** Eigenes Feature `0042` mit unveröffentlichtem Adapter-Task und getrenntem Veröffentlichungs-/Pilot-Integrations-Task.
    - **Disposition:** `selected`
    - **Reason:** Hält die `0040-09`-Baseline unverändert, erlaubt ein Pre-Publication-Gate und trennt Transport/Evidenz von Autorität.
  - **ALT-02:** `0040-09` nach `[x]` wieder öffnen und Website, Schema, GitHub-Transport und Pilot in den bestehenden Integrations-Task aufnehmen.
    - **Disposition:** `rejected`
    - **Reason:** Würde die bereits gepinnte Reviewbaseline und den abgeschlossenen Implementierungsumfang nachträglich verändern und Infrastruktur mit der durch sie transportierten Entscheidung vermischen.
  - **ALT-03:** Das vorhandene `review-package@v1` und `_src/tools/review_ingest.py` unverändert für Governance-Entscheidungen verwenden.
    - **Disposition:** `rejected`
    - **Reason:** Der heutige Ingest schreibt Anforderungs-/Flag-Zustand und besitzt kein sicheres Modell für Managementautorität, Acceptance, Waiver oder Feature-Abschluss; seine Wiederverwendung wäre ein Autoritäts- und Datenintegritätsrisiko.
- **Consequences:**
  - **CON-01:** `0040-09` bleibt auf Commit `30176beae65014efcf661dcb157ad14321964799` gepinnt und erhält noch keine `Acceptance: ✓`.
  - **CON-02:** GitHub-Login und Issue belegen nur Transportidentität und Zeitpunkt; verifizierte Entscheidungsautorität entsteht ausschließlich im bestehenden privilegierten Repository-Pfad.
  - **CON-03:** `0042-01` darf weder veröffentlichen noch `TODO.md`, Acceptance, Entscheidungsdatensätze, Spec-Records, Review-Queues oder Curation-Queues schreiben.
  - **CON-04:** `0042-02` benötigt vor Website-Publikation oder Issue-Erzeugung ein explizit zugewiesenes privilegiertes Pre-Publication-Review der exakten Baseline, Fragen, Public-Allowlist, Privacy-/Injection-Negativtests, Ziel-Repository- und Credential-Grenze.
  - **CON-05:** Öffentliche Daten werden ausschließlich per Allowlist projiziert. Claim-/Session-/Runner-Tokens, Credential-/Signerinformationen, private Autoritätsdaten, private Evidenzpfade, nicht freigegebene Findings und private Begründungen bleiben ausgeschlossen.
  - **CON-06:** Das Pilotformat unterscheidet `review_baseline_commit`, `task_substantive_ref`, `question_set_digest`, `public_projection_digest` und `response_digest`; Commit `201017db524a1740919d02bbfcde217d46ee589c` darf nicht anstelle der Reviewbaseline verwendet werden.
  - **CON-07:** Die zukünftige Schreibautorität bleibt bei `0037-10.03` für signierte Entscheidungen und `0039-05` für Acceptance/Invalidation/Closure; `0037-10.04` bleibt read-only. Feature `0042` führt keinen konkurrierenden Authority Writer ein und startet oder entsperrt diese Tasks nicht.
  - **CON-08:** Die späteren Cross-Feature-Bezüge auf `0040-05` und `0040-09` sind exakte Contract-/Baseline-Gates, keine impliziten seitlichen Branch-Merges.
- **Affected work units:**
  - `feature:0042`
  - `task:0042-01`
  - `task:0042-02`
  - `task:0040-05`
  - `task:0040-09`
  - `task:0033-01`
  - `task:0037-10.03`
  - `task:0037-10.04`
  - `task:0039-05`
- **Affected gates:**
  - `task-start:0042-01`
  - `task-start:0042-02`
  - `integration:0042-02`
  - `release:0042-governance-review-pilot`
  - `external:github-issue-transport`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:zed-architect:0042-scope-review:20260818-a9f4c7d2`
    - **Role:** `Architekt`
    - **Participation:** `reviewed`
    - **Position:** `supports`
    - **Note:** Der getrennte nichtprivilegierte Architekt unterstützt den zweistufigen, writer-freien Zuschnitt unter den verbindlichen Grenzen in Abschnitt „Architekturauflagen“, insbesondere exact-digest Contract-/Baseline-Gates statt Cross-Feature-Branch-Merges und ein Pre-Publication-Gate vor jedem externen Effekt.
- **Waiver:** `none`

## Architekturauflagen

Das Vorabreview durch
`agent:zed-architect:0042-scope-review:20260818-a9f4c7d2` ist eine
Scope-/Architekturprüfung, keine Implementierungsabnahme. Seine verbindlichen
Auflagen sind:

1. `0040-05` wird für `0042-01` als aktueller, nicht invalidierter
   Acceptance-/Contract-Digest geprüft; sein Branch wird nicht seitlich gemergt.
2. `0040-09` wird für `0042-02` als erreichbarer `[x]`-Reviewbaseline-Commit
   `30176beae65014efcf661dcb157ad14321964799` geprüft; sein Branch wird nicht
   zur Erzeugung des Reviewpakets gemergt.
3. Vor Website-Publikation oder GitHub-Issue-Erzeugung prüft ein ausdrücklich
   zugewiesener privilegierter Integrator den unveröffentlichten Kandidaten.
4. Das Governance-Schema trennt mindestens Transport-Akteur, Transport-
   Identitätsmodus, behauptete Autoritätsreferenz, Autoritätsprüfstatus und
   verifizierte entscheidende Autorität. Client und Issue können die letzten
   beiden Felder nicht autoritativ setzen.
5. Die öffentliche Projektion ist allowlist-basiert; Freitext ist optional,
   größenbegrenzt, gegen Ausgabe-Injection geschützt und ausdrücklich als
   öffentlich gekennzeichnet. Private Begründungen nutzen einen getrennten Kanal.
6. Der Pilot erbt keinen Browser-PAT stillschweigend. Zulässig ist ein
   credential-freier GitHub-New-Issue-Pfad oder ein separat genehmigter,
   qualifizierter Credential-Handle.
7. `_src/tools/review_ingest.py` und der Requirement-/Curation-Schreibpfad
   bleiben ausgeschlossen. Negativtests beweisen die beidseitige Schema-
   Verwechslungssperre und die Unverändertheit der produktiven Stores.
8. Browser-/Issue-Transportzustände wie `draft`, `submitted`,
   `issue-received`, `response-validated` oder `stale` sind keine
   Autoritätszustände. `accepted`, `Acceptance: ✓`, `management-approved` und
   `feature-closed` dürfen dort nicht entstehen.
9. `0042-02` ist der einzige Integrationsknoten. Der externe Effekt liegt
   zwischen einem Pre-Publication-Review und einer Post-Publication-
   Evidenzprüfung; die endgültige Acceptance bleibt prerequisite-closed.
10. Die Reviewer-Identität dieses Vorabreviews darf für denselben Gegenstand
    nicht Implementierer, Publisher, Integrator oder Acceptance Reviewer sein.

## Gepinnter Pilotgegenstand

- **Task:** `0040-09`
- **Reviewbaseline:** `30176beae65014efcf661dcb157ad14321964799`
- **Substantive REF:** `201017db524a1740919d02bbfcde217d46ee589c`
- **Quelle der Fragen:** `docs/dossiers/0040-09-integration-package.md`, Abschnitt
  „Management review questions“, an der gepinnten Reviewbaseline
- **Fragen:**
  1. Ende, Widerruf oder Ersatz des Waivers `DEC-0040-001`;
  2. Management-Ratifizierung oder Zurückweisung des Sachinhalts von
     `DEC-0040-005` unter Erhalt des historischen Falscheintrags;
  3. Annahme oder Zurückweisung der nichtmateriellen Driftanalyse und der
     offengelegten Restpunkte;
  4. Aggregate-Verdikt `accepted`, `rejected` oder `inconclusive` für die
     gepinnte Baseline;
  5. Beibehaltung von `0040:0039-01` oder Ersatz durch eine explizite
     Downstream-Beziehung.

## User provenance

Die folgenden Benutzerprompts haben diese Entscheidung materiell ausgelöst und
werden unverändert wiedergegeben:

> bevor ich das mache, eine Frage: Gibt es die Möglichkeit diese und ähnliche Entscheidungen online zu stellen, so dass ich sie im Rahmen des review-curate-feedback-Frameworks mit einem github issue beantworten kann?

> Ich meinte das Review-Curate-Feedback Framework von https://2b-rs.github.io/autodocs/index.html. Dort sollten, bei vollständig etabliertem Prozess, ja auch die Reviews, Vorlagen und vergangene Entscheidungen irgendwann einsehbar sein.

Nach der Erklärung des Zielbilds und des vorgeschlagenen ersten Piloten:

> machen wir genau so

## Geltungsgrenze

Dieser Datensatz erlaubt die kontrollierte Vorbereitung von Feature `0042`.
Die öffentliche Veröffentlichung, das Erzeugen eines GitHub Issues, die
Materialisierung der Managementantwort, `Acceptance: ✓` und Feature-Abschluss
bleiben jeweils ihren eigenen, im Backlog festzulegenden Toren vorbehalten.
