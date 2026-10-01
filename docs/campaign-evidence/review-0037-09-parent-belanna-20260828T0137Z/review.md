# 0037-09 parent — independent first Task-Acceptance review (B'Elanna Torres)

**Reviewer:** `agent:belanna:0037-09-parent-review:20260828T0137Z`, privileged Integrator, Team Voyager
**Dispatcher:** Michael, Discovery Project Lead — OFFER `1787880844940-4e3be293`, ACCEPT
`1787880879067-32084ade`, AWARD `1787881010063-2adb04b0`, thread `0037-09-wave`.
**Review kind:** package-level first Task-Acceptance review of the `0037-09` parent per
`docs/pipeline/task-acceptance.md` and the "when all children are terminal, the parent is the next
eligible package-completion item" rule in `AGENTS.md`. Real package-level work (Kathryn
`1787879332718-d152a26d`), not aggregation-only. No checkpoint marker on this node.

## Independence

Implementer: `tuvok-0037-09-parent-20260828`, unprivileged Programmer, distinct persona from dispatcher
`gabriel`, from `0037-09.04`'s implementers (Pike/Chapel), from AE-5 follow-up implementer
(`tuvok-0037-09-ae5` — a different persona under the same account name, per the claim's own explicit
disclaimer text), and from lander `paul`. I am `belanna` — not the implementer of the parent verification,
the four Subtasks, or their Acceptance reviews (0037-09.01 was reviewed by `paul`, 0037-09.02/.04 by me,
0037-09.03 presumably by another reviewer — none of that is re-litigated here).

## Pins, independently verified (not trusted from the AWARD)

| | Given | Verified |
|---|---|---|
| `main` | `9cd007522` | `9cd0075225c6cf6d06faeef2ee432123c923a1b9` — exact match |
| Candidate tip | `a223de20a` | `a223de20a60000757a7124a330bdbe3cc7e8eede` — exact match, 2 commits ahead of `main` |
| Substantive REF | `80628b802` | ancestor of candidate, confirmed |
| Merge-base | `main` itself | confirmed via `git merge-base` |
| Stale branch `063b9c04eb` | not an ancestor | confirmed via `git merge-base --is-ancestor` — correctly not merged |
| Parent marker | `[x]` L1094, REF `80628b802`, "No `Acceptance: ✓`" | confirmed at `TODO.md:1094` |

## Scope

Product commit `80628b802` touches exactly `TODO-tuvok-0037-09-parent-20260828T031800Z.md` (claim) and
`docs/campaign-evidence/0037-09-parent-tuvok-20260828T0318Z/package-verify.md` (evidence). **Independently
confirmed zero `_src/` changes**: `git diff --stat main 80628b802 -- _src/` is empty. The "no product edit"
claim is not approximate — it is literally true.

## Criteria (`TODO.md:1095–1096`)

**Acceptance criteria:** all validators share `_src/tools/issue_validate.py` diagnostics/config, are
side-effect free, accept explicit authoritative/candidate/staged roots, and cover every rule ID in the
architecture review package without one validator silently weakening another.
**Definition of Done:** all four Subtasks pass the fixed rule-coverage/test profile and `_src/validate.py`
invokes the complete suite; tracked CI is not claimed unless separately introduced.

## Independent verification, one criterion at a time

- **Shared diagnostics/config:** one module (`issue_validate.py`), one `Diagnostic` dataclass, one CLI —
  confirmed directly by reading the module across this and my two prior `0037-09.02`/`0037-09.04` reviews
  this session; nothing here contradicts that.
- **Rule-ID coverage, re-derived from source, not copied from the evidence file:**
  `grep -oE '"IV0[0-9]{3}"' _src/tools/issue_validate.py | sort -u` → `IV0901`–`IV0908`, `IV0910`–`IV0944`,
  **no `IV0909`** — matches the claim exactly. `IV0900` is real but a different *kind* of code
  (`ConfigurationError` f-string prefix, e.g. `"IV0900: candidate root does not exist"`), not a `Diagnostic`
  rule literal — confirmed by direct grep of the unquoted usages; the evidence's "IV0900–IV0908 are
  configuration/limit/duplicate/self-edge codes" phrasing is accurate to this distinction.
- **Side-effect free / explicit roots:** already independently verified in my `0037-09.04` first-review
  (`6dc2b6819`) via the mutation-guard test and the `--root`/`--authoritative-root`/`--source`/`--issue-*`
  flags; this candidate makes no product change, so that finding stands unchanged.
- **No silent weakening:** `test_existing_structural_and_lifecycle_rules_are_unchanged` (line 663) and
  `test_existing_structural_lifecycle_and_provenance_rules_hold` (line 1300) both exist in
  `_src/tests/test_issue_validate.py`, independently located by `grep`, not taken on faith from the
  evidence's prose.
- **`_src/validate.py` invokes the complete suite — the flagged open question, resolved by execution, not
  inspection alone.** The implementer's venv lacked `lxml` (`_src/validate.py` does
  `from lxml import html as LH` at module scope, so the *whole module* fails to import without it — confirmed
  this is a real, unavoidable blocker in their environment, not a shortcut). I have a venv from earlier this
  session (`/private/tmp/autodocs-0019-13-belanna-venv`) with `lxml` 6.1.2 already installed. Used it to:
  1. **Import `_src/validate.py` successfully** (the implementer could not).
  2. **Read the real `CHECKS` list**: an explicit ordered `(name, callable)` sequence;
     `check_issue_store` is present at index 1 (second check, right after `check_automation_safety`),
     confirmed by iterating `V.CHECKS` in a live Python session, not by grepping source text.
  3. **Actually executed `check_issue_store`** through the real `run_checks([...])` wiring path (not a
     synthetic call) against the live current repo: completed in 0.50s, **0 problems, 0 structured
     findings** — consistent with my earlier `0037-09.04` finding that the current `issues/` tree has no
     populated content yet (only `_policy`/`_schema` scaffolding).

  This closes the exact gap the implementer flagged and Michael asked me to verify by execution: the wiring
  is genuine, correctly ordered, and functionally correct — not merely present in source text.
- **All four Subtasks pass the fixed test profile:** reran the full suite together in this exact worktree —
  `_src/tests/test_issue_validate.py` + `_src/tests/test_issue_validate_dag_ae5.py` = **63/63 passed**
  (58 + 5, matching the two files' independently-known counts from my own `0037-09.02` and `0037-09.04`
  reviews this session).
- **Tracked CI not claimed:** confirmed — no CI config file touched, no such claim made anywhere in the
  product commit or evidence.

## Further independent validation

- `python3 -m py_compile` on all four relevant files — OK.
- `git diff --check` on the full product range — clean.
- Scoped `automation_safety.py --path issue_validate.py --path validate.py --path test_issue_validate.py
  --path test_issue_validate_dag_ae5.py --json` → **verdict PASS, 0 findings** — reproduced exactly.
- Repo-wide `automation_safety.py` claim (82 findings / 40 policy errors, "pre-existing global, not
  introduced here"): **not re-run fresh in this review** (a full repo-wide scan takes several minutes and
  this candidate touches zero `_src/`/policy files, so it cannot have changed that number) — but I have
  first-hand, same-session knowledge of this exact figure: I personally implemented `DEC-0038-007`'s
  `proven-closed` disposition kind earlier tonight (`docs/campaign-evidence/automation-safety-proven-closed-impl-belanna-20260827T2251Z/`)
  and left the policy file at exactly 40 remaining policy errors (20 genuinely-still-open entries × 2 checks
  each) after migrating 13 genuine ones. That is the same number cited here, and nothing in this candidate
  touches `automation_safety_policy.json`. Corroboration by recent first-hand knowledge, disclosed as such
  rather than presented as a fresh independent run.

## Scope boundaries observed

No candidate/product repair. No mutation of `refs/heads/main`. No Feature `0037` `DONE.md` move. No touch of
`0037-16`, `0037-28`, `0039-01`, `0019`. No restamp of `0037-09.01`–`.04`. No mutation of `tuvok`'s worktree
(`.worktrees/0037-09-tuvok-parent-20260828T0318Z`, never entered). No spawning. No `Acceptance: ✓` written
anywhere — per the AWARD's explicit instruction, that remains a separately authorized act.

## Verdict

**ACCEPTED.** Every acceptance criterion and Definition-of-Done item is independently satisfied: shared
diagnostics/config, side-effect freedom, explicit roots, complete and correctly-bounded rule-ID coverage
(re-derived from source), no silent weakening (both named regression tests present and passing), and —
resolved by actually executing the code rather than trusting source inspection — `_src/validate.py`
genuinely and correctly wires the complete issue-validation suite into its ordered `CHECKS` sequence. The
implementer's one open question (unable to prove the `validate.py` wiring in their own `lxml`-less venv) is
closed here, not left as a residual doubt.
