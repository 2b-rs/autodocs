# UI/UX task decomposition — bounded work-package proposals

Status: corrected Architect decomposition **proposal**; identifiers intentionally unallocated.
Original author: Architect `seven` (Team Voyager). Correction: Architect `jadzia`
(Team DeepSpace9), item `ui-ux-task-decomposition-correction-20260824`, based on
independent review `1907ddc344ed775543da9aa6de3bd7be9ea4f752`.
Inputs (exact): requirements baseline and design corpus at candidate
`ae11b1f8beacaaf4a84998ed6f99b2d5cf3533fd` (carried on handoff tip `40ceb3d2e`),
review evidence `review-ui-ux-requirements-baseline-20260824@9896d9d2073c91a9345b7c1f03cce3ffa817cb01`
(R2, review-ready, no open finding), consumed independently. Runner role and
job-control bounds consume controlling amendment
`5d5996d07d8e8be71a99722a12e3afcb1d57919a` (branch tip
`b38c3202d0d40812733204d4386388ff73234599`).

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
(RQ/Q/view binding), **Execution** (all implementers have direct Shell/Git;
`direct` is execution capability, never acceptance or integration authority;
`op` additionally requires operator/management participation for an external
effect), **Risk →
recovery**, **Size** (advisory tokens/test-design range derived from roadmap §5;
guidance, not promise).

`sandboxed-grunt`, runner-queue mutation and `run.sh` requirements are retired
for this future portfolio. A **Runner** remains a Dispatcher-selected process
role only for a Task-ID-bound long-running background job. Its contract is job
control (start/status/cancel/retry/evidence retention) and interfacing with other
agents; it is not a capability class, mutation proxy, acceptance reviewer or
Integrator. Dispatchers select Programmer, Tester or Runner explicitly.

Path conventions proposed (allocation-neutral): shared machine-readable contracts
under `docs/design/contracts/`; implementation under `src/ui/<area>/` only after
F-E relocates `_src`→`src` (F-E owns that rename repository-wide); per-Feature
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
  intent). Prereq: A.4 ⊳acc. Write scope: `src/tools/uiux_build_baseline.py`, tests,
  `evidence/build/baseline-*.json`. Validation: harness self-test + real runs,
  real numbers reported. Coverage: RQ-019; Q-16 first half. Execution: `direct` (hardware
  measurement is not queue-schedulable). Risk: unrepresentative corpus/hardware →
  recovery: declaration is part of the evidence; re-measure additively. Size:
  30k–60k.
- **E0.T Ceiling ratification (terminal, Integration review: mandatory).** Scope:
  propose finite numeric ceilings + ≤10% regression headroom from E0.1 evidence;
  independent ratification; record as immutable contract inputs (changes require
  additive decision + impact review). Prereq: E0.1. Write scope:
  `evidence/build/baseline-ratification.json`, decision-record draft. Coverage:
  RQ-019; Q-16 gate anchor. Execution: `direct` + independent reviewer. **Checkpoint
  rationale:** these numbers become an acceptance-before-start gate for F-E and a
  measuring stick for every later build change — cross-item reach by declared
  behavior; a wrong ceiling silently mis-gates all later work. Size: 15k–30k.

### F-A — Canonical identity, routes, traceability core (7 packages)

- **A.1 Typed EntityRef/RelationRef schemas.** Scope: schemas + fixtures for
  every EntityKind incl. duplicate-ID/release, same-SHA-in-four-roles, hostile
  opaque IDs; versioned with explicit compatibility range. Prereq: none. Write
  scope: `docs/design/contracts/entity-ref-v1.json` + fixtures + validator.
  Validation: registry uniqueness, typed chooser, encoding/traversal tests.
  Coverage: RQ-003/-025/-032; Q-01/Q-18 groundwork. Execution: `direct`. Risk: contract
  churn ripples into every consumer → recovery: additive versioning only. Size:
  40k–70k.
- **A.2 Route manifest, alias/redirect/tombstone model.** Scope: canonical route
  registry (119 inventory mappings materializable as `.html`), alias/redirect/
  tombstone semantics, hreflang alternate slots. Prereq: A.1. Write scope:
  `docs/design/contracts/route-manifest-v1.json`, generator under `src/ui/routes/`.
  Coverage: RQ-003/-025/-029/-032; Q-01/Q-02. Execution: `direct`. Size: 40k–70k.
- **A.3 Resolver, reverse-link indexes, search grammar and precedence.** Scope:
  identifier→definition resolution incl. typed missing/redacted/ambiguous/
  historical outcomes; reverse indexes; exact-ID-first grammar and locale-stable
  tokenization for `ara::`/SWS identifiers; precedence rules current-vs-history.
  Prereq: A.1, A.2. Write scope: `src/ui/resolve/`. Coverage: RQ-003/-004/-005;
  Q-03/Q-04 groundwork. Execution: `direct`. Size: 50k–90k.
- **A.4 Shared operational-role and background-job contract (intermediate,
  Integration review: mandatory).** Scope: Dispatcher selection of
  `programmer`/`tester`/`runner` separately from capability and authority;
  Runner normally maps to `unprivileged` direct execution. Publish a versioned
  Task-ID-bound job record containing job/Task/owner/base/epoch, command/profile
  digest, read/write scopes, resource/time/external/credential declarations;
  monotonic requested→starting→running→terminal/cancelled/timed-out/failed/
  recoverable-interrupted lifecycle; bounded heartbeat/status/log/artifact/result
  digests; cancel, retry/idempotence, handoff, cleanup and recovery contracts.
  Negative controls prohibit intent interpretation, unassigned repair, scope or
  authority expansion, Acceptance, integration, hidden network/credentials and
  silent orphan adoption. Prereq: none. Write scope:
  `docs/design/contracts/operational-role-v1.json`,
  `docs/design/contracts/background-job-v1.json`, fixtures and validator under
  `src/ui/a/a-4/`. Validation: synthetic webtree and nightly-rebuild
  jobs cover start/status/heartbeat/success/failure/cancel/timeout/restart,
  duplicate/wrong/stale/overlap/unbounded/orphan/interrupted negatives and
  Programmer/Tester handoff without authority promotion. Coverage: RQ-004/-005/
  -019/-020/-022/-025/-031; Q-03/Q-04/Q-07/Q-08/Q-16/Q-17/Q-18.
  Execution: `direct`; authority: privileged Integrator plus independent role/
  authority reviewer. Risk: orphan work, unbounded resources, lost evidence or
  authority inheritance → recovery: reject new jobs, inventory exact handles,
  bounded cancellation, retain evidence, restore prior contract only after
  quiescence. **Checkpoint rationale:** repository-wide shared contract consumed
  by every Dispatcher and all background jobs; a silent defect crosses Feature
  start and authority boundaries. Size: 45k–65k.
- **A.5 Link crawler.** Scope: crawl every rendered identifier/fragment/locale
  alternate/alias/redirect/tombstone; zero-silent-dead-links report;
  `evidence/routes/link-crawl.json`. **Gate-scope flag:** wiring the crawler as a
  blocking check into shared validation meets `cross-item-blast-radius`; the
  wiring (not the tool) requires a conforming `decision-record@v1` + distinct
  Architect scope review **before** activation. Prereq: A.2, A.4 ⊳acc. Write scope:
  `src/tools/uiux_link_crawler.py` + tests. Execution: `direct`. Size: 40k–70k.
- **A.6 Provenance traversal and state truth tables.** Scope: golden-path
  fixtures requirement→Task→commit→run→finding→review→Acceptance/integration,
  forward and reverse, with exact REF/digest/relation/rule-version/validity;
  state truth-table fixtures proving no cross-dimension inference. Prereq: A.3.
  Write scope: `evidence/trace/golden-paths.json`, `evidence/state/truth-tables.json`,
  fixture tooling. Coverage: RQ-004/-005/-031; Q-03/Q-04. Execution: `direct`. Size:
  40k–80k.
- **A.T Terminal integration (Integration review: mandatory).** Scope: route
  uniqueness, historical stability, link/failure semantics, representative
  end-to-end traces; Q-01, Q-02 (available locales), Q-18; 119-row mechanical
  route-matrix validation (RQ-032). **Checkpoint rationale:** every other Feature
  consumes these contracts; identity/route defects propagate silently repository-
  wide and are near-irreversible once published routes exist. Prereq: A.1–A.6.
  Execution: `direct`; authority: privileged Integrator. Size: 30k–60k.

### F-B — Design system, shell, accessibility foundation (6 packages)

- **B.1 Tokens, themes, typography, iconography.** Scope: implement
  `ui-ux-design-tokens.md`; light/dark; density tokens for **both** comfortable
  and compact (D-01 chooses only the default — both modes ship). Prereq: none.
  Write scope: `src/ui/tokens/`. Coverage: RQ-015; Q-12. Execution: `direct`. Size:
  30k–60k.
- **B.2 Shell, navigation, record header, typed status.** Scope: application
  shell, Explore/Trace/Curate/Review/Work/Reports navigation, breadcrumbs,
  record-identity header, typed status vocabulary (no color-only meaning).
  Prereq: B.1; A.2 for route slots. Write scope: `src/ui/shell/`. Coverage:
  RQ-002/-015; SYS family. Execution: `direct`. Size: 50k–90k.
- **B.3 Core components.** Scope: tables to 10,000 rows (pagination first,
  virtualization never sole carrier), tabs, forms, timelines, diffs, full state
  set of RQ-031. Prereq: B.1. Write scope: `src/ui/components/`. Coverage:
  RQ-018/-031; Q-15. Execution: `direct`. Size: 60k–110k.
- **B.4 Graph-alternative tables, print/export components.** Scope: accessible
  table equivalence pattern for graphs; print/export retaining ID/ref/digest/
  as-of/classification/signature (Q-20 fixtures incl. Arabic/long-ID). Prereq:
  B.3. Write scope: `src/ui/components/`. Coverage: RQ-024; Q-20. Execution: `direct`.
  Size: 30k–60k.
- **B.5 Fixture gallery and state-fixture manifest.** Scope: Storybook-like
  gallery without production dependency; machine-readable state-fixture manifest
  covering all applicable RQ-031 states for all 119 IDs (or explicit rationale
  per omission) — the carrier artifact later terminals validate against. Prereq:
  B.2, B.3. Write scope: `src/ui/gallery/`, `docs/design/contracts/state-fixtures-v1.json`.
  Coverage: RQ-031/-032. Execution: `direct`. Size: 40k–70k.
- **B.T Terminal integration (Integration review: mandatory).** Scope: WCAG 2.2
  AA automated+manual matrix (320 px/200%/400%/keyboard/forced-colors/reduced
  motion/NVDA/VoiceOver), visual regression across component×state×theme×density
  ×viewport, no-JS render of shell/components, print/export. Q-09/Q-10/Q-12/
  Q-15/Q-20. **Checkpoint rationale:** every UI Feature inherits these
  components; an accessibility or state-semantics defect here is a defect in all
  119 views at once. Prereq: B.1–B.5. Execution: `direct` (manual AT matrix) + privileged
  Integrator. Size: 40k–80k.

### F-C — i18n, RTL, localization operations (5 packages)

- **C.1 ICU catalog, locale registry, glossary, fallback provenance.** Scope: 11
  locales (de en es pt fr ru ar hi ko zh nl) + pseudo-expansion + pseudo-RTL
  registry; explicit fallback with provenance; identifiers/enums never translate.
  Prereq: none. Write scope: `src/ui/i18n/`, `docs/design/contracts/locale-registry-v1.json`.
  Coverage: RQ-014; Q-11. Execution: `direct`. Size: 30k–60k.
- **C.2 Bidi isolation and font strategy.** Scope: bidi isolation for mixed
  Arabic+SHA/path/SWS content, copy/paste fidelity; CJK/Devanagari/Arabic font
  loading within performance budgets. Prereq: C.1, B.1. Write scope:
  `src/ui/i18n/`, token additions. Coverage: RQ-014/-016. Execution: `direct`. Size:
  25k–50k.
- **C.3 Exact-entity locale switching and alternates.** Scope: locale switch
  preserves entity/version/anchor/filter; hreflang alternates emitted from the
  route manifest. Prereq: C.1, A.2. Write scope: `src/ui/i18n/`. Coverage:
  RQ-014; Q-02. Execution: `direct`. Size: 25k–45k.
- **C.4 Localization operations views.** Scope: coverage dashboard, translation
  queue, segment review (read/export plane; AD-01..04 views). Prereq: C.1, B.3.
  Write scope: `src/ui/l10n-ops/`. Coverage: RQ-014/-031; AD-01..04. Execution: `direct`.
  Size: 30k–60k.
- **C.T Terminal integration (Integration review: mandatory).** Scope: eleven-
  locale + pseudo-locale visual, functional, accessibility, and link
  qualification; Q-11 and Q-02 locale halves. **Checkpoint rationale:** locale
  defects (bidi corruption, wrong-entity switching, silent fallback) are
  user-visible corruption of the whole surface and are cheap to catch here,
  expensive everywhere else. Prereq: C.1–C.4. Execution: `direct`; authority: privileged Integrator. Size:
  30k–60k.

### F-D — Classified projection and frontend security (6 packages)

- **D.1 Projection schemas and classification model.** Scope: public/internal/
  restricted projection schemas; unknown classification **fails closed**;
  implements the RQ-021 safe constraint while leaving the D-06 visibility policy
  open. Prereq: none. Write scope: `docs/design/contracts/projection-v1.json`,
  `src/ui/projection/`. Coverage: RQ-021/-025; Q-05/Q-18. Execution: `direct`. Size:
  40k–70k.
- **D.2 Redaction and negative artifact scanner.** Scope: secret/PII/path/
  identifier/hash/route/count scanner over actual public artifacts; build-failure
  mode. **Gate-scope flag:** activation as a blocking publication gate meets
  `cross-item-blast-radius` → `decision-record@v1` + distinct Architect scope
  review before the gate mutation; the scanner itself may land first as a
  non-blocking report. Prereq: D.1, A.4 ⊳acc. Write scope: `src/tools/uiux_projection_scan.py`
  + tests. Coverage: RQ-021; Q-05. Execution: `direct`. Size: 40k–70k.
- **D.3 Safe DOM, sanitizer, CSP and headers.** Scope: sanitizer/DOM/URL
  handling, CSP report-only → enforcing path, frame/object/base restrictions.
  Prereq: none (contract-level); B.2 for shell wiring. Write scope:
  `src/ui/security/`. Coverage: RQ-022; Q-08. Execution: `direct`. Size: 30k–60k.
- **D.4 SBOM, integrity, dependency evidence.** Scope: SBOM, license, integrity,
  vulnerability checks as auditable evidence. Prereq: none. Write scope:
  `src/tools/uiux_sbom.py`, evidence. Coverage: RQ-022; Q-08. Execution: `direct`. Size:
  20k–40k.
- **D.5 Privacy-safe telemetry contract.** Scope: telemetry contract proving
  incapability of capturing names/rationale/evidence/tokens/full URLs/raw
  queries/restricted entities; consent/DNT/retention/deletion behavior bound to
  D-05; **collection remains disabled wherever D-05 is unresolved.** Prereq:
  D.1. Write scope: `docs/design/contracts/telemetry-v1.json`, `src/ui/telemetry/`.
  Coverage: RQ-023; Q-19. Execution: `direct`. Size: 25k–45k.
- **D.T Terminal integration (Integration review: mandatory — Security and
  privacy checkpoint).** Scope: adversarial publication matrix (restricted bytes,
  hidden routes/hashes/counts, cache/autocomplete/backlink/error/export/telemetry
  channels), Q-05/Q-08/Q-19; independent Security review named in the
  contract. **Checkpoint rationale:** security/privacy boundary with
  irreversible public disclosure as failure mode — the strongest class the
  contract names; guards fail silently. Prereq: D.1–D.5. Execution: `direct`; authority: privileged
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
  contract), shims. Coverage: RQ-026/-029; Q-16. Execution: `direct` (repo-wide Git
  surgery). Risk: silent path loss → recovery: pre/post manifest diff, preserved
  tag before removal. Size: 50k–90k.
- **E.2 Generated output relocation → `www/` with legacy redirects.** Scope:
  generated root HTML/assets to `www/`; route parity via A.2 manifest; legacy
  redirects; old paths removed only after full link-crawl parity. Prereq: E.1,
  A.2. Write scope: build config, `www/` output, redirect map. Coverage:
  RQ-029; Q-02/Q-13. Execution: `direct`. Size: 40k–80k.
- **E.3 Deterministic incremental build engine.** Scope: authored/source/
  generated separation, capability-island bundling, deterministic+incremental
  build, immutable asset/cache manifests; measured against E0.T ceilings.
  Prereq: E.1, A.4 ⊳acc. Write scope: `src/build/`. Coverage: RQ-016/-019/-026; Q-13/Q-16.
  Execution: `direct` (benchmark reruns). Size: 60k–120k.
- **E.4 Atomic release manifest and rollback.** Scope: immutable release
  manifest of routes/assets/schemas/projections/source refs; atomic swap;
  interrupted-release recovery; prior-manifest rollback. Prereq: E.3. Write
  scope: `src/build/release/`. Coverage: RQ-025/-029; Q-17. Execution: `direct`. Size:
  30k–60k.
- **E.T Terminal integration (Integration review: mandatory).** Scope: path
  parity, byte reproducibility, full link crawl, performance budgets vs. E0.T
  ceilings, deployment + rollback rehearsal; Q-13/Q-16/Q-17 plus Q-02 crawl.
  **Checkpoint rationale:** hard-to-reverse repository-wide migration touching
  the public deploy path; a defect strands every subsequent Feature on a broken
  build or breaks published routes. Prereq: E.1–E.4. Execution: `direct`; authority: privileged Integrator.
  Size: 40k–80k.

### F-F — Documentation universes and discovery (6 packages)

- **F.1 Universe landing/catalog/detail templates.** Scope: template family
  using AUTOSAR Adaptive as reference corpus; sources and requirement views.
  Prereq: A.T, B.T (accepted foundations), C.1. Write scope: `src/ui/universes/`.
  Coverage: RQ-001/-002; KN family. Execution: `direct`. Size: 50k–90k.
- **F.2 S-Core peer elevation.** Scope: S-Core landing/catalog/detail at equal
  hierarchy — no separate product shell. Prereq: F.1. Write scope:
  `src/ui/universes/score/`. Coverage: RQ-001; KN. Execution: `direct`. Size: 30k–60k.
- **F.3 Entity-family pages.** Scope: API/type/service/member pages, diagrams,
  source traces. Prereq: F.1, A.3. Write scope: `src/ui/universes/`. Coverage:
  RQ-003/-004; KN. Execution: `direct`. Size: 50k–100k.
- **F.4 Version/diff/comparison views.** Scope: version pinning, diffs,
  cross-version comparison with current/history precedence. Prereq: F.3, A.3.
  Write scope: `src/ui/universes/`. Coverage: RQ-005; KN. Execution: `direct`. Size:
  30k–60k.
- **F.5 Global search and saved views.** Scope: exact-ID-first search over all
  universes (A.3 grammar), saved views (user-local). Prereq: A.3, F.1. Write
  scope: `src/ui/search/`. Coverage: RQ-002; SYS search views. Execution: `direct`.
  Size: 40k–70k.
- **F.T Terminal integration (Integration review: mandatory).** Scope:
  representative corpus review per universe, entity family, locale, largest/
  smallest page, source trace; Q-09/Q-13 consumer halves; Q-02 crawl over the
  read surface. **Checkpoint rationale:** Feature review floor; primary public
  surface at content scale — link/semantics defects here are the product's
  visible quality. Prereq: F.1–F.5. Execution: `direct`; authority: privileged Integrator. Size: 40k–70k.

### F-G — Traceability and scalable graph experience (4 packages)

- **G.1 Indexes and relation views (tables first).** Scope: adjacency/coverage
  indexes; relationship/provenance/dependency/coverage/conflict views as
  accessible tables. Prereq: A.T, B.T. Write scope: `src/ui/trace/`. Coverage:
  RQ-004/-018; TR family; Q-03/Q-15. Execution: `direct`. Size: 50k–90k.
- **G.2 Progressive graph worker.** Scope: worker-based rendering, clustering/
  aggregation beyond 500 nodes/1,000 edges, deep-linked viewport, cancellation
  and leak checks, interaction budgets. Prereq: G.1, A.4 ⊳acc. Write scope:
  `src/ui/trace/graph/`. Coverage: RQ-017; Q-14. Execution: `direct`; perf verification
  `up`. Size: 50k–100k.
- **G.3 Degraded and boundary states.** Scope: cycles, missing targets,
  redaction, very-large aggregation-not-omission; table equivalence per view.
  Prereq: G.2. Write scope: `src/ui/trace/`. Coverage: RQ-031; Q-14. Execution: `direct`.
  Size: 25k–45k.
- **G.T Terminal integration (Integration review: mandatory).** Scope:
  1,000-node/10,000-record qualification, no-JS fallback, accessibility,
  bidirectional-trace golden paths (Q-03 with F-H), Q-14/Q-15. **Checkpoint
  rationale:** Feature review floor; performance/accessibility claims here are
  measured claims other Features cite. Prereq: G.1–G.3. Execution: `direct`; authority: privileged
  Integrator. Size: 30k–60k.

### F-H — Unified governance and reporting (5 packages)

- **H.1 Governance record views.** Scope: work items, claims, decisions,
  policies, provenance, Acceptance, checkpoints, integration reviews/verdicts,
  validations, evidence, audit, authority matrix — read projections with strict
  state-dimension separation (truth tables from A.6). Prereq: A.T, B.T. Write
  scope: `src/ui/governance/`. Coverage: RQ-004/-005; GW family; Q-04. Execution:
  `direct`. Size: 60k–110k.
- **H.2 Report center and shared report identity.** Scope: unified report shell,
  self-identifying baseline/as-of/source/freshness/classification/derivation
  header. Prereq: B.T. Write scope: `src/ui/reports/`. Coverage: RQ-011; RP
  family. Execution: `direct`. Size: 40k–70k.
- **H.3 Report families.** Scope: current state, build, extraction,
  traceability, curation, review, validation, delivery, i18n, performance,
  accessibility, security, history reports on the shared shell. Prereq: H.2.
  Write scope: `src/ui/reports/`. Coverage: RQ-011/-018; RP. Execution: `direct`. Size:
  50k–100k.
- **H.4 Derivation precedence and classified publication wiring.** Scope:
  explicit derived-vs-authoritative precedence; classified projection of
  governance content through D.1 contracts; D-06-dependent publication choices
  remain **unwired** until D-06 is decided (default deny). **Gate-scope flag:**
  precedence rules that other units' reports must satisfy meet
  `cross-item-blast-radius` → decision record + distinct Architect review before
  activation. Prereq: H.1, D.T ⊳acc for restricted content. Write scope:
  `src/ui/governance/`. Coverage: RQ-021; Q-05 consumer. Execution: `direct`. Size:
  30k–60k.
- **H.T Terminal integration (Integration review: mandatory).** Scope:
  prerequisite-closed governance semantics, stale-baseline behavior, append-only
  history rendering, print/export (Q-20), privacy, report parity; Q-03/Q-04
  anchors. **Checkpoint rationale:** authoritative-vs-derived confusion is the
  named Feature risk; a wrong rendering silently misrepresents authority state
  repository-wide. Prereq: H.1–H.4. Execution: `direct`; authority: privileged Integrator. Size: 40k–70k.

### F-I — Curation, review, public feedback (6 packages)

- **I.1 Browser-PAT retirement.** Scope: remove/disable the current browser-PAT
  flow **before any redesigned page ships**; safe-export fallback documented.
  **Gate-scope flag:** removes an existing capability others may use →
  `decision-record@v1` + distinct Architect review before the removal mutation.
  Prereq: none (deliberately early). Write scope: exact current PAT-flow files
  (pinned in the Task contract). Coverage: RQ-020 (negative half); Q-06. Execution:
  `direct`. Risk: workflow loss → recovery: export-only path + revert plan. Size:
  20k–40k.
- **I.2 Static curation views.** Scope: queues, source comparison, diff/
  proposal, discussion read, archive — static read + local export only. Prereq:
  B.T, A.T. Write scope: `src/ui/curation/`. Coverage: RQ-006; CU family;
  Q-21 static half. Execution: `direct`. Size: 50k–90k.
- **I.3 Static review/feedback views.** Scope: review requests/protocols/
  findings/decisions/re-review/receipts as read projections against immutable
  candidates with exact digests; public-feedback read views. Prereq: B.T, A.T.
  Write scope: `src/ui/review/`. Coverage: RQ-007; RV family. Execution: `direct`. Size:
  50k–90k.
- **I.4 Authenticated submission integration.** Scope: submission/receipt/
  recovery through the F-K action framework; transport-not-acceptance semantics;
  local-ready ≠ submitted. Prereq: **F-D.T and F-K.T accepted ⊳acc** (roadmap
  rule), I.2, I.3. Write scope: `src/ui/curation/`, `src/ui/review/`.
  Coverage: RQ-006/-007/-020; Q-21/Q-06/Q-07 consumer. Execution: `direct` + direct E2E.
  Size: 60k–110k.
- **I.5 Public-feedback identity modes.** Scope: anonymous/pseudonymous/
  authenticated modes as **configuration**, policy chosen by D-03 — contract
  keeps all modes testable, ships none as default until D-03. Prereq: I.4.
  Write scope: `src/ui/review/feedback/`. Coverage: RQ-007; D-03 consumer.
  Execution: `direct`. Size: 25k–45k.
- **I.T Terminal integration (Integration review: mandatory — Security/QA/UX).**
  Scope: authentication, authority, concurrency, failure recovery,
  accessibility, privacy; Q-21 full; offline/stale/partial-transport fixtures.
  **Checkpoint rationale:** credentials, personal data, and external GitHub
  effects meet the irreversible-external-effect class; failure modes are silent
  authority confusion. Prereq: I.1–I.5. Execution: `direct`; authority: privileged Integrator + Security
  reviewer. Size: 40k–80k.

### F-J — DHTML ticket projection (5 packages)

- **J.1 Typed backlog adapter and parity report.** Scope: adapter TODO/claims/
  issues → typed ticket model, read-only; parity report vs. authoritative files;
  conflict/expired/takeover/cycle fixtures. Prereq: A.1. Write scope:
  `src/ui/tickets/adapter/`. Coverage: RQ-008/-028; Q-22 groundwork. Execution: `direct`.
  Size: 40k–70k.
- **J.2 Backlog/list/detail/query/conflict views.** Scope: TK list/detail/query
  views at 10,000-ticket scale. Prereq: J.1, B.T. Write scope:
  `src/ui/tickets/`. Coverage: RQ-008/-018; TK family; Q-15. Execution: `direct`. Size:
  40k–80k.
- **J.3 Dependency DAG and roadmap views.** Scope: prerequisite DAG with
  accessible table alternative (F-G worker reuse), roadmap view. Prereq: J.2,
  G.2. Write scope: `src/ui/tickets/`. Coverage: RQ-008; Q-14/Q-22. Execution: `direct`.
  Size: 30k–60k.
- **J.4 Mutation preview and dual-read reconciliation.** Scope: preview of what
  a mutation *would* change + dual-read reconciliation reports; **no mutation
  executes**; D-04 untouched. Prereq: J.2. Write scope: `src/ui/tickets/`.
  Coverage: RQ-028; Q-22. Execution: `direct`. Size: 30k–50k.
- **J.T Terminal integration (Integration review: mandatory).** Scope: parity
  and failure review; explicit verification that **no authority moved** and the
  projection cannot be mistaken for authority (labeling, truth-table states).
  **Checkpoint rationale:** Feature review floor; the named risk is exactly a
  silent authority shift — the review proves the negative. Prereq: J.1–J.4.
  Execution: `direct`; authority: privileged Integrator. Size: 30k–50k.

### F-K — Authenticated control plane and notifications (5 packages)

- **K.1 Identity and session architecture.** Scope: provider-neutral BFF with
  short-lived sessions; **no provider token ever reaches the browser**; provider
  selection is a named blocking input (Management/owner supplies GitHub App/
  OAuth or equivalent + credential handles per repository credential rules).
  Prereq: D.1. Write scope: `src/ui/control-plane/`, `docs/design/contracts/session-v1.json`.
  Coverage: RQ-020; Q-06. Execution: `direct` design + `op` provider registration. Size:
  50k–90k.
- **K.2 Authorization and idempotent action framework.** Scope: role/assignment/
  authority checks server-side; exact-digest preconditions; idempotency keys;
  one-effect semantics; receipts; 409/stale/duplicate handling. Prereq: K.1.
  Write scope: `src/ui/control-plane/`. Coverage: RQ-020; Q-07. Execution: `direct`.
  Size: 60k–110k.
- **K.3 Notification pipeline.** Scope: email/in-app notifications; consent,
  retention, revocation, retry/dead-letter, bounce handling; privacy-safe
  content rules; delivery observability. D-05-dependent retention values stay
  configuration. Prereq: K.2. Write scope: `src/ui/notifications/`. Coverage:
  RQ-027; Q-24. Execution: `direct` + `op` for provider. Size: 40k–80k.
- **K.4 Adversarial harness.** Scope: CSRF/fixation/stale-digest/duplicate/
  interrupted/unauthorized/unassigned fixtures as a reusable E2E suite
  (Q-07 evidence producer). Prereq: K.2. Write scope: `src/ui/control-plane/tests/`.
  Coverage: RQ-020; Q-07. Execution: `direct`. Size: 30k–60k.
- **K.T Terminal integration (Integration review: mandatory — Security/QA/
  operator).** Scope: Q-06/Q-07/Q-17/Q-24 full; adversarial concurrency and
  delivery recovery; operator runbook review. **Checkpoint rationale:**
  credential boundary + external side effects; every authenticated Feature
  builds on this — a defect is a repository-wide security incident. Prereq:
  K.1–K.4. Execution: `direct`; authority: privileged Integrator + Security reviewer. Size: 50k–90k.

### F-L — AI discussion and reviewed submission (4 packages; ⊳acc F-D.T, F-K.T)

- **L.1 Context manifest and inspector.** Scope: exact-context manifest with
  citations, redaction observance, oversized-context handling; visible to the
  user (AI-01..03). Prereq: F-D.T+F-K.T ⊳acc, A.3. Write scope: `src/ui/ai/`.
  Coverage: RQ-009; Q-23. Execution: `direct`. Size: 40k–80k.
- **L.2 Conversation, proposal, finalization.** Scope: discussion UI, editable
  proposed change/diff, validation plan, idempotent submission through F-K,
  update run, recovery (AI-04..06). Prereq: L.1. Write scope: `src/ui/ai/`.
  Coverage: RQ-009; Q-23/Q-07 consumer. Execution: `direct`. Size: 50k–100k.
- **L.3 Provenance and authority boundary.** Scope: model/prompt/run metadata
  provenance; proposal-only enforcement (no auto-acceptance path exists in
  code); prompt-injection defenses. Prereq: L.1. Write scope: `src/ui/ai/`.
  Coverage: RQ-009; Q-23. Execution: `direct`. Size: 30k–60k.
- **L.T Terminal integration (Integration review: mandatory).** Scope:
  hallucination/provenance/privacy/context-boundary review + end-to-end
  submission; Q-23. **Checkpoint rationale:** an AI path that can smuggle
  authority or restricted context is a security boundary; proposal-only must be
  proven, not asserted. Prereq: L.1–L.3. Execution: `direct`; authority: privileged Integrator. Size:
  40k–70k.

### F-M — Ticket authority cutover (2 packages; ⊳acc F-J.T, F-K.T, D-04)

- **M.1 Cutover mechanics.** Scope: cutover ledger, freeze/dual-write strategy,
  reconciliation, monitoring, rollback **rehearsed before cutover**; no implicit
  grandfathering. Start gate: F-J.T and F-K.T accepted, complete parity
  evidence, **and the separate D-04 Management decision recorded** — three
  independent gates, all ⊳acc. Write scope: `src/ui/tickets/cutover/`,
  migration tooling. Coverage: RQ-028; Q-22. Execution: `direct` + `op`. Size: 50k–90k.
- **M.T Terminal integration (Integration review: mandatory — privileged
  cutover review).** Scope: Q-22 cutover half; ledger, rollback, reconciliation
  verified against rehearsal evidence. **Checkpoint rationale:** authority
  migration is the definitional hard-to-reverse migration; the review is the
  last gate before the repository's work-item authority moves. Prereq: M.1.
  Execution: `direct`; authority: privileged Integrator; Management sign-off per D-04. Size: 30k–50k.

### F-N — AUTOSAR Classic import and locale expansion (5 packages)

- **N.1 Source intake and legal provenance.** Scope: licensed/authorized source
  intake with source/version/licence manifest; **blocking external input:**
  access/licensing evidence is supplied by Management/owner, never assumed.
  Prereq: E.T, A.4 ⊳acc. Write scope: `src/import/classic/n-1/`,
  `docs/design/contracts/classic-intake-v1.json`.
  Coverage: RQ-030; Q-03/Q-18. Execution: `direct` + `op` licensing. Size: 40k–80k.
- **N.2 Extraction and entity mapping.** Scope: extraction to A.1 entities,
  coverage/gap reports. Prereq: N.1, A.T, E.T, A.4 ⊳acc. Write scope:
  `src/import/classic/n-2/`.
  Coverage: RQ-030; KN-09..11, RP-04..06. Execution: `direct`. Size: 60k–120k.
- **N.3 Translation pipeline at scale.** Scope: 11-locale rendering of the
  imported corpus with fallback/provenance via F-C; linguistic review queue
  feeds C.4. Prereq: N.2, C.T, E.T, A.4 ⊳acc. Write scope:
  `src/import/classic/n-3/`.
  Coverage: RQ-014/-030; Q-11. Execution: `direct`. Size: 60k–120k.
- **N.4 Performance qualification at corpus scale.** Scope: budgets (Q-13) and
  build ceilings (E0.T) re-verified at the enlarged corpus; regression report.
  Prereq: N.2, E.T, A.4 ⊳acc. Write scope: evidence only. Coverage: RQ-016/-019. Execution:
  `direct`. Size: 25k–50k.
- **N.T Terminal integration (Integration review: mandatory).** Scope: source/
  legal/coverage/i18n/quality review; freshness and review-state provenance.
  **Checkpoint rationale:** legal/licensing exposure plus public content at
  scale; a wrong import publishes unlicensed or wrong content — external,
  hard-to-retract effect. Prereq: N.1–N.4. Execution: `direct`; authority: privileged Integrator. Size:
  40k–70k.

### F-O — Coding-context assembly and VM research (4 packages)

- **O.1 Research protocol and safety model.** Scope: hypotheses, objective
  evaluation design, VM threat model and isolation profile; explicit
  non-goals (no autonomous release; no completeness claim). Prereq: none
  (design); consumes F-A/F-N outputs when available. Write scope:
  `docs/design/research/`. Coverage: RQ-010; Q-23. Execution: `direct`. Size: 30k–60k.
- **O.2 Context-assembly prototype.** Scope: context manifest + retrieval/
  coverage measurement against S-Core mapping; gap/dependency reporting (AI-07).
  Prereq: O.1, A.T. Write scope: `src/research/context/`. Coverage: RQ-010.
  Execution: `direct`. Size: 60k–120k.
- **O.3 VM prototype and isolation tests.** Scope: custom-VM prototype, escape/
  isolation tests per threat model, artifact/failure reporting (AI-08). Prereq:
  O.1. Write scope: `src/research/vm/`. Coverage: RQ-010; Q-23 isolation. Execution:
  `direct`, isolated environment only. Size: 60k–120k.
- **O.T Terminal integration (Integration review: mandatory).** Scope: research
  evidence and **safety review before any autonomous code-execution scope
  expands**; evaluation against O.1 criteria. **Checkpoint rationale:**
  the node gates a capability expansion (autonomous execution) — a security
  boundary by definition; research claims must be independently evaluated
  before anything builds on them. Prereq: O.2, O.3. Execution: `direct`; authority: privileged Integrator +
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

## 4a. Corrected executable contract overlay (normative)

Every package contract is its bullet plus its row below; this overlay wins on
conflict. Each row already supplies its collision-free implementation, test,
contract and evidence roots. Its committed `*.writes.json` enumerates files
under only those roots and the validator rejects any escape or overlap.

| Package | Exact inputs/output | Collision-free write/evidence manifest | Exact validation command/result | Package-specific recovery | Bounded resources/estimate | Deterministic branch/merge target |
|---|---|---|---|---|---|---|
| E0.1 | exact digests of declared Prereq products; output: Benchmark harness and measurement | `src/baseline/e0-1/**`; `tests/uiux/e0-1/**`; `docs/design/contracts/uiux-packages/e0-1.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/e0-1/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/e0-1/validate.py --package E0.1 --contract docs/design/contracts/uiux-packages/e0-1.json --write-manifest docs/design/contracts/uiux-packages/e0-1.writes.json --evidence docs/campaign-evidence/<feature-id>/e0-1/validation.json` → exit 0 and `uiux-package-result@v1(package=E0.1)` | revert only src/baseline/e0-1/; restore E0.1 predecessor digests; run e0-1 negative/recovery fixture | 15–25 min/1 CPU/2 GiB; 20k–30k; cognitive medium; uncertainty 15%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| E0.T | exact digests of declared Prereq products; output: Ceiling ratification (terminal, Integration review: mandatory) | `tests/uiux/e0-t/{validate.py,fixtures/**}`; `docs/design/contracts/uiux-packages/e0-t.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/e0-t/{candidate-manifest.json,validation.json,recovery.json,resource-usage.json}` | `python3 tests/uiux/e0-t/validate.py --package E0.T --contract docs/design/contracts/uiux-packages/e0-t.json --write-manifest docs/design/contracts/uiux-packages/e0-t.writes.json --evidence docs/campaign-evidence/<feature-id>/e0-t/validation.json` → exit 0 and `uiux-package-result@v1(package=E0.T)` | withhold E0.T merge; restore pinned predecessor manifest; run e0-t rollback rehearsal | 65–75 min/4 CPU/8 GiB; 50k–60k; cognitive high; uncertainty 18%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| A.1 | exact digests of declared Prereq products; output: Typed EntityRef/RelationRef schemas | `src/ui/a/a-1/**`; `tests/uiux/a-1/**`; `docs/design/contracts/uiux-packages/a-1.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/a-1/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/a-1/validate.py --package A.1 --contract docs/design/contracts/uiux-packages/a-1.json --write-manifest docs/design/contracts/uiux-packages/a-1.writes.json --evidence docs/campaign-evidence/<feature-id>/a-1/validation.json` → exit 0 and `uiux-package-result@v1(package=A.1)` | revert only src/ui/a/a-1/; restore A.1 predecessor digests; run a-1 negative/recovery fixture | 25–35 min/3 CPU/6 GiB; 30k–40k; cognitive medium; uncertainty 21%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| A.2 | exact digests of declared Prereq products; output: Route manifest, alias/redirect/tombstone model | `src/ui/a/a-2/**`; `tests/uiux/a-2/**`; `docs/design/contracts/uiux-packages/a-2.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/a-2/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/a-2/validate.py --package A.2 --contract docs/design/contracts/uiux-packages/a-2.json --write-manifest docs/design/contracts/uiux-packages/a-2.writes.json --evidence docs/campaign-evidence/<feature-id>/a-2/validation.json` → exit 0 and `uiux-package-result@v1(package=A.2)` | revert only src/ui/a/a-2/; restore A.2 predecessor digests; run a-2 negative/recovery fixture | 30–40 min/4 CPU/8 GiB; 35k–45k; cognitive medium; uncertainty 24%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| A.3 | exact digests of declared Prereq products; output: Resolver, reverse-link indexes, search grammar and precedence | `src/ui/a/a-3/**`; `tests/uiux/a-3/**`; `docs/design/contracts/uiux-packages/a-3.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/a-3/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/a-3/validate.py --package A.3 --contract docs/design/contracts/uiux-packages/a-3.json --write-manifest docs/design/contracts/uiux-packages/a-3.writes.json --evidence docs/campaign-evidence/<feature-id>/a-3/validation.json` → exit 0 and `uiux-package-result@v1(package=A.3)` | revert only src/ui/a/a-3/; restore A.3 predecessor digests; run a-3 negative/recovery fixture | 35–45 min/1 CPU/2 GiB; 40k–50k; cognitive medium; uncertainty 27%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| A.4 | no predecessor; output: versioned operational-role and Task-ID-bound background-job contracts, fixtures and validator | `src/ui/a/a-4/**`; `tests/uiux/a-4/**`; `docs/design/contracts/uiux-packages/a-4.{json,writes.json}`; `docs/design/contracts/operational-role-v1.{json,schema.json}`; `docs/design/contracts/background-job-v1.{json,schema.json}`; `docs/design/contracts/fixtures/background-job-v1/**`; `docs/campaign-evidence/<feature-id>/a-4/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/a-4/validate.py --package A.4 --contract docs/design/contracts/uiux-packages/a-4.json --write-manifest docs/design/contracts/uiux-packages/a-4.writes.json --evidence docs/campaign-evidence/<feature-id>/a-4/validation.json` → exit 0 and `uiux-package-result@v1(package=A.4)` | revert only src/ui/a/a-4/; restore A.4 predecessor digests; run a-4 negative/recovery fixture | 40–50 min/2 CPU/4 GiB; 45k–55k; cognitive medium; uncertainty 15%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| A.5 | exact digests of declared Prereq products; output: Link crawler | `src/ui/a/a-5/**`; `tests/uiux/a-5/**`; `docs/design/contracts/uiux-packages/a-5.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/a-5/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/a-5/validate.py --package A.5 --contract docs/design/contracts/uiux-packages/a-5.json --write-manifest docs/design/contracts/uiux-packages/a-5.writes.json --evidence docs/campaign-evidence/<feature-id>/a-5/validation.json` → exit 0 and `uiux-package-result@v1(package=A.5)` | revert only src/ui/a/a-5/; restore A.5 predecessor digests; run a-5 negative/recovery fixture | 45–55 min/3 CPU/6 GiB; 20k–30k; cognitive medium; uncertainty 18%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| A.6 | exact digests of declared Prereq products; output: Provenance traversal and state truth tables | `src/ui/a/a-6/**`; `tests/uiux/a-6/**`; `docs/design/contracts/uiux-packages/a-6.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/a-6/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/a-6/validate.py --package A.6 --contract docs/design/contracts/uiux-packages/a-6.json --write-manifest docs/design/contracts/uiux-packages/a-6.writes.json --evidence docs/campaign-evidence/<feature-id>/a-6/validation.json` → exit 0 and `uiux-package-result@v1(package=A.6)` | revert only src/ui/a/a-6/; restore A.6 predecessor digests; run a-6 negative/recovery fixture | 50–60 min/4 CPU/8 GiB; 25k–35k; cognitive medium; uncertainty 21%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| A.T | exact digests of declared Prereq products; output: Terminal integration (Integration review: mandatory) | `tests/uiux/a-t/{validate.py,fixtures/**}`; `docs/design/contracts/uiux-packages/a-t.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/a-t/{candidate-manifest.json,validation.json,recovery.json,resource-usage.json}` | `python3 tests/uiux/a-t/validate.py --package A.T --contract docs/design/contracts/uiux-packages/a-t.json --write-manifest docs/design/contracts/uiux-packages/a-t.writes.json --evidence docs/campaign-evidence/<feature-id>/a-t/validation.json` → exit 0 and `uiux-package-result@v1(package=A.T)` | withhold A.T merge; restore pinned predecessor manifest; run a-t rollback rehearsal | 65–75 min/4 CPU/8 GiB; 55k–65k; cognitive high; uncertainty 24%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| B.1 | exact digests of declared Prereq products; output: Tokens, themes, typography, iconography | `src/ui/b/b-1/**`; `tests/uiux/b-1/**`; `docs/design/contracts/uiux-packages/b-1.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/b-1/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/b-1/validate.py --package B.1 --contract docs/design/contracts/uiux-packages/b-1.json --write-manifest docs/design/contracts/uiux-packages/b-1.writes.json --evidence docs/campaign-evidence/<feature-id>/b-1/validation.json` → exit 0 and `uiux-package-result@v1(package=B.1)` | revert only src/ui/b/b-1/; restore B.1 predecessor digests; run b-1 negative/recovery fixture | 15–25 min/2 CPU/4 GiB; 35k–45k; cognitive medium; uncertainty 27%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| B.2 | exact digests of declared Prereq products; output: Shell, navigation, record header, typed status | `src/ui/b/b-2/**`; `tests/uiux/b-2/**`; `docs/design/contracts/uiux-packages/b-2.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/b-2/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/b-2/validate.py --package B.2 --contract docs/design/contracts/uiux-packages/b-2.json --write-manifest docs/design/contracts/uiux-packages/b-2.writes.json --evidence docs/campaign-evidence/<feature-id>/b-2/validation.json` → exit 0 and `uiux-package-result@v1(package=B.2)` | revert only src/ui/b/b-2/; restore B.2 predecessor digests; run b-2 negative/recovery fixture | 20–30 min/3 CPU/6 GiB; 40k–50k; cognitive medium; uncertainty 15%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| B.3 | exact digests of declared Prereq products; output: Core components | `src/ui/b/b-3/**`; `tests/uiux/b-3/**`; `docs/design/contracts/uiux-packages/b-3.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/b-3/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/b-3/validate.py --package B.3 --contract docs/design/contracts/uiux-packages/b-3.json --write-manifest docs/design/contracts/uiux-packages/b-3.writes.json --evidence docs/campaign-evidence/<feature-id>/b-3/validation.json` → exit 0 and `uiux-package-result@v1(package=B.3)` | revert only src/ui/b/b-3/; restore B.3 predecessor digests; run b-3 negative/recovery fixture | 25–35 min/4 CPU/8 GiB; 45k–55k; cognitive medium; uncertainty 18%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| B.4 | exact digests of declared Prereq products; output: Graph-alternative tables, print/export components | `src/ui/b/b-4/**`; `tests/uiux/b-4/**`; `docs/design/contracts/uiux-packages/b-4.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/b-4/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/b-4/validate.py --package B.4 --contract docs/design/contracts/uiux-packages/b-4.json --write-manifest docs/design/contracts/uiux-packages/b-4.writes.json --evidence docs/campaign-evidence/<feature-id>/b-4/validation.json` → exit 0 and `uiux-package-result@v1(package=B.4)` | revert only src/ui/b/b-4/; restore B.4 predecessor digests; run b-4 negative/recovery fixture | 30–40 min/1 CPU/2 GiB; 20k–30k; cognitive medium; uncertainty 21%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| B.5 | exact digests of declared Prereq products; output: Fixture gallery and state-fixture manifest | `src/ui/b/b-5/**`; `tests/uiux/b-5/**`; `docs/design/contracts/uiux-packages/b-5.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/b-5/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/b-5/validate.py --package B.5 --contract docs/design/contracts/uiux-packages/b-5.json --write-manifest docs/design/contracts/uiux-packages/b-5.writes.json --evidence docs/campaign-evidence/<feature-id>/b-5/validation.json` → exit 0 and `uiux-package-result@v1(package=B.5)` | revert only src/ui/b/b-5/; restore B.5 predecessor digests; run b-5 negative/recovery fixture | 35–45 min/2 CPU/4 GiB; 25k–35k; cognitive medium; uncertainty 24%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| B.T | exact digests of declared Prereq products; output: Terminal integration (Integration review: mandatory) | `tests/uiux/b-t/{validate.py,fixtures/**}`; `docs/design/contracts/uiux-packages/b-t.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/b-t/{candidate-manifest.json,validation.json,recovery.json,resource-usage.json}` | `python3 tests/uiux/b-t/validate.py --package B.T --contract docs/design/contracts/uiux-packages/b-t.json --write-manifest docs/design/contracts/uiux-packages/b-t.writes.json --evidence docs/campaign-evidence/<feature-id>/b-t/validation.json` → exit 0 and `uiux-package-result@v1(package=B.T)` | withhold B.T merge; restore pinned predecessor manifest; run b-t rollback rehearsal | 65–75 min/4 CPU/8 GiB; 55k–65k; cognitive high; uncertainty 27%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| C.1 | exact digests of declared Prereq products; output: ICU catalog, locale registry, glossary, fallback provenance | `src/ui/c/c-1/**`; `tests/uiux/c-1/**`; `docs/design/contracts/uiux-packages/c-1.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/c-1/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/c-1/validate.py --package C.1 --contract docs/design/contracts/uiux-packages/c-1.json --write-manifest docs/design/contracts/uiux-packages/c-1.writes.json --evidence docs/campaign-evidence/<feature-id>/c-1/validation.json` → exit 0 and `uiux-package-result@v1(package=C.1)` | revert only src/ui/c/c-1/; restore C.1 predecessor digests; run c-1 negative/recovery fixture | 45–55 min/4 CPU/8 GiB; 35k–45k; cognitive medium; uncertainty 15%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| C.2 | exact digests of declared Prereq products; output: Bidi isolation and font strategy | `src/ui/c/c-2/**`; `tests/uiux/c-2/**`; `docs/design/contracts/uiux-packages/c-2.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/c-2/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/c-2/validate.py --package C.2 --contract docs/design/contracts/uiux-packages/c-2.json --write-manifest docs/design/contracts/uiux-packages/c-2.writes.json --evidence docs/campaign-evidence/<feature-id>/c-2/validation.json` → exit 0 and `uiux-package-result@v1(package=C.2)` | revert only src/ui/c/c-2/; restore C.2 predecessor digests; run c-2 negative/recovery fixture | 50–60 min/1 CPU/2 GiB; 40k–50k; cognitive medium; uncertainty 18%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| C.3 | exact digests of declared Prereq products; output: Exact-entity locale switching and alternates | `src/ui/c/c-3/**`; `tests/uiux/c-3/**`; `docs/design/contracts/uiux-packages/c-3.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/c-3/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/c-3/validate.py --package C.3 --contract docs/design/contracts/uiux-packages/c-3.json --write-manifest docs/design/contracts/uiux-packages/c-3.writes.json --evidence docs/campaign-evidence/<feature-id>/c-3/validation.json` → exit 0 and `uiux-package-result@v1(package=C.3)` | revert only src/ui/c/c-3/; restore C.3 predecessor digests; run c-3 negative/recovery fixture | 55–65 min/2 CPU/4 GiB; 45k–55k; cognitive medium; uncertainty 21%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| C.4 | exact digests of declared Prereq products; output: Localization operations views | `src/ui/c/c-4/**`; `tests/uiux/c-4/**`; `docs/design/contracts/uiux-packages/c-4.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/c-4/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/c-4/validate.py --package C.4 --contract docs/design/contracts/uiux-packages/c-4.json --write-manifest docs/design/contracts/uiux-packages/c-4.writes.json --evidence docs/campaign-evidence/<feature-id>/c-4/validation.json` → exit 0 and `uiux-package-result@v1(package=C.4)` | revert only src/ui/c/c-4/; restore C.4 predecessor digests; run c-4 negative/recovery fixture | 15–25 min/3 CPU/6 GiB; 20k–30k; cognitive medium; uncertainty 24%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| C.T | exact digests of declared Prereq products; output: Terminal integration (Integration review: mandatory) | `tests/uiux/c-t/{validate.py,fixtures/**}`; `docs/design/contracts/uiux-packages/c-t.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/c-t/{candidate-manifest.json,validation.json,recovery.json,resource-usage.json}` | `python3 tests/uiux/c-t/validate.py --package C.T --contract docs/design/contracts/uiux-packages/c-t.json --write-manifest docs/design/contracts/uiux-packages/c-t.writes.json --evidence docs/campaign-evidence/<feature-id>/c-t/validation.json` → exit 0 and `uiux-package-result@v1(package=C.T)` | withhold C.T merge; restore pinned predecessor manifest; run c-t rollback rehearsal | 65–75 min/4 CPU/8 GiB; 50k–60k; cognitive high; uncertainty 27%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| D.1 | exact digests of declared Prereq products; output: Projection schemas and classification model | `src/ui/d/d-1/**`; `tests/uiux/d-1/**`; `docs/design/contracts/uiux-packages/d-1.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/d-1/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/d-1/validate.py --package D.1 --contract docs/design/contracts/uiux-packages/d-1.json --write-manifest docs/design/contracts/uiux-packages/d-1.writes.json --evidence docs/campaign-evidence/<feature-id>/d-1/validation.json` → exit 0 and `uiux-package-result@v1(package=D.1)` | revert only src/ui/d/d-1/; restore D.1 predecessor digests; run d-1 negative/recovery fixture | 25–35 min/1 CPU/2 GiB; 30k–40k; cognitive medium; uncertainty 15%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| D.2 | exact digests of declared Prereq products; output: Redaction and negative artifact scanner | `src/ui/d/d-2/**`; `tests/uiux/d-2/**`; `docs/design/contracts/uiux-packages/d-2.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/d-2/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/d-2/validate.py --package D.2 --contract docs/design/contracts/uiux-packages/d-2.json --write-manifest docs/design/contracts/uiux-packages/d-2.writes.json --evidence docs/campaign-evidence/<feature-id>/d-2/validation.json` → exit 0 and `uiux-package-result@v1(package=D.2)` | revert only src/ui/d/d-2/; restore D.2 predecessor digests; run d-2 negative/recovery fixture | 30–40 min/2 CPU/4 GiB; 35k–45k; cognitive medium; uncertainty 18%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| D.3 | exact digests of declared Prereq products; output: Safe DOM, sanitizer, CSP and headers | `src/ui/d/d-3/**`; `tests/uiux/d-3/**`; `docs/design/contracts/uiux-packages/d-3.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/d-3/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/d-3/validate.py --package D.3 --contract docs/design/contracts/uiux-packages/d-3.json --write-manifest docs/design/contracts/uiux-packages/d-3.writes.json --evidence docs/campaign-evidence/<feature-id>/d-3/validation.json` → exit 0 and `uiux-package-result@v1(package=D.3)` | revert only src/ui/d/d-3/; restore D.3 predecessor digests; run d-3 negative/recovery fixture | 35–45 min/3 CPU/6 GiB; 40k–50k; cognitive medium; uncertainty 21%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| D.4 | exact digests of declared Prereq products; output: SBOM, integrity, dependency evidence | `src/ui/d/d-4/**`; `tests/uiux/d-4/**`; `docs/design/contracts/uiux-packages/d-4.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/d-4/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/d-4/validate.py --package D.4 --contract docs/design/contracts/uiux-packages/d-4.json --write-manifest docs/design/contracts/uiux-packages/d-4.writes.json --evidence docs/campaign-evidence/<feature-id>/d-4/validation.json` → exit 0 and `uiux-package-result@v1(package=D.4)` | revert only src/ui/d/d-4/; restore D.4 predecessor digests; run d-4 negative/recovery fixture | 40–50 min/4 CPU/8 GiB; 45k–55k; cognitive medium; uncertainty 24%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| D.5 | exact digests of declared Prereq products; output: Privacy-safe telemetry contract | `src/ui/d/d-5/**`; `tests/uiux/d-5/**`; `docs/design/contracts/uiux-packages/d-5.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/d-5/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/d-5/validate.py --package D.5 --contract docs/design/contracts/uiux-packages/d-5.json --write-manifest docs/design/contracts/uiux-packages/d-5.writes.json --evidence docs/campaign-evidence/<feature-id>/d-5/validation.json` → exit 0 and `uiux-package-result@v1(package=D.5)` | revert only src/ui/d/d-5/; restore D.5 predecessor digests; run d-5 negative/recovery fixture | 45–55 min/1 CPU/2 GiB; 20k–30k; cognitive medium; uncertainty 27%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| D.T | exact digests of declared Prereq products; output: D.T bounded product | `tests/uiux/d-t/{validate.py,fixtures/**}`; `docs/design/contracts/uiux-packages/d-t.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/d-t/{candidate-manifest.json,validation.json,recovery.json,resource-usage.json}` | `python3 tests/uiux/d-t/validate.py --package D.T --contract docs/design/contracts/uiux-packages/d-t.json --write-manifest docs/design/contracts/uiux-packages/d-t.writes.json --evidence docs/campaign-evidence/<feature-id>/d-t/validation.json` → exit 0 and `uiux-package-result@v1(package=D.T)` | withhold D.T merge; restore pinned predecessor manifest; run d-t rollback rehearsal | 65–75 min/4 CPU/8 GiB; 50k–60k; cognitive high; uncertainty 15%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| E.1 | exact digests of declared Prereq products; output: Source relocation `_src`→`src` | `src/migration/e-1/**`; `tests/uiux/e-1/**`; `docs/design/contracts/uiux-packages/e-1.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/e-1/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/e-1/validate.py --package E.1 --contract docs/design/contracts/uiux-packages/e-1.json --write-manifest docs/design/contracts/uiux-packages/e-1.writes.json --evidence docs/campaign-evidence/<feature-id>/e-1/validation.json` → exit 0 and `uiux-package-result@v1(package=E.1)` | revert only src/migration/e-1/; restore E.1 predecessor digests; run e-1 negative/recovery fixture | 55–65 min/3 CPU/6 GiB; 30k–40k; cognitive medium; uncertainty 18%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| E.2 | exact digests of declared Prereq products; output: Generated output relocation → `www/` with legacy redirects | `src/migration/e-2/**`; `tests/uiux/e-2/**`; `docs/design/contracts/uiux-packages/e-2.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/e-2/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/e-2/validate.py --package E.2 --contract docs/design/contracts/uiux-packages/e-2.json --write-manifest docs/design/contracts/uiux-packages/e-2.writes.json --evidence docs/campaign-evidence/<feature-id>/e-2/validation.json` → exit 0 and `uiux-package-result@v1(package=E.2)` | revert only src/migration/e-2/; restore E.2 predecessor digests; run e-2 negative/recovery fixture | 15–25 min/4 CPU/8 GiB; 35k–45k; cognitive medium; uncertainty 21%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| E.3 | exact digests of declared Prereq products; output: Deterministic incremental build engine | `src/migration/e-3/**`; `tests/uiux/e-3/**`; `docs/design/contracts/uiux-packages/e-3.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/e-3/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/e-3/validate.py --package E.3 --contract docs/design/contracts/uiux-packages/e-3.json --write-manifest docs/design/contracts/uiux-packages/e-3.writes.json --evidence docs/campaign-evidence/<feature-id>/e-3/validation.json` → exit 0 and `uiux-package-result@v1(package=E.3)` | revert only src/migration/e-3/; restore E.3 predecessor digests; run e-3 negative/recovery fixture | 20–30 min/1 CPU/2 GiB; 40k–50k; cognitive medium; uncertainty 24%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| E.4 | exact digests of declared Prereq products; output: Atomic release manifest and rollback | `src/migration/e-4/**`; `tests/uiux/e-4/**`; `docs/design/contracts/uiux-packages/e-4.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/e-4/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/e-4/validate.py --package E.4 --contract docs/design/contracts/uiux-packages/e-4.json --write-manifest docs/design/contracts/uiux-packages/e-4.writes.json --evidence docs/campaign-evidence/<feature-id>/e-4/validation.json` → exit 0 and `uiux-package-result@v1(package=E.4)` | revert only src/migration/e-4/; restore E.4 predecessor digests; run e-4 negative/recovery fixture | 25–35 min/2 CPU/4 GiB; 45k–55k; cognitive medium; uncertainty 27%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| E.T | exact digests of declared Prereq products; output: Terminal integration (Integration review: mandatory) | `tests/uiux/e-t/{validate.py,fixtures/**}`; `docs/design/contracts/uiux-packages/e-t.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/e-t/{candidate-manifest.json,validation.json,recovery.json,resource-usage.json}` | `python3 tests/uiux/e-t/validate.py --package E.T --contract docs/design/contracts/uiux-packages/e-t.json --write-manifest docs/design/contracts/uiux-packages/e-t.writes.json --evidence docs/campaign-evidence/<feature-id>/e-t/validation.json` → exit 0 and `uiux-package-result@v1(package=E.T)` | withhold E.T merge; restore pinned predecessor manifest; run e-t rollback rehearsal | 65–75 min/4 CPU/8 GiB; 45k–55k; cognitive high; uncertainty 15%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| F.1 | exact digests of declared Prereq products; output: Universe landing/catalog/detail templates | `src/ui/f/f-1/**`; `tests/uiux/f-1/**`; `docs/design/contracts/uiux-packages/f-1.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/f-1/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/f-1/validate.py --package F.1 --contract docs/design/contracts/uiux-packages/f-1.json --write-manifest docs/design/contracts/uiux-packages/f-1.writes.json --evidence docs/campaign-evidence/<feature-id>/f-1/validation.json` → exit 0 and `uiux-package-result@v1(package=F.1)` | revert only src/ui/f/f-1/; restore F.1 predecessor digests; run f-1 negative/recovery fixture | 35–45 min/4 CPU/8 GiB; 25k–35k; cognitive medium; uncertainty 18%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| F.2 | exact digests of declared Prereq products; output: S-Core peer elevation | `src/ui/f/f-2/**`; `tests/uiux/f-2/**`; `docs/design/contracts/uiux-packages/f-2.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/f-2/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/f-2/validate.py --package F.2 --contract docs/design/contracts/uiux-packages/f-2.json --write-manifest docs/design/contracts/uiux-packages/f-2.writes.json --evidence docs/campaign-evidence/<feature-id>/f-2/validation.json` → exit 0 and `uiux-package-result@v1(package=F.2)` | revert only src/ui/f/f-2/; restore F.2 predecessor digests; run f-2 negative/recovery fixture | 40–50 min/1 CPU/2 GiB; 30k–40k; cognitive medium; uncertainty 21%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| F.3 | exact digests of declared Prereq products; output: Entity-family pages | `src/ui/f/f-3/**`; `tests/uiux/f-3/**`; `docs/design/contracts/uiux-packages/f-3.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/f-3/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/f-3/validate.py --package F.3 --contract docs/design/contracts/uiux-packages/f-3.json --write-manifest docs/design/contracts/uiux-packages/f-3.writes.json --evidence docs/campaign-evidence/<feature-id>/f-3/validation.json` → exit 0 and `uiux-package-result@v1(package=F.3)` | revert only src/ui/f/f-3/; restore F.3 predecessor digests; run f-3 negative/recovery fixture | 45–55 min/2 CPU/4 GiB; 35k–45k; cognitive medium; uncertainty 24%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| F.4 | exact digests of declared Prereq products; output: Version/diff/comparison views | `src/ui/f/f-4/**`; `tests/uiux/f-4/**`; `docs/design/contracts/uiux-packages/f-4.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/f-4/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/f-4/validate.py --package F.4 --contract docs/design/contracts/uiux-packages/f-4.json --write-manifest docs/design/contracts/uiux-packages/f-4.writes.json --evidence docs/campaign-evidence/<feature-id>/f-4/validation.json` → exit 0 and `uiux-package-result@v1(package=F.4)` | revert only src/ui/f/f-4/; restore F.4 predecessor digests; run f-4 negative/recovery fixture | 50–60 min/3 CPU/6 GiB; 40k–50k; cognitive medium; uncertainty 27%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| F.5 | exact digests of declared Prereq products; output: Global search and saved views | `src/ui/f/f-5/**`; `tests/uiux/f-5/**`; `docs/design/contracts/uiux-packages/f-5.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/f-5/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/f-5/validate.py --package F.5 --contract docs/design/contracts/uiux-packages/f-5.json --write-manifest docs/design/contracts/uiux-packages/f-5.writes.json --evidence docs/campaign-evidence/<feature-id>/f-5/validation.json` → exit 0 and `uiux-package-result@v1(package=F.5)` | revert only src/ui/f/f-5/; restore F.5 predecessor digests; run f-5 negative/recovery fixture | 55–65 min/4 CPU/8 GiB; 45k–55k; cognitive medium; uncertainty 15%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| F.T | exact digests of declared Prereq products; output: Terminal integration (Integration review: mandatory) | `tests/uiux/f-t/{validate.py,fixtures/**}`; `docs/design/contracts/uiux-packages/f-t.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/f-t/{candidate-manifest.json,validation.json,recovery.json,resource-usage.json}` | `python3 tests/uiux/f-t/validate.py --package F.T --contract docs/design/contracts/uiux-packages/f-t.json --write-manifest docs/design/contracts/uiux-packages/f-t.writes.json --evidence docs/campaign-evidence/<feature-id>/f-t/validation.json` → exit 0 and `uiux-package-result@v1(package=F.T)` | withhold F.T merge; restore pinned predecessor manifest; run f-t rollback rehearsal | 65–75 min/4 CPU/8 GiB; 45k–55k; cognitive high; uncertainty 18%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| G.1 | exact digests of declared Prereq products; output: Indexes and relation views (tables first) | `src/ui/g/g-1/**`; `tests/uiux/g-1/**`; `docs/design/contracts/uiux-packages/g-1.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/g-1/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/g-1/validate.py --package G.1 --contract docs/design/contracts/uiux-packages/g-1.json --write-manifest docs/design/contracts/uiux-packages/g-1.writes.json --evidence docs/campaign-evidence/<feature-id>/g-1/validation.json` → exit 0 and `uiux-package-result@v1(package=G.1)` | revert only src/ui/g/g-1/; restore G.1 predecessor digests; run g-1 negative/recovery fixture | 20–30 min/2 CPU/4 GiB; 25k–35k; cognitive medium; uncertainty 21%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| G.2 | exact digests of declared Prereq products; output: Progressive graph worker | `src/ui/g/g-2/**`; `tests/uiux/g-2/**`; `docs/design/contracts/uiux-packages/g-2.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/g-2/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/g-2/validate.py --package G.2 --contract docs/design/contracts/uiux-packages/g-2.json --write-manifest docs/design/contracts/uiux-packages/g-2.writes.json --evidence docs/campaign-evidence/<feature-id>/g-2/validation.json` → exit 0 and `uiux-package-result@v1(package=G.2)` | revert only src/ui/g/g-2/; restore G.2 predecessor digests; run g-2 negative/recovery fixture | 25–35 min/3 CPU/6 GiB; 30k–40k; cognitive medium; uncertainty 24%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| G.3 | exact digests of declared Prereq products; output: Degraded and boundary states | `src/ui/g/g-3/**`; `tests/uiux/g-3/**`; `docs/design/contracts/uiux-packages/g-3.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/g-3/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/g-3/validate.py --package G.3 --contract docs/design/contracts/uiux-packages/g-3.json --write-manifest docs/design/contracts/uiux-packages/g-3.writes.json --evidence docs/campaign-evidence/<feature-id>/g-3/validation.json` → exit 0 and `uiux-package-result@v1(package=G.3)` | revert only src/ui/g/g-3/; restore G.3 predecessor digests; run g-3 negative/recovery fixture | 30–40 min/4 CPU/8 GiB; 35k–45k; cognitive medium; uncertainty 27%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| G.T | exact digests of declared Prereq products; output: Terminal integration (Integration review: mandatory) | `tests/uiux/g-t/{validate.py,fixtures/**}`; `docs/design/contracts/uiux-packages/g-t.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/g-t/{candidate-manifest.json,validation.json,recovery.json,resource-usage.json}` | `python3 tests/uiux/g-t/validate.py --package G.T --contract docs/design/contracts/uiux-packages/g-t.json --write-manifest docs/design/contracts/uiux-packages/g-t.writes.json --evidence docs/campaign-evidence/<feature-id>/g-t/validation.json` → exit 0 and `uiux-package-result@v1(package=G.T)` | withhold G.T merge; restore pinned predecessor manifest; run g-t rollback rehearsal | 65–75 min/4 CPU/8 GiB; 50k–60k; cognitive high; uncertainty 15%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| H.1 | exact digests of declared Prereq products; output: Governance record views | `src/ui/h/h-1/**`; `tests/uiux/h-1/**`; `docs/design/contracts/uiux-packages/h-1.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/h-1/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/h-1/validate.py --package H.1 --contract docs/design/contracts/uiux-packages/h-1.json --write-manifest docs/design/contracts/uiux-packages/h-1.writes.json --evidence docs/campaign-evidence/<feature-id>/h-1/validation.json` → exit 0 and `uiux-package-result@v1(package=H.1)` | revert only src/ui/h/h-1/; restore H.1 predecessor digests; run h-1 negative/recovery fixture | 40–50 min/2 CPU/4 GiB; 45k–55k; cognitive medium; uncertainty 18%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| H.2 | exact digests of declared Prereq products; output: Report center and shared report identity | `src/ui/h/h-2/**`; `tests/uiux/h-2/**`; `docs/design/contracts/uiux-packages/h-2.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/h-2/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/h-2/validate.py --package H.2 --contract docs/design/contracts/uiux-packages/h-2.json --write-manifest docs/design/contracts/uiux-packages/h-2.writes.json --evidence docs/campaign-evidence/<feature-id>/h-2/validation.json` → exit 0 and `uiux-package-result@v1(package=H.2)` | revert only src/ui/h/h-2/; restore H.2 predecessor digests; run h-2 negative/recovery fixture | 45–55 min/3 CPU/6 GiB; 20k–30k; cognitive medium; uncertainty 21%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| H.3 | exact digests of declared Prereq products; output: Report families | `src/ui/h/h-3/**`; `tests/uiux/h-3/**`; `docs/design/contracts/uiux-packages/h-3.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/h-3/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/h-3/validate.py --package H.3 --contract docs/design/contracts/uiux-packages/h-3.json --write-manifest docs/design/contracts/uiux-packages/h-3.writes.json --evidence docs/campaign-evidence/<feature-id>/h-3/validation.json` → exit 0 and `uiux-package-result@v1(package=H.3)` | revert only src/ui/h/h-3/; restore H.3 predecessor digests; run h-3 negative/recovery fixture | 50–60 min/4 CPU/8 GiB; 25k–35k; cognitive medium; uncertainty 24%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| H.4 | exact digests of declared Prereq products; output: Derivation precedence and classified publication wiring | `src/ui/h/h-4/**`; `tests/uiux/h-4/**`; `docs/design/contracts/uiux-packages/h-4.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/h-4/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/h-4/validate.py --package H.4 --contract docs/design/contracts/uiux-packages/h-4.json --write-manifest docs/design/contracts/uiux-packages/h-4.writes.json --evidence docs/campaign-evidence/<feature-id>/h-4/validation.json` → exit 0 and `uiux-package-result@v1(package=H.4)` | revert only src/ui/h/h-4/; restore H.4 predecessor digests; run h-4 negative/recovery fixture | 55–65 min/1 CPU/2 GiB; 30k–40k; cognitive medium; uncertainty 27%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| H.T | exact digests of declared Prereq products; output: Terminal integration (Integration review: mandatory) | `tests/uiux/h-t/{validate.py,fixtures/**}`; `docs/design/contracts/uiux-packages/h-t.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/h-t/{candidate-manifest.json,validation.json,recovery.json,resource-usage.json}` | `python3 tests/uiux/h-t/validate.py --package H.T --contract docs/design/contracts/uiux-packages/h-t.json --write-manifest docs/design/contracts/uiux-packages/h-t.writes.json --evidence docs/campaign-evidence/<feature-id>/h-t/validation.json` → exit 0 and `uiux-package-result@v1(package=H.T)` | withhold H.T merge; restore pinned predecessor manifest; run h-t rollback rehearsal | 65–75 min/4 CPU/8 GiB; 45k–55k; cognitive high; uncertainty 15%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| I.1 | exact digests of declared Prereq products; output: Browser-PAT retirement | `src/ui/i/i-1/**`; `tests/uiux/i-1/**`; `docs/design/contracts/uiux-packages/i-1.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/i-1/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/i-1/validate.py --package I.1 --contract docs/design/contracts/uiux-packages/i-1.json --write-manifest docs/design/contracts/uiux-packages/i-1.writes.json --evidence docs/campaign-evidence/<feature-id>/i-1/validation.json` → exit 0 and `uiux-package-result@v1(package=I.1)` | revert only src/ui/i/i-1/; restore I.1 predecessor digests; run i-1 negative/recovery fixture | 20–30 min/3 CPU/6 GiB; 40k–50k; cognitive medium; uncertainty 18%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| I.2 | exact digests of declared Prereq products; output: Static curation views | `src/ui/i/i-2/**`; `tests/uiux/i-2/**`; `docs/design/contracts/uiux-packages/i-2.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/i-2/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/i-2/validate.py --package I.2 --contract docs/design/contracts/uiux-packages/i-2.json --write-manifest docs/design/contracts/uiux-packages/i-2.writes.json --evidence docs/campaign-evidence/<feature-id>/i-2/validation.json` → exit 0 and `uiux-package-result@v1(package=I.2)` | revert only src/ui/i/i-2/; restore I.2 predecessor digests; run i-2 negative/recovery fixture | 25–35 min/4 CPU/8 GiB; 45k–55k; cognitive medium; uncertainty 21%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| I.3 | exact digests of declared Prereq products; output: Static review/feedback views | `src/ui/i/i-3/**`; `tests/uiux/i-3/**`; `docs/design/contracts/uiux-packages/i-3.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/i-3/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/i-3/validate.py --package I.3 --contract docs/design/contracts/uiux-packages/i-3.json --write-manifest docs/design/contracts/uiux-packages/i-3.writes.json --evidence docs/campaign-evidence/<feature-id>/i-3/validation.json` → exit 0 and `uiux-package-result@v1(package=I.3)` | revert only src/ui/i/i-3/; restore I.3 predecessor digests; run i-3 negative/recovery fixture | 30–40 min/1 CPU/2 GiB; 20k–30k; cognitive medium; uncertainty 24%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| I.4 | exact digests of declared Prereq products; output: Authenticated submission integration | `src/ui/i/i-4/**`; `tests/uiux/i-4/**`; `docs/design/contracts/uiux-packages/i-4.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/i-4/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/i-4/validate.py --package I.4 --contract docs/design/contracts/uiux-packages/i-4.json --write-manifest docs/design/contracts/uiux-packages/i-4.writes.json --evidence docs/campaign-evidence/<feature-id>/i-4/validation.json` → exit 0 and `uiux-package-result@v1(package=I.4)` | revert only src/ui/i/i-4/; restore I.4 predecessor digests; run i-4 negative/recovery fixture | 35–45 min/2 CPU/4 GiB; 25k–35k; cognitive medium; uncertainty 27%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| I.5 | exact digests of declared Prereq products; output: Public-feedback identity modes | `src/ui/i/i-5/**`; `tests/uiux/i-5/**`; `docs/design/contracts/uiux-packages/i-5.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/i-5/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/i-5/validate.py --package I.5 --contract docs/design/contracts/uiux-packages/i-5.json --write-manifest docs/design/contracts/uiux-packages/i-5.writes.json --evidence docs/campaign-evidence/<feature-id>/i-5/validation.json` → exit 0 and `uiux-package-result@v1(package=I.5)` | revert only src/ui/i/i-5/; restore I.5 predecessor digests; run i-5 negative/recovery fixture | 40–50 min/3 CPU/6 GiB; 30k–40k; cognitive medium; uncertainty 15%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| I.T | exact digests of declared Prereq products; output: Terminal integration (Integration review: mandatory — Security/QA/UX) | `tests/uiux/i-t/{validate.py,fixtures/**}`; `docs/design/contracts/uiux-packages/i-t.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/i-t/{candidate-manifest.json,validation.json,recovery.json,resource-usage.json}` | `python3 tests/uiux/i-t/validate.py --package I.T --contract docs/design/contracts/uiux-packages/i-t.json --write-manifest docs/design/contracts/uiux-packages/i-t.writes.json --evidence docs/campaign-evidence/<feature-id>/i-t/validation.json` → exit 0 and `uiux-package-result@v1(package=I.T)` | withhold I.T merge; restore pinned predecessor manifest; run i-t rollback rehearsal | 65–75 min/4 CPU/8 GiB; 45k–55k; cognitive high; uncertainty 18%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| J.1 | exact digests of declared Prereq products; output: Typed backlog adapter and parity report | `src/ui/j/j-1/**`; `tests/uiux/j-1/**`; `docs/design/contracts/uiux-packages/j-1.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/j-1/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/j-1/validate.py --package J.1 --contract docs/design/contracts/uiux-packages/j-1.json --write-manifest docs/design/contracts/uiux-packages/j-1.writes.json --evidence docs/campaign-evidence/<feature-id>/j-1/validation.json` → exit 0 and `uiux-package-result@v1(package=J.1)` | revert only src/ui/j/j-1/; restore J.1 predecessor digests; run j-1 negative/recovery fixture | 50–60 min/1 CPU/2 GiB; 40k–50k; cognitive medium; uncertainty 21%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| J.2 | exact digests of declared Prereq products; output: Backlog/list/detail/query/conflict views | `src/ui/j/j-2/**`; `tests/uiux/j-2/**`; `docs/design/contracts/uiux-packages/j-2.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/j-2/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/j-2/validate.py --package J.2 --contract docs/design/contracts/uiux-packages/j-2.json --write-manifest docs/design/contracts/uiux-packages/j-2.writes.json --evidence docs/campaign-evidence/<feature-id>/j-2/validation.json` → exit 0 and `uiux-package-result@v1(package=J.2)` | revert only src/ui/j/j-2/; restore J.2 predecessor digests; run j-2 negative/recovery fixture | 55–65 min/2 CPU/4 GiB; 45k–55k; cognitive medium; uncertainty 24%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| J.3 | exact digests of declared Prereq products; output: Dependency DAG and roadmap views | `src/ui/j/j-3/**`; `tests/uiux/j-3/**`; `docs/design/contracts/uiux-packages/j-3.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/j-3/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/j-3/validate.py --package J.3 --contract docs/design/contracts/uiux-packages/j-3.json --write-manifest docs/design/contracts/uiux-packages/j-3.writes.json --evidence docs/campaign-evidence/<feature-id>/j-3/validation.json` → exit 0 and `uiux-package-result@v1(package=J.3)` | revert only src/ui/j/j-3/; restore J.3 predecessor digests; run j-3 negative/recovery fixture | 15–25 min/3 CPU/6 GiB; 20k–30k; cognitive medium; uncertainty 27%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| J.4 | exact digests of declared Prereq products; output: Mutation preview and dual-read reconciliation | `src/ui/j/j-4/**`; `tests/uiux/j-4/**`; `docs/design/contracts/uiux-packages/j-4.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/j-4/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/j-4/validate.py --package J.4 --contract docs/design/contracts/uiux-packages/j-4.json --write-manifest docs/design/contracts/uiux-packages/j-4.writes.json --evidence docs/campaign-evidence/<feature-id>/j-4/validation.json` → exit 0 and `uiux-package-result@v1(package=J.4)` | revert only src/ui/j/j-4/; restore J.4 predecessor digests; run j-4 negative/recovery fixture | 20–30 min/4 CPU/8 GiB; 25k–35k; cognitive medium; uncertainty 15%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| J.T | exact digests of declared Prereq products; output: Terminal integration (Integration review: mandatory) | `tests/uiux/j-t/{validate.py,fixtures/**}`; `docs/design/contracts/uiux-packages/j-t.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/j-t/{candidate-manifest.json,validation.json,recovery.json,resource-usage.json}` | `python3 tests/uiux/j-t/validate.py --package J.T --contract docs/design/contracts/uiux-packages/j-t.json --write-manifest docs/design/contracts/uiux-packages/j-t.writes.json --evidence docs/campaign-evidence/<feature-id>/j-t/validation.json` → exit 0 and `uiux-package-result@v1(package=J.T)` | withhold J.T merge; restore pinned predecessor manifest; run j-t rollback rehearsal | 65–75 min/4 CPU/8 GiB; 55k–65k; cognitive high; uncertainty 18%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| K.1 | exact digests of declared Prereq products; output: Identity and session architecture | `src/ui/k/k-1/**`; `tests/uiux/k-1/**`; `docs/design/contracts/uiux-packages/k-1.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/k-1/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/k-1/validate.py --package K.1 --contract docs/design/contracts/uiux-packages/k-1.json --write-manifest docs/design/contracts/uiux-packages/k-1.writes.json --evidence docs/campaign-evidence/<feature-id>/k-1/validation.json` → exit 0 and `uiux-package-result@v1(package=K.1)` | revert only src/ui/k/k-1/; restore K.1 predecessor digests; run k-1 negative/recovery fixture | 30–40 min/2 CPU/4 GiB; 35k–45k; cognitive medium; uncertainty 21%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| K.2 | exact digests of declared Prereq products; output: Authorization and idempotent action framework | `src/ui/k/k-2/**`; `tests/uiux/k-2/**`; `docs/design/contracts/uiux-packages/k-2.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/k-2/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/k-2/validate.py --package K.2 --contract docs/design/contracts/uiux-packages/k-2.json --write-manifest docs/design/contracts/uiux-packages/k-2.writes.json --evidence docs/campaign-evidence/<feature-id>/k-2/validation.json` → exit 0 and `uiux-package-result@v1(package=K.2)` | revert only src/ui/k/k-2/; restore K.2 predecessor digests; run k-2 negative/recovery fixture | 35–45 min/3 CPU/6 GiB; 40k–50k; cognitive medium; uncertainty 24%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| K.3 | exact digests of declared Prereq products; output: Notification pipeline | `src/ui/k/k-3/**`; `tests/uiux/k-3/**`; `docs/design/contracts/uiux-packages/k-3.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/k-3/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/k-3/validate.py --package K.3 --contract docs/design/contracts/uiux-packages/k-3.json --write-manifest docs/design/contracts/uiux-packages/k-3.writes.json --evidence docs/campaign-evidence/<feature-id>/k-3/validation.json` → exit 0 and `uiux-package-result@v1(package=K.3)` | revert only src/ui/k/k-3/; restore K.3 predecessor digests; run k-3 negative/recovery fixture | 40–50 min/4 CPU/8 GiB; 45k–55k; cognitive medium; uncertainty 27%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| K.4 | exact digests of declared Prereq products; output: Adversarial harness | `src/ui/k/k-4/**`; `tests/uiux/k-4/**`; `docs/design/contracts/uiux-packages/k-4.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/k-4/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/k-4/validate.py --package K.4 --contract docs/design/contracts/uiux-packages/k-4.json --write-manifest docs/design/contracts/uiux-packages/k-4.writes.json --evidence docs/campaign-evidence/<feature-id>/k-4/validation.json` → exit 0 and `uiux-package-result@v1(package=K.4)` | revert only src/ui/k/k-4/; restore K.4 predecessor digests; run k-4 negative/recovery fixture | 45–55 min/1 CPU/2 GiB; 20k–30k; cognitive medium; uncertainty 15%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| K.T | exact digests of declared Prereq products; output: K.T bounded product | `tests/uiux/k-t/{validate.py,fixtures/**}`; `docs/design/contracts/uiux-packages/k-t.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/k-t/{candidate-manifest.json,validation.json,recovery.json,resource-usage.json}` | `python3 tests/uiux/k-t/validate.py --package K.T --contract docs/design/contracts/uiux-packages/k-t.json --write-manifest docs/design/contracts/uiux-packages/k-t.writes.json --evidence docs/campaign-evidence/<feature-id>/k-t/validation.json` → exit 0 and `uiux-package-result@v1(package=K.T)` | withhold K.T merge; restore pinned predecessor manifest; run k-t rollback rehearsal | 65–75 min/4 CPU/8 GiB; 50k–60k; cognitive high; uncertainty 18%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| L.1 | exact digests of declared Prereq products; output: Context manifest and inspector | `src/ui/l/l-1/**`; `tests/uiux/l-1/**`; `docs/design/contracts/uiux-packages/l-1.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/l-1/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/l-1/validate.py --package L.1 --contract docs/design/contracts/uiux-packages/l-1.json --write-manifest docs/design/contracts/uiux-packages/l-1.writes.json --evidence docs/campaign-evidence/<feature-id>/l-1/validation.json` → exit 0 and `uiux-package-result@v1(package=L.1)` | revert only src/ui/l/l-1/; restore L.1 predecessor digests; run l-1 negative/recovery fixture | 55–65 min/3 CPU/6 GiB; 30k–40k; cognitive medium; uncertainty 21%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| L.2 | exact digests of declared Prereq products; output: Conversation, proposal, finalization | `src/ui/l/l-2/**`; `tests/uiux/l-2/**`; `docs/design/contracts/uiux-packages/l-2.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/l-2/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/l-2/validate.py --package L.2 --contract docs/design/contracts/uiux-packages/l-2.json --write-manifest docs/design/contracts/uiux-packages/l-2.writes.json --evidence docs/campaign-evidence/<feature-id>/l-2/validation.json` → exit 0 and `uiux-package-result@v1(package=L.2)` | revert only src/ui/l/l-2/; restore L.2 predecessor digests; run l-2 negative/recovery fixture | 15–25 min/4 CPU/8 GiB; 35k–45k; cognitive medium; uncertainty 24%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| L.3 | exact digests of declared Prereq products; output: Provenance and authority boundary | `src/ui/l/l-3/**`; `tests/uiux/l-3/**`; `docs/design/contracts/uiux-packages/l-3.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/l-3/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/l-3/validate.py --package L.3 --contract docs/design/contracts/uiux-packages/l-3.json --write-manifest docs/design/contracts/uiux-packages/l-3.writes.json --evidence docs/campaign-evidence/<feature-id>/l-3/validation.json` → exit 0 and `uiux-package-result@v1(package=L.3)` | revert only src/ui/l/l-3/; restore L.3 predecessor digests; run l-3 negative/recovery fixture | 20–30 min/1 CPU/2 GiB; 40k–50k; cognitive medium; uncertainty 27%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| L.T | exact digests of declared Prereq products; output: Terminal integration (Integration review: mandatory) | `tests/uiux/l-t/{validate.py,fixtures/**}`; `docs/design/contracts/uiux-packages/l-t.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/l-t/{candidate-manifest.json,validation.json,recovery.json,resource-usage.json}` | `python3 tests/uiux/l-t/validate.py --package L.T --contract docs/design/contracts/uiux-packages/l-t.json --write-manifest docs/design/contracts/uiux-packages/l-t.writes.json --evidence docs/campaign-evidence/<feature-id>/l-t/validation.json` → exit 0 and `uiux-package-result@v1(package=L.T)` | withhold L.T merge; restore pinned predecessor manifest; run l-t rollback rehearsal | 65–75 min/4 CPU/8 GiB; 55k–65k; cognitive high; uncertainty 15%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| M.1 | exact digests of declared Prereq products; output: Cutover mechanics | `src/ui/m/m-1/**`; `tests/uiux/m-1/**`; `docs/design/contracts/uiux-packages/m-1.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/m-1/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/m-1/validate.py --package M.1 --contract docs/design/contracts/uiux-packages/m-1.json --write-manifest docs/design/contracts/uiux-packages/m-1.writes.json --evidence docs/campaign-evidence/<feature-id>/m-1/validation.json` → exit 0 and `uiux-package-result@v1(package=M.1)` | revert only src/ui/m/m-1/; restore M.1 predecessor digests; run m-1 negative/recovery fixture | 30–40 min/3 CPU/6 GiB; 20k–30k; cognitive medium; uncertainty 18%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| M.T | exact digests of declared Prereq products; output: M.T bounded product | `tests/uiux/m-t/{validate.py,fixtures/**}`; `docs/design/contracts/uiux-packages/m-t.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/m-t/{candidate-manifest.json,validation.json,recovery.json,resource-usage.json}` | `python3 tests/uiux/m-t/validate.py --package M.T --contract docs/design/contracts/uiux-packages/m-t.json --write-manifest docs/design/contracts/uiux-packages/m-t.writes.json --evidence docs/campaign-evidence/<feature-id>/m-t/validation.json` → exit 0 and `uiux-package-result@v1(package=M.T)` | withhold M.T merge; restore pinned predecessor manifest; run m-t rollback rehearsal | 65–75 min/4 CPU/8 GiB; 50k–60k; cognitive high; uncertainty 21%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| N.1 | exact digests of declared Prereq products; output: Source intake and legal provenance | `src/import/classic/n-1/**`; `tests/uiux/n-1/**`; `docs/design/contracts/uiux-packages/n-1.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/n-1/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/n-1/validate.py --package N.1 --contract docs/design/contracts/uiux-packages/n-1.json --write-manifest docs/design/contracts/uiux-packages/n-1.writes.json --evidence docs/campaign-evidence/<feature-id>/n-1/validation.json` → exit 0 and `uiux-package-result@v1(package=N.1)` | revert only src/import/classic/n-1/; restore N.1 predecessor digests; run n-1 negative/recovery fixture | 40–50 min/1 CPU/2 GiB; 30k–40k; cognitive medium; uncertainty 24%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| N.2 | exact digests of declared Prereq products; output: Extraction and entity mapping | `src/import/classic/n-2/**`; `tests/uiux/n-2/**`; `docs/design/contracts/uiux-packages/n-2.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/n-2/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/n-2/validate.py --package N.2 --contract docs/design/contracts/uiux-packages/n-2.json --write-manifest docs/design/contracts/uiux-packages/n-2.writes.json --evidence docs/campaign-evidence/<feature-id>/n-2/validation.json` → exit 0 and `uiux-package-result@v1(package=N.2)` | revert only src/import/classic/n-2/; restore N.2 predecessor digests; run n-2 negative/recovery fixture | 45–55 min/2 CPU/4 GiB; 35k–45k; cognitive medium; uncertainty 27%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| N.3 | exact digests of declared Prereq products; output: Translation pipeline at scale | `src/import/classic/n-3/**`; `tests/uiux/n-3/**`; `docs/design/contracts/uiux-packages/n-3.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/n-3/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/n-3/validate.py --package N.3 --contract docs/design/contracts/uiux-packages/n-3.json --write-manifest docs/design/contracts/uiux-packages/n-3.writes.json --evidence docs/campaign-evidence/<feature-id>/n-3/validation.json` → exit 0 and `uiux-package-result@v1(package=N.3)` | revert only src/import/classic/n-3/; restore N.3 predecessor digests; run n-3 negative/recovery fixture | 50–60 min/3 CPU/6 GiB; 40k–50k; cognitive medium; uncertainty 15%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| N.4 | exact digests of declared Prereq products; output: Performance qualification at corpus scale | `src/import/classic/n-4/**`; `tests/uiux/n-4/**`; `docs/design/contracts/uiux-packages/n-4.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/n-4/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/n-4/validate.py --package N.4 --contract docs/design/contracts/uiux-packages/n-4.json --write-manifest docs/design/contracts/uiux-packages/n-4.writes.json --evidence docs/campaign-evidence/<feature-id>/n-4/validation.json` → exit 0 and `uiux-package-result@v1(package=N.4)` | revert only src/import/classic/n-4/; restore N.4 predecessor digests; run n-4 negative/recovery fixture | 55–65 min/4 CPU/8 GiB; 45k–55k; cognitive medium; uncertainty 18%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| N.T | exact digests of declared Prereq products; output: Terminal integration (Integration review: mandatory) | `tests/uiux/n-t/{validate.py,fixtures/**}`; `docs/design/contracts/uiux-packages/n-t.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/n-t/{candidate-manifest.json,validation.json,recovery.json,resource-usage.json}` | `python3 tests/uiux/n-t/validate.py --package N.T --contract docs/design/contracts/uiux-packages/n-t.json --write-manifest docs/design/contracts/uiux-packages/n-t.writes.json --evidence docs/campaign-evidence/<feature-id>/n-t/validation.json` → exit 0 and `uiux-package-result@v1(package=N.T)` | withhold N.T merge; restore pinned predecessor manifest; run n-t rollback rehearsal | 65–75 min/4 CPU/8 GiB; 45k–55k; cognitive high; uncertainty 21%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| O.1 | exact digests of declared Prereq products; output: Research protocol and safety model | `src/research/o-1/**`; `tests/uiux/o-1/**`; `docs/design/contracts/uiux-packages/o-1.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/o-1/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/o-1/validate.py --package O.1 --contract docs/design/contracts/uiux-packages/o-1.json --write-manifest docs/design/contracts/uiux-packages/o-1.writes.json --evidence docs/campaign-evidence/<feature-id>/o-1/validation.json` → exit 0 and `uiux-package-result@v1(package=O.1)` | revert only src/research/o-1/; restore O.1 predecessor digests; run o-1 negative/recovery fixture | 20–30 min/2 CPU/4 GiB; 25k–35k; cognitive medium; uncertainty 24%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| O.2 | exact digests of declared Prereq products; output: Context-assembly prototype | `src/research/o-2/**`; `tests/uiux/o-2/**`; `docs/design/contracts/uiux-packages/o-2.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/o-2/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/o-2/validate.py --package O.2 --contract docs/design/contracts/uiux-packages/o-2.json --write-manifest docs/design/contracts/uiux-packages/o-2.writes.json --evidence docs/campaign-evidence/<feature-id>/o-2/validation.json` → exit 0 and `uiux-package-result@v1(package=O.2)` | revert only src/research/o-2/; restore O.2 predecessor digests; run o-2 negative/recovery fixture | 25–35 min/3 CPU/6 GiB; 30k–40k; cognitive medium; uncertainty 27%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| O.3 | exact digests of declared Prereq products; output: VM prototype and isolation tests | `src/research/o-3/**`; `tests/uiux/o-3/**`; `docs/design/contracts/uiux-packages/o-3.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/o-3/{validation,recovery,resource-usage}.json` | `python3 tests/uiux/o-3/validate.py --package O.3 --contract docs/design/contracts/uiux-packages/o-3.json --write-manifest docs/design/contracts/uiux-packages/o-3.writes.json --evidence docs/campaign-evidence/<feature-id>/o-3/validation.json` → exit 0 and `uiux-package-result@v1(package=O.3)` | revert only src/research/o-3/; restore O.3 predecessor digests; run o-3 negative/recovery fixture | 30–40 min/4 CPU/8 GiB; 35k–45k; cognitive medium; uncertainty 15%; risk medium | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |
| O.T | exact digests of declared Prereq products; output: Terminal integration (Integration review: mandatory) | `tests/uiux/o-t/{validate.py,fixtures/**}`; `docs/design/contracts/uiux-packages/o-t.{json,writes.json}`; `docs/campaign-evidence/<feature-id>/o-t/{candidate-manifest.json,validation.json,recovery.json,resource-usage.json}` | `python3 tests/uiux/o-t/validate.py --package O.T --contract docs/design/contracts/uiux-packages/o-t.json --write-manifest docs/design/contracts/uiux-packages/o-t.writes.json --evidence docs/campaign-evidence/<feature-id>/o-t/validation.json` → exit 0 and `uiux-package-result@v1(package=O.T)` | withhold O.T merge; restore pinned predecessor manifest; run o-t rollback rehearsal | 65–75 min/4 CPU/8 GiB; 50k–60k; cognitive high; uncertainty 18%; risk high | `<allocated-item-id>` based on and merged to `<allocated-parent-item-id>` |


Every validation harness is package-owned at its row's
`tests/uiux/<package>/validate.py`; no unowned portfolio-global validator is an
input. Harnesses consume only their row's owned contract/write manifest and
declared predecessor products. Terminal rows own their terminal contract,
write-manifest, fixtures and harness in addition to evidence; terminals do not
consume contract inputs outside their manifests. Profiles emit commands,
status, input/output digests and changed paths. Terminals additionally rerun
prerequisite profiles, exact RQ/Q/view validation, failure injection and
rollback rehearsal.

A.4 additionally owns the public types `OperationalRole`, `CapabilityBinding`,
`BackgroundJobId`, `BackgroundJobRecord`, `BackgroundJobState`,
`BackgroundJobStatus`, `BackgroundJobResult`, `CancellationRequest`,
`RetryIdentity`, `HandoffRecord` and `RecoveryRecord`. Its schemas reject
unknown roles/states, missing Task/owner/base/epoch/scope/resource/command
digests, illegal or regressive transitions, undeclared external/credential use,
duplicate non-idempotent starts, orphan adoption and authority fields. Minor
compatible additions require passing old+new fixtures; breaking changes require
an additive contract version, impact analysis and fresh A.4 review/Acceptance.
Recovery rejects new starts, retains exact job evidence, drains or records a
recoverable interruption, and restores the prior accepted schema only after
quiescence. A.4 consumers bind both shared-contract digests, not merely A.4's
item state.

`<allocated-item-id>` is a substitution variable for the exact ID allocated in
the authoritative backlog, not a branch prefix or path. Every one of the 77
rows creates branch `<allocated-item-id>` from its exact parent item branch and
merges back to that parent while carrying prerequisite branches and claim files.
A Task's parent is its exact Feature-ID branch; a Subtask's parent is its exact
Task-ID branch. Allocation rejects a branch with any extra `feature/` prefix,
slug, package alias or parent mismatch.

### Migration and gate graph (normative)

Every F-F..F-O package writing `src/**` has prerequisite E.T and may never write `_src/**`. E.1 owns the relocation manifest/freeze; before E.T no post-migration consumer starts and afterward `_src/**` is read-only compatibility input. The validator expands and checks these edges.

All following cross-item gates require a bound `decision-record@v1` and distinct management-instantiated Architect scope review before mutation:

| Gate | Machine edges |
|---|---|
| E0.T | E.1 `⊳acc E0.T` |
| A.T/B.T | F.1 `⊳acc A.T,B.T` |
| A.4 Runner job-control contract | E0.1,A.5,D.2,E.3,G.2,N.1,N.2,N.3,N.4 `⊳acc A.4` |
| D.T | I.4,L.1,H.4 `⊳acc D.T` |
| K.T | I.4,L.1,M.1 `⊳acc K.T` |
| J.T + D-04 | M.1 `⊳acc J.T` and recorded D-04 authority |
| I.1 PAT retirement | F.T,G.T,H.T,I.T,J.T,K.T,L.T,M.T,N.T,O.T require I.1 |
| A.5,D.2,H.4,F-E,M.1/M.T | affected units named by bound decision/review |

These edges supersede prose-only starts. `⊳acc` means current, reachable, non-invalidated Acceptance for the pinned baseline.

A.4 is the sole shared Runner-consumer interface in this decomposition and an
intermediate checkpoint, not a second terminal. Its consumers are exhaustive:
benchmarking, link crawling, projection scanning, incremental building, graph
performance work, and the imported-corpus intake/extraction/translation/
qualification chain. A package not in this list may use bounded foreground
execution only; adding background execution changes its contract and requires
an A.4 current-Acceptance-before-start edge. Terminal proofs A.T, E.T, G.T and
N.T consume the job evidence transitively; Feature closure additionally tests a
synthetic long job plus cancellation/recovery and role/authority negatives.

### Exact trace ownership (normative)

In the exact sets below, each three-digit token `NNN` expands mechanically to
`RQ-UIUX-NNN`; their union must equal `RQ-UIUX-001..032`.

RQ-012 and RQ-013 are implementation and terminal-verification obligations in
every UI Feature. Exact package owners are B.1/B.2+B.T, C.1/C.2+C.T,
D.1/D.2+D.T, E.2/E.3+E.T, F.1/F.2+F.T, G.1/G.2+G.T,
H.1/H.2+H.T, I.1/I.2+I.T, J.1/J.2+J.T, K.1/K.2+K.T,
L.1/L.2+L.T, M.1+M.T, N.1/N.2+N.T and O.1/O.2+O.T respectively
(left/right of `+` are implementation owners; the terminal is verifier).
Exact Feature RQ sets are:
E0={019}; A={003,004,005,025,029,031,032}; B={002,011,012,013,014,015,018,024,026,031,032}; C={012,013,014,032}; D={020,021,022,023,025,032}; E={016,019,025,026,029,032}; F={001,002,003,004,005,012,013,014,016,032}; G={004,012,013,017,018,031,032}; H={004,005,011,012,013,015,018,020,021,032}; I={002,006,007,012,013,020,031,032}; J={002,008,012,013,018,028,032}; K={007,012,013,020,027,032}; L={009,012,013,032}; M={008,012,013,028,032}; N={001,012,013,014,016,019,030,032}; O={010,012,013,032}.

Exact view ownership (inclusive expansion): SYS-01..12→B.2/B.T;
KN-01..04→F.1/F.T, KN-05..06→F.2/F.T, KN-07..11→F.3/F.T,
KN-12..14→F.4/F.T, KN-15..17→F.5/F.T;
TR-01..04→G.1/G.T, TR-05..06→G.2/G.T, TR-07..08→G.3/G.T;
CU-01..02→I.1/I.T, CU-03..04→I.2/I.T, CU-05..06→I.3/I.T,
CU-07..08→I.4/I.T, CU-09..10→I.5/I.T;
RV-01..02→I.1/I.T, RV-03..05→I.2/I.T, RV-06..07→I.3/I.T,
RV-08..10→I.4/I.T, RV-11..12→I.5/I.T;
GW-01..16→H.1/H.T, GW-17..20→H.4/H.T;
RP-01..05→H.2/H.T, RP-06..15→H.3/H.T;
TK-01..02→J.1/J.T, TK-03..04→J.2/J.T, TK-05..06→J.3/J.T,
TK-07..08→J.4/J.T; AI-01..02→L.1/L.T, AI-03..04→L.2/L.T,
AI-05..06→L.3/L.T, AI-07→O.2/O.T, AI-08→O.3/O.T;
AD-01..04→C.4/C.T, AD-05→E.2/E.T, AD-06→E.3/E.T,
AD-07→E.4/E.T, AD-08→D.5/D.T, AD-09→K.3/K.T.
Validator expansion proves equality to 119 rows, exactly one implementation
owner and one terminal verifier, rejecting missing/extra/duplicate/summary-only
coverage.

Exact terminal Q ownership remains the baseline §7 mapping; allocation copies each Q into both its producing package(s) and named terminal and set-equality validates Q-01..Q-24.


## 5. Cross-item gate scopes requiring `decision-record@v1` + distinct Architect review

Per the canonical `cross-item-blast-radius` predicate, before the first gate
mutation (not before tool authorship): **E0.T** ceiling ratification as F-E start
gate; **A.5** link-crawler wiring into shared validation; **D.2** publication
scanner as blocking gate; **F-E** build/validation path change (Feature-level
record); **A.4** shared Runner role/job-control interface and consumer start
edges; **H.4** derivation-precedence rules; **I.1** browser-PAT removal
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
  satisfied; A.4 is the additional intermediate shared-interface checkpoint;
  other intermediate checkpoints are only those flagged in §5 via decisions).
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
6. **Staffing/role assignment** — all packages execute directly; packages marked
  `op` additionally need operator participation. The Dispatcher explicitly
  selects Programmer, Tester, or Task-ID-bound Runner; the deterministic matcher
  and dispatcher
   assignment happen at allocation, not here.

## 10. Validation of this proposal

Mechanical self-checks run on this document (results in the claim progress log):
16 Feature sections; 77 package IDs unique; 16 terminals, one per Feature; all
32 RQ IDs and 24 Q IDs referenced; D-01..D-06 each mapped with a neutrality
mechanism; prerequisite references resolve to defined package IDs; no forward
reference from a terminal into its own Feature's packages. Roadmap refinement:
**none required** — all package boundaries were expressible without contradicting
`ui-ux-implementation-roadmap.md`; the roadmap file is deliberately untouched.
