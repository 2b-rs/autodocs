# Governance Update Proposal for 0037-46.02 (To be integrated on `main` by Integrator)

- **Target Files on `main`**: `SANDBOX.md`, `AGENTS.md`
- **Associated Task**: `0037-46.02`
- **Protocol Epoch**: `runner-queue@v1` / `runner-request@v1`
- **Reference**: `DEC-0044-012` (Governance files live strictly on `main`)

---

## 1. Proposed Additions / Modifications for `SANDBOX.md`

### Section: Runner Protocol & Queue Operations
```markdown
### 4. Runner Protocol & Execution Model (`runner-queue@v1`)

- **Execution Model**: The runner host operates in multi-worker continuous mode, accepting asynchronous drafts and processing ready queue requests under `.runner/`.
- **Publication Workflow**:
  1. Sandboxed agents compose request drafts under `.runner/drafts/<agent>/<request_id>/` with `manifest.json` and `request.json`.
  2. Atomically publish drafts to `.runner/requests/<request_id>` using a single same-filesystem rename.
  3. Execution results are published under `.runner/results/<request_id>.result.json` with distinct SHA-256 digests.
- **Scope Isolation & Collision Guard**:
  - Concurrent requests with disjoint `write_scopes` are processed in parallel.
  - Concurrent requests with overlapping `write_scopes` are rejected with `RD-SCOPE-COLLISION`.
  - Unprivileged attempts to mutate governance documents (`AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `CLAUDE.md`, `docs/pipeline/`) are rejected with `RD-GOVERNANCE-SCOPE`.
- **Slot Management**:
  - Direct writes to legacy execution slots (`run.sh`) are rejected once legacy-singleton submission is closed.
```

---

## 2. Proposed Additions / Modifications for `AGENTS.md`

### Section: Sandboxed Agent Tooling & Queue Interaction
```markdown
### Queue-Based Tool Dispatch (`runner-queue@v1`)

Sandboxed agents interact with the repository runner using non-execution file operations:
- Use standard file write tools (`write_file`) to stage requests in `.runner/drafts/<agent>/<request_id>/`.
- Use filesystem rename (`os.rename` or equivalent helper) to atomically move drafts to `.runner/requests/<request_id>`.
- Monitor `.runner/results/<request_id>.result.json` for execution verdicts and outputs.
- Observe lease expirations and idempotence keys; retries of prior rejected/failed requests automatically maintain ancestry records (`retry_of`).
```
