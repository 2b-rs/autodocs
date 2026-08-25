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
