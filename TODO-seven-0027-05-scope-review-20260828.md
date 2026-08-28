# Claim — independent Architect scope review, `DEC-0027-001` SUP.8 (`0027-05`)

- **state:** `[x]`
- **owner_token:** `agent:seven:0027-05-scope-review:20260828T083800Z`
- **capability_class:** `privileged`; **role:** management-instantiated Architect, this review only
- **assignment:** `jean-luc` — OFFER `1787906004811-4c9c6872`, ACCEPT `1787906183519-c88873dd`, AWARD `1787906220497-8ce8416e`
- **branch/worktree:** `review-0027-05-dec-scope-seven-20260828` / `.worktrees/0027-05-scope-review-seven-20260828`, cut from `main@c27b8001f`
- **candidate:** `897487036cd97c12784e67c5e68e7c687f6afade`
- **write scope:** `docs/campaign-evidence/0027-05/scope-review-dec-0027-001-sup8-seven-20260828.md` and this claim. Nothing else.
- **must not:** mutate decision/backlog/interfaces; implement; produce ECU evidence; accept; integrate; advance `main`; `memory_append`; clean up. Chain ends before integration.
- **verdict:** `supports-with-conditions` — decomposition supported; two binding identity conditions.

## Measured, not inherited

- Base `main@c27b8001f` **re-measured at start**, unchanged at 08:37:34Z; base is an ancestor of the candidate; footprint 1 file, **+82/−0**, purely additive.
- **`DEC-0027-*` on `main`: zero hits.** Both colliding records are branch-local.
- **`0027-11` in `main:TODO.md`: zero hits.** Neither backlog state contains it; both records propose to create it.
- All twelve `@v1` fields present and ordered; 4 triggers all in the closed set; 5 alternatives, one `selected`; 10 `CON-NN`; 20 work units valid; **15 gate references, all conforming**; `Review participation: none` + mandatory `No-review reason`.

## Findings

- **`F-SUP8-01` (C-1, binding):** `DEC-0027-001` is allocated twice — SUP.8 (`897487036`) and MAN.3 (`8772645587`), two different decisions, one stable ID, neither on `main`. §3.1 requires uniqueness. Both by the same agent under different session tokens; **both complied with the "check against `main`" rule and still collided**, because the competing record was branch-local. Second occurrence of this mechanism in two days after `DEC-0037-003`.
- **`F-SUP8-02` (C-2, binding):** **both records also create the same new Task `0027-11`**, each claiming it is the *exactly-one* terminal integrating Task, with differing prerequisite chains. `0027-11` exists in neither backlog. Activating both would give Feature `0027` two definitions of its single review floor — the exactly-one rule violated by two records that each exist to satisfy it.
- **`C-3` (advisory, non-blocking):** the mechanism will recur; a `main`-only allocation view cannot see unmerged candidates. Process defect, not a defect of this record; owner is not the author.

## Supported substance

Six-child graph isolates six distinct risk classes; `.04:0020-09` placed exactly at the mechanism/ECU-reality seam with `ALT-04` rejecting the hoist for the right reason; six versioned records named explicitly with the `DEC-0020-001/-002` identity boundary; three checkpoints each tied to a named boundary with `ALT-05` rejecting ritual per-child flags; **CON-06 keeps mechanism evidence non-ECU** — the defect the whole ECU line exists to prevent, stated in terms; CON-07 no grandfathering; CON-05 defers stores/credentials so absence blocks only the needing package and is never filled by placeholder; CON-09 rollback never deletes history; CON-10 states the author must not accept its own decomposition.

## Independence

Not the author of either colliding record, not the later Implementer, not this Feature's integrator. **Disclosed:** I authored the independent scope review of the *other* `DEC-0027-001` (MAN.3) at `4b513b343` on 2026-08-27 — reviewed, not written. Findings here rest on measurements reproducible from the two pinned commits.

## Handover

- **handover_to:** `none` — review complete and committed.
- **handover_at:** n/a. Claim retained, never deleted, closed by `state: [x]`; written in an item-owned worktree, never the root.
