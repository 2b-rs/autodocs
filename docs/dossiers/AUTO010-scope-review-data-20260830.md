# AUTO010 scope review — Python recovery-state detection

- **Review identity:** `data`
- **Role:** management-instantiated Architect, Process Architecture
- **Reviewed baseline:** `auto010-decision-draft-seven-20260830@830c6f1a096b719a115aa8a7af2f907549c6b9c9`
- **Reviewed proposal:** `docs/dossiers/auto010-python-recovery-detection-draft.md`
- **Review type:** independent cross-item gate-scope review; not Task Acceptance, integration review, implementation authority, or a decision record
- **Decision identifier allocation:** none

## Verdict

**Support the analyzer-correction direction, with required corrections to the
draft's evidence and blast-radius statement before the decision record becomes
operative.** The `AUTO010` analyzer has both demonstrated error directions:
it fails to associate a context-manager-bound handle with the path opened for
durable journal output, and it fails to resolve mutating commands routed through
variadic Python wrappers. Correcting the measured fixture to hide its literal
`git commit` behind such a wrapper would preserve the false negative and is not
an acceptable resolution.

The proposed mutation meets the canonical `cross-item-blast-radius` predicate:
it changes a repository validation gate's classification of more than one work
unit. The scope is therefore supportable only after the on-`main` decision record
states the corrected evidence and affected units below. This review does not
authorize mutation before that record exists on `main` with a real, uniquely
allocated identifier.

## Independent classification

### Handle-bound journal: analyzer false positive confirmed

At the pinned source, `_src/tests/test_derive_tk2_measurement_population.py`
performs three operations classified as `AUTO010`: the initial `DONE.md` write,
the per-event `TODO.md` write, and the literal `git commit`. Each is followed on
its execution path by `_record(...)`. `_record(...)` builds a structured record
containing `action`, `path`/`target`, `outcome`, `status`, and `recovery`, then
appends it to `self.journal_path` through:

```python
with open(self.journal_path, "a", encoding="utf-8") as handle:
    handle.write(json.dumps(entry, sort_keys=True) + "\n")
```

The current `_scope_has_durable_state` machinery profiles direct path writes and
`open(...)` calls, but the `handle.write(...)` call does not expose the opening
path to `_write_target_node`; no binding from the `with ... as handle` target to
`self.journal_path` is resolved. Consequently the structured writer is missed.
The fixture has durable outcome/recovery state; these three `AUTO010` results are
false positives in the analyzer.

A correction must remain conservative: recognize the context-manager binding
and the write through that bound handle, retain the existing operation-identity
and postdomination requirements, and state the residual unsupported dataflow
cases. Merely treating any `.write(...)` call as durable state would widen the
false-negative surface and is not supported.

### Variadic Git wrappers: analyzer false negative confirmed, claimed population corrected

The wrapper mechanism is real. At the same pinned baseline both
`test_build_ledger.py` and `test_task_evidence_pack.py` define a helper whose
subprocess command is `['git', *args]`; callers pass `"add"` and `"commit"` as
parameters. A scan of each full file reports no `AUTO010`. The analyzer sees the
literal command only inside the wrapper body and does not propagate the
call-site arguments into its destructive-command classification. Thus mutating
Git calls can be hidden from the gate by one ordinary helper boundary.

The draft's statement that **four** named peer fixtures exhibit this mechanism
is not supported:

- `test_review_request_baseline_audit.py` contains neither the asserted Git
  wrapper nor a Git commit operation.
- `test_legacy_task_doctor.py` does not contain the asserted variadic commit
  wrapper. Its relevant subprocess calls are read-only probes, while the file
  already produces multiple `AUTO010` findings for direct writes/unlinks.

Therefore the independently confirmed wrapper-routed false-negative population
among the four named peers is **two**, not four. The technical conclusion still
holds, but the proposed record must not use the two unsupported examples as
evidence or claim that all four write `TODO`/`DONE` and commit them.

## Corrected blast radius

The minimum evidenced work-unit set is:

- `task:0039-01` — its measurement fixture is currently blocked by three
  handle-binding false positives;
- `task:0043-02` — owner of `test_build_ledger.py`, currently exempted by the
  variadic-wrapper false negative;
- `task:0038-12` — owner of `test_task_evidence_pack.py`, currently exempted by
  the same false negative.

The affected gate is `validation:_src/tools/automation_safety.py`, whose normal
tracked-source coverage can classify automation belonging to any work unit.
Accordingly the behavioral reach is repository-wide for future and current
items entering that validation gate, even though the presently demonstrated
fixture set is the three tasks above.

`task:0038-14` is not supported as the owner of either demonstrated peer
fixture or of the analyzer implementation; it consumed the analyzer for chore
inventory work. It may be named only as a gate consumer if the final record
states that relationship explicitly, not as a substitute for the evidenced
owners above.

## Required decision and implementation boundaries

The on-`main` decision record must:

1. retain the selection to correct the analyzer rather than conceal the literal
   command in the `0039-01` fixture;
2. replace the four-peer claim with the two confirmed files and name their
   owning work units;
3. distinguish the minimum demonstrated task set from the gate's
   repository-wide prospective reach;
4. require red-before/green-after falsification for both error directions;
5. include adjacent negative cases proving that unrelated handle writes and
   non-mutating wrapper calls remain unclassified;
6. declare the bounded dataflow model, including unsupported cross-function or
   stored-handle flows, rather than implying complete Python call resolution.

Subject to those corrections and the required on-`main` decision record, the
proposed analyzer scope is **supported**. The draft as presently worded is not
sufficient evidence for the mutation because its peer count and affected-work-
unit classification are materially overstated.
