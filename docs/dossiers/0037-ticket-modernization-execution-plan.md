# 0037 Ticket Modernization Execution Plan (Final Revision - Runner Aligned)

**Author:** Benjamin (Project Lead)
**Target:** `docs/dossiers/0037-ticket-modernization-execution-plan.md`

## 1. Exact Current Implementation Inventory

- **Store Foundation:** `/issues/` directory structure exists.
- **Schemas (`issues/_schema/`):** 16 completed JSON schemas.
- **Policies (`issues/_policy/`):** 7 completed policy files.
- **Data State:** `TODO.md` is strictly authoritative. `issues/` is the disposable shadow database until authorized cutover.

## 2. Retained Transport-Independent Safety Invariants

- Collision detection.
- Governance write protection.
- Claim CAS and concurrency control.
- Recovery mechanisms.
- Evidence immutability (`task-evidence-pack@v1`).
- Stale-client fencing.
- Cutover audit trails.
- Checkpoint-driven independent Integrator review.

## 3. Task Graph & Critical Path Rewire Proposal

Task `0037-51` will govern the transition to native unprivileged execution and the new Runner semantics.

- **Sandboxed-Grunt and Queue Retirement:** `sandboxed-grunt`, `runner-queue`, `singleton`, `typed-action`, and Host-Transport models are strictly retired.
- **New Runner Role:** The "Runner" role is NOT retired. It remains as an explicitly selectable, normally unprivileged role designated by Dispatchers for Task-ID-bound long-running background jobs, job control, and inter-agent interfaces.

| Task ID | Description | Current Blocker / Prereq | Post-0037-51 Rewire Candidate | Immediately Executable? |
|---------|-------------|--------------------------|-------------------------------|-------------------------|
| `0037-08` | Parser & Normalized Store | `0037-39` (→ `0037-47` → `0037-46`) | Align to unprivileged execution | No (Bounded prep only) |
| `0037-11` | Derived Views | `0037-08` | Native execution | No |
| `0037-12, 22, 23` | Graph Adapter & UI Paths | `0037-11` | Native execution | No |
| `0037-13..16, 29..31` | Migration & Parity | Previous chain | Native execution | No |
| `0037-30/31 → 34.01/32/33 → 34.02 → 35/36` | Cutover Chain | Migration Parity | Native execution | No |
| `0037-40` | Final Post-Cutover Activation | `0037-36` | Native execution | No |

## 4. Immediately Executable Preparation & Bounded Packages

No actual Task implementation from the critical path above is fully unblocked until `0037-51` completes. The following bounded prep packages are authorized immediately:

- **Package A (UI/Projection Prep):** Read-only preparation of the DHTML projection leveraging Data's UI/UX Dossier. Must reconcile strictly with reviewed UI F-J. Can only develop against existing schema fixtures.
- **Package B (Parser Design Prep):** Bounded design preparation for the `0037-08` parser.
- **Package C (0037-51 Arch Prep):** Data must conduct the Architecture Scope Review. Old transport/queue schemas must be retired, while new abstractions for Task-ID-bound Job Control must be formalized in alignment with `5d5996d07d8e8be71a99722a12e3afcb1d57919a`.
