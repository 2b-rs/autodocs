# Independent Architect scope review — `DEC-0037-007` legacy migration dispositions

**Verdict:** `REWORK`

**Reviewer:** `agent:saru:0037-29-migration-disposition-scope-review:1788395978297-9c7d8d6c`, privileged Management-instantiated Architect, Team Discovery. Distinct from author Data (`9805fb66e6` author). This is not Acceptance, implementation, integration, production cutover, or Feature `0037` closure.

**Award:** offer `1788395978297-9c7d8d6c` (notice `1788395985785-f343a2d2`, wake `1788396169645-2f192a71`). Mail is not additional authority. Already-awarded 0037 governance review under the cutover HARD HOLD.

**Write scope:** only this artifact. Candidate `docs/dossiers/dec-0037-007-legacy-migration-dispositions.md` was not modified.

---

## 1. Pins and digests

| Input | Ref / digest |
| --- | --- |
| Exact candidate | `9805fb66e6a23d72421adb45bf82690dc214962b` (`docs(0037): decide legacy finding dispositions`) |
| Awarded source baseline | `main@7eebde81ec61681a37acd9ef667b72e4b537ad9a` |
| Observed later `main` at review start | `b0c7fd83fdb6033fd3d79411cbd2244d21fc15bc`. **Not absorbed.** Pin is an ancestor of the candidate. |
| Candidate vs pin | exactly one path: `docs/dossiers/dec-0037-007-legacy-migration-dispositions.md` |
| Candidate file SHA-256 | `68c279f07f7b02af1fd5b2761a933a0dcb82d56f9c28350435f187b502f42076` |
| Architecture assignment (authoring, not this review) | `1788395547064-f0ac8300` winner `data` |

This review does not silent-retarget later `main`.

---

## 2. Awarded review questions vs candidate *content*

Independently remesured the Decision/Consequences text against the award checklist. The **intended contract** is aligned:

| Question | Candidate content | Result |
| --- | --- | --- |
| Cross-item reach | Triggers include `cross-item-blast-radius`; units `0037-29`/`0037-30`/`0037-31`/`0037-34.02`; gates integration/start of those nodes | Named |
| Least scope | Implementation limited to schema/fixtures, importer/runtime validation, coverage reporting, manifests, corresponding tests/docs; no legacy-blob mutation, no completion synthesis, no production effect | Named |
| Source/field digest binding | Every entry binds finding ID, rule, locator, work-item, exact source commit, and blob digest or referenced-field-value digest | Named |
| One-to-one coverage | Deterministic one-to-one coverage report; a disposition matches only the single bound finding | Named |
| Authority authentication | Deciding identity/role, authority reference, decision time, evidence refs, signature or equivalent durable verification | Named |
| Complete claim/source preservation | Source blob not altered or discarded; complete source retained as provenance | Named |
| Zero closure/Acceptance/authority/evidence credit | Explicit zero Task closure, Acceptance, ownership, authority, lease, release, or evidence credit; no fabricated refs/`closure.json`/ownership inference | Named |
| Malformed syntax repair-first | Malformed structural syntax is repair-first; `archive-excluded-from-active-migration` only with explicit archival-safety justification | Named |
| Rollback | Pre-implementation: abandon branch. Post-implementation: disable consumption, retain manifests/blobs/run history, findings return to blocking | Named |
| Schema/runtime parity | Schema and runtime must accept/reject the same records | Named |
| AE-3/4/5 | Requires AE red baseline (unchanged importer blocking), green candidate with valid dispositions/repairs, named finding-family tests, and property tests over missing/duplicate/conflict/verify/mismatch/unmatched/ordering/coverage | Required of later implementation; not claimed as already executed |

**Content of the disposition contract is not the REWORK cause.** Implementation remains separately assigned and still has no production effect from this candidate.

---

## 3. Blocking `decision-record@v1` defects (REWORK)

The file claims `decision-record@v1` and Role `Management`. Independently checked against `docs/pipeline/decision-record.md` section 3. It **does not conform**. A nonconforming record cannot bind the cross-item gate it names.

- **F-1 — Invalid deciding identity.** Value is `Current user`. The grammar forbids display names and “current user”. Required: `agent:…`, `authority:…`, or `legacy-authority:…`.
- **F-2 — Incomplete timestamp.** `Recorded at: 2026-09-03` is a date, not a complete ISO-8601 timestamp with seconds and timezone.
- **F-3 — Invalid trigger token.** `authority-tailoring` is not in the closed set. The required value is `authority-tailoring-or-waiver`.
- **F-4 — Alternatives not in canonical form.** Required `ALT-NN` entries with exactly one `Disposition: selected` and `Reason` subfields. Candidate uses a numbered 1–4 list with selected/rejected inline in the title.
- **F-5 — Consequences not `CON-NN`.** Required contiguous `CON-01`… list IDs. Candidate is one undifferentiated paragraph.
- **F-6 — Heading/identity provenance.** Heading is not `` ### `DEC-0037-007` — <title> ``. Role is `Management` while the authority line and git author are the Architecture assignment/`data`. Independent review cannot treat “Current user” as a recorded Management identity.

Until F-1–F-6 are repaired on a replacement candidate cut from the same pin (or a newly awarded exact pin), this record is **not** a conforming `decision-record@v1` and must not be consumed as gate-opening architecture.

**Do not** implement importer/schema mutation against `9805fb66e6` as-is.

---

## 4. What this review does not do

- Does not rewrite the candidate decision.
- Does not implement `migration-dispositions@v1`, mutate importer/schema, or edit TODO/DONE/claims.
- Does not integrate, accept, advance `main`, produce production effects, or credit closure/evidence.

**Next:** Data (or a newly awarded Architect) produces a schema-conforming replacement of the same four-part disposition contract; then a distinct reviewer re-reviews the exact new candidate. This mailbox does not implement.

---

## 5. Completion

| Field | Value |
| --- | --- |
| Verdict | `REWORK` |
| Candidate | `9805fb66e6a23d72421adb45bf82690dc214962b` |
| Review branch | `review-0037-29-migration-dispositions-20260903` |
| Review path | `docs/dossiers/dec-0037-007-legacy-migration-dispositions-scope-review.md` |

---

## 6. Rereview (R2)

**Reviewer:** Kira Nerys (Architect)
**Target:** Commit 8a752a1f240f95dde87749c448ba6cb0719b580f
**Prior Evidence:** 15d8a332fb

### Verdict
**SUPPORT**

### Findings
1. **F-1 (Identity):** **CLOSED.** Deciding identity is correctly specified as `authority:supervisor`.
2. **F-2 (Timestamp):** **CLOSED.** Recorded at is a valid ISO-8601 timestamp (`2026-09-03T00:48:30Z`).
3. **F-3 (Trigger token):** **CLOSED.** Trigger token is correctly specified as `authority-tailoring-or-waiver`.
4. **F-4 (Alternatives form):** **CLOSED.** Alternatives are in proper `ALT-NN` format with `Disposition` and `Reason` fields.
5. **F-5 (Consequences form):** **CLOSED.** Consequences are properly structured as `CON-01` through `CON-10`.
6. **F-6 (Heading):** **CLOSED.** Heading exactly matches the required structure: `### \`DEC-0037-007\` — Source-bound, fail-closed dispositions for legacy migration findings`.
7. **Substantive Preservation:** Verified. The substantive constraints including exact-source bindings, digest-bound manifest, one-to-one coverage, explicit dispositions, fail-closed verification, rollback semantics, AE requirements, and zero-credit bounds remain completely intact.

### Conclusion
The corrected candidate addresses all prior structural defects while preserving the intended substantive rules. Support is granted.
