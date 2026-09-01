# Feature 0019 handoff-scope correction — 20260822T013000Z

This append-only correction addresses Major finding `0019-READINESS-001` in readiness review `f39c75fa1d18fe7e22553fa21e0a88a3286649d8`. Historical handoff packages, their checksum indexes, and validation receipts remain unchanged.

- **Pinned candidate:** `0b884cd7c96ae7edfd19be4d5a0d83cd9d6d1d07`.
- **Pinned comparison baseline:** `b4af9f88834f2872801aa60158158b59317ac500`.
- **Correction:** `candidate-scope.tsv` records the exact `git diff --name-status -M` candidate delta. It includes legitimate merged corrective claim `TODO-worf-martok-0019-11-20260821T220000Z-c7a91d42.md`, alongside every other actual candidate path.
- **Fail-closed behavior:** `validate_handoff_scope.py` compares the complete ordered observed delta with the manifest; an extra, missing, renamed, or reordered entry fails. It does not use a broad directory-prefix allowlist.
- **Authority boundary:** evidence-only repair by an unprivileged implementer. It adds no acceptance record, passes no checkpoint, changes no candidate/export behavior, and does not authorize integration, publication, push, SSH/configuration/key action, `DONE.md` change, or `0019-10` work.
- **Validation receipt:** `validation.txt` records a successful local run of the validator against the pinned candidate; `SHA256SUMS.txt` binds it with the manifest, validator, README, and user-prompt provenance.
