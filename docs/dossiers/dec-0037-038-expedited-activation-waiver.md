# Expedited activation waiver

### `DEC-0037-038` — One bounded activation/reference sequence with deferred assurance

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-09-06T05:50:04Z`
- **Deciding identity:** `authority:mancons:decision-0037-40-expedited-activation-waiver-20260905`
- **Role:** `Management`
- **Authority reference:** `decision-0037-40-expedited-activation-waiver-20260905`; duration and owner-provenance supplement `decision-0037-40-expedited-waiver-duration-and-owner-prompt-20260906`, resolved event `1788673754003-f2612965`.
- **Subject:** Activation-precondition waiver for exactly one Task `0037-40` activation/reference sequence on the retained candidate branch, based on `e255b794b8d746ec2f65048a412faa907d2a2314`, without false completion of deferred assurance or Feature closure.
- **Decision:** Select `expedite_activation`: `0037-35.01`, `0037-35.02`, `0037-35`, and `0037-36` cease to be preconditions for this one `0037-40` activation/reference sequence. Their evidence, findings, and unpassed/unaccepted states remain visible. Apply the minimum controls below before the first normal write and record remaining assurance as subsequent work after writing is enabled. Do not close Feature `0037` or claim Task Acceptance through this waiver. The resolved supplement selects `single_sequence_boundary`: expiry is completion or abandonment of this sequence, or earlier explicit revocation; a later retry or materially changed candidate requires fresh authority.
- **Technical justification:** The durable request records a completed switch to `issues/` as the sole authority, frozen normal writes, no newly created canonical data existing only in the new model, and no external irreversible effects. Those decision-time premises make Git retention and additive recovery suitable compensations. The freeze prevents new tickets, claims, and Features and causes disproportionate time and budget cost (Handlungsunfähigkeit). Management chose restored working capacity with bounded minimum controls over further advance assurance. These premises are attributed to the resolved request; this dossier does not claim a new operational audit. Changed premises require authority reassessment. The waiver changes only the specified precondition effects of the earlier assurance chain and `0037-40` contract, retaining earlier decisions and unrelated controls append-only.
- **Triggers:**
  - `cross-item-blast-radius`
  - `authority-tailoring-or-waiver`
  - `material-architecture-or-repository-behavior`
  - `material-risk-decision`
- **Considered alternatives:**
  - **ALT-01:** `expedite_activation` — activate with minimum controls and defer the remaining assurance.
    - **Disposition:** `selected`
    - **Reason:** Recommended by the durable request because Git retains the relevant states, no new-only or external irreversible state is in scope, and continued freeze cost exceeds the remaining advance-assurance benefit. The duration supplement restricts this choice to one sequence.
  - **ALT-02:** `continue_full_chain` — finish `0037-35.01`, `0037-35.02`, `0037-35`, and `0037-36` before activation.
    - **Disposition:** `rejected`
    - **Reason:** More advance assurance preserves the existing prerequisites but prolongs inability to create work and consumes additional time and budget with an uncertain activation date.
- **Consequences:**
  - **CON-01:** All issue/claim writers and fresh-agent bootstrap consumers are affected by the eventual writable epoch; the assurance tasks remain unpassed, and their remaining work must be recorded after normal writes are enabled. No quantitative cost estimate or additional deadline is asserted.
  - **CON-02:** The supported later authored activation paths are exactly `agent-workflow.json`, `docs/pipeline/agent-instructions/future/index.md`, `issues/0037/0037-40/index.md`, `provenance/migrations/issue-store/0037-40-activation.json`, and `provenance/migrations/issue-store/0037-40-reference.json`. Generated paths follow the real committed mapping described below. The present award permits only this decision dossier.
  - **CON-03:** Regeneration, rollback-rehearsal, and audit assurance remain outstanding risks. Real minimum controls remain blocking; no full assurance PASS, general validator bypass, or tool/policy rewrite is authorized.
  - **CON-04:** Preserve every ref, commit, finding, and post-activation issue. Recovery is additive correction, re-freeze, or rollback through the retained recovery path. No reset, rebase, ref deletion, push, publication, external migration, competing legacy authority, or loss of new data is authorized.
  - **CON-05:** The record must be independently reviewed and integrated into canonical governance before activation mutation. Exact implementation assignment, distinct implementation/review identities, the named Integrator reservation, candidate ancestry, and the two-commit activation/reference sequence remain required. Recording or accepting this dossier does not activate writes or close the Feature.
- **Affected work units:**
  - `repository:autodocs`
  - `feature:0037`
  - `subtask:0037-35.01`
  - `subtask:0037-35.02`
  - `task:0037-35`
  - `task:0037-36`
  - `task:0037-40`
  - `task:0037-44`
- **Affected gates:**
  - `task-start:0037-40`
  - `integration:0037-40`
  - `validation:issue-store-first-normal-write`
  - `validation:_src/tools/agent_bootstrap.py`
  - `feature-closure:0037`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:data:0037-40:1788648697101-b574994d`
    - **Role:** `Architekt`
    - **Participation:** `reviewed`
    - **Position:** `supports`
    - **Note:** Conditional scope support in `1788648814551-d0079f36`, `1788648833587-3a380eab`, and `1788648833613-34397683`, accepted by supervisor in `1788667212758-909cf403`. Binds exact authored/generated paths, minimum checks, two-commit sequencing, additive recovery, and no false assurance completion or Feature closure. This is distinct scope review for later implementation, not independent review of Data's present decision dossier; that remains a separate assigned step.
- **Waiver:** `bounded`
  - **Conflict:** The current `0037-40` prerequisite and criteria require completed clean-regeneration, rollback-rehearsal, package, and post-cutover-audit assurance from `0037-35.01`, `0037-35.02`, `0037-35`, and `0037-36` before activation, and describe their closure and Feature closure. The owner-directed expedited sequence cannot satisfy or claim that advance completion.
  - **Reason:** Restore project working capacity under the resolved Management choice while retaining minimum authority/operability controls and the outstanding assurance honestly.
  - **Scope:** Exactly one `0037-40` activation/reference sequence; remove only `0037-35.01`, `0037-35.02`, `0037-35`, and `0037-36` as its preconditions. Cross-item effect is availability for all ordinary issue/claim writers and bootstrap consumers after controlled activation. No assurance-task pass/acceptance, Feature closure, independent-review waiver, or other authority transfer is included. A later retry or materially changed candidate requires fresh authority.
  - **Duration:** `from 2026-09-06T05:49:14Z until event:DEC-0037-038-single-sequence-end`
  - **Compensating controls:**
    - **CTRL-01:** `DEC-0037-038-single-sequence-end` is the first occurrence of completion of the one activation/reference sequence, abandonment of that sequence, or earlier explicit Management revocation, as authorized by resolved event `1788673754003-f2612965`. Retain the terminal event with the sequence evidence. Later retries or materially changed candidates require fresh authority. Expiry does not undo a completed activation or erase outstanding assurance and recovery obligations.
    - **CTRL-02:** Before activation mutation integrate this conforming record and obtain the exact implementation assignment; keep the one candidate chain and reserved independent Integrator. Review this dossier independently; no self-acceptance.
    - **CTRL-03:** Before any normal write verify exactly one readable issue-store authority, deterministic real regeneration plus repeat no-op, successful fresh-agent doctor, and rejection of legacy write commands with unchanged bytes. Retain red assurance findings; minimum-check failure continues to block normal writes.
    - **CTRL-04:** Bind the writable selector profile/epoch/write phase, incremented workflow version, instruction-member hash, and selector digest. Reject stale and legacy expectations. Generate only actual committed outputs; do not hand-author projections or weaken validators.
    - **CTRL-05:** Sign the activation manifest with base/tree, expected transaction head, exact delta, and authority. The follow-up reference commit binds the actual activation OID and results without self-hashing. Keep writers quiescent until both commits are integrated and minimum controls pass.
    - **CTRL-06:** The named Integrator checks the exact candidate, hygiene, root pre/post conditions, ancestry, and append-only transaction CAS. This author performs none of those integration actions; privilege and scope support do not substitute for exact authority.
    - **CTRL-07:** Bound the first normal write to a subsequently named item/path/owner/preimage through the ordinary command and validation/regeneration; retain its commit and verify additive compensation. The present dossier does not select or authorize an unspecified first-write target.
    - **CTRL-08:** Preserve all refs, commits, evidence, findings, and new data. On failure use additive correction/re-freeze/rollback, with `0037-44` retained as the recovery path, never destructive reset or competing authority. Record deferred assurance as normal follow-up after write availability; do not mark it passed or accepted.

## Owner instruction and completion authority

Verbatim repository-owner operative instruction, supplied by Management in
resolved event `1788673754003-f2612965`:

> Ja — sofortiger Cutover; Restnachweise nachgelagert

The corresponding decision is
`decision-0037-40-expedited-waiver-duration-and-owner-prompt-20260906`, option
`single_sequence_boundary`, resolved by `mancons` at `2026-09-06T05:49:14Z`.
Its complete resolution text is:

> Authorize exactly one 0037-40 activation/reference sequence. The waiver expires when that sequence completes or is abandoned, and may be revoked earlier explicitly; any later retry or materially changed candidate requires fresh authority. The exact Repository Owner operative instruction to quote verbatim in DEC-0037-038 is: „Ja — sofortiger Cutover; Restnachweise nachgelagert“. This supplements, without changing, resolved decision decision-0037-40-expedited-activation-waiver-20260905 and its minimum controls.

This closes the two missing-input questions recorded in coordinator request
`1788667306923-94f1905a`. The earlier uncommitted preparation was explicitly
non-operative; no activation or check-in occurred under it. The canonical
record above awaits independent record review and governance integration.

## Authorship and baseline

- Authoring assignment: `1788667224280-2b1c1102`.
- Recording identity: `agent:data:0037-40:1788667224280-2b1c1102`.
- Capability: `privileged`; process: Architecture/governance recording only.
- Sole branch: `0037-40-expedited-activation`.
- Worktree: `/private/tmp/autodocs-worktrees/0037-40-expedited-activation`.
- Base: `e255b794b8d746ec2f65048a412faa907d2a2314`.
- Sole authored path: `docs/dossiers/dec-0037-038-expedited-activation-waiver.md`.
- Identifier check: `DEC-0037-038` absent from `main:docs/dossiers` at the base.
- No separate claim is created: ordinary claim writes remain frozen and the
  award permits only this dossier.

## Verified decision source

The durable request is
`decision-0037-40-expedited-activation-waiver-20260905`, stored at
`logs/agent-inbox/decision-requests/decision-0037-40-expedited-activation-waiver-20260905.json`.
Its corresponding `.events.jsonl` contains resolution event
`1788648639396-57d60144`, responder `mancons`, timestamp
`2026-09-05T22:50:39Z`, selected option `expedite_activation`.
The deciding identity is
`authority:mancons:decision-0037-40-expedited-activation-waiver-20260905`,
role `Management`; Data records the decision and does not decide the waiver.

The complete resolution text, reproduced as an authority-event quote rather
than represented as the owner's verbatim prompt, is:

> Management entscheidet auf ausdrückliche Auswahl des Repository Owners: sofortiger Cutover; Restnachweise werden nachgelagert. Waiver-Scope: 0037-35.01, 0037-35.02, 0037-35 und 0037-36 entfallen als Vorbedingungen für 0037-40, ohne ihre bisherigen Evidence- oder Finding-Historien zu löschen oder als bestanden darzustellen. Grund: Der Freeze macht das Projekt handlungsunfähig und verursacht unverhältnismäßige Zeit- und Budgetkosten; es existieren keine neuen ausschließlich im neuen Modell vorhandenen Daten und keine externen irreversiblen Effekte. Kompensierende Kontrollen: vor dem ersten normalen Write genau eine Authority, lesbarer issue store, deterministische Regeneration, Fresh-Agent-Doctor und Legacy-Command-Rejection prüfen; erster Write kontrolliert und reversibel; alle Refs/Commits erhalten; Fehler nur durch additiven Korrektur-/Rollback-Commit behandeln, kein destruktiver Reset; Restnachweise nach Schreibfreigabe als normale Nachfolgearbeit erfassen.

## Supporting scope and execution rationale

### Subject and operative effect

Permit the single `0037-40` activation/reference sequence to proceed without
the remaining `0037-35.01`, `0037-35.02`, `0037-35`, and `0037-36` assurance
work as activation preconditions. Preserve those work products, findings, and
states without recording them as passed or accepted. This does not close
Feature `0037`, grant Task Acceptance, or remove independent integration.

The resolution changes the precondition effect of the cited assurance chain
and the corresponding `0037-40` contract only. Earlier decision records remain
visible; their unrelated semantic-validation, evidence-retention, identity,
independence, and integration controls continue to apply. No generic validator
bypass or tool/policy rewrite follows from this waiver.

### Reason, alternatives, and consequences

The request records that `issues/` already is the single authority, that normal
writes are frozen, and that no new canonical post-cutover-only data or external
irreversible effects are involved. Those are the Management decision's stated
premises, not a fresh operational verification by this record author. The
continued freeze prevents tickets, claims, and Feature work and incurs
disproportionate time and budget cost. Any changed premise requires authority
reassessment before proceeding.

1. `expedite_activation` — selected and recommended by the durable request:
   perform the minimum controls before normal writes, preserve all refs, make
   the first write reversible, and schedule deferred assurance after writing is
   enabled. This restores working capacity sooner but leaves the remaining
   regeneration, rollback-rehearsal, and audit assurance outstanding.
2. `continue_full_chain` — rejected by selection of the first option: complete
   the existing assurance chain before activation. This provides fuller
   advance assurance at the cost of continuing the freeze and consuming more
   time and budget.

There is no numerical cost estimate or new delivery commitment in the durable
resolution. There is no authorization for remote push, publication, external
migration, destructive reset, rebase, or ref deletion. Recovery uses additive
correction or rollback while retaining all historical and post-activation data.

### Affected units and gates

- `repository:autodocs`: all ordinary issue/claim writers and bootstrap consumers.
- `feature:0037`: activation availability changes; Feature closure stays separate.
- `subtask:0037-35.01`, `subtask:0037-35.02`, `task:0037-35`, `task:0037-36`:
  activation-precondition effect is waived; assurance is deferred, not passed.
- `task:0037-40`: bounded terminal activation/reference sequence.
- `task:0037-44`: retained post-activation recovery path.
- Gates: `task-start:0037-40`, `integration:0037-40`,
  `validation:issue-store-first-normal-write`,
  `validation:_src/tools/agent_bootstrap.py`, and `feature-closure:0037`.

### Accepted distinct Architect scope review

Review assignment `1788648697101-b574994d`, identity
`agent:data:0037-40:1788648697101-b574994d`, role `Architekt`, participation
`reviewed`, position `supports` conditionally. Result messages are
`1788648814551-d0079f36`, `1788648833587-3a380eab`, and
`1788648833613-34397683`; the supervisor accepted that assignment in
`1788667212758-909cf403`. These review records establish scope support distinct
from later activation implementation. They do not independently review this
new decision dossier; an independently assigned reviewer must do that.

The supported later authored activation paths are `agent-workflow.json`,
`docs/pipeline/agent-instructions/future/index.md`,
`issues/0037/0037-40/index.md`,
`provenance/migrations/issue-store/0037-40-activation.json`, and
`provenance/migrations/issue-store/0037-40-reference.json`. The present award
authorizes none of those writes. Derived outputs must come from the actual
committed generation mapping: `TODO.md`, `DONE.md`,
`issues/_views/catalog.json`, `issues/_views/dependency-graph.json`, and
`summaries/{open,blocked,unclear,owners}.md` plus `run-manifest.json` only where
the committed mapping requires them. The request's `issues/_catalog.json`
reference is not the implemented catalog output; the accepted review makes
this correction explicit.

### Compensating controls and execution boundaries

1. Integrate a conforming decision record and obtain explicit implementation
   assignment before activation mutation. Keep the same candidate chain and
   named Integrator reservation; no sibling candidate or self-acceptance.
2. Before any normal write, establish exactly one readable issue-store
   authority, deterministic real regeneration with repeat no-op, a successful
   fresh-agent doctor, and rejection of legacy writes without byte changes.
   Preserve visible red assurance results; do not claim a full `0037-35.01` pass.
3. Bind the writable selector profile/epoch/write phase, incremented workflow
   version, instruction member hash, and selector digest. Reject stale and
   legacy expectations. Failed minimum checks continue to block normal writes.
4. Sign an activation manifest binding base/tree, transaction expected head,
   exact delta, and authority. The separate follow-up reference commit binds
   the actual activation OID and results without a self-hash. Writers remain
   quiescent until both commits are integrated and minimum controls pass.
5. The named Integrator verifies the exact candidate, hygiene, root pre/post
   checks, ancestry, and append-only transaction CAS. This record author does
   not issue that verdict or advance the transaction or `main`.
6. The first normal write is limited to a subsequently named item/path/owner
   and preimage, through the ordinary command and validation/regeneration.
   Retain its commit and verify additive compensation. This record does not
   choose or authorize an unspecified first-write target.
7. Preserve all refs, commits, evidence, findings, and post-activation issues.
   Failures require additive re-freeze/correction or rollback, never destructive
   reset or a competing legacy authority. Record deferred assurance as normal
   follow-up work once writes are enabled; it remains unpassed meanwhile.

## Validation boundary

Validation of this documentation-only product checks canonical field order,
cardinality, permitted values, identity, timestamps, waiver duration, source
bindings, the single authored path, and whitespace. It does not execute or
claim activation, regeneration, doctor, first-write, recovery, or integration
checks. Those remain required at the later authorized execution points.
