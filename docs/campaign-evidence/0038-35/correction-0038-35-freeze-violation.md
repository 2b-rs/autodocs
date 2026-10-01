# Correction: 0038-35 Freeze Violation
The accepted PASS verdict on 0038-35 integration review was INVALIDATED.
Worf's commit 4c114df3b hand-edited `TODO.md` to insert the AE-8 block. `TODO.md` is generated from the issue store, and the issue store is currently under a write freeze (0037-40). Manual edits to `TODO.md` are prohibited and non-reproducible (they will be erased on next generation).

**Action Required (Belanna):**
1. Revert/regenerate the `TODO.md` hunk on `main` to remove the manual edit, invalidating the previous PASS on 4c114df3b.
2. Implement Seven's spec for the generator fix: single-source AE-8 in `AGENTS.md`, and extract it at generation time in `_src/tools/issue_lists.py:_header()` (~L115-131). This touches `_src/` which is executable under the freeze, rather than maintaining a second copy in `TODO.md`.
