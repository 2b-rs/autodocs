---
schema_version: "1.0"
id: "0044-14"
level: "task"
parent: "0044"
state: "closed"
visibility: "internal"
prerequisites:
  - "2026"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1236"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
---

## Goal

Anchor the shared-checkout rule and the pre-integration hygiene check. **Claim freigegeben (2026-08-22):** vormaliger Owner `Data-Miles-20260821T195500Z` ist beim Neustart von `Data` verlorengegangen. ACHTUNG, Kernliefergegenstand ist FERTIG: Branch `0044-14`, Tip `f3f59e01b` — `_src/tools/check_integration_hygiene.py` (194 Z.) plus `test_check_integration_hygiene.py` (96 Z.). Lesend gegen das Repository verifiziert (kathryn, 2026-08-22): fand fuenf echte Befunde (vier `FOREIGN_STAGED_TREE`, zwei `STALE_AFTER_REF_MOVE`), alle inzwischen bereinigt; Wiederholungslauf `ok: true`. Offen ist nur noch die Prosa-Verankerung in `AGENTS.md`/`branch-workflow.md` und die Registrierung in `docs/pipeline/tools.md`. Dort aufsetzen, NICHT neu beginnen. **Claim (2026-08-22):** `TODO-Kathryn-Chakotay-0044-14-20260822T114500Z.md` (owner_token: `agent:kathryn-chakotay-20260822t114500z:0044-14:20260822T114500Z`). **REF:** `649db737b` (Governance-Prosa, Branch `0044-14`), aufbauend auf `11d3498e8` (Werkzeug + Tests, Miles). Validierung: Fixture-Suite 3/3 gruen (pytest 9.1.1 / Python 3.14.7 und `unittest`); Live-Scan ueber 94 registrierte Worktrees `PASS`/EXIT=0; `process_doc_doctor` 30 Befunde auf Branch wie auf `main`-Baseline, keiner betrifft die geaenderten Dateien. **OFFEN, nicht Teil dieses `[x]`:** `AGENTS.md`, `docs/pipeline/branch-workflow.md`, `docs/pipeline/tools.md` sind Governance-Artefakte nach `DEC-0044-012` und muessen von der Projektleitung nach `main` gebracht werden (Verfahren `DEC-0044-015`); dieser unprivilegierte Implementierer hat keinen Ref bewegt und den Integrationsknoten nicht ueberschritten. **Werkzeuggrenzen, bewusst im Text benannt statt umschrieben:** die Pruefung vergleicht Index gegen `HEAD` und meldet einen Worktree mit sauberem Index, aber abweichenden Dateien nicht — der harte Root-Preflight aus `DEC-0044-015` bleibt deshalb zwingend zusaetzlich; `FOREIGN_STAGED_TREE` trifft auch regulaere laufende Arbeit und ist eine Ruhezustandsforderung, kein Vorwurf. **Acceptance: ✓** (2026-08-22, Integrationscheckpoint bestanden). Reviewer: privilegierte Integratorin `Kathryn-BEllana-20260822T120000Z`, unabhaengig von beiden Implementierern, gepinnt auf `f885ad281`. Verdikt `accepted`; **Checkpoint bestaetigt, nicht herabgestuft** — Begruendung im Bericht. Review-REF: `964e6caed`; Bericht: `docs/campaign-evidence/review-0044-14-20260822/review-0044-14-bellana.md`. Integration nach `main`: `7e12f877d` (nach `DEC-0044-015` aus dem Root, harter Preflight und Hygienepruefung `ok: true` vorab).

## Scope

- **Implements:** `DEC-0044-010`.
  - **Context:** The shared root checkout carried a staged tree from before Feature `0040`'s closure — 138 files, 28683 deletions — and its working tree matched that old state too (`DONE.md` on disk held zero mentions of `0040` against 88 in `HEAD`). An unrestricted `git commit -a` there would have silently reverted the closure. The damage sat in working-tree state, not in history, so no history-based control could ever have found it; it was found by manual inspection. Cleaned up 2026-08-21 under management authorization, with the prior state preserved in `preserved/root-worktree-20260821-kathryn`. **Suspected mechanism, to be confirmed by this Task:** moving `refs/heads/main` by `update-ref` while `main` is checked out in the root worktree leaves that worktree's index and files stale against the new `HEAD`, which presents as exactly this kind of divergence.
  - **Integration review: mandatory.** **Rationale (provisional — conservative default, not an architect decision):** the rule constrains where every agent may work. Weighing against a checkpoint: it adds an obligation rather than a capability, which elsewhere in this Feature carried a no-checkpoint justification. Set by Projektleiter Kathryn as the conservative default because only an architect may record that justification; to be confirmed or downgraded by the architect, at the latest at `0044-08`.
    - **Architect checkpoint decision (2026-08-24, Architect `seven`, Seven of Nine; recorded per `process-roles.md` §Architect and the `AGENTS.md` checkpoint contract):** **confirmed — mandatory; already exercised.** The rule constrains where every agent may work — a repository-wide behavioral contract, not a mere obligation. The checkpoint was crossed under review: privileged integrator `Kathryn-BEllana-20260822T120000Z`, verdict `accepted`, checkpoint confirmed at review (REF `964e6caed`). The architect ratifies that confirmation; no downgrade.

## Acceptance criteria

- **AC-001** `AGENTS.md` and `branch-workflow.md` state that agents mutate only in item-owned worktrees and that the root checkout is not written to
- **AC-002** the pre-integration hygiene check (index equals `HEAD`, no foreign staged trees, no stale worktree after a ref move) is specified as a step of the integration procedure and is machine-runnable
- **AC-003** the suspected mechanism above is confirmed or refuted with evidence, and if confirmed, the required refresh (or detaching the root checkout) is documented
- **AC-004** recovery from a preserved snapshot tag is documented

## Definition of Done

Committed; authority documents agree; the check is registered in `docs/pipeline/tools.md`; the existing `preserved/*` tags and their retention are documented so no one deletes evidence that is still the only copy of something.
