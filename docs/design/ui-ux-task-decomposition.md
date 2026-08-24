# UI/UX task decomposition — bounded work-package proposals

Status: Architect decomposition **proposal**; identifiers intentionally unallocated.
Author: Architect `seven` (Team Voyager), item `ui-ux-task-decomposition-20260824`,
claim `TODO-seven-ui-ux-task-decomposition-20260824.md`.
Inputs (exact): requirements baseline and design corpus at candidate
`ae11b1f8beacaaf4a84998ed6f99b2d5cf3533fd` (carried on handoff tip `40ceb3d2e`),
review evidence `review-ui-ux-requirements-baseline-20260824@9896d9d2073c91a9345b7c1f03cce3ffa817cb01`
(R2, review-ready, no open finding), consumed independently.

Binding rules preserved from the baseline: proposed `F-*` labels and the package
IDs below (`A.1`, `B.T`, …) are **not** allocations; real Feature/Task/DEC IDs are
allocated only on current `main` under the assigned Project Lead. Nothing here
creates implementation, checkpoint-crossing, acceptance, or integration authority.
D-01..D-06 remain unresolved product decisions; no package below silently chooses
one. Every quality gate `Q-01..Q-24` and requirement `RQ-UIUX-001..032` from the
baseline is preserved or strengthened, never weakened.

## 1. Conventions

Each package states: **Scope** (bounded deliverable), **Prereq** (package IDs;
`⊳acc` marks an explicit acceptance-before-start gate, everything else follows the
standing rule that `[x]`/`[w]` opens successor implementation), **Write scope**
(exact path families; disjoint within a phase unless stated), **Validation**
(test kind + evidence family from the quality trace matrix), **Coverage**
(RQ/Q/view binding), **Cap** (capability class per `SANDBOX.md`; `sg` =
sandboxed-grunt via runner queue, `up` = unprivileged direct execution, `op` =
requires operator/management participation for an external effect), **Risk →
recovery**, **Size** (advisory tokens/test-design range derived from roadmap §5;
guidance, not promise).

Path conventions proposed (allocation-neutral): shared machine-readable contracts
under `docs/design/contracts/`; implementation under `_src/ui/<area>/` until F-E
relocates `_src`→`src` (F-E owns that rename repository-wide); per-Feature
evidence under `docs/campaign-evidence/<allocated-feature-id>/` using the
`evidence/...` families named by the quality trace matrix.

Every Feature ends in exactly one terminal integrating Task (`*.T`), proposed
`Integration review: mandatory`, with checkpoint rationale recorded inline. That
satisfies the Feature review floor; intermediate checkpoints are proposed only
where reach or material risk warrants them and are marked explicitly. Checkpoint
placement becomes binding only when an authorized Architect sets the attribute on
the allocated nodes.

## 2. Phase structure and lanes

Topological phases (each lane inside a phase is parallelizable; a package starts
when its named prerequisites — not its phase — are satisfied):

- **P0 — decisions and ratification:** D-01..D-06 routing (Project Lead /
  Management), F-E0 baseline ratification. No UI implementation depends on a
  D-value; packages consume decisions only where marked.
- **P1 — shared foundations (4 parallel lanes):** F-A (identity/routes), F-B
  (design system), F-C (i18n), F-D (projection/security). Interfaces between the
  lanes are the committed contracts of A.1/A.2, B.1, C.1, D.1.
- **P2 — migration:** F-E (after F-E0 acceptance ⊳acc), deliberately isolated:
  **no visual or semantic change travels with filesystem movement.**
- **P3 — read experiences (parallel lanes):** F-F, F-G, F-H, F-J (read-only),
  plus F-I static packages I.1–I.3.
- **P4 — control plane and consumers:** F-K; then F-I.4/I.5 and F-L (both ⊳acc
  on F-D and F-K terminal acceptance); F-M (⊳acc on F-J, F-K plus the separate
  D-04 Management decision); F-N (content lane, independent of P4 control
  packages except locale ops); F-O last.

Deliberate separations demanded by the assignment: repo restructuring (F-E) is
its own phase with byte-identity proof; ticket modernization is split read
projection (F-J) vs. authority cutover (F-M) with a Management decision between;
shared foundations (P1) are the only packages other Features may name as
interface prerequisites; independently parallelizable work is marked per lane.

## 3. Packages per Feature

### F-E0 — Build baseline ratification (predecessor, 2 packages)

- **E0.1 Benchmark harness and measurement.** Scope: fixed command/environment/
  Brotli-11 declaration over the named current corpus on named hardware; ≥5 cold
  + ≥5 warm runs; median/p95 wall+CPU, peak RSS, public bytes/file count;
  byte-identity of identical inputs; one-record incremental probe (p95 ≤5 s
  intent). Prereq: none. Write scope: `_src/tools/uiux_build_baseline.py`, tests,
  `evidence/build/baseline-*.json`. Validation: harness self-test + real runs,
  real numbers reported. Coverage: RQ-019; Q-16 first half. Cap: `up` (hardware
  measurement is not queue-schedulable). Risk: unrepresentative corpus/hardware →
  recovery: declaration is part of the evidence; re-measure additively. Size:
  30k–60k.
- **E0.T Ceiling ratification (terminal, Integration review: mandatory).** Scope:
  propose finite numeric ceilings + ≤10% regression headroom from E0.1 evidence;
  independent ratification; record as immutable contract inputs (changes require
  additive decision + impact review). Prereq: E0.1. Write scope:
  `evidence/build/baseline-ratification.json`, decision-record draft. Coverage:
  RQ-019; Q-16 gate anchor. Cap: `sg` + independent reviewer. **Checkpoint
  rationale:** these numbers become an acceptance-before-start gate for F-E and a
  measuring stick for every later build change — cross-item reach by declared
  behavior; a wrong ceiling silently mis-gates all later work. Size: 15k–30k.

### F-A — Canonical identity, routes, traceability core (7 packages)

- **A.1 Typed EntityRef/RelationRef schemas.** Scope: schemas + fixtures for
  every EntityKind incl. duplicate-ID/release, same-SHA-in-four-roles, hostile
  opaque IDs; versioned with explicit compatibility range. Prereq: none. Write
  scope: `docs/design/contracts/entity-ref-v1.json` + fixtures + validator.
  Validation: registry uniqueness, typed chooser, encoding/traversal tests.
  Coverage: RQ-003/-025/-032; Q-01/Q-18 groundwork. Cap: `sg`. Risk: contract
  churn ripples into every consumer → recovery: additive versioning only. Size:
  40k–70k.
- **A.2 Route manifest, alias/redirect/tombstone model.** Scope: canonical route
  registry (119 inventory mappings materializable as `.html`), alias/redirect/
  tombstone semantics, hreflang alternate slots. Prereq: A.1. Write scope:
  `docs/design/contracts/route-manifest-v1.json`, generator under `_src/ui/routes/`.
  Coverage: RQ-003/-025/-029/-032; Q-01/Q-02. Cap: `sg`. Size: 40k–70k.
- **A.3 Resolver, reverse-link indexes, current/history precedence.** Scope:
  identifier→definition resolution incl. typed missing/redacted/ambiguous/
  historical outcomes; reverse indexes; precedence rules current-vs-history.
  Prereq: A.1, A.2. Write scope: `_src/ui/resolve/`. Coverage: RQ-003/-004/-005;
  Q-03/Q-04 groundwork. Cap: `sg`. Size: 50k–90k.
- **A.4 Search grammar and identifier lexicon.** Scope: exact-ID-first grammar,
  tokenization for `ara::`-style and SWS identifiers, locale-stable. Prereq: A.1.
  Write scope: `_src/ui/search-grammar/`. Coverage: RQ-002/-003. Cap: `sg`.
  Size: 25k–50k.
- **A.5 Link crawler.** Scope: crawl every rendered identifier/fragment/locale
  alternate/alias/redirect/tombstone; zero-silent-dead-links report;
  `evidence/routes/link-crawl.json`. **Gate-scope flag:** wiring the crawler as a
  blocking check into shared validation meets `cross-item-blast-radius`; the
  wiring (not the tool) requires a conforming `decision-record@v1` + distinct
  Architect scope review **before** activation. Prereq: A.2. Write scope:
  `_src/tools/uiux_link_crawler.py` + tests. Cap: `sg`. Size: 40k–70k.
- **A.6 Provenance traversal and state truth tables.** Scope: golden-path
  fixtures requirement→Task→commit→run→finding→review→Acceptance/integration,
  forward and reverse, with exact REF/digest/relation/rule-version/validity;
  state truth-table fixtures proving no cross-dimension inference. Prereq: A.3.
  Write scope: `evidence/trace/golden-paths.json`, `evidence/state/truth-tables.json`,
  fixture tooling. Coverage: RQ-004/-005/-031; Q-03/Q-04. Cap: `sg`. Size:
  40k–80k.
- **A.T Terminal integration (Integration review: mandatory).** Scope: route
  uniqueness, historical stability, link/failure semantics, representative
  end-to-end traces; Q-01, Q-02 (available locales), Q-18; 119-row mechanical
  route-matrix validation (RQ-032). **Checkpoint rationale:** every other Feature
  consumes these contracts; identity/route defects propagate silently repository-
  wide and are near-irreversible once published routes exist. Prereq: A.1–A.6.
  Cap: privileged Integrator. Size: 30k–60k.

### F-B — Design system, shell, accessibility foundation (6 packages)

- **B.1 Tokens, themes, typography, iconography.** Scope: implement
  `ui-ux-design-tokens.md`; light/dark; density tokens for **both** comfortable
  and compact (D-01 chooses only the default — both modes ship). Prereq: none.
  Write scope: `_src/ui/tokens/`. Coverage: RQ-015; Q-12. Cap: `sg`. Size:
  30k–60k.
- **B.2 Shell, navigation, record header, typed status.** Scope: application
  shell, Explore/Trace/Curate/Review/Work/Reports navigation, breadcrumbs,
  record-identity header, typed status vocabulary (no color-only meaning).
  Prereq: B.1; A.2 for route slots. Write scope: `_src/ui/shell/`. Coverage:
  RQ-002/-015; SYS family. Cap: `sg`. Size: 50k–90k.
- **B.3 Core components.** Scope: tables to 10,000 rows (pagination first,
  virtualization never sole carrier), tabs, forms, timelines, diffs, full state
  set of RQ-031. Prereq: B.1. Write scope: `_src/ui/components/`. Coverage:
  RQ-018/-031; Q-15. Cap: `sg`. Size: 60k–110k.
- **B.4 Graph-alternative tables, print/export components.** Scope: accessible
  table equivalence pattern for graphs; print/export retaining ID/ref/digest/
  as-of/classification/signature (Q-20 fixtures incl. Arabic/long-ID). Prereq:
  B.3. Write scope: `_src/ui/components/`. Coverage: RQ-024; Q-20. Cap: `sg`.
  Size: 30k–60k.
- **B.5 Fixture gallery and state-fixture manifest.** Scope: Storybook-like
  gallery without production dependency; machine-readable state-fixture manifest
  covering all applicable RQ-031 states for all 119 IDs (or explicit rationale
  per omission) — the carrier artifact later terminals validate against. Prereq:
  B.2, B.3. Write scope: `_src/ui/gallery/`, `docs/design/contracts/state-fixtures-v1.json`.
  Coverage: RQ-031/-032. Cap: `sg`. Size: 40k–70k.
- **B.T Terminal integration (Integration review: mandatory).** Scope: WCAG 2.2
  AA automated+manual matrix (320 px/200%/400%/keyboard/forced-colors/reduced
  motion/NVDA/VoiceOver), visual regression across component×state×theme×density
  ×viewport, no-JS render of shell/components, print/export. Q-09/Q-10/Q-12/
  Q-15/Q-20. **Checkpoint rationale:** every UI Feature inherits these
  components; an accessibility or state-semantics defect here is a defect in all
  119 views at once. Prereq: B.1–B.5. Cap: `up` (manual AT matrix) + privileged
  Integrator. Size: 40k–80k.

### F-C — i18n, RTL, localization operations (5 packages)

- **C.1 ICU catalog, locale registry, glossary, fallback provenance.** Scope: 11
  locales (de en es pt fr ru ar hi ko zh nl) + pseudo-expansion + pseudo-RTL
  registry; explicit fallback with provenance; identifiers/enums never translate.
  Prereq: none. Write scope: `_src/ui/i18n/`, `docs/design/contracts/locale-registry-v1.json`.
  Coverage: RQ-014; Q-11. Cap: `sg`. Size: 30k–60k.
- **C.2 Bidi isolation and font strategy.** Scope: bidi isolation for mixed
  Arabic+SHA/path/SWS content, copy/paste fidelity; CJK/Devanagari/Arabic font
  loading within performance budgets. Prereq: C.1, B.1. Write scope:
  `_src/ui/i18n/`, token additions. Coverage: RQ-014/-016. Cap: `sg`. Size:
  25k–50k.
- **C.3 Exact-entity locale switching and alternates.** Scope: locale switch
  preserves entity/version/anchor/filter; hreflang alternates emitted from the
  route manifest. Prereq: C.1, A.2. Write scope: `_src/ui/i18n/`. Coverage:
  RQ-014; Q-02. Cap: `sg`. Size: 25k–45k.
- **C.4 Localization operations views.** Scope: coverage dashboard, translation
  queue, segment review (read/export plane; AD-01..04 views). Prereq: C.1, B.3.
  Write scope: `_src/ui/l10n-ops/`. Coverage: RQ-014/-031; AD-01..04. Cap: `sg`.
  Size: 30k–60k.
- **C.T Terminal integration (Integration review: mandatory).** Scope: eleven-
  locale + pseudo-locale visual, functional, accessibility, and link
  qualification; Q-11 and Q-02 locale halves. **Checkpoint rationale:** locale
  defects (bidi corruption, wrong-entity switching, silent fallback) are
  user-visible corruption of the whole surface and are cheap to catch here,
  expensive everywhere else. Prereq: C.1–C.4. Cap: privileged Integrator. Size:
  30k–60k.

### F-D — Classified projection and frontend security (6 packages)

- **D.1 Projection schemas and classification model.** Scope: public/internal/
  restricted projection schemas; unknown classification **fails closed**;
  implements the RQ-021 safe constraint while leaving the D-06 visibility policy
  open. Prereq: none. Write scope: `docs/design/contracts/projection-v1.json`,
  `_src/ui/projection/`. Coverage: RQ-021/-025; Q-05/Q-18. Cap: `sg`. Size:
  40k–70k.
- **D.2 Redaction and negative artifact scanner.** Scope: secret/PII/path/
  identifier/hash/route/count scanner over actual public artifacts; build-failure
  mode. **Gate-scope flag:** activation as a blocking publication gate meets
  `cross-item-blast-radius` → `decision-record@v1` + distinct Architect scope
  review before the gate mutation; the scanner itself may land first as a
  non-blocking report. Prereq: D.1. Write scope: `_src/tools/uiux_projection_scan.py`
  + tests. Coverage: RQ-021; Q-05. Cap: `sg`. Size: 40k–70k.
- **D.3 Safe DOM, sanitizer, CSP and headers.** Scope: sanitizer/DOM/URL
  handling, CSP report-only → enforcing path, frame/object/base restrictions.
  Prereq: none (contract-level); B.2 for shell wiring. Write scope:
  `_src/ui/security/`. Coverage: RQ-022; Q-08. Cap: `sg`. Size: 30k–60k.
- **D.4 SBOM, integrity, dependency evidence.** Scope: SBOM, license, integrity,
  vulnerability checks as auditable evidence. Prereq: none. Write scope:
  `_src/tools/uiux_sbom.py`, evidence. Coverage: RQ-022; Q-08. Cap: `sg`. Size:
  20k–40k.
- **D.5 Privacy-safe telemetry contract.** Scope: telemetry contract proving
  incapability of capturing names/rationale/evidence/tokens/full URLs/raw
  queries/restricted entities; consent/DNT/retention/deletion behavior bound to
  D-05; **collection remains disabled wherever D-05 is unresolved.** Prereq:
  D.1. Write scope: `docs/design/contracts/telemetry-v1.json`, `_src/ui/telemetry/`.
  Coverage: RQ-023; Q-19. Cap: `sg`. Size: 25k–45k.
- **D.T Terminal integration (Integration review: mandatory — Security and
  privacy checkpoint).** Scope: adversarial publication matrix (restricted bytes,
  hidden routes/hashes/counts, cache/autocomplete/backlink/error/export/telemetry
  channels), Q-05/Q-08/Q-19; independent Security review named in the
  contract. **Checkpoint rationale:** security/privacy boundary with
  irreversible public disclosure as failure mode — the strongest class the
  contract names; guards fail silently. Prereq: D.1–D.5. Cap: privileged
  Integrator + Security reviewer distinct from implementers. Size: 40k–80k.

### F-E — Directory and deterministic build migration (5 packages; ⊳acc F-E0)

Start gate: **F-E0 accepted** (acceptance-before-start; E0.T evidence is a
contract input). Cross-item note: F-E changes the build/validation path of every
later work unit → a Feature-level `decision-record@v1` + distinct Architect scope
review precede the first gate-affecting mutation.

- **E.1 Source relocation `_src`→`src`.** Scope: relocation with compatibility
  shims, path-map manifest, byte-identical outputs proven against pre-move
  build; underscore removal for source dirs. No output-semantics change. Prereq:
  F-E0 ⊳acc. Write scope: repository-wide rename (exact path map in the Task
  contract), shims. Coverage: RQ-026/-029; Q-16. Cap: `up` (repo-wide Git
  surgery). Risk: silent path loss → recovery: pre/post manifest diff, preserved
  tag before removal. Size: 50k–90k.
- **E.2 Generated output relocation → `www/` with legacy redirects.** Scope:
  generated root HTML/assets to `www/`; route parity via A.2 manifest; legacy
  redirects; old paths removed only after full link-crawl parity. Prereq: E.1,
  A.2. Write scope: build config, `www/` output, redirect map. Coverage:
  RQ-029; Q-02/Q-13. Cap: `up`. Size: 40k–80k.
- **E.3 Deterministic incremental build engine.** Scope: authored/source/
  generated separation, capability-island bundling, deterministic+incremental
  build, immutable asset/cache manifests; measured against E0.T ceilings.
  Prereq: E.1. Write scope: `src/build/`. Coverage: RQ-016/-019/-026; Q-13/Q-16.
  Cap: `up` (benchmark reruns). Size: 60k–120k.
- **E.4 Atomic release manifest and rollback.** Scope: immutable release
  manifest of routes/assets/schemas/projections/source refs; atomic swap;
  interrupted-release recovery; prior-manifest rollback. Prereq: E.3. Write
  scope: `src/build/release/`. Coverage: RQ-025/-029; Q-17. Cap: `sg`. Size:
  30k–60k.
- **E.T Terminal integration (Integration review: mandatory).** Scope: path
  parity, byte reproducibility, full link crawl, performance budgets vs. E0.T
  ceilings, deployment + rollback rehearsal; Q-13/Q-16/Q-17 plus Q-02 crawl.
  **Checkpoint rationale:** hard-to-reverse repository-wide migration touching
  the public deploy path; a defect strands every subsequent Feature on a broken
  build or breaks published routes. Prereq: E.1–E.4. Cap: privileged Integrator.
  Size: 40k–80k.

### F-F — Documentation universes and discovery (6 packages)

- **F.1 Universe landing/catalog/detail templates.** Scope: template family
  using AUTOSAR Adaptive as reference corpus; sources and requirement views.
  Prereq: A.T, B.T (accepted foundations), C.1. Write scope: `_src/ui/universes/`.
  Coverage: RQ-001/-002; KN family. Cap: `sg`. Size: 50k–90k.
- **F.2 S-Core peer elevation.** Scope: S-Core landing/catalog/detail at equal
  hierarchy — no separate product shell. Prereq: F.1. Write scope:
  `_src/ui/universes/score/`. Coverage: RQ-001; KN. Cap: `sg`. Size: 30k–60k.
- **F.3 Entity-family pages.** Scope: API/type/service/member pages, diagrams,
  source traces. Prereq: F.1, A.3. Write scope: `_src/ui/universes/`. Coverage:
  RQ-003/-004; KN. Cap: `sg`. Size: 50k–100k.
- **F.4 Version/diff/comparison views.** Scope: version pinning, diffs,
  cross-version comparison with current/history precedence. Prereq: F.3, A.3.
  Write scope: `_src/ui/universes/`. Coverage: RQ-005; KN. Cap: `sg`. Size:
  30k–60k.
- **F.5 Global search and saved views.** Scope: exact-ID-first search over all
  universes (A.4 grammar), saved views (user-local). Prereq: A.4, F.1. Write
  scope: `_src/ui/search/`. Coverage: RQ-002; SYS search views. Cap: `sg`.
  Size: 40k–70k.
- **F.T Terminal integration (Integration review: mandatory).** Scope:
  representative corpus review per universe, entity family, locale, largest/
  smallest page, source trace; Q-09/Q-13 consumer halves; Q-02 crawl over the
  read surface. **Checkpoint rationale:** Feature review floor; primary public
  surface at content scale — link/semantics defects here are the product's
  visible quality. Prereq: F.1–F.5. Cap: privileged Integrator. Size: 40k–70k.

### F-G — Traceability and scalable graph experience (4 packages)

- **G.1 Indexes and relation views (tables first).** Scope: adjacency/coverage
  indexes; relationship/provenance/dependency/coverage/conflict views as
  accessible tables. Prereq: A.T, B.T. Write scope: `_src/ui/trace/`. Coverage:
  RQ-004/-018; TR family; Q-03/Q-15. Cap: `sg`. Size: 50k–90k.
- **G.2 Progressive graph worker.** Scope: worker-based rendering, clustering/
  aggregation beyond 500 nodes/1,000 edges, deep-linked viewport, cancellation
  and leak checks, interaction budgets. Prereq: G.1. Write scope:
  `_src/ui/trace/graph/`. Coverage: RQ-017; Q-14. Cap: `sg`; perf verification
  `up`. Size: 50k–100k.
- **G.3 Degraded and boundary states.** Scope: cycles, missing targets,
  redaction, very-large aggregation-not-omission; table equivalence per view.
  Prereq: G.2. Write scope: `_src/ui/trace/`. Coverage: RQ-031; Q-14. Cap: `sg`.
  Size: 25k–45k.
- **G.T Terminal integration (Integration review: mandatory).** Scope:
  1,000-node/10,000-record qualification, no-JS fallback, accessibility,
  bidirectional-trace golden paths (Q-03 with F-H), Q-14/Q-15. **Checkpoint
  rationale:** Feature review floor; performance/accessibility claims here are
  measured claims other Features cite. Prereq: G.1–G.3. Cap: privileged
  Integrator. Size: 30k–60k.

### F-H — Unified governance and reporting (5 packages)

- **H.1 Governance record views.** Scope: work items, claims, decisions,
  policies, provenance, Acceptance, checkpoints, integration reviews/verdicts,
  validations, evidence, audit, authority matrix — read projections with strict
  state-dimension separation (truth tables from A.6). Prereq: A.T, B.T. Write
  scope: `_src/ui/governance/`. Coverage: RQ-004/-005; GW family; Q-04. Cap:
  `sg`. Size: 60k–110k.
- **H.2 Report center and shared report identity.** Scope: unified report shell,
  self-identifying baseline/as-of/source/freshness/classification/derivation
  header. Prereq: B.T. Write scope: `_src/ui/reports/`. Coverage: RQ-011; RP
  family. Cap: `sg`. Size: 40k–70k.
- **H.3 Report families.** Scope: current state, build, extraction,
  traceability, curation, review, validation, delivery, i18n, performance,
  accessibility, security, history reports on the shared shell. Prereq: H.2.
  Write scope: `_src/ui/reports/`. Coverage: RQ-011/-018; RP. Cap: `sg`. Size:
  50k–100k.
- **H.4 Derivation precedence and classified publication wiring.** Scope:
  explicit derived-vs-authoritative precedence; classified projection of
  governance content through D.1 contracts; D-06-dependent publication choices
  remain **unwired** until D-06 is decided (default deny). **Gate-scope flag:**
  precedence rules that other units' reports must satisfy meet
  `cross-item-blast-radius` → decision record + distinct Architect review before
  activation. Prereq: H.1, D.T ⊳acc for restricted content. Write scope:
  `_src/ui/governance/`. Coverage: RQ-021; Q-05 consumer. Cap: `sg`. Size:
  30k–60k.
- **H.T Terminal integration (Integration review: mandatory).** Scope:
  prerequisite-closed governance semantics, stale-baseline behavior, append-only
  history rendering, print/export (Q-20), privacy, report parity; Q-03/Q-04
  anchors. **Checkpoint rationale:** authoritative-vs-derived confusion is the
  named Feature risk; a wrong rendering silently misrepresents authority state
  repository-wide. Prereq: H.1–H.4. Cap: privileged Integrator. Size: 40k–70k.

### F-I — Curation, review, public feedback (6 packages)

- **I.1 Browser-PAT retirement.** Scope: remove/disable the current browser-PAT
  flow **before any redesigned page ships**; safe-export fallback documented.
  **Gate-scope flag:** removes an existing capability others may use →
  `decision-record@v1` + distinct Architect review before the removal mutation.
  Prereq: none (deliberately early). Write scope: exact current PAT-flow files
  (pinned in the Task contract). Coverage: RQ-020 (negative half); Q-06. Cap:
  `sg`. Risk: workflow loss → recovery: export-only path + revert plan. Size:
  20k–40k.
- **I.2 Static curation views.** Scope: queues, source comparison, diff/
  proposal, discussion read, archive — static read + local export only. Prereq:
  B.T, A.T. Write scope: `_src/ui/curation/`. Coverage: RQ-006; CU family;
  Q-21 static half. Cap: `sg`. Size: 50k–90k.
- **I.3 Static review/feedback views.** Scope: review requests/protocols/
  findings/decisions/re-review/receipts as read projections against immutable
  candidates with exact digests; public-feedback read views. Prereq: B.T, A.T.
  Write scope: `_src/ui/review/`. Coverage: RQ-007; RV family. Cap: `sg`. Size:
  50k–90k.
- **I.4 Authenticated submission integration.** Scope: submission/receipt/
  recovery through the F-K action framework; transport-not-acceptance semantics;
  local-ready ≠ submitted. Prereq: **F-D.T and F-K.T accepted ⊳acc** (roadmap
  rule), I.2, I.3. Write scope: `_src/ui/curation/`, `_src/ui/review/`.
  Coverage: RQ-006/-007/-020; Q-21/Q-06/Q-07 consumer. Cap: `sg` + `up` E2E.
  Size: 60k–110k.
- **I.5 Public-feedback identity modes.** Scope: anonymous/pseudonymous/
  authenticated modes as **configuration**, policy chosen by D-03 — contract
  keeps all modes testable, ships none as default until D-03. Prereq: I.4.
  Write scope: `_src/ui/review/feedback/`. Coverage: RQ-007; D-03 consumer.
  Cap: `sg`. Size: 25k–45k.
- **I.T Terminal integration (Integration review: mandatory — Security/QA/UX).**
  Scope: authentication, authority, concurrency, failure recovery,
  accessibility, privacy; Q-21 full; offline/stale/partial-transport fixtures.
  **Checkpoint rationale:** credentials, personal data, and external GitHub
  effects meet the irreversible-external-effect class; failure modes are silent
  authority confusion. Prereq: I.1–I.5. Cap: privileged Integrator + Security
  reviewer. Size: 40k–80k.

### F-J — DHTML ticket projection (5 packages)

- **J.1 Typed backlog adapter and parity report.** Scope: adapter TODO/claims/
  issues → typed ticket model, read-only; parity report vs. authoritative files;
  conflict/expired/takeover/cycle fixtures. Prereq: A.1. Write scope:
  `_src/ui/tickets/adapter/`. Coverage: RQ-008/-028; Q-22 groundwork. Cap: `sg`.
  Size: 40k–70k.
- **J.2 Backlog/list/detail/query/conflict views.** Scope: TK list/detail/query
  views at 10,000-ticket scale. Prereq: J.1, B.T. Write scope:
  `_src/ui/tickets/`. Coverage: RQ-008/-018; TK family; Q-15. Cap: `sg`. Size:
  40k–80k.
- **J.3 Dependency DAG and roadmap views.** Scope: prerequisite DAG with
  accessible table alternative (F-G worker reuse), roadmap view. Prereq: J.2,
  G.2. Write scope: `_src/ui/tickets/`. Coverage: RQ-008; Q-14/Q-22. Cap: `sg`.
  Size: 30k–60k.
- **J.4 Mutation preview and dual-read reconciliation.** Scope: preview of what
  a mutation *would* change + dual-read reconciliation reports; **no mutation
  executes**; D-04 untouched. Prereq: J.2. Write scope: `_src/ui/tickets/`.
  Coverage: RQ-028; Q-22. Cap: `sg`. Size: 30k–50k.
- **J.T Terminal integration (Integration review: mandatory).** Scope: parity
  and failure review; explicit verification that **no authority moved** and the
  projection cannot be mistaken for authority (labeling, truth-table states).
  **Checkpoint rationale:** Feature review floor; the named risk is exactly a
  silent authority shift — the review proves the negative. Prereq: J.1–J.4.
  Cap: privileged Integrator. Size: 30k–50k.

### F-K — Authenticated control plane and notifications (5 packages)

- **K.1 Identity and session architecture.** Scope: provider-neutral BFF with
  short-lived sessions; **no provider token ever reaches the browser**; provider
  selection is a named blocking input (Management/owner supplies GitHub App/
  OAuth or equivalent + credential handles per repository credential rules).
  Prereq: D.1. Write scope: `_src/ui/control-plane/`, `docs/design/contracts/session-v1.json`.
  Coverage: RQ-020; Q-06. Cap: `sg` design + `op` provider registration. Size:
  50k–90k.
- **K.2 Authorization and idempotent action framework.** Scope: role/assignment/
  authority checks server-side; exact-digest preconditions; idempotency keys;
  one-effect semantics; receipts; 409/stale/duplicate handling. Prereq: K.1.
  Write scope: `_src/ui/control-plane/`. Coverage: RQ-020; Q-07. Cap: `sg`.
  Size: 60k–110k.
- **K.3 Notification pipeline.** Scope: email/in-app notifications; consent,
  retention, revocation, retry/dead-letter, bounce handling; privacy-safe
  content rules; delivery observability. D-05-dependent retention values stay
  configuration. Prereq: K.2. Write scope: `_src/ui/notifications/`. Coverage:
  RQ-027; Q-24. Cap: `sg` + `op` for provider. Size: 40k–80k.
- **K.4 Adversarial harness.** Scope: CSRF/fixation/stale-digest/duplicate/
  interrupted/unauthorized/unassigned fixtures as a reusable E2E suite
  (Q-07 evidence producer). Prereq: K.2. Write scope: `_src/ui/control-plane/tests/`.
  Coverage: RQ-020; Q-07. Cap: `up`. Size: 30k–60k.
- **K.T Terminal integration (Integration review: mandatory — Security/QA/
  operator).** Scope: Q-06/Q-07/Q-17/Q-24 full; adversarial concurrency and
  delivery recovery; operator runbook review. **Checkpoint rationale:**
  credential boundary + external side effects; every authenticated Feature
  builds on this — a defect is a repository-wide security incident. Prereq:
  K.1–K.4. Cap: privileged Integrator + Security reviewer. Size: 50k–90k.

### F-L — AI discussion and reviewed submission (4 packages; ⊳acc F-D.T, F-K.T)

- **L.1 Context manifest and inspector.** Scope: exact-context manifest with
  citations, redaction observance, oversized-context handling; visible to the
  user (AI-01..03). Prereq: F-D.T+F-K.T ⊳acc, A.3. Write scope: `_src/ui/ai/`.
  Coverage: RQ-009; Q-23. Cap: `sg`. Size: 40k–80k.
- **L.2 Conversation, proposal, finalization.** Scope: discussion UI, editable
  proposed change/diff, validation plan, idempotent submission through F-K,
  update run, recovery (AI-04..06). Prereq: L.1. Write scope: `_src/ui/ai/`.
  Coverage: RQ-009; Q-23/Q-07 consumer. Cap: `sg`. Size: 50k–100k.
- **L.3 Provenance and authority boundary.** Scope: model/prompt/run metadata
  provenance; proposal-only enforcement (no auto-acceptance path exists in
  code); prompt-injection defenses. Prereq: L.1. Write scope: `_src/ui/ai/`.
  Coverage: RQ-009; Q-23. Cap: `sg`. Size: 30k–60k.
- **L.T Terminal integration (Integration review: mandatory).** Scope:
  hallucination/provenance/privacy/context-boundary review + end-to-end
  submission; Q-23. **Checkpoint rationale:** an AI path that can smuggle
  authority or restricted context is a security boundary; proposal-only must be
  proven, not asserted. Prereq: L.1–L.3. Cap: privileged Integrator. Size:
  40k–70k.

### F-M — Ticket authority cutover (2 packages; ⊳acc F-J.T, F-K.T, D-04)

- **M.1 Cutover mechanics.** Scope: cutover ledger, freeze/dual-write strategy,
  reconciliation, monitoring, rollback **rehearsed before cutover**; no implicit
  grandfathering. Start gate: F-J.T and F-K.T accepted, complete parity
  evidence, **and the separate D-04 Management decision recorded** — three
  independent gates, all ⊳acc. Write scope: `_src/ui/tickets/cutover/`,
  migration tooling. Coverage: RQ-028; Q-22. Cap: `sg` + `op`. Size: 50k–90k.
- **M.T Terminal integration (Integration review: mandatory — privileged
  cutover review).** Scope: Q-22 cutover half; ledger, rollback, reconciliation
  verified against rehearsal evidence. **Checkpoint rationale:** authority
  migration is the definitional hard-to-reverse migration; the review is the
  last gate before the repository's work-item authority moves. Prereq: M.1.
  Cap: privileged Integrator; Management sign-off per D-04. Size: 30k–50k.

### F-N — AUTOSAR Classic import and locale expansion (5 packages)

- **N.1 Source intake and legal provenance.** Scope: licensed/authorized source
  intake with source/version/licence manifest; **blocking external input:**
  access/licensing evidence is supplied by Management/owner, never assumed.
  Prereq: none (content lane). Write scope: intake manifests, `_src/import/`.
  Coverage: RQ-030; Q-03/Q-18. Cap: `sg` + `op` licensing. Size: 40k–80k.
- **N.2 Extraction and entity mapping.** Scope: extraction to A.1 entities,
  coverage/gap reports. Prereq: N.1, A.T. Write scope: `_src/import/classic/`.
  Coverage: RQ-030; KN-09..11, RP-04..06. Cap: `sg`. Size: 60k–120k.
- **N.3 Translation pipeline at scale.** Scope: 11-locale rendering of the
  imported corpus with fallback/provenance via F-C; linguistic review queue
  feeds C.4. Prereq: N.2, C.T. Write scope: `_src/import/classic/i18n/`.
  Coverage: RQ-014/-030; Q-11. Cap: `sg`. Size: 60k–120k.
- **N.4 Performance qualification at corpus scale.** Scope: budgets (Q-13) and
  build ceilings (E0.T) re-verified at the enlarged corpus; regression report.
  Prereq: N.2, E.T. Write scope: evidence only. Coverage: RQ-016/-019. Cap:
  `up`. Size: 25k–50k.
- **N.T Terminal integration (Integration review: mandatory).** Scope: source/
  legal/coverage/i18n/quality review; freshness and review-state provenance.
  **Checkpoint rationale:** legal/licensing exposure plus public content at
  scale; a wrong import publishes unlicensed or wrong content — external,
  hard-to-retract effect. Prereq: N.1–N.4. Cap: privileged Integrator. Size:
  40k–70k.

### F-O — Coding-context assembly and VM research (4 packages)

- **O.1 Research protocol and safety model.** Scope: hypotheses, objective
  evaluation design, VM threat model and isolation profile; explicit
  non-goals (no autonomous release; no completeness claim). Prereq: none
  (design); consumes F-A/F-N outputs when available. Write scope:
  `docs/design/research/`. Coverage: RQ-010; Q-23. Cap: `sg`. Size: 30k–60k.
- **O.2 Context-assembly prototype.** Scope: context manifest + retrieval/
  coverage measurement against S-Core mapping; gap/dependency reporting (AI-07).
  Prereq: O.1, A.T. Write scope: `_src/research/context/`. Coverage: RQ-010.
  Cap: `sg`. Size: 60k–120k.
- **O.3 VM prototype and isolation tests.** Scope: custom-VM prototype, escape/
  isolation tests per threat model, artifact/failure reporting (AI-08). Prereq:
  O.1. Write scope: `_src/research/vm/`. Coverage: RQ-010; Q-23 isolation. Cap:
  `up`, isolated environment only. Size: 60k–120k.
- **O.T Terminal integration (Integration review: mandatory).** Scope: research
  evidence and **safety review before any autonomous code-execution scope
  expands**; evaluation against O.1 criteria. **Checkpoint rationale:**
  the node gates a capability expansion (autonomous execution) — a security
  boundary by definition; research claims must be independently evaluated
  before anything builds on them. Prereq: O.2, O.3. Cap: privileged Integrator +
  Security reviewer. Size: 40k–70k.

## 4. Decision handles D-01..D-06 — consumption map (all preserved unresolved)

| Handle | Consuming packages | Neutrality mechanism until decided |
|---|---|---|
| D-01 density | B.1, B.T | both modes ship and are tested; default is configuration |
| D-02 personality | B.1, H.2 | token/theme layer isolates expressiveness; semantics decision-free |
| D-03 feedback identity | I.5 | all modes implemented as testable configuration; none default |
| D-04 ticket cutover | M.1/M.T start gate | F-M cannot start without the recorded decision |
| D-05 telemetry | D.5, K.3 | collection disabled; retention values configuration |
| D-06 visibility policy | D.1, H.4 | default deny; unknown class fails closed; publication unwired |

No other package reads a D-value. An implementation contract that needs a D-value
before its decision is recorded is mis-scoped and must be split, not resolved by
assumption.

## 5. Cross-item gate scopes requiring `decision-record@v1` + distinct Architect review

Per the canonical `cross-item-blast-radius` predicate, before the first gate
mutation (not before tool authorship): **E0.T** ceiling ratification as F-E start
gate; **A.5** link-crawler wiring into shared validation; **D.2** publication
scanner as blocking gate; **F-E** build/validation path change (Feature-level
record); **H.4** derivation-precedence rules; **I.1** browser-PAT removal
(capability removal); **M.1/M.T** authority cutover (additionally D-04). Terminal
checkpoints themselves become binding through allocated-node Architect flags, not
through this proposal.

## 6. Prerequisite-graph analysis

Cycle check: the package graph is a DAG. Proof sketch: edges point only
P0→P1→P2→P3→P4 or within a Feature from lower package number to terminal; the
only cross-phase back-reference is F-N.3→C.T and F-N.4→E.T (both forward in
phase order) and J.3→G.2 (P3-internal, acyclic). No package names a successor as
prerequisite; no terminal is a prerequisite of its own Feature's packages.
Semantic-deadlock check: every ⊳acc gate (E→E0.T; I.4/L→D.T+K.T; M→J.T+K.T+D-04)
is producible by packages that themselves carry no dependency on the gated
consumer. No Task requires an artifact owned by a downstream Task.

Independent parallel lanes at full staffing: P1 = 4 lanes (A, B, C, D) + E0.1;
P3 = 5 lanes (F, G, H, J, I-static); P4 = K then {I.4+, L} parallel, N parallel
throughout P3/P4 up to N.3/N.4 joins, O.1 anytime, O.2/O.3 late.

## 7. Coverage accounting

- **Features:** F-A..F-O + F-E0 = 16 sections above; 77 packages total, of which
  16 terminal integrating Tasks — exactly one per Feature, each proposed
  `Integration review: mandatory` with recorded rationale (review floor
  satisfied; intermediate checkpoints only where flagged in §5 via decision
  records).
- **Requirements:** all 32 RQ-UIUX IDs appear in package Coverage lines; the
  per-Feature RQ bindings of roadmap §3 are preserved unchanged (RQ-001 F.1/F.2/
  N; RQ-002 B.2/F.5/I; RQ-003 A.1–A.5/F.3; RQ-004 A.6/G/H; RQ-005 A.6/F.4/H.1;
  RQ-006 I.2/I.4; RQ-007 I.3/I.5/K; RQ-008 J; RQ-009 L; RQ-010 O; RQ-011 H.2/
  H.3; RQ-012 B.T + consumer terminals; RQ-013 B.T/C; RQ-014 C/N.3; RQ-015 B.1/
  B.2/H; RQ-016 E.3/N.4/F.T; RQ-017 G.2; RQ-018 B.3/G.1/H.3/J.2; RQ-019 E0/E.3/
  N.4; RQ-020 K/I.1/I.4; RQ-021 D.1/D.2/H.4; RQ-022 D.3/D.4; RQ-023 D.5;
  RQ-024 B.4; RQ-025 A.1/A.2/D.1/E.4; RQ-026 B.5/E.1/E.3; RQ-027 K.3; RQ-028
  J.1/J.4/M; RQ-029 E.1/E.2/E.T; RQ-030 N; RQ-031 B.3/B.5/A.6/C.4/G.3; RQ-032
  A.T mechanical validation + every terminal's family check).
- **Quality gates:** all 24 Q gates are anchored at the terminals named by the
  quality trace matrix (Q-01/02 A.T+C.T; Q-03 G.T/H.T; Q-04 H.T; Q-05/08/19
  D.T; Q-06/07/24 K.T; Q-09/10/12 B.T + consumer terminals; Q-11 C.T +
  consumers; Q-13 E.T/F.T; Q-14 G.T; Q-15 consuming terminals; Q-16 E0.T/E.T;
  Q-17 E.T/K.T; Q-18 A.T/D.T; Q-20 B.T/H.T; Q-21 I.T; Q-22 J.T/M.T; Q-23
  L.T/O.T). No gate is narrowed.
- **Views:** 119 = SYS 12 (B.2/F.5/E/D per route matrix rows) + KN 17 (F, N
  content) + TR 8 (G; TR-08 with A) + CU 10 (I) + RV 12 (I) + GW 20 (H) + RP 15
  (H) + TK 8 (J) + AI 8 (L; AI-07/08 O) + AD 9 (AD-01..04 C.4; AD-05..07 E;
  AD-08 D.5; AD-09 K.3). Row-level authority remains the view→route matrix;
  every terminal validates its family's rows mechanically (RQ-032).

## 8. Recovery strategy (inherited, per package)

Roadmap §4 applies to every package: immutable release manifests, atomic swap,
prior-manifest rollback, dual-read before any cutover, control-plane Features
disablable without removing the static read plane, legacy routes retained until
measured parity justifies separately reviewed removal. Package-specific
recovery is stated where it deviates (E.1 preserved-tag rule, I.1 revert plan,
M.1 rehearsed rollback).

## 9. Genuine decisions blocking allocation (report to the dispatcher)

1. **Feature/Task ID allocation** on current `main` by the Project Lead (this
   proposal deliberately allocates nothing).
2. **D-01..D-06** routing per baseline §5 — D-04 additionally gates F-M start;
   D-06 gates H.4 publication wiring; D-05 gates any telemetry collection.
3. **F-E0 hardware/corpus naming** — the benchmark host and corpus must be
   named by Management/owner; measured numbers cannot be invented.
4. **Identity-provider selection and credential handles for F-K** (GitHub App/
   OAuth or equivalent) — owner-supplied, with scope/expiry/revocation route.
5. **AUTOSAR Classic licensing/access evidence for F-N** — legal input, not an
   agent decision.
6. **Staffing/capability assignment** — packages marked `up`/`op` need direct
   execution or operator participation; the deterministic matcher and dispatcher
   assignment happen at allocation, not here.

## 10. Validation of this proposal

Mechanical self-checks run on this document (results in the claim progress log):
16 Feature sections; 77 package IDs unique; 16 terminals, one per Feature; all
32 RQ IDs and 24 Q IDs referenced; D-01..D-06 each mapped with a neutrality
mechanism; prerequisite references resolve to defined package IDs; no forward
reference from a terminal into its own Feature's packages. Roadmap refinement:
**none required** — all package boundaries were expressible without contradicting
`ui-ux-implementation-roadmap.md`; the roadmap file is deliberately untouched.
