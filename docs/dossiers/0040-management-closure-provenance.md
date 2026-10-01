# Feature 0040 — Management closure decisions, verbatim provenance

This document retains the user-authored authority for the two Management
decisions that resolve the open blockers of the `0040-09` integration checkpoint.
It contains no decision of its own; the records themselves live next to the
defects they close:

- `DEC-0040-007` — [`0040-05-cross-item-scope-review.md`](0040-05-cross-item-scope-review.md)
- `DEC-0040-008` — [`re-intake-evidence-traceability-and-roles.md`](re-intake-evidence-traceability-and-roles.md)

**Deciding identity:** `authority:current-user:0040-closure-decisions:20260820T080227Z`
**Recorded at:** `2026-08-20T08:02:27Z`
**Transcribing session:** `agent:picard:0040-closure:20260820T080227Z` (Integrator; transcribed the decisions, did not make them)

## Triggering user instruction (verbatim)

> Prüfe, welche Features reif für eine Integration auf main sind und lass uns die ggfs. dafür nötigen Reviews in Angriff nehmen.

Preceding session context, in order, establishing this session's privileged
designation and its review assignment (verbatim, user-authored only):

> Du bist Picard, ein privilegierter Agent und die höchste Entscheidungsinstanz in diesem Projekt. Schau dich kurz um, ich komme gleich um mit dir etwas zu besprechen.

> ich kann die Reviews, die du nicht selbst machen darfst, für dich übernehmen. Um die Integration von 0039-03 kümmert sich denke ich schon einer deiner Offiziere.

## DEC-0040-007

Decision taken by the current user through a structured choice. Question text as
presented, verbatim:

> DEC-0040-005: Ein Agent hat sich selbst die Rolle `Management` gegeben und damit eine repo-weite Scope-Review-Regel gesetzt. Der Inhalt ist geprüft und solide; Task 0040-05, der ihn umsetzt, ist bereits akzeptiert. Wie disponierst du?

Options presented, verbatim:

1. `Als eigene Management-Entscheidung ratifizieren (Empfohlen)` — Du übernimmst den Inhalt append-only als deine Entscheidung; der ursprüngliche falsche Agent-als-Management-Eintrag bleibt als Historie sichtbar. Begründung: Der Inhalt wurde unabhängig geprüft, und eine Ablehnung würde bereits akzeptierte Arbeit (0040-05) aufrollen.
2. `Ablehnen und Regel zurückziehen` — Die Regel verliert ihre Autorität. Folge: 0040-05 ist umgesetzt und akzeptiert, seine Grundlage entfällt — es braucht dann eine Nachfolge-Task, die die Umsetzung zurückbaut oder neu begründet.
3. `Inhaltlich ändern, dann ratifizieren` — Du ratifizierst mit Änderungen am Predicate oder Review-Umfang. Ich lege dir dafür den exakten Regeltext vor, bevor etwas geschrieben wird.

**User selection, verbatim:** `Als eigene Management-Entscheidung ratifizieren (Empfohlen)`

## DEC-0040-008

Decision taken by the current user through a structured choice. Question text as
presented, verbatim:

> DEC-0040-001 (Authority-Waiver, unter dem der Requirements-Autor als privilegierter Eigner von Feature 0040 handeln durfte) nennt keine Dauer. PRIVILEGED.md verlangt eine. Welche Dauer trägst du nach?

Options presented, verbatim:

1. `Bis Closure von Feature 0040 (Empfohlen)` — Der Waiver endet automatisch mit dem DONE.md-Move. Deckt genau den Zweck ab, für den er erteilt wurde, und kann nicht auf andere Features überlaufen.
2. `Festes Enddatum` — Du nennst ein konkretes ISO-Datum. Sinnvoll, wenn der Waiver auch nach Closure noch für Nacharbeiten gelten soll.
3. `Rückwirkend widerrufen` — Der Waiver gilt als beendet. Achtung: Damit werden unter ihm erteilte Acceptance-Records angreifbar und müssten einzeln nachgeprüft werden.

**User selection, verbatim:** `Bis Closure von Feature 0040 (Empfohlen)`

## Scope boundary

These two decisions supply missing Management authority only. They are not Task
acceptance, not the `0040-09` aggregate integration verdict, and not Feature
closure. The aggregate verdict remains the separate, independent decision of the
assigned privileged integrator and is recorded in its own review evidence.

A third decision taken in the same interaction — a general waiver of the
mandatory integrating-task review floor for Features created before that rule
existed — concerns Feature `0034` and other legacy Features. It is recorded
separately with its own scope and is deliberately not part of Feature `0040`.
