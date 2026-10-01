# Independent integration evidence — `gov-0022-01-decision-main-integration`

- **Integrator:** Geordi La Forge (`geordi`), privileged Integrator.
- **Authority:** atomic priority-offer award `1787917856827-753e4ea7`.
- **Pinned main baseline:** `0e0650e664bae7519db7ed1a26656059c073a65b`.
- **Pinned source tip:** `gov-0022-01-decision-data-20260828@55439d98bc81be7ed19287d851569eb675e70cb4`.
- **Source substantive REF:** `b2d87ae87d6cb6c635b57b29482f4afa0dc8276e`; reconciliation parent `7bf03e6963442b06c6a52f1fc339fe164d2af12c`.
- **Boundary:** five assigned non-operative governance additions, this evidence, and the integration claim only. No `TODO.md`, product, gate, Acceptance, checkpoint, Feature/DONE, cleanup, push, or external action is in scope.

## Independent inspection

- `DEC-0022-001` is absent from the pinned `main` tree; the incoming identifier is unique there.
- The incoming record is structurally `decision-record@v1`: all required identity, authority, decision, justification, trigger, alternative, consequence, affected-unit/gate, review-participation, and waiver fields are present.
- Saru's independent Architect review identifies `agent:saru:0022-01-scope-review:20260828T100338Z`, is distinct from Data, pins the proposal SHA-256 `126774f75bac69f1c5dcc8784bfb4de61c1b55542a57e9d8afc2950b23177080`, and returns `scope-ok-with-conditions`.
- All eight binding conditions are represented: use-time-only `0023-11`; downstream-use/release-only `0024-02`; future-only `0028-01`; no broad start edge; candidate-root-only validator; later A1 before operative mutation; non-passing `not-decided`; and decision allocation/current-baseline authority reach.
- Current `main` contains the required `DEC-0020-002` decision and supporting review blobs unchanged: `da4242a865aede7fa567c0a37ffc740b4ce24d7f` and `1717e89262c557fda6fd5a86094d59f33a8a7351`.
- The five carried paths equal the exact source blobs: decision `f136d9b8b33fd597b7514a4165bb524874fbcbdc`; proposal `f3e359af6fb69b1d80f1c795bec9bd2cf1acd8fa`; brief `953e4868a45534ed2a715832517c7efbdce9d493`; review `012b32dc1148551971319a40d9ef8cd0abac719f`; Data claim `78148731ae2546a34134443c332886730260d796`.

## Validation before guarded merge

- `git diff --cached --check`: PASS.
- `python3 _src/tools/process_doc_doctor.py --root . --json`: exit 0, `ok: true`; `DEC-0022-001` has only its expected pre-activation DOC005 unreferenced-record advisory. The sole error is the pre-existing unrelated `DOC001` at `docs/dossiers/0044-03-gate-scope-proposal.md:146`.
- `python3 _src/tools/check_policy_provenance.py --source-branch gov-0022-01-decision-data-20260828 --target-branch main --repo . --json`: PASS; no findings and merge base `0dda470a9496434f3f0ff89a899e794ccf60df0e`.
- Conditional final gates: exact-candidate hygiene and root preflight immediately before, then root postflight immediately after, the authorized root merge. Any nonzero result stops integration without foreign cleanup.

## Verdict

**Supported for the guarded integration boundary only.** This is not Task Acceptance, a checkpoint verdict, operative activation, or Feature closure.
