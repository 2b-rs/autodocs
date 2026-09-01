# Decision records (`decision-record@v1`)

**Status:** Normative for process-relevant decisions in this repository's own development process.

**Requirements basis:** `RQ-DEC-01` … `RQ-DEC-05` from
[`../dossiers/re-intake-evidence-traceability-and-roles.md`](../dossiers/re-intake-evidence-traceability-and-roles.md).

**Scope boundary:** This document defines a Markdown work product and its trigger threshold. It does not implement a validator, grant authority, or replace Task acceptance or an integration verdict.

## 1. Normative terms

The key words **MUST**, **MUST NOT**, **SHOULD**, and **MAY** are normative. A record conforms to `decision-record@v1` only if its fields and subfields occur in the order and cardinality specified by section 3 and satisfy this document's semantic rules.

A decision record captures **who**, under **which authority**, made which process-relevant decision at **what time**, why it was made, which alternatives were considered, and which work units or gates it affects. It is not a retrospective success narrative: it SHOULD be created before the decision is implemented, but no later than before an affected gate is crossed.

## 2. When a record is mandatory

A decision MUST be recorded as `decision-record@v1` as soon as at least one of the following triggers applies. **Triggers** lists every applicable value from this closed set:

The trigger answers **whether a durable record is mandatory**, not **which role
decides**. The deciding role and authority reference still come from the
existing contract and authority model. A trigger therefore does not by itself
create a Management escalation. Technical disagreement first follows the
delegated ladder in [`integration-flow-control.md`](integration-flow-control.md);
only an exact remaining non-delegable question is eligible for the Management
request prepared under
[`decision-request-preparation.md`](decision-request-preparation.md).

| Trigger value | Mandatory criterion |
|---|---|
| `cross-item-blast-radius` | The decision can block the start, validation, acceptance, integration, release, or closure of at least one **other** work unit, or change that unit's contract. This applies regardless of whether the deciding node is marked as an integration checkpoint. |
| `authority-tailoring-or-waiver` | A role, independence, responsibility, approval, or other authority rule is tailored, combined, suspended, overridden, or given a waiver. |
| `material-architecture-or-repository-behavior` | The decision chooses between materially different architectures, or establishes repository-wide behavior, a canonical or shared interface, a persistent or boundary-crossing data format, or a durable process rule. Purely Task-local intermediate forms without persistent, shared, or boundary-crossing effects do not trigger this value. |
| `irreversible-or-external-effect` | The decision causes an irreversible migration/deletion or an effect outside the isolated worktree. |
| `security-or-credential-boundary` | The decision establishes or changes security boundaries, credentials, signatures, identity verification, permissions, or secret handling. |
| `public-release` | The decision concerns a public release, delivery, or its approval conditions. |
| `material-risk-decision` | The decision accepts, rejects, defers, or compensates for a material technical, operational, privacy, security, safety, legal, or residual risk. |

Triggers are **alternative**, not cumulative: one match is sufficient. In particular, `cross-item-blast-radius` is the normative reach criterion from TK-2. Difficulty, novelty, effort, privilege, or a green validation result alone are neither triggers nor exemptions.

No record is required when **no** trigger applies. Typical negative cases appear in section 8. Anyone who classifies a mandatory case as a local implementation detail even though it can affect other units or gates violates TK-2.

## 3. Canonical Markdown format

### 3.1 Lexical and semantic rules

- **Stable ID:** `DEC-` followed by four decimal digits, a hyphen, and three decimal digits; regular expression `^DEC-[0-9]{4}-[0-9]{3}$`. The ID is unique in the repository, is never reused, and remains unchanged on correction, deferral, or supersession.
- **Timestamp:** a complete ISO-8601 timestamp with seconds and timezone; the permitted RFC-3339 subset is `YYYY-MM-DDTHH:MM:SS`, optionally followed by `.fraction`, and ending in `Z`, `+HH:MM`, or `-HH:MM`. Date, time, and offset must be semantically valid. A local timestamp without an offset is invalid.
- **Identity:** an immutable session token or stable reference to a registered human/organizational authority. Exactly one of the following complete grammars is permitted:
  - Agent/session:
    `^agent:[A-Za-z0-9][A-Za-z0-9._-]*(?::[A-Za-z0-9][A-Za-z0-9._-]*){2,}$`;
  - registered authority:
    `^authority:[A-Za-z0-9][A-Za-z0-9._-]*(?::[A-Za-z0-9][A-Za-z0-9._-]*)+$`;
  - additive historical authority reference:
    `^legacy-authority:[A-Za-z0-9][A-Za-z0-9._-]*(?::[A-Za-z0-9][A-Za-z0-9._-]*)+$`.
  Each colon-separated payload component begins alphanumerically and thereafter contains only ASCII letters, digits, periods, underscores, or hyphens. Empty components, whitespace, `/`, `\\`, `#`, `..` as a component, and path-like relative segments are therefore invalid. The agent grammar permits current owner-token forms, including Task/Subtask ID and any collision-resistant request ID. Display names, model names, “current user”, “privileged”, or a Git author line alone are not identities.
- **Role:** exactly one of `Requirements Engineer`, `Architekt`, `Implementierer`, `Integrator`, `QA-Manager`, `Management`, or a specialist role matching `^registered specialist:[a-z0-9][a-z0-9._-]*$`. The stable role ID is non-empty, contains no whitespace or path separator, and begins with an ASCII lowercase letter or digit component.
- **Authority reference:** a stable ID or path-and-anchor reference to an assignment, directive, policy, or registered authority. A capability class or self-asserted role is not an authority reference.
- **Work-unit references:** `feature:<ID>`, `task:<ID>`, `subtask:<ID>`, `path:<repository-relative-path>`, `repository:<name>`, or `external:<stable-id>`. At least one entry is required; `none` is permitted only when the decision demonstrably cannot be assigned to a single work unit despite its mandatory trigger.
- **Gate references:** `task-start:<ID>`, `validation:<stable-id-or-path>`, `integration:<ID>`, `feature-closure:<ID>`, `release:<stable-id>`, `external:<stable-id>`, or the sole value `none`.
- Free-text fields are non-empty and contain no placeholders such as `TBD`, `unknown`, or `n/a`. A genuinely missing human decision is recorded as nonconformity, not invented.

### 3.2 Required fields and order

A record uses exactly this structure. List IDs start at `01`, are contiguous within their list, and are never renumbered:

```markdown
### `DEC-1234-001` — <short title>

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-18T12:34:56+02:00`
- **Deciding identity:** `agent:<immutable-session-token>`
- **Role:** `Architekt`
- **Authority reference:** `<stable authority reference>`
- **Subject:** <unambiguously bounded decision subject>
- **Decision:** <decision made>
- **Technical justification:** <technical/domain justification>
- **Triggers:**
  - `cross-item-blast-radius`
- **Considered alternatives:**
  - **ALT-01:** <alternative>
    - **Disposition:** `selected`
    - **Reason:** <reason>
  - **ALT-02:** <alternative>
    - **Disposition:** `rejected`
    - **Reason:** <reason>
- **Consequences:**
  - **CON-01:** <positive, negative, or neutral consequence>
- **Affected work units:**
  - `task:1234-01`
- **Affected gates:**
  - `validation:_src/validate.py`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `authority:<immutable-authority-id>`
    - **Role:** `registered specialist:<stable-role-id>`
    - **Participation:** `consulted`
    - **Position:** `supports`
    - **Note:** <non-empty summary>
- **Waiver:** `none`
```

The following cardinalities apply:

- `Record format` through `Technical justification` occur exactly once.
- `Triggers` contains at least one unique value from section 2.
- `Considered alternatives` contains at least two alternatives. Exactly one has `selected`; every other alternative has `rejected` or `deferred`. Every alternative has exactly one non-empty reason.
- `Consequences` contains at least one entry. Costs, commitments, rollback boundaries, and deliberately remaining risks are also named.
- `Affected work units` and `Affected gates` each contain at least one entry using the syntax in section 3.1; `none` cannot be mixed with further entries.
- `Review participation` contains either at least one `PART-NN` block or exactly the value `none`. When it is `none`, the mandatory field `No-review reason` follows immediately. Participation values are `consulted`, `reviewed`, or `dissented`; position values are `supports`, `opposes`, or `no-position`.
- The deciding instance MAY additionally appear as a participant, but does not replace an available second instance.
- `Waiver` is either `none` or the block in section 4.

This format requires recorded participation, but does not automatically require a positive review. Dissent remains visible; the absence of a second instance is recorded openly with `Review participation: none` and a reason.

### 3.3 Preparing the unresolved request

A `decision-request@v1` is the durable request for a decision; it is not the
decision and it does not allocate a `DEC-*` identifier. Preparers MUST follow
[`decision-request-preparation.md`](decision-request-preparation.md) before
submitting a request that may later produce a record under this document.

The preparation rules preserve the boundary between question and answer:

- one durable request contains exactly one decision question;
- a binary question contains exactly the mutually exclusive `YES` and `NO`
  effects;
- a question with more than two valid outcomes contains one mutually exclusive
  option set, not one yes/no request for each option;
- the submitter and the authorized resolver are named separately; submitting a
  request does not grant authority to resolve it;
- known later decisions or reviews are identified as subsequent signature
  waves, not hidden inside the current question; and
- handoff occurs only after the exact created decision ID reports `pending`;
  continuation after an answer uses that same exact ID and requires a
  `resolved` status.

Mail and graphical views are informational projections. Their presence,
absence, title, or visual state is never the durable request status, the
resolution, the deciding authority, or a final `decision-record@v1`.

This preparation clarification changes neither the field order in section 3.2
nor decision authority, gate reach, tool schema, assignment state-machine
behavior, or the append-only recording rules below.

## 4. Authority tailoring and waivers

Every authority tailoring and waiver triggers `authority-tailoring-or-waiver`. A bounded waiver replaces the final line of the base format with exactly this block:

```markdown
- **Waiver:** `bounded`
  - **Conflict:** <which role, independence, or authority rule conflicts>
  - **Reason:** <why the waiver is required>
  - **Scope:** <exhaustively named work units, actions, and gates>
  - **Duration:** `from <ISO-8601 timestamp with timezone> until <ISO-8601 timestamp with timezone>`
  - **Compensating controls:**
    - **CTRL-01:** <control>
```

Instead of the end timestamp, `event:<stable-reference>` is permitted. Start and end must be unambiguous; `indefinite`, a missing end, and an implicit Task/Feature lifetime are invalid. `Compensating controls` contains at least one entry. Conflict, reason, scope, duration, and compensating controls are independently mandatory. Only the responsible management or registered authority may add missing waiver information; an implementer must not infer or invent it.

## 5. Append-only history and corrections

Published records are not rewritten, deleted, or silently “cleaned up”. A correction fixes a recording error; a decision made differently later is a **new** `DEC-…` record that references the earlier record under `Subject`, `Technical justification`, and `Consequences`.

A correction is appended immediately after the previous record or its preceding correction events. Each event changes exactly one field so that sequence and effective value are deterministic:

````markdown
#### `DEC-1234-001-C001`

- **Event format:** `decision-record-correction@v1`
- **Target record:** `DEC-1234-001`
- **Recorded at:** `2026-08-18T13:00:00+02:00`
- **Correcting identity:** `agent:example:architect:1234-01:session-a1`
- **Role:** `Architekt`
- **Authority reference:** `<stable authority reference>`
- **Correction reason:** <which recording error is corrected>
- **Target field:** `Technical justification`
- **Previous effective block SHA-256:** `<64 lowercase hexadecimal digits>`
- **Replacement block:**
  ```markdown
  - **Technical justification:** <complete replacement field block>
  ```
````

Event IDs follow `^DEC-[0-9]{4}-[0-9]{3}-C[0-9]{3}$`, start at `C001`, and are contiguous per record. `Target field` names exactly one top-level field of the base format. Changing a subfield therefore replaces the complete enclosing top-level block, for example the entire `Waiver` or `Considered alternatives` block. Multiple top-level field changes require multiple events.

The digest preimage is defined exactly as follows:

1. The record is UTF-8 without BOM and uses only LF (`0x0a`) line endings. No Unicode, whitespace, line-ending, indentation, or Markdown normalization occurs for the digest.
2. The field block starts at the first byte `-` of the top-level line `- **<Target field>:**` in column 1. Label, colon, Markdown markup, spaces, and every indentation character are part of the preimage.
3. The field block ends immediately after the LF of the last physical line belonging to the field. After the label line, only non-empty continuation or child lines with at least two leading ASCII spaces belong to the field. The first empty line, next column-1 line beginning with `- **`, next heading, or end of file ends the block and is not part of it. A separating blank line before a heading or correction event is therefore never part of the preimage. The preimage includes the terminating LF of the final included line.
4. For a scalar field, the preimage therefore includes the label line, all indented physical continuation lines, and their terminating LF. For a list field, it additionally includes every list entry and descendant with their original indentation through the preceding block boundary.
5. `Previous effective block SHA-256` is SHA-256 of exactly that byte sequence. After a previous correction, the preimage is the effective `Replacement block` of that correction, not the historical original block.
6. The inner `markdown` fence under `Replacement block` is transport only. The effective replacement bytes start at the first `-` of the embedded field line and end with exactly one LF immediately before the closing fence; the fence, its indentation, and the two transport spaces before the displayed lines are not part of the replacement byte sequence. The deindented replacement block MUST begin with the same top-level label and satisfy rules 2–4.

The digest prevents applying an event to obsolete history. No event may make the ID, original timestamp, or original deciding identity invisible; an error in recording them can be corrected only through a visible correction event.

## 6. Additive mapping of structurally divergent legacy records

A historical record that does not exactly conform to section 3 remains **structurally nonconforming**, even if its semantics can be reconstructed completely. Neither original plus free text nor original plus a map thereby becomes a `decision-record@v1`. The separate format `decision-record-legacy-map@v1` is used for the explicit, machine-readable deviation disposition:

````markdown
#### `DEC-1234-001-LM001`

- **Map format:** `decision-record-legacy-map@v1`
- **Target record:** `DEC-1234-001`
- **Source path:** `docs/path/file.md#stable-heading`
- **Map recorded at:** `2026-08-18T14:00:00Z`
- **Mapping identity:** `agent:example:implementer:1234-01:session-b2`
- **Mapping role:** `Implementierer`
- **Mapping authority reference:** `task:1234-01`
- **Structural disposition:** `legacy-structurally-nonconforming`
- **Semantic disposition:** `complete`
- **Missing semantic fields:** `none`
- **Deviation:** <why the historical layout is not v1-parseable>
- **Semantic projection JSON:**
  ```json
  {"recorded_at":"2026-08-18T12:00:00Z","deciding_identity":"legacy-authority:example:review:2026-08-18T12.00.00Z","role":"Management","authority_reference":"RQ-EXAMPLE-01","subject":"<text>","decision":"<text>","technical_justification":"<text>","triggers":["material-architecture-or-repository-behavior"],"considered_alternatives":[{"id":"ALT-01","text":"<text>","disposition":"selected","reason":"<text>"},{"id":"ALT-02","text":"<text>","disposition":"rejected","reason":"<text>"}],"consequences":[{"id":"CON-01","text":"<text>"}],"affected_work_units":["task:1234-01"],"affected_gates":["none"],"review_participation":[{"id":"PART-01","identity":"agent:example:reviewer:1234-01:session-c3","role":"Requirements Engineer","participation":"consulted","position":"supports","note":"<text>"}],"no_review_reason":null,"waiver":{"type":"none"}}
  ```
- **Source bindings JSON:**
  ```json
  {"recorded_at":["legacy:Zeitpunkt"],"deciding_identity":["additive:historical-authority-anchor"],"role":["additive:recorded-management-context"],"authority_reference":["legacy:review-context"],"subject":["legacy:Gegenstand"],"decision":["legacy:Entscheidung"],"technical_justification":["legacy:Fachliche Rechtfertigung"],"triggers":["additive:trigger-classification"],"considered_alternatives":["legacy:Gegenstand","legacy:Fachliche Rechtfertigung"],"consequences":["legacy:Folge"],"affected_work_units":["additive:scope-classification"],"affected_gates":["additive:gate-classification"],"review_participation":["legacy:review-context"],"no_review_reason":["additive:not-applicable"],"waiver":["additive:none"]}
  ```
````

Map IDs follow `^DEC-[0-9]{4}-[0-9]{3}-LM[0-9]{3}$` and are contiguous per target. Field order is exactly as shown in the pattern. `Source path` is a non-empty repository-relative Markdown path with an anchor, without whitespace, `..`, an absolute path, or a backslash. Both fence contents are RFC-8259 JSON without duplicate keys. The projection has exactly the keys shown in the pattern and uses the field semantics from sections 2–4; `Source bindings JSON` has exactly the same keys and, for each key, a non-empty array of `legacy:<exact-field-label-or-stable-source-anchor>` or `additive:<stable-reason-id>`. Each payload is a non-empty single-line string without leading or trailing whitespace; `legacy:` names a literal legacy field label or stable section anchor, and `additive:` names a stable reason for the added classification.

`Semantic disposition: complete` requires `Missing semantic fields: none`, no `null` value in a semantically mandatory field, and a fully v1-validatable projection. For `incomplete`, `Missing semantic fields` contains a comma-separated list of canonical field paths, and exactly these values are `null` in the projection; every other field remains complete. A missing waiver endpoint is named as `Waiver.Duration`. The map is a deviation/migration trace, not a correction and not a retrospective decision. An actually migrated v1 record requires a new append-only entry under the responsible authority and must not replace the historical original.

## 7. Acceptance and integration verdicts are specialized formats

An `Acceptance: ✓` record under [`task-acceptance.md`](task-acceptance.md) is a specialized format for accepting an exactly bound work-product baseline. A `[u]` integration verdict under [`branch-workflow.md`](branch-workflow.md) is a specialized format for a blocked integration checkpoint. Neither is a `decision-record@v1` record and neither is rewritten into this layout. Their own authority, identity, time, and append-only rules remain authoritative.

The specialization does not exempt TK-2: if acceptance or a verdict rests on an architectural choice, authority waiver, security/release decision, or material risk decision, a separate `DEC-…` record MUST exist. The acceptance record references it in its `Authority reference` or bound review evidence; the integration verdict references it in `Reason` or its append-only resolution. A review result alone does not grant missing specialist authority.

## 8. Worked examples

The IDs `DEC-9000-901` … `DEC-9000-903` are instructional, unregistered examples only.

### Positive 1 — repository-wide validation gate

```markdown
### `DEC-9000-901` — Host scripts receive a separate validation profile

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-18T09:15:00Z`
- **Deciding identity:** `agent:example:architect:9000-01:session-a1`
- **Role:** `Architekt`
- **Authority reference:** `task:9000-01`
- **Subject:** Scope of a blocking script checker
- **Decision:** Privileged host scripts are not blocked by the sandbox-internal standard profile; they are checked by their own equivalent profile instead.
- **Technical justification:** Host and sandbox scripts have different trust and execution boundaries; a shared gate creates repository-wide blocks without matching repair authority.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
  - `security-or-credential-boundary`
- **Considered alternatives:**
  - **ALT-01:** Separate profiles with a shared minimum contract
    - **Disposition:** `selected`
    - **Reason:** Preserves complete checking while separating authority boundaries.
  - **ALT-02:** Block every script through the same profile
    - **Disposition:** `rejected`
    - **Reason:** A finding in host infrastructure could block every other Task.
- **Consequences:**
  - **CON-01:** Both profiles must pass before Feature closure.
  - **CON-02:** The standard gate cannot block a host file solely due to sandbox-inapplicable rules.
- **Affected work units:**
  - `repository:autodocs`
  - `task:9000-01`
- **Affected gates:**
  - `validation:_src/validate.py`
  - `feature-closure:9000`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `authority:example:security-owner-01`
    - **Role:** `registered specialist:security-owner`
    - **Participation:** `reviewed`
    - **Position:** `supports`
    - **Note:** Separate profiles do not weaken host checking.
- **Waiver:** `none`
```

**Why positive:** The possible blocking of other Tasks alone triggers TK-2; the security boundary and repository-wide behavior are additional triggers.

### Positive 2 — materially different architectures

```markdown
### `DEC-9000-902` — One record per work unit instead of a shared state file

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-18T11:20:30+02:00`
- **Deciding identity:** `agent:example:architecture:9000-02:session-b2`
- **Role:** `Architekt`
- **Authority reference:** `feature:9000`
- **Subject:** Persistence architecture for work status
- **Decision:** Every work unit receives its own record at a stable path.
- **Technical justification:** Path isolation reduces merge conflicts and enables atomic validation per unit; a shared file couples independent authors.
- **Triggers:**
  - `material-architecture-or-repository-behavior`
  - `cross-item-blast-radius`
- **Considered alternatives:**
  - **ALT-01:** One record per work unit
    - **Disposition:** `selected`
    - **Reason:** Isolated ownership and deterministic integration.
  - **ALT-02:** One repository-wide state file
    - **Disposition:** `rejected`
    - **Reason:** Conflicts and partial updates would have cross-Feature effects.
  - **ALT-03:** External database service
    - **Disposition:** `deferred`
    - **Reason:** The added operational and credential dependency is not justified for the current scope.
- **Consequences:**
  - **CON-01:** Readers must aggregate multiple records deterministically.
  - **CON-02:** Write transactions remain limited to one work unit.
- **Affected work units:**
  - `feature:9000`
  - `repository:autodocs`
- **Affected gates:**
  - `integration:9000`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:example:implementer:9000-02:session-c3`
    - **Role:** `Implementierer`
    - **Participation:** `consulted`
    - **Position:** `supports`
    - **Note:** The isolated path is implementable with the existing file transactions.
- **Waiver:** `none`
```

**Why positive:** The alternatives differ materially in persistence, conflict model, and operation; the choice shapes repository-wide behavior.

### Positive 3 — time-bounded waiver for a public emergency release

```markdown
### `DEC-9000-903` — Narrowly override the four-eyes conflict for an emergency release

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-18T14:00:00Z`
- **Deciding identity:** `authority:example:management-on-call-07`
- **Role:** `Management`
- **Authority reference:** `authority:example:incident-INC-9000`
- **Subject:** One-time public emergency release when the independent instance is unavailable
- **Decision:** The implementer may additionally integrate release 9.0.1 only; signing remains with the registered release authority.
- **Technical justification:** The correction closes an active external security vulnerability; waiting for the integrator to return increases the documented risk.
- **Triggers:**
  - `authority-tailoring-or-waiver`
  - `irreversible-or-external-effect`
  - `security-or-credential-boundary`
  - `public-release`
  - `material-risk-decision`
- **Considered alternatives:**
  - **ALT-01:** Narrow role override with independent signing and subsequent review
    - **Disposition:** `selected`
    - **Reason:** Minimizes exposure duration without transferring signing authority.
  - **ALT-02:** Defer release until the integrator returns
    - **Disposition:** `rejected`
    - **Reason:** The external security risk remains open for longer.
  - **ALT-03:** Transfer signing credentials to the implementer
    - **Disposition:** `rejected`
    - **Reason:** Would unnecessarily remove an additional credential boundary.
- **Consequences:**
  - **CON-01:** Release 9.0.1 becomes externally visible and is not fully retractable.
  - **CON-02:** An independent follow-up review is mandatory before the next release.
- **Affected work units:**
  - `task:9000-03`
  - `external:release-9.0.1`
- **Affected gates:**
  - `integration:9000-03`
  - `release:9.0.1`
- **Review participation:** `none`
- **No-review reason:** The independent integrator instance is unavailable during the documented incident window.
- **Waiver:** `bounded`
  - **Conflict:** The implementer and integrator of the same work-product baseline would be the same person.
  - **Reason:** Active external security vulnerability while an independent instance is unavailable.
  - **Scope:** Integration of task:9000-03 into release:9.0.1 only; no signing or credential authority.
  - **Duration:** `from 2026-08-18T14:00:00Z until 2026-08-18T18:00:00Z`
  - **Compensating controls:**
    - **CTRL-01:** The registered release authority verifies the manifest and signs personally.
    - **CTRL-02:** An independent downstream review blocks every subsequent release.
```

**Why positive:** The record is mandatory because of the waiver alone; external effect, security boundary, public release, and risk acceptance reinforce the obligation. Conflict, reason, scope, duration, and controls are complete.

### Negative 1 — local helper choice

Within `task:9000-04`, an implementer chooses a loop rather than a local comprehension for a new private function. Signature, output, runtime bound, persistent format, foreign paths, and every gate remain unchanged. **Result:** no trigger and therefore no decision record. The choice can be assessed in ordinary review. If it instead became a repository-wide style rule or a lint gate that blocks other Tasks, `material-architecture-or-repository-behavior` or `cross-item-blast-radius` would apply.

### Negative 2 — unambiguously determined typo/link repair

A document refers to `task-aceptance.md`; only `task-acceptance.md` exists in the same directory, and every neighboring reference confirms that target. The repair changes only the defective link and no normative meaning. **Result:** an unambiguously determined editorial repair, no trigger, and no decision record. If several plausible targets exist or the choice changes the normative process, it is no longer unambiguous and is assessed again against section 2.

## 9. Checkable in principle

A later validator can check at least the following without domain heuristics:

1. unique ID and closed field order;
2. valid ISO-8601 timestamp with timezone;
3. permitted identity prefixes, role, and trigger values;
4. list cardinality, contiguous IDs, and exactly one selected alternative;
5. reference syntax for work units and gates;
6. a complete review or no-review variant;
7. for `bounded`, the five waiver components including finite duration;
8. contiguous correction events and binding to the previous effective field value.

Whether a technical justification is substantively sound, an alternative is truly material, or a stated authority was responsible remains a matter for review. Machine-checkable form is not automatic approval.
