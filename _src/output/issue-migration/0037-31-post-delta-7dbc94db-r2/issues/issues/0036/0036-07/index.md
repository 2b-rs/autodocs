---
schema_version: "1.0"
id: "0036-07"
level: "task"
parent: "0036"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:414"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Governance-Check: Sicherstellen, dass weder Prozessdoku noch Seitenerzeugungsprozess die Sicherheits-/Lifecycle-Grenze aus Feature 0021 (kein direktes Mutieren von Records durch Website/KI/Browser) relativieren oder missverstaendlich darstellen. <!-- REF: e9125e942a6067ab972271eacaed45a0cd367818 -->

## Scope

- **Akzeptanzkriterien:** Textliche und diagrammatische Darstellung beider Prozesse macht fuer Laien unmissverstaendlich klar, dass ein Review-Paket (Entscheidung) und ein Flag-for-review-Request (Antrag) unterschiedliche Wirkung auf den Record haben; kein Diagramm suggeriert eine sofortige Record-Aenderung durch einen der beiden Wege; die Dokumentation des KI-Agenten-/Seitenerzeugungsprozesses behauptet nirgends, dass KI direkt normative Prozessdoku oder Website-HTML ausserhalb des regulierten Pipeline-/Review-Pfads selbst autorisieren duerfe.

**Retained collaboration/tooling suggestion (pending reconciliation into the append-only `AGENTS.md` suggestion log):**

- 2026-08-16 — proposer: `agent:zed:0036-06:20260816-9c4e7b2a`; scope: `Feature 0036 / Task 0036-06`
  - **Observation:** Global `i18n_translate.py status` can report complete when a page was never fully extracted; generic German-leak checks also missed mixed compound headings, ARIA text, and inline-SVG labels.
  - **Suggestion:** Productize the task prototype as a tested `_src/tools/validate_page_i18n.py` with explicit page-model completeness opt-in, source-to-register coverage, rendered fallback/leak checks, stable-anchor comparison, ARIA/inline-SVG verification, and bounded JSON evidence; integrate it into `_src/validate.py` for every opted-in localized page family.
  - **Expected benefit:** Prevents false-green translation status and gives later process/issue pages one reusable completeness gate instead of task-specific ad hoc scripts.
  - **Risk/tradeoff:** Exact leak matching must distinguish protected identifiers and intentionally untranslated terms; keep allowlists page-local and fail closed on unknown authored text.
  - **Evidence:** `output/logs/0036-06/20260816-9c4e7b2a/validate_process_i18n.py` and `logs/i18n-process-0036-06/20260816-9c4e7b2a/completeness.json`.
  - **Disposition:** pending; retained here because `AGENTS.md` had foreign concurrent edits at Feature closure.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Review-Notiz mit Fundstellen-Check committed mit `REF`.
