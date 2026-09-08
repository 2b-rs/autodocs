---
schema_version: "1.0"
id: "0038-05.01"
level: "subtask"
parent: "0038-05"
state: "open"
visibility: "internal"
prerequisites:
  - "0038-04"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1673"
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
  - id: "AC-005"
    status: "active"
---

## Goal

PREREQ: 0038-05.01:0038-04 Implement the digest-bound structural parser, pure renderer, candidate/diff producer, and complete promotion-preflight verifier for the legacy backlog/claim editor. REF: ffaf3934796023872eb4a58134865c3daf6f5079

## Scope

- **Closed (2026-08-17):** Committed the strict structural parser, nine closed typed operation plans, exact actor/claim/read-set preimages, content-addressed candidate/diff contract, and mutation-free promotion preflight; every authoritative promotion fails closed with verified coordinator handoff evidence for `.02`. The direct-write closure helper is retired and only its two remediated policy dispositions were removed. Validation passed 39 focused editor tests, 121 automation-safety tests, JSON checks, and an explicit two-file scan with zero findings/policy errors; independent review `6ac11e2c-a69a-4a56-9761-79c48037a577` returned `ACCEPT`. Isolated full validation reproduced the unrelated 12-link/six-file baseline and passed after candidate-only empty shims. Provenance receipt SHA-256 `19f813918b12bf381add0168ebe21122f499da676e4959dfcbade2d4ed84ec20`.
  - **Correction (2026-08-25, `agent:tom-saru:0038-05.01:correction-20260825T141800Z`):** `_open_dir_nofollow()` opened every path component with `O_NOFOLLOW` unconditionally, so any path below the macOS `/var` symlink — including every `tempfile.mkdtemp()` result — failed with `NotADirectoryError: [Errno 20] Not a directory: 'var'`; measured `11 failed, 41 passed` on `main`@`28d7a0091`. The "39/39" recorded above and at `0038-05` was obtained with `TMPDIR` relocated outside the alias, i.e. a documented workaround rather than a fix. Ported the pattern `runner_transaction.py` already carried from Task `0038-10`: track the physical (`realpath`) prefix while descending and follow a symlinked component only when its resolved target stays under that prefix, re-raising otherwise. `O_NOFOLLOW` is retained on every component. Suite now `54 passed` (52 pre-existing + a `/var` regression test and an adversarial symlink-escape test); the escape test is fault-injection-proven to fail when the guard is removed. `runner_transaction.py` unchanged. Branch `0038-05.01-correction`; see `TODO-Tom-Saru-0038-05.01-correction-20260825T141800Z.md`. Integration checkpoint not crossed; no acceptance state touched.
  - **Acceptance:** ✓ (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `ffaf3934796023872eb4a58134865c3daf6f5079`-Autor und von Korrektur-Implementierer `agent:tom-saru:0038-05.01:correction-20260825T141800Z`). Abgenommene Baseline nach Korrektur `8ddc0fffa0823e9d598f122779c59b8a870584e1` (Fix `2539db6bf`, Tests `8950d32cc`, Buchung `8ddc0fffa`); Teil der durch Checkpoint `0038-30` induzierten prerequisite-closed Batch. Review-REF `a995f9047`. **Echter Befund während dieser Prüfung selbst gefunden** (nicht übernommen): 11/39 Fehlschläge am ursprünglichen REF, reproduzierbarer macOS-`/var`-Symlink-Bug in `_open_dir_nofollow()`, live auf main bestätigt vor der Korrektur. Nicht selbst repariert (Produktautorschaft an geprüftem Code); Implementierer angefordert, Korrektur unabhängig verifiziert: 54/54 mit echtem TMPDIR, eigene Fault-Injection (Guard entfernt → `AssertionError: OSError not raised`, wiederhergestellt → 54/54), automation_safety 7 Funde alle bestätigt vorbestehend/main-identisch, Diff-Scope exakt wie gemeldet. Korrektur nach main integriert (`--ff-only`, Hygiene+Preflight PASS vor/nach).

## Acceptance criteria

- **AC-001** Parse exact Feature/Task boundaries and normative sections
- **AC-002** use expected full-document/Feature/Task/claim/read-set digests
- **AC-003** support pickup, progress, closure, wontfix, parent aggregation, REF injection, claim handoff/finalization, and append-only correction as closed typed plans without heredocs, shell strings, globs, or broad regex replacement. Always generate a content-addressed candidate and bounded diff
- **AC-004** validate every planning preimage, absent path, candidate member, and postcondition in promotion preflight
- **AC-005** perform no authoritative write because portable pathname replacement cannot provide repository-authority CAS or race-safe rollback without the durable coordinator. Every promotion request returns `LTE-PROMOTE-COORDINATOR-REQUIRED` with verified candidate evidence consumed by `.02`. Retire `task_bookkeeping_closure.py` and remove only its remediated policy dispositions

## Definition of Done

Fixtures reproduce/reject the `9e033f32`→`9c4795bb`→`cd6d8db1` corruption chain, stale amend REFs, structural/decoy duplicate Task text, neighboring-header/section capture, current claim variants, concurrent TODO/claim/read-set edits, candidate/path tampering, and wrong-claim deletion; all operation plans preserve unrelated bytes, promotion preflight is mutation-free and complete, and focused/safety/independent review passes.
