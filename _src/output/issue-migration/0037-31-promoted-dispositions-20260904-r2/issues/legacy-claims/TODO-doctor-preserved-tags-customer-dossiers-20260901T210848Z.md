# Claim: preserved/* tags for four customer-authority dossiers + registration

- **state:** `[x]` — complete
- **handover_to:** `kathryn` — authorizing Project Lead; governance text is `seven`'s, separately routed
- **handover_at:** `2026-09-01T21:15:00Z`
- **Agent:** `doctor` (Requirements Engineer, Team Voyager), `unprivileged`
- **owner_token:** `agent:doctor:preserved-tags-customer-dossiers:20260901T210848Z`
- **Branch / worktree:** `gov-preserved-tags-customer-dossiers-doctor-20260901`, own worktree
- **Base:** `main@5cfc814cb`
- **Authority:** Management `decision-1788290269652-1e9b7e68`, option `tag_and_govern`, relayed by
  `kathryn` (`1788296787038-8097d110`). Origin: my finding `1788290097738-220968d0`.

## What was done

| Tag | Points at | Preserves |
|---|---|---|
| `preserved/customer-dossier-mgmt-decision-interface-20260901-doctor` | `556216e4b` | `customer-request-management-decision-interface-20260827.md`, sha256 `f0c91f62…` |
| `preserved/customer-dossiers-batch-20260901-doctor` | `d697930b4` | `score-api-reference` `27b2874d…`, `integration-throughput` `a8278e7d…`, `pl-role-operationalization` `b3641c16…` |

Both annotated, each carrying its digests, its branch, the non-ancestry fact, and the authorizing
decision. Registration rows appended to `docs/pipeline/branch-workflow.md` § *Preserved snapshot tags
and recovery* **in the same commit**, per the duty I reported and Management adopted.

## Scope note recorded alongside the rows

These two rows differ from every preceding row: they preserve state that **does** exist in a branch.
The section's documented trigger is state existing in *no* branch, about to be cleared. Rather than let
the registry acquire rows its own section does not explain, a bounded scope note records the
difference and points at the decision. **It does not attempt the governance text** — that is `seven`'s
separately routed work, and writing it here would be exactly the scope creep I declined earlier.

## Boundaries observed

Authored on a branch cut from `main` in my own worktree, never the root checkout (`DEC-0044-015`).
**`main` is not advanced** — that is the privileged Integrator's act, not mine. No branch or tag
deleted, no `git worktree prune`, no Acceptance, no `DONE.md`, no push, no publication. The four root
originals remain untracked and untouched; the two preserved branches are unmodified.
