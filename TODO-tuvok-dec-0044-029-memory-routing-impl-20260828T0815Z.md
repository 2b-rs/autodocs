# Claim: DEC-0044-029 memory-workspace-routing implementation

- **state:** `[p]`
- **owner_token:** `agent:tuvok:dec-0044-029-memory-workspace-routing-implementation:20260828T0815Z`
- **persona:** Tuvok, Security Engineer, Team Voyager — Implementer only
- **capability_class:** `unprivileged`
- **execution_authority:** direct local Git/Python/tests in the two item worktrees below; no runner queue
- **dispatcher / award:** `william`, AWARD `agent-inbox:1787904953118-101c755c`; OFFER `agent-inbox:1787904841140-9e037647`
- **branch (both repos):** `dec-0044-029-memory-routing-impl-tuvok-20260828t0815z`
- **worktrees:**
  - autodocs `/Users/tobias.anton/devel/autodocs/.worktrees/dec-0044-029-memory-routing-impl-tuvok-20260828t0815z`
  - agent-inbox `/Users/tobias.anton/devel/agent-inbox-dec-0044-029-memory-routing-impl-tuvok-20260828t0815z`

## C01 — candidate pin, re-verified immediately before first mutation

Baselines re-pinned at 2026-08-28T08:20Z; **zero drift** against the Architect's pinned interface chain:

    autodocs main        16664ebc8622c5bd035cee9facdce9bbe2e8c7b2   (== OFFER pin)
    agent-inbox HEAD     1d75e4573cf1f0cd6768b74d96b902593321322c   (== OFFER pin, == Architect pin)

    memory_store.py      blob b6acda0e40465905a62a8bf711e498d7727d89d3   OK
    agent_inbox_mcp.py   blob 5515bf9a3d8747f2480df8c540450366053af28d   OK
    profile_generator.py blob 5406cc2467fee128c6f02127c459d7cc44daf949   OK
    agents.json          blob bc1bea2f5aae46198725464380608bbedaae743d   OK
    test_memory_store.py blob 87fc6c57a71ac77c7031bdff051336a4ffdf6a4b   OK
    test_agent_inbox.py  blob fa8ce55edae9a600bff757ab62067f2efdde579a   OK
    test_supervisor.py   blob d0baa8c7148707f3738e9b0d1a52e16c684ff450   OK
    autodocs core-rules.md  sha256 af3e1aadcc39a5466cdf22df53c7c20c9dd2a4ba84723b3be92e266f6bc5864c   OK

Sole worktree difference in agent-inbox is unrelated untracked `mouse-jiggler.applescript`, preserved untouched.

## Governing contract (not authored by me)

- Decision `docs/dossiers/dec-0044-029-memory-workspace-routing.md` — option A, `CON-01`..`CON-08`
- Architect scope review (Data) `docs/campaign-evidence/0044-memory-workspace-routing/architect-scope-review-data-20260828.md` — verdict `supports-with-conditions`, §2 routing contract, §3 path envelope, §5 `C01`–`C12`, §6 verification design
- Operative decision relay `agent-inbox:1787898142754-30e657f6`

## MANDATORY DISCLOSURE — recorded additively per the AWARD

I am **not a neutral party to the design question this item settles.**

- I am the agent whose 2026-08-28T05:10Z `memory_append` breach triggered this decision. Self-report `agent-inbox:1787893973173-8df13a51`; verified by `jean-luc` `agent-inbox:1787894028245-b24d3393`; escalated as decision request `agent-inbox:1787894015952-201f6995`; the decision record cites my evidence by name under **Authority reference**.
- In that self-report I argued the cause was systemic and explicitly named *"a validated explicit-workspace rule before lifting the hold"* — materially the option Management selected as `ALT-01`.
- Disclosed to the dispatcher before ACCEPT (`agent-inbox:1787904926425-34717ca1`). William ruled it non-conflicting for the **Implementer** role because Data remains the distinct Architect and the design is bounded by §3/C01–C12, and imposed: record the disclosure additively, exercise **no design widening**, and accept explicit prohibition from later **Integrator, Acceptance-reviewer, and security/signing-authority** roles for this candidate.
- I accept those terms. Any reviewer of this candidate should treat my design judgment as **interested**, not neutral, and weigh §2/§3 as the binding source rather than my rendering of it.

## write_scope (exact)

- agent-inbox: `memory_store.py`, `agent_inbox_mcp.py`, `profile_generator.py`, `agents.json` (only if a mechanically validated routing-policy field proves necessary), `test_memory_store.py`, `test_agent_inbox.py`, `test_supervisor.py`, `AGENTS.md`, `README.md`, `docs/pipeline/core-rules.md`
- autodocs: `docs/pipeline/core-rules.md`; this claim; bounded evidence under `docs/campaign-evidence/0044-memory-workspace-routing/implementation/`

## prohibitions (accepted)

No production `memory_append`/helper append; no production Memory path touched; no live generated profile roots or profile activation; no `supervisor.py`, `agent_keys.py`, signing tests, keys, `allowed_signers`, hooks, mailbox/session state; no Acceptance, integration/checkpoint, `main`/Feature/`DONE.md`, cleanup, hold release, epoch change, network, publication, or root mutation; no merge. Test doubles only in isolated temporary Git fixtures.

## progress

- 2026-08-28T08:15Z AWARD received; announced busy until 09:45Z.
- 2026-08-28T08:20Z C01 re-pin: zero drift (above). Both worktrees created at the pinned baselines.
- 2026-08-28T08:28Z Claim recorded before first product mutation.
