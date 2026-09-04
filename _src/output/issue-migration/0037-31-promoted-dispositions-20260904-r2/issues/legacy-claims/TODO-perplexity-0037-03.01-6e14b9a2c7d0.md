# TODO-perplexity-0037-03.01-6e14b9a2c7d0.md — active claim

## Claim identity

- `task_id`: 0037-03.01
- `feature_id`: 0037 — Git-Native Issue Store, Provenance Graph, and Backlog Migration
- `agent`: perplexity (SANDBOXED AGENT PERPLEXITY)
- `capability_class`: sandboxed/grunt — execution only via the singleton root `run.sh` runner slot
- `request_id`: 6e14b9a2c7d0
- `owner_token`: agent:perplexity:0037-03.01:6e14b9a2c7d0
- `base_commit`: c7ab7480b09d32e18222bb61fef1477958dcfc43
- `claim_opened`: 2026-08-16 (Europe/Berlin)
- `state`: [p]

## Task and scope

Task text (from TODO.md):

- [ ] **0037-03.01** PREREQ: 0037-03.01:0037-02 Define lifecycle transitions, criterion evidence, decisions, and terminal records in `docs/pipeline/issue-lifecycle.md`.
  - **Acceptance criteria:** Map `[ ]/[u]/[p]/[?]/[w]/[x]`; reserve `[u]` for the next unresolved human decision; define roles and transition authority; require checked `AC-NNN` entries with reachable evidence and `closure.json` for completion; distinguish completed, wontfix, superseded, duplicate, cancelled, and archived-not-accepted; preserve Feature `0021`'s historical non-acceptance; and retain the two-commit rule for real commit refs.
  - **Definition of Done:** `issues/_schema/issue-closure-v1.schema.json`, `issues/_schema/issue-decision-v1.schema.json`, transition table, authority matrix, and positive/negative fixtures are review-ready and committed.

Prerequisite `0037-02` is `[x]`, with closure commit `91a4b99fb07948cdea4c71d18ada49f4d661ea42` and REF bookkeeping commit `610a324208bcb85bd847c219d60315b8c924614c`.

## Intended write scope

- `TODO.md` — only task `0037-03.01` marker and its claim/closure records
- `TODO-perplexity-0037-03.01-6e14b9a2c7d0.md` — this claim
- `docs/pipeline/issue-lifecycle.md`
- `issues/_schema/issue-closure-v1.schema.json`
- `issues/_schema/issue-decision-v1.schema.json`
- `issues/_schema/fixtures/issue-lifecycle/`
- `run.sh` — one-use runner envelopes for this claim only

## Runner scope

- Root `run.sh` singleton slot; inspected as free before this claim was opened.
- Initial request is fixed read-only discovery only. It may inspect current commit, authority state, index/worktree status, relevant existing lifecycle/provenance material, active claims, and slot state. It must not mutate files, refs, index, or external state.

## Assumptions

- No external service, credential, approval, or architecture choice is required to produce the review-ready lifecycle contract and schemas.
- `0037-03.02` is a sibling task and is outside this claim’s write scope.

## Progress log

- 2026-08-16 — Self-selected as the first open, unclaimed Task after closed `0037-02`; prerequisite check passed. Claim created with `base_commit: pending-discovery`; publishing the required fixed read-only discovery request.
- 2026-08-16 — Validation and substantive commit request `4c6a1e8b9d20` succeeded. Commit: `f3adcde91487f774d29b80985f54a5736da556bd`; JSON syntax and lifecycle fixture semantic checks passed. Task marked [x]; REF bookkeeping pending this commit.
- 2026-08-16 — Repair request `8a4d6f1c9b72`: prior bookkeeping heredoc expanded Markdown backticks, so it omitted the intended TODO closure note and rendered `[x]` empty in this claim. The substantive commit remains `f3adcde91487f774d29b80985f54a5736da556bd`; this repair adds the missing additive closure evidence and corrects the claim history.
