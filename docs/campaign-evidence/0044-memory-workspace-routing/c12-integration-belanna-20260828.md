# DEC-0044-029 C12 corrections — independent review and conditional integration

- **Reviewer/Integrator:** belanna (privileged Integrator, Team Voyager)
- **AWARD:** `1787907897508-0b0a8752` (jean-luc, thread `DEC-0044-029-c12-corrections`); OFFER `1787907793015-6f305ecf`, ACCEPT `1787907836213-0d9006d5`.
- **Independence:** not Tuvok (implementer of both the original routing change and the corrective wave; excluded from Integrator/Acceptance/signing-security by his own AWARD's terms), not Seven (authored the governing C12 Architect re-review), not william (dispatcher of the implementation/corrective AWARDs), not jean-luc (Project-Lead-acting dispatcher of this review).
- **Governing review:** `docs/campaign-evidence/0044-memory-workspace-routing/c12-rereview-seven-20260828.md` at `aad2774215f57344978196c73dc450dba3395dc1` — Architect `seven`, verdict `supports-with-conditions`, conditions C-1 (blocking for activation, not integration), C-2 (clarification), C-3 (activation provenance).

## Pins (independently remeasured, both repos, before cutting anything)

| Repo | Item | Value |
|---|---|---|
| agent-inbox | target at AWARD | `main@1d75e4573cf1f0cd6768b74d96b902593321322c` — confirmed exact match, no drift throughout |
| agent-inbox | candidate | `024c3bef5757882ea03afc28742afbf387fc62db` — confirmed via `git rev-parse` |
| agent-inbox | ancestor check | `main` **is** an ancestor of candidate — ff-only viable directly |
| autodocs | target at AWARD | `main@22f1096c6e75c7cccaab2f381ed155c93b5b09d2` — confirmed exact match at review start |
| autodocs | target at merge time | `main@3dd4e23354886134939a7a161458f3123a8c791e` — **drifted** (disjoint `0027-05` governance work + the `0037-11.02` AE candidate I reviewed earlier being landed) |
| autodocs | candidate | `348db37d31ab1c17540766ccb98b801da76daafc` — confirmed via `git rev-parse`; merge-base with original target `16664ebc8622c5bd035cee9facdce9bbe2e8c7b2` |
| autodocs | reconciliation | zero path overlap between candidate's 3-file scope and everything landed on `main` since `22f1096c6`; old target confirmed still an ancestor of new `main`; reconciled via fresh branch + `--no-ff` merge, exact 3-file scope preserved |

Per the AWARD's scope ("Stop on conflict, unexpected path, material drift, or nonzero gate"), the autodocs drift was investigated, found disjoint and nonmaterial (matching the identical pattern already handled twice this session for `0044-17`), and reconciled without stopping for a fresh AWARD.

## Scope (independently confirmed via `git diff --stat`)

- **agent-inbox**, full candidate vs `main`: 9 files exactly as declared (`AGENTS.md`, `README.md`, `agent_inbox_mcp.py`, `docs/pipeline/core-rules.md`, `memory_store.py`, `profile_generator.py`, `test_agent_inbox.py`, `test_memory_store.py`, `test_supervisor.py`).
- **agent-inbox**, corrective delta only (`258f18fbb` → `024c3bef5`): exactly `memory_store.py` (+39/−1) and `test_memory_store.py` (+64) — confirmed the other 7 files are **byte-identical** between the original (Seven-reviewed) and corrected candidate.
- **autodocs**, candidate vs implementation baseline `16664ebc8`: exactly 3 files (`TODO-tuvok-...md`, the evidence file, `docs/pipeline/core-rules.md`) — matches the AWARD's declared carried scope exactly.

## C-1 (`F-C12-01`) — merged-read provenance marking: **verified FIXED**

Read the full `memory_store.py` delta and the new `MergedReadProvenanceTest` class (3 methods) in full. `read_memory_text` now renders a merged read as two labelled sections (`### shared baseline (committed and integrated)` / `### branch-local (...NOT yet shared...)`), sourced from `committed_baseline_lines()` reading the shared checkout's `HEAD`. Failure direction is cautious by construction: any resolution failure yields an empty shared-set, so every entry degrades to *branch-local* — it can under-claim shared status, never over-claim it.

Independently reran the new test class: `test_baseline_only_read_is_labelled_shared`, `test_branch_local_entry_is_labelled_and_separated` (asserts both presence **and** section-exclusivity: a shared entry never appears under the branch-local header and vice versa, plus ordering — shared section before branch-local), `test_read_from_shared_checkout_is_unlabelled` (confirms the unmerged read path is unchanged). All three pass. This is exactly the adjacent-case discipline (positive, negative-space, and unchanged-baseline) this session has applied throughout.

## C-2 (`F-C12-02`) — root canary: **verified DISCHARGED BY CONSTRUCTION**

The implementation evidence's discharge argument was independently checked against the code: `resolve_write_workspace()` rejects a workspace resolving to the shared/primary checkout **before** any lock directory, temp file, or memory file is created (confirmed below under fail-closed boundary) — so a canary "observing the root did not change" would be observing a path the resolver never reaches. The two named zero-mutation canaries (`assert_rejected_without_mutation()`'s whole-fixture digest-map equality check used by all twelve negative cases; `test_rendering_touches_no_live_profile_root`'s five-live-root mtime+sha256 snapshot) were located in the test file and confirmed to exist and pass as part of the full suite rerun below. Seven's own C-2 language ("or record that the enumerated rejection... discharges that requirement by construction. One sentence resolves it.") is satisfied by the evidence file's explicit discharge paragraph, independently corroborated by reading the code rather than merely trusting the prose.

## C-3 — activation provenance: **verified RECORDED PLAINLY (not fabricated compliance)**

Read the evidence file's C-3 section and the claim file's "GATE BREACH" and "PROVENANCE REPAIR" sections in full. The disclosure states, without softening: *"Live haltability was not evidenced for the original implementation window"* and, for the corrective wave itself, *"Live haltability was NOT evidenced for this corrective window... This repair does not convert any of the above into compliance."* Independently verified every cited timestamp against the actual commit metadata (not merely trusted from prose):

| Claimed | Verified (`git log -1 --format=%cI`) |
|---|---|
| Corrective product commit `024c3bef5` at `2026-08-28T08:57:34Z` (10:57:34+02:00) | **matches exactly** |
| Corrective evidence commit `671f04db7` at `08:58:17Z` (10:58:17+02:00) | **matches exactly** |
| Self-report claim commit `508312d03` at `08:59:55Z` (10:59:55+02:00) | **matches exactly** |
| Original claim-first commit `a41312db3` at `08:18:51Z` (10:18:51+02:00) | **matches exactly** |

This confirms the self-report is truthful and precisely dated, not a minimized or approximate account: the corrective claim-first REF was genuinely not delivered before the corrective product mutation (58 seconds, not the original mis-timezoned "~hour" figure — itself a further, disclosed self-correction). **This gate-breach question is a dispatcher/authority matter, not a code-correctness one.** Per Tuvok's own claim, it was already handled by jean-luc ("Jean-Luc's binding handling relayed in `agent-inbox:1787907619742-8bfc8926`") — the same jean-luc who is my dispatcher for this AWARD and who, with that handling already on record, proceeded to AWARD me the review of this exact corrected candidate. I record the finding and my independent verification of its truthfulness; I do not re-adjudicate an authority question already resolved by the assigning Project-Lead-acting dispatcher, and no `Acceptance`/activation is stamped by this integration regardless.

## MCP/CLI parity — independently reverified

`agent_inbox_mcp.py`: the memory-append tool schema lists `"required": ["agent", "scope", "fact", "reference", "workspace"]` and the `workspace` field description states "REQUIRED... rejected before any write." `memory_store.py`'s CLI `append` path: `args.workspace is None` raises `MemoryRoutingError` immediately (no `Path.cwd()` fallback), and the argparse `--workspace` argument defaults to `None`, not the CLI's invocation directory. Both entry points converge on the same `resolve_write_workspace()`. Parity holds, confirmed by reading the code directly rather than trusting Seven's or Tuvok's prose.

## Fail-closed mutation boundary — independently reverified

Read `append_memory_entry()` in full: `resolve_write_workspace(workspace)` is called immediately after argument validation, **before** `lock_dir.mkdir(...)`, before any temp file, before any memory file write. The docstring's claim ("every workspace, scope, identifier, and containment check completes before any lock directory, parent directory, temporary file, or memory file is created") matches the actual code order.

## Independent test verification — a genuine false alarm caught and resolved

Reran `python3 -m unittest test_memory_store test_agent_inbox test_supervisor` from my AWARD-specified worktree (`/Users/tobias.anton/devel/agent-inbox/.worktrees/integrate-dec-0044-029-c12-belanna-20260828`): **754 tests, 2 failures** — the expected pre-existing `DashboardTests.test_integration_status_classifies_branches_and_features`, **plus** a second, unexpected failure: `test_profiles_contain_team_specific_escalation_contract` — `13001 not less than 13000`, deterministic across 3 reruns.

This did **not** match Tuvok's claimed `753/754` (exactly one failure). Investigated rather than either trusting the claim or reporting a false regression: `agents.json`'s blob in my worktree is byte-identical to Tuvok's pinned blob (`bc1bea2f5...`), ruling out roster drift. Located the actual mechanism: `profile_generator.py`'s `instructions()` embeds `Path(__file__).resolve().with_name("memory_store.py")` — an **absolute, checkout-path-dependent string** — twice into the size-budgeted generated "leader" profile text. My AWARD-specified worktree path is long (`.worktrees/integrate-dec-0044-029-c12-belanna-20260828`, itself nested under `/Users/tobias.anton/devel/agent-inbox/`); Tuvok's was evidently shorter. Confirmed by direct reproduction: the identical candidate `024c3bef5`, checked out to a short path (`/tmp/b-ai-024`), reproduces exactly Tuvok's claimed **754 tests, 1 failure**, with leader-profile length **12859** chars (vs. 13001 in the long-path worktree) — an 8-fold-longer-path swing of ~142 chars, consistent with two embedded absolute-path occurrences.

**Conclusion:** not a candidate defect, not introduced by the corrective delta (`profile_generator.py` is untouched by it — confirmed above), and not a false claim by Tuvok — a genuine, pre-existing, path-length-dependent test fragility (an unpinned `__file__`-derived absolute path inside a hard-budgeted generated string) that this candidate did not create and is not responsible for fixing. Disclosed here as a real, independently-discovered, non-blocking finding rather than silently worked around.

## Verdict: **PASS** (both repos)

Both C-1 and C-2 are verified genuinely closed by the code, not merely asserted. C-3's honest non-compliance disclosure is verified truthful to the commit record and correctly routed as an authority question already handled by the dispatching Project-Lead-acting jean-luc rather than re-litigated here. MCP/CLI parity and the fail-closed mutation boundary are independently reconfirmed by reading the code. The one test discrepancy found is fully explained as a self-inflicted worktree-path artifact, not a regression. Proceeding to per-repository candidate hygiene (autodocs), root preflight, guarded merge, and postflight, in the order agent-inbox → autodocs (per the AWARD's fail-closed integration-order requirement, recorded here: agent-inbox is the substantive candidate; autodocs carries only the mirrored governance text and evidence, so it is the dependent side of the pair).

## Scope boundaries observed

No live-profile activation, no service restart, no `memory_append` call, no hold release, no Task/Feature Acceptance, no TODO/DONE lifecycle change, no unrelated mutation, no cleanup/deletion, no concealment of the claim-first failures (both original and corrective, both independently reverified above), no external deployment, no scope widening beyond the AWARD's declared paths.
