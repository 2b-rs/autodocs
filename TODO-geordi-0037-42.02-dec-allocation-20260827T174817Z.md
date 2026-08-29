# Integrator coordination claim — DEC allocation for `0037-42.02`

- **Owner token:** `agent:geordi:0037-42.02-dec-allocation:20260827T174817Z`
- **Capability class:** `privileged`
- **Execution authority:** Current-user Option A release recorded by supervisor in `agent-inbox:1787852610858-53439b5f`; Project Lead boundary notice `agent-inbox:1787852726605-316f67f6`.
- **Baseline:** `main@ce17bbe92d688e8369833cbd8ee451f925951047`
- **Branch/worktree:** `gov-0037-42.02-dec-allocation-geordi-20260827` / `.worktrees/gov-0037-42.02-dec-allocation-geordi-20260827`
- **Write scope:** `docs/dossiers/dec-0037-005-authority-ref-cas.md`; this claim.
- **Scope boundary:** Allocate exactly one new DEC ID for the existing `0037-42.02` Authority-Ref-CAS decision record, serialize it on `main`, and do not alter the frozen `DEC-0009-001` candidate or any other work item.

## Discovery and allocation

- `DEC-0037-003` exists on the frozen off-main governance candidate `1da019f377f622b230ad93aa98bcc7f6d6b421f6`; its record blob is `af21f685fe8ba679e264e82eabd87c5e7cd89e0319cc55337d7d890d4954131a`.
- Current `main` already allocates `DEC-0037-001`, `DEC-0037-002`, and `DEC-0037-004`; `DEC-0037-003` and frozen `DEC-0009-001@e40f7414c` remain unavailable under repository-wide uniqueness. `DEC-0037-005` was free across local branch refs at allocation time.
- `DEC-0037-005` carries the unchanged substantive Authority-Ref-CAS decision text from the frozen `DEC-0037-003` candidate under the newly allocated non-colliding ID. It neither activates a selector nor performs any `0037-42.02` product mutation.

## Validation and next step

- `git diff --check`: passed.
- `python3 _src/tools/process_doc_doctor.py --root . --json`: exit `0`, `ok: true`; 150 documents and 32 findings. Its one error is the pre-existing broken relative link at `docs/dossiers/0044-03-gate-scope-proposal.md:146`; the new record has only the non-blocking DOC005 reachability warning.
- The record body equals `1da019f377f622b230ad93aa98bcc7f6d6b421f6:docs/dossiers/dec-0037-003-authority-ref-cas.md` after the sole `DEC-0037-003` → `DEC-0037-005` allocation substitution.
- Pending: commit this two-path allocation, then run the required root hygiene preflight before any authorized `main` fast-forward. A hygiene finding will be recorded and left unresolved; no foreign state will be changed.

## Supervisor-restart terminal reconciliation — 2026-08-29

**State:** `[x]` terminal historical claim. Allocation `5512f736b0698a72ba82f2ce1279e508da39ea9d`
and integration `719d09794a` are ancestors of current `main`. The original
boundary is concluded; this claim authorizes no additional allocation or root
action. Any successor requires a fresh exact assignment.
