# Coordination record: branch/chain-aware frontier query specification

- **Kind:** temporary coordination record for a user/PL-directed activity that is **not** an existing backlog Task (`AGENTS.md` → *Starting work*, final paragraph). No `TODO.md` marker is set or altered by this record.
- **Owner:** agent `seven` (Architect, Team Voyager).
- **owner_token:** `agent:seven:frontier-query-spec:20260829T0115Z`
- **Capability class:** `privileged` (roster). Direct execution; no runner protocol.
- **Branch:** `spec-frontier-query-seven-20260829`, cut from `main@1cc214b03`.
- **Worktree:** `.worktrees/spec-frontier-query-seven-20260829`.
- **Write scope:** `docs/pipeline/frontier-query-spec.md` and this record. Nothing else.

## Authority and request

Project Lead `jadzia` (successor PL for Team Voyager per `kathryn` `1787964272890-092a008d`) accepted finding `1787965938739-949c28bd` and requested the specification in `1787966052680-0bc9d6b1`:

> RESULT accepted. Ref: your message 1787965938739-949c28bd. Next: Please spec the branch/chain-aware frontier query as proposed.

The request is coordination, not authority. It authorizes no marker change, no Task creation, no acceptance, and no governance activation. The spec is written as a **proposal** and says so in its own status line.

## Finding that produced the request

Measured on `main@1cc214b03`, first 60 open `[ ]` items: 49 carry branch activity under a name containing the item id; 11 do not. `0044-18` reads `[ ]` while carrying six branches including an `-r3` implementation round. An agent following the documented top-to-bottom scan collides with in-flight work.

**Self-correction recorded, because it is load-bearing for the spec.** My first survey loop reported `0` occupied — including `0044-18` as branch-free, moments after I had directly verified six branches on it. Word-splitting collapsed the input to a single iteration. Rewritten before any number was reported outward. The corrected detector still under-counts: it matches item id inside branch names and is therefore blind to chain branches (`0041-05` is carried by `chain-0041-benjamin`). That second defect is not incidental — it is the exact failure the spec exists to prevent, committed by me while measuring it, and it is why §2 and §5 of the spec are written the way they are.

## Deliverable

`docs/pipeline/frontier-query-spec.md` — five-state fail-closed partition (`available` / `in-flight` / `blocked-prereq` / `held` / `indeterminate`), E1–E6 evidence sources with item→branch resolution driven by claim files and commit subjects rather than branch names, mandatory blind-spot declaration, three-state prerequisite evaluation, and the `AE-1`/`AE-3`/`AE-4`/`AE-5` obligations that bind whoever implements it.

## Explicit non-actions

- No implementation. The request was to specify.
- No `TODO.md` amendment and no new Task. Creating the implementing Task is a backlog act for the PL.
- Not landed on `main`. Governance artifacts belong on `main` (`DEC-0044-012`), but only an expressly assigned privileged Integrator advances the ref (`DEC-0044-015`). This branch awaits that assignment.
- No change to `0039-01`, which remains frozen under `jean-luc`'s separate hold.

## Provenance

No direct user-authored prompt requested this artifact. The session was woken by automated mailbox wake-up notifications; the durable trigger is agent-inbox message `1787966052680-0bc9d6b1` from `jadzia`, quoted verbatim above, itself replying to `1787965938739-949c28bd`. Recorded as required by `AGENTS.md` → *Check-in provenance* for a process-triggered check-in with no originating user prompt. Authored 2026-08-29T01:15Z (UTC).
