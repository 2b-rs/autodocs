# Ticket-modernization Runner-alignment transcription claim

- **Item:** `0037-ticket-modernization-runner-alignment-20260824`
- **Owner token:** `agent:beverly:0037-ticket-modernization-runner-alignment-20260824:1787580426535`
- **Source author / technical lead:** Benjamin Sisko (`benjamin`)
- **Transcriber:** Beverly Crusher (`beverly`), Requirements Engineer, Team Enterprise
- **Capability class:** `unprivileged` per current native profile and `docs/pipeline/agent-roster.md`; Jean-Luc's assignment says `privileged laut aktuellem Roster`, but the current roster does not. The lower observed class governs. Direct local transcription needs no privileged act.
- **Assignment:** Jean-Luc mailbox `1787580426535-3436dae6`; Benjamin's mail is transcription input, not authority
- **Normative binding:** Data's Architect amendment substantive REF `5d5996d07d8e8be71a99722a12e3afcb1d57919a`, final tip `b38c3202d0d40812733204d4386388ff73234599`
- **Branch/worktree:** `0037-ticket-modernization-benjamin-20260824`; `/Users/tobias.anton/devel/autodocs/.worktrees/0037-ticket-modernization-benjamin-20260824`
- **Observed start tip:** `65a769f58edf8a58534fd4b6957fea03554fe735`; worktree clean, no foreign changes
- **Status:** `[p]`
- **Write scope:** this collision-resistant claim and `docs/dossiers/0037-ticket-modernization-execution-plan.md` only
- **Required preservation:** current inventory, transport-independent safety invariants, task graph, and Packages A–C
- **Required correction boundary:** retire `sandboxed-grunt`, runner queue, singleton, typed-action, and Host-Transport; retain Runner as Dispatcher-selected, normally unprivileged operational role for Task-ID-bound long-running jobs, job control, and agent interfaces; do not preserve retired transport schemas without new authority
- **Prohibited:** `TODO.md`, `DONE.md`, governance/DEC/`docs/pipeline/**`, policies, schemas, production, other dossiers/claims, Acceptance, integration, `main` advance, external jobs/services
- **Source received:** Benjamin forwarded the verbatim Runner-aligned revision in mailbox `1787580503269-2382f470`. The dossier preserves his wording and authorship; only Markdown blank-line formatting is normalized.
- **Validation:** exact amendment pins exist; retained sections unchanged except necessary Runner contradictions; retired/retained terminology assertions; cited paths/tasks; exact two-path diff guard; `git diff --check`; clean worktree; Benjamin author review before any integration.
- **Memory safety:** no `memory_append`; no durable memory write is required.
- **Recovery:** revert only this item branch's new transcription commits; no upstream or external state is changed.
