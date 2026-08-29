# Independent Architect supersession review — `0041-02` / corrected `DEC-0041-006`

**Consumer-finding verdict:** `supersedes`

**0041-02 start verdict:** `still-blocked` for operative authority-document mutation and for any reuse of `0041-02@8b1afb933f`; `may-start` only as bounded, non-activating re-derivation under `DEC-0041-006` CON-05/CON-06.

**Reviewer:** `agent:saru:0041-02-blackout-supersession:20260829T042200Z`, privileged Management-instantiated Architect, Team Discovery. Distinct from Enterprise Architect Data (`DEC-0041-006` PART-01). This is not Acceptance, checkpoint review, implementation, or integration.

**Award:** offer `1787976542681-96e09f9a` (notice `1787977283347-fdd2d098`); William `1787976302302-b258c4ef`. Mail is not additional authority.

**Claim-first REF:** `634791a0238cd36265ebd8faa65ae6901d3e6147`

No `DEC-` identifier is allocated or changed here. No option among `DEC-0041-006` alternatives is selected.

---

## 1. Pins and digests

| Input | Ref / digest |
| --- | --- |
| Award / this branch cut | `main@ef7aa528d154a9be8754ee6c6bef84f21056247b` |
| Observed later `main` at review start | `5b06f31d7f7fbc69649406518773c3b5a72b57c2` (`docs(0019-02)` only). **Not absorbed.** Pin is an ancestor. `TODO.md` Feature `0041` / `DEC-0041-006` bytes were not in that delta. |
| `DEC-0041-006` base (Jadzia target) | `059f7e326ad0a8447c9f54205841bf27d24dc786`; file SHA-256 `b6204148d3c53e9955ea0f46488e1e8fd8663856d8ec3c2e758ff238a7528e87` (matches Jadzia digest cite) |
| Additive correction | `4a11a0d284d1ce643c233bf9d208ca9cccf7322d` (`governance(0041): complete synchronous consumer scope`). Ancestor of the pin. |
| `docs/dossiers/dec-0041-006-atomic-implementation-checkin.md` on pin / `4a11a0d28` | SHA-256 `3bd3a24445219def41e867f2fddadc5698e64a54ee7ed5b0b97eda4747470e18` (identical) |
| Prior off-main Architect stop | `a94298f2cb8e2cbc271a3b0c7a764bd74787e5e1` — **not** an ancestor of the pin |
| `docs/dossiers/0041-06-scope-review-jadzia.md` at that stop | SHA-256 `2100dfa391ce04e2cc544bebd2275cc005b654824b496aa9421498ce27d30afd` (read via `git show`; path **absent** from this pin) |
| Historical candidate (do not merge) | `8b1afb933f0f9029d09c2fd3e9660aad3a8fa9a3` |
| Task `0041-02` on pin | `[ ]`, PREREQ `0041-01` (`[x]` `8aafc0cb4`). Hold text still names Architect stop `1bc504e4b` / `docs/dossiers/0041-02-gate-scope-review.md` and forbids merging `8b1afb933f`. |
| `0041-01` | `[x]` on pin. Implementation-start predecessor of `0041-02` is satisfied. |

---

## 2. Jadzia missing-consumer findings vs corrected record

Jadzia `scope-not-ready-for-mutation` named three omitted synchronous consumers of terminal implementation `REF`:

1. `_src/tools/legacy_task_editor.py`
2. `docs/pipeline/core-rules.md`
3. `_src/tools/check_integration_hygiene.py`

Independently remesured on the pin: `DEC-0041-006-C001` … `C005` (authored in `4a11a0d28`) add those three to Decision, Technical justification, Consequences CON-05/CON-08/CON-11–CON-13, Affected work units, and Affected gates (`validation:` for each plus `integration:repository-main`). Hygiene is an evidence/compatibility obligation, not an invented unconditional code change.

**Those three prior findings are resolved in the on-main corrected record.** Consumer-finding verdict: `supersedes`.

This does **not** rewrite Jadzia's report (it is not on this pin). It does not accept Data's participation as this review.

---

## 3. Does the correction completely close split-brain risk?

**For Jadzia's named set: yes.** **For 0041-02 DoD as written: no.**

`0041-02` Acceptance criteria / Definition of Done still require `AGENTS.md` ("Completing implementation work"), the `TODO.md` header, and `branch-workflow.md` to stop demanding a separate bookkeeping commit. Those paths are already in `DEC-0041-006` affected units. Executing that DoD **is** atomic-contract activation of governance prose.

On this pin those documents (and executable consumers) still encode the two-commit / implementation-`REF` contract, including:

- `TODO.md` header: `[x]` requires real substantive `REF`
- `docs/pipeline/core-rules.md` commit-hash `REF`
- `_src/tools/runner_transaction.py` / tests: two-commit REF closure
- `_src/tools/legacy_task_doctor.py` (tool listed; docs `docs/pipeline/legacy-task-doctor.md` still describe header `REF:`)
- `docs/pipeline/runner-transaction.md`, `docs/pipeline/agent-execution.md`, `docs/pipeline/issue-lifecycle.md`, `docs/pipeline/legacy-handoff-manifest.md` (`bookkeeping.two-commit-ref-closure@v1`)

CON-05 remains: the two-commit rule is operative until one reviewed cutover where **all named** consumers enforce or demonstrably accept one contract. `0041-06` is the runner/doctor alignment task and still `[ ]` with PREREQ `0041-02`.

Independent adjacent finding (not a new `DEC-*`): matching-guidance files `agent-execution.md`, `issue-lifecycle.md`, and `legacy-handoff-manifest.md` still teach two-commit and were not in Jadzia's three. They sit under CON-05 "matching guidance". They are **remaining activation conditions**, not a revival of the three omitted-consumer findings.

Prior Saru review `89e17a525` (cited in `DEC-0041-006`): activating repository-wide completion prose while runner/doctor still enforce two-commit is the split-brain. That mechanism is unchanged if `0041-02` is implemented to its current DoD before `0041-06` / editor / core-rules / hygiene evidence cut over together.

---

## 4. May bounded current-main re-derivation of `0041-02` start?

**Yes, only if it does not activate.** CON-06 already requires manual re-derivation on current main rather than cherry-pick/squash/rebase/reuse of stale lineages. CON-05 permits ordered non-operative preparation.

**Allowed now (non-activating):** new branch from current-main-at-assignment (remeasure; do not silently use this pin if `main` moved); claim-first; trailer-format/spec drafts that do **not** make `AGENTS.md` / `TODO.md` header / `core-rules.md` / editor / runner / doctor / hygiene operative-new; no merge of `8b1afb933f`; no `TODO.md` marker lift that pretends the hold is gone for full DoD.

**Still blocked:** implementing `0041-02` DoD (authority documents no longer demand two-commit bookkeeping); merging `8b1afb933f`; starting `0041-03` / `0041-06` (they PREREQ `0041-02` terminal); treating this review as Acceptance, Integrator landing, or activation.

`0041-04` also PREREQs `0041-02`; it stays implementation-blocked until `0041-02` is terminal under the hold rules. This review does not start it.

---

## 5. Exact affected gates / consumers (from corrected `DEC-0041-006` on pin)

**Work units:** `repository:autodocs`; `feature:0041`; `task:0041-02` … `0041-06`; `path:AGENTS.md`; `SANDBOX.md`; `PRIVILEGED.md`; `TODO.md`; `_src/tools/runner_transaction.py`; `legacy_task_doctor.py`; `legacy_task_editor.py`; `check_integration_hygiene.py`; `docs/pipeline/core-rules.md`; `branch-workflow.md`; `task-acceptance.md`; `runner-transaction.md`.

**Gates:** `validation:` runner_transaction, legacy_task_doctor, legacy_task_editor, check_integration_hygiene, core-rules, task-acceptance; `integration:repository-main`; `integration:0041-02` … `0041-06`; `feature-closure:0041`.

**Remaining activation-condition guidance (not in Jadzia's three, still two-commit on pin):** `docs/pipeline/agent-execution.md`; `docs/pipeline/issue-lifecycle.md`; `docs/pipeline/legacy-handoff-manifest.md`; `docs/pipeline/legacy-task-doctor.md`.

---

## 6. Remaining conditions (binding)

1. Do not merge `8b1afb933f`.
2. Do not change operative two-commit consumers in a `0041-02` candidate until the CON-05 cutover set (including editor, core-rules, hygiene evidence, runner, doctor, AGENTS/TODO header/branch-workflow) can agree in one reviewed activation.
3. `0041-03`/`0041-06` stay unstarted until `0041-02` is terminal without early activation.
4. This review is not a `TODO.md` hold-lift. A separately authorized bookkeeping change may cite this verdict for **bounded preparation** only.
5. Governance landing of this file requires a separate privileged Integrator. This mailbox does not advance `main`.

---

## 7. Verdict

- **`supersedes`** Jadzia `a94298f2c` `scope-not-ready-for-mutation` insofar as it concerned the three omitted consumers; those are on-main in `DEC-0041-006-C001`–`C005`.
- **`still-blocked`** for early activation: full `0041-02` authority-document DoD, historical candidate merge, and successor Tasks that consume a terminal `0041-02`.
- **`may-start`** bounded current-main re-derivation that keeps the two-commit contract operative.

No implementation. No Acceptance. No checkpoint. No Feature closure.
