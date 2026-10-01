# Independent Architect review — DEC-0044-036 normative process implementation

**Verdict:** `SUPPORT`

**Reviewer:** `agent:saru:decision-lifecycle-dedup-normative-process-review:1788398111138-99d893ec`, privileged Management-instantiated Architect, Team Discovery. Distinct from Implementer `jean-luc` (candidate `39cff21552`) and from Architect `data` (DEC-0044-036 author). Distinct from Architect `kira` (accepted 036 scope SUPPORT rereview). This session's prior DEC-0044-037 landing audit is **not** 036-text review and is **not** this implementation Acceptance. This is not Acceptance, checkpoint review, implementation, integration, Feature closure, or permission to advance `main`.

**Award:** offer `1788398111138-99d893ec` (supervisor ACTION NOW `1788398119354-425a2bc8`; execution wake `1788398259768-40eb5cbc`). Mail is coordination, not additional authority.

**Write scope:** only this artifact. Candidate, `main`, root checkout, TODO/DONE, claims, and cutover refs were not modified.

No `DEC-` identifier is allocated or changed here. DEC-0044-036 is not re-decided.

---

## 1. Pins and digests

| Input | Ref / digest |
| --- | --- |
| Exact implementation candidate (award pin; this review branch parent) | `39cff21552de928fd8ca3013bb269910c08db00c` (`docs(decisions): enforce canonical request lifecycle`, author jean-luc) |
| Candidate parent (must remain exact; not later `main`) | `a49d753be4be3d5b9c72ed8dcba1b3065bf38c32` (`docs(0044): privileged SUPPORT audit for DEC-0044-037 recovery`) |
| Observed `main` at this review | `998dba844591db2aca9f51957de41b236b4b08c4` (`docs(0037): SUPPORT R2 scope rereview (path corrected)`). Matches supervisor "may be `998dba8445`". **Not absorbed.** |
| One-path vs parent `a49d753be4..39cff21552` | **exactly one path:** `docs/pipeline/decision-request-preparation.md` (65 insertions, 90 deletions) |
| Candidate playbook blob | `a3729042a320dc7670fcd62296992d2306bde7fd` SHA-256 `796f582a7fcad75f09b0789e4f18c483892f29f78e8db6367725e8b6f0fdf053` |
| `main` DEC-0044-036 record | `docs/dossiers/dec-0044-036-decision-request-deduplication.md` blob `8656986d6687e7310d2ff58856bee205cd09baac` SHA-256 `b999aae6aa84a71970a3840163b2b2b61baaaabfa9eb3130393c82413443a67a` |
| `main` accepted 036 scope review (kira SUPPORT rereview of `1786fcc9f6`) | `docs/dossiers/dec-0044-036-decision-request-deduplication-scope-review.md` blob `7492baac1aecac22a2602c35adccb46b5bd35ca3` SHA-256 `50e80b778faf4abd7ac78b3e68e69967826f7ab389b1c653f52099050a38572d` |
| Award required write path | `docs/dossiers/dec-0044-036-normative-process-implementation-review.md` (this file) |

This review does **not** silent-retarget a later `main`. Integration remains a separate Integrator act.

---

## 2. Contract the award required this review to verify

Independently remesured on `39cff21552` against `main` DEC-0044-036 and kira's accepted SUPPORT rereview. Inspected **only** the changed `docs/pipeline/decision-request-preparation.md` behavior.

| Required behavior | Result |
| --- | --- |
| Semantic identity fields | **PASS.** §1.1: exact affected `item`, normalized single `question`, `deciding_role`, `paused_action`, mutually exclusive option IDs and meanings, affected work products and processes, and the material evidence that makes the authority choice necessary. Presentation-only wording, mail subjects, GUI grouping, timestamps, and submitter identity are excluded from identity. Matches DEC-0044-036 identity combination. |
| Exact pending reuse | **PASS.** §1.1 item 1 + `REQ-DTP-08`: exact semantic match in `pending` is reused; creating another request is prohibited. |
| Exact resolved reuse | **PASS.** §1.1 item 2: exact semantic match in `resolved` is the answer; preparer records that exact ID and selected option and applies ordinary continuation checks; reopening/recreating is prohibited. |
| Pre-submit durable lookup | **PASS.** §1.1: MUST query with existing `decision_list` and confirm matches with existing `decision_status` before either request-creation operation. |
| Atomic create-or-return | **PASS as service-boundary contract, not a claimed live autodocs tool.** `REQ-DTP-09` and §1.1 closing paragraph require the request service to enforce the same identity at its transaction boundary. Client check-then-create without that guarantee is explicitly nonconforming. This matches DEC-0044-036 Consequences ("atomic create-or-return operation at the durable decision store") and does not invent a new MCP tool name or extra `decision_request` field. |
| Explicit successor/supersession for material change | **PASS.** §1.1 item 3: MUST name exactly one predecessor ID and one of `supersedes`, `narrows`, `widens`, `replaces-question`; permanent preparation record explains the semantic change. Title/submitter/assignment/mail/recommendation alone is not a material change. Predecessor remains a named relation; the playbook does not rewrite prior records. |
| Ambiguity/conflict fail-close | **PASS.** `REQ-DTP-10` + §1.1 item 4: multiple plausible matches, incompatible predecessor chains, or conflicting resolved selections stop creation and continuation until the authorized resolver reconciles durable records. No convenient-record selection or manufactured supersession. |
| Current-user / Supervisor / `mancons` boundaries | **PASS.** §1.2 restates kira-closed 036 finding: current user may exercise authority in own scope; Supervisor assignment coordinates and does not choose/waive/supersede unless a governing record separately grants it; `mancons` may triage and may record a resolution only when an authorized instruction selects an option or exactly one supplied option is uniquely predetermined; must not invent a choice, waiver, supersession, or altered question; uncertainty fails closed to the named deciding role. Lifecycle state never creates authority. |
| Projection non-authority | **PASS.** `REQ-DTP-07` retained; §1.2 last bullet: mail, GUI, submitter identity, assignment, and offer/award are coordination or projections and prove neither authority nor a durable request/resolution/Acceptance/continuation. §5 still requires exact-ID `decision_status`. |
| Removal of accidental duplicate content without weakening existing preparation rules | **PASS with adjacent note.** Deleted former §6 checklist and §7 `0045-00` instructional examples. Remaining `REQ-DTP-01`–`07` and §§2–5 still carry the same MUST-level rules (one question; binary `YES`/`NO` vs one mutually exclusive set; title pattern; option effects and one recommendation; submitter ≠ resolver; exact-ID pending then resolved checks; projections are non-authoritative). The deleted checklist restated those MUSTS; the examples were labeled non-allocating instruction. Scope boundary still forbids adding tool fields or changing the assignment state machine. |

---

## 3. One-path, no invented tool capability, reported validation

**One-path.** `git diff --name-only a49d753be4..39cff21552` lists only `docs/pipeline/decision-request-preparation.md`. Symmetric `main...39cff21552` also lists that single path. No TODO/DONE/claim/cutover/main-touching path is in the candidate.

**No invented tool capability.** Provenance still cites existing `decision_request`, `decision_request_from_preparation`, and `decision_status` at `agent-inbox/main@d4095e64d174f546502b8cf93930084d455b5e35`. §4 mapping table uses only already-enforced request fields. Wave plan / follow-on choices remain in the permanent preparation artifact via `permanent_records`. §6 Scope boundary still states the playbook does not change the minimum number of tool options, add tool fields, choose Management's answer, instantiate an Architect, count a GUI card as a signature, alter assignment transitions, allocate a `DEC-*` identifier, or replace `decision-record.md`. `REQ-DTP-09` is a MUST on the **request service**, matching DEC-0044-036 future-store implementation; it does not claim an autodocs helper already performs create-or-return.

**Reported validation.** The candidate commit message records `Offer-ID: 1788397696388-47fdcde9` and `Base-Ref: a49d753be4be3d5b9c72ed8dcba1b3065bf38c32` and does **not** name an executed command. This change is documentation/process (AE-7 out of scope for adversarial completion evidence). Independent review verification used:

```text
git rev-parse 39cff21552^
# a49d753be4be3d5b9c72ed8dcba1b3065bf38c32
git diff --name-only a49d753be4..39cff21552
# docs/pipeline/decision-request-preparation.md
git rev-parse main
# 998dba844591db2aca9f51957de41b236b4b08c4
```

Absence of an implementer-reported test command is **not** REWORK for this documentation-only one-path playbook when the contract behaviors above are independently remesured. It is also **not** Acceptance.

---

## 4. Adjacent (non-blocking)

1. **Instructional examples removed.** A coordinator who wants the worked `0045-00` examples retained may restore them additively; their deletion does not remove a MUST that is not already in `REQ-DTP-01`–`07` or §§2–5.
2. **`REQ-DTP-09` is not yet a live store guarantee.** The playbook correctly refuses to treat client-only check-then-create as conforming. Store-side create-or-return remains a separate implementation; this review does not certify that the running request service already provides it.
3. **Independence reminder.** Saru previously audited the DEC-0044-037 landing incident, not this playbook. That SUPPORT does not accept this candidate.

---

## 5. What this SUPPORT does and does not do

**Does:** record that candidate `39cff21552` implements the awarded DEC-0044-036 process delta in the named playbook without weakening retained preparation MUSTS, without inventing tool fields, and on a one-path diff from exact parent `a49d753be4`.

**Does not:** accept the Task; integrate; move a Feature to `DONE.md`; advance `main`; modify the playbook; implement store-side create-or-return; waive hygiene/preflight; credit Feature `0037` cutover; or lift the 0037 HARD HOLD.

Coordinator / Integrator next: ordinary review disposition on this dossier; any landing still needs a fresh Integrator hygiene/preflight. Do not treat this file as `Acceptance: ✓`.
