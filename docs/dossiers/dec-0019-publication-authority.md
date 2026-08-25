# Decision record: publication authority for Feature 0019

**Format** per `decision-record@v1` (`docs/pipeline/decision-record.md`), append-only.
Own ID series `DEC-0019-0xx`.

---

## `DEC-0019-001` — Publication authority for Feature 0019 granted to `worf`

- **Recorded at:** 2026-08-21T22:45:00Z
- **Deciding identity:** Management (current user / repository owner)
- **Recording identity:** `agent:kathryn:projektleiter:0019-publication-authority:20260821T224500Z`
- **Role of the recorder:** Projektleiter under `DEC-ROLE-001` — records the
  decision, does not make it
- **Authority reference:** verbatim management order, reproduced under
  *Provenance* below and in
  [`dec-0019-001-provenance.txt`](dec-0019-001-provenance.txt)
- **Escalation origin:** privileged orchestrator `worf`, agent-inbox thread
  `0019`, 2026-08-21T21:56:14Z (message `1787349374460-b43791db`)

### Subject

Task `0019-10` closes the Eclipse S-Core v0.6.0 import campaign. Its acceptance
criteria require the campaign report to demonstrate every criterion in
`docs/pipeline/aspice-level1-score-import.md`, and that list explicitly includes
a **publication result**. Publication means pushing the built tree to the public
deploy repository `2b-rs/autodocs` (GitHub Pages,
<https://2b-rs.github.io/autodocs/>) — an external, public, and for practical
purposes irreversible effect.

`worf` declined to infer that authority from its existing local review and
integration permissions and escalated instead. That refusal was correct:
`AGENTS.md` reserves external effects and public release for explicit
authorization, and local integration permission does not imply it. Without the
grant, `0019-10` carried an acceptance criterion no agent could satisfy.

### Decision

**Management grants publication authority for Feature `0019` to `worf`, in full
scope.**

1. **Grantee:** the privileged orchestrator `worf`. `worf` may exercise the
   authority directly or delegate it to a subagent it dispatches; the delegation
   must be recorded in the dispatching briefing, and `worf` remains answerable
   for it.
2. **Scope:** every action required to satisfy the `publication result`
   criterion of `0019-10` and to close the v0.6.0 import campaign — publishing
   the authorized generated views to `2b-rs/autodocs`, the required remote/SSH
   configuration, and the push itself.
3. **Limits.** The grant is bounded to **Feature `0019`**. It is not a standing
   publication authority, does not extend to other Features, and does not
   authorize publishing anything Feature `0019` has not itself authorized.
4. **Unchanged by this record.** `Acceptance: ✓`, the integration checkpoints,
   and the `DONE.md` move remain separate privileged acts requiring their own
   explicit assignment. Publication authority is not acceptance authority.
5. **The `0019-08` curator decision still binds the payload.** All 2,239
   `invalid`/`to-be-confirmed` records remain excluded from factual
   publication; only the bounded curation/review views authorized under
   `0019-08`/`0019-09` may be published. This grant removes the *authority*
   gate, not the *content* gate.
6. **Publication does not become the next action.** As `worf` reported
   (2026-08-21T22:35:59Z), the `0019-11`/`0019-12` corrections must still
   converge into a checkpoint candidate and pass independent checkpoint
   acceptance before Feature integration. Publication is the last step of the
   Feature, not an unblocked one.

### Technical justification

Publishing is the one action in this repository that leaves the machine. It is
not covered by the ordinary local authority model, and no amount of local review
substitutes for it, which is precisely why `AGENTS.md` routes it to `[u]`. The
grant is recorded rather than conveyed in a message because a mailbox message is
explicitly **not** an authority proof (management directive, 2026-08-20): the
repository is the source of truth, and an agent asked later on what basis it
pushed must be able to point at a commit.

The scope is bounded to Feature `0019` because that is the question management
was asked. "In vollem Umfang" removes the internal limits on *how* `worf`
publishes for `0019` — it does not widen the Feature boundary of the grant. A
later Feature needing publication asks again.

### Consequences

- `0019-10` becomes completable. The recorded blocker is removed.
- `worf` should keep `0019-10` at `[p]` while the `0019-11`/`0019-12`
  convergence and checkpoint acceptance remain outstanding, and record this
  decision's REF as the authority reference in the `0019-10` bookkeeping when
  the publication is actually performed.
- The publication must carry its own evidence: what was published, from which
  commit, which digests, and against which curator decision.

### Provenance

Management order, verbatim, 2026-08-21, in answer to the question
"Erteilst du die Publikationsautorität für Feature 0019 — und wenn ja, an wen
und in welchem Umfang?":

> ja, an Worf, in vollem Umfang.

Full prompt chain of the recording session, unsummarized, in
[`dec-0019-001-provenance.txt`](dec-0019-001-provenance.txt).

**Note on the name.** The order says "Worf". The roster entry that holds the
privileged orchestrator role for Feature `0019` is `worf` (lower case); the
capitalized `Worf` is not a registered mailbox. Mailbox addresses in this
project are case-sensitive and have caused lost mail twice. The grantee is the
`worf` roster identity, unambiguous from the escalation this answers.

---

## `DEC-0019-002` — Integrationscheckpoints von Feature `0019` gewaivt; enge Ausschlussprüfung und Freigabevorschau treten an ihre Stelle

- **Recorded at:** 2026-08-22T00:00:00Z
- **Deciding identity:** Management (aktueller User / Repository-Eigentümer)
- **Recording identity:** `agent:kathryn:projektleiter:0019-checkpoint-waiver:20260822T000000Z`
- **Role of the recorder:** Projektleiter unter `DEC-ROLE-001` — zeichnet auf,
  entscheidet nicht
- **Authority reference:** wörtliche Managemententscheidung, siehe *Provenance*
  und [`dec-0019-002-provenance.txt`](dec-0019-002-provenance.txt)
- **Art des Datensatzes:** ausdrückliche Management-**Waiver** des vom
  Architekten gesetzten Review-Bodens. `AGENTS.md` erlaubt das ausschließlich
  dem Management und ausschließlich mit benannter Autorität, Geltungsbereich,
  Grund und kompensierenden Kontrollen. Alle vier sind unten benannt.

### Geltungsbereich

Die beiden Knoten in Feature `0019`, die `Integration review: mandatory`
tragen — `0019-12` (Public-Export-/Deployment-Grenze) und `0019-10` (die eine
integrierende Aufgabe des Features, sein Review-Boden) — verlieren die
Pflicht zum **vollen** unabhängigen Checkpoint-Review.

Der Waiver gilt **nur für Feature `0019`**. Er ändert die Checkpoint-Semantik
für kein anderes Feature, hebt `Integration review: mandatory` nirgendwo sonst
auf und ist kein Präzedenzfall für künftige Features.

### Grund

Feature `0019` hat über mehrere Tage sechs parallele Reviewer-Sessions
beschäftigt, ohne zu einem einzigen aktuellen Verdikt zu konvergieren. Der
Review-Boden hat in diesem Feature nachweislich nicht als Qualitätssicherung
gewirkt, sondern als Endlosschleife. Das Management hat den Zustand
ausdrücklich beendet.

### Kompensierende Kontrollen — verbindlich, kein Verzicht

Der volle Checkpoint wird ersetzt, **nicht gestrichen**. An seine Stelle treten
drei Kontrollen, die alle drei erfüllt sein müssen:

1. **Enge Ausschlussprüfung durch einen unabhängigen Agenten.** Ein Agent, der
   nicht an `0019` implementiert hat, beantwortet **genau eine** Frage: *Ist im
   Exportbaum versehentlich etwas enthalten, das nicht veröffentlicht werden
   darf?* Maßgeblich ist die Kuratorentscheidung `CUR-0019-08-20260820`: die
   2.239 als `invalid`/`to-be-confirmed` geführten Records bleiben von
   faktischer Publikation ausgeschlossen. Der Prüfer bewertet **nicht** Design,
   Codequalität, Testabdeckung oder Vollständigkeit des Features. Ergebnis ist
   `sauber` oder `Fund` mit Pfadliste, append-only aufgezeichnet.
2. **Freigabevorschau vor der Veröffentlichung.** Vor dem Push legt der
   Publizierende dem Management vor:
   - einen **anklickbaren lokalen Link** (`file://`) auf den fertig gebauten
     Exportbaum, damit er im Browser begehbar ist;
   - eine **Änderungsübersicht** in Prosa: was neu ist, was sich geändert hat,
     was bewusst fehlt — mit je einem Link auf die betroffene Seite.
   Die Übersicht darf mit veröffentlicht werden (Changelog auf der Website).
3. **Ausdrückliche Freigabe.** Erst nach einem ausdrücklichen „ja, das kann
   raus" des Managements erfolgt der Push. Die Publikationsautorität aus
   `DEC-0019-001` bleibt an diese Freigabe gebunden.

### Was der Waiver *nicht* tut

- Er hebt die **Inhaltsschranke nicht auf**. Die Kuratorentscheidung
  `CUR-0019-08-20260820` bindet unverändert; genau ihre Einhaltung ist der
  Gegenstand von Kontrolle 1.
- Er erlaubt **keine Selbstprüfung**. Der Prüfer aus Kontrolle 1 muss von der
  Implementierung unabhängig sein.
- Er ersetzt **nicht** die Feature-Integration nach `main` und den
  `DONE.md`-Umzug; die bleiben privilegierte Akte. Das Management hat die
  Feature-Integration `0019` → `main` der Projektleitung zugewiesen.
- Er ist **keine** Aussage darüber, dass die Arbeit fehlerfrei ist. Er ist eine
  bewusste Verschiebung von Prüftiefe zu Prüfgeschwindigkeit, deren Restrisiko
  das Management ausdrücklich trägt.

### Verfahrensanweisung an die Beteiligten

Die Blockadehaltung gegenüber der Fertigstellung von `0019` endet mit diesem
Datensatz. Weitere Reviewrunden über den Umfang von Kontrolle 1 hinaus werden
**nicht** angesetzt. Wer einen konkreten, benannten Fund hat, meldet ihn; ein
allgemeiner Wunsch nach mehr Prüfung ist ab hier kein Blocker mehr.

### Provenance

Managemententscheidung, wörtlich, 2026-08-22 — Antwort auf die Erläuterung der
drei Optionen (Bremse drin lassen / Bremse lösen / Mittelweg mit enger
Ausschlussprüfung):

> Ich möchte in solchen Fällen einen klickbaren Link ins lokale Dateisystem,
> zusammen mit einer übersicht über die durchgeführten änderungen, auch jeweils
> mit einem Link auf die Seiten, die sie betreffen. Ihr könnt das Changelog
> meinetwegen auch mit auf die Website stellen. Und dann könnt ihr mich fragen,
> ob das so raus kann. Aber die Art und Weise, in der Worf sich hier querstellt,
> das möchte ich nicht mehr. Die Frage "ist versehentlich etwas ungeprüftes
> dabei" kann von mir unabhängig ein Agent machen. Also 3.

Vollständige Prompt-Kette in
[`dec-0019-002-provenance.txt`](dec-0019-002-provenance.txt).

---

### `DEC-0019-003` — Later S-Core curation exports are self-contained and locally link-closed

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-25T06:09:44Z`
- **Deciding identity:** `agent:tasha:0019-13:20260825T060255Z-702c7697`
- **Role:** `Implementierer`
- **Authority reference:** `task:0019-13`
- **Subject:** The assembled publication root and blocking local-link validation contract for later releases of the S-Core v0.6.0 unvalidated-curation subtree, without changing the already published digest-bound tree.
- **Decision:** The assembled publication root is the strict `eclipse-score-v0.6.0-curation-review/` export directory. A later candidate packages the canonical `review_request.js` at that root and a deterministic local `curation-report.html` replacement at that root; record pages reference the packaged script within the root, and `participate.html` references the local report. Validation examines every local `href` and `src` in every generated HTML page against that exact root and refuses missing files, non-regular targets, absolute or scheme-like local paths, and any path escape. No defect-specific missing-link allowlist remains. The decision authorizes only local candidate preparation under Task `0019-13`; implementation begins only after a separate supporting scope review by a management-instantiated Architect and after this governance record is current on `main`. It does not authorize publication.
- **Technical justification:** The approved narrow publisher copies only the named subtree, so targets outside that subtree are not part of its supported output and cannot be assumed present. Packaging the unchanged canonical browser client and a small local report makes the artifact independently navigable, deterministic, and testable without widening the publisher or silently depending on ambient website layout. Resolving every local link against the actual assembled root removes both known false exceptions and makes a later publication fail before external effect if any required target is absent. The old digest `7c514686ba7241416dbab340b4cad9abe032e2c6150e807b302efac363d08283` remains immutable evidence and is not repaired in place.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
  - `public-release`
- **Considered alternatives:**
  - **ALT-01:** Make the strict subtree self-contained by packaging the canonical review client and a local curation-report replacement, then validate all local links within that root.
    - **Disposition:** `selected`
    - **Reason:** This is the smallest topology that matches the narrow publisher's actual payload, preserves the participation route, and permits exhaustive pre-release validation without ambient dependencies.
  - **ALT-02:** Keep the links escaping the subtree and define the complete website root as the validator's assembled root.
    - **Disposition:** `rejected`
    - **Reason:** The bounded publication mechanism copies only the subtree, so a larger assumed root would validate files that are not carried by the approved payload and would reproduce the shipped defect class.
  - **ALT-03:** Remove the curation-report link and browser review-request script from the generated pages.
    - **Disposition:** `rejected`
    - **Reason:** This would avoid dead targets by deleting the established user participation route, weakening the existing curation contract instead of repairing its packaging.
- **Consequences:**
  - **CON-01:** Any later S-Core curation candidate contains two additional root files, both included in deterministic inventory, digest, repeat-generation, and whole-population link evidence.
  - **CON-02:** The strict validator may block a later release candidate when any local `href` or `src` is missing, escapes the root, resolves to a non-regular target, or is removed after generation; green validation is not release authorization.
  - **CON-03:** The canonical IDs, version IDs, unvalidated markers, status/history, provenance, candidate counts, manifests, curator boundary, review-request authentication semantics, and narrow publisher authority remain unchanged.
  - **CON-04:** The already published 2,248-file tree and its approved digest are retained byte-for-byte as historical evidence; this decision creates no special publication and has no external effect by itself.
  - **CON-05:** Rollback before a later authorized publication is the ordinary removal of the Task `0019-13` candidate commit; after publication, supersession requires a new reviewed candidate and cannot relabel the old digest.
- **Affected work units:**
  - `task:0019-13`
  - `repository:autodocs`
  - `external:autodocs-github-pages-eclipse-score-curation`
- **Affected gates:**
  - `validation:_src/tools/prepare_score_curation_export.py`
  - `release:eclipse-score-curation-later-release`
- **Review participation:** `none`
- **No-review reason:** The mandatory distinct Architect scope review is requested separately before any gate-scope implementation; no second-instance response existed when this pre-implementation decision record was created, so no support is inferred.
- **Waiver:** `none`

---

### `DEC-0019-004` — Unchanged review client resolves a packaged local process report

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-25T06:13:12Z`
- **Deciding identity:** `agent:tasha:0019-13:20260825T060255Z-702c7697`
- **Role:** `Implementierer`
- **Authority reference:** `task:0019-13`
- **Subject:** Supersession of the incomplete `DEC-0019-003` topology after discovery that the canonical review client dynamically creates an additional local `process.html` dependency on every record page.
- **Decision:** `DEC-0019-003` is not implemented. The assembled publication root remains the strict `eclipse-score-v0.6.0-curation-review/` export directory. A later candidate packages the canonical `review_request.js` byte-for-byte at that root; relocates the generated view stylesheet from `assets/view.css` to root `style.css`; and packages root `process.html` as the deliberately local curation/process report, including stable `flag-for-review-protocol` and `storage-and-privacy` anchors. Record pages reference `../style.css` and `../review_request.js`, so the unchanged client's existing `style.css` discovery resolves its dynamic process-document links to `../process.html`; `participate.html` also references `process.html`. Validation examines every static local `href` and `src` in every generated HTML page against that exact root, while an interactive browser regression opens the review dialog and proves both dynamically created process-document links resolve inside the same root. Missing files, non-regular targets, absolute or scheme-like local paths, path escapes, removed targets, and defect-specific missing-link allowlists are refused. This decision authorizes only local Task `0019-13` candidate preparation after a separate supporting scope review by a management-instantiated Architect and after the effective governance record is current on `main`; it does not authorize publication.
- **Technical justification:** `review_request.js` computes process-document links by locating the literal suffix `style.css` in the page's stylesheet URL. `DEC-0019-003` retained `assets/view.css`, so the lookup failed and the browser fell back to `process.html` relative to each record page, producing missing `records/process.html` targets even though all initial HTML links were closed. Relocating the existing generated CSS payload to root `style.css` satisfies the unchanged client's established discovery rule; a single root `process.html` then serves both the explicit participation link and the two dynamic help/privacy anchors. This closes the actual browser flow without forking authentication, token, package, or GitHub-submission logic. The approved old digest remains immutable evidence and no current publication occurs.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
  - `security-or-credential-boundary`
  - `public-release`
- **Considered alternatives:**
  - **ALT-01:** Package the unchanged root review client and root process report, and relocate the generated stylesheet payload to root `style.css` so existing client link discovery resolves the report.
    - **Disposition:** `selected`
    - **Reason:** This closes static and dynamic local links with one shared process target while leaving the credential, identity, export, and submission client byte-identical to the established implementation.
  - **ALT-02:** Implement `DEC-0019-003` with `assets/view.css` and a separate root `curation-report.html`.
    - **Disposition:** `rejected`
    - **Reason:** The dynamically created help and privacy links would still resolve to missing `records/process.html`, so the assembled tree would not be link-closed in actual browser use.
  - **ALT-03:** Patch a subtree-specific copy of `review_request.js` to accept a new process-document configuration.
    - **Disposition:** `rejected`
    - **Reason:** Forking the client would create a second credential and GitHub-submission implementation whose security behavior could drift; the established client already supports a safe path convention.
  - **ALT-04:** Validate against the complete ambient website and retain escaping dependencies.
    - **Disposition:** `rejected`
    - **Reason:** The approved bounded publisher carries only the subtree, so ambient files are not guaranteed members of the released payload and cannot satisfy deterministic pre-release validation.
- **Consequences:**
  - **CON-01:** The later strict candidate has two net additional files, root `review_request.js` and root `process.html`; the existing stylesheet payload changes path from `assets/view.css` to root `style.css` without changing bytes.
  - **CON-02:** Whole-population static validation covers all local `href` and `src` values on all generated pages, and interactive validation additionally exercises the review dialog's dynamically created help and privacy links.
  - **CON-03:** Any later candidate is blocked before publication if the script, stylesheet, process report, dynamic anchors, or another local target is missing, non-regular, escaping, or removed; green validation remains neither release authorization nor risk acceptance.
  - **CON-04:** The canonical IDs, versions, unvalidated markers, status/history, provenance, counts, manifests, curator boundary, localStorage token keys, explicit GitHub authentication, JSON export, and submission semantics remain unchanged.
  - **CON-05:** The already published 2,248-file tree and digest `7c514686ba7241416dbab340b4cad9abe032e2c6150e807b302efac363d08283` remain byte-for-byte historical evidence; no special publication or external effect follows from this record.
  - **CON-06:** The root process report is deliberately scoped to this unvalidated S-Core candidate subtree; it does not replace repository-wide process documentation or grant a content decision, review identity, publication authority, or Acceptance.
- **Affected work units:**
  - `task:0019-13`
  - `repository:autodocs`
  - `external:autodocs-github-pages-eclipse-score-curation`
- **Affected gates:**
  - `validation:_src/tools/score_curation_views.py`
  - `validation:_src/tools/prepare_score_curation_export.py`
  - `release:eclipse-score-curation-later-release`
- **Review participation:** `none`
- **No-review reason:** The prior Architect assignment was paused immediately after this additional dependency was discovered; a new distinct scope review is required against this superseding record and its exact candidate commit before any product mutation.
- **Waiver:** `none`

#### Independent Architect pre-mutation scope review of `DEC-0019-004`

- **Recorded at:** `2026-08-25T06:16:53Z`
- **Reviewing identity:** `agent:data:architect:0019-13-scope-review:20260825T061653Z-1750c1d4`
- **Role:** `Architekt`
- **Capability class:** `privileged`
- **Authority reference:** Current runtime management-instantiated Architect profile; exact review assignment coordinated by Project Lead Jean-Luc in agent-inbox messages `1787638361760-c7bfac65` and `1787638498090-581e5f47`. The mailbox messages identify the scope but do not themselves create authority.
- **Independence:** Data is distinct from Implementer and deciding identity `agent:tasha:0019-13:20260825T060255Z-702c7697`, did not author the candidate decision or the contemplated product mutation, and acts here only as Architect scope reviewer.
- **Exact reviewed candidate:** `d6953ea7a140b948749858532364c12d62b1491a` (`DEC-0019-004`), parent `40c03c01ae502dd05a6517b2f12f1c109cd67e4d`, governance base `f1631200b22e53ac13b410662048dec2ba47ddd0`.
- **Implementation-contract evidence:** Task/claim baseline `0019-13@1d17e99ea0ef51daae4db97917a2e8d27400496d`; no product mutation is present in the reviewed governance candidate.
- **Verdict:** `supports`

The canonical `cross-item-blast-radius` predicate applies. The exhaustive
validator is declared to block a later release of the strict S-Core curation
subtree, which is a work unit other than the local preparation Task. The named
work-unit set (`task:0019-13`, `repository:autodocs`, and the stable external
curation-release target) and the two producer/validator gates plus later-release
gate cover the actual declared reach without converting this decision into a
repository-wide publication rule.

The strict subtree is the correct assembled root because it is the complete
payload copied by the already bounded publisher. For a record page at
`records/<id>.html`, stylesheet `../style.css` contains the literal suffix used
by the unchanged client, so `processDocHref()` derives prefix `../` and produces
`../process.html#flag-for-review-protocol` and
`../process.html#storage-and-privacy`. Both resolve to the single root
`process.html`; `participate.html` resolves the same root target directly.
Relocating the existing CSS bytes removes `assets/view.css` and adds
`style.css`, while `review_request.js` and `process.html` are the only two net
new files. The topology is therefore narrower than ambient-site validation or
a subtree-specific credential client and preserves the established
participation boundary.

Support is bound to all of the following constraints; deviation invalidates
this review for the changed scope:

1. **Exact client and CSS identity.** Package `review_request.js` byte-for-byte
   from blob `9b239ecf14ed0e628f0091046137209123e189d6` (SHA-256
   `bd6e23ae7454e7dee4daba98a104fa76db0ef9cdf54713ef35569a6c992ef0e2`).
   Relocate, without byte change, the generated `assets/view.css` payload from
   blob `219d8a819bb06bd15e42b3f6f0e03baed7944202` (SHA-256
   `7fa99621f52bac786f6793024eda694f0d54454cd8715bc346292c6c5d0d133c`) to
   root `style.css`. A client or CSS-content change requires fresh scope and
   security analysis; it is not covered by “canonical” as an unpinned moving
   label.
2. **One exact root.** Generate and validate only
   `eclipse-score-v0.6.0-curation-review/` as the assembled root. Every carried
   regular file, the new script/report, inventory, digests, repeat-generation
   evidence, and validation result bind that same root. No ambient website file
   may satisfy a required local target.
3. **Static URL population and refusal.** Inspect every non-empty `href` and
   `src` on every generated HTML page. Explicit external `https`, `http`, and
   `mailto` references remain external; reject protocol-relative URLs,
   filesystem-absolute paths, unapproved schemes, backslashes/control
   characters, and any browser-normalized local path that escapes the root.
   For a local URL, separate query/fragment from the path, resolve with browser
   URL semantics against its owning page, require the resolved target to remain
   under the exact root, and require a regular non-symlink file. There is no
   defect, filename, page, or count-specific missing-link allowlist.
4. **Dynamic dependencies and anchors.** Root `process.html` contains the
   stable `flag-for-review-protocol` and `storage-and-privacy` anchors, and
   `participate.html` links to `process.html`. A browser regression opens the
   review dialog from a generated record page, extracts both dynamically
   created links, proves that each resolves to root `process.html` and its
   existing anchor, and fails if the script, CSS, process file, either anchor,
   or a participating page reference is removed. Whole-population static
   checking still covers all 2,239 record pages and every other generated HTML
   page; one dynamic interaction case is sufficient only because constraint 1
   pins a single byte-identical client and every record uses the same relative
   depth and stylesheet reference.
5. **Authentication and mutation boundary.** The packaged client retains the
   existing localStorage token key, GitHub verification, JSON-export package,
   and issue-submission code unchanged. Negative browser evidence must prove
   that the unauthenticated route exports only and performs no GitHub write;
   direct submission remains possible only with an explicitly supplied and
   verified token. The subtree does not invent credentials, persist them in
   generated evidence, authenticate a self-declared identity, or claim that a
   fresh standalone subtree provides a new token-acquisition UI.
6. **Content and authority preservation.** Candidate IDs and versions,
   unvalidated markers, `invalid/to-be-confirmed` state, history, provenance,
   record/count/manifest reconciliation, curator boundary, and narrow publisher
   authority remain unchanged. Green local validation is neither Task
   Acceptance, checkpoint/integration approval, release authorization,
   publication approval, nor security/risk acceptance.
7. **Historical immutability and activation.** The already published 2,248-file
   tree and digest
   `7c514686ba7241416dbab340b4cad9abe032e2c6150e807b302efac363d08283`
   remain byte-for-byte historical evidence. `DEC-0019-003` is not implemented.
   The effective decision and this review must first reach authoritative
   `main`; there is no implicit grandfathering of a prior candidate or gate
   mutation, and no external effect follows from governance integration.
8. **Recovery.** Before any separately authorized publication, rollback is
   removal/reversion of the later Task-owned candidate commit and restoration
   of its prior local branch state; the approved old tree remains untouched.
   After a publication, correction requires a new reviewed candidate and
   separately authorized superseding release; neither the old digest nor its
   evidence may be relabeled.

Residual risks remain bounded and are not accepted here: a future client change
could create new dynamic dependencies that static HTML scanning cannot see;
GitHub availability, token validity, browser network policy, and later release
authorization are external to this local gate; and the interactive regression
proves the pinned client's two current dynamic links, not arbitrary future
script behavior. Constraint 1 converts the first risk into an explicit
re-review trigger. The others remain release-time or external-operational
concerns under their existing authorities.

**Governance effect:** This supporting review satisfies only the distinct
Architect pre-mutation scope-review condition for the exact candidate above,
once both decision and review are authoritative on `main`. It does not
implement the gate, accept Task `0019-13`, cross an integration checkpoint,
move a Feature, publish, push, waive a rule, or accept residual risk.

**Advisory implementation/test design:** deterministic whole-population URL
checking is linear in generated links and should use one CPU worker; the focused
negative and interactive browser matrix should remain bounded to roughly
1–5 minutes and below 1 GiB under the existing 2,239-record corpus. Cognitive
demand is medium-high because filesystem and browser URL semantics differ.
Uncertainty is low for the pinned path derivation and medium for browser/network
environment variance; implementation risk is medium because the route touches
an authentication and future public-release boundary. These are planning
ranges, not acceptance criteria, authority, or risk approval.
