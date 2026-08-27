# Claim: `0044-05.03` — adopt the versioned capability-matcher contract as bounded Feature-0044 pilot governance

- **owner_token:** `agent:belanna:0044-05.03:20260825T182800Z`
- **owner:** B'Elanna Torres, Team Voyager
- **capability_class:** `privileged`
- **process_role:** Implementer only for this exact item; explicitly distinct from
  Architect `data` (`0044-05.01`) and from the separately assigned privileged
  Integrator `geordi`, who reviews the complete parent `0044-05` package before any
  `main` advance. This claim does not instantiate Architect, Acceptance-reviewer,
  Integrator, checkpoint-verdict, Feature-closure, or main-advance authority.
- **execution_authority:** direct Git/text edits and validation in this item-owned
  worktree; no runner, no network, no secrets, no external effects.
- **authority_reference:** Project Lead `jean-luc`, explicit Implementer-only
  assignment, agent-inbox `1787681682578-811c37aa`, thread `0044-05`, 2026-08-25;
  authority basis stated therein: "current user's standing direction to coordinate
  PLs and execute remaining Features in parallel, and the recorded 0044-05.03
  contract at parent P."
- **branch:** `0044-05.03-belanna-20260825`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/0044-05.03-belanna-20260825`
- **write scope:** `AGENTS.md`; `docs/pipeline/capability-matching.md`;
  `docs/pipeline/tools.md`; `docs/pipeline/README.md`; this claim; path-limited
  `TODO.md` bookkeeping for the `0044-05.03` marker/REF line only.
- **prohibited:** Acceptance, review, checkpoint verdict, parent (`0044-05`) package
  completion, broad activation, historic-dispatch credit, `main` advance, unrelated
  mutation, network, secrets, external effects.

## Startup review

- No prior claim file for `0044-05.03` found repository-wide before this one;
  no conflict.
- Read the complete `0044-05.03` contract at `docs/campaign-evidence/0044-05/capability-matcher-architecture.md`
  section 10 (`0044-05.03` subsection) at parent pin `P` before any mutation.
- Independently re-verified before accepting (not taken from the assignment
  packet alone): `main` `M` = `5aefac8533bb85fec930851dbb6446608a34b352` (matched
  exactly); `P` = `4468a78d1d208bc81090ebed77de2fc34d602ed6` exists; `79f279ffc`
  (`.02` bookkeeping/product) and `a222f7b32` (topology clarification) both
  confirmed ancestors of `P` via `git merge-base --is-ancestor`.

## Candidate topology

1. `git worktree add <path> -b 0044-05.03-belanna-20260825 5aefac8533bb85fec930851dbb6446608a34b352` —
   branch cut at exact then-current `main` `M`.
2. `git merge --no-ff 4468a78d1d208bc81090ebed77de2fc34d602ed6` — assigned parent `P`
   as second parent, `M` first parent. Clean, zero conflicts. Result tip `7af5dc784`.
   Carries `.01`/`.02` product, schemas, tests, and their claims into this candidate
   per the architecture's own instruction; not an undeclared scope widening.
3. Governance edits authored only after the merge, strictly within the declared
   write scope (see below).

## Governance edits, exact scope

- **`AGENTS.md`:** new paragraph after the four mandatory briefing fields under
  "Dispatching a subagent" — Feature `0044` pilot briefing input. States the
  `capability_match.py` result is an **additional**, non-replacing briefing input;
  does not substitute for the four mandatory fields; eligibility evidence is never
  itself assignment/ownership/independence/Acceptance/waiver/specialist/release
  authority. Required non-activation sentence appended as a blockquote,
  byte-identical to the one in `capability-matching.md` (verified, see Validation).
- **`docs/pipeline/capability-matching.md`:** new file. Public contract (three
  schemas summarized), eligibility/rejection-code table, CLI/exit-code contract,
  failure/recovery section (no AI fallback, capacity-drop handling, rollback,
  additive-only schema supersession), legacy-schema distinction section
  (`agent-capability-v1.schema.json` preserved byte-for-byte, rejected as
  unsupported if given to the matcher), explicit no-grandfathering section,
  required non-activation sentence as a blockquote, provenance section naming
  `.01`/`.02`/`.03` owners and the separately assigned Integrator.
- **`docs/pipeline/tools.md`:** one new table row for `_src/tools/capability_match.py`,
  matching house style (see the `legacy_handoff_manifest.py` row as the closest
  precedent), linking to `capability-matching.md`.
- **`docs/pipeline/README.md`:** one new index entry linking `capability-matching.md`,
  placed next to the `legacy-handoff-manifest.md` entry.
- **This claim.**
- **`TODO.md`:** path-limited — only the `0044-05.03` marker (`[ ]` → `[x]`) and its
  REF line, appended below the existing contract text without altering any other
  line. No `Acceptance: ✓` added.

No other file touched. `git diff --check` clean throughout.

## Validation

- `python3 -m pytest _src/tests/test_capability_match.py -q` — **16 passed** (matches
  `0044-05.02`'s own recorded count), rerun by this claim, not merely read from
  `0044-05.02`'s bookkeeping.
- `git merge-base --is-ancestor 2c563040563b350f26e6c85b0dccb8c211fdbdef HEAD` — **OK**,
  the bound product commit is an ancestor of this candidate.
- All three schemas confirmed present under `issues/_schema/`:
  `task-requirement-profile-v1.schema.json`, `agent-capability-descriptor-v1.schema.json`,
  `capability-match-result-v1.schema.json`.
- Required non-activation sentence: present in both `AGENTS.md` and
  `docs/pipeline/capability-matching.md`. **Correction made during this claim:** the
  first draft wrapped the sentence across a mid-sentence line break in `AGENTS.md`
  (ordinary prose-wrap), which a naive single-line verbatim check would miss even
  though the words were unaltered. Rewrote both occurrences as a single unbroken
  blockquote line and confirmed byte-for-byte identical
  (`grep -n '^> This pilot requirement' AGENTS.md docs/pipeline/capability-matching.md`,
  shell string-equality check) — recorded here rather than left implicit, since a
  "verbatim" requirement should be checked, not assumed satisfied by intent.
- `git diff --check` — clean (no whitespace errors).
- No file outside the declared write scope touched (`git diff --stat` reviewed
  against the write-scope list above before this claim was finalized).

## Disposition

Candidate prepared and validated. **Not** Accepted, reviewed, or integrated by this
claim — that is the separately assigned privileged Integrator's action at the
complete parent `0044-05` mandatory checkpoint. `main` not advanced. Reporting exact
candidate tip, ordered parents, full diff, Acceptance evidence placeholders, and
validation to Project Lead `jean-luc` per the assignment packet.

## Closure (2026-08-27, supervisor claim-lifecycle instruction)

state: [x]

Implementer work for this exact item is complete as recorded above; the product
this claim prepared is already reachable from current `main`. No further action
remains under this claim. Recorded per the standing convention that a finished
claim is closed with `state: [x]` rather than left open or deleted.
