# Retrospective Pilot — Feature 0040

**Assessment type:** Candidate-process retrospective; no `0040` marker, claim, scope, or acceptance state was changed.

**Why materially different:** `0040` is a repository-process and governance Feature. Its primary risk is a cross-item decision/gate with latent blast radius, rather than an operational implementation migration.

## Candidate-process coverage

| Candidate control | Observed evidence | Assessment |
|---|---|---|
| Intake and outcome | `TODO.md` Feature 0040 trigger and requirements baseline | Outcome and incident evidence are explicit. |
| Requirements/architecture boundary | `docs/dossiers/re-intake-evidence-traceability-and-roles.md`; `0040-01` role model | The process boundary is explicit; it does not claim ECU assessment capability. |
| Stable outcomes to Tasks | `RQ-ROLE-*`, `RQ-DEC-*`, `RQ-PROC-*`, `RQ-TRACE-*` allocations in `TODO.md` | Coverage exists, including dispositions for superseded/deferred Tasks. |
| Decision and authority interface | `DEC-0040-001`…`0040-004`; `process-roles.md` TK-2 | The incident demonstrates why a blast-radius decision record is required. |
| Semantic-deadlock audit | Feature closure edge `0040:0039-01` and its recorded management decision | The gate is explicit rather than silently bypassed; it remains a closure, not implementation-start, gate. |
| Parent integration | `0040-09` is the mandatory integrating Task | Parent-level coherence is a real deliverable. |

## Findings

- `P0040-01` (observation): A candidate contract should carry one compact, machine-checkable criterion-to-Task-to-evidence manifest; current coverage is distributed across backlog prose and dossiers. This is a candidate-process improvement, not a change to `0040`.
- `P0040-02` (pass): The separate decision/role records make the cross-item blast-radius control auditable before implementation.

## Verdict

The candidate process would retain the Feature's explicit outcome and authority boundary, identify the distributed coverage manifest as a pre-baseline improvement, and preserve the closure gate. No conclusion is drawn about acceptance of `0040`.

## Process-version pin and re-check — added 2026-08-26

**This pilot originally pinned no process version.** It assessed "the candidate process"
without naming which text, so a reader could not tell afterwards what was piloted. That is a
violation of `feature-definition-and-breakdown.md` §7a.2, committed by this package before that
rule existed. The pin is added retrospectively rather than the pilot being rewritten.

| | |
|---|---|
| Process text assessed | `docs/pipeline/feature-definition-and-breakdown.md` and siblings, as of branch `0039-01` @ `316bce655` |
| Governance baseline | `main` @ `9ccd99b25`; `feature-breakdown.md` from Task `0044-04` (`[x]`, **Task Acceptance `✓`**), its §8 from `0044-06` (`[x]`, integration-reviewed, **no Task Acceptance**) |
| Assessed Feature | unchanged — no marker, claim, scope, or acceptance state of the assessed Feature was touched, then or now |

**Re-check against the reworked process.** Every control row above was re-read against the
current text. **All rows still map**, and none depended on removed material:

- The removed templates §C (the competing eight-field decision-record format) is **cited by
  neither pilot** — both reference real `DEC-` records instead — so its removal disturbs no row.
- §4's move from restating breakdown mechanics to citing `feature-breakdown.md` does not change
  what the rows assess; it changes where the rule is written.
- `feature-breakdown.md` §8 adds cognitive-demand fields to the **task record**, which these
  retrospective assessments do not produce; no row is invalidated, and no row now covers it.

**What this re-check does not claim.** It does not upgrade these pilots into evidence for the
*expanded* contract. They demonstrate that the process can be applied retrospectively to two
materially different Features; they do not address the 20-Task effectiveness measurement added
to the contract later, which is carried by
`docs/dossiers/0039-01-effectiveness-measurement.md` instead. Nor does a re-check substitute
for the independent review that the exit criteria require.
