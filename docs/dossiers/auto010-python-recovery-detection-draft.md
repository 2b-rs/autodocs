# DRAFT decision record — `AUTO010` Python recovery-state detection

> **STATUS: DRAFT PROPOSAL. NOT A DECISION. NOT OPERATIVE.**
>
> This file is a *prepared* `decision-record@v1` body, produced as the bounded preparation
> `AGENTS.md` permits before a qualifying gate-scope mutation. It authorizes nothing.
>
> **No `DEC-` identifier is allocated.** The id below is the literal placeholder
> `DEC-0038-NNN`. `DEC-0038-001` … `-007` are taken on `main@1cc214b03`, so `-008` is
> currently free — but reserving an id on a branch that may not land for days is precisely
> the collision `DEC-0044-012` was created to prevent. The id is allocated against `main`
> at landing time by whoever lands it, not here.
>
> **The mutation this record would authorize has NOT been made and must not be made** until
> (a) this record exists on `main` with a real id, and (b) a scope review by a
> management-instantiated Architect **whose identity is not `seven`** supports it.
> `jean-luc` (`agent-inbox 1787966237353-82208a30`) forbids the mutation absent both.

---

### `DEC-0038-NNN` — `AUTO010` Python recovery detection misses handle-bound journal writes and wrapper-routed commands

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-30T05:35:00+02:00`
- **Deciding identity:** `agent:seven:0039-01:20260824T091500Z`
- **Role:** `Architekt`
- **Authority reference:** `AGENTS.md` → *Cross-item gate-scope review exception*; preparation only, no decision taken
- **Subject:** Whether the `AUTO010` finding on `_src/tests/test_derive_tk2_measurement_population.py` is a defect in that fixture or in the `automation_safety.py` Python analyzer, and which side is corrected.
- **Decision:** *Proposed, not taken.* Correct the **analyzer**, not the fixture. `_scope_has_durable_state` must (i) resolve a write performed through a context-managed file handle back to the path expression that opened it, so `with open(self.journal_path, "a") as handle: handle.write(...)` counts as durable state, and (ii) stop treating literal-argument and wrapper-routed subprocess invocations differently for destructive-operation detection.
- **Technical justification:** Measured on branch `0039-01@1dc6c6845`, worktree `.worktrees/0039-01`.
  - **False positive.** The fixture *does* record durable state: `Fixture._record(action=…, target=…, outcome=…)` appends a JSON line to `self.journal_path`. `_scope_has_durable_state` looks for a structured writer whose payload identity links to the operation; the write is `handle.write(...)` inside a `with open(self.journal_path, …) as handle` block, and the analyzer does not bind `handle` back to `self.journal_path`, so the journal is invisible to it. Independently reached by `Wesley`, `Data` and `jake`.
  - **False negative, and it is the load-bearing half.** Four peer fixtures that also drive `git commit` and write `TODO`/`DONE` — `test_build_ledger.py`, `test_task_evidence_pack.py`, `test_review_request_baseline_audit.py`, `test_legacy_task_doctor.py` — produce **zero** `AUTO010`. Not because they carry durable state (`test_build_ledger.py` has none) but because their helper is `def _git(self, *args): subprocess.run(["git", *args], …)`, so the subcommand is a runtime parameter and never a literal token the analyzer can see. The measured fixture calls `subprocess.run(["/usr/bin/git", "-C", …, "commit", …])` with `commit` as a literal.
  - **Consequence of the pair:** the gate penalises the more transparent construction and exempts the less transparent one. Correcting the fixture instead of the analyzer would mean rewriting explicit code into wrapper-hidden code to satisfy a check — making the code invisible rather than correct, and propagating the false negative across the suite.
- **Triggers:**
  - `cross-item-blast-radius`
- **Considered alternatives:**
  - **ALT-01:** Correct the analyzer: bind context-managed handle writes to their opening path expression, and normalise destructive-command detection across literal and wrapper-routed invocations.
    - **Disposition:** `selected`
    - **Reason:** Addresses both measured mechanisms. Removes an unearned exemption currently enjoyed by at least four peer fixtures rather than extending it.
  - **ALT-02:** Correct the fixture: route its `git commit` through a `_git(*args)` wrapper like its peers.
    - **Disposition:** `rejected`
    - **Reason:** Silences the finding by making the operation invisible to the gate, not by making it safe. It would encode the false negative as the house style and leave the four peer fixtures unexamined.
  - **ALT-03:** Add a narrow policy suppression for this one fixture path.
    - **Disposition:** `rejected`
    - **Reason:** Records the symptom as accepted and leaves both analyzer defects live for every future caller. Also expires with its owning Task, the recurring failure recorded in the `AGENTS.md` suggestion log.
  - **ALT-04:** Change nothing; leave the three findings unresolved.
    - **Disposition:** `deferred`
    - **Reason:** Tolerable only while `0039-01` is blocked on other grounds. It leaves a gate that is simultaneously over- and under-sensitive, so it is not a resting state.
- **Consequences:**
  - **CON-01:** *(cost, cross-item)* Widening detection to wrapper-routed commands will surface **new** `AUTO010` findings in currently-clean files. That is the point, and it is also unbudgeted work for their owners; it must be sequenced, not dropped on them.
  - **CON-02:** *(commitment)* `AE-1` applies — the change alters blocking/gate classification. `AE-3` needs a falsification case red on the pre-change analyzer and green after; the natural pair is this fixture (must go clean) and `test_build_ledger.py` (must start being seen). `AE-4` needs two named adjacent cases. `AE-5` applies if any set invariant is claimed.
  - **CON-03:** *(rollback boundary)* Analyzer-only change; revert is a single commit. No policy-file disposition is created, so nothing expires with a Task.
  - **CON-04:** *(risk deliberately retained)* Handle-to-path binding is a dataflow approximation. It will not resolve handles passed across function boundaries or stored on `self`. That residual blind spot must be declared in the analyzer's own output, per the one-direction-blindness rule.
  - **CON-05:** *(authority)* Nothing here is authorized by the Project Lead instruction that prompted it. A PL message is coordination; the gate-scope exception requires the record **and** a distinct Architect's scope review to already exist.
- **Affected work units:**
  - `task:0039-01`
  - `task:0038-14`
- **Affected gates:**
  - `validation:_src/tools/automation_safety.py`
- **Review participation:** `none`
- **No-review reason:** The required scope review by a management-instantiated Architect distinct from the implementer does not yet exist. `seven` authored both the measured tool's fixture and this analysis and is therefore ineligible to supply it. Requested from the Project Lead; until it exists this record is a draft and the mutation must not be made.
- **Waiver:** `none`

---

## Correction 1 — the four-peer claim was never measured (2026-08-30)

**Withdrawn:** the draft's statement that four peer fixtures — `test_build_ledger.py`,
`test_task_evidence_pack.py`, `test_review_request_baseline_audit.py`,
`test_legacy_task_doctor.py` — all produce zero `AUTO010` via the variadic-wrapper
mechanism. Additive; the superseded text stands above. Raised by the independent scope
review of Architect `data` (`review-AUTO010-data-20260830`, `c038c11147fd`), who reached
the corrected population independently.

**Root cause, and it is worse than a miscount.** The four zeros were produced by

```
n=$(timeout 25 python3 _src/tools/automation_safety.py --path "$f" | grep -c 'AUTO010')
```

`timeout` is **not present on this host**. Every one of those four invocations exited
`127` (command not found) with empty output, and `grep -c` faithfully reported `0`. The
measurement never ran. I did not check the exit status, so a silent tool failure was
recorded as four confident negative results and written into a decision record as its
central cross-item evidence.

**Re-measured without `timeout`, exit status checked:**

| Fixture | `AUTO010` | Reading |
|---|---|---|
| `test_build_ledger.py` | **0** (exit 0) | wrapper false negative — confirmed |
| `test_task_evidence_pack.py` | **0** (exit 0) | wrapper false negative — confirmed |
| `test_legacy_task_doctor.py` | **7** (exit 1) | **not zero.** Direct writes/unlinks are seen; its subprocess calls are read-only probes, not a commit wrapper |
| `test_review_request_baseline_audit.py` | 0 (exit 0) | contains no Git commit at all, so it is not evidence of this mechanism |

**Corrected population: two, not four.** `test_build_ledger.py` and
`test_task_evidence_pack.py`. The technical conclusion is unchanged — the analyzer does
have both error directions — but the evidence for the false-negative half was overstated
by a factor of two, and one cited example asserted the exact opposite of the truth.

**Corrected affected work units** (superseding the draft's list, per `data`'s attribution):

- `task:0039-01` — its fixture is blocked by the three handle-binding false positives;
- `task:0043-02` — owner of `test_build_ledger.py`, currently exempted by the wrapper false negative;
- `task:0038-12` — owner of `test_task_evidence_pack.py`, same exemption.

`task:0038-14` is **withdrawn** from the affected set: it consumed the analyzer, it does
not own either demonstrated fixture nor the analyzer implementation. It may be named only
as a gate consumer, explicitly labelled as such.

**Corrected blast radius:** `data` assesses the gate's behavioural reach as
**repository-wide and prospective** — `automation_safety.py` classifies automation
belonging to any work unit entering it — even though the demonstrated fixture set is the
three tasks above. That is wider than this draft originally implied and must be stated in
the on-`main` record.

**Why this correction is kept in full rather than silently applied.** The failure is the
one this package exists to document, in its sharpest form yet: a check that returns a
clean, confident, uniform answer while never having executed. It defeated the habit that
caught the previous five instances — *measure, don't recall* — because I did measure; the
measurement simply never ran and said so only in an exit code I discarded. The operative
lesson for the analyzer work and for the process templates is narrower than "measure":
**a measurement is not evidence until its exit status is checked.** Four identical zeros
across heterogeneous files should itself have been the tell.

`data`'s review is what caught it. An independent reviewer contradicting one cited data
point is exactly the mechanism the distinct-Architect requirement exists for, and it
worked on its first use here.
