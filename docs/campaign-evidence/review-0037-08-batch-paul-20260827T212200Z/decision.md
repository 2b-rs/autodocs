# Task-Acceptance decision — 0037-08 batch (induce 07+39; named widening 49+51)

- **Reviewer:** paul (Discovery Integrator, privileged)
- **OFFER:** michael `1787865569072-75488504` (paul ACCEPT `1787865848802-c87f5fc3`)
- **HOLD superseded:** `1787865590846-d8edc33d`
- **Feature owner named batch:** kathryn `1787865367689-62983ff2`
- **Named widening (not yet an AWARD):** kathryn `1787865936760-b24fa074` — include 0037-49 and 0037-51 in AWARD write scope; 0037-37 and 0038-15 remain excluded. Forwarded to michael `1787865981845-fcd4ca6f`. **ACCEPT is not the award. No `Acceptance: ✓` written.**
- **Reviewed at:** 2026-08-27T21:28:00Z
- **Baseline:** `main@f3f17f66f5e18177ce779b356a8ff8b0a8399afb`
- **Worktree:** `.worktrees/review-0037-08-batch-paul-20260827T212200Z`
- **Branch:** `review-0037-08-batch-paul-20260827T212200Z`

## Independence

Not Julian (08/39). Not Seven-Icheb (07). Not Seven (49 closer). Not jean-luc (51 implementer). Not data (51 Architect). Not belanna (existing 02/37/38-15 Acceptance). No waiver. 0037-09.03 remains closed at `9e86bd668`; not re-awarded.

## Boundaries (verify-only; not rewritten)

- **0037-02:** heading `Acceptance: ✓` (belanna, 2026-08-25, baseline `91a4b99fb07948cdea4c71d18ada49f4d661ea42`). Ancestor of this baseline. No impact review of 0037-02 product in this assignment.
- **0037-37:** sub-bullet `Acceptance: ✓` (belanna, baseline `927da0690a964249f7ca0b83719601b849be801f`, 0038-30 batch). Ancestor of this baseline.
- **0038-15:** sub-bullet `Acceptance: ✓` (belanna, baseline `f818542c6`, 0038-30 batch). Ancestor of this baseline.

Heading-only scans miss 0037-37 and 0038-15. Same class as the 0037-04 projection lag on 0037-09.03.

## Contract digests (exact `TODO.md` blocks at this baseline)

| Item | SHA-256 | start line |
|---|---|---|
| 0037-49 | `a3b0fe4d4fe17bba78b586d3514f097f2777f31f7a7d271c7b93ea30d9407d9a` | 964 |
| 0037-51 | `7ab75cf84d7ede42b377d964b883c70abc5e7005425b981e0e89148c53fce30a` | 1072 |
| 0037-07 | `d839a20a75a38abff183be7db37b7be3caaeda5cec8e869b197fce71247b8900` | 973 |
| 0037-39 | `bc3ddc976815014915341432439ce7edb3ebf6c82661e15fbf1f7d9eba0ed685` | 1089 |
| 0037-08 | `1df736b7e14eb4352f68d44c749e325aa76b514d9d4b3c7efbb7b7d0dc5229a4` | 1085 |

Work-product key-file set SHA-256: `2e78b29ee63cc940179b6cfdee685ee342caa868be318f0a99d063833d6849dc`.

## Independent validation (this session, this worktree)

### 0037-49

- `python3 _src/tools/manage_approval_readiness.py --check --json` → `all_ok: true`, six checks OK (remote, SSH signing, allowed_signers, authorities.json roles, credential handle, runner-service controls).
- `docs/pipeline/fixtures/0037-49/validate_readiness_fixtures.py` → `PASS: 7 readiness fixtures`.
- REF `9d4815c6b` is an ancestor of the baseline. Owner provisioning commit `e0c969976` likewise.

### 0037-51

- Decision candidate `DEC-0037-002` in `docs/dossiers/dec-0037-future-direct-execution.md` is reachable.
- Independent Architect scope review `docs/dossiers/0037-51-de-sandboxing-scope-review.md` (Architect `agent:data:0037-51:20260824T083513Z`, verdict `scope-supported-with-bounds`) is reachable.
- Integration commit `7a10f50d76e5620f3b7e3c796093c88037bb54bd` and backlog-rewire REF `f3522aaaa80d851f3ba28744b08956a52eb63275` are ancestors of the baseline.
- Node is **not** flagged `Integration review: mandatory`.

### 0037-07

- `git -c gpg.ssh.allowedSignersFile=issues/_policy/allowed_signers verify-commit b4f03bf88c6d8b1adb45f29b10c27974cb8dfdf1` → Good "git" signature for `tobias.anton@accenture.com` with ED25519 key `SHA256:ciGUV68+0uuJGw+HsDQmur/ZO0INAtZbg5M0A+zydl4`.
- That fingerprint equals `issues/_policy/authorities.json` `repository-owner.ssh_fingerprint`.
- `refs/autodocs/approval/0037-07` = `b4f03bf88c6d8b1adb45f29b10c27974cb8dfdf1`.
- `python3 _src/tools/verify_issue_approval_bootstrap.py docs/pipeline/0037-07-approval.json` → structural pass.
- Live `sha256(docs/pipeline/issue-store-review-package.json)` = `bf98dffe33da51c29e8952e7cfe10e0bb172d1d50ddb191282ea5c3330909a5f`, matching `package_digest`. Approval JSON at HEAD matches the approval commit (empty diff).
- Integration REF `2f83441870936cfce1236fa4d549d6eac3afff45` is an ancestor of the baseline. Named branch tip `5b941d1a5aa0acf1aee36a885dac9f8ba2726b1a` likewise.

### 0037-39 and 0037-08

Command: `uv run python -m unittest _src.tests.test_issue_store _src.tests.test_0037_39_toolchain`

Result: **16/16 OK** in 8.179s (CPython 3.9.6 via uv; 10 issue-store + 6 toolchain).

Also: `python3 -m py_compile _src/tools/issue_store.py` PASS; `automation_safety.py --path _src/tools/issue_store.py` verdict PASS, 0 findings; `git diff --check` on product commits `4376be766` and `7dcaf135c` empty.

`issue_store.py` is a side-effect-free reader (no writer), uses `ruamel.yaml`, enforces `MAX_DOCUMENT_BYTES` / `MAX_DEPTH`, path-derived identity, and `IS08xx` rule IDs. Toolchain manifests `tools/toolchain/manifest.json` and `tools/toolchain/check.py` are present.

## Per-item dispositions (work products vs contract)

- **0037-49:** `accepted` vs contract (readiness green; fixtures 7/7; signed single-authority model in live policy).
- **0037-51:** `accepted` vs contract (decision record + distinct Architect review + integration on main).
- **0037-07:** `accepted` vs contract (owner SSH-signed approval ref; bootstrap + digest + fingerprint confirmation independently green; authors did not self-approve).
- **0037-39:** `accepted` vs contract (independent toolchain suite 6/6).
- **0037-08:** `accepted` vs contract (independent issue-store suite 10/10; compile/safety/diff-check green).

None of these nodes is flagged `Integration review: mandatory`.

## Current `Acceptance: ✓`

**Not recorded.** Waiting for michael's explicit AWARD (ACCEPT is not the award). Kathryn named a write-scope widening to 0037-49 and 0037-51; that is not itself an AWARD.

Once an AWARD names 0037-49, 0037-51, 0037-07, 0037-39, and 0037-08 against this baseline, path-limited bookkeeping on `TODO.md` may add `Acceptance: ✓` for each item that still has a current accepted disposition at that moment.

## Overall review record

`inconclusive` for Acceptance credit until AWARD. `accepted` for work-product fitness on the five named items at this baseline.

No `TODO.md` Acceptance bookkeeping. `refs/heads/main` not advanced. Feature 0037 not moved to `DONE.md`. 0037-16 not mutated. 0037-28 not merged. 0039-01 not claimed.
