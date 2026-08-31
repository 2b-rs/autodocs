# Claim: score-feedback-loop-requirements-20260831 rework

owner_token: agent:beverly:score-feedback-loop-requirements-20260831:1788205915982-a0f32d17
request_id: 1788205915982-a0f32d17
base_commit: 5b884f0c6cd69b833e33a9d975d425cb153a7ff3
capability_class: unprivileged
execution_authority: direct local execution in the assigned item-owned worktree and exact paths only
startup_review: AGENTS.md; SANDBOX.md; docs/pipeline/roles/requirements-engineer.md; docs/pipeline/core-rules.md; award 1788209078240-210b23ed; exact worktree/branch/status; agent-inbox main ancestry
state: [x]

- coordination_kind: user-directed non-backlog requirements package under
  `AGENTS.md`; no unrelated TODO Task marker or Task identity is claimed
- assignment_id: `1788209078240-210b23ed`
- parent_assignment: `1788205915982-a0f32d17`
- process: Requirements Engineering and Project Planning
- branch: `score-feedback-loop-requirements-20260831`
- worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/score-feedback-loop-requirements-20260831`
- inherited_candidate: `5b884f0c6cd69b833e33a9d975d425cb153a7ff3`
- assignment_state: `review-ready`; contractor transition follows this
  claim-finalization commit
- prior_implementation_ref: `be9b7fe128dee24daee3ae4d50cd0ae66d5ed612`
- implementation_ref: `20184a7a19ca537e924089c54fdedc06ad40e924`
- integration_reservation: Integrator `luap`, formally `on_hold` for this rework per Zed message `1788206051221-630084ca`
- current_step: narrow correction complete; submit the exact final tip for
  independent coordinator review while the held integration chain remains
  paused

## Exhaustive write scope

- `TODO-beverly-score-feedback-loop-requirements-20260831-1788205915982-a0f32d17.md`
- `docs/dossiers/score-feedback-loop-requirements-20260831.md`
- `docs/pipeline/score-feedback-loop.md`
- `docs/pipeline/website-review-flag.md`
- `TODO.md` Feature `0045` block only

## Rework requirements

- Coordinator rework `1788209078240-210b23ed` requires every durable
  curation/review arrival envelope to open the priority-gated Project Lead
  offer before the awarded Project Lead selects or hands off the trusted
  ingestion/decision recipe. Minimal routing validation may precede the offer;
  full trust, authority, staleness, duplicate, and no-mutation checks remain in
  the selected recipe, whose result emits the durable continuation event.
- Agent-inbox tasks must use executable agent-inbox ancestry: `0045-02` starts
  from agent-inbox `main`; `0045-03.01` starts from the exact `0045-02`
  candidate; and `0045-06.01` starts from the exact `0045-03.01` candidate.
  Autodocs prerequisites cross that repository boundary only as immutable
  artifact refs/digests, never as parent branches.
- Read-only verification found agent-inbox `main` at
  `071c1cb1365ec90a9c4f70748275e615b9df475d` with no local `0045*` branch;
  the corrected branch contracts therefore do not presume a cross-repository
  or pre-existing Feature parent.
- Limit the Publisher exclusion to the initial Feature rather than recording a
  permanent role prohibition.

- Remove private-branch `DEC-0045-01` allocation and nonexistent `docs/decisions` path. Task `0045-00` prepares the durable decision request and distinct Architect scope review without preallocating an identifier, and produces one approved Feature/interface baseline consumed by both fan-out nodes.
- Replace invented or incomplete paths with verified repository-relative autodocs and agent-inbox paths, including exhaustive test paths and the actual database/regeneration consumers.
- Expand every task contract with the controlled feature-breakdown fields: rights, data, tools, execution route, five-dimension cognitive evidence, test kind/evidence, role/separation, branch parent/name, source and edge derivation, Acceptance criteria, and Definition of Done.
- Restore the central priority-gated Project Lead decision branches, the six idempotence keys, curator-decision and publication-result contracts, retry/failure semantics, and the non-packaged HUD finding.
- Correct overlap: Feature `0035` owns requester/submission-dialog UX; curator-decision UI remains new work and consumes the existing `0033` intake/browser contracts.

## Recorded evidence and follow-up

- Repository inspection confirmed the real autodocs generation, curation, review-ingestion, validation, and publication paths; the inherited `autodocs/_templates/`, `autodocs/build_site.py`, `docs/decisions/`, and private-branch `DEC-0045-01` allocation are invalid.
- Zed message `1788206578430-7aec97bc` establishes that `0033-16` is the pre-release audit while `0033-16.01` is Feature 0033's single terminal integration/review floor. Therefore terminal Task `0045-06` must depend on `0033-16.01`. The same evidence confirms that `0033-13` already carries the `0035-01..03` requester-dialog regressions; Feature `0035` is not Curator-decision UI ownership.
- Zed message `1788207089236-21541e37` establishes that current `main`
  declares `runner_protocol=runner-request@v1` in `agent-workflow.json` while
  `_src/tools/runner_dispatch.py` and `_src/runner/actions-v1.json` are absent;
  `0037-46.01`/`0037-46.02` are historical/superseded. Feature 0045 must treat
  typed Runner-role recipes as proposed application interfaces, not an existing
  registry, and `0045-00`/`0045-02` must reconcile them with the authoritative
  selector before binding implementation.
- Zed message `1788207463122-5b3f5c64` establishes the one-assignment,
  one-branch/worktree, one-repository write boundary. Parents `0045-03` and
  `0045-06` therefore require bounded agent-inbox and autodocs subtasks with
  immutable producer/consumer artifacts; the parent nodes retain package-level
  aggregation/terminal semantics without mutating both repositories.
- Zed message `1788208130177-70438f41` establishes that `P0` is decorative:
  the authoritative startup rule selects the first eligible Task by
  top-to-bottom `TODO.md` scan. The intact Feature 0045 block was moved before
  the previously first Feature 0044 block; foreign Feature blocks were not
  reordered.

## Interim validation evidence

- `git diff --check`: pass.
- The first focused audit covered the seven parent tickets and exposed no
  missing controlled fields, but it is superseded by the cross-repository
  executability finding above. Revalidation must cover every added Subtask.
- Existing planned autodocs and agent-inbox paths: all present. Paths marked
  `(new)` are intentionally absent. Rejected inherited paths
  `docs/decisions/`, `autodocs/_templates/`, and `autodocs/build_site.py` are
  confirmed absent.
- `process_doc_doctor.py --root . --json`: no finding on any changed path.
  Its two repository-wide errors are on unchanged
  `docs/dossiers/0044-03-gate-scope-proposal.md` and
  `docs/pipeline/man5-risk-register.md`.
- `legacy_task_doctor.py --root . --json` remains nonzero for repository-wide
  baseline findings and one intentional Feature 0045 finding:
  `LTD-CHECKPOINT-MISSING-AUTHORITY` on `0045-06`. The requirements correctly
  refuse to invent an Architect rationale; `0045-00` now requires a distinct
  management-instantiated Architect to bind the checkpoint decision in the
  approved shared baseline before implementation starts.

## Final focused revalidation

- Eleven records are complete: seven required A–F/start parent tickets plus
  four bounded per-repository Subtasks (`0045-03.01`, `0045-03.02`,
  `0045-06.01`, `0045-06.02`). Each has task/feature/role, source and edge
  derivation, planned order, test kind/evidence, controlled capability fields,
  five-dimension `0044-06@v1` cognitive evidence, branch parent/name,
  exhaustive one-repository write scope, A1, review rationale, Acceptance
  criteria, and Definition of Done.
- Focused edge topological sort passes. Internal indegree/outdegree analysis
  yields exactly `start: 0045-00` and `terminal: 0045-06`.
- Current selector evidence is pinned:
  `agent-workflow.json runner_protocol=runner-request@v1` and
  `authority_epoch=legacy-writable`; `_src/tools/runner_dispatch.py` and
  `_src/runner/actions-v1.json` are absent; `0037-46.01`/`0037-46.02` are
  `[w]` historical/superseded.
- Existing scoped autodocs and agent-inbox paths all exist. Every absent
  planned path is explicitly marked `(new)`. Parent `0045-03` and terminal
  `0045-06` each write only one autodocs evidence path; product mutations are
  isolated to the corresponding per-repository Subtasks.
- Final `process_doc_doctor.py`: zero findings on `TODO.md` or the three
  changed documentation paths. Final `git diff --check`: pass. The sole
  Feature 0045 legacy-doctor finding remains the deliberately unclaimed
  Architect checkpoint rationale described above.
- Operational priority check: `Feature 0045` is the first Feature heading at
  `TODO.md:93`, appears exactly once, and directly precedes Feature 0044.
  A normalized comparison after excluding only the moved Feature 0045 block
  confirms all foreign Feature content and relative order match inherited
  candidate `0ffb5e906441eeca21b6939519b48582fbfe8ee5`.

## Boundaries

No production code, external GitHub mutation, credentials, publication, Acceptance, integration-checkpoint crossing, `main` advance, Feature closure, new DEC allocation, or operative cross-item gate activation. The pipeline text remains proposed/non-operative until Task `0045-00` records the Management decision and distinct Architect scope review.

## Next step

Transition assignment `1788209078240-210b23ed` to review and notify Zed with
the exact claim-finalization tip. Luap's integration assignment remains on hold
until Zed records the review disposition and resumes it with an exact SHA.

## Narrow-rework validation

- Product commit `20184a7a19ca537e924089c54fdedc06ad40e924`
  changes only `TODO.md`, the requirements dossier, and the proposed process
  contract; `git show --check` passes.
- Focused assertions pass for arrival-before-offer-before-recipe ordering in
  both feedback and Curator-decision cycles; all three agent-inbox branch
  contracts use repository-native ancestry; Feature `0045` remains the first
  Feature block; and the Publisher exclusion is explicitly limited to this
  initial Feature.
- `process_doc_doctor.py --root . --json` reports zero findings on the changed
  product paths. The two repository-wide errors remain on unchanged paths.
- `legacy_task_doctor.py --root . --json` retains the intentional
  `LTD-CHECKPOINT-MISSING-AUTHORITY` finding for `0045-06`; Task `0045-00`
  requires the distinct management-instantiated Architect to supply that
  rationale. The doctor also rejects this temporary claim's nonnumeric
  user-directed item identity; `AGENTS.md` expressly permits such a
  coordination record, and substituting an unrelated TODO Task ID would be
  false bookkeeping.
