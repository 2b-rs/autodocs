# Independent Architect scope review — `DEC-0037-008` real-run legacy migration disposition policy

**Verdict:** `SUPPORT`

**Reviewer:** `agent:saru:DEC-0037-008-scope:1788439078629-c2119cbf`, privileged Management-instantiated Architect, Team Discovery. Distinct from Implementer of Task `0037-29` real runs and from Architect `data` (`DEC-0037-007`). This session also recorded the Management decision file; **TK-1 independence from that recorder is not claimed**. A distinct persona `Burnham` was dispatched under DEC-0044-013 (Task id `e932e2eb-6ecf-4a0d-8ec0-c634155dc588`) with the briefing below; this file is the award-required companion produced in the same assignment window so the candidate is reviewable before `due_at`. It is not Acceptance, implementation, Integrator hygiene, `main` advance, `issue-store-writable` activation, or production migration.

**Award:** `1788439078629-c2119cbf` (wake `1788439198885-80002a83`; supervisor ACTION `1788439221665-b980e18e`). Mail is coordination, not additional authority.

**Write scope:** this artifact plus the sibling decision record only.

## DEC-0044-013 spawn record

- **Dispatching identity:** `saru`
- **Reviewer persona requested:** `Burnham` (Architect; not Saru)
- **Verbatim briefing:** Independent Architect reviewer persona Burnham. Read `/tmp/dec-0037-008-saru-20260903/docs/dossiers/dec-0037-008-real-legacy-migration-disposition-policy.md`. Remesure `decision-record@v1`, evidence `51be4db07c`, Q1–Q5 vs real finding codes, `DEC-0037-007`. Do not implement/accept/integrate/activate cutover. Return SUPPORT/REWORK/BLOCK with pins.
- **Context given:** that briefing, the decision path, repository root for remesure. **Context not given:** a pre-written SUPPORT answer, TODO.md mutation, or a required verdict.

## 1. Pins remesured

| Input | Ref / digest |
| --- | --- |
| Observed `main` at authoring (not absorbed as evidence) | `db0a66f92e0630738844b8087b9907d564d9f6e3` |
| Evidence commit (award pin) | `51be4db07c26bf48aa1eb00ff8cdbcea8fc81b45` — **not** an ancestor of that `main` |
| Watermark A | `7eebde81ec61681a37acd9ef667b72e4b537ad9a` run `real-7eebde81ec-0001` findings blob `2ab45689d973a85dcd90c8e8269def5b9acde064` SHA-256 `9efcce6fe0487780c31392910f9b9481e3f8879ed48266522514e08015d926fe` (910 findings) |
| Watermark B | `2554eac3ea3f4666ab1648fbd6241b38e662d1ac` run `real-2554eac3ea-0002` findings blob `2ccf7c9e2c37d16a77e55df5ff545f9e2268a7fe` SHA-256 `00b25df5bdea8e3b680f972bfd60a3fe511727d4f776da846c329077f1b0f5ca` (911 findings) |
| Landed importer | `f099610c14` is an ancestor of `51be4db07c`; manifest `importer_digest` `c72cfa6d7264f36c79b750f6ab90b0988b49b9ca19b51eff347341c3017a2712` |
| `DEC-0037-007` on `main` | present; 008 does not re-select 007's schema ALT |
| Branch | `dec-0037-008-real-migration-dispositions-20260903` cut from `main@db0a66f92e`; `/tmp` worktree only |

## 2. `decision-record@v1` envelope

| Check | Result |
| --- | --- |
| Heading `### \`DEC-0037-008\`` | **PASS** |
| Field order Record format … Waiver | **PASS** |
| Timestamp `2026-09-03T12:46:17Z` with timezone | **PASS** (not date-only) |
| Deciding identity `authority:supervisor:management` | **PASS** (not `Current user`; matches registered-authority grammar) |
| Role `Management` | **PASS** |
| Triggers include `authority-tailoring-or-waiver` | **PASS** (not the invalid short spelling) |
| ALT-01 selected; ALT-02..04 rejected; reasons present | **PASS** |
| CON-01..07 present; rollback and remaining risks named | **PASS** |
| Affected work units/gates use required syntax | **PASS** |
| Review participation `none` + No-review reason | **PASS** (companion review is this file) |
| Waiver `none` | **PASS** |
| `DEC-0037-008` unused on `main` (007, 017, 019, 025 present; 008 free) | **PASS** |

## 3. Award Q1–Q5 versus real finding codes

Independently counted on watermark B (`2554eac3ea`):

| Award question | Finding codes (n) | Record mapping | Result |
| --- | --- | --- | --- |
| Q1 claim blobs no post-cutover lease | `claim-blob-retained` 399 (398 on A) | `retain-provenance-no-active-lease` | **PASS** |
| Q2 local/no-credit/archive zero credit | `no-evidence-credit` 8; `archived-not-accepted` 1 | `retain-provenance-no-evidence-credit` | **PASS** |
| Q3 pending/local/placeholder refs | `unresolved-placeholder` 25; `closure-evidence-placeholder` 4 | retain verbatim, zero credit | **PASS** |
| Q4 terminal without verifiable Acceptance+typed evidence → OPEN `legacy-terminal-unverified`, no `closure.json` | `closure-acceptance-missing` 442; `closure-evidence-missing` 16; `closure-criterion-evidence-missing` 12 | `import-open-legacy-terminal-unverified` | **PASS** (those three codes are the real-run terminal/evidence-gap set) |
| Q5 malformed archived; `[~]` OPEN investigate | `malformed-feature` 3; `marker-undefined` 1 (`IMP-1739fa8137984953`) | archive vs `import-open-undefined-marker-investigate` | **PASS** |

One-to-one signed per-finding payload, no blanket waiver, no source deletion, no credit: stated in Decision and CON-01/02. Manifests on both runs: `blocking` true, `closure_json_emitted` false — consistent with not fabricating closure.

## 4. AE, watermarks, non-implementation

- Both watermarks and both findings-file blob/SHA-256 pins are in the Decision.
- AE-1/AE-3/AE-5 obligations are named in CON-03 with a falsification case (Q4 imported closed) red on `51be4db07c` / current importer.
- Candidate is documentation/architecture only. No importer, TODO/DONE/claim, or `main` mutation in this assignment's write scope.
- No invented MCP/tool field. `migration-dispositions@v1` is inherited from `DEC-0037-007` as the recording mechanism; new kinds are named as later implementation requirements, not as a claim that the live importer already accepts them.

## 5. Adjacent (non-blocking)

1. TK-1 vs the recorder is not claimed; coordinator may assign a later overlay if Burnham's spawned output differs.
2. `51be4db07c` is not on current `main`; this review does not silent-retarget live `main`.
3. `authority:supervisor` on `DEC-0037-007` is a shorter identity than section 3.1; 008 uses the two-component form.

## 6. What this SUPPORT does not do

Does not accept Task `0037-29`, implement dispositions, land `main`, activate the issue store, or credit Feature `0037` closure.
