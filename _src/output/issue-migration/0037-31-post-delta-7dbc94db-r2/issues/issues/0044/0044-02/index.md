---
schema_version: "1.0"
id: "0044-02"
level: "task"
parent: "0044"
state: "closed"
visibility: "internal"
prerequisites:
  - "0044-01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1091"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0044-02:0044-01 Define the risk-integration procedure (three-role review, unanimity, temporary policy suspension, escalation). **MANAGEMENTENTSCHEIDUNG (2026-08-22, aktueller User, aufgezeichnet von Projektleiter `kathryn`):** Die Befugnis **soll es geben**. Im Wortlaut: „Ja, es soll diese Befugnis geben, ja. Wenn drei privilegierte Agenten einstimmig entscheiden, dann darf eine Regel ausser Kraft gesetzt werden, wobei QA-Manager und Security-Manager jeweils ein Veto-Recht besitzen." Damit ist der Entwurf von `Data-Nora` in **zwei** Punkten geaendert: die entscheidende Instanz sind **drei privilegierte Agenten** (nicht die urspruenglich vorgeschlagene feste Besetzung Integrator/QA/Architekt), und es gibt ein **eigenes Veto-Recht fuer QA-Manager und Security-Manager**. Der **Security-Manager** kam im Entwurf ueberhaupt nicht vor. **Offener Punkt, der vor dem Datensatz zu klaeren ist:** ob QA-Manager und Security-Manager zu den drei Entscheidenden zaehlen (dann waere das Veto in der Einstimmigkeit bereits enthalten und bezoege sich vermutlich auf ein **nachtraegliches** Veto) oder ob sie ausserhalb des Dreiergremiums ein unabhaengiges Veto halten. Das ist keine Formulierungsfrage — es bestimmt, wer ueberhaupt gefragt werden muss. Kein Agent entscheidet das durch Auslegung. **ZUSAMMENSETZUNG RATIFIZIERT (2026-08-22, Management):** Im Wortlaut: „koennen im Gremium sitzen, vetorecht gilt aber auch von aussen." Damit ist der harte Halt aus `DEC-0044-018` aufgehoben. QA-Manager und Security-Manager **duerfen** Mitglied des einstimmigen Dreiergremiums sein, muessen es aber nicht; **ihr Veto besteht unabhaengig davon und gilt auch von aussen**. Folge: beide sind **immer zu befassen** — eine Aussetzung, die an einem von beiden vorbeigeht, ist ungueltig. Sitzt keiner im Gremium, ist die Einstimmigkeit **notwendig, aber nicht hinreichend**; Schweigen ist keine Zustimmung, die Befassung ist nachzuweisen. Ein Veto ist fuer den jeweiligen Antrag **endgueltig** und wird auch durch Einstimmigkeit nicht ueberstimmt. Vollstaendig in `docs/dossiers/dec-branching-merging-strategie.md`. Die Auflagen aus dem Scope-Review `Data-Lore-20260822T210200Z` bleiben unberuehrt. **Claim:** `TODO-william-ezra-20260823T192000Z-0044-02-20260823T192000Z.md`.

## Scope

- **Requirements covered:** `RQ-IP-06`; implements `DEC-0044-003`.
  - **Implementation REF:** `c9f0968e9765fa2eab765d85dab6c376cf314a99` (reconciled procedure, evidence, and references on baseline `86783cbaa`).
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** the Task documents a procedure that itself requires three-party unanimity or user decision at use time; misuse is caught at that gate. Re-examined at `0044-08`.

## Acceptance criteria

- **AC-001** A documented procedure defines when an integration is a risk integration (case A4), the three-role review (Integrator, QA, Architect — distinct sessions, `TK-1` independence applies), the unanimity requirement, what a temporary policy suspension may and may not cover, its mandatory record (participants, scope, duration, restoration), and the escalation path to the user on non-unanimity, connected to the existing `[u]` integration verdict rather than replacing it

## Definition of Done

Committed in `docs/pipeline/`; the record format is specified; `branch-workflow.md` and `task-acceptance.md` reference it; a worked example exists.
