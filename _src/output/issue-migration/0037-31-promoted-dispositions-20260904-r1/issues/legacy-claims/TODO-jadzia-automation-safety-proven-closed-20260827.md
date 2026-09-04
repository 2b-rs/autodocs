# Claim — Automation Safety: `proven-closed` Disposition Kind

- **item:** `automation-safety-proven-closed`
- **owner_token:** `agent:jadzia:automation-safety-proven-closed:20260827`
- **request_id:** `20260827T232544Z-jadzia`
- **identity/role:** `jadzia`, privileged Architect
- **capability_class:** `privileged`
- **execution_authority:** Read-only drafting of `docs/dossiers/dec-0038-007-automation-safety-proven-closed.md`. No product mutation, implementation of schema changes, or external effects.
- **state:** `[x]`
- **authority:** Kathryn AWARD `agent-inbox:1787864903627-53ee454d`; Management decision `1787854883138-45083376`

## Scope and Execution
I drafted the decision record `dec-0038-007-automation-safety-proven-closed.md` to authorize the new `proven-closed` disposition kind, cleanly addressing the recurrent false positive issue with terminal `owner_task` and `expires_after_task` entries. The decision anchors validity to immutable proof references (`owner_ref`, `evidence_sha256`) rather than live tasks.
Because my read-only runtime environment prevented direct commit or push actions, the text of this claim and the DEC record were transmitted verbatim to the assigned coordinator/Runner for mechanical transcription onto the branch.

## Conclusion
The DEC is complete and returned to Kathryn for transcription and subsequent independent review by Saru.

## Round 1 correction (2026-08-27, kathryn, Project Lead)
`kes` (Runner) provisioned the branch/worktree (`agent-inbox:1787865354712-20e79c54`) but hit a local harness file-write blocker; Kathryn performed both rounds' mechanical transcription and commits in the already-provisioned, item-owned worktree.

Round 1 (`14c6b1791`) was reviewed by `saru` and found `scope-not-supported` (`1787865837650-08fe71f1`): non-conforming DEC ID, an unaddressed `expires_after_task` terminal check plus missing proof-anchor fields, a wrong file citation (`DONE.md:793` instead of `TODO.md:793` — Kathryn's own earlier measurement had the identical error, caught independently by `saru`), and an incomplete blast-radius list.

This round (r2) transcribes jadzia's corrected verbatim text (`agent-inbox:1787866010539-eba8d754`) addressing all four findings, with one non-verbatim addition Kathryn made for traceability: a "Revision history" section at the foot of the DEC record, documenting r1's rejection and r2's fixes append-only. That section was Kathryn's text, not jadzia's, and was flagged as such to both jadzia and saru.

## Round 2 correction (2026-08-27, kathryn, Project Lead)
`saru`'s r2 re-review (`1787866478079-4317d92d`, tip `d896ebd15`, verdict `scope-supported-with-conditions`) closed findings F-02 through F-05 in the authorization text, but raised F-R2-01: `decision-record@v1` is exactly the fields through Waiver, and the Revision-history footer added in r2 parses as extra top-level labels that don't belong in the DEC body. Recommended moving it to claim-only, which is what this section is: the r1/r2 revision history now lives here instead of in the DEC file. r3 (this commit) removes that footer from `docs/dossiers/dec-0038-007-automation-safety-proven-closed.md` — the DEC body itself is otherwise byte-identical to r2's authorization text.

Other conditions from `saru`'s r2 review, carried forward as outstanding (not this claim's scope to close): F-R2-02 (a PART-01 implementation record is required before this can be called review-complete for actual integration into `automation_safety.py`/the policy schema); F-R2-03 (the implementer of that schema/checker change must be distinct from both `jadzia` and `saru`, must not mutate the checker or policy file before this DEC lands on `main`, and must not weaken `POLICY_STALE` or omit `owner_ref` reachability verification).

Revision history:
- r1 (`14c6b1791`): initial candidate. `saru` verdict `scope-not-supported` — F-02 non-conforming ID, F-03 unaddressed `expires_after_task` terminal check and missing proof-anchor fields, F-04 wrong file citation (`DONE.md:793` instead of `TODO.md:793`), F-05 incomplete blast-radius list.
- r2 (`434b72e06`): corrected ID (`DEC-0038-007`, verified unused on `main`), added `owner_ref`/`evidence_sha256`/`proof_summary` anchoring and explicit `expires_after_task` waiver (ALT-03 added to reject the unanchored alternative), corrected citation to `TODO.md:793`, widened affected work units/gates. `saru` verdict `scope-supported-with-conditions` — substance accepted, F-R2-01 footer-placement finding plus F-R2-02/F-R2-03 forward conditions.
- r3 (this commit): removed the Revision-history footer from the DEC body per F-R2-01; DEC body otherwise unchanged from r2.
