# `0011-03` Automotive SPICE claim reconciliation — preparation packet

**Status:** Implementer preparation for the cross-item scope decision and
independent Architect review. This is not a decision record, Architect review,
assessment, capability rating, Task Acceptance, integration verdict, waiver or
risk acceptance. No Feature `0019` contract or claim gate is changed by this
packet.

## 1. Identity, baseline and authority boundary

- Task: `0011-03`; Implementer: `tasha`, Security Engineer, `unprivileged`.
- Owner token: `agent:tasha:0011-03:20260829T043440Z`.
- Current-main product baseline:
  `5b06f31d7f7fbc69649406518773c3b5a72b57c2`.
- Claim commit/candidate preparation baseline:
  `d0f24335cbc141071eb6cdb89c76c6051fda93d8`.
- Prerequisite `0011-01` is `[x]` and reachable from current `main`.
- Approved ECU bounds are `DEC-0020-001`, the 14-process
  `0020-04` applicability matrix, and the `0020-07` assessment method.
- Evidence offered for catalogue/assessment use is governed by
  `DEC-0020-002`: refuse at the named use/freeze points, not at arbitrary Task
  start and not through a repository-wide validator.

The Task requires reconciliation of Feature `0019` acceptance wording. That
can change another work unit's acceptance/closure contract and therefore meets
the canonical `cross-item-blast-radius` predicate. An Implementer cannot
authorize that reach. A conforming decision record and supporting review by a
management-instantiated Architect distinct from Tasha must be reachable before
the qualifying mutation.

## 2. Pinned live-source inventory

Blob IDs at the current-main baseline:

| Source | Blob | Classification |
|---|---|---|
| `TODO.md` | `514dadbd96a226773975e4b259090b87c0efb711` | authoritative backlog and Feature `0019` contract |
| `docs/pipeline/aspice-level1-score-import.md` | `11d40d2b25734abd08e53dd6a8367598ffea9748` | live local campaign-evidence contract |
| `docs/pipeline/aspice-report-evidence-map.md` | `7583121fb95fa0d56cf4a5ce32e232b832cc72a3` | live evidence-map guidance |
| `docs/ASPICE/README.md` | `beea0fa1029c878df75dfd0a5a73237130f2c586` | informative 2026-08-15 survey index |
| `docs/ASPICE/01-assessment-basis-and-scope.md` | `f7e0f529bcde5f0abab7ae6f55dce8fccca364d8` | informative pre-decision survey |
| `docs/ASPICE/02-level-1-requirements.md` | `c6b0b3be22090cc4089fbb70d9a4a31bcbc78333` | PAM-informed requirements survey |
| `docs/ASPICE/02-level-2-requirements.md` | `c7d0050208a7837833f0324015e89f02b0f0ca14` | PAM-informed requirements survey |
| `docs/ASPICE/03-current-state-assessment.md` | `3e950c0208b26fd403daf9093f6f5cbf58d7c2b1` | dated readiness observation, not rating |
| `docs/ASPICE/04-gap-roadmap.md` | `1345f120b4d7c479678a02d1f1141e3050130617` | informative roadmap |
| `docs/ASPICE/05-evidence-register.md` | `ffbff9ece073da0085eb627239176269246d2c17` | informative evidence inventory |

Historical decision, requirements, review, acceptance and claim records are
evidence and will not be rewritten to make the current story cleaner.

## 3. Observed findings

### `F-0011-03-01` — No affirmative ECU capability rating was found

The live sources consistently say that capability belongs to a named process,
requires an approved process instance and assessment, and is not established
by templates, tools, documentation execution or a repository as a whole.
Feature `0019` already says it makes no ECU or Automotive SPICE capability
claim. This is a protective baseline to preserve, not evidence that a rating
exists.

Disposition candidate: retain the prohibition, but do not represent its mere
presence as an assessment control or as proof of compliance.

### `F-0011-03-02` — Open Task is cited as if it already established wording

`docs/pipeline/aspice-report-evidence-map.md` says its wording constraints were
"established by `0011-03`" although the authoritative Task is open on current
`main`. It also calls a future assessment an `0011-03` scope even though this
Task reconciles claims and does not perform the process assessment.

Smallest correction candidate: credit the current Feature `0020`/`0025`
assessment boundary and describe `0011-03` as the reconciliation owner until
its own committed result exists.

### `F-0011-03-03` — “Map later” is ambiguous about achievement

Feature `0019` and its local campaign contract correctly classify artifacts as
`documentation-execution`, but say the evidence may later map to named
documentation-process outcomes. Without a sharp qualifier, readers can confuse
"candidate evidence association" with "outcome achieved" or a capability
rating.

Smallest correction candidate: permit a trace from each artifact/control to a
candidate named-process outcome category only. Require the trace to name the
documentation product/project/process instance, origin, baseline, limitation
and contrary evidence. State that an authorized assessment alone judges
outcome achievement and `N/P/L/F`; no mapping self-rates.

### `F-0011-03-04` — Dated survey language can be mistaken for current scope

The `docs/ASPICE/` set is explicitly a 2026-08-15 internal readiness survey,
but portions still say the ECU product/profile decisions are open. Current
authority now includes `DEC-0020-001`, the 14-process profile and the
`0020-07` method. Rewriting the historical observations would falsify their
baseline; leaving them without a current overlay can mislead readers.

Smallest correction candidate: add one concise current-authority overlay in
the survey index pointing to the later decisions and stating that dated
observations remain historical. Do not rewrite every historical paragraph.

### `F-0011-03-05` — Alias provenance is present and must remain

`TODO.md` records that active S-Core Feature `0019` was renumbered from the
conflicting active ID `0010`; historical `0010` remains Performance Package 2
in `DONE.md`. `docs/ASPICE/03-current-state-assessment.md` repeats the
provenance. No correction is needed. Both references are protected from
removal or reinterpretation.

### `F-0011-03-06` — Neighboring CL2 rule conflict is not silently owned here

Live sources do not state one completely consistent CL2 threshold: the survey
states `PA 1.1 = F` plus `PA 2.1`/`PA 2.2 = L or F`, while the `0011-02` Task
and its current scaffolding use `PA 1.1 >= L`. This is material to capability
wording, but `0011-02` is a separate terminal work product and its historical
contract cannot be silently repaired under `0011-03`.

Disposition candidate: record a blocking reconciliation finding for the owner
of the CL2 method before any CL2 claim; do not assign or accept a CL2 result in
this Task. The `0011-03` wording must be conservative enough that the conflict
cannot create a rating.

## 4. Proposed named-process association boundary

The following are **candidate evidence associations**, not assertions that a
PAM outcome is achieved and not ratings:

| Feature `0019` local control/evidence | Candidate named-process association | Required limitation |
|---|---|---|
| campaign scope, plan and status | `MAN.3`-adjacent | Documentation campaign instance only; no ECU project-performance claim |
| release-pinned source/configuration inventory and versioned records | `SUP.8`-adjacent | Configuration evidence for the documentation campaign only |
| structural validation, curator review and finding disposition | `SUP.1`-adjacent | Review/validation evidence is not automatically independent QA or content correctness |
| persisted problems/exceptions and closure links | `SUP.9`-adjacent | Only when a real problem lifecycle, cause/correction/verification and closure are present |
| controlled change/curation decisions | `SUP.10`-adjacent | Request, decision and apply remain distinct; no bare queue state proves outcome achievement |
| authorized documentation publication package and close report | `SPL.2`-adjacent | Documentation release only; not ECU software/product release evidence |

This association set is deliberately narrow. Import extraction is not relabeled
as ECU `SWE.*`; public S-Core/AUTOSAR content is not the assessed unit's
requirements; and a Git commit, generated page or passing validator does not
become an assessment decision.

## 5. Cross-item scope proposal for decision/review

### Affected work units

- `task:0011-03` — owns the claim-language reconciliation;
- `feature:0019` and `task:0019-10` — campaign acceptance/closure wording;
- `task:0011-06` — later process-by-process coverage baseline;
- `feature:0025` — the authorized Level-1 assessment/rating path;
- `feature:0018` — later CL2 assessment/closure path;
- `task:0043-06` work product — report evidence-map attribution.

### Affected gates

- `closure:0019-documentation-campaign-evidence`;
- `validation:0011-06-evidence-coverage-language`;
- `assessment:0025-named-process-pa1.1`;
- `assessment:0018-named-process-cl2`.

### Recommended decision

Select a **documentation-only, no-new-gate** reconciliation:

1. preserve Feature `0019`'s five local campaign-evidence conditions and its
   `documentation-execution` origin;
2. allow only the candidate associations in section 4, with exact instance and
   limitation labels;
3. reserve outcome achievement and capability rating to the authorized
   assessment paths;
4. correct false/open-Task attribution and add one dated-survey overlay;
5. add no TODO prerequisite, no default/shared validator, no publication
   blocker and no automatic claim scanner.

Rejected alternatives for the reviewer to confirm or supersede:

- treating Feature `0019` evidence as achieved ECU or documentation-process
  outcomes without an assessment;
- creating a repository-wide lexical gate that blocks unrelated work based on
  words such as “CL1”, “capability” or “ASPICE”;
- rewriting dated survey or append-only decision/review history;
- resolving the separate `0011-02` CL2 method conflict without its exact
  authority, baseline and owner.

## 6. Negative cases required after scope authorization

The eventual candidate should be falsified against at least these cases:

1. “Feature `0019` proves `SUP.8` CL1” must be rejected as an unsupported
   outcome/rating inference.
2. A Feature `0019` artifact lacking the exact documentation campaign instance,
   baseline or origin must not be associated as assessment evidence.
3. A candidate association must not satisfy an ECU `SWE.*`, `SPL.2`, `SUP.*` or
   `MAN.*` execution obligation.
4. The `0010` -> `0019` alias must remain discoverable in both current backlog
   and dated survey provenance.
5. Historical text must remain visibly dated rather than being rewritten as if
   the 2026-08-15 survey observed later decisions.
6. A report/evidence map must not claim `0011-03` completion before its real
   substantive REF exists.

## 7. Requested independent review

A Team Enterprise Project Lead should instantiate Architect `data` (or record
another management-instantiated Architect) to:

- decide or sponsor the required `decision-record@v1` allocation on current
  `main`;
- test the affected units/gates and the no-new-gate recommendation;
- confirm whether the association set is complete but no broader than needed;
- confirm the historical-survey overlay and `0010` -> `0019` preservation;
- return `scope-ready-for-mutation`, required narrowing, or a stop.

Until that record and review are reachable, this Implementer remains stopped
before the qualifying Feature `0019`/claim-policy mutation.

## 8. Authorized implementation result

Management selected option A in
`decision-1787978346367-bf78a92f`. `DEC-0011-001` and Data's independent
Architect review were integrated on `main` at
`6dde37575f0fd3816c91b498d8aa7b0a17fad69e` before the first qualifying
mutation. The implementation baseline carries that commit through merge
`b152bccb8b`.

The applied reconciliation:

- defines the six closed candidate association categories and the mandatory
  documentation instance/origin/baseline/limitation/validity/contrary-evidence
  context in `aspice-level1-score-import.md`;
- replaces unsupported `SWE.6`-adjacent report-map labels with bounded
  `SUP.1`/`SUP.9` candidate associations and assigns future ratings only to the
  authorized Feature `0025`/`0018` assessment paths;
- adds one current-authority overlay to the dated survey index without
  rewriting its historical bodies;
- preserves the `0010` to `0019` alias and completed historical `0010`;
- updates only Feature `0019` goal/scope and `0019-10` wording needed to remove
  the stale “map later through 0011-03” contract; and
- leaves the separate `0011-02` CL2 threshold conflict unresolved and unusable
  as a rating basis.

No prerequisite, shared/default validator, lexical scanner, publication
blocker, automatic rating, new gate, assessment, capability result, Task
Acceptance, or Feature closure is created.
