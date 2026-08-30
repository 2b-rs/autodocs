# Claim: 0039-04 provenance repair — restore missing implementation claim file

- **state:** `[p]` — awarded, executing
- **handover_to:** *(none)*
- **handover_at:** *(none)*
- **Agent:** `doctor` (The Doctor, Requirements Engineer, Team Voyager)
- **owner_token:** `agent:doctor:0039-04-claim-repair:20260830T054121Z`
- **capability_class:** `unprivileged`
- **Branch / worktree:** `0039-04-claim-repair-doctor-20260830T054121Z`, `.worktrees/0039-04-claim-repair-doctor-20260830T054121Z`
- **Base:** `main@4022945cb123d4d619da5dd60527ab3e7bd61428`
- **Award:** priority offer `1788067994279-2a9dcce6`, execution wake `1788068037375-ce446547`;
  dispatcher `tom`, ordinary dispatchable work per `kathryn` (`1788067834941-3e3dd843`)

## 1. Result: the original was FOUND. Nothing is reconstructed.

**The claim file was recovered intact and is restored byte-identically.** No content is invented,
inferred, or reconstructed, and no reconstruction label is required.

| | |
|---|---|
| Recovered from | `/Users/tobias.anton/devel/autodocs.bak/TODO-zed-0039-04-20260817-131714-a3facd2d095e.md` |
| SHA-256 (source == restored) | `5a3a4bb44c14507acc1ef23d4e5c988bf2a2c7269dc8a4db5a7b4862adf0c0f1` |
| Git blob | `8b739336e99dd6f9e5b385ff1b0eddb81b00cb32` |
| Size | 69 lines / 6568 bytes |
| Source mtime | `2026-08-17T16:18:45Z` — **4 minutes before** the substantive commit at `16:22:51` |
| `cmp` source vs restored | identical |

**The source lies outside the repository and was read only.** It was not modified, moved, or removed;
its mtime is unchanged after the copy. `autodocs.bak` is not a Git repository under my control and
nothing there was written.

## 2. Authenticity — proved, not assumed

Four independent checks, the third of which is conclusive:

1. **`owner_token` matches `TODO.md` byte-for-byte:**
   `agent:zed:0039-04:20260817-131714-a3facd2d095e` — identical in the backlog citation and in the
   recovered file.
2. **`base_commit` `7df56ab6686b2b5bc45efc1d99455e4e838530ab` is a real commit and a verified
   ancestor** of the substantive REF `924eeaf59e`.
3. **The dossier digests recorded inside the claim match the bytes actually committed** in
   `924eeaf59e`:
   - DOCX `d4ce3a1d5081ce9422518698607c2054cd798478351fc440e9f1e859f36321d6` — **match**
   - PDF `cde72d962d4ad6c3f814a66a636b9688f40657529faa6aa6eb4b2a8d8af016c4` — **match**

   **This cannot be produced by reconstruction.** The digests were written into the claim at
   `16:18:45Z`, before the commit at `16:22:51Z`, and they reproduce the committed artefacts exactly.
   A fabricated record could not contain them.
4. **The claim's declared write scope matches the files the substantive commit actually touched** —
   `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `TODO.md`, `docs/pipeline/task-acceptance.md`,
   `docs/pipeline/README.md`, the DOCX/PDF dossier, and a provenance receipt under `docs/studies/`.

## 3. How it was lost — measured, not speculated

The substantive commit `924eeaf59e` (2026-08-17, "docs(0039-04): introduce privileged task
acceptance") touched **eleven files and none of them is a claim file.** The claim was never committed
at all — it is absent from every branch, tag, remote ref, reflog-reachable tree, and from the object
database entirely (searched via `git rev-list --all --reflog --objects`).

**This is therefore not a deletion.** The claim's own closing line says it intended to *"finalize this
claim"* after bookkeeping; that step never produced a commit. The work is real and reachable; only its
provenance record never entered the repository.

**Search performed before concluding this**, in order: all refs; the full object database including
reflog-reachable objects; commit history for the exact path and for any `TODO-*0039-04*` variant;
dangling objects; and the filesystem. **The filesystem search is what found it** — nothing in Git ever
held it.

## 4. Scope observed

Restored the claim file verbatim and wrote this claim. **`TODO.md` is untouched** — the `[x]` marker
and the REF are expressly not mine to change. **No Acceptance created, no `DONE.md`, no `main`, no
push, no fabricated provenance.**

The two other 0039-04-related claims found during the search — `TODO-paul-0039-04-20260826T154500Z.md`
(privileged impact review) and `TODO-zed-acceptance-0039-04-0039-05.01-20260819T133129+0200.md`
(privileged acceptance review, recording `review_ref caedf5002` and `bookkeeping_ref 917899a43`) —
**were read as evidence only and are not touched.**
