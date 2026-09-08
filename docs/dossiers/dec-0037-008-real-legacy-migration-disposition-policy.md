### `DEC-0037-008` — Real-run legacy migration finding families: retain provenance, import unverified terminals as OPEN, archive malformed syntax

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-09-03T12:46:17Z`
- **Deciding identity:** `authority:supervisor:management`
- **Role:** `Management`
- **Authority reference:** Current-user/Management Q1–Q5 resolution recorded in Architecture assignment `1788439078629-c2119cbf` (`DEC-0037-008-real-legacy-migration-disposition-policy`); supervisor ACTION `1788439221665-b980e18e`; fleet HARD HOLD `1788436590594-f26d3190`. Recorder is Architect `agent:saru:DEC-0037-008:1788439078629-c2119cbf`. Mail, GUI, and award notices are not themselves this authority.
- **Subject:** Disposition policy for blocking findings from the two fail-closed real shadow-migration watermarks recorded at `51be4db07c26bf48aa1eb00ff8cdbcea8fc81b45`, using the landed importer `f099610c14` (`importer_digest` `c72cfa6d7264f36c79b750f6ab90b0988b49b9ca19b51eff347341c3017a2712`). This record selects the per-family treatment; it does not re-open `DEC-0037-007`'s schema contract and has no production-migration effect.
- **Decision:** Select ALT-01. Against the exact real-run evidence at commit `51be4db07c26bf48aa1eb00ff8cdbcea8fc81b45`, every blocking importer finding receives exactly one finding-bound disposition or a deterministic source-repair mapping. Blanket waivers, source deletion, synthesized `closure.json`, and any closure, Acceptance, ownership, lease, release, or evidence credit are prohibited. The two watermarks are `7eebde81ec61681a37acd9ef667b72e4b537ad9a` (run `real-7eebde81ec-0001`, 910 findings, `import-findings.json` blob `2ab45689d973a85dcd90c8e8269def5b9acde064` SHA-256 `9efcce6fe0487780c31392910f9b9481e3f8879ed48266522514e08015d926fe`) and `2554eac3ea3f4666ab1648fbd6241b38e662d1ac` (run `real-2554eac3ea-0002`, 911 findings, `import-findings.json` blob `2ccf7c9e2c37d16a77e55df5ff545f9e2268a7fe` SHA-256 `00b25df5bdea8e3b680f972bfd60a3fe511727d4f776da846c329077f1b0f5ca`). Observed finding codes and the selected family mapping are:

  1. Q1 `claim-blob-retained` (398 then 399): legacy `TODO-*`/`DONE-*` claim blobs are retained byte-exact as provenance. After cutover they confer no active lease or ownership. Current work authority comes only from the assignment/issue system. Disposition kind: `retain-provenance-no-active-lease`.
  2. Q2 `no-evidence-credit` (8) and `archived-not-accepted` (1): local, no-credit, and archive findings are retained with zero evidence, Acceptance, or closure credit. Disposition kind: `retain-provenance-no-evidence-credit`.
  3. Q3 `unresolved-placeholder` (25) and `closure-evidence-placeholder` (4): pending, local, and placeholder refs are retained verbatim with zero credit and cannot satisfy closure or criteria. Disposition kind: `retain-provenance-no-evidence-credit`.
  4. Q4 `closure-acceptance-missing` (442), `closure-evidence-missing` (16), and `closure-criterion-evidence-missing` (12): any legacy terminal marker lacking current verifiable Acceptance plus typed evidence is imported as OPEN with label/state provenance `legacy-terminal-unverified`, is never closed by this import, and emits no `closure.json`. This removes false completion without fabricating Acceptance. Disposition kind: `import-open-legacy-terminal-unverified`.
  5. Q5 `malformed-feature` (3): malformed headers are parser-independently archived and excluded from active state (`archive-excluded-from-active-migration`). Undefined marker `[~]` (`marker-undefined`, 1, sample `IMP-1739fa8137984953` at `TODO.md:1595`) is preserved and imported OPEN with investigation required, never silently rewritten as complete. Disposition kind: `import-open-undefined-marker-investigate`.

  Each disposition entry MUST bind one finding `id`, `code`/`rule`, locator, work-item identity, exact source commit, and either the source-blob digest or the referenced-field digest; carry a signed canonical per-disposition authority payload; and match only that finding. Missing, duplicate, conflicting, malformed, unsigned, wrong-source, wrong-commit, wrong-digest, and unmatched entries remain blocking. `DEC-0037-007`'s `migration-dispositions@v1` remains the recording mechanism. This decision does not implement the importer, mutate TODO/DONE/claims, advance `main`, activate `issue-store-writable`, or perform production migration.
- **Technical justification:** The real importer runs already classify 910/911 blocking findings and emit no `claim.json`, `closure.json`, or approvals (`approval_emitted`/`claim_json_emitted`/`closure_json_emitted` all false; `blocking` true). Leaving Q4 terminals `[x]`/`[w]` in the issue store would import false completion. Deleting claim blobs or rewriting `[~]` would destroy provenance. Weakening `DEC-0037-007` into a blanket waiver would let unmatched findings through. Binding each finding to one signed disposition at a pinned watermark commit and digest keeps fail-closed coverage while removing false completion. The extra `claim-blob-retained` on watermark `2554eac3ea` versus `7eebde81ec` shows why each run needs its own one-to-one coverage, not a copied waiver list.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
  - `authority-tailoring-or-waiver`
  - `irreversible-or-external-effect`
- **Considered alternatives:**
  - **ALT-01:** Per-family Q1–Q5 mapping with one signed finding-bound disposition or deterministic source-repair per real-run finding
    - **Disposition:** `selected`
    - **Reason:** It retains every source byte, removes false terminal completion, excludes only malformed syntax from active state, and keeps unmatched findings blocking.
  - **ALT-02:** Import every legacy terminal marker as closed because TODO.md/DONE.md already show `[x]`/`[w]`
    - **Disposition:** `rejected`
    - **Reason:** That fabricates Acceptance and `closure.json` for 442+ findings that lack current verifiable Acceptance plus typed evidence.
  - **ALT-03:** Delete or rewrite claim blobs, placeholders, and `[~]` until the importer is green
    - **Disposition:** `rejected`
    - **Reason:** That destroys provenance, conceals the finding, and makes reproduction against the original watermark impossible.
  - **ALT-04:** One blanket waiver covering all 910/911 findings
    - **Disposition:** `rejected`
    - **Reason:** A blanket cannot prove which bytes were reviewed and would suppress later source versions and unrelated rules.
- **Consequences:**
  - **CON-01:** Later implementation must extend `migration-dispositions@v1` (or a successor enumerated kind set) so every real finding code in this record has a kind; the importer/runtime must apply only finding-bound signed payloads and emit deterministic one-to-one coverage for both watermarks.
  - **CON-02:** Importer/schema/runtime changes required: accept kinds `retain-provenance-no-active-lease`, `retain-provenance-no-evidence-credit`, `import-open-legacy-terminal-unverified`, `archive-excluded-from-active-migration`, and `import-open-undefined-marker-investigate`; refuse unsigned, unmatched, or blanket entries; never emit `closure.json` or claim leases from these dispositions; archive malformed feature headers out of active indexes; preserve `[~]` as OPEN investigation.
  - **CON-03:** AE obligations (AE-1 counting/cardinality, identity matching, blocking/gate classification, set coverage): exact baselines are pre-change importer behavior on `51be4db07c` versus a candidate that applies only valid per-finding dispositions. Falsification case: a Q4 terminal imported closed or with `closure.json` MUST be red on this policy and on the current importer (`blocking` true, `closure_json_emitted` false) and green only on a candidate that imports it OPEN `legacy-terminal-unverified`. Adjacent cases: Q1 claim blob retained without lease; Q5 `[~]` not rewritten complete. AE-5: generative or exhaustive property test over finding-id uniqueness, one-to-one coverage of both watermark finding sets (910 and 911), and rejection of blanket/mismatched-digest payloads; name invariant, domain, seed, and executed case count at implementation.
  - **CON-04:** Linked holds and work authority resume only from the assignment/issue system, never from a retained `TODO-*` blob or from this policy record.
  - **CON-05:** Rollback before implementation abandons this candidate branch. Rollback after implementation disables consumption of these kinds while retaining source blobs, run evidence `51be4db07c`, and append-only history; affected findings return to blocking.
  - **CON-06:** Independent scope review of this record is the sibling file under the same award. Implementation, Acceptance, Integrator hygiene/`main` advance, `issue-store-writable` activation, and production migration remain separately assigned.
  - **CON-07:** `agent:saru:DEC-0037-008:1788439078629-c2119cbf` is only the assigned Architect/recorder. `authority:supervisor:management` is the Management decider. Assignment does not transfer that decision authority, grant Acceptance, or authorize cutover effects.
- **Affected work units:**
  - `repository:autodocs`
  - `feature:0037`
  - `task:0037-29`
  - `task:0037-30`
  - `task:0037-31`
  - `subtask:0037-34.02`
  - `path:_src/output/issue-migration/real-7eebde81ec-0001/issues/import-findings.json`
  - `path:_src/output/issue-migration/real-2554eac3ea-0002/issues/import-findings.json`
- **Affected gates:**
  - `integration:0037-29`
  - `task-start:0037-30`
  - `task-start:0037-31`
  - `task-start:0037-34.02`
  - `feature-closure:0037`
- **Review participation:** `none`
- **No-review reason:** Independent Architect scope review is the sibling artifact `docs/dossiers/dec-0037-008-real-legacy-migration-disposition-policy-scope-review.md` produced under the same award by a distinct spawned Architect persona; it is not this Management decision field and does not accept, integrate, or activate cutover.
- **Waiver:** `none`
