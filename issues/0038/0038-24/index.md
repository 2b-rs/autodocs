---
schema_version: "1.0"
id: "0038-24"
level: "task"
parent: "0038"
state: "open"
visibility: "internal"
prerequisites:
  - "0038-01"
  - "0038-20"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1906"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0038-24:0038-01, 0038-24:0038-20 Create the tracked `runner-host/` source package for the host execution environment. REF: `6f4bf33daf883b58244989f652777a2f941c9769`

## Scope

- **Backlog repair (2026-08-20, Seven, autonomous backlog repair per `AGENTS.md`):** No committed record of Task `0038-24` existed anywhere in project history: not on branch `0038`, not on `main`. A detailed draft of this Task's design/acceptance text was found only inside the live *uncommitted* working-tree edit of the shared main checkout's `TODO.md`, alongside an unrelated uncommitted `_src/tools/runner_transaction.py` change of unknown authorship that this session has never touched and does not rely on. That uncommitted state is not a valid claim or a committed backlog record under `AGENTS.md`; per the user's explicit instruction of 2026-08-20 ("you will take responsibility for all 0038 tasks"), this Task is formally (re)established here on branch `0038` as a fresh Seven-owned entry, reusing the coherent design intent from the observed draft where it survives scrutiny, rather than inheriting an unverifiable prior claim. `0038-20` (typed branch/merge actions in the legacy transaction runner) is now implementation-underway rather than missing, so the original draft's rationale for gating on it as an infrastructure prerequisite is preserved as a PREREQ rather than as a blocking discovery note.
  - **Claim (2026-08-20):** Owned by privileged agent `Seven` pending dispatch of an unprivileged implementer; see `docs/pipeline/process-roles.md` for capability-class boundaries. No foreign claim is overridden — none was ever committed.
  - **Design decision (2026-08-20, carried from the observed draft, re-affirmed by Seven):** The repository tracks host executable *source*, not a live installed runtime. Place the four host binaries in a root-level `runner-host/` package, bind them to a versioned manifest and static policy/qualification material, and document the boundary between tracked source and the externally installed/service runtime without inventing an external deployment path or claiming activation. Sandbox validation may inspect source, manifests, and hermetic fixtures through the runner, but must not fail merely because it cannot execute a host-only binary. Host static policy and later privileged qualification remain mandatory rather than being excluded.
  - **Implementation completion (2026-08-20, `agent:seven-jetrel:0038-24:20260820T175454Z`, dispatched by privileged agent Seven):** `run-loop.sh`, `perplexity-cpu-loop.js`, `perplexity-echo.as`, and `perplexity-loop.applescript` moved from `_src/` to a new root-level `runner-host/` package with a sha256-verified `MANIFEST.json` and an operator `README.md` documenting the tracked-source-vs-installed-runtime boundary and the capability-class basis for excluding host execution from ordinary sandboxed validation (no profile/scan exclusion added; `automation_safety.py` still statically scans `runner-host/run-loop.sh`). A deterministic `git grep`-based inventory across all four basenames (excluding the frozen `_src/tools/orphan-state-diagram/` snapshot copy, `logs/**`, and other sessions' `TODO-*.md` files) found and updated every live consumer: `.gitignore`'s un-ignore exception; `run-loop.sh`'s own absolute-from-root reference to `perplexity-echo.as`; the 3 `_src/tools/automation_safety_policy.json` disposition `path` fields naming the file (mechanical field only — rationale/line/evidence/owner_task left untouched, per the recorded "whichever lands second updates the other's paths" agreement with `0040-10`, which remains responsible for refreshing their already-known-stale line/evidence values); the 1 `_src/tools/chore_tool_inventory_data.json` enumerated-entry path; 2 comments in `_src/tools/spec_upstream.py`; `docs/pipeline/tools.md`, `docs/pipeline/automation-safety.md`, `docs/pipeline/process-roles.md`, `docs/pipeline/worker-clone-provisioning.md`, `docs/ASPICE/05-evidence-register.md`; `issues/_policy/runner-service.json`; and this Feature's own still-open `0041` "Capability constraint (finding I)" requirements text. `0038-10`'s current Acceptance Criteria/Definition of Done was read in full and contains no `_src/run-loop.sh` reference — nothing to update there; its actually-delivered scope was `runner_transaction.py`. Historical evidence (the two `docs/dossiers/re-intake-*` dossiers, other sessions' claim files, `logs/**`, and this TODO.md's own past-tense narrative entries) was deliberately left untouched to avoid falsifying the record of what was observed at the time. Added `_src/README.md` mapping the existing top-level `_src/` categories and recording a deferred clustering plan; no other `_src/` content relocated. **Validation:** `python3 _src/generate.py` (via a throwaway venv with `lxml` installed, absent from the host shell) produced 428 pages cleanly; `python3 -m unittest _src.tests.test_chore_tool_inventory` 26/26 passed (`stale=0`); `python3 _src/tools/chore_tool_inventory.py --check` PASS; `python3 _src/tools/automation_safety.py --json` and the full `python3 _src/validate.py` both reproduce exactly the pre-existing baseline already documented in the `0038-14`-repair note under both this Task and `0040-10`: the same ten `run-loop.sh` findings at the identical source lines (398/495/705/790/796/802/843/847/1070/1224), now at `runner-host/run-loop.sh`, still owned by open Task `0040-10`; the same two pre-existing `provision_worker_clone.sh` findings (Feature `0041`, unowned); and the same 4 `policy_errors` (3 pre-existing `POLICY_STALE` on the three re-pointed dispositions, unchanged in count by this Task's path-only edit, plus one `POLICY_DIVERGENCE` that is an artifact of running the scan pre-commit). No new critical finding or policy error is attributable to this Task. A handful of dead-link findings in `curation-report.html`/`open-reviews.html` point at unrelated missing `_src/logs/validate-review-request-ui/**` sample files and are pre-existing. Substantive commit `6f4bf33daf883b58244989f652777a2f941c9769` on branch `0038-24` (based on Feature branch `0038` at `518786e4d`); branch left at rest, not merged into `0038`/`main` by this unprivileged session. Claim `TODO-seven-jetrel-0038-24-20260820T175454Z.md` travels on branch `0038-24` per `docs/pipeline/branch-workflow.md`.

## Acceptance criteria

- **AC-001** Create a distinct tracked `runner-host/` source package containing the four current host executable sources (`run-loop.sh`, `perplexity-cpu-loop.js`, `perplexity-echo.as`, and `perplexity-loop.applescript`), a versioned digest-bound manifest, and an operator README. Complete a deterministic repository-wide inventory of references before moving, then update every consumer, documentation, policy/disposition, deployment/bootstrap, qualification, and fixture path that consumes the migrated files. The package documentation makes tracked source versus externally installed runtime explicit, names only repository-supported source paths, and states that live host validation/service activation is neither performed nor claimed. Static host policy and privileged qualification remain applicable through manifest/path-bound checks. Ordinary sandboxed Task validation profiles exclude host execution by capability/profile rather than by hiding or omitting the package
- **AC-002** static checks and hermetic fixtures remain runner-executable. Update `0038-10` to consume the migrated host runner path and remove stale `_src/run-loop.sh` references from its contract. Add `_src/README.md` mapping the existing top-level source categories and a deferred clustering plan that preserves stable paths for all non-host `_src` sources
- **AC-003** do not broadly relocate them or create a second authoritative compatibility copy

## Definition of Done

The manifest/README and all four canonical source files are committed under `runner-host/`; no tracked consumer/document/policy/bootstrap/deployment/qualification reference still treats `_src/run-loop.sh` or the other former `_src` host-binary paths as canonical; deterministic reference inventory results and path/digest validation are retained; static policy/qualification coverage names the package; focused hermetic checks pass through the runner; no host binary execution, service activation, external-resource access, credentials, or privileged qualification is claimed; and the implementation plus separate REF bookkeeping commits preserve unrelated work.
