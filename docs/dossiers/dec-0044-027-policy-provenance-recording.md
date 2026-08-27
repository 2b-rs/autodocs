# `DEC-0044-027` — Conforming reach, activation, and trailer boundary for recorded policy provenance

This is an append-only follow-on to Management decision `DEC-0044-008`. It does
**not** rewrite, delete, or silently replace
`docs/dossiers/dec-branching-merging-strategie.md` §`DEC-0044-008`. The
substance already authorized on 2026-08-21 (policy origin is **recorded**, not
reconstructed; absorption outside an item's own predecessor/successor chain
uses a real `--no-ff` merge commit; `_src/tools/check_policy_provenance.py`
is the mechanical check) remains in force. This record supplies the
`decision-record@v1` fields that `DEC-0044-008` does not carry, so Task
`0044-12` can mutate the named surface.

**Authority for the substance:** Management, 2026-08-21, recorded by
`agent:kathryn:projektleiter:branching-strategie:20260821T090000Z` under
`DEC-0044-008` / `DEC-0044-011` (legacy narrative form). Mailbox is not that
authority.

**Authority for this reach/activation/convergence record:** Project Lead
`jean-luc` assigned Architect recording (agent-inbox `1787751762460-6a7ad4b6`
and `1787751849693-634e6d1e`, thread `0044-12`) after independent Architect
`seven` review `5ff5aae54436707126d168507ee2f7c6ef347da0` returned
`scope-not-ready-for-mutation`. This Architect records; does not implement;
does not accept; does not integrate.

**Identifier allocation:** `DEC-0044-027`, checked against `main`
`059f7e326ad0a8447c9f54205841bf27d24dc786` (`DEC-0044-001` … `DEC-0044-026`
present; `DEC-0044-027` absent).

---

### `DEC-0044-027` — Recorded policy provenance: v1 reach, non-retroactivity, atomic activation, trailer composition

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-26T15:50:00+02:00`
- **Deciding identity:** `agent:saru:0044-12:gov-0044-12-decision-record:20260826T154400Z`
- **Role:** `Architekt`
- **Authority reference:** `docs/dossiers/dec-branching-merging-strategie.md#dec-0044-008--herkunft-wird-aufgezeichnet-nicht-rekonstruiert`; independent review `5ff5aae54436707126d168507ee2f7c6ef347da0:docs/dossiers/0044-12-gate-scope-review.md`; Project Lead assignment `agent-inbox:1787751762460-6a7ad4b6`; binding branch instruction `agent-inbox:1787751849693-634e6d1e`; `docs/dossiers/dec-0041-006-atomic-implementation-checkin.md` on `main` `059f7e326ad0a8447c9f54205841bf27d24dc786`
- **Subject:** Exact mutation reach, non-retroactivity, atomic activation and fail-closed rollback, and trailer-key composition for Task `0044-12` implementing already-authorized `DEC-0044-008` / `DEC-0044-011`, including the boundary with `DEC-0041-006` / Task `0041-02`.
- **Decision:** Preserve `DEC-0044-008` append-only. Task `0044-12` may mutate **only** the enumerated paths below, in one atomic activation commit, to (a) specify commit-trailer `Policy-Origin-Branch:` (name, value, when required) in `docs/pipeline/branch-workflow.md` consistently with `AGENTS.md`; (b) state the `--no-ff` absorption rule as binding, consistent with `DEC-0044-007` as the narrower case; (c) extend `_src/tools/check_policy_provenance.py` so a missing required trailer is a finding, with tests in `_src/tools/test_check_policy_provenance.py`; (d) register that behavior in `docs/pipeline/tools.md`; (e) if the intake dossier is touched, record `DEC-0044-011`'s extension of `DEC-0044-002` additively without deleting the original `DEC-0044-002` text. Git commit trailers are the single recorded-provenance medium. Two named key families exist and must not be collapsed into a third key: **Family A** `Policy-Origin-Branch:` on policy-touching commits (this record / `DEC-0044-008`); **Family B** `Task-ID:` and `Base-Ref:` on post-cutover implementation or disposition carrying commits (`DEC-0041-006` as integrated on `main` `059f7e326ad0a8447c9f54205841bf27d24dc786`). A commit that matches both predicates carries both families. Topology reconstruction of origin remains forbidden. The mechanical provenance gate is non-operative until that atomic activation commit; rollback before activation abandons the candidate without changing current tool behavior; rollback after activation reverts the enumerated paths together to one previously coherent contract and remains fail-closed. No retroactive finding is asserted against commits authored before the Management decision date 2026-08-21. The implementer of the mutation is distinct from Architect `seven` and from this recording identity. This record does not start `0044-13`, does not grant `Acceptance: ✓`, and does not advance `refs/heads/main`.
- **Technical justification:** `DEC-0044-008` authorizes recorded origin because Git stores no authoring branch and fast-forward absorption is topologically identical to native authorship (three `0044-01` review rounds). It is not a `decision-record@v1` and names neither affected units/gates, activation instant, nor the `0041-02` trailer constraint that post-dates the stale `0044-12` product tip `47331dca2`. `DEC-0044-011` extends the origin prohibition and states non-retroactivity but does not name the trailer, `--no-ff`, or the tool. `docs/dossiers/0044-04-gate-scope-review.md` records no mandatory affectedness of `0044-12`/`0044-13` and warns against a third mechanism. `DEC-0041-006` on current `main` already requires `Task-ID` and ancestor `Base-Ref` on atomic implementation check-ins and fail-closed trailer validation; composing those keys with `Policy-Origin-Branch:` on overlapping commits matches the trailer medium already used on this `main` for governance (`Policy-Origin-Branch: main` in `docs/pipeline/branch-workflow.md`) without creating a second closure procedure. Candidate `4a11a0d284d1ce643c233bf9d208ca9cccf7322d` expands `DEC-0041-006` consumer scope (editor, core-rules, hygiene); it is not on `main` and does not change Family A or the composition rule, so it is an exact open `0041` dependency rather than silent `0044-12` authority. Atomic activation follows the same split-brain lesson `DEC-0041-006` recorded: prose, tool, tests, and registration must agree in one commit.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
- **Considered alternatives:**
  - **ALT-01:** Append-only `decision-record@v1` follow-on that preserves `DEC-0044-008`, enumerates the mutation paths, states non-retroactivity, names one atomic activation commit with fail-closed rollback, and composes Family A with Family B from integrated `DEC-0041-006` without a third trailer key.
    - **Disposition:** `selected`
    - **Reason:** Closes the six conditions in `5ff5aae54` without rewriting authorized Management substance and without waiting on an unintegrated `0041` consumer-scope correction for keys that `main` already names.
  - **ALT-02:** Rewrite `DEC-0044-008` in `docs/dossiers/dec-branching-merging-strategie.md` into `decision-record@v1` shape.
    - **Disposition:** `rejected`
    - **Reason:** Published records are append-only; the assignment forbids rewriting the predecessor.
  - **ALT-03:** Treat `DEC-0044-011` as already covering trailer, `--no-ff`, and `check_policy_provenance.py`.
    - **Disposition:** `rejected`
    - **Reason:** `DEC-0044-011` names none of those three mutation elements; citing it as coverage repeats finding F-2 of `5ff5aae54`.
  - **ALT-04:** Keep `Policy-Origin-Branch:` and `Task-ID`/`Base-Ref` as unrelated conventions with no composition rule, or invent a third unifying trailer key.
    - **Disposition:** `rejected`
    - **Reason:** Unrelated conventions re-create two contradictory provenance procedures on overlapping commits; a third key is the “dritte Mechanik” `0044-04` warned against.
  - **ALT-05:** Block this record until `4a11a0d284d1ce643c233bf9d208ca9cccf7322d` and Jadzia transcription `6e967dd9a7f0b5bf3766735f497c149c6362acd6` are integrated.
    - **Disposition:** `rejected`
    - **Reason:** That candidate changes `0041` synchronous consumers, not the Family A key or the composition rule already derivable from integrated `DEC-0041-006`. Jean-luc required an exact open dependency rather than a silent wait or silent absorption.
- **Consequences:**
  - **CON-01:** `DEC-0044-008` and `DEC-0044-011` remain the substantive Management decisions. This record does not re-decide them.
  - **CON-02:** Exact mutation paths for `0044-12` (no others): `docs/pipeline/branch-workflow.md`, `AGENTS.md`, `_src/tools/check_policy_provenance.py`, `_src/tools/test_check_policy_provenance.py`, `docs/pipeline/tools.md`, and `docs/dossiers/re-intake-prozessverbesserung-integration-und-capabilities.md` (additive `DEC-0044-002`/`011` text only; original `DEC-0044-002` body is not deleted).
  - **CON-03:** Trailer Family A: required key `Policy-Origin-Branch:`; value is the branch on which the policy-touching commit was authored (`main` when the commit is governance authored under `DEC-0044-012`); required on commits that touch the declared policy paths the tool already defaults or accepts via `--policy-path`. After activation, a missing, malformed, or contradictory Family A trailer on a required commit is a finding (fail-closed for the check). Family B remains exactly `Task-ID:` and `Base-Ref:` as `DEC-0041-006` on this `main` specifies, including ancestor `Base-Ref`. Overlap carries both families. No third trailer family. Origin is never reconstructed from merge-base or `git branch --contains`.
  - **CON-04:** Non-retroactivity: no violation is asserted against history authored before 2026-08-21. Pre-decision commits without trailers are not findings. New or materially reopened post-activation work uses the new rule for its new delta.
  - **CON-05:** Activation is one Git commit that updates every path in CON-02 that actually changes, together. Until that commit, current `check_policy_provenance.py` topology classification and `DEC-0044-007`'s documented residual remain the mechanical behavior; binding `--no-ff` prose already in `branch-workflow.md` is not silently weakened. `0044-13` (hook) must not start from an unactivated suite.
  - **CON-06:** Rollback before activation abandons the `0044-12` candidate without changing operative checks. Rollback after activation reverts the CON-02 paths together to one previously coherent contract, preserves evidence, and requires impact analysis for work completed under the activated rule. Partial revert that leaves prose requiring trailers while the tool still passes missing trailers is forbidden.
  - **CON-07:** The Feature `0041` consumer-completeness dependency is **closed**. Correction `4a11a0d284d1ce643c233bf9d208ca9cccf7322d` and Jadzia transcription `6e967dd9a7f0b5bf3766735f497c149c6362acd6` are reachable from `main` `4d3f3fefae2d50fcff3d323db01451ed2d1079f9` (`git merge-base --is-ancestor` verified 2026-08-26). They remain not authority for `0044-12` CON-02 mutation.
  - **CON-08:** The implementer of CON-02 is distinct from Architect `seven` and from `agent:saru:0044-12:gov-0044-12-decision-record:20260826T154400Z`. This record does not assign that implementer, does not appropriate an existing `0044-12` claim, does not write `Acceptance: ✓`, and does not move Feature `0044` to `DONE.md`.
  - **CON-09:** `0044-04` planning-gate A1 is not a third provenance mechanism. `0044-12` is the trailer-and-check layer; `0044-13` remains the `reference-transaction` net; the integrator checkpoint remains the gate (`DEC-0044-009`).
- **Affected work units:**
  - `repository:autodocs`
  - `feature:0044`
  - `task:0044-01`
  - `task:0044-12`
  - `task:0044-13`
  - `task:0044-08`
  - `feature:0041`
  - `task:0041-02`
  - `path:docs/pipeline/branch-workflow.md`
  - `path:AGENTS.md`
  - `path:_src/tools/check_policy_provenance.py`
  - `path:_src/tools/test_check_policy_provenance.py`
  - `path:docs/pipeline/tools.md`
  - `path:docs/dossiers/re-intake-prozessverbesserung-integration-und-capabilities.md`
- **Affected gates:**
  - `validation:_src/tools/check_policy_provenance.py`
  - `validation:docs/pipeline/branch-workflow.md`
  - `task-start:0044-13`
  - `integration:0044-12`
  - `integration:0044-08`
  - `feature-closure:0044`
- **Review participation:** `none`
- **No-review reason:** Independent Architect `seven` is assigned to re-review this record after it exists (`1787751762460-6a7ad4b6`). Authoring participation by that reviewer would collapse the required distinctness from the later scope review. Project Lead `jean-luc` assigned the recording; a mailbox is not a `decision-record@v1` identity.
- **Waiver:** `none`
