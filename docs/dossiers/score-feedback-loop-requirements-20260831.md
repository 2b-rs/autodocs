# S-Core Feedback Loop Requirements Dossier

## Provenance and status

This dossier preserves the material requester requirements recorded verbatim in
the ancestor commit messages `8a9961674a`, `b5eeddbe97`, and `0ffb5e9064`.
Repository evidence was rechecked on 2026-08-31 against the current Feature
0019, 0021, 0033, and 0035 contracts. The target pipeline is proposed and
non-operative until Task `0045-00` records a resolved Management decision
request, a supporting scope review by a distinct management-instantiated
Architect, and one approved shared Feature/interface baseline.

## Atomic requirements

- **REQ-0045-01 — Product entry point.** The official 2b-rs.github index shall
  let a user reach both the existing AUTOSAR Adaptive documentation and a first
  pretty-printed S-Core documentation tree.
- **REQ-0045-02 — Authoritative multilingual publication.** Both trees shall be
  generated from the latest authoritative database snapshot in every language
  configured by `_src/site.json`; publication evidence shall identify that
  snapshot and the generated digest set.
- **REQ-0045-03 — No component-library constraint.** Feature 0045 shall not
  require use, reuse, or creation of an S-Core component library.
- **REQ-0045-04 — Priority-gated scheduling.** Every durable curation/review
  arrival envelope that passes the minimum validation needed to route it shall
  produce a priority-gated Project Lead offer **before** trusted ingestion or
  decision-recipe execution. The awarded Project Lead may hand the item to a
  Project Lead already handling a materially similar item, create a dependent
  typed-runner assignment, or hand the same item to a runner when the action is
  trivial. The selected recipe shall still perform full trust, authority,
  binding, staleness, and duplicate checks before any queue, history, factual,
  or publication mutation.
- **REQ-0045-05 — Central Project Lead decisions.** Similar-item handling,
  dependency creation, trivial-runner handoff, proposal disposition, and
  publication continuation shall remain explicit Project Lead decision
  branches with durable outcomes; Supervisor and runner code shall not make
  those product/workflow decisions.
- **REQ-0045-06 — Feedback/proposal cycle.** Browser feedback shall become a
  durable GitHub request, trusted ingestion result, committed queue item,
  awarded AI assignment, evidence-bearing proposal, and GitHub-backed proposal
  version without directly changing canonical factual data.
- **REQ-0045-07 — Decision/publication cycle.** A Curator shall inspect the
  exact proposal and baseline, write a durable accept/reject/revision decision,
  and only an accepted non-stale decision may be applied transactionally,
  committed as a database version, projected live, regenerated, validated, and
  published.
- **REQ-0045-08 — Typed deterministic recipes.** Feedback ingestion, AI
  proposal, and apply/regenerate/publish shall be deterministic typed recipes.
  Recipes may validate and execute an awarded transition, but may not assign
  work, decide products, accept their own proposal, grant authority, or cross a
  release gate.
- **REQ-0045-09 — Live/static truth.** The UI shall distinguish live workflow
  state from publication state. Exact acceptance wording:
  **“DHTML shows what is happening now; static HTML proves what was
  published.”** Static generation shall remain complete, multilingual,
  deterministic, link-validatable, and usable when JavaScript is unavailable.
- **REQ-0045-10 — Durable Curator decision.** A decision shall bind proposal
  ID/version, baseline record version/hash, Curator identity/authority
  evidence, decision revision, disposition, rationale, evidence references,
  timestamp, and stale-check result. Accept, reject, and request-revision shall
  be distinguishable and replay-safe.
- **REQ-0045-11 — Publication result.** Apply/publish shall return a typed
  result containing proposal and accepted-decision IDs, database commit,
  generator version, static publication commit/target, digest manifest,
  configured-language set, validation result, workflow/publication state, and
  retry/failure disposition. Success shall not be reported before every
  required durable effect is proven.
- **REQ-0045-12 — Idempotence and retry.** The six exact idempotence keys in
  `docs/pipeline/score-feedback-loop.md` shall cover feedback, proposal,
  decision, apply, publish, and chat operations. Same-key/same-payload replay
  returns the recorded result; same-key/different-payload is a conflict;
  retryable failure retains ancestry and resumes from the last proven durable
  boundary; terminal failure emits an actionable durable result and never
  advances state.
- **REQ-0045-13 — HUD evidence boundary.** `supervisor-gui.py`,
  `supervisor.py`, `roster-gui.js`, and `README.md` in agent-inbox are evidence
  for interaction concepts such as SSE, assignment cards, causal chat,
  structured handoff, acknowledgement/retry, provenance, and decisions. They
  are not a packaged reusable component and are not an implementation scope for
  the S-Core Curator UI.
- **REQ-0045-14 — Existing-feature ownership.** Feature `0035` remains the
  requester/submission-dialog UX acceptance set; its regressions are carried
  through `0033-13`. The new Curator-decision UI consumes Feature `0033`
  intake, authenticated lifecycle, browser, transport, accessibility, and test
  contracts without claiming that Feature 0045 implements Feature 0035.
- **REQ-0045-15 — Historical 0021 truth.** The manual/non-bypass contract in
  `docs/pipeline/website-review-flag.md` remains the historical Feature 0021
  truth. Feature 0045 may link a proposed continuation but shall not describe
  it as operative before `0045-00`.
- **REQ-0045-16 — Runner selector compatibility.** “Typed Runner-role recipe”
  names a proposed deterministic application interface, not an existing queue
  registry. Task `0045-00` shall resolve the interface choice and `0045-02`
  shall reconcile it with the current authoritative selector and agent-inbox
  assignment Runner before implementation paths are bound. No absent or
  retired registry may be treated as current infrastructure.
- **REQ-0045-17 — Operational priority.** Human labels such as `P0` shall not
  be the sole priority mechanism. While the legacy TODO startup scan is
  authoritative, the Feature 0045 block shall precede the previously first
  Feature block so the globally eligible scan encounters `0045-00` first,
  without changing the relative order or content of foreign Feature blocks.

## Repository evidence and overlap

- **Feature 0019:** `0019-13` owns the two known S-Core link-defect classes.
  Task `0045-01` consumes that work in the next publication baseline; it does
  not rewrite a historic publication digest.
- **Feature 0033:** `0033-06` supplies trusted-target/transport verification;
  `0033-07` atomic idempotent queue write; `0033-07.01` authenticated,
  role-enforced lifecycle transitions; `0033-10` browser packaging/staging;
  `0033-11` truthful receipt/stale/duplicate/failure UI; `0033-12`
  accessibility/no-JS; `0033-13` realistic transport and Feature 0035
  regressions; `0033-16.01` the terminal Feature 0033 integration/review floor.
- **Feature 0035:** requester identity, submission dialog, transport result,
  and recovery UX only. It is not the Curator-decision surface.
- **Feature 0021:** manual curation entry and the Curator-only apply/complete
  boundary remain normative history.
- **Autodocs implementation evidence:** `_src/generate.py`,
  `_src/sources/pages/index.json`, `_src/site.json`,
  `_src/tools/score_curation_views.py`,
  `_src/tools/prepare_score_curation_export.py`,
  `_src/tools/review_request_ingest.py`, `_src/tools/curation_ingest.py`,
  `_src/tools/score_curation.py`, `_src/tools/curation_flags.py`, `review.js`,
  `_src/validate.py`, and `_src/tools/publish_public_site.sh`.
- **Runner evidence:** current `agent-workflow.json` declares
  `runner_protocol=runner-request@v1` and `authority_epoch=legacy-writable`;
  the selector named by `SANDBOX.md` remains machine authority.
  `_src/tools/runner_dispatch.py` and `_src/runner/actions-v1.json` are absent,
  while `0037-46.01`/`0037-46.02` are historical/superseded. The Feature 0045
  typed recipes therefore require an explicit compatibility decision rather
  than a fabricated registry path.
- **Priority evidence:** `AGENTS.md` selects the first globally eligible Task
  by a top-to-bottom `TODO.md` scan and defines no operative `P0` marker.
  Feature 0045 is therefore placed before Feature 0044; the A–F/P0/P1 labels
  remain human explanations only.
- **Rejected inherited paths/claims:** `docs/decisions/DEC-0045-01.md`,
  `autodocs/_templates/`, and `autodocs/build_site.py` do not exist; a private
  branch may not allocate a `DEC-*` ID.

## DAG intent

| Task | Producer/consumer intent |
| --- | --- |
| `0045-00` | Single start; prepares the Management decision request and distinct Architect review, then records one approved shared baseline. |
| `0045-01` | Fan-out A; consumes the approved baseline and `0019-13`, producing the navigable multilingual publication baseline. |
| `0045-02` | Fan-out B; consumes the same approved baseline, producing typed event/scheduling and Project Lead decision contracts. |
| `0045-03.01` | Agent-inbox Subtask; consumes `0045-02` and produces a versioned feedback-recipe/result contract without assuming a registry. |
| `0045-03.02` | Autodocs Subtask; consumes `0045-03.01` plus `0033-06`/`0033-07` and produces the trusted committed queue item. |
| `0045-03` | Autodocs parent package; verifies the two immutable repository candidates and records their interface/digest aggregation. |
| `0045-04` | Consumes the queue item and scheduling contract; produces an evidence-bearing proposal plus causal, non-authoritative chat handoff. |
| `0045-05` | Consumes the proposal and `0033` authenticated browser contracts; produces the durable Curator decision. |
| `0045-06.01` | Agent-inbox Subtask; produces the accepted-decision→apply/publication recipe/result contract under the approved runner interface. |
| `0045-06.02` | Autodocs Subtask; consumes `0045-06.01`, `0045-01`, `0045-05`, and `0033-16.01` to apply, regenerate, validate, and publish under separate authority. |
| `0045-06` | Exactly one terminal parent; consumes canonical receipts from both per-repository Subtasks and records the cross-repository terminal proof without itself mutating both repositories. |

Agent-inbox ancestry is repository-native: `0045-02` branches from current
agent-inbox `main`; `0045-03.01` branches from the exact `0045-02` agent-inbox
candidate; `0045-04` branches from the exact `0045-03.01` agent-inbox
candidate; and `0045-06.01` branches from the exact `0045-04` agent-inbox
candidate. Autodocs outputs such as the approved `0045-00` baseline, the
`0045-03` queue-item/aggregation artifacts, and the `0045-05`
Curator-decision contract are consumed by immutable ref and digest; they are
not parent branches in the agent-inbox repository.

## Assumptions, exclusions, and open authority

- **Assumption A-0045-01:** GitHub remains the durable transport/provenance
  boundary for requests, proposals, and decisions. Task `0045-00` must confirm
  or replace this assumption before implementation becomes operative.
- **Assumption A-0045-02:** The existing score-curation record/flag tools remain
  the canonical database application boundary. The terminal task must verify
  this against its pinned baseline.
- **Open interface OI-0045-01:** Whether the typed recipes bind directly to
  `runner-request@v1`, an agent-inbox assignment Runner adapter, or another
  Management-approved interface is intentionally unresolved. `0045-00` decides
  the contract; `0045-02` proves selector compatibility. Downstream tasks may
  not guess.
- **Exclusions:** no Publisher role for now/in this initial Feature, no generic
  HUD/component-library extraction, no browser direct canonical writes, no AI
  self-acceptance, no source-history publication output, and no Feature 0035
  redesign.
- **Open authority:** only Management can resolve the cross-item scheduling
  policy; only a distinct management-instantiated Architect can supply the
  required scope review; only an authorized Curator can decide a proposal; and
  only an authorized Integrator/release operator can cross integration and
  publication gates.

## Acceptance intent

Acceptance must trace every `REQ-0045-*` to committed evidence, demonstrate the
two real GitHub round trips and all six idempotence classes, exercise
stale/duplicate/conflict/retry/terminal-failure paths, verify the exact
database-to-multilingual-static digest chain, and independently confirm the
authority separations above. A green recipe test alone is not evidence that
the scheduling scope, Curator decision, integration, or release is authorized.
