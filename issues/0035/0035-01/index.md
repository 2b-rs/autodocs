---
schema_version: "1.0"
id: "0035-01"
level: "task"
parent: "0035"
state: "open"
visibility: "internal"
prerequisites:
  - "0033-11"
  - "0033-13"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2563"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Verifizieren und schliessen, dass der `Submit`-Button im Bestaetigungsschritt des "Flag for review"-Dialogs fuer den tatsaechlich gewaehlten Transport funktioniert. PREREQ: 0035-01:0033-11, 0035-01:0033-13

## Scope

- **Befund (2026-08-15, Nutzer):** Im Schritt "Confirm request" loest `Submit` keine erkennbare Aktion aus.
  - **Root Cause (2026-08-15, verifiziert per Volldump von `review_request.js`, 236 Zeilen):** `[data-submit].onclick` ruft ausschliesslich `submitGithub(root, data)` auf (Zeilen 218-224), welches intern via `activeToken()` einen gespeicherten GitHub-Token voraussetzt. Ohne gueltigen Token bricht `submitGithub` fehlerfrei-leise ab bzw. wirft, ohne dass ein sichtbarer Fehlertext im `[data-errors]`-Feld erscheint, wenn kein Token vorhanden ist (im gezeigten Screenshot ist Identity `self_declared`, also kein Token gesetzt). Der Button ist also nicht generell tot, sondern **nur fuer self-declared/nicht-GitHub-authentifizierte Nutzer praktisch wirkungslos**, waehrend `Transport: json_export` im Bestaetigungstext bereits anzeigt, dass fuer diesen Fall der JSON-Pfad vorgesehen war. `[data-export].onclick` ruft separat `exportJson(root, data)` auf und funktioniert unabhaengig. Die beiden Buttons sind also nicht wie vom Transport-Feld suggeriert exklusiv, sondern immer beide sichtbar (Zeilen 204-205), unabhaengig vom tatsaechlich waehlbaren Pfad.
  - **Klarstellung:** Der urspruengliche Verdacht (Handler generell nicht verdrahtet) ist widerlegt — der Handler existiert und ist verdrahtet (Zeile 218), das eigentliche Problem ist ein UX-/Fehlerbehandlungsdefekt: Fuer self-declared Identitaet ist `Submit` faktisch nicht nutzbar, ohne dass dies vor dem Klick kommuniziert wird, und ein etwaiger Fehlschlag zeigt laut Code zwar `[data-errors]`, aber ggf. nicht fuer den Fall "kein Token vorhanden" mit einer fuer den Nutzer verstaendlichen Meldung.
  - **Akzeptanzkriterien:** Root Cause ist benannt und dokumentiert (nicht nur symptomatisch umgangen); `Submit` fuehrt den fuer den gewaehlten Transport definierten Pfad aus; jeder Fehlerfall (Transportfehler, Validierungsfehler, fehlende Berechtigung) erzeugt sichtbares, verstaendliches Nutzerfeedback statt eines stummen No-Op; ein automatisierter Browser-Test deckt Klick auf `Submit` inkl. Fehlerpfad ab und wuerde den jetzigen Zustand rot melden.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Fix und Regressionstest committed mit `REF`; die Zustandsunterscheidung `exported` / `submitted` / `ingested-queued` aus 0021-05 ist nachweislich nicht verletzt.
