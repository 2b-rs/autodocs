---
schema_version: "1.0"
id: "0035-04"
level: "task"
parent: "0035"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2583"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Pruefen, ob Feature 0021 aufgrund der Befunde 0035-01 bis 0035-03 verfrueht nach `DONE.md` verschoben wurde, und das Ergebnis dokumentieren. REF: 0de4b846

## Scope

- **Begruendung:** Die Feature-0021-Definition-of-Done verlangt automatisierte Tests, die den Browser-Flow abdecken, sowie klares Nutzerfeedback in Fehlerfaellen. Ein wirkungsloser `Submit`-Button deutet auf eine Luecke in genau dieser Testabdeckung hin.
  - **Akzeptanzkriterien:** Es ist belegt, welcher Test den Submit-Pfad haette abdecken muessen und warum er den Defekt nicht gemeldet hat; das Ergebnis wird entweder als Testluecke behoben oder mit Begruendung als akzeptiert dokumentiert.
  - **Ergebnis (2026-08-15):** Feature `0021` wurde verfrueht als abgeschlossen behandelt. Der einzige Browser-Checker `_src/tools/check_review_request_ui.cjs` pruefte einen synthetischen mobilen WebKit-JSON-Exportpfad und las das eingebettete Server-Payload statt der tatsaechlich heruntergeladenen/gesendeten Request-Bytes; er pruefte weder den self-declared `Submit`-Fehlerpfad noch GitHub-Receipt, sichtbare Fehler, Retry, Cancel, No-JS, Desktop/weitere Engines oder Produktionsmetadaten. Zusaetzlich scheiterten unabhaengige Probes an strikter Schema-/Trust-Validierung, autoritativer Live-Zielauflösung, korrekter Queue-Kanonik/Origin, realen Produktionsmetadaten und authentifizierter Lifecycle-Autorisierung. Die damaligen `local-20260815-0021-06` bis `-08` sind keine Git-Objekte und erhalten ohne reproduzierbaren Snapshot keinen Evidenzkredit.
  - **Governance-Entscheidung (2026-08-15, Nutzerauftrag):** Feature `0021` bleibt in `DONE.md` ausschliesslich als deutlich gekennzeichnetes historisches, **nicht akzeptiertes** und durch `0033`/`0035` abgeloestes Implementierungsarchiv. Es ist keine Release-, Funktions- oder Akzeptanzfreigabe. Alle offenen technischen, UX-, Sicherheits-, Datenschutz-, Prozess- und Assurance-Punkte bleiben in `0033` bzw. `0035` offen.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Auditresultat, fehlende Testabdeckung, Nicht-Git-Referenzen und die Zuordnung jedes Befundclusters zu `0033`/`0035` sind in `TODO.md` und `DONE.md` konsistent dokumentiert; die beiden Dateien sind gemeinsam committed.
