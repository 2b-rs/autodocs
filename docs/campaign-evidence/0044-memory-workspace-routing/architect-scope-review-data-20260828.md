# DEC-0044-029 — bounded Architect scope review

- **Review identity:** Data, Management-instantiated Architect, Team Enterprise
- **Review authority:** Management appointment `agent-inbox:1787900955164-f5d818a8`; main-visible appointment at `8685b9bfd910c629dec21f95f392cf22d2f23d97`; scope-review AWARD `agent-inbox:1787902704512-2b68a101`
- **Decision baseline:** `docs/dossiers/dec-0044-029-memory-workspace-routing.md` at exact `main@8685b9bfd910c629dec21f95f392cf22d2f23d97`
- **Proposal status:** no separate implementation candidate exists. Project Lead confirmation `agent-inbox:1787903115657-5154b906` directs this review to bind the exact current interfaces as the proposed boundary. A later implementation must pin its actual candidate and return for scope review if it deviates or widens.
- **Current external implementation baseline:** `/Users/tobias.anton/devel/agent-inbox@1d75e4573cf1f0cd6768b74d96b902593321322c`; the sole observed worktree difference is unrelated untracked `mouse-jiggler.applescript`
- **Verdict:** `supports-with-conditions`
- **Effect of verdict:** the boundary and conditions below are supported for a later separately assigned implementation. This is not implementation approval, activation, Acceptance, integration review, hold release, or permission to write Memory.

## 1. Exact current-interface pin

The current proposal boundary is the following observed interface chain, not an inferred future code candidate:

| Work unit / path | Exact identity or observation | Current behavior relevant to the review |
| --- | --- | --- |
| `autodocs:docs/dossiers/dec-0044-029-memory-workspace-routing.md` | SHA-256 `426df35d3bee1a4659ac32a63cd24cb5e3a326510413a51d93e485aa0bee663d` at the pinned main | Holds all writes and requires explicit safe-worktree success plus omitted/default/unresolved/shared-root/path-escape rejection before activation. |
| `autodocs:docs/pipeline/core-rules.md` | SHA-256 `af3e1aadcc39a5466cdf22df53c7c20c9dd2a4ba84723b3be92e266f6bc5864c` | Lines 33-52 currently say shared agent/role/capability paths resolve against the common repository root and Feature memory against the active worktree. |
| `autodocs:docs/pipeline/roles/requirements-engineer.md` | SHA-256 `5e6510b0950f995faeac3123774399c082310564c493a7aef5e12dd71c74672e` | Named by the decision as an affected consumer; it contains no current memory-routing rule, so no role-specific change is justified unless the later candidate adds one. |
| `agent-inbox:memory_store.py` | blob `b6acda0e40465905a62a8bf711e498d7727d89d3`, SHA-256 `eee92759c43005460cb3f613bfe47f57b63aa7122b5bca92a3a11d5583f15487` | `roots()` derives common and worktree roots; `scope_path()` selects the common root for agent/role/capability-set writes; CLI `--workspace` defaults to `Path.cwd()`. |
| `agent-inbox:agent_inbox_mcp.py` | blob `5515bf9a3d8747f2480df8c540450366053af28d`, SHA-256 `085da4457bfee457bd498a6dfe45bb8d217918becac3da9caa63eda021763d9b` | `DEFAULT_MEMORY_WORKSPACE` is the shared autodocs root; omitted MCP `workspace` uses it; the `memory_append` schema does not require `workspace`. |
| `agent-inbox:profile_generator.py` | blob `5406cc2467fee128c6f02127c459d7cc44daf949`, SHA-256 `19a61ea64cdcd8f31016a86bbe281d8d24bb441c9cfca1b7ad54ea0a92294f50` | Every generated profile instructs a repository-root read, an append without `workspace`, and a fallback append without `--workspace`. |
| `agent-inbox:agents.json` | blob `bc1bea2f5aae46198725464380608bbedaae743d`, SHA-256 `7fd66c00619d9590ad793aab1500530d8d8c5434c0584b97c3544b3b08fa1801` | Defines four scopes and their repository-relative path templates; 50 agents across five provider profile roots consume the common generator block. |
| current Data profile | `~/.codex/data.config.toml`, SHA-256 `04df544ab2b50fecb5e79d5623fbc902616ef385d4d43ce98e440c7a8391b777` | Materializes the unsafe append omission and repository-root wording from the generator. Other providers show the same generated common block. |
| current tests | `test_memory_store.py` blob `87fc6c57a71ac77c7031bdff051336a4ffdf6a4b`; `test_agent_inbox.py` blob `fa8ce55edae9a600bff757ab62067f2efdde579a`; `test_supervisor.py` blob `d0baa8c7148707f3738e9b0d1a52e16c684ff450` | The store test affirmatively expects linked-worktree shared writes to land in the root; MCP/profile tests do not exercise required workspace or root rejection. |

Observed incident evidence in `TODO-data-0044-memory-hygiene-rereview-20260825T071244Z-29d37e749.md:44-50` confirms the same behavior dynamically: an append called with an item-owned worktree reported and wrote the shared-root path. No production append was called during this review.

## 2. Supported routing contract

The supported contract is intentionally narrower than a new memory-storage architecture:

1. **All append calls require an explicit workspace.** MCP `memory_append.workspace` and CLI append `--workspace` become required. No constant, environment variable, current directory, repository root, or profile placeholder may supply a write default. `memory_read` may retain a read-only default for shared-scope startup reads; it must require an explicit active Feature worktree when Feature memory is requested.
2. **The write workspace is the active item-owned linked worktree.** Canonical Git resolution must prove that the supplied path belongs to a registered linked worktree and that its top-level differs from the common/shared repository root. A symlink, subdirectory, or alternate spelling is canonicalized before the comparison. A primary/root checkout, standalone clone, missing/non-Git/unresolved path, or indeterminate result fails before any directory, lock, temporary file, or memory file is created.
3. **Every scope writes inside that proved worktree.** Agent, role, and capability-set appends target `logs/agent-memory/**` in the active item worktree; Feature appends target `docs/features/{feature}/MEMORY.md` in the active Feature worktree. The current common-root selection in `scope_path()` is removed for writes. Shared-scope changes become common only through ordinary branch commit/integration; mailbox traffic, not dirty root state, remains the immediate coordination channel.
4. **Scope/identifier combinations are closed.** Feature scope requires exactly one valid Feature identifier. Non-Feature scopes reject a Feature argument. Policy templates and identifiers must remain contained below the selected worktree after canonical resolution; path escape and case/prefix lookalikes reject.
5. **The tool is the enforcement boundary.** Profile wording is required guidance but cannot authorize or rescue a rejected target. Successful path validation grants no Task ownership, write-scope expansion, Acceptance, integration, release, waiver, or specialist authority.
6. **No memory content is migrated or cleaned by this package.** Existing root divergence and every committed/uncommitted Memory entry are preserved. Reconciliation, deduplication, cleanup, or historic-carriage work remains separately authorized.

This contract preserves the existing repository-relative paths, locking, bounded entry format, and Feature lifecycle. It changes only how a write base is selected and how shared changes reach the common baseline. A dedicated persistent Memory worktree, a non-Git store, path relocation, or new synchronization service is outside this supported scope and requires a new decision and scope review because it would add lifecycle and cross-item gates.

## 3. Exact later implementation path envelope

The smallest supported source envelope is:

- `agent-inbox/memory_store.py`
- `agent-inbox/agent_inbox_mcp.py`
- `agent-inbox/profile_generator.py`
- `agent-inbox/agents.json` only for a mechanically validated routing-policy field if the implementation needs one; path templates and retention semantics otherwise remain unchanged
- `agent-inbox/test_memory_store.py`
- `agent-inbox/test_agent_inbox.py`
- `agent-inbox/test_supervisor.py`
- `agent-inbox/AGENTS.md`
- `agent-inbox/README.md`
- `agent-inbox/docs/pipeline/core-rules.md`
- `autodocs/docs/pipeline/core-rules.md`
- a later item claim, decision-review provenance, and bounded validation evidence under `autodocs/docs/campaign-evidence/0044-memory-workspace-routing/`
- generated native profiles at the five configured roots (`~/.codex`, `~/.claude/agents`, `~/.gemini/config/agents`, `~/.cursor/agents`, `~/.grok/agents`) as activation outputs, never hand-edited source

The following are excluded absent another decision/authority package: Memory content, `allowed_signers`, signing keys, `.githooks`, supervisor session state, acceptance records, unrelated role guides, Task ownership, checkpoint placement outside Feature 0044, root cleanup, and any external publication.

`supervisor.py`, `agent_keys.py`, and signing-key tests are not part of the routing source envelope by default. Current `supervisor.py generate-profiles` always synchronizes profile-hash-derived keys, appends `allowed_signers`, and installs hooks. Therefore activation **must not** invoke that mutating path under this decision unless a separate authorized security/identity scope permits those effects. The routing package must either provide a reviewed profile-only activation path or obtain that separate authority; neither may be inferred from this verdict.

Any later candidate that changes this path envelope, selects another storage topology, changes read semantics beyond the stated Feature requirement, adds a persistent worktree, touches signing identity, or changes another work unit's gate must return to a distinct Architect scope review before its first qualifying mutation.

## 4. Affected work units, interfaces, and gates

| Kind | Affected unit | Reach and boundary |
| --- | --- | --- |
| Repository | `repository:autodocs` | Root writes can block unrelated validation/integration; supported routing removes that write reach but leaves ordinary branch integration intact. |
| Feature | `feature:0044` | Owns the cross-item routing decision, implementation evidence, affected governance, and integration/closure gates. |
| External source | `external:agent-inbox@1d75e4573c` | Owns the MCP/helper/profile-generation implementation. Its later candidate must be pinned by commit and file digests. |
| Runtime consumers | 50 generated agents across Codex, Claude, Antigravity, Cursor, and Grok roots | All consume the shared memory instruction block. Partial activation can leave old callers dangerous and is prohibited. |
| Memory data | `path:logs/agent-memory/**` | Preserved data; future shared-scope writes occur on item branches and reach main through normal integration. No cleanup or migration here. |
| Feature data | `path:docs/features/{feature}/MEMORY.md` | Remains Feature-worktree-bound and subject to final Acceptance lifecycle. |
| Governance | `path:docs/pipeline/core-rules.md` in autodocs and its agent-inbox source copy | Must stop promising common-root writes and specify active-worktree append routing. |
| Named role consumer | `path:docs/pipeline/roles/requirements-engineer.md` | Inspected and unchanged unless a later candidate introduces a role-specific rule; common generator/core guidance is sufficient and narrower. |
| Interface | `memory_append(workspace, agent, scope, fact, reference, feature?)` and CLI equivalent | Workspace becomes mandatory for writes; rejected inputs create no filesystem mutation. |
| Interface | generated profile `MEMORY GOVERNANCE` block | Must name explicit active-item/Feature worktree append arguments and preserve the hold until activation. |
| Gate | `validation:memory-workspace-routing-fail-closed` | New positive, negative, whole-profile, zero-mutation, and activation checks below are binding. |
| Gate | `integration:0044` | Later source/governance/profile activation evidence crosses the declared Feature integration boundary under ordinary privileged Integrator authority. |
| Gate | `feature-closure:0044` | Cannot close while the hold, activation, profile population, external source, or recovery contract is unverified. |

The cross-item predicate is met because a root append can block another unit's validation or integration and the changed common profile/tool contract reaches every agent. The scope is no broader than necessary because it changes only write-base selection, its common guidance, and tests; it neither redesigns content nor changes unrelated authority.

## 5. Binding conditions

- **C01 — candidate pin:** Before implementation mutation, the Implementer records exact baselines and paths for both repositories and confirms the candidate fits section 3. Drift in any pinned interface is a stop-and-re-review condition.
- **C02 — hold:** `memory_append` and `memory_store.py append` remain unused in every scope until all activation conditions pass. Test doubles may exercise the code only in isolated temporary Git fixtures after the implementation assignment explicitly permits them; production Memory paths remain untouched.
- **C03 — reject before mutation:** All workspace, root, scope, identifier, containment, and policy validation completes before lock-directory creation, parent-directory creation, temp-file creation, or append.
- **C04 — shared writes are branch writes:** Agent/role/capability-set entries land only in the active item worktree and are committed/carried through its ordinary branch lifecycle. The root checkout is never their staging area.
- **C05 — separation:** The Architect, Implementer, Integrator, Acceptance reviewer, and any security/signing authority remain separately assigned as required. This review supplies neither implementation nor acceptance independence.
- **C06 — signing boundary:** No profile activation may rotate/mint keys, mutate `allowed_signers`, or install hooks under this routing authority. Such effects require a separate current authority and affected-unit review.
- **C07 — whole population:** The common generator source and all 50 generated profiles are verified; sampling is insufficient because one stale profile can call an old unsafe form.
- **C08 — tool epoch:** Activation proves every live MCP server/runtime uses the new server version and every resumed/new agent receives the new generated profile. A new profile talking to an old server is specifically prohibited because the old server would still redirect shared writes to root.
- **C09 — no grandfathering:** Old sessions, servers, profiles, CLI forms, environment defaults, and previously accepted work receive no exception. Until their epoch is proved current they remain under the hold.
- **C10 — preserved evidence:** Root Memory divergence and decision/review provenance are neither cleaned nor rewritten. Later reconciliation is a separate item.
- **C11 — governance self-application:** The new server-side rejection applies even when a current/old profile, operator, environment, or helper invocation supplies unsafe guidance. The governance update becomes effective only through the normal main-visible integration path.
- **C12 — re-review:** Any widened path, storage topology, persistent state/worktree, identity-key effect, read-contract change, or new affected gate requires a new supporting Architect review before mutation.

## 6. Required verification design

The later implementation evidence must retain commands, exit codes, fixture paths, path manifests, and before/after digests. At minimum:

1. **Positive linked-worktree matrix:** agent, role, capability-set, and Feature appends with explicit registered linked worktrees write exactly their expected worktree-relative files; root/index bytes remain unchanged. Feature requires the matching identifier.
2. **Negative workspace matrix:** omitted MCP workspace, omitted CLI workspace, empty/defaulted value, root checkout, symlink resolving to root, nonexistent/unresolved path, non-Git directory, standalone clone, and indeterminate Git result each reject with zero writes, zero lock/temp/parent creation, and a stable error class.
3. **Negative scope/path matrix:** missing Feature ID, Feature argument on a non-Feature scope, `..`, absolute, symlink, case/prefix lookalike, and malicious policy-template escapes reject before mutation.
4. **Root canary:** snapshot root index/worktree status and exact `logs/agent-memory/**` digests before and after every positive/negative fixture batch; equality is mandatory. Existing preserved divergence is recorded, not normalized.
5. **Concurrency/recovery:** concurrent appends in one permitted worktree remain serialized and bounded; injected failure before atomic replacement leaves the prior file intact and no orphan temp file.
6. **MCP/CLI parity:** both public entry points enforce the same resolver and errors. Direct calls to `append_memory_entry()` cannot bypass the check.
7. **Whole-profile proof:** deterministic generation asserts all 50 profiles require the explicit active worktree for append, distinguish Feature routing, retain authority limits, and contain no repository-root/default append instruction. Generated-output drift is zero.
8. **Activation dry run:** stage profiles outside live roots, prove exact path population/digests, and prove the chosen installation path does not touch keys, `allowed_signers`, hooks, Memory, mailbox data, or repository root.
9. **Version/epoch canary:** each provider reports the new tool/server contract and profile generation before the hold lifts. One stale provider/session fails the activation gate.
10. **Policy checks:** agent-inbox unit suites for store, MCP, generator/supervisor profile text, and the separately authorized activation path pass; autodocs `process_doc_doctor.py --json`, targeted governance checks, path-scope inspection, and `git diff --check` pass.

These tests are design obligations, not results of this review. No append test was executed here because the operative hold prohibits it.

## 7. Activation, rollback, and recovery

Activation is an ordered gate, not a profile-generation side effect:

1. Keep the hold; integrate the decision and this review to main.
2. Separately assign and implement the exact pinned source envelope in the agent-inbox repository and the matching autodocs governance/evidence package.
3. Run the isolated positive/negative suites and profile-only dry run. Obtain any separately required signing/security authority before touching that boundary.
4. Quiesce append-capable sessions; install/restart the new tool/server epoch first, then install the complete generated profile population. Do not expose new profiles to old servers.
5. Prove every provider/session epoch and root canary. Integrate under the declared `integration:0044` gate.
6. Only then may the registered authority explicitly lift the hold. Main visibility or this verdict alone does not lift it.

Rollback after any later activation is fail-closed: first reinstate the global hold and stop/quiesce append-capable sessions; then disable the new append path, preserve all Memory bytes and evidence, and restore profile/tool versions only while writes remain disabled. Re-run the root canary. Rollback never routes a write to root, deletes a preserved entry, rewrites this decision/review, changes Acceptance, or silently re-enables old sessions. Resume requires the full activation gate again.

## 8. Review conclusion

The proposed boundary is architecturally justified and proportionate **only with C01-C12**. The decisive correction is to make every append an explicit, proved item-worktree mutation and let shared learnings travel through ordinary Git integration, while keeping the tool—not caller convention—as the fail-closed boundary. Current defaults, current generated profiles, current tests, and the generic profile-generation activation path do not satisfy the decision. Therefore the `memory_append` hold remains fully operative, and no implementation or activation may claim support from this review unless it conforms exactly or returns for re-review.
