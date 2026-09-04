---
schema_version: "1.0"
id: "0037-51"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "2026"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2206"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Prepare the governed removal of `sandboxed-grunt` and runner-only dependencies from the future Feature `0037` architecture. Claim: `TODO-jean-luc-0037-51-20260824T072000Z.md`; owner token `agent:jean-luc:0037-51:20260824T072000Z`. REF: `f3522aaaa80d851f3ba28744b08956a52eb63275`. **Acceptance: ✓** (2026-08-27, Integrator `paul`, unabhängig von Implementierer `jean-luc` und Architect `data`). Abgenommene Baseline `f3522aaaa80d851f3ba28744b08956a52eb63275`; Review-REF `b6d2bfdfe4850ad2cf7c1d898105088409e01378`; AWARD `1787865994204-934c578e`.

## Scope

- **Implementation completion (2026-08-24):** `DEC-0037-002` and the independent Architect review were integrated on `main` at `7a10f50d76e5620f3b7e3c796093c88037bb54bd`; the operative backlog rewire, Runner-role contract, checkpoint placement, supersessions, and cross-Feature release were committed at the REF above. William's `.02`/`.03` claims were additively released and their preserved tips recorded. `git diff --check` passed; the process-doc doctor remained `ok: true` with one unrelated pre-existing broken-link error, and the legacy doctor retained its pre-existing global findings.
  - **Management authority (2026-08-24, current user, direct Jean-Luc session):** “Die Sandboxed Grunts gibt es nicht mehr. Bzw. sind sie kein Bestandteil des zukünftigen Systems. Wir haben mittlerweile ein technologisches Niveau erreicht, auf dem wir alle unsere Agenten mit Shell- und git-Zugang ausstatten können. Sie können daher alle Tasks, die damit in Zusammenhang stehen, zurückstellen bzw. rausnehmen und damit auch alle Zwischenschritte eliminieren, die wir nur wegen der sandboxed grunts eingeführt hatten.” Follow-up: “ok, das klingt gut!”
  - **Scope:** Preparation only. A distinct Management-instantiated Architect inventories every affected `0037` and cross-Feature gate, allocates a conforming decision record, and produces a remove/defer/retain/rewrite plus dependency-rewiring matrix. Preserve useful issue-store, validation, migration, provenance, collision protection, governance write protection, review, recovery, and cutover mechanisms that do not intrinsically depend on sandboxed execution.
  - **Integration review:** not mandatory. This item only creates the pre-mutation decision and scope-review evidence; it does not implement or cross the affected gates.

## Acceptance criteria

- **AC-001** The decision candidate states the replacement capability model (all future agents have Shell and Git access), separates transport-specific runner mechanisms from still-required safety invariants, names every affected work unit and gate, dispositions already implemented runner artifacts without erasing history, and derives the smallest safe path from the current authority state to the revised Feature `0037` plan

## Definition of Done

A conforming decision-record candidate and independent Architect scope review are committed with exact baseline and affected-item matrix. No qualifying gate, `TODO.md` dependency, agent instruction, runner implementation, selector, or production path is changed by this preparation Task; operative mutation requires the reviewed decision to be integrated on `main` first.
