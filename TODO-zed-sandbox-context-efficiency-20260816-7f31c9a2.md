# Temporary coordination claim — Sandboxed-agent context and token efficiency

request_id: sandbox-context-discovery-20260816-7f31c9a2
owner_token: agent:zed:user-directed-sandbox-context-efficiency:20260816-7f31c9a2
base_commit: unavailable — `.git` is editor-excluded and execution/run.sh are prohibited for this session
capability_class: sandboxed/grunt
state: [p]

## Assignment

User-directed policy/tooling work not represented by a single existing Task. No unrelated `TODO.md` item is marked `[p]`.

## User prompt provenance

Find ways for sandboxed agents to save tokens, use tool calls sparingly, and elimitate Context Overflow. Examples (non-comprehensive):
1. Offload Heavy Lifting to a Deterministic Python Tool (Recommended)
Instead of having the agent manually read, edit, and verify JSON files in conversation context, instruct the agent to search for an existing self-contained script that does the job (e.g., _src/tools/link_verification_evidence.py), and if it doesn't, to craft such a script on the fly. Structurally, that script performs the work, updates / filters / extracts the relevant contents programmatically, runs validation, and prints a concise 10-line summary verdict. Instruct them to use Strict Output Bounding, refine SANDBOX.md Rule 9 if necessary: Enforce that scripts redirect verbose compiler/generator logs to files in output/logs/ and echo only high-level status (pass/fail, exit codes, and counts) to stdout. Avoid bloating the md. files, because instructions also consume context.

run script terminated; it overlapped. Don't use run.sh from now on.

retry the discovery but avoid run.sh entirely

## Intended write scope

- `SANDBOX.md`
- A small reusable stdlib-only bounded-execution helper under `_src/tools/`, only if repository inspection shows no suitable existing helper
- Focused tests for any new helper
- This temporary claim file
- Root `run.sh` only as a one-use runner request envelope
- Task-scoped ephemeral execution logs under `output/logs/`

## Runner scope

1. Fixed read-only discovery: exact HEAD and authority, worktree/index status, active claims, relevant existing tools/patterns, and singleton-slot state; zero source mutation.
2. One coherent implementation/validation/check-in phase after discovery: focused tests, output-bound checks, mutation-scope checks, and a path-limited substantive commit carrying verbatim prompt provenance.
3. Reconcile/delete this temporary claim only after commit evidence is authoritative; claim cleanup/bookkeeping remains separate when required.

## External resources

None. No network, credentials, package installation, external mutation, or privileged-agent dependency.

## Coordination and assumptions

- The foreign `TODO-zed-link-verification-logs-20260816-a91c7e2d.md` claim owns report page models and related evidence-linking work, not this scope; it will remain untouched.
- The active `0037-37` claim owns architecture review-package/policy artifacts, not `SANDBOX.md` or a generic bounded-output helper; it will remain untouched.
- Existing unrelated staged, unstaged, untracked, and active-claim work must be preserved.
- The policy amendment will be concise: prefer deterministic scripts, cap conversation-facing output, retain verbose logs out of Markdown, and avoid duplicating detailed guidance.

## Progress

- 2026-08-16: Read `AGENTS.md`, `SANDBOX.md`, authoritative `TODO.md`, relevant active claims, and `_src/tools/link_verification_evidence.py`. Classified this session as sandboxed/grunt. No existing backlog item or claim with the exact requested scope was found.
- 2026-08-16: Published fixed read-only runner request `sandbox-context-discovery-20260816-7f31c9a2`; the runner terminated it because its scope overlapped another request. No matching archived result exists and root `run.sh` is absent, so no discovery result, validation, Git operation, or commit is claimed.
- 2026-08-16: User explicitly instructed: `run script terminated; it overlapped. Don't use run.sh from now on.` This session will not publish or use `run.sh` again.
- 2026-08-16: Non-execution inspection found no reusable bounded-output helper and confirmed that `_src/tools/link_verification_evidence.py` can replay complete captured stdout/stderr on failure. Left that foreign-claim-owned tool untouched.
- 2026-08-16: Concisely amended `SANDBOX.md` Rule 5 to require deterministic tool-first handling of bulk/repetitive data and Rule 9 to require `output/logs/` redirection, bounded progress/failure excerpts, and a final verdict of at most ten lines.
- 2026-08-16: Retried discovery without `run.sh`, terminal, scripts, Git commands, or any execution. Editor search confirmed root `run.sh` absent; authority remains the legacy `TODO.md`/`DONE.md` plus active claims; this owner token and exact `SANDBOX.md`/bounded-output scope remain unique; and `SANDBOX.md` diagnostics have zero errors/warnings. Direct `.git/HEAD` access was rejected by the editor's global exclusions, so exact HEAD and command-derived index/worktree status remain unavailable. Project diagnostics also report pre-existing diagnostics in foreign-claim-owned `_src/tools/link_verification_evidence.py`; that file remains untouched.

## Next step

Do not publish or use `run.sh`. Non-execution discovery is complete to the editor's capability boundary. The policy edit is editor-diagnostic-clean but remains uncommitted because exact Git base/status and Git operations are unavailable under the current constraints. Preserve this claim and verbatim prompt provenance with the `[p]` work until a separately authorized non-`run.sh` Git/status/check-in capability exists.
