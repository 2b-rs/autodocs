---
schema_version: "1.0"
id: "0039-03"
level: "task"
parent: "0039"
state: "open"
visibility: "internal"
prerequisites:
  - "0039-02"
labels:
  - "investigation-required"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1595"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0039-03:0039-02 Productize or explicitly reject the retained page-i18n completeness validator proposal from completed Feature `0036` as the first controlled tool-process pilot.

## Scope

- **Reservation gate:** The sole next action is a current-user decision naming an explicitly privileged owning session after `0039-02` is approved; historical prototype availability is not permission to execute or promote it.
  - **Marker `[u]` → `[d]` (2026-08-27, Projektleitung `kathryn`):** Die Management-Entscheidung des aktuellen Benutzers lautet `Productize.` und autorisiert ausdruecklich die Markerbewegung (agent-inbox `1787783780977-5d7dee6e`; parallele Zustellungen `1787783780813-a0322f10`, `1787783780893-e9407cf3`, `1787783781144-70a6516e`; Folgeantwort `1787788477209-e768ae5c`). Die Provenienz ist von `main` erreichbar: `docs/dossiers/0039-03-management-decision-provenance.md` in `main@4731a9996ce26b8a13307a1f05b62b86468fda74`. **Es ist damit keine Menschentscheidung mehr die naechste Handlung**; offen ist allein die **unerfuellte Vorbedingung `0039-02`** (auf `main` weiterhin `[ ]`). Der Reservierungsvorbehalt oben bleibt unveraendert gueltig: die Benennung einer explizit privilegierten Owning-Session wird **erst nach `0039-02`-Freigabe faellig** — sie ist nicht ueberfaellig, sondern noch nicht an der Reihe. Kein Eigentuemer zugewiesen, keine Implementierung begonnen, `0039-02` nicht veraendert.
  - **Marker `[d]` → `[~]` (2026-08-29, Projektleitung `jadzia`):** The decision `decision-1787975094535-77b8484c` resulted in option `opt-worf`. Assigning to `worf` and moving marker to `[~]`. `0039-02` is DONE. Claim: `TODO-worf-0039-03-20260829.md`.
  - **Waiver (2026-08-31, Projektleitung `jadzia`):** Management granted a bounded waiver (decision `decision-1788207042652-3fd4ab3f`, msg `1788212619308-84a0332e`, see `docs/dossiers/0039-03-waiver-decision.md`) for the implementer `obrien` to self-integrate `0039-03` due to no available independent Integrators. Marker returned to `[~]` for integration.

## Acceptance criteria

- **AC-001** Recover the retained `validate_process_i18n.py` prototype/evidence without treating ignored output as authoritative source
- **AC-002** assess overlap with current i18n and Feature `0038` validation tooling
- **AC-003** then either create a tested, cataloged `_src/tools/validate_page_i18n.py` with explicit opt-in page families, source-to-register and rendered-output coverage, fallback/leak, stable-anchor, ARIA, inline-SVG, bounded JSON, false-positive, and retirement semantics, or record an evidence-backed rejection/supersession. Any integration into `_src/validate.py` must be fail-closed, deterministic, and separately reviewed

## Definition of Done

The suggestion has exactly one authoritative disposition and owner; representative positive, missing-extraction, fallback/leak, protected-identifier, anchor, ARIA, inline-SVG, and stale-output fixtures pass or justify rejection; catalogs and historical suggestion references point to the disposition; and the `0039-02` pilot report measures whether the tool process improved reuse and assurance without duplicating an existing validator.
